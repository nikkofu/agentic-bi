from app.domain.diagnostic_report_models import (
    DiagnosticFinding,
    DiagnosticRecommendation,
    DiagnosticReport,
    DiagnosticReportSummary,
)
from app.domain.insight_models import AttributionResult, InsightCard


def test_diagnostic_report_accepts_nested_payloads():
    summary = DiagnosticReportSummary(
        headline="毛利率低于基线 6 个点",
        metric="gross_margin_rate",
        scope={"region": "华东"},
    )
    finding = DiagnosticFinding(
        metric="gross_margin_rate",
        scope={"region": "华东"},
        description="华东区域毛利率低于基线。",
    )
    recommendation = DiagnosticRecommendation(
        action="检查华东区域的主要成本驱动因素。",
        rationale="确定导致毛利率下降的原因。",
    )

    report = DiagnosticReport(
        id="dr-1",
        report_intent_id="ri-1",
        trace_id="trace-1",
        dashboard_id="dash-1",
        summary=summary,
        findings=[finding],
        recommendations=[recommendation],
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
