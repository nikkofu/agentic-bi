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


def test_query_returns_value_from_fixture_backend():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-1",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率")


def test_query_honors_direct_south_region_question():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华南区毛利率是多少？",
        "conversation_id": "c-2",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华南区毛利率为28.70%")
    assert body["chart"]["data"][0]["region"] == "华南"
    assert body["chart"]["data"][0]["value"] == 0.287


def test_query_returns_revenue_metric_with_metric_specific_answer():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额是多少？",
        "conversation_id": "c-3",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额为2500")
    assert body["chart"]["data"][0]["metric"] == "revenue"
    assert body["chart"]["data"][0]["value"] == 2500


def test_unknown_metric_returns_structured_error_code():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区未知指标是多少？",
        "conversation_id": "c-err",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "UNKNOWN_METRIC"
