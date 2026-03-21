from app.domain.metrics_catalog import DIMENSION_LABELS, METRIC_LABELS


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


def _format_compare_fragment(metric: str, compare_to: str, delta_value: float | None) -> str:
    if compare_to not in {"prev_month", "prev_year"} or delta_value is None:
        return ""

    direction = "持平"
    if delta_value > 0:
        direction = "上升"
    elif delta_value < 0:
        direction = "下降"

    compare_label = "前月" if compare_to == "prev_month" else "去年同期"

    if direction == "持平":
        return f"，较{compare_label}持平"

    if metric == "gross_margin_rate":
        return f"，较{compare_label}{direction}{abs(delta_value) * 100:.2f}个百分点"

    return f"，较{compare_label}{direction}{_format_value(metric, abs(delta_value))}"


def build_response(result: dict) -> dict:
    series = result.get("series", [])
    breakdown = result.get("breakdown", [])
    if series:
        chart_type = "line"
    elif breakdown:
        chart_type = "bar"
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
        compare_fragment = _format_compare_fragment(
            metric=metric,
            compare_to=result.get("compare_to", ""),
            delta_value=result.get("delta_value"),
        )
        compare_summary = ""
        if compare_fragment:
            compare_summary = f"，最新月份{compare_fragment.lstrip('，')}"
        answer = f"{time_window_label}{region}区{metric_label}按月趋势为：{series_summary}{compare_summary}"
        chart_data = series
    elif breakdown:
        dimension = result.get("group_by", [""])[0]
        dimension_label = DIMENSION_LABELS.get(dimension, dimension)
        breakdown_summary = "，".join(
            f"{point.get(dimension, '')} {_format_value(metric, point['value'])}" for point in breakdown
        )
        answer = f"{time_window_label}{region}区{metric_label}按{dimension_label}分布为：{breakdown_summary}"
        chart_data = breakdown
    else:
        value = _format_value(metric, result.get("value", 0))
        compare_fragment = _format_compare_fragment(
            metric=metric,
            compare_to=result.get("compare_to", ""),
            delta_value=result.get("delta_value"),
        )
        answer = f"{time_window_label}{region}区{metric_label}为{value}{compare_fragment}"
        chart_data = [result]
    return {
        "answer": answer,
        "chart": {"type": chart_type, "data": chart_data},
    }
