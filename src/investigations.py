"""SQLite-backed storage for reproducible job investigations."""

import json
from html import escape
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "jobforensics.sqlite3"


def _database_path() -> Path:
    configured = os.getenv("JOBFORENSICS_DATABASE_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_DATABASE_PATH


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            source_url TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            company TEXT NOT NULL DEFAULT '',
            classification TEXT NOT NULL,
            overall_risk_score REAL,
            result_json TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    job = result.get("job") or {}
    risk = result.get("risk") or {}
    return {
        "source_url": str(job.get("source_url") or ""),
        "title": str(job.get("title") or ""),
        "company": str(job.get("company") or ""),
        "classification": str(result.get("classification") or "Needs Review"),
        "overall_risk_score": risk.get("overall_risk_score"),
    }


def save_investigation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or not result.get("success"):
        raise ValueError("A successful analysis result is required")
    investigation_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    summary = _summary(result)
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO investigations
                (id, created_at, source_url, title, company, classification,
                 overall_risk_score, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                investigation_id,
                created_at,
                summary["source_url"],
                summary["title"],
                summary["company"],
                summary["classification"],
                summary["overall_risk_score"],
                json.dumps(result, separators=(",", ":"), ensure_ascii=True),
            ),
        )
    return {
        "id": investigation_id,
        "created_at": created_at,
        **summary,
    }


def list_investigations(limit: int = 50) -> list[dict[str, Any]]:
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, source_url, title, company, classification,
                   overall_risk_score
            FROM investigations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def investigation_flag_counts(limit: int = 100) -> list[dict[str, Any]]:
    """Aggregate triggered rule/application indicators from saved results."""
    counts: dict[str, int] = {}
    with _connect() as connection:
        rows = connection.execute(
            "SELECT result_json FROM investigations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    for row in rows:
        result = json.loads(row["result_json"])
        indicators = [
            rule for rule in (result.get("content_risk") or {}).get("rules", [])
            if rule.get("triggered")
        ]
        indicators.extend((result.get("application_analysis") or {}).get("indicators", []))
        for indicator in indicators:
            name = str(indicator.get("name") or "Uncategorized indicator")
            counts[name] = counts.get(name, 0) + 1
    total = len(rows)
    return [
        {"name": name, "count": count, "percentage": round(count / total * 100) if total else 0}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ][:5]


def get_investigation(investigation_id: str) -> dict[str, Any] | None:
    if not investigation_id.strip():
        raise ValueError("Investigation ID is required")
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, created_at, result_json FROM investigations WHERE id = ?",
            (investigation_id,),
        ).fetchone()
    if row is None:
        return None
    result = json.loads(row["result_json"])
    return {"id": row["id"], "created_at": row["created_at"], "result": result}


def investigation_report(investigation_id: str) -> str | None:
    stored = get_investigation(investigation_id)
    if stored is None:
        return None
    result = stored["result"]
    job = result.get("job") or {}
    risk = result.get("risk") or {}
    rules = (result.get("content_risk") or {}).get("rules") or []
    recommendations = result.get("recommendations") or []
    rows = "".join(
        f"<tr><th>{escape(str(key).replace('_', ' ').title())}</th><td>{escape(str(value or 'Unavailable'))}</td></tr>"
        for key, value in (
            ("Title", job.get("title")),
            ("Company", job.get("company")),
            ("Location", job.get("location")),
            ("Employment type", job.get("employment_type")),
            ("Source URL", job.get("source_url")),
            ("Source platform", job.get("source_platform")),
            ("Analyzed at", stored["created_at"]),
        )
    )
    signal_rows = "".join(
        f"<tr><th>{escape(str(key).title())}</th><td>{escape(str(value))}/100</td></tr>"
        for key, value in (risk.get("component_scores") or {}).items()
    )
    rule_items = "".join(
        f"<li><strong>{escape(str(rule.get('name', 'Indicator')))}</strong>: "
        f"{escape(str(rule.get('description', '')))}"
        f"{' Evidence: ' + escape(str(rule.get('evidence'))) if rule.get('evidence') else ''}</li>"
        for rule in rules
        if rule.get("triggered")
    ) or "<li>No content rules were triggered.</li>"
    recommendation_items = "".join(f"<li>{escape(str(item))}</li>" for item in recommendations) or "<li>No recommendations recorded.</li>"
    title = escape(str(job.get("title") or "Job investigation"))
    classification = escape(str(result.get("classification") or "Needs Review"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title} - JobForensics report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;color:#172033;line-height:1.5}}
h1{{margin-bottom:4px}}h2{{border-bottom:1px solid #d8dee9;padding-bottom:6px;margin-top:30px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8dee9;padding:8px;text-align:left;vertical-align:top}}
th{{background:#f5f7fa;width:28%}}.verdict{{font-size:1.25rem;font-weight:700}}.note{{color:#52606d;font-size:.9rem}}</style></head>
<body><h1>{title}</h1><p class="verdict">{classification}</p>
<p class="note">Generated by JobForensics. Model and rule outputs are assistive signals, not proof of fraud or legitimacy.</p>
<h2>Job and source</h2><table>{rows}</table>
<h2>Risk assessment</h2><table><tr><th>Overall risk</th><td>{escape(str(risk.get("overall_risk_score", "Unavailable")))}/100 ({escape(str(risk.get("risk_level", "Unavailable")))})</td></tr>{signal_rows}</table>
<h2>Triggered indicators</h2><ul>{rule_items}</ul>
<h2>Recommendations</h2><ul>{recommendation_items}</ul>
</body></html>"""
