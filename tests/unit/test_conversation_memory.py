from app.domain.models import QueryPlan
from app.services.conversation_memory import apply_followup


def test_followup_replaces_region_from_previous_plan():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="prev_month",
    )
    nxt = apply_followup("那华南呢", prev)
    assert nxt.filters["region"] == "华南"


def test_followup_switches_to_monthly_view():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="prev_month",
    )
    nxt = apply_followup("按月看", prev)
    assert nxt.time_window == "recent_3_months"
    assert nxt.group_by == ["month"]


def test_followup_can_change_region_and_monthly_view_together():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="prev_month",
    )
    nxt = apply_followup("那华南按月看", prev)
    assert nxt.filters["region"] == "华南"
    assert nxt.time_window == "recent_3_months"
    assert nxt.group_by == ["month"]


def test_followup_can_switch_to_month_over_month_compare():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("环比呢", prev)
    assert nxt.compare_to == "prev_month"
    assert nxt.time_window == "last_month"


def test_followup_can_switch_to_year_over_year_compare():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("同比呢", prev)
    assert nxt.compare_to == "prev_year"
    assert nxt.time_window == "last_month"
