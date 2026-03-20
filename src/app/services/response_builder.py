from app.domain.metrics_catalog import METRIC_LABELS


TIME_WINDOW_LABELS = {
    "last_month": "上个月",
    "current": "当前",
}


def _format_value(metric: str, value: float) -> str:
    if metric == "gross_margin_rate":
        return f"{value:.2%}"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def build_response(result: dict) -> dict:
    if result.get("has_time_series"):
        chart_type = "line"
    elif result.get("has_rank"):
        chart_type = "bar"
    else:
        chart_type = "table"

    metric = result.get("metric", "")
    metric_label = METRIC_LABELS.get(metric, metric)
    time_window_label = TIME_WINDOW_LABELS.get(result.get("time_window", "last_month"), "当前")
    region = result.get("region", "全域")
    value = _format_value(metric, result.get("value", 0))
    answer = f"{time_window_label}{region}区{metric_label}为{value}"
    return {
        "answer": answer,
        "chart": {"type": chart_type, "data": [result]},
    }
