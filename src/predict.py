"""Unified backend inference result for a scraped or supplied job posting."""
from src.application_analyzer import analyze_application
from src.company_analyzer import analyze_company
from src.explain import explain_with_lime, explain_with_shap, top_shap_features_for_instance
from src.model import predict_text
from src.risk_engine import aggregate_risk, content_rules
from src.salary_analyzer import analyze_salary
from src.url_analyzer import analyze_url


def _generate_recommendations(analysis_results: dict) -> list[str]:
    """Generate actionable recommendations based on detected risks and signals."""
    recommendations = []
    
    # Domain-based recommendations
    if analysis_results.get("domain_analysis", {}).get("suspicious_url"):
        recommendations.append("Verify the job posting on the company's official website.")
    if not analysis_results.get("domain_analysis", {}).get("https"):
        recommendations.append("The job posting is not served over HTTPS. Exercise caution.")
    
    # Company-based recommendations
    company = analysis_results.get("company_analysis", {})
    if company.get("missing_fields"):
        recommendations.append("Limited company information is provided. Independently verify the employer.")
    if any("mismatch" in w.lower() or "differs" in w.lower() for w in company.get("warnings", [])):
        recommendations.append("The recruiter's email domain does not match the company website. Verify independently.")
    
    # Application-based recommendations
    app = analysis_results.get("application_analysis", {})
    app_indicators = app.get("indicators", [])
    
    if any(ind["name"] == "Payment request" for ind in app_indicators):
        recommendations.append("Do not send money, fees, or cryptocurrency to apply for this position.")
    
    if any("Telegram" in ind["name"] or "WhatsApp" in ind["name"] for ind in app_indicators):
        recommendations.append("Verify the employer through its official website before communicating on messaging apps.")
    
    if any("Sensitive information" in ind["name"] for ind in app_indicators):
        recommendations.append("Do not provide banking details, social security numbers, or identity documents until you verify the employer.")
    
    if any("Suspicious application domain" in ind["name"] for ind in app_indicators):
        recommendations.append("The application link uses a URL shortener or unusual domain. Verify the link before submitting information.")
    
    # Salary-based recommendations
    salary = analysis_results.get("salary_analysis", {})
    if any("unrealistic" in str(r).lower() or "guaranteed" in str(r).lower() for r in salary.get("salary_reason", [])):
        recommendations.append("The salary promises seem unusually generous. Verify independently.")
    
    # Content-based recommendations  
    content_risk = analysis_results.get("content_risk", {})
    triggered_rules = [r for r in content_risk.get("rules", []) if r.get("triggered")]
    
    if any(r["name"] == "urgency" for r in triggered_rules):
        recommendations.append("The posting uses urgent language. Take time to verify before responding.")
    
    # Classification-based recommendations
    classification = analysis_results.get("classification", "")
    if classification == "Likely Fake":
        recommendations.append("This posting shows multiple warning signs of a fraudulent job posting. Avoid responding.")
    elif classification == "Needs Review":
        recommendations.append("This posting has both legitimate and suspicious indicators. Research the company before proceeding.")
    
    return sorted(list(set(recommendations)))  # Remove duplicates


def analyze_posting(model, text: str, url: str = "", job: dict | None = None, 
                   generate_xai: bool = True) -> dict:
    """
    Run model and external indicators through one stable result schema.
    
    Args:
        model: Trained sklearn pipeline
        text: Job posting description/text
        url: Optional job posting URL for domain analysis
        job: Optional dict with structured job fields (title, company_name, etc.)
        generate_xai: Whether to generate XAI explanations (LIME/SHAP)
    
    Returns:
        Unified analysis result dict with classification, scores, analyses, and recommendations
    """
    job = job or {}
    
    # 1. ML Model Prediction
    label, fake_probability, cleaned = predict_text(model, text, fields=job)
    
    # 2. URL Analysis
    domain = {}
    if url:
        try:
            domain = analyze_url(url)
        except ValueError as e:
            domain = {"domain": "Invalid URL", "https": False, "warnings": [str(e)], "suspicious_url": True}
    else:
        domain = {"domain": "Unavailable", "https": False, "warnings": [], "suspicious_url": False}
    
    # 3. Company Analysis
    company = analyze_company(
        job.get("company_name", ""), 
        job.get("company_website", ""), 
        text,
        job.get("company_profile", ""), 
        domain.get("domain", ""),
    )
    
    # 4. Salary Analysis
    salary = analyze_salary(text)
    
    # 5. Application Analysis
    application = analyze_application(
        text, 
        job.get("application_url", ""), 
        company.get("contact_emails", [])
    )
    
    # 6. Content Rules
    rules = content_rules(text, company_present=not company.get("missing_fields", []))
    
    # 7. Risk Aggregation
    # Calculate content score from triggered rules
    content_score = min(100, sum(
        {"low": 20, "medium": 50, "high": 100}[rule["severity"]] 
        for rule in rules if rule.get("triggered")
    ))
    
    risk = aggregate_risk(
        ml_score=fake_probability * 100,
        domain_score=100 if domain.get("suspicious_url") else (50 if not domain.get("https") else 0),
        company_score=company.get("risk_score", 0),
        salary_score=100 if salary.get("salary_signal") == "high" else (50 if salary.get("salary_signal") == "medium" else 0),
        application_score=application.get("risk_score", 0),
        content_score=content_score,
    )
    
    # 8. Classification Logic
    ml_prob = fake_probability
    overall_risk = risk.get("overall_risk_score", 50)
    
    if ml_prob >= 0.7 or (ml_prob >= 0.5 and overall_risk >= 70):
        classification = "Likely Fake"
    elif ml_prob <= 0.3 and overall_risk <= 40:
        classification = "Likely Legitimate"
    else:
        classification = "Needs Review"
    
    # 9. Build base result
    result = {
        "success": True,
        "classification": classification,
        "classification_details": {
            "label": classification,
            "model_fake_probability": fake_probability,
        },
        "model_probability": {
            "fake_probability": fake_probability,
            "label": label,
            "description": f"Model trained on EMSCAD dataset estimates {fake_probability*100:.1f}% probability this posting is fraudulent."
        },
        "risk": risk,
        "job": {
            "title": job.get("title", "Unavailable"),
            "company": job.get("company_name", "Unavailable"),
            "location": job.get("location", "Unavailable"),
            "employment_type": job.get("employment_type", "Unavailable"),
        },
        "domain_analysis": domain,
        "company_analysis": company,
        "salary_analysis": salary,
        "application_analysis": application,
        "content_risk": {"rules": rules},
        "model_explanation": {
            "cleaned_text": cleaned,
            "label": label,
        },
    }
    
    # 10. Generate Recommendations
    result["recommendations"] = _generate_recommendations(result)
    
    # 11. Generate XAI Explanations (with error handling)
    xai_explanations = {}
    if generate_xai:
        try:
            lime_list, _ = explain_with_lime(model, cleaned, num_features=10)
            xai_explanations["lime"] = {
                "available": bool(lime_list),
                "method": "LIME",
                "features": lime_list,
                "error": None,
            }
        except Exception as e:
            xai_explanations["lime"] = {
                "available": False,
                "method": "LIME",
                "features": [],
                "error": str(e),
            }
        
        try:
            shap_result = explain_with_shap(model, [cleaned])
            shap_features = top_shap_features_for_instance(shap_result, top_n=10)
            if shap_result.get("available") and shap_features:
                xai_explanations["shap"] = {
                    "available": True,
                    "method": "SHAP",
                    "features": shap_features,
                    "error": None,
                }
            else:
                xai_explanations["shap"] = {
                    "available": False,
                    "method": "SHAP",
                    "features": [],
                    "error": shap_result.get("error") or "SHAP returned no usable feature contributions",
                }
        except Exception as e:
            xai_explanations["shap"] = {
                "available": False,
                "method": "SHAP",
                "features": [],
                "error": str(e),
            }
    
    result["explanations"] = xai_explanations
    
    return result
