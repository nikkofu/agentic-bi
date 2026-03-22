import sqlite3

from fastapi.testclient import TestClient

from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.infra.repositories.report_intent_repo import ReportIntentRepository
from app.main import app
from app.services.audit_log import _AUDIT_EVENTS
from app.services.insight_monitor import run_monitor_once
import app.services.insight_monitor as insight_monitor


client = TestClient(app)


def count_rows_or_zero(connection: sqlite3.Connection, table_name: str) -> int:
    try:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc):
            raise
        return 0


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

    generated_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATED")
    permission_context = generated_event["result_summary"]["permission_context"]
    assert permission_context["principal_id"] == "u-1"
    assert permission_context["role_scope"] == ["region:华东", "region:华南"]
    assert permission_context["row_level_policy_ref"] == "sales-region:u-1"

    stored_report = DiagnosticReportRepository().get_for_owner(
        report_id=cards[0]["report_id"],
        tenant_id="t-1",
        principal_id="u-1",
    )
    stored_intent = ReportIntentRepository().get_for_owner(
        intent_id=stored_report["report_intent_id"],
        tenant_id="t-1",
        principal_id="u-1",
    )
    assert stored_intent["trace"]["trace_id"] == cards[0]["trace_id"]
    assert stored_intent["question"] == cards[0]["suggested_next_question"]

    report = client.get(
        f"/v1/reports/{cards[0]['report_id']}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert report.status_code == 200
    assert any(event["status"] == "DIAGNOSTIC_REPORT_GENERATED" for event in _AUDIT_EVENTS)


def test_monitor_repeated_runs_keep_linked_snapshots_unique(tmp_path, monkeypatch):
    db_path = tmp_path / "monitor-report-repeat.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    first_count = run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30}
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )
    second_count = run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30}
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    assert first_count == 1
    assert second_count == 1

    cards = InsightRepository().list_by_regions(["华东"])
    assert len(cards) == 2
    assert all(card["report_id"] for card in cards)
    assert all(card["dashboard_id"] for card in cards)
    assert len({card["dashboard_id"] for card in cards}) == 2
    assert len({card["trace_id"] for card in cards}) == 2

    reports = DiagnosticReportRepository()
    intents = ReportIntentRepository()
    for card in cards:
        stored_report = reports.get_for_owner(
            report_id=card["report_id"],
            tenant_id="t-1",
            principal_id="u-1",
        )
        stored_intent = intents.get_for_owner(
            intent_id=stored_report["report_intent_id"],
            tenant_id="t-1",
            principal_id="u-1",
        )
        assert stored_intent["trace"]["trace_id"] == card["trace_id"]

    assert not any(event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED" for event in _AUDIT_EVENTS)


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
    failed_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED")
    permission_context = failed_event["result_summary"]["permission_context"]
    assert permission_context["principal_id"] == "u-1"
    assert permission_context["role_scope"] == ["region:华东", "region:华南"]
    assert permission_context["row_level_policy_ref"] == "sales-region:u-1"
    assert failed_event["error_code"] == "DEFAULT_REPORT_SNAPSHOT_CREATE_FAILED"


def test_monitor_report_failure_rolls_back_partial_snapshot_artifacts(tmp_path, monkeypatch):
    db_path = tmp_path / "monitor-report-rollback.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    def raise_report_save_failure(self, report, connection=None):
        raise RuntimeError("report-save-failed")

    monkeypatch.setattr(DiagnosticReportRepository, "save", raise_report_save_failure)

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

    with sqlite3.connect(db_path) as connection:
        assert count_rows_or_zero(connection, "report_intents") == 0
        assert count_rows_or_zero(connection, "dashboards") == 0
        assert count_rows_or_zero(connection, "dashboard_revisions") == 0
        assert count_rows_or_zero(connection, "diagnostic_reports") == 0

    failed_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED")
    assert failed_event["error_code"] == "DEFAULT_REPORT_SNAPSHOT_CREATE_FAILED"
