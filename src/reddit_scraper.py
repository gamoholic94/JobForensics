"""Bounded extraction of public Reddit post content for job-risk analysis."""

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit
import requests
from src.url_analyzer import normalize_url

REDDIT_HOSTS = {"reddit.com", "www.reddit.com", "old.reddit.com"}
MAX_RESPONSE_BYTES = 2_000_000
MAX_COMMENTS = 20
TIMEOUT_SECONDS = 15
REDDIT_HEADERS = {
    "User-Agent": "JobForensics/1.0 public job-safety research bot",
    "Accept": "application/json",
}

def _reddit_json_url(value: str) -> str:
    normalized = normalize_url(value)
    parts = urlsplit(normalized)
    hostname = (parts.hostname or "").lower()
    if hostname not in REDDIT_HOSTS:
        raise ValueError("Only public Reddit URLs are supported for Reddit analysis")
    if not parts.path or parts.path == "/":
        raise ValueError("Provide a Reddit post or subreddit URL")
    path = parts.path.rstrip("/")
    if not path.endswith(".json"):
        path += ".json"
    return urlunsplit(("https", "www.reddit.com", path, parts.query, ""))

def _bounded_json_get(url: str, timeout: float = TIMEOUT_SECONDS) -> Any:
    response = requests.get(
        url,
        headers=REDDIT_HEADERS,
        timeout=min(float(timeout), TIMEOUT_SECONDS),
        allow_redirects=False,
        stream=True,
    )
    if response.status_code == 429:
        raise ValueError("Reddit is rate-limiting automated requests. Try again later.")
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "json" not in content_type:
        raise ValueError("Reddit did not return a JSON response")
    content_length = int(response.headers.get("content-length", 0) or 0)
    if content_length > MAX_RESPONSE_BYTES:
        raise ValueError("The Reddit response is too large to process")
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=65536):
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError("The Reddit response is too large to process")
        chunks.append(chunk)
    return json.loads(b"".join(chunks).decode(response.encoding or "utf-8"))


def _post_data(payload: Any) -> dict[str, Any]:
    try:
        return payload[0]["data"]["children"][0]["data"]
    except (IndexError, KeyError, TypeError) as exc:
        raise ValueError("The Reddit URL did not contain a readable post") from exc


def scrape_reddit(url: str) -> dict[str, Any]:
    """Extract a Reddit post title, body, and bounded public comments."""
    json_url = _reddit_json_url(url)
    payload = _bounded_json_get(json_url)
    post = _post_data(payload)
    title = str(post.get("title") or "").strip()
    body = str(post.get("selftext") or "").strip()
    subreddit = str(post.get("subreddit_name_prefixed") or post.get("subreddit") or "").strip()
    permalink = str(post.get("permalink") or "").strip()
    comments: list[str] = []
    if isinstance(payload, list) and len(payload) > 1:
        try:
            children = payload[1]["data"]["children"]
        except (IndexError, KeyError, TypeError):
            children = []
        for child in children[:MAX_COMMENTS]:
            comment = child.get("data", {}).get("body") if isinstance(child, dict) else ""
            if comment:
                comments.append(str(comment).strip())
    text_parts = [part for part in (title, body, *comments) if part]
    if not text_parts:
        raise ValueError("The Reddit post has no readable text")
    return {
        "url": normalize_url(url),
        "source_platform": "Reddit",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "description": "\n\n".join(text_parts),
        "company_name": "",
        "location": "",
        "subreddit": subreddit,
        "permalink": f"https://www.reddit.com{permalink}" if permalink.startswith("/") else "",
        "comment_count_analyzed": len(comments),
        "success": True,
        "error": None,
    }
