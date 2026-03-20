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
    return sum(values)


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
        grouped_values.setdefault(row["month"], []).append(row.get(metric_key, 0.0))

    return [
        {"month": month, "value": _aggregate_values(grouped_values[month], aggregation)}
        for month in sorted(grouped_values)
    ]


def execute_query(plan, scope):
    rows = load_sales_fixture()
    region = plan.filters.get("region")
    if region:
        rows = [r for r in rows if r.get("region") == region]
    allowed_regions = scope.get("allowed_regions", [])
    if allowed_regions:
        rows = [r for r in rows if r.get("region") in allowed_regions]
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
    values = [r.get(metric_key, 0.0) for r in rows]

    series = []
    if plan.group_by == ["month"]:
        series = _build_month_series(rows, metric_key, aggregation)

    value = _aggregate_values(values, aggregation)

    return {
        "value": value,
        "metric": metric_key,
        "region": region or "全域",
        "time_window": plan.time_window,
        "series": series,
    }
