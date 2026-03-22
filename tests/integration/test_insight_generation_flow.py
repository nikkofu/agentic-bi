import sqlite3

from fastapi.testclient import TestClient

from app.infra.repositories.insight_repo import InsightRepository
from app.main import app
from app.services.audit_log import _AUDIT_EVENTS
from app.services.insight_monitor import run_monitor_once
import app.services.insight_monitor as insight_monitor


client = TestClient(app)


def test_monitor_generates_and_persists_insight_card(tmp_path, monkeypatch):
    db_path = tmp_path / "insights.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    count = run_monitor_once(
        snapshots=[
            {
                "metric": "gross_margin_rate",
                "scope": {"region": "华东"},
                "current_value": 0.24,
                "baseline_value": 0.30,
            }
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    assert count == 1

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT metric, severity, summary, suggested_next_question
            FROM insight_cards
            """
        ).fetchall()

    assert len(rows) == 1
    metric, severity, summary, next_question = rows[0]
    assert metric == "gross_margin_rate"
    assert severity in {"P1", "P2", "P3"}
    assert summary
    assert next_question


def test_monitor_generates_card_and_default_report_snapshot(tmp_path, monkeypatch):
    db_path = tmp_path / "monitor-report-link.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    count = run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30}
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )
    assert count == 1

    cards = InsightRepository().list_by_regions(["华东"])
    assert cards[0]["report_id"]
    assert cards[0]["dashboard_id"]

    report = client.get(
        f"/v1/reports/{cards[0]['report_id']}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert report.status_code == 200
    assert any(event["status"] == "DIAGNOSTIC_REPORT_GENERATED" for event in _AUDIT_EVENTS)


def test_monitor_keeps_card_when_report_generation_fails(tmp_path, monkeypatch):
    db_path = tmp_path / "monitor-report-failure.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    def raise_report_failure(**_: dict):
        raise RuntimeError("report-builder-broke")

    monkeypatch.setattr(insight_monitor, "_create_default_report_snapshot", raise_report_failure)

    count = run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30}
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    assert count == 1
    cards = InsightRepository().list_by_regions(["华东"])
    assert cards[0]["report_id"] is None
    assert any(event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED" for event in _AUDIT_EVENTS)
