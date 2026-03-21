# Auto Reporting Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-shaped auto-reporting slice by adding protocol schemas, backend dashboard assembly/persistence APIs, and a read-only web viewer that renders saved or preview dashboards through ECharts while keeping `/v1/chat/query` backward compatible.

**Architecture:** Extend the existing FastAPI sales-copilot backend with a reporting protocol layer (`report_intent`, `dashboard_spec`, `editor_state`) and a `dashboard_assembler` that converts the current query-plan/result pipeline into reusable report documents. Add dashboard persistence with revisions in SQLite, expose a small reporting API surface for generate/assemble/save/load, and introduce a separate Vite + React viewer that consumes the abstract dashboard spec and renders charts through a frontend ECharts adapter plus structured explanation widgets.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy Core, SQLite, pytest, Node.js 20, Vite, React, TypeScript, Apache ECharts, Vitest, Testing Library

---

## 0) File Structure & Responsibilities

### Backend files
- Create: `src/app/domain/reporting_models.py` — protocol-layer Pydantic models for `ReportIntent`, `SemanticQuery`, `DashboardSpec`, `Widget`, `ChartPresentation`, and `EditorState`
- Create: `src/app/services/report_intent_builder.py` — converts request context + query plans + execution metadata into `ReportIntent`
- Create: `src/app/services/dashboard_assembler.py` — builds default dashboard pages/widgets from `ReportIntent` + query results
- Create: `src/app/api/reporting.py` — `report-intents:generate`, `dashboards:assemble`, `dashboards` save/load endpoints
- Create: `src/app/infra/repositories/report_intent_repo.py` — `report_intents` and `semantic_queries` persistence in SQLite
- Create: `src/app/infra/repositories/dashboard_repo.py` — dashboard and revision persistence in SQLite
- Modify: `src/app/api/chat.py` — keep legacy `answer/chart/trace_id` while attaching report preview payload
- Modify: `src/app/main.py` — register reporting router and add dev CORS middleware for the new viewer
- Modify: `src/app/services/response_builder.py` — keep legacy response shaping narrow and stop it from becoming the new reporting protocol home
- Modify: `src/app/domain/models.py` — only if shared enums or helper models need to move into the reporting model layer

### Backend tests
- Create: `tests/unit/test_reporting_models.py`
- Create: `tests/unit/test_report_intent_builder.py`
- Create: `tests/unit/test_dashboard_assembler.py`
- Create: `tests/integration/test_reporting_api.py`
- Create: `tests/integration/test_dashboard_persistence.py`
- Modify: `tests/integration/test_chat_query_flow.py`

### Frontend files
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/index.html`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/styles.css`
- Create: `web/src/types/reporting.ts`
- Create: `web/src/api/client.ts`
- Create: `web/src/components/DashboardPage.tsx`
- Create: `web/src/components/WidgetRenderer.tsx`
- Create: `web/src/components/MetricCardWidget.tsx`
- Create: `web/src/components/ChartWidget.tsx`
- Create: `web/src/components/InsightWidget.tsx`
- Create: `web/src/components/TextWidget.tsx`
- Create: `web/src/renderers/echartsAdapter.ts`
- Create: `web/src/routes/PreviewPage.tsx`
- Create: `web/src/routes/DashboardPageRoute.tsx`
- Create: `web/src/test/setup.ts`
- Create: `web/src/test/fixtures/reportPreview.ts`

### Frontend tests
- Create: `web/src/components/__tests__/DashboardPage.test.tsx`
- Create: `web/src/components/__tests__/PreviewPage.test.tsx`
- Create: `web/src/renderers/__tests__/echartsAdapter.test.ts`

### Docs
- Modify: `README.md`
- Modify: `docs/PROJECT-STATUS.md`

### Scope guardrails
- Do not implement drag-and-drop editing in this plan
- Do not implement arbitrary dataset registration in this plan
- Do not expose raw model chain-of-thought in this plan

### Helper placement
- Put `intent_fixture()` in `tests/unit/test_dashboard_assembler.py` or a tiny sibling helper module under `tests/unit/fixtures_reporting.py`
- Put `build_materialized_binding()` and `build_overview_page()` in `src/app/services/dashboard_assembler.py`
- Keep test-only viewer payloads in `web/src/test/fixtures/reportPreview.ts`

---

## 1) Delivery Sequence (TDD, small steps, frequent commits)

### Task 1: Add backend reporting protocol models

**Files:**
- Create: `src/app/domain/reporting_models.py`
- Test: `tests/unit/test_reporting_models.py`

- [ ] **Step 1: Write the failing schema validation tests**

```python
from app.domain.reporting_models import ChartPresentation, DashboardSpec, EditorState, ReportIntent


def test_report_intent_requires_version_and_semantic_queries():
    intent = ReportIntent(
        id="ri-1",
        version="1.0",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        source="chat",
        question="上个月华东区毛利率是多少？",
        goal="answer question",
        permission_context={
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        semantic_queries=[{"id": "sq-1", "kind": "metric"}],
        explanations=[],
        constraints={},
        trace={"trace_id": "trace-1"},
    )
    assert intent.version == "1.0"
    assert intent.permission_context.principal_id == "u-1"
    assert intent.semantic_queries[0].id == "sq-1"


def test_dashboard_spec_requires_pages_and_widget_bindings():
    dashboard = DashboardSpec(
        id="dash-1",
        version="1.0",
        title="毛利率预览",
        description="preview",
        theme={"name": "paper"},
        refresh_policy={"mode": "manual"},
        variables=[],
        data_bindings=[],
        interactions=[],
        pages=[{"id": "page-1", "title": "Overview", "layout": {"columns": 12}, "sections": []}],
    )
    assert dashboard.pages[0].id == "page-1"


def test_editor_state_stays_separate_from_dashboard_spec():
    state = EditorState(
        version="1.0",
        document_id="dash-1",
        selection={"widget_ids": ["widget-1"]},
        draft_layout_overrides={},
        panel_state={},
        history=[],
        validation_markers=[],
        viewport={"zoom": 1},
    )
    assert state.document_id == "dash-1"
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/unit/test_reporting_models.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing reporting model classes

- [ ] **Step 3: Implement minimal protocol models in `src/app/domain/reporting_models.py`**

```python
from pydantic import BaseModel, Field


class PermissionContext(BaseModel):
    principal_id: str
    role_scope: list[str] = Field(default_factory=list)
    row_level_policy_ref: str | None = None


class SemanticQuery(BaseModel):
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


class ReportIntent(BaseModel):
    id: str
    version: str
    tenant_id: str
    dataset_id: str
    source: str
    question: str
    goal: str
    permission_context: PermissionContext
    semantic_queries: list[SemanticQuery]
    explanations: list[dict] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)
    trace: dict = Field(default_factory=dict)
```

- [ ] **Step 4: Re-run the tests**

Run: `pytest tests/unit/test_reporting_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/domain/reporting_models.py tests/unit/test_reporting_models.py
git commit -m "feat: add auto-reporting protocol models"
```

---

### Task 2: Build `ReportIntent` and `DashboardSpec` assembly from the existing sales-copilot pipeline

**Files:**
- Create: `src/app/services/report_intent_builder.py`
- Create: `src/app/services/dashboard_assembler.py`
- Modify: `src/app/domain/reporting_models.py`
- Test: `tests/unit/test_report_intent_builder.py`
- Test: `tests/unit/test_dashboard_assembler.py`
- Modify: `src/app/services/response_builder.py`

- [ ] **Step 1: Write the failing builder and assembler tests**

```python
from app.services.dashboard_assembler import assemble_dashboard
from app.services.report_intent_builder import build_report_intent


def test_build_report_intent_maps_existing_query_plan_to_semantic_query():
    intent = build_report_intent(
        question="上个月华东区毛利率是多少？",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-1",
        permission_context={
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        plan={"metric": "gross_margin_rate", "region": "华东", "time_window": "last_month"},
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东"},
    )
    assert intent.semantic_queries[0].measures == ["gross_margin_rate"]
    assert intent.permission_context.principal_id == "u-1"
    assert intent.trace["trace_id"] == "trace-1"


def test_assemble_dashboard_creates_metric_card_chart_and_insight_widgets():
    dashboard = assemble_dashboard(
        intent=intent_fixture(),
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东", "series": []},
    )
    widget_kinds = [widget.kind for widget in dashboard.pages[0].sections[0].widgets]
    assert widget_kinds == ["metric_card", "chart", "insight"]
    assert dashboard.pages[0].sections[0].widgets[1].presentation.family == "table_like"
    assert dashboard.data_bindings[0]["source_ref"] == dashboard.pages[0].sections[0].widgets[1].binding.source_ref
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/unit/test_report_intent_builder.py tests/unit/test_dashboard_assembler.py -v`
Expected: FAIL because the builder and assembler modules do not exist yet

- [ ] **Step 3: Implement builder and assembler with the current sales result shapes**

```python
def build_report_intent(*, question, tenant_id, dataset_id, trace_id, permission_context, plan, result):
    return ReportIntent(
        id=f"ri-{trace_id}",
        version="1.0",
        tenant_id=tenant_id,
        dataset_id=dataset_id,
        source="chat",
        question=question,
        goal="answer question",
        permission_context=permission_context,
        semantic_queries=[
            SemanticQuery(
                id=f"sq-{trace_id}",
                kind="metric_query",
                measures=[plan["metric"]],
                dimensions=[dimension for dimension in plan.get("group_by", [])],
                filters=[{"field": "region", "op": "=", "value": plan.get("region", "全域")}],
                time={"window": plan.get("time_window", "current")},
                comparison={"mode": plan.get("compare_to")} if plan.get("compare_to") else None,
            )
        ],
        explanations=[{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
        trace={"trace_id": trace_id},
    )
```

```python
def assemble_dashboard(*, intent, result):
    return DashboardSpec(
        id=f"dash-preview-{intent.trace['trace_id']}",
        version="1.0",
        title=intent.question,
        description="Auto-generated dashboard preview",
        theme={"name": "paper"},
        refresh_policy={"mode": "manual"},
        variables=[],
        data_bindings=[build_materialized_binding(intent=intent, result=result)],
        interactions=[],
        pages=[build_overview_page(intent=intent, result=result)],
    )
```

Implementation note:
- Extend `src/app/domain/reporting_models.py` with the smallest typed submodels needed to make Task 2 object access real rather than `dict`-shaped guessing. At minimum, add typed page/section/widget/binding models if needed so assertions like `widget.presentation.family` and `widget.binding.source_ref` are backed by actual schema types.

- [ ] **Step 4: Re-run the tests**

Run: `pytest tests/unit/test_report_intent_builder.py tests/unit/test_dashboard_assembler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/report_intent_builder.py src/app/services/dashboard_assembler.py src/app/services/response_builder.py tests/unit/test_report_intent_builder.py tests/unit/test_dashboard_assembler.py
git commit -m "feat: assemble dashboard specs from sales copilot results"
```

---

### Task 3: Expose reporting preview APIs, persist `ReportIntent`, and keep `/v1/chat/query` backward compatible

**Files:**
- Create: `src/app/api/reporting.py`
- Create: `src/app/infra/repositories/report_intent_repo.py`
- Modify: `src/app/api/chat.py`
- Modify: `src/app/main.py`
- Test: `tests/integration/test_reporting_api.py`
- Modify: `tests/integration/test_chat_query_flow.py`

- [ ] **Step 1: Write failing integration tests for preview generation and assembly**

```python
def test_generate_report_intent_endpoint_returns_protocol_document(client):
    resp = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": "c-1",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    assert body["permission_context"]["principal_id"] == "u-1"
    assert body["permission_context"]["role_scope"] == ["region:华东"]
    assert body["permission_context"]["row_level_policy_ref"] == "sales-region:u-1"
    assert body["semantic_queries"][0]["measures"] == ["gross_margin_rate"]

    stored = client.get(f"/v1/report-intents/{body['id']}")
    assert stored.status_code == 200
    assert stored.json()["id"] == body["id"]


def test_assemble_dashboard_endpoint_returns_preview_dashboard(client):
    intent = build_intent_payload()
    resp = client.post("/v1/dashboards:assemble", json={"intent": intent})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dashboard"]["version"] == "1.0"
    assert body["dashboard"]["data_bindings"][0]["kind"] == "materialized_result"


def test_chat_query_keeps_legacy_fields_and_adds_report_preview():
    resp = client.post("/v1/chat/query", json=payload)
    body = resp.json()
    assert "answer" in body
    assert "chart" in body
    assert "report_preview" in body
    assert body["report_preview"]["dashboard"]["version"] == "1.0"
```

- [ ] **Step 2: Run the integration tests to confirm they fail**

Run: `pytest tests/integration/test_reporting_api.py tests/integration/test_chat_query_flow.py -v`
Expected: FAIL because reporting routes and `report_preview` do not exist yet

- [ ] **Step 3: Implement router registration and chat façade compatibility**

```python
@router.post("/report-intents:generate")
def generate_report_intent(req: ReportingGenerateRequest):
    plan, result, trace_id = execute_reporting_preview(req)
    intent = build_report_intent(
        question=req.question,
        tenant_id=req.tenant_id,
        dataset_id="sales-fixture",
        trace_id=trace_id,
        permission_context=build_permission_context(
            principal_id=req.principal_id or req.user_id,
            role_scope=[f"region:{region}" for region in resolve_allowed_regions(req.user_id, req.tenant_id)],
            row_level_policy_ref=f"sales-region:{req.user_id}",
        ),
        plan=plan.model_dump(),
        result=result,
    )
    report_intent_repo.save(intent)
    append_audit_event(
        {
            "trace_id": trace_id,
            "status": "REPORT_INTENT_GENERATED",
            "question": req.question,
            "conversation_id": req.conversation_id,
            "query_plan": plan.model_dump(),
            "result_summary": {
                "report_intent_id": intent.id,
                "principal_id": intent.permission_context.principal_id,
            },
        }
    )
    return intent


@router.get("/report-intents/{intent_id}")
def get_report_intent(intent_id: str):
    return report_intent_repo.get(intent_id)


@router.post("/dashboards:assemble")
def assemble_dashboard_preview(req: ReportingAssembleRequest):
    result = execute_semantic_queries_from_intent(req.intent)
    dashboard = assemble_dashboard(intent=req.intent, result=result)
    return {"dashboard": dashboard}
```

- [ ] **Step 4: Re-run the integration tests**

Run: `pytest tests/integration/test_reporting_api.py tests/integration/test_chat_query_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/api/reporting.py src/app/infra/repositories/report_intent_repo.py src/app/api/chat.py src/app/main.py tests/integration/test_reporting_api.py tests/integration/test_chat_query_flow.py
git commit -m "feat: persist report intents for auto-reporting previews"
```

---

### Task 4: Persist dashboards and revisions in SQLite and add save/load endpoints

**Files:**
- Create: `src/app/infra/repositories/dashboard_repo.py`
- Modify: `src/app/api/reporting.py`
- Test: `tests/integration/test_dashboard_persistence.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
def test_create_dashboard_persists_current_and_published_revision(client):
    resp = client.post("/v1/dashboards", json=dashboard_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["dashboard_id"].startswith("dash-")
    assert body["report_intent_id"].startswith("ri-")
    stored = client.get(f"/v1/dashboards/{body['dashboard_id']}")
    assert stored.status_code == 200
    assert stored.json()["dashboard"]["version"] == "1.0"
    assert stored.json()["report_intent"]["id"] == body["report_intent_id"]
    assert stored.json()["current_revision_id"] == stored.json()["published_revision_id"]
```

- [ ] **Step 2: Run the persistence tests to confirm they fail**

Run: `pytest tests/integration/test_dashboard_persistence.py -v`
Expected: FAIL because the repository tables and save/load endpoints do not exist yet

- [ ] **Step 3: Implement repository tables and the save/load API**

```python
dashboards = Table(
    "dashboards",
    metadata,
    Column("dashboard_id", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("report_intent_id", String, nullable=False),
    Column("current_revision_id", String, nullable=False),
    Column("published_revision_id", String, nullable=False),
)

dashboard_revisions = Table(
    "dashboard_revisions",
    metadata,
    Column("revision_id", String, primary_key=True),
    Column("dashboard_id", String, nullable=False),
    Column("spec_json", Text, nullable=False),
)
```

- [ ] **Step 4: Re-run the persistence tests**

Run: `pytest tests/integration/test_dashboard_persistence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/infra/repositories/dashboard_repo.py src/app/api/reporting.py tests/integration/test_dashboard_persistence.py
git commit -m "feat: persist dashboards and revisions"
```

---

### Task 5: Scaffold the read-only web viewer app and shared TypeScript reporting types

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/index.html`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/styles.css`
- Create: `web/src/types/reporting.ts`
- Create: `web/src/components/DashboardPage.tsx`
- Create: `web/src/components/WidgetRenderer.tsx`
- Create: `web/src/test/setup.ts`
- Create: `web/src/test/fixtures/reportPreview.ts`
- Test: `web/src/components/__tests__/DashboardPage.test.tsx`

- [ ] **Step 1: Add package/config files and write the failing dashboard shell test**

```tsx
import { render, screen } from "@testing-library/react";
import { DashboardPage } from "../DashboardPage";
import { reportPreviewFixture } from "../../test/fixtures/reportPreview";

it("renders dashboard title and top-level widgets", () => {
  render(<DashboardPage dashboard={reportPreviewFixture.dashboard} />);
  expect(screen.getByText("上个月华东区毛利率是多少？")).toBeInTheDocument();
  expect(screen.getByText("核心指标")).toBeInTheDocument();
  expect(screen.getByText("分析说明")).toBeInTheDocument();
});
```

- [ ] **Step 2: Install the frontend dependencies**

Run: `cd web && npm install`
Expected: install completes and writes `package-lock.json`

- [ ] **Step 3: Run the frontend test to confirm it fails**

Run: `cd web && npm run test -- DashboardPage.test.tsx`
Expected: FAIL because `DashboardPage` and the fixture types do not exist yet

- [ ] **Step 4: Implement the app shell, shared types, and base dashboard layout**

```tsx
export function DashboardPage({ dashboard }: { dashboard: DashboardSpec }) {
  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p className="eyebrow">Auto Reporting Preview</p>
        <h1>{dashboard.title}</h1>
      </header>
      {dashboard.pages.map((page) => (
        <section key={page.id}>
          <h2>{page.title}</h2>
          <WidgetRenderer widgets={page.sections.flatMap((section) => section.widgets)} />
        </section>
      ))}
    </main>
  );
}
```

- [ ] **Step 5: Re-run the frontend test**

Run: `cd web && npm run test -- DashboardPage.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add web/package.json web/package-lock.json web/tsconfig.json web/vite.config.ts web/index.html web/src/main.tsx web/src/App.tsx web/src/styles.css web/src/types/reporting.ts web/src/test/setup.ts web/src/test/fixtures/reportPreview.ts web/src/components/__tests__/DashboardPage.test.tsx web/src/components/DashboardPage.tsx web/src/components/WidgetRenderer.tsx
git commit -m "feat: scaffold auto-reporting viewer"
```

---

### Task 6: Render abstract chart widgets through an ECharts adapter and explanation components

**Files:**
- Create: `web/src/components/MetricCardWidget.tsx`
- Create: `web/src/components/ChartWidget.tsx`
- Create: `web/src/components/InsightWidget.tsx`
- Create: `web/src/components/TextWidget.tsx`
- Create: `web/src/renderers/echartsAdapter.ts`
- Test: `web/src/renderers/__tests__/echartsAdapter.test.ts`
- Modify: `web/src/components/__tests__/DashboardPage.test.tsx`

- [ ] **Step 1: Write the failing adapter and widget tests**

```tsx
import { buildEChartsOption } from "../echartsAdapter";
import { reportPreviewFixture } from "../../test/fixtures/reportPreview";

it("maps line-family chart presentations to an ECharts option", () => {
  const dashboard = reportPreviewFixture.dashboard;
  const chartWidget = reportPreviewFixture.dashboard.pages[0].sections[0].widgets.find(
    (widget) => widget.kind === "chart",
  )!;
  const rows = getRowsForWidget(chartWidget, dashboard.data_bindings);
  const option = buildEChartsOption(chartWidget.presentation, rows);
  expect(option.xAxis.type).toBe("category");
  expect(option.series[0].type).toBe("line");
});
```

- [ ] **Step 2: Run the frontend tests to confirm they fail**

Run: `cd web && npm run test -- echartsAdapter.test.ts DashboardPage.test.tsx`
Expected: FAIL because the adapter and widget components do not exist yet

- [ ] **Step 3: Implement widget components and the ECharts adapter**

```tsx
export function getRowsForWidget(widget: Widget, bindings: DataBinding[]) {
  return bindings.find((binding) => binding.source_ref === widget.binding.source_ref)?.rows ?? [];
}

export function buildEChartsOption(presentation: ChartPresentation, rows: ChartRow[]) {
  if (presentation.family === "line") {
    return {
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: rows.map((row) => row.month) },
      yAxis: { type: "value" },
      series: [{ type: "line", data: rows.map((row) => row.value) }],
    };
  }
  return {
    dataset: { source: rows },
    xAxis: { type: "category" },
    yAxis: { type: "value" },
    series: [{ type: "bar" }],
  };
}
```

- [ ] **Step 4: Re-run the frontend tests**

Run: `cd web && npm run test -- echartsAdapter.test.ts DashboardPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/MetricCardWidget.tsx web/src/components/ChartWidget.tsx web/src/components/InsightWidget.tsx web/src/components/TextWidget.tsx web/src/renderers/echartsAdapter.ts web/src/renderers/__tests__/echartsAdapter.test.ts web/src/components/__tests__/DashboardPage.test.tsx
git commit -m "feat: render auto-report widgets with echarts"
```

---

### Task 7: Connect the viewer to preview and saved-dashboard backend endpoints

**Files:**
- Create: `web/src/api/client.ts`
- Create: `web/src/routes/PreviewPage.tsx`
- Create: `web/src/routes/DashboardPageRoute.tsx`
- Modify: `web/src/App.tsx`
- Modify: `src/app/main.py`
- Test: `web/src/components/__tests__/PreviewPage.test.tsx`

- [ ] **Step 1: Write the failing route-level tests with mocked API responses**

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../../App";

it("loads a preview dashboard from the backend", async () => {
  mockFetchPreview();
  render(
    <MemoryRouter initialEntries={["/preview?question=上个月华东区毛利率是多少？"]}>
      <App />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getByText("Auto Reporting Preview")).toBeInTheDocument());
});
```

- [ ] **Step 2: Run the route tests to confirm they fail**

Run: `cd web && npm run test -- PreviewPage.test.tsx`
Expected: FAIL because the API client and route components do not exist yet

- [ ] **Step 3: Implement the API client, routes, and backend CORS**

```tsx
export async function fetchPreview(question: string) {
  const resp = await fetch(`${API_BASE_URL}/v1/report-intents:generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_id: "t-1",
      user_id: "u-1",
      principal_id: "u-1",
      conversation_id: "preview-session",
      question,
    }),
  });
  const intent = await resp.json();
  const dashboardResp = await fetch(`${API_BASE_URL}/v1/dashboards:assemble`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent }),
  });
  return dashboardResp.json();
}
```

- [ ] **Step 4: Re-run the route tests**

Run: `cd web && npm run test -- PreviewPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/api/client.ts web/src/routes/PreviewPage.tsx web/src/routes/DashboardPageRoute.tsx web/src/App.tsx web/src/components/__tests__/PreviewPage.test.tsx src/app/main.py
git commit -m "feat: connect auto-reporting viewer to backend apis"
```

---

### Task 8: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT-STATUS.md`

- [ ] **Step 1: Update the docs to describe the new reporting protocol and viewer**

Add:
- backend reporting endpoints
- viewer setup/run instructions
- scope note that Phase 1 is read-only Viewer, not the full dashboard editor

- [ ] **Step 2: Run the backend test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Run the frontend test suite**

Run: `cd web && npm run test -- --run`
Expected: PASS

- [ ] **Step 4: Build the frontend**

Run: `cd web && npm run build`
Expected: PASS and `web/dist` is generated

- [ ] **Step 5: Commit**

```bash
git add README.md docs/PROJECT-STATUS.md web
git commit -m "docs: document auto-reporting phase 1"
```

---

## 2) Verification Checklist

- `pytest tests/unit/test_reporting_models.py -v`
- `pytest tests/unit/test_report_intent_builder.py tests/unit/test_dashboard_assembler.py -v`
- `pytest tests/integration/test_reporting_api.py tests/integration/test_dashboard_persistence.py tests/integration/test_chat_query_flow.py -v`
- `pytest -q`
- `cd web && npm run test -- --run`
- `cd web && npm run build`

Expected outcome:
- Legacy `/v1/chat/query` tests still pass
- New reporting preview/save/load endpoints pass
- Viewer renders `metric_card`, `chart`, `text`, and `insight` widgets from `dashboard_spec`
- ECharts is only used in the frontend adapter, not leaked into the backend protocol schema

---

## 3) Handoff Notes

- Keep the current sales-domain semantics as the only dataset in scope for this plan
- Do not implement `editor_state` APIs yet; only define the model so later editor work has a stable contract target
- Carry `principal_id`, `role_scope`, and `row_level_policy_ref` through `ReportIntent`, dashboard save/load, and audit events from the first implementation task onward
- If a task starts requiring drag-and-drop, collaborative editing, or generic dataset registration, stop and create a new spec/plan instead of expanding this one in place
