from pydantic import BaseModel


class AnomalyEvent(BaseModel):
    metric: str
    scope: dict[str, str]
    current_value: float
    baseline_value: float
    delta: float
    severity: str
    trigger_rule: str


class AttributionResult(BaseModel):
    dimension: str
    key: str
    contribution: float


class InsightCard(BaseModel):
    card_id: str
    metric: str
    scope: dict[str, str]
    severity: str
    summary: str
    attribution: AttributionResult
    suggested_next_question: str
    trace_id: str
    report_id: str | None = None
    dashboard_id: str | None = None
    detail_url: str | None = None
    report_status: str | None = None
    report_error_code: str | None = None
