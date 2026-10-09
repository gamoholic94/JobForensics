import pytest
from fastapi.testclient import TestClient

from api_server import app
from src.investigations import (
    get_investigation,
    investigation_flag_counts,
    investigation_report,
    list_investigations,
    save_investigation,
)

client = TestClient(app)


def test_investigation_store_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFORENSICS_DATABASE_PATH", str(tmp_path / "investigations.sqlite3"))
    result = {
        "success": True,
        "classification": "Needs Review",
        "job": {
            "title": "Engineer",
            "company": "Acme",
            "source_url": "https://example.com/jobs/1",
        },
        "risk": {"overall_risk_score": 42},
    }

    saved = save_investigation(result)
    assert saved["title"] == "Engineer"
    assert saved["overall_risk_score"] == 42
    assert list_investigations() == [{
        "id": saved["id"],
        "created_at": saved["created_at"],
        "source_url": "https://example.com/jobs/1",
        "title": "Engineer",
        "company": "Acme",
        "classification": "Needs Review",
        "overall_risk_score": 42.0,
    }]

    loaded = get_investigation(saved["id"])
    assert loaded is not None
    assert loaded["result"] == result
    report = investigation_report(saved["id"])
    assert report is not None
    assert "registration" not in report
    assert "Engineer" in report


def test_investigation_store_rejects_unsuccessful_result(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFORENSICS_DATABASE_PATH", str(tmp_path / "investigations.sqlite3"))
    with pytest.raises(ValueError, match="successful analysis"):
        save_investigation({"success": False})


def test_investigation_flag_counts_aggregate_triggered_indicators(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFORENSICS_DATABASE_PATH", str(tmp_path / "investigations.sqlite3"))
    base_result = {
        "success": True,
        "classification": "Needs Review",
        "job": {"title": "Engineer", "company": "Acme"},
        "risk": {"overall_risk_score": 42},
        "content_risk": {
            "rules": [
                {"name": "Upfront payment request", "triggered": True},
                {"name": "Untriggered rule", "triggered": False},
            ]
        },
        "application_analysis": {
            "indicators": [{"name": "External messaging app"}],
        },
    }
    save_investigation(base_result)
    save_investigation({**base_result, "job": {"title": "Designer", "company": "Beta"}})

    assert investigation_flag_counts() == [
        {"name": "External messaging app", "count": 2, "percentage": 100},
        {"name": "Upfront payment request", "count": 2, "percentage": 100},
    ]


def test_investigation_api_exposes_stats_and_html_report(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBFORENSICS_DATABASE_PATH", str(tmp_path / "investigations.sqlite3"))
    result = {
        "success": True,
        "classification": "Likely Legitimate",
        "job": {"title": "Analyst", "company": "Acme"},
        "risk": {"overall_risk_score": 8},
        "content_risk": {"rules": [{"name": "Unusual request", "triggered": True}]},
    }

    created = client.post("/investigations", json={"result": result})
    assert created.status_code == 200
    investigation_id = created.json()["id"]

    stats = client.get("/investigations/stats")
    assert stats.status_code == 200
    assert stats.json()["red_flags"] == [
        {"name": "Unusual request", "count": 1, "percentage": 100}
    ]

    report = client.get(f"/investigations/{investigation_id}/report")
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/html")
    assert f'jobforensics-{investigation_id}.html' in report.headers["content-disposition"]
    assert "Analyst" in report.text
