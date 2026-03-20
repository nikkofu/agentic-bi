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


def test_followup_monthly_view_returns_time_series_chart():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-4",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按月看",
        "conversation_id": "c-4",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华东区毛利率按月趋势为")
    assert body["chart"]["type"] == "line"
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 0.301},
        {"month": "2026-01", "value": 0.295},
        {"month": "2026-02", "value": 0.32},
    ]


def test_followup_can_change_region_and_monthly_view_together():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-5",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "那华南按月看",
        "conversation_id": "c-5",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华南区毛利率按月趋势为")
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 0.276},
        {"month": "2026-01", "value": 0.281},
        {"month": "2026-02", "value": 0.287},
    ]


def test_direct_trend_question_returns_monthly_series():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "近3个月华东区毛利率趋势",
        "conversation_id": "c-6",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华东区毛利率按月趋势为")
    assert body["chart"]["type"] == "line"
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 0.301},
        {"month": "2026-01", "value": 0.295},
        {"month": "2026-02", "value": 0.32},
    ]


def test_direct_month_over_month_question_returns_compare_answer():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率环比怎么样？",
        "conversation_id": "c-7",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较前月上升2.50个百分点" in body["answer"]


def test_direct_year_over_year_question_returns_compare_answer():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率同比怎么样？",
        "conversation_id": "c-8",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较去年同期上升4.00个百分点" in body["answer"]


def test_followup_month_over_month_question_reuses_previous_metric_and_scope():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-9",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "环比呢",
        "conversation_id": "c-9",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较前月上升2.50个百分点" in body["answer"]


def test_followup_year_over_year_question_reuses_previous_metric_and_scope():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-10",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "同比呢",
        "conversation_id": "c-10",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较去年同期上升4.00个百分点" in body["answer"]


def test_followup_metric_switch_reuses_previous_scope():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-11",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "销售额呢",
        "conversation_id": "c-11",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额为2500")


def test_combined_followup_reuses_time_and_switches_scope_metric_and_compare_mode():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-12",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "那华南销售额同比呢",
        "conversation_id": "c-12",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华南区销售额为900")
    assert "较去年同期上升120" in body["answer"]


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


def test_incomplete_question_returns_metric_clarification():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区怎么样？",
        "conversation_id": "c-clarify",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "MISSING_METRIC"
    assert body["message"] == "请补充要查询的指标"
    assert body["suggestions"] == ["毛利率", "销售额"]
