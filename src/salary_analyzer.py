"""Conservative salary signal extraction; missing context is never fabricated."""
import re

SALARY_PATTERN = re.compile(r"(?P<currency>[$€£]|usd|eur|gbp)?\s*(?P<low>\d[\d,.]*)\s*(?:-|to|–)\s*(?P<high>\d[\d,.]*)", re.I)


def analyze_salary(text: str) -> dict:
    """Extract stated ranges and flag only explicit high-risk wording."""
    raw = text or ""
    matches = list(SALARY_PATTERN.finditer(raw))
    ranges = []
    for match in matches:
        ranges.append({
            "currency": (match.group("currency") or "Unavailable").upper(),
            "minimum": float(match.group("low").replace(",", "")),
            "maximum": float(match.group("high").replace(",", "")),
        })
    reasons = []
    if re.search(r"guaranteed\s+(?:income|salary)|unlimited\s+income|easy\s+money", raw, re.I):
        reasons.append("The posting uses unusually strong income promises.")
    if re.search(r"commission[- ]only|pay\s+to\s+(?:apply|start)|send\s+(?:money|fee)", raw, re.I):
        reasons.append("The posting mentions commission-only work or requesting payment.")
    return {
        "salary_ranges": ranges,
        "salary_signal": "high" if reasons else ("medium" if ranges else "Unavailable"),
        "salary_reason": reasons or ["Unavailable"],
    }
