from app.domain.reporting_models import PermissionContext, ReportIntent, SemanticQuery


def report_intent_fixture(*, question: str = "请分析华东毛利率") -> ReportIntent:
    semantic_query = SemanticQuery(
        id="sq-fixture",
        kind="metric_query",
        measures=["gross_margin_rate"],
        dimensions=[],
        filters=[{"field": "region", "op": "=", "value": "华东"}],
        time={"window": "last_month"},
    )
    return ReportIntent(
        id="ri-fixture",
        version="1.0",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        source="chat",
        question=question,
        goal="answer question",
        permission_context=PermissionContext(
            principal_id="u-1",
            role_scope=["region:华东"],
            row_level_policy_ref="sales-region:u-1",
        ),
        semantic_queries=[semantic_query],
        explanations=[],
        trace={"trace_id": "trace-fixture"},
    )
