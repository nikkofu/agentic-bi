from app.domain.models import QueryPlan


def build_query_plan(intent) -> QueryPlan:
    group_by = ["month"] if intent.time_window == "recent_3_months" else ["category"]
    return QueryPlan(
        metric=intent.metric,
        filters=intent.filters,
        time_window=intent.time_window,
        group_by=group_by,
        compare_to=getattr(intent, "compare_to", ""),
    )
