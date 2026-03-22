from fastapi.testclient import TestClient

from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.infra.repositories.report_intent_repo import ReportIntentRepository
from app.main import app
from app.services.audit_log import _AUDIT_EVENTS

client = TestClient(app)


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


def test_insight_card_detail_returns_report_linkage(tmp_path, monkeypatch):
    db_path = tmp_path / "reports-api-card-detail.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    card_id, report_id = seed_insight_with_default_report()

    resp = client.get(f"/v1/insights/cards/{card_id}", params={"tenant_id": "t-1", "user_id": "u-1"})

    assert resp.status_code == 200
    assert resp.json()["card"]["report_id"] == report_id
    assert resp.json()["report_summary"]["report_id"] == report_id


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
