# Phase 1 Sales Copilot Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Phase 1 sales-domain BI copilot that answers natural-language metric questions with high accuracy via a semantic metrics API path, supports follow-up questions, enforces RBAC, and emits auditable query traces.

**Architecture:** Use a Text-to-Metrics pipeline (not free-form SQL generation): intent parser -> query planner DSL -> validator (schema + permission) -> metrics query adapter -> response narrator/chart config builder. Keep stateful conversation context as lightweight plan deltas for follow-up turns. Add explicit audit records for every request lifecycle.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, SQLite (dev), SQLAlchemy Core (query adapter), httpx (API test client)

---

## 0) File Structure & Responsibilities

### New files
- `src/app/main.py` — FastAPI app bootstrap and route registration
- `src/app/api/chat.py` — `/v1/chat/query` endpoint, request/response orchestration
- `src/app/domain/models.py` — Pydantic domain models (intent, query plan, result, audit)
- `src/app/domain/metrics_catalog.py` — sales metric/dimension registry and version metadata
- `src/app/services/intent_parser.py` — natural-language to structured intent extraction
- `src/app/services/query_planner.py` — intent -> query plan DSL generation
- `src/app/services/query_validator.py` — plan validation + RBAC scope checks
- `src/app/services/query_executor.py` — query adapter calling semantic metrics backend
- `src/app/services/response_builder.py` — narrative summary + chart config generation
- `src/app/services/conversation_memory.py` — follow-up rewrite via previous query plan
- `src/app/services/audit_log.py` — audit event build/persist API
- `src/app/infra/db.py` — SQLite engine/session setup (dev)
- `src/app/infra/repositories/audit_repo.py` — audit record persistence
- `tests/unit/test_intent_parser.py`
- `tests/unit/test_query_planner.py`
- `tests/unit/test_query_validator.py`
- `tests/unit/test_response_builder.py`
- `tests/unit/test_conversation_memory.py`
- `tests/integration/test_chat_query_flow.py`
- `tests/integration/test_rbac_enforcement.py`
- `tests/integration/test_audit_logging.py`
- `tests/fixtures/sales_metrics.json` — deterministic fixture dataset
- `README.md` — setup/run/test instructions for this MVP

### Optional split if file grows
- `src/app/services/planning_rules.py` — parser/planner rule tables
- `src/app/services/chart_templates.py` — chart strategy catalog

---

## 1) Delivery Sequence (TDD, small steps, frequent commits)

### Task 1: Bootstrap service skeleton

**Files:**
- Create: `src/app/main.py`
- Create: `src/app/api/chat.py`
- Create: `src/app/domain/models.py`
- Test: `tests/integration/test_chat_query_flow.py`

- [ ] **Step 1: Write failing integration test for endpoint contract**

```python
# tests/integration/test_chat_query_flow.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_query_contract_returns_200_and_required_fields():
    payload = {
        "user_id": "u-1",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-1"
    }
    resp = client.post("/v1/chat/query", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "chart" in body
    assert "trace_id" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_chat_query_flow.py::test_chat_query_contract_returns_200_and_required_fields -v`
Expected: FAIL (module/app not found or route not implemented)

- [ ] **Step 3: Add minimal app + route + response model**

```python
# src/app/main.py
from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI()
app.include_router(chat_router)
```

```python
# src/app/api/chat.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/chat")

class QueryRequest(BaseModel):
    user_id: str
    tenant_id: str
    question: str
    conversation_id: str

@router.post("/query")
def query(req: QueryRequest):
    return {"answer": "stub", "chart": {"type": "table", "data": []}, "trace_id": "stub-trace"}
```

- [ ] **Step 4: Re-run test to verify pass**

Run: `pytest tests/integration/test_chat_query_flow.py::test_chat_query_contract_returns_200_and_required_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/main.py src/app/api/chat.py tests/integration/test_chat_query_flow.py
git commit -m "feat: bootstrap chat query endpoint contract"
```

---

### Task 2: Implement metrics catalog + intent parser (sales domain only)

**Files:**
- Create: `src/app/domain/metrics_catalog.py`
- Create: `src/app/services/intent_parser.py`
- Test: `tests/unit/test_intent_parser.py`
- Fixture: `tests/fixtures/sales_metrics.json`

- [ ] **Step 1: Write failing parser tests for metric/dimension/time extraction**

```python
def test_parse_margin_rate_for_region_last_month():
    intent = parse_intent("上个月华东区毛利率是多少？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
```

- [ ] **Step 2: Run parser tests to confirm failure**

Run: `pytest tests/unit/test_intent_parser.py -v`
Expected: FAIL (parse_intent missing)

- [ ] **Step 3: Implement minimal catalog and rule-based parser**

```python
# metric aliases example
ALIASES = {
  "毛利率": "gross_margin_rate",
  "销售额": "revenue",
}
```

- [ ] **Step 4: Re-run parser tests**

Run: `pytest tests/unit/test_intent_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/domain/metrics_catalog.py src/app/services/intent_parser.py tests/unit/test_intent_parser.py tests/fixtures/sales_metrics.json
git commit -m "feat: add sales metric catalog and intent parser"
```

---

### Task 3: Implement query plan DSL + validator (including RBAC)

**Files:**
- Create: `src/app/services/query_planner.py`
- Create: `src/app/services/query_validator.py`
- Test: `tests/unit/test_query_planner.py`
- Test: `tests/unit/test_query_validator.py`
- Modify: `src/app/domain/models.py`

- [ ] **Step 1: Write failing tests for planner output schema and sort/compare fields**

```python
def test_planner_outputs_structured_plan():
    plan = build_query_plan(intent)
    assert plan.metric == "gross_margin_rate"
    assert plan.group_by == ["category"]
    assert plan.compare_to == "prev_month"
```

- [ ] **Step 2: Write failing validator tests for unauthorized region access**

```python
def test_validator_blocks_out_of_scope_region():
    with pytest.raises(PermissionError):
        validate_plan(plan, allowed_regions=["华南"])
```

- [ ] **Step 3: Run tests and confirm failures**

Run: `pytest tests/unit/test_query_planner.py tests/unit/test_query_validator.py -v`
Expected: FAIL

- [ ] **Step 4: Implement planner + validator with explicit error codes**

```python
class ValidationErrorCode(str, Enum):
    UNKNOWN_METRIC = "UNKNOWN_METRIC"
    INVALID_DIMENSION_COMBO = "INVALID_DIMENSION_COMBO"
    PERMISSION_DENIED = "PERMISSION_DENIED"
```

- [ ] **Step 5: Re-run tests**

Run: `pytest tests/unit/test_query_planner.py tests/unit/test_query_validator.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/app/services/query_planner.py src/app/services/query_validator.py src/app/domain/models.py tests/unit/test_query_planner.py tests/unit/test_query_validator.py
git commit -m "feat: add query plan DSL and rbac-aware validator"
```

---

### Task 4: Implement query execution adapter + deterministic sales fixture backend

**Files:**
- Create: `src/app/services/query_executor.py`
- Test: `tests/integration/test_chat_query_flow.py`
- Test: `tests/integration/test_rbac_enforcement.py`
- Fixture: `tests/fixtures/sales_metrics.json`

- [ ] **Step 1: Add failing integration tests for actual numeric response and scope filter**

```python
def test_query_returns_value_from_fixture_backend():
    ...
    assert body["answer"].startswith("上个月华东区毛利率")
```

- [ ] **Step 2: Run integration tests to confirm fail**

Run: `pytest tests/integration/test_chat_query_flow.py tests/integration/test_rbac_enforcement.py -v`
Expected: FAIL

- [ ] **Step 3: Implement executor that reads semantic metric + scoped filter from fixture source**

```python
def execute_query(plan, scope):
    rows = load_sales_fixture()
    rows = apply_scope(rows, scope)
    return aggregate(rows, plan)
```

- [ ] **Step 4: Re-run integration tests**

Run: `pytest tests/integration/test_chat_query_flow.py tests/integration/test_rbac_enforcement.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/query_executor.py tests/integration/test_chat_query_flow.py tests/integration/test_rbac_enforcement.py tests/fixtures/sales_metrics.json
git commit -m "feat: add scoped query executor with deterministic fixture backend"
```

---

### Task 5: Implement response builder (narrative + chart strategy)

**Files:**
- Create: `src/app/services/response_builder.py`
- Test: `tests/unit/test_response_builder.py`
- Modify: `src/app/api/chat.py`

- [ ] **Step 1: Add failing unit tests for chart selection and narrative format**

```python
def test_builder_selects_line_chart_for_time_series():
    payload = build_response(result_time_series)
    assert payload.chart["type"] == "line"
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/unit/test_response_builder.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal chart strategy + narrative template**

```python
if result.has_time_series:
    chart_type = "line"
elif result.has_rank:
    chart_type = "bar"
else:
    chart_type = "table"
```

- [ ] **Step 4: Re-run tests**

Run: `pytest tests/unit/test_response_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/response_builder.py src/app/api/chat.py tests/unit/test_response_builder.py
git commit -m "feat: add narrative and chart response builder"
```

---

### Task 6: Implement conversation follow-up memory (plan delta rewrite)

**Files:**
- Create: `src/app/services/conversation_memory.py`
- Test: `tests/unit/test_conversation_memory.py`
- Modify: `src/app/api/chat.py`

- [ ] **Step 1: Add failing tests for follow-up replacement behavior**

```python
def test_followup_replaces_region_from_previous_plan():
    prev = QueryPlan(filters={"region": "华东"})
    nxt = apply_followup("那华南呢", prev)
    assert nxt.filters["region"] == "华南"
```

- [ ] **Step 2: Run tests to confirm fail**

Run: `pytest tests/unit/test_conversation_memory.py -v`
Expected: FAIL

- [ ] **Step 3: Implement memory store + delta-apply logic**

```python
# key by conversation_id, store last validated query plan
memory[conversation_id] = plan
```

- [ ] **Step 4: Re-run tests**

Run: `pytest tests/unit/test_conversation_memory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/conversation_memory.py src/app/api/chat.py tests/unit/test_conversation_memory.py
git commit -m "feat: add follow-up query plan memory"
```

---

### Task 7: Add audit persistence and full request lifecycle logging

**Files:**
- Create: `src/app/services/audit_log.py`
- Create: `src/app/infra/db.py`
- Create: `src/app/infra/repositories/audit_repo.py`
- Test: `tests/integration/test_audit_logging.py`
- Modify: `src/app/api/chat.py`

- [ ] **Step 1: Add failing integration test requiring persisted audit record**

```python
def test_chat_query_persists_audit_record():
    ...
    assert saved.trace_id == resp.json()["trace_id"]
    assert saved.status == "SUCCESS"
```

- [ ] **Step 2: Run audit test and confirm fail**

Run: `pytest tests/integration/test_audit_logging.py -v`
Expected: FAIL

- [ ] **Step 3: Implement audit model + repo + lifecycle hooks in endpoint**

```python
record = AuditRecord(..., stage="VALIDATED")
repo.save(record)
```

- [ ] **Step 4: Re-run audit test**

Run: `pytest tests/integration/test_audit_logging.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/services/audit_log.py src/app/infra/db.py src/app/infra/repositories/audit_repo.py src/app/api/chat.py tests/integration/test_audit_logging.py
git commit -m "feat: add auditable query lifecycle logging"
```

---

### Task 8: End-to-end quality gate and documentation

**Files:**
- Modify: `README.md`
- Modify: `tests/integration/test_chat_query_flow.py`
- Modify: `tests/integration/test_rbac_enforcement.py`
- Modify: `tests/integration/test_audit_logging.py`

- [ ] **Step 1: Add failing tests for explicit error code responses**

```python
def test_unknown_metric_returns_structured_error_code():
    ...
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "UNKNOWN_METRIC"
```

- [ ] **Step 2: Run full test suite and capture failures**

Run: `pytest tests -v`
Expected: FAIL (new error-code tests)

- [ ] **Step 3: Implement minimal structured error mapper and wire into endpoint**

```python
return JSONResponse(status_code=400, content={"error_code": code, "message": msg})
```

- [ ] **Step 4: Re-run full test suite**

Run: `pytest tests -v`
Expected: PASS

- [ ] **Step 5: Update README with runbook**

```markdown
## Run
uvicorn app.main:app --reload

## Test
pytest tests -v
```

- [ ] **Step 6: Commit**

```bash
git add README.md src/app/api/chat.py tests
git commit -m "chore: finalize phase1 quality gates and developer runbook"
```

---

## 2) Verification Matrix (maps to approved spec)

- **Accuracy-first path**: intent parser + query planner + validator + semantic execution (Tasks 2-4)
- **Follow-up continuity**: conversation memory with delta rewrite (Task 6)
- **RBAC hard enforcement**: validator + integration tests (Tasks 3-4)
- **Auditability**: lifecycle persistence and trace IDs (Task 7)
- **Error handling clarity**: structured error codes + tests (Task 8)

---

## 3) Execution commands (quick reference)

- Setup env: `python -m venv .venv && source .venv/bin/activate && pip install fastapi pydantic pytest httpx sqlalchemy uvicorn`
- Run API: `uvicorn app.main:app --reload`
- Run unit tests: `pytest tests/unit -v`
- Run integration tests: `pytest tests/integration -v`
- Run all tests: `pytest tests -v`

---

## 4) Out of scope for this plan

- Proactive anomaly detection scheduler (Phase 2)
- Cross-system execution (CRM/supply chain) (Phase 3)
- Autonomous approval bypass for high-risk actions

---

## 5) Done definition

- All tests in `tests/` pass
- Query endpoint enforces RBAC and returns deterministic chart+answer payload
- Audit record exists for each request with traceability fields
- README enables a new engineer to run and test without extra tribal knowledge
