import sqlite3

import pytest

from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository


def build_report_payload(report_id="dr-1", dashboard_id="dash-1"):
    return {
        "id": report_id,
        "version": "1.0",
        "tenant_id": "t-1",
        "principal_id": "u-1",
        "source_kind": "insight_card",
        "source_ref": "card-1",
        "snapshot_time": "2026-03-22T10:00:00Z",
        "status": "ready",
        "summary": {
            "title": "华东毛利率异常诊断",
            "subtitle": "上个月",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "time_window": "last_month",
            "severity": "P1",
            "headline": "毛利率低于基线 6 个点",
        },
        "findings": [],
        "recommendations": [],
        "dashboard_id": dashboard_id,
        "report_intent_id": "ri-1",
        "trace": {"trace_id": "trace-1"},
    }


def build_dashboard_payload(dashboard_id="dash-1"):
    return {
        "id": dashboard_id,
        "version": "1.0",
        "title": "华东毛利率异常诊断",
        "description": "snapshot",
        "theme": {"name": "paper"},
        "refresh_policy": {"mode": "snapshot"},
        "variables": [],
        "data_bindings": [],
        "interactions": [],
        "pages": [{"id": "page-1", "title": "Overview", "layout": {"columns": 12}, "sections": []}],
    }


def test_report_repo_persists_metadata_for_owner(tmp_path, monkeypatch):
    db_path = tmp_path / "report-snapshot.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    dashboards = DashboardRepository()
    reports = DiagnosticReportRepository()

    saved_dashboard = dashboards.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-1",
        dashboard=build_dashboard_payload("dash-keep-me"),
        dashboard_id="dash-keep-me",
    )
    assert saved_dashboard["dashboard_id"] == "dash-keep-me"

    payload = build_report_payload(report_id="dr-1", dashboard_id=saved_dashboard["dashboard_id"])
    reports.save(payload)

    stored = reports.get_for_owner(report_id="dr-1", tenant_id="t-1", principal_id="u-1")
    assert stored["id"] == "dr-1"
    assert stored["dashboard_id"] == "dash-keep-me"
    assert stored["summary"]["severity"] == "P1"

    by_source = reports.get_by_source_ref(
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="insight_card",
        source_ref="card-1",
    )
    assert by_source["id"] == "dr-1"
    assert (
        reports.get_by_source_ref(
            tenant_id="t-1",
            principal_id="u-1",
            source_kind="insight_card",
            source_ref="card-missing",
        )
        is None
    )

    with pytest.raises(KeyError):
        reports.get_for_owner(report_id="dr-1", tenant_id="t-1", principal_id="u-2")


def test_report_repo_get_or_create_default_for_insight_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "report-idempotent.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    reports = DiagnosticReportRepository()

    calls = {"count": 0}

    def create_fn():
        calls["count"] += 1
        created = build_report_payload(report_id=f"dr-create-{calls['count']}", dashboard_id="dash-default")
        return reports.save(created)

    first = reports.get_or_create_default_for_insight(
        tenant_id="t-1",
        principal_id="u-1",
        source_ref="card-1",
        create_fn=create_fn,
    )
    second = reports.get_or_create_default_for_insight(
        tenant_id="t-1",
        principal_id="u-1",
        source_ref="card-1",
        create_fn=create_fn,
    )

    assert first["id"] == second["id"] == "dr-create-1"
    assert calls["count"] == 1

    with sqlite3.connect(db_path) as connection:
        total_rows = connection.execute("SELECT COUNT(*) FROM diagnostic_reports").fetchone()[0]
    assert total_rows == 1


def test_insight_repo_generates_unique_card_ids_when_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-card-id-fallback.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    repo = InsightRepository()
    payload = {
        "trace_id": "trace-same",
        "metric": "gross_margin_rate",
        "scope": {"region": "华东"},
        "severity": "P1",
        "summary": "summary",
        "attribution": {"key": "华东", "contribution": -0.06},
        "suggested_next_question": "next",
    }

    first = repo.save_card(payload)
    second = repo.save_card(payload)

    assert first["card_id"].startswith("card-")
    assert second["card_id"].startswith("card-")
    assert first["card_id"] != second["card_id"]

    with sqlite3.connect(db_path) as connection:
        total_rows = connection.execute("SELECT COUNT(*) FROM insight_cards").fetchone()[0]
    assert total_rows == 2


def test_dashboard_repo_generates_fresh_ids_without_explicit_dashboard_id(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-id-generation.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    dashboards = DashboardRepository()
    preview_payload = build_dashboard_payload("dash-preview-1")

    first = dashboards.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-1",
        dashboard=preview_payload,
    )
    second = dashboards.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-1",
        dashboard=preview_payload,
    )

    assert first["dashboard_id"].startswith("dash-")
    assert second["dashboard_id"].startswith("dash-")
    assert first["dashboard_id"] != "dash-preview-1"
    assert second["dashboard_id"] != "dash-preview-1"
    assert first["dashboard_id"] != second["dashboard_id"]
    assert first["dashboard"]["id"] == first["dashboard_id"]
    assert second["dashboard"]["id"] == second["dashboard_id"]


def test_report_repo_allows_multiple_on_demand_snapshots_for_same_source_ref(tmp_path, monkeypatch):
    db_path = tmp_path / "report-on-demand.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    reports = DiagnosticReportRepository()

    first = build_report_payload(report_id="dr-od-1", dashboard_id="dash-1")
    first["source_kind"] = "on_demand"
    first["source_ref"] = "direct:u-1:last_month"
    first["snapshot_time"] = "2026-03-22T10:00:00Z"
    second = build_report_payload(report_id="dr-od-2", dashboard_id="dash-2")
    second["source_kind"] = "on_demand"
    second["source_ref"] = "direct:u-1:last_month"
    second["snapshot_time"] = "2026-03-22T11:00:00Z"

    reports.save(first)
    reports.save(second)

    with sqlite3.connect(db_path) as connection:
        total_rows = connection.execute("SELECT COUNT(*) FROM diagnostic_reports").fetchone()[0]
    assert total_rows == 2


def test_insight_repo_attach_report_and_get_by_card_id(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-linkage.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    repo = InsightRepository()

    saved = repo.save_card(
        {
            "trace_id": "trace-1",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "severity": "P1",
            "summary": "summary",
            "attribution": {"key": "华东", "contribution": -0.06},
            "suggested_next_question": "next",
        }
    )

    assert saved["card_id"].startswith("card-")
    assert saved["report_id"] is None
    assert saved["dashboard_id"] is None
    assert saved["detail_url"] is None

    repo.attach_report(card_id=saved["card_id"], report_id="dr-9", dashboard_id="dash-9")
    stored = repo.get(card_id=saved["card_id"], allowed_regions=["华东"])

    assert stored["report_id"] == "dr-9"
    assert stored["dashboard_id"] == "dash-9"
    assert stored["detail_url"] == "/reports/dr-9"

    with pytest.raises(KeyError):
        repo.get(card_id=saved["card_id"], allowed_regions=["华南"])


def test_insight_repo_bootstraps_legacy_table_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-legacy-schema.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE insight_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                scope TEXT NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                attribution TEXT NOT NULL,
                suggested_next_question TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO insight_cards (
                trace_id, metric, scope, severity, summary, attribution, suggested_next_question
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-trace-1",
                "gross_margin_rate",
                '{"region":"华东"}',
                "P1",
                "legacy-summary",
                '{"key":"华东","contribution":-0.06}',
                "legacy-next",
            ),
        )
        connection.commit()

    repo = InsightRepository()

    items = repo.list_by_regions(["华东"])
    assert len(items) == 1
    assert items[0]["card_id"].startswith("card-")

    saved = repo.save_card(
        {
            "trace_id": "new-trace-1",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "severity": "P2",
            "summary": "new-summary",
            "attribution": {"key": "华东", "contribution": -0.03},
            "suggested_next_question": "new-next",
        }
    )
    assert saved["card_id"].startswith("card-")

    all_items = repo.list_by_regions(["华东"])
    assert len(all_items) == 2
