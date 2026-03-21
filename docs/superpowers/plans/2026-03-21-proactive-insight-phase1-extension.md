# Proactive Insight Phase 1 Extension Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rule-first proactive insight pipeline that detects sales metric anomalies, produces single-layer attribution, and publishes auditable insight cards without breaking existing chat query behavior.

**Architecture:** Add a background-friendly insight pipeline alongside the existing chat path: monitor snapshot inputs, run anomaly rule checks, generate normalized anomaly events, compute single-dimension attribution, and persist/publish insight cards. Reuse existing metric/query primitives where possible, and isolate new proactive modules to avoid inflating `src/app/api/chat.py` complexity.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, SQLite/SQLAlchemy Core, existing app service modules

---

## 0) File Structure & Responsibilities

### Create
- `src/app/domain/insight_models.py` — Pydantic models for anomaly events, attribution payload, and insight cards
- `src/app/services/insight_rules.py` — rule evaluation functions (absolute threshold, delta threshold, severity mapping)
- `src/app/services/insight_monitor.py` — monitor orchestration for pulling metric snapshots and emitting anomaly candidates
- `src/app/services/insight_attribution.py` — single-layer attribution calculation (region/channel/category)
- `src/app/services/insight_cards.py` — card builder and publish payload formatter
- `src/app/infra/repositories/insight_repo.py` — persistence for generated insight cards/events
- `src/app/api/insights.py` — read endpoints for insight cards (list/detail)
- `tests/unit/test_insight_rules.py`
- `tests/unit/test_insight_attribution.py`
- `tests/unit/test_insight_cards.py`
- `tests/integration/test_insight_generation_flow.py`
- `tests/integration/test_insight_visibility_rbac.py`

### Modify
- `src/app/main.py` — register proactive insight API router
- `src/app/infra/db.py` — support insight table creation helper usage
- `src/app/services/audit_log.py` — optionally support proactive insight audit event type
- `src/app/services/query_executor.py` — expose reusable aggregate helpers for monitor/attribution reuse (without changing query behavior)
- `README.md` — document proactive insight run/test usage
- `docs/PROJECT-STATUS.md` — update stage progress and new capability summary

### Keep unchanged for this plan
- `src/app/api/chat.py` core behavior except optional non-breaking integration hooks
- existing follow-up parsing/response logic unless required by proactive card deep-link behavior

---

## 1) Plan Guardrails

- Do **not** expand into automated action execution (Phase 3 behavior).
- Do **not** add model-based anomaly scoring; stick to rule-first detection.
- Keep attribution depth to exactly one dimension level.
- Preserve existing chat integration tests as-is; proactive additions must be additive.

---

## 2) Task Sequence (TDD, one action per step)

### Task 1: Define proactive insight domain contracts

**Files:**
- Create: `src/app/domain/insight_models.py`
- Test: `tests/unit/test_insight_rules.py`

- [ ] **Step 1: Write failing unit test for anomaly event model shape**

```python
from app.domain.insight_models import AnomalyEvent

def test_anomaly_event_model_contract():
    event = AnomalyEvent(
        metric="gross_margin_rate",
        scope={"region": "华东"},
        current_value=0.31,
        baseline_value=0.28,
        delta=0.03,
        severity="P2",
        trigger_rule="delta_threshold"
    )
    assert event.metric == "gross_margin_rate"
    assert event.scope["region"] == "华东"
```

- [ ] **Step 2: Run unit test to verify RED**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_rules.py::test_anomaly_event_model_contract -v`
Expected: FAIL with `ModuleNotFoundError` or missing model

- [ ] **Step 3: Implement minimal insight models**

```python
class AnomalyEvent(BaseModel):
    metric: str
    scope: dict[str, str]
    current_value: float
    baseline_value: float
    delta: float
    severity: str
    trigger_rule: str
```

- [ ] **Step 4: Re-run test to verify GREEN**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_rules.py::test_anomaly_event_model_contract -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/domain/insight_models.py tests/unit/test_insight_rules.py
git commit -m "feat: define proactive insight domain models"
```

---

### Task 2: Implement rule-first anomaly detection engine

**Files:**
- Create: `src/app/services/insight_rules.py`
- Test: `tests/unit/test_insight_rules.py`

- [ ] **Step 1: Add failing tests for threshold rules and severity mapping**

```python
def test_delta_threshold_triggers_event():
    event = evaluate_anomaly(
        metric="gross_margin_rate",
        current_value=0.24,
        baseline_value=0.30,
        abs_threshold=None,
        delta_threshold=0.04,
        scope={"region": "华东"}
    )
    assert event is not None
    assert event.severity in {"P1", "P2", "P3"}
```

- [ ] **Step 2: Run tests to verify RED**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_rules.py -v`
Expected: FAIL with missing evaluator

- [ ] **Step 3: Implement minimal evaluator and severity helper**

```python
def evaluate_anomaly(...):
    delta = current_value - baseline_value
    if abs_threshold is not None and current_value < abs_threshold:
        return build_event(...)
    if abs(delta) >= delta_threshold:
        return build_event(...)
    return None
```

- [ ] **Step 4: Re-run tests to verify GREEN**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_rules.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/insight_rules.py tests/unit/test_insight_rules.py
git commit -m "feat: add rule-first anomaly detection engine"
```

---

### Task 3: Build single-layer attribution service

**Files:**
- Create: `src/app/services/insight_attribution.py`
- Test: `tests/unit/test_insight_attribution.py`
- Modify: `src/app/services/query_executor.py` (only if helper extraction is needed)

- [ ] **Step 1: Add failing unit test for top-contributor attribution**

```python
def test_single_layer_attribution_returns_top_dimension_item():
    rows = [
        {"region": "华东", "value": -120},
        {"region": "华南", "value": -30},
    ]
    item = compute_single_layer_attribution(rows, dimension="region")
    assert item["dimension"] == "region"
    assert item["key"] == "华东"
```

- [ ] **Step 2: Run test to verify RED**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_attribution.py -v`
Expected: FAIL with missing module/function

- [ ] **Step 3: Implement minimal attribution selector**

```python
def compute_single_layer_attribution(rows, dimension):
    best = max(rows, key=lambda r: abs(r.get("value", 0)))
    return {"dimension": dimension, "key": best[dimension], "contribution": best["value"]}
```

- [ ] **Step 4: Re-run test to verify GREEN**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_attribution.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/insight_attribution.py tests/unit/test_insight_attribution.py src/app/services/query_executor.py
git commit -m "feat: add single-layer attribution service"
```

---

### Task 4: Build insight card generator and repository persistence

**Files:**
- Create: `src/app/services/insight_cards.py`
- Create: `src/app/infra/repositories/insight_repo.py`
- Modify: `src/app/infra/db.py`
- Test: `tests/unit/test_insight_cards.py`

- [ ] **Step 1: Add failing unit test for card payload contract**

```python
def test_card_builder_outputs_required_fields():
    card = build_insight_card(event=event, attribution=attribution)
    assert card["summary"]
    assert card["severity"] == event.severity
    assert card["suggested_next_question"]
```

- [ ] **Step 2: Run tests to verify RED**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_cards.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal card builder and SQLite repository**

```python
def build_insight_card(event, attribution):
    return {
        "metric": event.metric,
        "severity": event.severity,
        "summary": ...,
        "attribution": attribution,
        "suggested_next_question": ...
    }
```

- [ ] **Step 4: Re-run tests to verify GREEN**

Run: `PYTHONPATH=src pytest tests/unit/test_insight_cards.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/insight_cards.py src/app/infra/repositories/insight_repo.py src/app/infra/db.py tests/unit/test_insight_cards.py
git commit -m "feat: add insight card builder and persistence"
```

---

### Task 5: Implement monitor orchestration and end-to-end generation flow

**Files:**
- Create: `src/app/services/insight_monitor.py`
- Test: `tests/integration/test_insight_generation_flow.py`
- Modify: `src/app/services/audit_log.py` (if proactive audit event type needed)

- [ ] **Step 1: Add failing integration test for monitor -> persisted card flow**

```python
def test_monitor_generates_and_persists_insight_card(tmp_path, monkeypatch):
    count = run_monitor_once(...)
    assert count == 1
    cards = list_insight_cards(...)
    assert len(cards) == 1
```

- [ ] **Step 2: Run test to verify RED**

Run: `PYTHONPATH=src pytest tests/integration/test_insight_generation_flow.py -v`
Expected: FAIL

- [ ] **Step 3: Implement monitor orchestration with cooldown filter**

```python
def run_monitor_once(config):
    snapshots = fetch_metric_snapshots(...)
    for snap in snapshots:
        event = evaluate_anomaly(...)
        if event and not in_cooldown(event):
            ... persist card ...
```

- [ ] **Step 4: Re-run test to verify GREEN**

Run: `PYTHONPATH=src pytest tests/integration/test_insight_generation_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/insight_monitor.py tests/integration/test_insight_generation_flow.py src/app/services/audit_log.py
git commit -m "feat: add proactive insight monitor orchestration"
```

---

### Task 6: Expose insight card read APIs with RBAC visibility

**Files:**
- Create: `src/app/api/insights.py`
- Modify: `src/app/main.py`
- Test: `tests/integration/test_insight_visibility_rbac.py`

- [ ] **Step 1: Add failing integration tests for scoped card listing**

```python
def test_insight_list_only_returns_in_scope_cards(client):
    resp = client.get("/v1/insights/cards", params={"user_id": "u-south", "tenant_id": "t-1"})
    assert resp.status_code == 200
    assert all(card["scope"]["region"] == "华南" for card in resp.json()["items"])
```

- [ ] **Step 2: Run tests to verify RED**

Run: `PYTHONPATH=src pytest tests/integration/test_insight_visibility_rbac.py -v`
Expected: FAIL

- [ ] **Step 3: Implement insight list/detail endpoints with access policy filtering**

```python
@router.get("/cards")
def list_cards(user_id: str, tenant_id: str):
    allowed = resolve_allowed_regions(user_id, tenant_id)
    return repo.list_by_regions(allowed)
```

- [ ] **Step 4: Re-run tests to verify GREEN**

Run: `PYTHONPATH=src pytest tests/integration/test_insight_visibility_rbac.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/api/insights.py src/app/main.py tests/integration/test_insight_visibility_rbac.py
git commit -m "feat: add rbac-scoped proactive insight APIs"
```

---

### Task 7: Full regression and documentation updates

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT-STATUS.md`
- Modify: `tests/` (only if missing deterministic setup)

- [ ] **Step 1: Add failing regression assertion for no chat API breakage (if absent)**

```python
def test_existing_chat_contract_still_works(...):
    ...
```

- [ ] **Step 2: Run full test suite to verify RED (if new assertion added) or baseline**

Run: `PYTHONPATH=src pytest tests -v`
Expected: Either fail on newly added assertion, or pass baseline before final docs

- [ ] **Step 3: Implement minimal compatibility fix (only if failing)**

```python
# small compatibility patch only
```

- [ ] **Step 4: Run full test suite final verification**

Run: `PYTHONPATH=src pytest tests -v`
Expected: PASS

- [ ] **Step 5: Update docs with proactive insight usage**

```markdown
## Proactive insights
- Trigger monitor run
- Query /v1/insights/cards
- Interpret severity and attribution
```

- [ ] **Step 6: Commit**

```bash
git add README.md docs/PROJECT-STATUS.md tests
git commit -m "chore: finalize proactive insight docs and regression gate"
```

---

## 3) Validation Matrix (spec alignment)

- Rule-first anomaly detection: Tasks 1-2
- Single-layer attribution: Task 3
- Insight card generation: Task 4
- End-to-end monitor flow: Task 5
- RBAC card visibility: Task 6
- Regression safety + docs: Task 7

---

## 4) Execution commands reference

- Setup: `python -m venv .venv && source .venv/bin/activate && pip install fastapi pydantic pytest "httpx<0.28" sqlalchemy uvicorn`
- Run API: `PYTHONPATH=src uvicorn app.main:app --reload`
- Run single unit suite: `PYTHONPATH=src pytest tests/unit/test_insight_rules.py -v`
- Run single integration suite: `PYTHONPATH=src pytest tests/integration/test_insight_generation_flow.py -v`
- Run full suite: `PYTHONPATH=src pytest tests -v`
