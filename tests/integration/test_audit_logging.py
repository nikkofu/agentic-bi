import sqlite3
from copy import deepcopy

from fastapi.testclient import TestClient

from app.api import reports as reports_api
from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.main import app
from app.services.audit_log import _AUDIT_EVENTS

client = TestClient(app)


def _build_assemble_intent_payload() -> dict:
    return {
        "id": "ri-audit-1",
        "version": "1.0",
        "tenant_id": "t-1",
        "dataset_id": "sales-fixture",
        "source": "chat",
        "question": "上个月华东区毛利率是多少？",
        "goal": "answer question",
        "permission_context": {
            "principal_id": "u-1",
            "role_scope": ["region:华东", "region:华南"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        "semantic_queries": [
            {
                "id": "sq-audit-1",
                "kind": "metric_query",
                "measures": ["gross_margin_rate"],
                "dimensions": [],
                "filters": [{"field": "region", "op": "=", "value": "华东"}],
                "time": {"window": "last_month"},
                "comparison": None,
                "sort": None,
                "limit": None,
                "display_hint": {},
            }
        ],
        "explanations": [{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
        "constraints": {},
        "trace": {"trace_id": "trace-audit-1"},
    }


def _build_dashboard_save_payload() -> dict:
    return {
        "tenant_id": "t-1",
        "user_id": "u-1",
        "principal_id": "u-1",
        "report_intent": {
            "id": "ri-dashboard-audit-1",
            "version": "1.0",
            "tenant_id": "t-1",
            "dataset_id": "sales-fixture",
            "source": "chat",
            "question": "上个月华东区毛利率是多少？",
            "goal": "answer question",
            "permission_context": {
                "principal_id": "u-1",
                "role_scope": ["region:华东", "region:华南"],
                "row_level_policy_ref": "sales-region:u-1",
            },
            "semantic_queries": [
                {
                    "id": "sq-dashboard-audit-1",
                    "kind": "metric_query",
                    "measures": ["gross_margin_rate"],
                    "dimensions": [],
                    "filters": [{"field": "region", "op": "=", "value": "华东"}],
                    "time": {"window": "last_month"},
                    "comparison": None,
                    "sort": None,
                    "limit": None,
                    "display_hint": {},
                }
            ],
            "explanations": [{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
            "constraints": {},
            "trace": {"trace_id": "trace-dashboard-audit-1"},
        },
        "dashboard": {
            "id": "dash-preview-dashboard-audit-1",
            "version": "1.0",
            "title": "毛利率预览",
            "description": "preview",
            "theme": {"name": "paper"},
            "refresh_policy": {"mode": "manual"},
            "variables": [],
            "data_bindings": [
                {
                    "id": "binding-dashboard-audit-1",
                    "source_ref": "sq-dashboard-audit-1",
                    "kind": "materialized_result",
                    "value": 0.31,
                    "rows": [{"region": "华东", "gross_margin_rate": 0.31}],
                    "insight": "auto",
                }
            ],
            "interactions": [],
            "pages": [
                {
                    "id": "page-dashboard-audit-1",
                    "title": "Overview",
                    "layout": {"columns": 12},
                    "sections": [
                        {
                            "id": "section-dashboard-audit-1",
                            "title": "Summary",
                            "layout": {"columns": 12},
                            "widgets": [
                                {
                                    "id": "widget-dashboard-audit-1",
                                    "kind": "metric_card",
                                    "title": "核心指标",
                                    "presentation": {"family": "kpi", "variant": "primary", "config": {}},
                                    "binding": {
                                        "source_ref": "sq-dashboard-audit-1",
                                        "value_path": "value",
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }


def _build_insight_card_payload() -> dict:
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


def _build_report_payload(
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


def _build_dashboard_payload(dashboard_id: str = "dash-1") -> dict:
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


def _seed_insight_with_default_report() -> tuple[str, str]:
    dashboard_repo = DashboardRepository()
    report_repo = DiagnosticReportRepository()
    insight_repo = InsightRepository()
    dashboard = dashboard_repo.save(
        tenant_id="t-1",
        principal_id="u-1",
        report_intent_id="ri-1",
        dashboard=_build_dashboard_payload("dash-1"),
        dashboard_id="dash-1",
    )
    report = report_repo.save(report=_build_report_payload(dashboard_id=dashboard["dashboard_id"]))
    insight_repo.save_card(_build_insight_card_payload())
    insight_repo.attach_report(card_id="card-1", report_id=report["id"], dashboard_id=dashboard["dashboard_id"])
    return "card-1", report["id"]


def _seed_insight_without_report(card_id: str = "card-audit-new") -> dict:
    card = _build_insight_card_payload()
    card["card_id"] = card_id
    card["trace_id"] = f"trace-{card_id}"
    InsightRepository().save_card(card)
    return card


def test_chat_query_persists_audit_record(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-audit",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200

    saved = _AUDIT_EVENTS[-1]
    assert saved["trace_id"] == resp.json()["trace_id"]
    assert saved["status"] == "SUCCESS"
    assert saved["query_plan"]["metric"] == "gross_margin_rate"
    assert saved["response_type"] == "table"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT trace_id, status, question, conversation_id, query_plan, response_type, error_code
            FROM audit_events
            """
        ).fetchall()

    assert len(rows) == 1
    trace_id, status, question, conversation_id, query_plan, response_type, error_code = rows[0]
    assert trace_id == resp.json()["trace_id"]
    assert status == "SUCCESS"
    assert question == "上个月华东区毛利率是多少？"
    assert conversation_id == "c-audit"
    assert '"metric": "gross_margin_rate"' in query_plan
    assert response_type == "table"
    assert error_code is None


def test_permission_denied_request_is_audited(tmp_path, monkeypatch):
    db_path = tmp_path / "audit-denied.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    payload = {
        "user_id": "u-south",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-audit-denied",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 403
    saved = _AUDIT_EVENTS[-1]
    assert saved["status"] == "PERMISSION_DENIED"
    assert saved["trace_id"] == resp.json()["trace_id"]
    assert saved["error_code"] == "PERMISSION_DENIED"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT trace_id, status, question, conversation_id, query_plan, response_type, error_code
            FROM audit_events
            """
        ).fetchall()

    assert len(rows) == 1
    trace_id, status, question, conversation_id, query_plan, response_type, error_code = rows[0]
    assert trace_id == resp.json()["trace_id"]
    assert status == "PERMISSION_DENIED"
    assert question == "上个月华东区毛利率是多少？"
    assert conversation_id == "c-audit-denied"
    assert '"metric": "gross_margin_rate"' in query_plan
    assert response_type is None
    assert error_code == "PERMISSION_DENIED"


def test_reporting_endpoints_persist_success_and_failure_audit_records(tmp_path, monkeypatch):
    db_path = tmp_path / "reporting-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    generate_ok = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": "c-report-audit",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert generate_ok.status_code == 200
    intent_id = generate_ok.json()["id"]

    generate_bad = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-other",
            "conversation_id": "c-report-audit-mismatch",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert generate_bad.status_code == 400

    get_ok = client.get(
        f"/v1/report-intents/{intent_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert get_ok.status_code == 200

    get_denied = client.get(
        f"/v1/report-intents/{intent_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert get_denied.status_code == 403

    assemble_ok = client.post(
        "/v1/dashboards:assemble",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "intent": _build_assemble_intent_payload(),
        },
    )
    assert assemble_ok.status_code == 200

    assemble_denied = client.post(
        "/v1/dashboards:assemble",
        json={
            "tenant_id": "t-1",
            "user_id": "u-south",
            "principal_id": "u-south",
            "intent": _build_assemble_intent_payload(),
        },
    )
    assert assemble_denied.status_code == 403

    statuses = {event["status"] for event in _AUDIT_EVENTS}
    assert "REPORT_INTENT_GENERATED" in statuses
    assert "REPORT_INTENT_GENERATE_FAILED" in statuses
    assert "REPORT_INTENT_FETCHED" in statuses
    assert "REPORT_INTENT_FETCH_DENIED" in statuses
    assert "DASHBOARD_PREVIEW_ASSEMBLED" in statuses
    assert "DASHBOARD_PREVIEW_ASSEMBLE_FAILED" in statuses

    assembled_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DASHBOARD_PREVIEW_ASSEMBLED")
    permission_context = assembled_event["result_summary"]["permission_context"]
    assert permission_context["principal_id"] == "u-1"
    assert permission_context["role_scope"] == ["region:华东", "region:华南"]
    assert permission_context["row_level_policy_ref"] == "sales-region:u-1"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT status, result_summary, error_code
            FROM audit_events
            """
        ).fetchall()
    db_statuses = {row[0] for row in rows}
    assert "REPORT_INTENT_GENERATED" in db_statuses
    assert "REPORT_INTENT_GENERATE_FAILED" in db_statuses
    assert "REPORT_INTENT_FETCHED" in db_statuses
    assert "REPORT_INTENT_FETCH_DENIED" in db_statuses
    assert "DASHBOARD_PREVIEW_ASSEMBLED" in db_statuses
    assert "DASHBOARD_PREVIEW_ASSEMBLE_FAILED" in db_statuses


def test_dashboard_endpoints_persist_success_and_failure_audit_records(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    save_ok = client.post("/v1/dashboards", json=_build_dashboard_save_payload())
    assert save_ok.status_code == 201
    dashboard_id = save_ok.json()["dashboard_id"]

    fetch_ok = client.get(
        f"/v1/dashboards/{dashboard_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert fetch_ok.status_code == 200

    save_bad_payload = deepcopy(_build_dashboard_save_payload())
    save_bad_payload["report_intent"]["permission_context"]["role_scope"] = ["region:华北"]
    save_bad = client.post("/v1/dashboards", json=save_bad_payload)
    assert save_bad.status_code == 403

    fetch_denied = client.get(
        f"/v1/dashboards/{dashboard_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert fetch_denied.status_code == 403

    statuses = {event["status"] for event in _AUDIT_EVENTS}
    assert "DASHBOARD_SAVED" in statuses
    assert "DASHBOARD_SAVE_FAILED" in statuses
    assert "DASHBOARD_FETCHED" in statuses
    assert "DASHBOARD_FETCH_DENIED" in statuses

    saved_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DASHBOARD_SAVED")
    permission_context = saved_event["result_summary"]["permission_context"]
    assert permission_context["principal_id"] == "u-1"
    assert permission_context["role_scope"] == ["region:华东", "region:华南"]
    assert permission_context["row_level_policy_ref"] == "sales-region:u-1"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT status, result_summary, error_code
            FROM audit_events
            """
        ).fetchall()
    db_statuses = {row[0] for row in rows}
    assert "DASHBOARD_SAVED" in db_statuses
    assert "DASHBOARD_SAVE_FAILED" in db_statuses
    assert "DASHBOARD_FETCHED" in db_statuses
    assert "DASHBOARD_FETCH_DENIED" in db_statuses


def test_diagnostic_report_endpoints_persist_success_and_failure_audit_records(tmp_path, monkeypatch):
    db_path = tmp_path / "diagnostic-report-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    card_id, report_id = _seed_insight_with_default_report()

    generate_ok = client.post(
        "/v1/reports:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "mode": "from_insight",
            "insight_card_id": card_id,
        },
    )
    assert generate_ok.status_code == 200

    fetch_ok = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert fetch_ok.status_code == 200

    generate_bad = client.post(
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
    assert generate_bad.status_code == 400

    fetch_denied = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert fetch_denied.status_code == 403

    statuses = {event["status"] for event in _AUDIT_EVENTS}
    assert "DIAGNOSTIC_REPORT_GENERATED" in statuses
    assert "DIAGNOSTIC_REPORT_GENERATE_FAILED" in statuses
    assert "DIAGNOSTIC_REPORT_FETCHED" in statuses
    assert "DIAGNOSTIC_REPORT_FETCH_DENIED" in statuses

    generated_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATED")
    permission_context = generated_event["result_summary"]["permission_context"]
    assert generated_event["result_summary"]["report_id"] == report_id
    assert permission_context["principal_id"] == "u-1"
    assert permission_context["role_scope"] == ["region:华东", "region:华南"]
    assert permission_context["row_level_policy_ref"] == "sales-region:u-1"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT status, result_summary, error_code
            FROM audit_events
            """
        ).fetchall()
    db_statuses = {row[0] for row in rows}
    assert "DIAGNOSTIC_REPORT_GENERATED" in db_statuses
    assert "DIAGNOSTIC_REPORT_GENERATE_FAILED" in db_statuses
    assert "DIAGNOSTIC_REPORT_FETCHED" in db_statuses
    assert "DIAGNOSTIC_REPORT_FETCH_DENIED" in db_statuses


def test_diagnostic_report_endpoints_persist_audit_records(tmp_path, monkeypatch):
    db_path = tmp_path / "diagnostic-report-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()

    generated = client.post(
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
    assert generated.status_code == 200
    report_id = generated.json()["report"]["id"]

    denied = client.get(
        f"/v1/reports/{report_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert denied.status_code == 403

    statuses = {event["status"] for event in _AUDIT_EVENTS}
    assert "DIAGNOSTIC_REPORT_GENERATED" in statuses
    assert "DIAGNOSTIC_REPORT_FETCH_DENIED" in statuses


def test_diagnostic_report_generate_reuses_request_trace_for_uncached_success(tmp_path, monkeypatch):
    db_path = tmp_path / "diagnostic-report-trace-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    trace_ids = iter(["trace-request", "trace-snapshot"])
    monkeypatch.setattr(reports_api, "new_trace_id", lambda: next(trace_ids))

    generated = client.post(
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

    assert generated.status_code == 200
    assert generated.json()["report"]["trace"]["trace_id"] == "trace-request"
    generated_event = next(event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATED")
    assert generated_event["trace_id"] == "trace-request"


def test_insight_endpoints_audit_lazy_report_generation_failures(tmp_path, monkeypatch):
    db_path = tmp_path / "diagnostic-report-lazy-failure-audit.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    _AUDIT_EVENTS.clear()
    seeded_card = _seed_insight_without_report("card-audit-lazy-fail")

    def raise_report_save_failure(self, report, connection=None):
        raise RuntimeError("report-save-failed")

    monkeypatch.setattr(DiagnosticReportRepository, "save", raise_report_save_failure)

    list_resp = client.get("/v1/insights/cards", params={"tenant_id": "t-1", "user_id": "u-1"})
    assert list_resp.status_code == 200
    listed_card = next(item for item in list_resp.json()["items"] if item["card_id"] == seeded_card["card_id"])
    assert listed_card["report_status"] == "unavailable"
    assert listed_card["report_error_code"] == reports_api.DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED

    detail_resp = client.get(
        f"/v1/insights/cards/{seeded_card['card_id']}",
        params={"tenant_id": "t-1", "user_id": "u-1"},
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["card"]["report_status"] == "unavailable"
    assert detail_resp.json()["card"]["report_error_code"] == reports_api.DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED

    failed_events = [event for event in _AUDIT_EVENTS if event["status"] == "DIAGNOSTIC_REPORT_GENERATE_FAILED"]
    assert len(failed_events) == 2
    assert all(
        event["error_code"] == reports_api.DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED for event in failed_events
    )
    assert all(event["result_summary"]["card_id"] == seeded_card["card_id"] for event in failed_events)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT status, error_code, result_summary
            FROM audit_events
            WHERE status = 'DIAGNOSTIC_REPORT_GENERATE_FAILED'
            """
        ).fetchall()

    assert len(rows) == 2
    assert all(row[1] == reports_api.DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED for row in rows)
    assert all(seeded_card["card_id"] in (row[2] or "") for row in rows)
