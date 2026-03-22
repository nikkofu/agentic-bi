from app.domain.diagnostic_report_models import (
    DiagnosticRecommendation,
    DiagnosticReport,
    DiagnosticReportSummary,
)
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


def diagnostic_report_fixture(*, dashboard_id: str = "dash-1") -> DiagnosticReport:
    return DiagnosticReport(
        id="dr-fixture",
        version="1.0",
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="insight_card",
        source_ref="card-fixture",
        snapshot_time="2026-03-22T10:00:00Z",
        status="ready",
        summary=DiagnosticReportSummary(
            title="华东毛利率异常诊断",
            subtitle="上个月",
            metric="gross_margin_rate",
            scope={"region": "华东"},
            time_window="last_month",
            severity="P1",
            headline="毛利率低于基线 6 个点",
        ),
        findings=[],
        recommendations=[
            DiagnosticRecommendation(
                kind="question",
                label="继续分析渠道",
                question="请分析渠道影响",
                rationale="渠道变化可解释毛利变化",
            )
        ],
        dashboard_id=dashboard_id,
        report_intent_id="ri-fixture",
        trace={"trace_id": "trace-fixture"},
    )
