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


def test_query_returns_gross_profit_metric_with_metric_specific_answer():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利额是多少？",
        "conversation_id": "c-3-gross-profit",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利额为800.80")
    assert body["chart"]["data"][0]["metric"] == "gross_profit"
    assert body["chart"]["data"][0]["value"] == 800.8


def test_grouped_category_query_returns_bar_chart_breakdown():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额按品类看",
        "conversation_id": "c-group-category",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额按品类分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"category": "家电", "value": 1200},
        {"category": "配件", "value": 1300},
    ]


def test_grouped_channel_query_returns_bar_chart_breakdown():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额按渠道看",
        "conversation_id": "c-group-channel",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额按渠道分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"channel": "线上", "value": 1200},
        {"channel": "线下", "value": 1300},
    ]


def test_grouped_region_query_returns_bar_chart_breakdown():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月销售额按区域看",
        "conversation_id": "c-group-region",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月全域区销售额按区域分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"region": "华东", "value": 2500},
        {"region": "华南", "value": 900},
    ]


def test_grouped_channel_query_accepts_alias_metric_and_dimension_phrasing():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东大区营收按销售渠道看",
        "conversation_id": "c-group-channel-alias",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额按渠道分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"channel": "线上", "value": 1200},
        {"channel": "线下", "value": 1300},
    ]


def test_invalid_multi_dimension_query_returns_structured_error():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额按渠道和品类看",
        "conversation_id": "c-invalid-group",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "INVALID_DIMENSION_COMBO"
    assert body["message"] == "暂不支持同时按多个维度查看，请只保留一个分组维度"
    assert body["suggestions"] == ["按渠道看", "按品类看"]


def test_invalid_region_and_channel_grouping_returns_targeted_repair_suggestions():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月销售额按区域和渠道看",
        "conversation_id": "c-invalid-region-channel-group",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "INVALID_DIMENSION_COMBO"
    assert body["message"] == "暂不支持同时按多个维度查看，请只保留一个分组维度"
    assert body["suggestions"] == ["按区域看", "按渠道看"]


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


def test_followup_grouped_channel_view_returns_bar_chart():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额是多少？",
        "conversation_id": "c-followup-group-channel",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按渠道看",
        "conversation_id": "c-followup-group-channel",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额按渠道分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"channel": "线上", "value": 1200},
        {"channel": "线下", "value": 1300},
    ]


def test_followup_grouped_region_view_returns_bar_chart():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月销售额是多少？",
        "conversation_id": "c-followup-group-region",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按大区看",
        "conversation_id": "c-followup-group-region",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月全域区销售额按区域分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"region": "华东", "value": 2500},
        {"region": "华南", "value": 900},
    ]


def test_followup_invalid_multi_dimension_grouping_returns_structured_error():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额是多少？",
        "conversation_id": "c-followup-invalid-group",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按渠道和品类看",
        "conversation_id": "c-followup-invalid-group",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "INVALID_DIMENSION_COMBO"
    assert body["message"] == "暂不支持同时按多个维度查看，请只保留一个分组维度"
    assert body["suggestions"] == ["按渠道看", "按品类看"]


def test_followup_invalid_region_and_channel_grouping_returns_targeted_repair_suggestions():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月销售额是多少？",
        "conversation_id": "c-followup-invalid-region-channel-group",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按区域和渠道看",
        "conversation_id": "c-followup-invalid-region-channel-group",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "INVALID_DIMENSION_COMBO"
    assert body["message"] == "暂不支持同时按多个维度查看，请只保留一个分组维度"
    assert body["suggestions"] == ["按区域看", "按渠道看"]


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


def test_direct_trend_question_accepts_recent_three_months_alias_and_revenue_alias():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "最近三个月华东区营收走势",
        "conversation_id": "c-6-alias",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华东区销售额按月趋势为")
    assert body["chart"]["type"] == "line"
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 1100},
        {"month": "2026-01", "value": 1000},
        {"month": "2026-02", "value": 2500},
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


def test_direct_gross_profit_trend_question_returns_monthly_series():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "近3个月华东区毛利额趋势",
        "conversation_id": "c-8-gross-profit-trend",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华东区毛利额按月趋势为")
    assert body["chart"]["type"] == "line"
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 331.1},
        {"month": "2026-01", "value": 295.0},
        {"month": "2026-02", "value": 800.8},
    ]


def test_direct_gross_profit_year_over_year_question_returns_compare_answer():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利额同比怎么样？",
        "conversation_id": "c-8-gross-profit-yoy",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利额为800.80")
    assert "较去年同期上升534.80" in body["answer"]


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


def test_followup_year_over_year_accepts_natural_compare_phrase():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-10-phrase",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "和去年同期比呢",
        "conversation_id": "c-10-phrase",
    }
    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较去年同期上升4.00个百分点" in body["answer"]


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


def test_followup_metric_switch_can_use_gross_profit_metric():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-11-gross-profit",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "毛利额呢",
        "conversation_id": "c-11-gross-profit",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利额为800.80")


def test_followup_gross_profit_year_over_year_question_reuses_previous_scope():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利额是多少？",
        "conversation_id": "c-11-gross-profit-yoy",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "同比呢",
        "conversation_id": "c-11-gross-profit-yoy",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利额为800.80")
    assert "较去年同期上升534.80" in body["answer"]


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


def test_combined_followup_accepts_revenue_alias_question():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-12-alias",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "那华南收入同比呢",
        "conversation_id": "c-12-alias",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华南区销售额为900")
    assert "较去年同期上升120" in body["answer"]


def test_combined_followup_can_return_monthly_trend_with_compare_summary():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-13",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "那华南销售额同比按月看",
        "conversation_id": "c-13",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("近3个月华南区销售额按月趋势为")
    assert "最新月份较去年同期上升120" in body["answer"]
    assert body["chart"]["data"] == [
        {"month": "2025-12", "value": 800},
        {"month": "2026-01", "value": 850},
        {"month": "2026-02", "value": 900},
    ]


def test_unknown_metric_returns_structured_error_code():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区未知指标是多少？",
        "conversation_id": "c-err",
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "UNKNOWN_METRIC"
    assert body["message"] == "未识别指标，请改问毛利率、销售额或毛利额"
    assert body["suggestions"] == ["毛利率", "销售额", "毛利额"]


def test_unknown_metric_returns_intent_aware_repair_suggestions():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区利润率是多少？",
        "conversation_id": "c-err-profit-rate",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "UNKNOWN_METRIC"
    assert body["message"] == "未识别指标，可能想问毛利率或毛利额"
    assert body["suggestions"] == ["毛利率", "毛利额"]


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
    assert body["suggestions"] == ["毛利率", "销售额", "毛利额"]


def test_metric_clarification_followup_reuses_previous_scope_and_time():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区怎么样？",
        "conversation_id": "c-clarify-followup",
    }

    initial = client.post("/v1/chat/query", json=initial_payload)

    assert initial.status_code == 422
    assert initial.json()["error_code"] == "MISSING_METRIC"

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "毛利率呢",
        "conversation_id": "c-clarify-followup",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区毛利率为32.00%")


def test_followup_grouped_category_view_returns_bar_chart():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区销售额是多少？",
        "conversation_id": "c-followup-group-category",
    }
    initial = client.post("/v1/chat/query", json=initial_payload)
    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "按产品品类看",
        "conversation_id": "c-followup-group-category",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("上个月华东区销售额按品类分布为")
    assert body["chart"]["type"] == "bar"
    assert body["chart"]["data"] == [
        {"category": "家电", "value": 1200},
        {"category": "配件", "value": 1300},
    ]


def test_same_conversation_id_does_not_leak_context_across_users():
    initial_payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "shared-cross-user",
    }

    initial = client.post("/v1/chat/query", json=initial_payload)

    assert initial.status_code == 200

    followup_payload = {
        "user_id": "u-south",
        "tenant_id": "t-1",
        "question": "销售额呢",
        "conversation_id": "shared-cross-user",
    }

    resp = client.post("/v1/chat/query", json=followup_payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("当前全域区销售额为3330")
