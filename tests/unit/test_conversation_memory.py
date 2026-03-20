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
