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

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT trace_id, status, question, conversation_id FROM audit_events"
        ).fetchall()

    assert rows == [
        (
            resp.json()["trace_id"],
            "SUCCESS",
            "上个月华东区毛利率是多少？",
            "c-audit",
        )
    ]
