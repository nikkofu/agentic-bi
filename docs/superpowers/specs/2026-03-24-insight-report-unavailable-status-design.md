# Insight Report Unavailable Status Design

**Date:** 2026-03-24
**Project:** agentic-bi
**Scope:** Make lazy diagnostic-report failures explicit in insight-card API responses without changing the saved-report API contract

---

## 1. Problem

Today `/v1/insights/cards` and `/v1/insights/cards/{card_id}` expose only two implicit states:
- report fields populated: a saved diagnostic report is available
- report fields empty / `report_summary = null`: either no report exists yet, or lazy generation failed

That ambiguity is now misleading because the backend deliberately keeps cards visible when lazy report creation fails. The UI and any API consumer can no longer distinguish:
- "report not attempted yet"
- "report generation failed and fallback behavior kept the card visible"

This weakens the Phase 2 Analyst contract. The system can detect and audit the failure, but it still hides the outcome behind missing fields.

## 2. Goal

Expose an explicit insight-card level report availability state so list/detail consumers can distinguish between:
- ready-to-open diagnostic reports
- currently unavailable diagnostic reports caused by lazy generation failure

The change must stay narrow:
- no `/v1/reports/{report_id}` contract change
- no new report viewer states in this slice
- no retry orchestration or background repair flow

## 3. Chosen Design

Add two flat fields to the insight-card API payload:
- `report_status`
- `report_error_code`

This keeps the change small and compatible with the existing payload shape while making the failure state explicit.

### 3.1 Field semantics

`report_status` values:
- `"ready"`: `report_id`, `dashboard_id`, and contextual `detail_url` are present and openable
- `"unavailable"`: lazy report creation failed during list/detail hydration, and the card is intentionally returned without a report link

`report_error_code` values:
- `null` when `report_status == "ready"`
- a structured error code when `report_status == "unavailable"`

For this slice, the expected unavailable code is:
- `DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED`

If future lazy-generation failures are caused by permission or validation issues, the same field can carry those existing structured error codes without further response-shape changes.

## 4. API Contract Changes

### 4.1 `GET /v1/insights/cards`

Every card item gains:
- `report_status: "ready" | "unavailable"`
- `report_error_code: string | null`

Rules:
- when hydration attaches a report snapshot successfully:
  - `report_status = "ready"`
  - `report_error_code = null`
- when hydration fails but the card remains visible:
  - `report_status = "unavailable"`
  - `report_error_code = <structured failure code>`
  - `report_id = null`
  - `dashboard_id = null`
  - `detail_url = null`

### 4.2 `GET /v1/insights/cards/{card_id}`

The `card` object gains the same fields:
- `report_status`
- `report_error_code`

Rules:
- successful hydration:
  - `card.report_status = "ready"`
  - `card.report_error_code = null`
  - `report_summary` remains populated
- lazy-generation failure:
  - `card.report_status = "unavailable"`
  - `card.report_error_code = <structured failure code>`
  - `report_summary = null`

### 4.3 No change to report document endpoints

This design does **not** change:
- `GET /v1/reports/{report_id}`
- `POST /v1/reports:generate`
- report viewer payload types

The unavailable state belongs to the insight-card linkage layer, not the saved-report document contract.

For this slice, insight-card API responses should always emit one of the two explicit states:
- `ready`
- `unavailable`

`null` is allowed only as an internal default before API hydration logic enriches the payload. It is not part of the intended list/detail response contract.

## 5. Backend Design

### 5.1 Insight model and repository payload

Extend `InsightCard` with:
- `report_status: str | None = None`
- `report_error_code: str | None = None`

Repository-returned card dictionaries should also carry those fields so API handlers can pass them through consistently.

No database schema migration is required in this slice because the state is derived during API hydration, not persisted to `insight_cards`.

### 5.2 Insight API behavior

In `src/app/api/insights.py`:
- on successful lazy hydration, enrich the returned card with:
  - `report_status = "ready"`
  - `report_error_code = None`
- on lazy hydration failure, keep the existing fallback behavior, but now return:
  - `report_status = "unavailable"`
  - `report_error_code = _lazy_report_failure_error_code(exc)`
  - all report linkage fields cleared to `None`

The existing lazy-failure audit event stays in place.

The error-code mapping for `_lazy_report_failure_error_code(exc)` should be deterministic:

| Exception shape | Returned code |
|-----------------|---------------|
| `ValueError` | `str(exc)` |
| `PermissionError` | `str(exc)` |
| any repository / persistence / unexpected failure | `DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED` |

This keeps the card API aligned with the structured report-generation failure code already used elsewhere in the reports API and audit trail.

## 6. Frontend Design

For this slice, frontend types should understand the new fields so the UI can safely consume them later:
- extend the insight-card type definitions in `web/src/types/reporting.ts`

No UI behavior change is required yet. The current viewer pages can ignore the new fields.
There is no existing insight-card frontend consumer that must render these states in this slice; the type change is contract-defensive so later UI work can consume the explicit status without another backend contract change.

This keeps the slice focused on making the API contract explicit without coupling it to a new visual design decision.

## 7. Testing

### Backend integration tests

Add or update tests so they verify:
- list/detail return `report_status = "ready"` and `report_error_code = null` when a report link is available
- lazy-failure fallback returns `report_status = "unavailable"` and `report_error_code = DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED`
- `report_summary` remains `null` for the unavailable detail state

### Unit / contract tests

Extend insight-card model contract coverage so the new fields are part of the explicit API shape.

## 8. Non-Goals

This design does not add:
- background retry
- explicit `"pending"` state
- viewer UX for unavailable reports
- persisted report-health metadata in `insight_cards`
- report regeneration or repair endpoints

Those can be layered later if the product needs them, but they are outside this narrowing step.
