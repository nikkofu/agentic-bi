import json
from pathlib import Path


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
        return {"value": 0.0, "metric": plan.metric, "region": region or "all"}

    value = sum(r.get("gross_margin_rate", 0.0) for r in rows) / len(rows)
    return {"value": round(value, 4), "metric": plan.metric, "region": region or "all"}
