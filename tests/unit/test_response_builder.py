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
