import json
from pathlib import Path

from app.domain.metrics_catalog import METRIC_AGGREGATIONS


def load_sales_fixture() -> list[dict]:
    fixture_path = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "sales_metrics.json"
    )
    with fixture_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _aggregate_values(values: list[float], aggregation: str) -> float:
    if aggregation == "average":
        return round(sum(values) / len(values), 4)
    return round(sum(values), 4)


def _get_metric_value(row: dict, metric_key: str) -> float:
    if metric_key == "gross_profit":
        return round(row.get("revenue", 0.0) * row.get("gross_margin_rate", 0.0), 4)
    return row.get(metric_key, 0.0)


def _filter_rows_by_time_window(rows: list[dict], time_window: str) -> list[dict]:
    months = sorted({row["month"] for row in rows if row.get("month")})
    if not months:
        return rows

    if time_window == "last_month":
        selected_months = {months[-1]}
    elif time_window == "recent_3_months":
        selected_months = set(months[-3:])
    else:
        return rows

    return [row for row in rows if row.get("month") in selected_months]


def _build_month_series(rows: list[dict], metric_key: str, aggregation: str) -> list[dict]:
    grouped_values: dict[str, list[float]] = {}
    for row in rows:
        grouped_values.setdefault(row["month"], []).append(_get_metric_value(row, metric_key))

    return [
        {"month": month, "value": _aggregate_values(grouped_values[month], aggregation)}
        for month in sorted(grouped_values)
    ]


def _build_dimension_breakdown(
    rows: list[dict],
    metric_key: str,
    aggregation: str,
    dimension: str,
) -> list[dict]:
    grouped_values: dict[str, list[float]] = {}
    for row in rows:
        dimension_value = row.get(dimension)
        if dimension_value is None:
            continue
        grouped_values.setdefault(dimension_value, []).append(_get_metric_value(row, metric_key))

    return [
        {dimension: dimension_value, "value": _aggregate_values(values, aggregation)}
        for dimension_value, values in grouped_values.items()
    ]


def _build_previous_month_comparison(
    scoped_rows: list[dict],
    metric_key: str,
    aggregation: str,
    compare_to: str,
) -> dict:
    if compare_to != "prev_month":
        return {}

    months = sorted({row["month"] for row in scoped_rows if row.get("month")})
    if len(months) < 2:
        return {}

    previous_month = months[-2]
    compare_rows = [row for row in scoped_rows if row.get("month") == previous_month]
    if not compare_rows:
        return {}

    compare_value = _aggregate_values(
        [_get_metric_value(row, metric_key) for row in compare_rows],
        aggregation,
    )
    return {
        "compare_to": compare_to,
        "compare_value": compare_value,
    }


def _build_previous_year_comparison(
    scoped_rows: list[dict],
    current_rows: list[dict],
    metric_key: str,
    aggregation: str,
    compare_to: str,
) -> dict:
    if compare_to != "prev_year" or not current_rows:
        return {}

    current_months = sorted({row["month"] for row in current_rows if row.get("month")})
    if not current_months:
        return {}

    anchor_month = current_months[-1]
    year, month = anchor_month.split("-")
    previous_year_month = f"{int(year) - 1:04d}-{month}"
    compare_rows = [row for row in scoped_rows if row.get("month") == previous_year_month]
    if not compare_rows:
        return {}

    compare_value = _aggregate_values(
        [_get_metric_value(row, metric_key) for row in compare_rows],
        aggregation,
    )
    return {
        "compare_to": compare_to,
        "compare_value": compare_value,
    }


def execute_query(plan, scope):
    rows = load_sales_fixture()
    region = plan.filters.get("region")
    if region:
        rows = [r for r in rows if r.get("region") == region]
    allowed_regions = scope.get("allowed_regions", [])
    if allowed_regions:
        rows = [r for r in rows if r.get("region") in allowed_regions]
    scoped_rows = list(rows)
    rows = _filter_rows_by_time_window(rows, plan.time_window)

    if not rows:
        return {
            "value": 0.0,
            "metric": plan.metric,
            "region": region or "全域",
            "time_window": plan.time_window,
        }

    metric_key = plan.metric
    aggregation = METRIC_AGGREGATIONS.get(metric_key, "sum")
    values = [_get_metric_value(row, metric_key) for row in rows]

    series = []
    breakdown = []
    if plan.group_by == ["month"]:
        series = _build_month_series(rows, metric_key, aggregation)
    elif getattr(plan, "group_requested", False) and len(plan.group_by) == 1:
        breakdown = _build_dimension_breakdown(rows, metric_key, aggregation, plan.group_by[0])

    value = _aggregate_values(values, aggregation)
    comparison = _build_previous_month_comparison(
        scoped_rows=scoped_rows,
        metric_key=metric_key,
        aggregation=aggregation,
        compare_to=plan.compare_to,
    )
    if not comparison:
        comparison = _build_previous_year_comparison(
            scoped_rows=scoped_rows,
            current_rows=rows,
            metric_key=metric_key,
            aggregation=aggregation,
            compare_to=plan.compare_to,
        )

    comparison_base_value = value
    if series:
        comparison_base_value = series[-1]["value"]

    return {
        "value": value,
        "metric": metric_key,
        "region": region or "全域",
        "time_window": plan.time_window,
        "group_by": plan.group_by,
        "series": series,
        "breakdown": breakdown,
        "delta_value": comparison_base_value - comparison["compare_value"] if comparison else None,
        **comparison,
    }
