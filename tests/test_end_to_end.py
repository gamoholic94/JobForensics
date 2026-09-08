import pandas as pd
from unittest.mock import patch

from src.model import build_pipeline
from src.predict import analyze_posting
from src.scraper import scrape_job


SUSPICIOUS_HTML = '''<script type="application/ld+json">{"@type":"JobPosting","title":"Work From Home Data Entry","description":"Urgently hiring. Guaranteed income. Pay a registration fee. Contact recruiter on Telegram.","hiringOrganization":{"name":"Example"}}</script>'''


def test_mocked_scrape_to_analysis_pipeline():
    rows = pd.DataFrame({"description": ["office role", "pay fee telegram"] * 3, "fraudulent": [0, 1] * 3})
    model = build_pipeline()
    model.fit(rows.drop(columns="fraudulent"), rows["fraudulent"])
    response = type("Response", (), {
        "status_code": 200, "headers": {"content-length": str(len(SUSPICIOUS_HTML))},
        "encoding": "utf-8", "iter_content": lambda self, chunk_size: [SUSPICIOUS_HTML.encode()],
        "raise_for_status": lambda self: None, "close": lambda self: None,
    })()
    with patch("src.scraper.requests.Session.get", return_value=response):
        scraped = scrape_job("https://example.com/jobs/1")
    result = analyze_posting(model, scraped["description"], scraped["url"], scraped, generate_xai=False)
    assert result["success"] is True
    assert result["job"]["title"] == "Work From Home Data Entry"
    assert result["application_analysis"]["risk_score"] > 0
    assert result["risk"]["overall_risk_score"] > 40
    assert "classification_details" in result
