import sqlite3

from fastapi.testclient import TestClient

from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.infra.repositories.report_intent_repo import ReportIntentRepository
from app.main import app
from app.services.audit_log import _AUDIT_EVENTS

client = TestClient(app)
DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED = "DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED"


def count_rows_or_zero(connection: sqlite3.Connection, table_name: str) -> int:
    try:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc):
            raise
        return 0


def build_insight_card_payload() -> dict:
    return {
        "card_id": "card-1",
        "trace_id": "trace-1",
        "metric": "gross_margin_rate",
        "scope": {"region": "华东"},
        "severity": "P1",
        "summary": "检测到毛利率异常",
        "attribution": {"dimension": "region", "key": "华东", "contribution": -0.06},
        "suggested_next_question": "请分析华东区域毛利率下滑的主要驱动因素",
        "report_id": None,
        "dashboard_id": None,
    }


def build_report_payload(
    report_id: str = "dr-1",
    dashboard_id: str = "dash-1",
    source_kind: str = "insight_card",
    source_ref: str = "card-1",
) -> dict:
    return {
        "id": report_id,
        "version": "1.0",
        "tenant_id": "t-1",
        "principal_id": "u-1",
        "source_kind": source_kind,
        "source_ref": source_ref,
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


def build_dashboard_payload(dashboard_id: str = "dash-1") -> dict:
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


def seed_insight_with_default_report() -> tuple[str, str]:
    dashboard_repo = DashboardRepository()
    report_repo = DiagnosticReportRepository()
    insight_repo = InsightRepository()
    dashboard = dashboard_repo.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-1",
        dashboard=build_dashboard_payload("dash-1"),
        dashboard_id="dash-1",
    )
    report = report_repo.save(report=build_report_payload(dashboard_id=dashboard["dashboard_id"]))
    insight_repo.save_card(build_insight_card_payload())
    insight_repo.attach_report(card_id="card-1", report_id=report["id"], dashboard_id=dashboard["dashboard_id"])
    return "card-1", report["id"]


def seed_insight_without_report(card_id: str = "card-new") -> dict:
    card = build_insight_card_payload()
    card["card_id"] = card_id
    card["trace_id"] = f"trace-{card_id}"
    InsightRepository().save_card(card)
    return card


def seed_insight_with_foreign_report(card_id: str = "card-foreign", region: str = "华南") -> tuple[str, str]:
    dashboard_repo = DashboardRepository()
    report_repo = DiagnosticReportRepository()
    insight_repo = InsightRepository()
    dashboard = dashboard_repo.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-foreign",
        dashboard=build_dashboard_payload("dash-foreign"),
        dashboard_id="dash-foreign",
    )
    report = report_repo.save(
        report=build_report_payload(
            report_id="dr-foreign",
            dashboard_id=dashboard["dashboard_id"],
            source_ref=card_id,
        )
    )
    card = build_insight_card_payload()
    card["card_id"] = card_id
    card["trace_id"] = f"trace-{card_id}"
    card["scope"] = {"region": region}
    insight_repo.save_card(card)
    insight_repo.attach_report(card_id=card_id, report_id=report["id"], dashboard_id=dashboard["dashboard_id"])
    return card_id, report["id"]


def test_get_report_returns_report_metadata_and_embedded_dashboard(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _, report_id = seed_insight_with_default_report()

    resp = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["report"]["id"] == report_id
    assert resp.json()["dashboard"]["id"] == resp.json()["report"]["dashboard_id"]


def test_post_reports_generate_from_insight_returns_existing_default_snapshot(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-from-insight.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card_id, seeded_report_id = seed_insight_with_default_report()

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "from_insight",
            "insight_card_id": card_id,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["report"]["source_kind"] == "insight_card"
    assert resp.json()["report"]["id"] == seeded_report_id


def test_post_reports_generate_from_insight_creates_snapshot_with_planned_defaults(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-from-insight-new.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card = seed_insight_without_report("card-new")

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "from_insight",
            "insight_card_id": card["card_id"],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["report"]["source_kind"] == "insight_card"
    assert body["report"]["source_ref"] == card["card_id"]
    assert body["report"]["summary"]["time_window"] == "last_month"
    assert body["report"]["summary"]["title"] == f"{card['suggested_next_question']} 诊断报告"
    assert body["report"]["findings"] == [
        {
            "kind": "trend",
            "title": "异常延续",
            "statement": card["summary"],
            "evidence_refs": [card["trace_id"]],
        }
    ]
    assert body["report"]["recommendations"] == [
        {
            "kind": "question",
            "label": "继续诊断",
            "question": card["suggested_next_question"],
            "rationale": "从异常卡片继续下钻",
        }
    ]

    intent = ReportIntentRepository().get(body["report"]["report_intent_id"])
    assert intent["question"] == card["suggested_next_question"]


def test_post_reports_generate_direct_creates_new_snapshot(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-direct.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "direct",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "time_window": "last_month",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["report"]["source_kind"] == "on_demand"
    assert resp.json()["dashboard"]["pages"][0]["title"] == "Overview"

    intent = ReportIntentRepository().get(resp.json()["report"]["report_intent_id"])
    assert intent["question"] == "请生成{'region': '华东'}gross_margin_rate诊断报告"


def test_post_reports_generate_requires_insight_card_id_error_code(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-missing-card-id.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "from_insight",
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "MISSING_INSIGHT_CARD_ID"


def test_post_reports_generate_requires_direct_params_error_code(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-missing-direct-params.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "direct",
            "metric": "gross_margin_rate",
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "MISSING_DIRECT_REPORT_PARAMS"


def test_post_reports_generate_direct_denies_unknown_user_scope(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-unknown-scope.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-unknown",
            "principal_id": "u-unknown",
            "mode": "direct",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "time_window": "last_month",
        },
    )

    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PERMISSION_DENIED"


def test_insight_card_detail_returns_report_linkage(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-card-detail.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card_id, report_id = seed_insight_with_default_report()

    resp = client.get(f"/v1/insights/cards/{card_id}", params={"tenant_id": "t-1", "user_id": "u-1"})

    assert resp.status_code == 200
    assert resp.json()["card"]["report_id"] == report_id
    assert (
        resp.json()["card"]["detail_url"]
        == f"/reports/{report_id}?tenant_id=t-1&user_id=u-1&principal_id=u-1"
    )
    assert resp.json()["report_summary"]["report_id"] == report_id


def test_insight_card_detail_returns_explicit_ready_report_state(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-card-ready-state.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card_id, report_id = seed_insight_with_default_report()

    resp = client.get(f"/v1/insights/cards/{card_id}", params={"tenant_id": "t-1", "user_id": "u-1"})

    assert resp.status_code == 200
    assert resp.json()["card"]["report_status"] == "ready"
    assert resp.json()["card"]["report_error_code"] is None
    assert resp.json()["report_summary"]["report_id"] == report_id

def test_insight_reads_fall_back_to_principal_owned_report_when_linked_report_is_inaccessible(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-inaccessible-linked-report.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card_id, foreign_report_id = seed_insight_with_foreign_report()

    list_resp = client.get("/v1/insights/cards", params={"tenant_id": "t-1", "user_id": "u-south"})
    assert list_resp.status_code == 200
    item = next(item for item in list_resp.json()["items"] if item["card_id"] == card_id)
    assert item["report_id"] != foreign_report_id
    assert (
        item["detail_url"]
        == f"/reports/{item['report_id']}?tenant_id=t-1&user_id=u-south&principal_id=u-south"
    )

    detail_resp = client.get(f"/v1/insights/cards/{card_id}", params={"tenant_id": "t-1", "user_id": "u-south"})
    assert detail_resp.status_code == 200
    assert detail_resp.json()["report_summary"]["report_id"] == item["report_id"]

    accessible_report = client.get(
        f"/v1/reports/{item['report_id']}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert accessible_report.status_code == 200

    denied_foreign_report = client.get(
        f"/v1/reports/{foreign_report_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert denied_foreign_report.status_code == 403


def test_report_endpoints_persist_success_and_failure_audit_records(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    card_id, report_id = seed_insight_with_default_report()

    ok_generate = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "from_insight",
            "insight_card_id": card_id,
        },
    )
    assert ok_generate.status_code == 200

    ok_fetch = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert ok_fetch.status_code == 200

    bad_generate = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-other",
            "mode": "direct",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "time_window": "last_month",
        },
    )
    assert bad_generate.status_code == 400

    denied_fetch = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert denied_fetch.status_code == 403

    statuses = {event["status"] for event in _AUDIT_EVENTS}
    assert "DIAGNOSTIC_REPORT_GENERATED" in statuses
    assert "DIAGNOSTIC_REPORT_GENERATE_FAILED" in statuses
    assert "DIAGNOSTIC_REPORT_FETCHED" in statuses
    assert "DIAGNOSTIC_REPORT_FETCH_DENIED" in statuses
    generated_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATED")
    assert generated_event["result_summary"]["report_id"] == report_id
    assert generated_event["result_summary"]["dashboard_id"].startswith("dash-")


def test_post_reports_generate_direct_rolls_back_snapshot_artifacts_on_report_save_failure(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-direct-rollback.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    def raise_report_save_failure(self, report, connection=None):
        raise RuntimeError("report-save-failed")

    monkeypatch.setattr(DiagnosticReportRepository, "save", raise_report_save_failure)

    resp = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "direct",
            "metric": "gross_margin_rate",
            "scope": {"region": "华东"},
            "time_window": "last_month",
        },
    )

    assert resp.status_code == 500
    assert resp.json()["detail"]["error_code"] == DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED

    with sqlite3.connect(db_path) as connection:
        assert count_rows_or_zero(connection, "report_intents") == 0
        assert count_rows_or_zero(connection, "dashboards") == 0
        assert count_rows_or_zero(connection, "dashboard_revisions") == 0
        assert count_rows_or_zero(connection, "diagnostic_reports") == 0

    failed_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED")
    assert failed_event["error_code"] == DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED


def test_insight_card_endpoints_keep_cards_visible_when_lazy_report_creation_fails(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-lazy-insight-report-failure.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    seeded_card = seed_insight_without_report("card-lazy-fail")

    def raise_report_save_failure(self, report, connection=None):
        raise RuntimeError("report-save-failed")

    monkeypatch.setattr(DiagnosticReportRepository, "save", raise_report_save_failure)

    list_resp = client.get("/v1/insights/cards", params={"tenant_id": "t-1", "user_id": "u-1"})
    assert list_resp.status_code == 200
    listed_card = next(item for item in list_resp.json()["items"] if item["card_id"] == seeded_card["card_id"])
    assert listed_card["report_id"] is None
    assert listed_card["dashboard_id"] is None
    assert listed_card["detail_url"] is None

    detail_resp = client.get(f"/v1/insights/cards/{seeded_card['card_id']}", params={"tenant_id": "t-1", "user_id": "u-1"})
    assert detail_resp.status_code == 200
    assert detail_resp.json()["card"]["report_id"] is None
    assert detail_resp.json()["card"]["dashboard_id"] is None
    assert detail_resp.json()["report_summary"] is None
