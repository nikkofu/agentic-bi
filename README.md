# Agentic BI

Agentic BI is a decision-intelligence product prototype that upgrades traditional ChatBI from passive query/visualization into an active, governable business copilot.

Current focus is **Phase 1 (Sales Copilot)** plus the first **Phase 2 proactive diagnostic-report** slice: high-accuracy, traceable, RBAC-safe natural-language metric Q&A in the sales domain, extended with proactive insight cards, default diagnostic report snapshots, and a canonical read-only report viewer.

## Why this project

Traditional ChatBI stops at "Text-to-SQL/Chart". This project targets a stronger loop:

`Question -> structured intent -> validated metric query -> explainable answer/chart -> auditable trace`

Phase 2/3 (from RFP) extend toward proactive diagnosis and execution workflows.

## Current scope (Phase 1)

- Sales-domain metrics and dimensions only
- Text-to-Metrics architecture (semantic layer first, not free-form SQL)
- Follow-up question continuity in conversation
- RBAC-aware query validation
- Full audit trail per request
- Auto-reporting protocol documents built from the same governed query pipeline
- Read-only dashboard preview/save/load flows
- Separate viewer app for previewing and loading saved dashboards

## Auto Reporting Phase 1 scope note

This phase delivers a **read-only viewer**, not a full dashboard editor. It intentionally does **not** include drag-and-drop layout editing, editor-state APIs, arbitrary dataset onboarding, or raw model chain-of-thought exposure.

## Current implementation

- Natural-language sales intent parsing
- Query-plan construction and validation
- Deterministic fixture-backed execution
- Narrative/chart response building for scalar answers, grouped breakdowns, and monthly trends
- Direct questions for last-month values, grouped region/channel/category breakdowns, recent-three-month trends, month-over-month comparisons, and year-over-year comparisons
- Core metric coverage for `毛利率`, `销售额`, and `毛利额`
- Revenue alias coverage for `销售额` / `营收` / `收入`, plus broader grouping phrasing such as `按销售渠道看`
- Broader time and comparison phrasing such as `最近三个月...走势`, `和上月比`, and `和去年同期比`
- Conversation follow-up memory for region switch, grouped breakdown view, monthly trend view, and `环比/同比` follow-up questions across the supported metrics
- Audit event logging with trace IDs and SQLite persistence
- Recovery guidance for missing metrics, unknown metrics, and invalid multi-dimension grouping requests, including targeted repair suggestions for near-miss metric terms and invalid dimension combinations
- Proactive insight pipeline primitives: rule-based anomaly detection, single-layer attribution, insight card generation, monitor orchestration, and RBAC-scoped insight listing API
- Reporting protocol layer with `ReportIntent`, `DashboardSpec`, and `EditorState` models
- Reporting endpoints for generating report intents, assembling dashboard previews, persisting dashboards, and fetching saved dashboards
- SQLite-backed dashboard persistence with revision tracking, audit logging, and permission-context checks to prevent access widening or drift leakage
- Read-only Vite + React viewer with routes for live preview and saved-dashboard rendering
- Frontend widget rendering for `metric_card`, `chart`, `insight`, and `text` widgets through an ECharts adapter

## Backend run

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi pydantic pytest "httpx<0.28" sqlalchemy uvicorn
uvicorn app.main:app --reload --app-dir src
```

The backend now exposes these reporting endpoints in addition to the existing chat and insight APIs:

- `POST /v1/report-intents:generate`
- `GET /v1/report-intents/{intent_id}`
- `POST /v1/dashboards:assemble`
- `POST /v1/dashboards`
- `GET /v1/dashboards/{dashboard_id}`
- `POST /v1/reports:generate`
- `GET /v1/reports/{report_id}`
- `GET /v1/insights/cards/{card_id}`

For local viewer development, CORS defaults allow:

- `http://127.0.0.1:5173`
- `http://localhost:5173`
- `http://127.0.0.1:4173`
- `http://localhost:4173`

Override with `AGENTIC_BI_DEV_VIEWER_ORIGINS=origin1,origin2` if needed.

## Viewer run

```bash
cd web
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

Viewer routes:

- `/preview?question=上个月华东区毛利率是多少？`
- `/reports/:reportId`
- `/dashboards/:dashboardId` (lower-level compatibility route for direct dashboard viewing)

## Test & build

```bash
.venv/bin/pytest -q
cd web && npm run test -- --run
cd web && npm run build
```

## Canonical documents

- RFP: `docs/RFP.md`
- Base sales-copilot design: `docs/superpowers/specs/2026-03-20-phase1-sales-copilot-design.md`
- Auto-reporting design: `docs/superpowers/specs/2026-03-21-agentic-bi-auto-reporting-protocol-design.md`
- Proactive diagnostic-report design: `docs/superpowers/specs/2026-03-22-proactive-diagnostic-report-design.md`
- Base sales-copilot implementation plan: `docs/superpowers/plans/2026-03-20-phase1-sales-copilot.md`
- Auto-reporting implementation plan: `docs/superpowers/plans/2026-03-21-auto-reporting-phase1.md`
- Proactive diagnostic-report implementation plan: `docs/superpowers/plans/2026-03-22-proactive-diagnostic-report.md`
- Extra MVP scenario spec: `docs/superpowers/specs/2026-03-20-agentic-bi-sales-pricing-design.md`
- Project status: `docs/PROJECT-STATUS.md`

## License

See `LICENSE`.
