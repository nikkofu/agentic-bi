from app.domain.models import QueryPlan
from app.services.conversation_memory import _conversation_store
from app.services.conversation_memory import apply_followup
from app.services.conversation_memory import get_last_plan
from app.services.conversation_memory import save_last_plan


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


def test_followup_switches_to_channel_breakdown():
    prev = QueryPlan(
        metric="revenue",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("按渠道看", prev)
    assert nxt.group_by == ["channel"]
    assert nxt.group_requested is True


def test_followup_switches_to_region_breakdown():
    prev = QueryPlan(
        metric="revenue",
        filters={},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("按大区看", prev)
    assert nxt.group_by == ["region"]
    assert nxt.group_requested is True


def test_followup_preserves_invalid_multi_dimension_grouping_for_validation():
    prev = QueryPlan(
        metric="revenue",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("按渠道和品类看", prev)
    assert nxt.group_by == ["channel", "category"]
    assert nxt.group_requested is True


def test_followup_preserves_invalid_region_and_channel_grouping_for_validation():
    prev = QueryPlan(
        metric="revenue",
        filters={},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("按区域和渠道看", prev)
    assert nxt.group_by == ["region", "channel"]
    assert nxt.group_requested is True


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


def test_followup_can_switch_metric_and_keep_scope():
    prev = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )
    nxt = apply_followup("销售额呢", prev)
    assert nxt.metric == "revenue"
    assert nxt.filters["region"] == "华东"
    assert nxt.time_window == "last_month"


def test_memory_is_scoped_by_tenant_and_user():
    _conversation_store.clear()
    plan = QueryPlan(
        metric="gross_margin_rate",
        filters={"region": "华东"},
        time_window="last_month",
        group_by=["category"],
        compare_to="",
    )

    save_last_plan("t-1", "u-1", "shared-c", plan)

    own_plan = get_last_plan("t-1", "u-1", "shared-c")
    other_user_plan = get_last_plan("t-1", "u-south", "shared-c")

    assert own_plan is not None
    assert own_plan.metric == "gross_margin_rate"
    assert other_user_plan is None
