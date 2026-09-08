"""Risk indicators for suspicious job application processes."""
import re
from urllib.parse import urlsplit

from src.company_analyzer import extract_emails


def analyze_application(text: str = "", application_url: str = "", contact_emails: list[str] | None = None) -> dict:
    """Return structured application indicators; unavailable data is explicit."""
    content = text or ""
    emails = contact_emails if contact_emails is not None else extract_emails(content)
    indicators = []

    def add(name, severity, description, evidence):
        indicators.append({"name": name, "severity": severity, "description": description, "evidence": evidence})

    patterns = [
        ("Telegram recruitment", "high", r"telegram", "Requests contact through Telegram."),
        ("WhatsApp-only recruitment", "high", r"whatsapp.*(?:only|exclusively)|only.*whatsapp", "Requires communication through WhatsApp only."),
        ("Payment request", "high", r"(?:pay|send|transfer)\s+(?:a\s+)?(?:fee|money)|registration fee|training fee|equipment fee|cryptocurrency|bitcoin", "Requests money, cryptocurrency, or a fee."),
        ("Sensitive information request", "high", r"bank details|bank account|credit card|social security|identity document", "Requests sensitive financial or identity information."),
        ("Off-platform communication", "medium", r"move (?:the )?conversation|contact me outside|outside (?:the )?platform", "Requests communication outside the official platform."),
    ]
    for name, severity, pattern, description in patterns:
        match = re.search(pattern, content, re.I)
        if match:
            add(name, severity, description, match.group(0))
    if emails and not application_url and re.search(r"apply|send.*resume|email", content, re.I):
        add("Email-only application", "low", "Application instructions rely on email without a supplied application page.", emails[0])
    if application_url:
        domain = urlsplit(application_url).hostname or ""
        if domain and re.search(r"(?:bit\.ly|tinyurl|forms\.gle|\.tk$|\.xyz$)", domain, re.I):
            add("Suspicious application domain", "medium", "The application link uses a shortener or higher-risk domain pattern.", domain)
    score = min(100, sum({"low": 20, "medium": 50, "high": 100}[item["severity"]] for item in indicators))
    return {
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 20 else "low",
        "information_available": bool(content.strip() or application_url or emails),
        "indicators": indicators,
    }
