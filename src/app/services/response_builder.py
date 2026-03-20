from app.domain.metrics_catalog import METRIC_LABELS


TIME_WINDOW_LABELS = {
    "last_month": "上个月",
    "recent_3_months": "近3个月",
    "current": "当前",
}


def _format_value(metric: str, value: float) -> str:
    if metric == "gross_margin_rate":
        return f"{value:.2%}"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def build_response(result: dict) -> dict:
    series = result.get("series", [])
    if series:
        chart_type = "line"
    elif result.get("has_time_series"):
        chart_type = "line"
    elif result.get("has_rank"):
        chart_type = "bar"
    else:
        chart_type = "table"

    metric = result.get("metric", "")
    metric_label = METRIC_LABELS.get(metric, metric)
    time_window_label = TIME_WINDOW_LABELS.get(result.get("time_window", "last_month"), "当前")
    region = result.get("region", "全域")
    if series:
        series_summary = "，".join(
            f"{point['month']} {_format_value(metric, point['value'])}" for point in series
        )
        answer = f"{time_window_label}{region}区{metric_label}按月趋势为：{series_summary}"
        chart_data = series
    else:
        value = _format_value(metric, result.get("value", 0))
        answer = f"{time_window_label}{region}区{metric_label}为{value}"
        chart_data = [result]
    return {
        "answer": answer,
        "chart": {"type": chart_type, "data": chart_data},
    }
