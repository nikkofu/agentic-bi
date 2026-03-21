def test_builder_selects_line_chart_for_time_series():
    from app.services.response_builder import build_response

    result = {
        "metric": "gross_margin_rate",
        "region": "华东",
        "value": 0.32,
        "has_time_series": True,
        "has_rank": False,
    }
    payload = build_response(result)
    assert payload["chart"]["type"] == "line"


def test_builder_includes_month_over_month_delta_for_compare_result():
    from app.services.response_builder import build_response

    result = {
        "metric": "gross_margin_rate",
        "region": "华东",
        "time_window": "last_month",
        "value": 0.32,
        "compare_to": "prev_month",
        "compare_value": 0.295,
        "delta_value": 0.025,
    }

    payload = build_response(result)

    assert payload["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较前月上升2.50个百分点" in payload["answer"]


def test_builder_includes_year_over_year_delta_for_compare_result():
    from app.services.response_builder import build_response

    result = {
        "metric": "gross_margin_rate",
        "region": "华东",
        "time_window": "last_month",
        "value": 0.32,
        "compare_to": "prev_year",
        "compare_value": 0.28,
        "delta_value": 0.04,
    }

    payload = build_response(result)

    assert payload["answer"].startswith("上个月华东区毛利率为32.00%")
    assert "较去年同期上升4.00个百分点" in payload["answer"]


def test_builder_includes_compare_summary_for_time_series_result():
    from app.services.response_builder import build_response

    result = {
        "metric": "revenue",
        "region": "华南",
        "time_window": "recent_3_months",
        "series": [
            {"month": "2025-12", "value": 800},
            {"month": "2026-01", "value": 850},
            {"month": "2026-02", "value": 900},
        ],
        "compare_to": "prev_year",
        "compare_value": 780,
        "delta_value": 120,
    }

    payload = build_response(result)

    assert payload["answer"].startswith("近3个月华南区销售额按月趋势为")
    assert "最新月份较去年同期上升120" in payload["answer"]


def test_builder_returns_bar_chart_for_grouped_breakdown():
    from app.services.response_builder import build_response

    result = {
        "metric": "revenue",
        "region": "华东",
        "time_window": "last_month",
        "group_by": ["channel"],
        "breakdown": [
            {"channel": "线上", "value": 1200},
            {"channel": "线下", "value": 1300},
        ],
    }

    payload = build_response(result)

    assert payload["chart"]["type"] == "bar"
    assert payload["answer"].startswith("上个月华东区销售额按渠道分布为")


def test_builder_returns_bar_chart_for_region_breakdown():
    from app.services.response_builder import build_response

    result = {
        "metric": "revenue",
        "region": "全域",
        "time_window": "last_month",
        "group_by": ["region"],
        "breakdown": [
            {"region": "华东", "value": 2500},
            {"region": "华南", "value": 900},
        ],
    }

    payload = build_response(result)

    assert payload["chart"]["type"] == "bar"
    assert payload["answer"].startswith("上个月全域区销售额按区域分布为")


def test_build_response_with_reporting_keeps_legacy_answer_and_chart_and_adds_reporting_fields():
    from app.domain.models import QueryPlan
    from app.services.response_builder import build_response, build_response_with_reporting

    result = {
        "metric": "gross_margin_rate",
        "region": "华东",
        "time_window": "last_month",
        "value": 0.32,
    }
    plan = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
        group_requested=False,
    )

    legacy_payload = build_response(result)
    reporting_payload = build_response_with_reporting(
        question="上个月华东区毛利率是多少？",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-1",
        permission_context={
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        plan=plan,
        result=result,
    )

    assert reporting_payload["answer"] == legacy_payload["answer"]
    assert reporting_payload["chart"] == legacy_payload["chart"]
    assert "report_intent" in reporting_payload
    assert "dashboard_spec" in reporting_payload
