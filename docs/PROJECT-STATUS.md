# Project Status

_Last updated: 2026-03-22_

## Current stage

- **Requirements:** complete (`docs/RFP.md`)
- **Design:** complete and approved for base sales-copilot plus Auto Reporting Phase 1
- **Implementation plan:** complete (`docs/superpowers/plans/2026-03-20-phase1-sales-copilot.md`, `docs/superpowers/plans/2026-03-21-auto-reporting-phase1.md`)
- **Code implementation:** complete for the current Auto Reporting Phase 1 plan on `feature/phase1-sales-copilot`, pending final integration decision

## What is done

1. Product-level RFP captured and versioned
2. Phase 1 sales-copilot design written and approved
3. Detailed TDD implementation plan written
4. Repository connected to remote GitHub and synchronized
5. Phase 1 MVP service scaffold, parsing, planning, validation, execution, response generation, and follow-up memory implemented
6. Audit logging now persists to SQLite and is covered by integration tests
7. Python test suite is runnable via `pytest` with repository-local configuration
8. Direct question coverage now includes scalar answers, recent-three-month trends, month-over-month comparisons, and year-over-year comparisons
9. Follow-up coverage now includes region switch, monthly trend view, and `环比/同比` comparative follow-ups
10. Incomplete metric questions now return a minimal clarification response instead of a generic unknown-metric failure
11. Grouped-dimension questions now support direct and follow-up `按渠道看` breakdowns, with invalid multi-dimension combinations rejected by structured error code
12. Validation failures now return recovery guidance for unknown metrics and invalid dimension combinations
13. Semantic parsing now accepts revenue aliases such as `营收` / `收入` and broader grouping phrasing such as `按销售渠道看`
14. Time-window and comparison parsing now accepts natural phrasings such as `最近三个月`, `和上月比`, and `和去年同期比`
15. Grouped breakdown coverage now includes region-level views such as `按区域看` / `按大区看`
16. Metric coverage now includes direct and follow-up queries for `毛利额`
17. Recovery guidance now supports targeted repair suggestions for invalid dimension combinations and near-miss metric terms such as `利润率`
18. Acceptance coverage now explicitly includes `毛利额` 的趋势/同比链路和 `按品类看` 的 direct/follow-up 分组链路
19. Proactive insight extension foundations implemented: anomaly event model, rule engine, attribution service, card persistence, monitor flow, and RBAC-scoped insight API
20. Reporting protocol models, report-intent builder, and dashboard assembler implemented for the governed auto-reporting flow
21. Reporting APIs implemented for intent generation, dashboard preview assembly, dashboard save, and saved-dashboard fetch, with RBAC-safe permission-context enforcement and audit coverage
22. Dashboard persistence now stores current and published revisions in SQLite while safely reusing existing report intents for the same owner
23. `/v1/chat/query` remains backward compatible while attaching report preview payloads for the new reporting flow
24. Read-only web viewer implemented with `/preview` and `/dashboards/:dashboardId` routes plus ECharts rendering for `metric_card`, `chart`, `insight`, and `text` widgets
25. End-to-end verification for the current plan now passes across backend tests, frontend tests, and frontend production build

## What is next

1. Run final review / integration decision for `feature/phase1-sales-copilot`
2. Merge `feature/phase1-sales-copilot` back to `main` when approved
3. Start the next phase only after this branch is closed out cleanly

## Out-of-scope now

- Proactive anomaly detection (Phase 2)
- Cross-system action orchestration and approval execution flows (Phase 3)
- Multi-domain expansion beyond sales
- Full dashboard editor, drag-and-drop layout editing, and editor-state APIs

## Success criteria for this stage

- Canonical plan remains the source of truth for implementation
- Each implementation task includes tests and verification before merge
- Feature branch remains mergeable into `main` without losing project documentation baselines
- Auto Reporting Phase 1 remains read-only and governed, with protocol/viewer work separated from future editor capabilities
