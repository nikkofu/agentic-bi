from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_query_contract_returns_200_and_required_fields():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-1",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "chart" in body
    assert "trace_id" in body
