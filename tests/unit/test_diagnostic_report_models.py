from app.domain.diagnostic_report_models import (
    DiagnosticFinding,
    DiagnosticRecommendation,
    DiagnosticReport,
    DiagnosticReportSummary,
)
from app.domain.insight_models import AttributionResult, InsightCard


def test_diagnostic_report_accepts_nested_payloads():
    summary = DiagnosticReportSummary(
        title="毛利率异常诊断",
        subtitle="华东区域",
        headline="毛利率低于基线 6 个点",
        metric="gross_margin_rate",
        scope={"region": "华东"},
        time_window="last_month",
        severity="P1",
    )
    finding = DiagnosticFinding(
        kind="metric_delta",
        title="毛利率偏离基线",
        statement="华东区域毛利率低于基线。",
        evidence_refs=["ev-1"],
    )
    recommendation = DiagnosticRecommendation(
        kind="followup_question",
        label="成本驱动分析",
        question="华东区域毛利率下降的主要驱动因素是什么？",
        rationale="确定导致毛利率下降的原因。",
    )

    report = DiagnosticReport(
        id="dr-1",
        version="1.0",
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="report_intent",
        source_ref="ri-1",
        snapshot_time="2026-03-23T08:00:00Z",
        status="ready",
        summary=summary,
        findings=[finding],
        recommendations=[recommendation],
        dashboard_id="dash-1",
        report_intent_id="ri-1",
        trace={"trace_id": "trace-1"},
    )

    assert report.summary.headline == "毛利率低于基线 6 个点"
    assert report.dashboard_id == "dash-1"


def test_insight_card_accepts_report_fields():
    attribution = AttributionResult(
        dimension="region", key="华东", contribution=-0.06
    )
    card = InsightCard(
        card_id="card-1",
        metric="gross_margin_rate",
        scope={"region": "华东"},
        severity="P1",
        summary="毛利率低于基线 6 个点",
        attribution=attribution,
        suggested_next_question="请分析华东在该异常中的主要驱动因素",
        trace_id="trace-1",
        report_id="dr-1",
        dashboard_id="dash-1",
        detail_url="/reports/dr-1",
    )

    assert card.card_id == "card-1"
    assert card.scope == {"region": "华东"}
    assert card.report_id == "dr-1"
    assert card.dashboard_id == "dash-1"
    assert card.detail_url == "/reports/dr-1"
