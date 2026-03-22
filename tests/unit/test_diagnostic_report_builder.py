from fixtures_diagnostic_reports import report_intent_fixture
from app.services.diagnostic_report_builder import build_diagnostic_report


def test_build_diagnostic_report_from_insight_context_reuses_report_intent_and_writes_findings():
    intent = report_intent_fixture()
    report = build_diagnostic_report(
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="insight_card",
        source_ref="card-1",
        report_intent=intent,
        metric_result={"metric": "gross_margin_rate", "value": 0.24, "time_window": "last_month"},
        finding_inputs=[
            {
                "kind": "trend",
                "title": "趋势下滑",
                "statement": "最近一个月持续走低",
                "evidence_refs": ["sq-trend-1"],
            }
        ],
        recommendations=[
            {
                "kind": "question",
                "label": "继续分析渠道",
                "question": "请分析渠道影响",
                "rationale": "渠道变化可解释毛利变化",
            }
        ],
        dashboard_id="dash-1",
    )
    assert report.source_kind == "insight_card"
    assert report.report_intent_id == intent.id
    assert report.findings[0].evidence_refs == ["sq-trend-1"]


def test_build_diagnostic_report_from_direct_context_creates_direct_summary():
    intent = report_intent_fixture(question="请生成华东毛利率诊断报告")
    report = build_diagnostic_report(
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="on_demand",
        source_ref="direct:u-1:last_month",
        report_intent=intent,
        metric_result={"metric": "gross_margin_rate", "value": 0.31, "time_window": "last_month"},
        finding_inputs=[],
        recommendations=[],
        dashboard_id="dash-2",
    )
    assert report.source_kind == "on_demand"
    assert report.summary.metric == "gross_margin_rate"


def test_build_diagnostic_report_preserves_finding_severity_metadata():
    intent = report_intent_fixture()
    severity_value = "critical"
    finding_inputs = [
        {
            "kind": "trend",
            "title": "趋势下滑",
            "statement": "最近一个月持续走低",
            "evidence_refs": ["sq-trend-1"],
            "severity": severity_value,
        }
    ]
    report = build_diagnostic_report(
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="insight_card",
        source_ref="card-5",
        report_intent=intent,
        metric_result={"metric": "gross_margin_rate", "value": 0.20, "time_window": "last_month"},
        finding_inputs=finding_inputs,
        recommendations=[],
        dashboard_id="dash-5",
    )
    assert report.summary.severity == severity_value
    assert report.findings[0].statement == "最近一个月持续走低"


def test_build_diagnostic_report_prefers_highest_severity():
    intent = report_intent_fixture()
    finding_inputs = [
        {
            "kind": "trend",
            "title": "低严重度",
            "statement": "低优先级异常",
            "evidence_refs": ["sq-trend-l"],
            "severity": "low",
        },
        {
            "kind": "trend",
            "title": "高严重度",
            "statement": "高优先级异常",
            "evidence_refs": ["sq-trend-h"],
            "severity": "P1",
        },
        {
            "kind": "trend",
            "title": "中等严重度",
            "statement": "中等优先级异常",
            "evidence_refs": ["sq-trend-m"],
            "severity": "medium",
        },
    ]
    report = build_diagnostic_report(
        tenant_id="t-1",
        principal_id="u-1",
        source_kind="insight_card",
        source_ref="card-7",
        report_intent=intent,
        metric_result={"metric": "gross_margin_rate", "value": 0.18, "time_window": "last_month"},
        finding_inputs=finding_inputs,
        recommendations=[],
        dashboard_id="dash-7",
    )
    assert report.summary.severity == "P1"
    assert len(report.findings) == 3
