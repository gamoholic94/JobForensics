"""Safe URL normalization and local domain risk indicators."""
import ipaddress
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source", "utm_campaign", "utm_medium", "utm_source"}


def normalize_url(value: str) -> str:
    """Validate and normalize an HTTP(S) URL without performing a request."""
    raw = (value or "").strip()
    if not raw:
        raise ValueError("URL is required")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Only valid http and https URLs are supported")
    if "@" in parts.netloc:
        raise ValueError("URLs containing embedded credentials are not supported")
    hostname = parts.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    try:
        ipaddress.ip_address(hostname)
        is_ip = True
    except ValueError:
        is_ip = False
    if hostname.lower() == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Localhost URLs are not supported")
    if is_ip and (ipaddress.ip_address(hostname).is_private or ipaddress.ip_address(hostname).is_loopback or ipaddress.ip_address(hostname).is_link_local):
        raise ValueError("Private or local IP addresses are not supported")
    if not is_ip and hostname != "localhost" and "." not in hostname:
        raise ValueError("URL must contain a valid domain name")
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key.lower() not in TRACKING_KEYS and not key.lower().startswith("utm_")]
    port = parts.port
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", urlencode(query), ""))


def analyze_url(value: str) -> dict:
    """Return transparent URL indicators; unavailable external facts stay absent."""
    normalized = normalize_url(value)
    parts = urlsplit(normalized)
    hostname = parts.hostname or ""
    warnings = []
    suspicious = []
    try:
        ipaddress.ip_address(hostname)
        suspicious.append("The URL uses an IP address instead of a domain name.")
    except ValueError:
        pass
    if len(normalized) > 180:
        suspicious.append("The URL is unusually long.")
    if len(hostname.split(".")) > 4:
        suspicious.append("The domain contains an unusually deep subdomain chain.")
    if re.search(r"(login|verify|wallet|crypto|free-money|urgent)", normalized, re.I):
        suspicious.append("The URL contains a potentially deceptive keyword.")
    if parts.scheme != "https":
        warnings.append("The page does not use HTTPS.")
    return {
        "url": normalized,
        "domain": hostname,
        "subdomain": ".".join(hostname.split(".")[:-2]) if len(hostname.split(".")) > 2 else "",
        "https": parts.scheme == "https",
        "domain_age_days": None,
        "registered_domain": "Unavailable",
        "suspicious_url": bool(suspicious),
        "trust_indicators": ["HTTPS is enabled"] if parts.scheme == "https" else [],
        "warnings": warnings + suspicious,
    }
