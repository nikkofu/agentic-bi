from datetime import datetime, timezone
from uuid import uuid4

from app.domain.diagnostic_report_models import (
    DiagnosticFinding,
    DiagnosticRecommendation,
    DiagnosticReport,
    DiagnosticReportSummary,
)


def _scope_from_intent(report_intent) -> dict[str, str]:
    for semantic_query in report_intent.semantic_queries:
        for filter_item in semantic_query.filters:
            if filter_item.get("field") == "region":
                value = filter_item.get("value")
                if value and str(value) != "全域":
                    return {"region": str(value)}
    return {}


_SEVERITY_PRIORITY = {
    "critical": 0,
    "p1": 0,
    "high": 1,
    "p2": 1,
    "medium": 2,
    "p3": 2,
    "low": 3,
}

_DEFAULT_SEVERITY_PRIORITY = max(_SEVERITY_PRIORITY.values()) + 1


def _severity_from_findings(findings: list[dict]) -> str:
    best_severity = "medium"
    best_priority = _DEFAULT_SEVERITY_PRIORITY
    for finding in findings:
        raw = finding.get("severity")
        if not raw:
            continue
        value = str(raw).strip()
        if not value:
            continue
        key = value.lower()
        priority = _SEVERITY_PRIORITY.get(key, _DEFAULT_SEVERITY_PRIORITY)
        if priority < best_priority:
            best_priority = priority
            best_severity = value
    return best_severity


def _sanitize_finding_inputs(findings: list[dict]) -> list[dict]:
    return [{key: value for key, value in item.items() if key != "severity"} for item in findings]


def _build_headline(metric_result: dict) -> str:
    metric = metric_result.get("metric", "metric")
    if "value" in metric_result:
        return f"{metric} = {metric_result['value']}"
    if metric_result.get("series"):
        return f"{metric} 趋势"
    return metric


def build_diagnostic_report(
    *,
    tenant_id: str,
    principal_id: str,
    source_kind: str,
    source_ref: str,
    report_intent,
    metric_result: dict,
    finding_inputs: list[dict],
    recommendations: list[dict],
    dashboard_id: str,
) -> DiagnosticReport:
    sanitized_findings = _sanitize_finding_inputs(finding_inputs)
    return DiagnosticReport(
        id=f"dr-{uuid4().hex[:12]}",
        version="1.0",
        tenant_id=tenant_id,
        principal_id=principal_id,
        source_kind=source_kind,
        source_ref=source_ref,
        snapshot_time=datetime.now(timezone.utc).isoformat(),
        status="ready",
        summary=DiagnosticReportSummary(
            title=f"{report_intent.question} 诊断报告",
            subtitle=metric_result.get("time_window", ""),
            metric=metric_result["metric"],
            scope=_scope_from_intent(report_intent),
            time_window=metric_result.get("time_window", "current"),
            severity=_severity_from_findings(finding_inputs),
            headline=_build_headline(metric_result),
        ),
        findings=[DiagnosticFinding(**item) for item in sanitized_findings],
        recommendations=[DiagnosticRecommendation(**item) for item in recommendations],
        dashboard_id=dashboard_id,
        report_intent_id=report_intent.id,
        trace=report_intent.trace,
    )
