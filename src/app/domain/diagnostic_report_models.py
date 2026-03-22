from pydantic import Field

from app.domain.reporting_models import StrictModel


class DiagnosticReportSummary(StrictModel):
    title: str
    subtitle: str | None = None
    metric: str
    scope: dict[str, str] = Field(default_factory=dict)
    time_window: dict = Field(default_factory=dict)
    severity: str
    headline: str


class DiagnosticFinding(StrictModel):
    kind: str
    title: str
    statement: str
    evidence_refs: list[str] = Field(default_factory=list)


class DiagnosticRecommendation(StrictModel):
    kind: str
    label: str
    question: str
    rationale: str


class DiagnosticReport(StrictModel):
    id: str
    version: str
    tenant_id: str
    principal_id: str
    source_kind: str
    source_ref: str
    snapshot_time: str
    status: str
    summary: DiagnosticReportSummary
    findings: list[DiagnosticFinding] = Field(default_factory=list)
    recommendations: list[DiagnosticRecommendation] = Field(default_factory=list)
    dashboard_id: str | None = None
    report_intent_id: str
    trace: dict = Field(default_factory=dict)
