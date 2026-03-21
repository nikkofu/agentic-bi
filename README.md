# Agentic BI

Agentic BI is a decision-intelligence product prototype that upgrades traditional ChatBI from passive query/visualization into an active, governable business copilot.

Current focus is **Phase 1 (Sales Copilot)**: high-accuracy, traceable, RBAC-safe natural-language metric Q&A in the sales domain.

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

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi pydantic pytest "httpx<0.28" sqlalchemy uvicorn
uvicorn app.main:app --reload --app-dir src
```

## Test

```bash
pytest tests -v
```

## Canonical documents

- RFP: `docs/RFP.md`
- Approved design spec: `docs/superpowers/specs/2026-03-20-phase1-sales-copilot-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-20-phase1-sales-copilot.md`
- Extra MVP scenario spec: `docs/superpowers/specs/2026-03-20-agentic-bi-sales-pricing-design.md`
- Project status: `docs/PROJECT-STATUS.md`

## License

See `LICENSE`.
