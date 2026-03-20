import pytest

from app.services.query_planner import build_query_plan


class DummyIntent:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    time_window = "last_month"
    compare_to = ""


def test_planner_outputs_structured_plan():
    plan = build_query_plan(DummyIntent())
    assert plan.metric == "gross_margin_rate"
    assert plan.group_by == ["category"]
    assert plan.compare_to == ""


class TrendIntent:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    time_window = "recent_3_months"
    compare_to = ""


def test_planner_uses_month_grouping_for_recent_trend_queries():
    plan = build_query_plan(TrendIntent())
    assert plan.metric == "gross_margin_rate"
    assert plan.group_by == ["month"]
    assert plan.compare_to == ""


class CompareIntent:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    time_window = "last_month"
    compare_to = "prev_month"


def test_planner_preserves_month_over_month_compare_request():
    plan = build_query_plan(CompareIntent())
    assert plan.metric == "gross_margin_rate"
    assert plan.group_by == ["category"]
    assert plan.compare_to == "prev_month"
