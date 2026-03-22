from pydantic import Field

from app.domain.reporting_models import StrictModel


class DiagnosticReportSummary(StrictModel):
    headline: str
    metric: str
    scope: dict[str, str] = Field(default_factory=dict)


class DiagnosticFinding(StrictModel):
    metric: str
    scope: dict[str, str] = Field(default_factory=dict)
    description: str
    severity: str | None = None


class DiagnosticRecommendation(StrictModel):
    action: str
    rationale: str | None = None
    priority: str | None = None


class DiagnosticReport(StrictModel):
    id: str
    report_intent_id: str
    trace_id: str
    dashboard_id: str | None = None
    summary: DiagnosticReportSummary
    findings: list[DiagnosticFinding] = Field(default_factory=list)
    recommendations: list[DiagnosticRecommendation] = Field(default_factory=list)
