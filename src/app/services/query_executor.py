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


def execute_query(plan, scope):
    rows = load_sales_fixture()
    region = plan.filters.get("region")
    if region:
        rows = [r for r in rows if r.get("region") == region]
    allowed_regions = scope.get("allowed_regions", [])
    if allowed_regions:
        rows = [r for r in rows if r.get("region") in allowed_regions]

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

    if aggregation == "average":
        value = sum(values) / len(values)
        value = round(value, 4)
    else:
        value = sum(values)

    return {
        "value": value,
        "metric": metric_key,
        "region": region or "全域",
        "time_window": plan.time_window,
    }
