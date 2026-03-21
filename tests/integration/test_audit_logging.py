import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.services.audit_log import _AUDIT_EVENTS

client = TestClient(app)


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
