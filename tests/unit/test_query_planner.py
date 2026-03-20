import pytest

from app.services.query_planner import build_query_plan


class DummyIntent:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    time_window = "last_month"


def test_planner_outputs_structured_plan():
    plan = build_query_plan(DummyIntent())
    assert plan.metric == "gross_margin_rate"
    assert plan.group_by == ["category"]
    assert plan.compare_to == "prev_month"
