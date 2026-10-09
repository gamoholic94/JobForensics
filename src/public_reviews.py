"""Bounded public review lookup using Reddit's public JSON search endpoint."""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from src.reddit_scraper import MAX_RESPONSE_BYTES, REDDIT_HEADERS, TIMEOUT_SECONDS, _bounded_json_get


def _review_status(text: str, score: int, author: str) -> tuple[str, str]:
    lower = text.lower()
    suspicious_terms = ("pay upfront", "send money", "telegram", "whatsapp", "crypto", "gift card")
    if any(term in lower for term in suspicious_terms):
        return "Suspicious", "Contains scam-related language or payment pressure."
    if author and score >= 2 and len(text.split()) >= 12:
        return "Likely authentic", "Public account and engagement signals support this label."
    return "Uncertain", "Public metadata is insufficient to verify authenticity."


def search_public_reviews(company: str, limit: int = 10) -> dict[str, Any]:
    company = company.strip()
    if len(company) < 2:
        raise ValueError("Enter a company name to search public reviews.")
    limit = max(1, min(int(limit), 20))
    url = (
        "https://www.reddit.com/search.json?q="
        f"{quote_plus(company + ' job review')}&type=link&sort=relevance&limit={limit}"
    )
    payload = _bounded_json_get(url, timeout=TIMEOUT_SECONDS)
    children = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
    reviews: list[dict[str, Any]] = []
    for child in children[:limit]:
        data = child.get("data", {}) if isinstance(child, dict) else {}
        title = str(data.get("title") or "").strip()
        body = str(data.get("selftext") or "").strip()
        text = "\n\n".join(part for part in (title, body) if part)
        if not text:
            continue
        score = int(data.get("score") or 0)
        author = str(data.get("author") or "")
        status, explanation = _review_status(text, score, author)
        permalink = str(data.get("permalink") or "")
        reviews.append({
            "id": str(data.get("id") or permalink),
            "title": title or "Public Reddit discussion",
            "text": body or title,
            "source": "Reddit",
            "subreddit": str(data.get("subreddit_name_prefixed") or ""),
            "author": author or "deleted",
            "score": score,
            "url": f"https://www.reddit.com{permalink}" if permalink.startswith("/") else "",
            "status": status,
            "status_explanation": explanation,
            "published_at": datetime.fromtimestamp(float(data["created_utc"]), timezone.utc).isoformat()
            if data.get("created_utc")
            else "",
        })
    return {"company": company, "reviews": reviews, "source": "Reddit public search"}
