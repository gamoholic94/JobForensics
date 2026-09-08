"""Transparent, non-probabilistic risk aggregation for job postings."""
import math
import re

DEFAULT_WEIGHTS = {"ml": 0.50, "domain": 0.15, "company": 0.10, "salary": 0.10, "application": 0.10, "content": 0.05}


def content_rules(text: str, company_present: bool = True) -> list[dict]:
    """Return evidence-based indicators; missing data is evaluated explicitly."""
    text = text or ""
    checks = [("payment_request", r"pay\s+(?:a\s+)?(?:fee|money)|send\s+(?:money|fee)", "Requests payment to apply or start.", "high"), ("sensitive_information", r"bank\s+account|credit\s+card|social\s+security", "Requests sensitive financial or identity information.", "high"), ("urgency", r"urgent(?:ly)?|immediate(?:ly)?|act\s+now", "Uses urgent hiring language.", "low"), ("messaging_app", r"telegram|whatsapp\s+only", "Directs applicants to an external messaging app.", "medium")]
    results = []
    for name, pattern, description, severity in checks:
        match = re.search(pattern, text, re.I)
        results.append({"name": name, "description": description, "severity": severity, "evidence": match.group(0) if match else "", "triggered": bool(match)})
    results.append({"name": "missing_company_information", "description": "Company information was not supplied.", "severity": "low", "evidence": "", "triggered": not company_present})
    return results


def aggregate_risk(ml_score: float | None = None, domain_score: float = 0, company_score: float = 0, salary_score: float = 0, application_score: float = 0, content_score: float = 0, weights: dict[str, float] | None = None) -> dict:
    """Combine finite 0-100 scores; weights are normalized and exposed."""
    scores = {"ml": 0 if ml_score is None else float(ml_score), "domain": float(domain_score), "company": float(company_score), "salary": float(salary_score), "application": float(application_score), "content": float(content_score)}
    if any(not math.isfinite(value) or value < 0 or value > 100 for value in scores.values()):
        raise ValueError("Risk scores must be finite numbers between 0 and 100")
    raw_weights = weights or DEFAULT_WEIGHTS
    if not raw_weights or any(not math.isfinite(float(value)) or value < 0 for value in raw_weights.values()):
        raise ValueError("Risk weights must be non-negative finite numbers")
    weight_total = sum(raw_weights.values())
    if not math.isfinite(weight_total) or weight_total <= 0:
        raise ValueError("Risk weights must have a positive finite total")
    normalized_weights = {key: value / weight_total for key, value in raw_weights.items()}
    overall = max(0, min(100, round(sum(scores[key] * normalized_weights.get(key, 0) for key in scores))))
    return {"overall_risk_score": overall, "risk_level": "High" if overall >= 70 else "Medium" if overall >= 40 else "Low", "component_scores": scores, "weights": normalized_weights}