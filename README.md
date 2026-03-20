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

## Canonical documents

- RFP: `docs/RFP.md`
- Approved design spec: `docs/superpowers/specs/2026-03-20-phase1-sales-copilot-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-20-phase1-sales-copilot.md`
- Extra MVP scenario spec: `docs/superpowers/specs/2026-03-20-agentic-bi-sales-pricing-design.md`

## Repository status

This repository currently contains product/docs baseline and implementation plan. Application code is planned under:

- `src/app/` for services/API/domain logic
- `tests/` for unit + integration tests

See `docs/PROJECT-STATUS.md` for progress details.

## License

See `LICENSE`.
