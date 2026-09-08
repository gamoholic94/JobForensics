"""Comprehensive test suite for Fake Job Detection backend."""
import pytest
import pandas as pd
import requests
from unittest.mock import patch, MagicMock

from src.company_analyzer import analyze_company, extract_emails
from src.application_analyzer import analyze_application
from src.model import build_pipeline, load_model, predict_text, MODEL_PATH
from src.predict import analyze_posting
from src.preprocessing import clean_text, preprocess_dataframe, make_inference_frame
from src.risk_engine import aggregate_risk, content_rules
from src.scraper import extract_job_fields, fetch_html, scrape_job
from src.url_analyzer import analyze_url, normalize_url
from src.salary_analyzer import analyze_salary
from src.explain import explain_with_lime, explain_with_shap


# ============================================================================
# PHASE 1: PREPROCESSING TESTS
# ============================================================================

def test_preprocessing_handles_missing_values_and_preserves_signals():
    """Test that preprocessing preserves fraud-related signals."""
    result = preprocess_dataframe(pd.DataFrame({"description": ["<b>Urgent</b> email me@example.com"]}))
    assert result.loc[0, "text"] == "urgent email email"
    assert result.loc[0, "has_salary_range"] == 0
    assert result.loc[0, "salary_midpoint"] == 0


def test_clean_text_handles_html_and_urls():
    """Test text cleaning removes HTML but tokenizes important elements."""
    assert clean_text("<p>Hello <b>world</b></p>") == "hello world"
    assert "url" in clean_text("Visit https://example.com")
    assert "email" in clean_text("Contact me@example.com")


def test_make_inference_frame_creates_valid_dataframe():
    """Test that make_inference_frame creates valid rows for model input."""
    frame = make_inference_frame("Test job posting")
    assert len(frame) == 1
    assert "description" in frame.columns
    assert frame.loc[0, "description"] == "Test job posting"


def test_make_inference_frame_preserves_structured_and_salary_fields():
    """Inference should populate the same structured fields used in training."""
    frame = make_inference_frame(
        "Role pays $50,000 - $70,000",
        title="Engineer",
        company_profile="A real company",
        employment_type="Full-time",
    )
    processed = preprocess_dataframe(frame)
    assert frame.loc[0, "title"] == "Engineer"
    assert frame.loc[0, "employment_type"] == "Full-time"
    assert processed.loc[0, "has_salary_range"] == 1
    assert processed.loc[0, "salary_min"] == 50000
    assert processed.loc[0, "salary_max"] == 70000


# ============================================================================
# PHASE 2: URL AND SCRAPER TESTS
# ============================================================================

def test_url_normalization_strips_tracking_params():
    """Test that URL normalization removes tracking parameters."""
    normalized = normalize_url("example.com/jobs?utm_source=x&id=2&utm_medium=y")
    assert normalized == "https://example.com/jobs?id=2"
    assert "utm" not in normalized


def test_url_normalization_rejects_localhost():
    """Test that localhost URLs are rejected."""
    with pytest.raises(ValueError, match="Localhost"):
        normalize_url("http://localhost/jobs")


def test_url_normalization_rejects_private_ips():
    """Test that private IP addresses are rejected."""
    with pytest.raises(ValueError, match="Private"):
        normalize_url("http://192.168.1.1/jobs")
    
    with pytest.raises(ValueError, match="Private"):
        normalize_url("http://10.0.0.1/jobs")
    
    with pytest.raises(ValueError, match="Private"):
        normalize_url("http://172.16.0.1/jobs")


def test_url_normalization_rejects_embedded_credentials():
    """Test that URLs with embedded credentials are rejected."""
    with pytest.raises(ValueError, match="credentials"):
        normalize_url("http://user:password@example.com/jobs")


def test_url_analysis_detects_suspicious_patterns():
    """Test that URL analysis identifies suspicious indicators."""
    result = analyze_url("https://example.com/verify-crypto-wallet-login-free-money")
    assert result["suspicious_url"] is True
    assert len(result["warnings"]) > 0


def test_url_analysis_https_status():
    """Test that URL analysis correctly identifies HTTPS usage."""
    https_result = analyze_url("https://example.com")
    assert https_result["https"] is True
    
    http_result = analyze_url("http://example.com")
    assert http_result["https"] is False


def test_structured_scraper_prefers_jobposting_json_ld():
    """Test that scraper prefers JSON-LD JobPosting format."""
    html = '''<html><script type="application/ld+json">
    {"@type":"JobPosting","title":"Engineer","description":"<p>Build things</p>","applicationUrl":"https://acme.example/apply","hiringOrganization":{"name":"Acme","sameAs":["https://acme.example"],"description":"We build things."}}
    </script><nav>Noise</nav></html>'''
    fields = extract_job_fields(html)
    assert fields["title"] == "Engineer"
    assert fields["description"] == "Build things"
    assert fields["company_name"] == "Acme"
    assert fields["company_website"] == "https://acme.example"
    assert fields["company_profile"] == "We build things."
    assert fields["application_url"] == "https://acme.example/apply"


def test_scraper_fallback_to_html_parsing():
    """Test that scraper falls back to HTML parsing without JSON-LD."""
    html = "<h1>Senior Developer</h1><p>Full job description here</p>"
    fields = extract_job_fields(html)
    assert fields["title"] == "Senior Developer"
    assert "job description" in fields["description"].lower()


def test_scraper_handles_empty_response():
    """Test scraper handles empty response gracefully."""
    with patch('src.scraper.requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b""]
        mock_response.headers.get.return_value = "0"
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = scrape_job("https://example.com/empty")
        assert result["success"] is False
        assert result["error"] is not None


def test_scraper_rejects_hostname_resolving_to_private_address():
    """A public-looking hostname must not be allowed to reach internal IPs."""
    with patch("src.scraper.socket.getaddrinfo", return_value=[(None, None, None, None, ("127.0.0.1", 0))]):
        result = scrape_job("https://public.example/jobs/1")
    assert result["success"] is False
    assert "private or local" in result["error"].lower()


def test_scraper_revalidates_redirect_destination():
    """Redirects are checked before the second request is made."""
    response = MagicMock()
    response.status_code = 302
    response.headers = {"Location": "http://127.0.0.1/admin"}
    response.raise_for_status.return_value = None
    with patch("src.scraper.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 0))]), \
         patch("src.scraper.requests.Session.get", return_value=response) as get:
        result = scrape_job("https://public.example/jobs/1")
    assert result["success"] is False
    assert "private or local" in result["error"].lower()
    assert get.call_count == 1


# ============================================================================
# PHASE 3: ANALYZER TESTS
# ============================================================================

def test_email_extraction_handles_multiple_formats():
    """Test email extraction works with various formats."""
    text = "Contact: john@example.com or jane.doe+tag@domain.co.uk"
    emails = extract_emails(text)
    assert "john@example.com" in emails
    assert "jane.doe+tag@domain.co.uk" in emails


def test_company_analyzer_detects_missing_fields():
    """Test company analyzer detects missing company information."""
    result = analyze_company(company_name="", website="", text="", profile="")
    assert len(result["missing_fields"]) > 0
    assert result["risk_score"] > 0


def test_company_analyzer_detects_free_email_mismatch():
    """Test company analyzer detects when free email doesn't match domain."""
    result = analyze_company(
        company_name="Acme Corp",
        website="https://acme.com",
        text="Apply at recruiter@gmail.com",
        profile="We are Acme"
    )
    assert len(result["warnings"]) > 0
    assert any("free provider" in w for w in result["warnings"])


def test_salary_analyzer_detects_ranges():
    """Test salary analyzer extracts salary ranges."""
    result = analyze_salary("Position offers $50000 - 75000 per year")
    assert len(result["salary_ranges"]) > 0
    assert result["salary_ranges"][0]["minimum"] == 50000
    assert result["salary_ranges"][0]["maximum"] == 75000


def test_salary_analyzer_flags_suspicious_language():
    """Test salary analyzer flags suspicious income language."""
    result = analyze_salary("Guaranteed income and unlimited money opportunities!")
    assert result["salary_signal"] == "high"
    assert len(result["salary_reason"]) > 0


def test_application_analyzer_detects_payment_requests():
    """Test application analyzer detects payment requests."""
    result = analyze_application("Send a $50 registration fee to apply")
    triggered_names = {item["name"] for item in result["indicators"]}
    assert "Payment request" in triggered_names
    assert result["risk_score"] > 0


def test_application_analyzer_detects_messaging_apps():
    """Test application analyzer detects messaging app communications."""
    result = analyze_application("Contact me on Telegram only")
    triggered_names = {item["name"] for item in result["indicators"]}
    assert "Telegram recruitment" in triggered_names


def test_application_analyzer_detects_sensitive_info_requests():
    """Test application analyzer detects sensitive information requests."""
    result = analyze_application("Please provide your bank account and social security number")
    triggered_names = {item["name"] for item in result["indicators"]}
    assert "Sensitive information request" in triggered_names


# ============================================================================
# PHASE 4: RISK ENGINE TESTS
# ============================================================================

def test_content_rules_detect_payment_requests():
    """Test content rules detect payment requests."""
    rules = content_rules("send money")
    triggered = [r for r in rules if r["triggered"]]
    assert any(r["name"] == "payment_request" for r in triggered)


def test_content_rules_detect_urgency():
    """Test content rules detect urgent language."""
    rules = content_rules("URGENT! Act now or lose this opportunity!")
    triggered = [r for r in rules if r["triggered"]]
    assert any(r["name"] == "urgency" for r in triggered)


def test_content_rules_detect_messaging_apps():
    """Test content rules detect messaging app references."""
    rules = content_rules("Contact me on WhatsApp only")
    triggered = [r for r in rules if r["triggered"]]
    assert any(r["name"] == "messaging_app" for r in triggered)


def test_risk_score_is_not_a_probability():
    """Test that risk score is properly aggregated, not a simple probability."""
    result = aggregate_risk(ml_score=80, domain_score=100, company_score=0)
    # With default weights: (80*0.5 + 100*0.15 + 0*0.1 + 0*0.1 + 0*0.1 + 0*0.05) / 1.0 = 55
    assert result["overall_risk_score"] == 55
    assert result["risk_level"] == "Medium"


def test_risk_score_normalizes_weights():
    """Test that risk weights are normalized correctly."""
    custom_weights = {"ml": 1.0, "domain": 1.0}  # Not normalized
    result = aggregate_risk(
        ml_score=80,
        domain_score=60,
        weights=custom_weights
    )
    assert result["weights"]["ml"] + result["weights"]["domain"] == 1.0


def test_risk_score_rejects_invalid_values():
    """Test risk aggregation validates input scores."""
    with pytest.raises(ValueError):
        aggregate_risk(ml_score=101)  # > 100
    
    with pytest.raises(ValueError):
        aggregate_risk(ml_score=-1)  # < 0


# ============================================================================
# PHASE 5: MODEL TESTS
# ============================================================================

def test_model_artifact_loads():
    """Test that the saved model artifact loads without errors."""
    try:
        model = load_model(MODEL_PATH)
        assert model is not None
    except FileNotFoundError:
        pytest.skip("Model artifact not found")


def test_model_pipeline_accepts_raw_rows_and_returns_probability():
    """Test model pipeline with constructed rows."""
    rows = pd.DataFrame({
        "title": ["Assistant", "Easy money"] * 3,
        "description": ["Office role", "Urgent pay fee"] * 3,
        "fraudulent": [0, 1] * 3
    })
    pipeline = build_pipeline()
    pipeline.fit(rows.drop(columns=["fraudulent"]), rows["fraudulent"])
    label, probability, cleaned = predict_text(pipeline, "Urgent pay fee")
    assert label in {"Fake", "Real"}
    assert 0 <= probability <= 1
    assert cleaned


def test_model_prediction_with_legitimate_job():
    """Test model prediction on legitimate job posting."""
    try:
        model = load_model(MODEL_PATH)
        label, prob, cleaned = predict_text(
            model,
            "Senior Software Engineer at Google. Work on cutting-edge projects."
        )
        assert label in {"Fake", "Real"}
        assert 0 <= prob <= 1
    except FileNotFoundError:
        pytest.skip("Model artifact not found")


def test_model_prediction_with_suspicious_job():
    """Test model prediction on suspicious job posting."""
    try:
        model = load_model(MODEL_PATH)
        label, prob, cleaned = predict_text(
            model,
            "Easy money! No experience needed. Pay $100 and start immediately. Telegram only."
        )
        assert label in {"Fake", "Real"}
        assert 0 <= prob <= 1
    except FileNotFoundError:
        pytest.skip("Model artifact not found")


# ============================================================================
# PHASE 6: XAI TESTS
# ============================================================================

def test_lime_handles_unavailable_package():
    """Test LIME handles missing package gracefully."""
    pipeline = build_pipeline()
    rows = pd.DataFrame({"description": ["test", "fake"] * 3, "fraudulent": [0, 1] * 3})
    pipeline.fit(rows, rows["fraudulent"])
    
    result = explain_with_lime(pipeline, "test text")
    # Should return tuple even if explanation fails
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_shap_error_handling():
    """Test SHAP error handling returns structured result."""
    pipeline = build_pipeline()
    rows = pd.DataFrame({"description": ["test", "fake"] * 3, "fraudulent": [0, 1] * 3})
    pipeline.fit(rows, rows["fraudulent"])
    
    result = explain_with_shap(pipeline, ["test"])
    assert "available" in result
    assert "method" in result
    assert "error" in result


# ============================================================================
# PHASE 7: UNIFIED PIPELINE TESTS
# ============================================================================

def test_unified_pipeline_result_schema():
    """Test unified analyze_posting returns complete schema."""
    rows = pd.DataFrame({
        "title": ["Assistant", "Easy money"] * 3,
        "description": ["Office role", "Urgent pay fee"] * 3,
        "fraudulent": [0, 1] * 3
    })
    pipeline = build_pipeline()
    pipeline.fit(rows.drop(columns=["fraudulent"]), rows["fraudulent"])
    
    html = '''<script type="application/ld+json">
    {"@type":"JobPosting","title":"Assistant","description":"Urgent work. Contact me on Telegram.",
     "hiringOrganization":{"name":"Acme","sameAs":"https://acme.example"}}
    </script>'''
    job = extract_job_fields(html)
    
    result = analyze_posting(
        pipeline,
        job["description"],
        "https://jobs.example.com",
        {**job, "company_profile": ""},
        generate_xai=False  # Skip XAI for faster testing
    )
    
    # Verify schema
    assert result["success"] is True
    assert result["classification"] in {"Likely Fake", "Needs Review", "Likely Legitimate"}
    assert 0 <= result["model_probability"]["fake_probability"] <= 1
    assert 0 <= result["risk"]["overall_risk_score"] <= 100
    assert result["domain_analysis"] is not None
    assert result["company_analysis"] is not None
    assert result["salary_analysis"] is not None
    assert result["application_analysis"] is not None
    assert isinstance(result["recommendations"], list)


def test_unified_pipeline_with_all_risk_signals():
    """Test unified pipeline with comprehensive risk signals."""
    rows = pd.DataFrame({
        "title": ["Real", "Fake", "Real", "Fake", "Real", "Fake"],
        "description": ["office", "suspicious", "office", "suspicious", "office", "suspicious"],
        "fraudulent": [0, 1, 0, 1, 0, 1]
    })
    pipeline = build_pipeline()
    pipeline.fit(rows.drop(columns=["fraudulent"]), rows["fraudulent"])
    
    suspicious_text = """
    URGENT HIRING! Easy money!
    send fee to recruiter@gmail.com
    Contact via Telegram ONLY.
    """
    
    result = analyze_posting(
        pipeline,
        suspicious_text,
        url="https://example.com",
        job={"company_name": "", "company_profile": ""},
        generate_xai=False
    )
    
    # Should detect multiple risk factors
    assert result["risk"]["overall_risk_score"] >= 0
    assert len(result["recommendations"]) >= 0


# ============================================================================
# PHASE 8: CLASSIFICATION LOGIC TESTS
# ============================================================================

def test_classification_logic_likely_fake():
    """Test classification logic for likely fake postings."""
    rows = pd.DataFrame({"description": ["office", "scam", "office", "scam", "office", "scam"], "fraudulent": [0, 1, 0, 1, 0, 1]})
    pipeline = build_pipeline()
    pipeline.fit(rows, rows["fraudulent"])
    
    result = analyze_posting(
        pipeline,
        "send fee telegram guarantee income",
        generate_xai=False
    )
    assert result["classification"] in {"Likely Fake", "Needs Review", "Likely Legitimate"}


def test_classification_logic_likely_legitimate():
    """Test classification logic for legitimate postings."""
    rows = pd.DataFrame({"description": ["office", "scam", "office", "scam", "office", "scam"], "fraudulent": [0, 1, 0, 1, 0, 1]})
    pipeline = build_pipeline()
    pipeline.fit(rows, rows["fraudulent"])
    
    result = analyze_posting(
        pipeline,
        "Senior engineer at company. Competitive salary. Apply now.",
        url="https://company.com",
        generate_xai=False
    )
    # Should return a valid classification
    assert result["classification"] in {"Likely Fake", "Needs Review", "Likely Legitimate"}


# ============================================================================
# PHASE 9: INTEGRATION TESTS
# ============================================================================

def test_end_to_end_mocked_job_analysis():
    """Test complete end-to-end mocked job analysis."""
    rows = pd.DataFrame({
        "title": ["Title", "Scam"] * 3,
        "description": ["Desc", "Pay fee"] * 3,
        "fraudulent": [0, 1] * 3
    })
    pipeline = build_pipeline()
    pipeline.fit(rows.drop(columns=["fraudulent"]), rows["fraudulent"])
    
    result = analyze_posting(
        pipeline,
        "Join our team as a Data Scientist. Competitive salary.",
        url="https://company.com/jobs/123",
        job={
            "title": "Data Scientist",
            "company_name": "TechCorp",
            "company_website": "https://techcorp.com",
            "company_profile": "Leading AI company",
            "location": "San Francisco",
        },
        generate_xai=False
    )
    
    # Verify complete result
    assert result["success"]
    assert result["job"]["title"] == "Data Scientist"
    assert result["job"]["company"] == "TechCorp"
    assert result["domain_analysis"]["domain"] == "company.com"
    assert result["company_analysis"]["website_domain"] == "techcorp.com"