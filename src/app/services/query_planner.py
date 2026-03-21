from app.domain.models import QueryPlan


def build_query_plan(intent) -> QueryPlan:
    explicit_group_by = getattr(intent, "group_by", [])
    if explicit_group_by:
        group_by = explicit_group_by
    elif intent.time_window == "recent_3_months":
        group_by = ["month"]
    else:
        group_by = ["category"]
    return QueryPlan(
        metric=intent.metric,
        filters=intent.filters,
        time_window=intent.time_window,
        group_by=group_by,
        compare_to=getattr(intent, "compare_to", ""),
        group_requested=bool(explicit_group_by),
    )
