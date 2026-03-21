from app.services.intent_parser import parse_intent
from app.services.query_planner import build_query_plan
from app.services.report_intent_builder import build_report_intent


def _permission_context() -> dict:
    return {
        "principal_id": "u-1",
        "role_scope": ["region:华东"],
        "row_level_policy_ref": "sales-region:u-1",
    }


def test_build_report_intent_ignores_default_category_grouping_for_scalar_query():
    question = "上个月华东区毛利率是多少？"
    plan = build_query_plan(parse_intent(question))
    intent = build_report_intent(
        question=question,
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-1",
        permission_context=_permission_context(),
        plan=plan,
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东"},
    )

    assert plan.group_by == ["category"]
    assert plan.group_requested is False
    assert intent.semantic_queries[0].dimensions == []
    assert intent.semantic_queries[0].measures == [plan.metric]
    assert intent.permission_context.principal_id == "u-1"
    assert intent.trace["trace_id"] == "trace-1"


def test_build_report_intent_preserves_month_dimension_for_trend_query():
    question = "近3个月华东区毛利率趋势"
    plan = build_query_plan(parse_intent(question))
    intent = build_report_intent(
        question=question,
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-2",
        permission_context=_permission_context(),
        plan=plan,
        result={
            "metric": "gross_margin_rate",
            "region": "华东",
            "series": [{"month": "2026-02", "value": 0.32}],
        },
    )

    assert plan.group_by == ["month"]
    assert plan.group_requested is False
    assert intent.semantic_queries[0].dimensions == ["month"]


def test_build_report_intent_preserves_requested_grouping_dimension_for_breakdown_query():
    question = "上个月华东区毛利率按渠道看"
    plan = build_query_plan(parse_intent(question))
    intent = build_report_intent(
        question=question,
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-3",
        permission_context=_permission_context(),
        plan=plan,
        result={
            "metric": "gross_margin_rate",
            "region": "华东",
            "breakdown": [{"channel": "线上", "value": 0.31}],
        },
    )

    assert plan.group_by == ["channel"]
    assert plan.group_requested is True
    assert intent.semantic_queries[0].dimensions == ["channel"]


def test_build_report_intent_does_not_synthesize_global_region_filter_for_unscoped_query():
    question = "上个月毛利率是多少？"
    plan = build_query_plan(parse_intent(question))
    intent = build_report_intent(
        question=question,
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-4",
        permission_context=_permission_context(),
        plan=plan,
        result={
            "metric": "gross_margin_rate",
            "value": 0.30,
            "region": "全域",
        },
    )

    assert plan.filters == {}
    assert intent.semantic_queries[0].filters == []
