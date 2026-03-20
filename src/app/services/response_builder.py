def build_response(result: dict) -> dict:
    if result.get("has_time_series"):
        chart_type = "line"
    elif result.get("has_rank"):
        chart_type = "bar"
    else:
        chart_type = "table"

    answer = f"上个月{result.get('region', '全域')}区毛利率为{result.get('value', 0):.2%}"
    return {
        "answer": answer,
        "chart": {"type": chart_type, "data": [result]},
    }
