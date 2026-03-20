# Agentic BI

Agentic BI is a decision-intelligence prototype focused on Phase 1 sales-domain copilot capabilities.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi pydantic pytest "httpx<0.28" sqlalchemy uvicorn
PYTHONPATH=src uvicorn app.main:app --reload
```

## Test

```bash
PYTHONPATH=src pytest tests -v
```

## Scope

Current implementation includes:
- Natural-language sales intent parsing
- Query-plan construction and validation
- RBAC-aware plan checks
- Deterministic fixture-backed execution
- Narrative/chart response building
- Conversation follow-up memory
- Audit event logging with trace IDs

## Product docs

- RFP: `docs/RFP.md`
- Design: `docs/superpowers/specs/2026-03-20-phase1-sales-copilot-design.md`
- Plan: `docs/superpowers/plans/2026-03-20-phase1-sales-copilot.md`
