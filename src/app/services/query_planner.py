from app.domain.models import QueryPlan


def build_query_plan(intent) -> QueryPlan:
    return QueryPlan(
        metric=intent.metric,
        filters=intent.filters,
        time_window=intent.time_window,
        group_by=["category"],
        compare_to="prev_month",
    )
