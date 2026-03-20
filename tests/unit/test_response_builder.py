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
