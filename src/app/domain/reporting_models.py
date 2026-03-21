from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PermissionContext(StrictModel):
    principal_id: str
    role_scope: list[str] = Field(default_factory=list)
    row_level_policy_ref: str | None = None


class SemanticQuery(StrictModel):
    id: str
    kind: str
    measures: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    filters: list[dict] = Field(default_factory=list)
    time: dict = Field(default_factory=dict)
    comparison: dict | None = None
    sort: dict | None = None
    limit: int | None = None
    display_hint: dict = Field(default_factory=dict)


class ChartPresentation(StrictModel):
    id: str
    title: str | None = None
    layout: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)


class WidgetPresentation(StrictModel):
    family: str
    variant: str | None = None
    title: str | None = None
    config: dict = Field(default_factory=dict)


class WidgetBinding(StrictModel):
    source_ref: str
    query_id: str | None = None
    value_path: str | None = None


class DashboardWidget(StrictModel):
    id: str
    kind: str
    title: str | None = None
    presentation: WidgetPresentation
    binding: WidgetBinding


class DashboardSection(StrictModel):
    id: str
    title: str | None = None
    layout: dict = Field(default_factory=dict)
    widgets: list[DashboardWidget] = Field(default_factory=list)


class DashboardPage(StrictModel):
    id: str
    title: str | None = None
    layout: dict = Field(default_factory=dict)
    sections: list[DashboardSection] = Field(default_factory=list)


class DashboardSpec(StrictModel):
    id: str
    version: str
    title: str
    description: str | None = None
    theme: dict = Field(default_factory=dict)
    refresh_policy: dict = Field(default_factory=dict)
    variables: list[dict] = Field(default_factory=list)
    data_bindings: list[dict] = Field(default_factory=list)
    interactions: list[dict] = Field(default_factory=list)
    pages: list[DashboardPage] = Field(..., min_length=1)


class EditorState(StrictModel):
    version: str
    document_id: str
    selection: dict = Field(default_factory=dict)
    draft_layout_overrides: dict = Field(default_factory=dict)
    panel_state: dict = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list)
    validation_markers: list[dict] = Field(default_factory=list)
    viewport: dict = Field(default_factory=dict)


class ReportIntent(StrictModel):
    id: str
    version: str
    tenant_id: str
    dataset_id: str
    source: str
    question: str
    goal: str
    permission_context: PermissionContext
    semantic_queries: list[SemanticQuery] = Field(..., min_length=1)
    explanations: list[dict] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)
    trace: dict = Field(default_factory=dict)
