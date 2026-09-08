"""Company and contact-domain consistency checks."""
import re
from urllib.parse import urlsplit

FREE_EMAIL_PROVIDERS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com"}
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")


def extract_emails(text: str) -> list[str]:
    """Extract unique email addresses without retaining message content."""
    return sorted(set(EMAIL_PATTERN.findall(text or "")))


def analyze_company(company_name: str = "", website: str = "", text: str = "", profile: str = "", job_domain: str = "") -> dict:
    """Compare company fields and contact domains without treating gaps as proof."""
    emails = extract_emails(text)
    website_domain = (urlsplit(website).hostname or "").lower() if website else ""
    email_domains = sorted({email.rsplit("@", 1)[1].lower() for email in emails})
    warnings = []
    email_types = {}
    for domain in email_domains:
        email_types[domain] = "free provider" if domain in FREE_EMAIL_PROVIDERS else "domain email"
        if website_domain and domain in FREE_EMAIL_PROVIDERS:
            warnings.append("Contact email uses a free provider rather than the apparent company domain.")
        elif website_domain and domain != website_domain and not website_domain.endswith("." + domain):
            warnings.append("Contact email domain does not match the apparent company domain.")
    missing_fields = []
    if not company_name.strip():
        missing_fields.append("company name")
    if not profile.strip():
        missing_fields.append("company profile")
    if not website_domain:
        missing_fields.append("company website")
    if not emails:
        missing_fields.append("contact email")
    if missing_fields:
        warnings.append("Limited company information was provided: " + ", ".join(missing_fields) + ".")
    if website_domain and job_domain and website_domain != job_domain and not website_domain.endswith("." + job_domain):
        warnings.append("Company website domain differs from the job-page domain.")
    mismatch = any("does not match" in warning or "differs" in warning for warning in warnings)
    risk_score = min(100, (20 if missing_fields else 0) + (30 if mismatch else 0))
    return {
        "company_name": company_name or "Unavailable",
        "website_domain": website_domain or "Unavailable",
        "contact_emails": emails,
        "email_types": email_types,
        "company_profile_present": bool(profile.strip()),
        "company_website_present": bool(website_domain),
        "contact_email_present": bool(emails),
        "missing_fields": missing_fields,
        "risk_score": risk_score,
        "risk_level": "high" if risk_score >= 70 else "medium" if risk_score >= 20 else "low",
        "warnings": sorted(set(warnings)),
    }
