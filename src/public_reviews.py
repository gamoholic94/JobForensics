"""Analyze review evidence supplied by the user without scraping review sites."""

from datetime import datetime, timezone
from typing import Any


def _review_status(text: str, score: int, author: str) -> tuple[str, str]:
    lower = text.lower()
    suspicious_terms = ("pay upfront", "send money", "telegram", "whatsapp", "crypto", "gift card")
    if any(term in lower for term in suspicious_terms):
        return "Suspicious", "Contains scam-related language or payment pressure."
    if author and score >= 2 and len(text.split()) >= 12:
        return "Likely authentic", "Public account and engagement signals support this label."
    return "Uncertain", "Public metadata is insufficient to verify authenticity."


def analyze_submitted_review(source: str, url: str, text: str) -> dict[str, Any]:
    source = source.strip()
    url = url.strip()
    text = text.strip()
    if not source:
        raise ValueError("Select the review platform.")
    if len(text) < 20:
        raise ValueError("Paste at least 20 characters of review text.")
    if url and not url.startswith(("http://", "https://")):
        raise ValueError("The review link must start with http:// or https://.")
    status, explanation = _review_status(text, 0, "")
    return {
        "id": f"submitted-{datetime.now(timezone.utc).timestamp()}",
        "title": f"Submitted {source} review",
        "text": text,
        "source": source,
        "url": url,
        "status": status,
        "status_explanation": explanation + " Source identity and authorship were not independently verified.",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
