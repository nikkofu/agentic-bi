import sqlite3

from fastapi.testclient import TestClient

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
