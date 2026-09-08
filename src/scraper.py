"""
Utility to fetch a job-posting URL and extract readable text content
so it can be fed into the fake-job-detection model.
"""
import json
import logging
import ipaddress
import socket
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.url_analyzer import normalize_url

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Tags that usually contain navigation/ads/boilerplate, not the JD itself
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "form", "noscript"]
MAX_RESPONSE_BYTES = 5_000_000
MAX_TIMEOUT_SECONDS = 30
ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
BLOCKED_SCRAPE_HOSTS = {"linkedin.com", "www.linkedin.com"}


def _validate_resolved_host(url: str) -> None:
    """Reject URLs whose current DNS answers point at internal networks."""
    hostname = requests.utils.urlparse(url).hostname
    if not hostname:
        raise ValueError("Invalid URL host")
    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve the URL host") from exc
    if not addresses:
        raise ValueError("Unable to resolve the URL host")
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if (
            parsed.is_private
            or parsed.is_loopback
            or parsed.is_link_local
            or parsed.is_reserved
            or parsed.is_unspecified
            or parsed.is_multicast
        ):
            raise ValueError("URLs resolving to private or local addresses are not supported")


def fetch_html(url: str, timeout: int = 10) -> str:
    """Download bounded HTML from a validated HTTP(S) URL with safe redirects."""
    normalized = normalize_url(url)
    hostname = requests.utils.urlparse(normalized).hostname or ""
    if hostname.lower() in BLOCKED_SCRAPE_HOSTS or hostname.lower().endswith(".linkedin.com"):
        raise ValueError(
            "LinkedIn blocks automated scraping. Paste the job description or upload a PDF/TXT file instead."
        )
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("Timeout must be a positive number")
    timeout = min(float(timeout), MAX_TIMEOUT_SECONDS)
    
    # Use allow_redirects=False to manually handle redirects
    session = requests.Session()
    
    # Custom redirect handling
    redirect_count = 0
    max_redirects = 30
    current_url = normalized
    
    while redirect_count < max_redirects:
        _validate_resolved_host(current_url)
        response = session.get(
            current_url, 
            headers=DEFAULT_HEADERS, 
            timeout=timeout, 
            allow_redirects=False,  # Manually handle redirects
            stream=True
        )
        if response.status_code == 429:
            raise ValueError(
                "This website is temporarily rate-limiting automated requests. "
                "Paste the job description or upload a PDF/TXT file instead."
            )
        response.raise_for_status()
        
        # Check if this is a redirect
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers.get('Location')
            if not redirect_url:
                break
            
            # Resolve relative targets and apply the full SSRF validator again.
            try:
                from urllib.parse import urljoin
                current_url = normalize_url(urljoin(current_url, redirect_url))
                redirect_count += 1
            except ValueError as exc:
                raise ValueError(f"Unsafe redirect detected: {exc}") from exc
        else:
            # Not a redirect, process response
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError("The URL did not return an HTML page")
            content_length = int(response.headers.get("content-length", 0) or 0)
            if content_length > MAX_RESPONSE_BYTES:
                raise ValueError("The response is too large to process")
            chunks = []
            size = 0
            for chunk in response.iter_content(chunk_size=65536):
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise ValueError("The response is too large to process")
                chunks.append(chunk)
            return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
    
    raise ValueError("Too many redirects")


def extract_text_from_html(html: str) -> str:
    """Extract the main readable text from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator=" ")
    text = " ".join(text.split())
    return text


def _json_ld_job(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.string or script.get_text())
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        candidates = payload if isinstance(payload, list) else payload.get("@graph", [payload]) if isinstance(payload, dict) else []
        for item in candidates:
            item_type = item.get("@type") if isinstance(item, dict) else ""
            if isinstance(item, dict) and (item_type == "JobPosting" or "JobPosting" in (item_type if isinstance(item_type, list) else [])):
                return item
    return {}


def extract_job_fields(html: str) -> dict[str, Any]:
    """Extract best-effort JobPosting fields, with JSON-LD preferred."""
    data = _json_ld_job(html)
    soup = BeautifulSoup(html, "html.parser")
    title = data.get("title") or (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")
    description = data.get("description") or extract_text_from_html(html)
    organization = data.get("hiringOrganization") or {}
    location = data.get("jobLocation") or {}
    same_as = organization.get("sameAs", "") if isinstance(organization, dict) else ""
    if isinstance(same_as, list):
        same_as = next((value for value in same_as if isinstance(value, str)), "")
    return {
        "title": title,
        "company_name": organization.get("name", "") if isinstance(organization, dict) else "",
        "company_website": same_as,
        "company_profile": organization.get("description", "") if isinstance(organization, dict) else "",
        "application_url": data.get("applicationUrl", ""),
        "description": BeautifulSoup(str(description), "html.parser").get_text(" ", strip=True),
        "requirements": data.get("qualifications", ""),
        "benefits": data.get("jobBenefits", ""),
        "salary": data.get("baseSalary", ""),
        "location": location,
        "employment_type": data.get("employmentType", ""),
        "date_posted": data.get("datePosted", ""),
    }


def extract_job_description_from_url(url: str, timeout: int = 10) -> str:
    """
    Fetch a job posting URL and return the extracted plain-text content.
    Raises requests.exceptions.RequestException on network/HTTP errors.
    """
    html = fetch_html(url, timeout=timeout)
    fields = extract_job_fields(html)
    return fields["description"]


def scrape_job(url: str, timeout: int = 10) -> dict[str, Any]:
    """Return structured extraction or a useful error object for callers."""
    try:
        normalized = normalize_url(url)
        html = fetch_html(normalized, timeout=timeout)
        result = extract_job_fields(html)
        result["url"] = normalized
        result["success"] = bool(result["description"])
        result["error"] = None if result["description"] else "No readable job content found"
        result["error_type"] = None if result["description"] else "EmptyContentError"
        logger.info("Scraped job URL successfully: %s", normalized)
        return result
    except (ValueError, requests.RequestException) as exc:
        logger.warning("Scraping failed: %s", exc)
        return {"url": url, "description": "", "success": False, "error": str(exc), "error_type": type(exc).__name__}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(extract_job_description_from_url(test_url)[:1000])
    else:
        print("Usage: python scraper.py <job_posting_url>")
