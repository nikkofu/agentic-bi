from fastapi import APIRouter
from pydantic import BaseModel

from app.services.conversation_memory import apply_followup, get_last_plan, save_last_plan
from app.services.intent_parser import parse_intent
from app.services.query_executor import execute_query
from app.services.query_planner import build_query_plan
from app.services.response_builder import build_response

router = APIRouter(prefix="/v1/chat")


class QueryRequest(BaseModel):
    user_id: str
    tenant_id: str
    question: str
    conversation_id: str


@router.post("/query")
def query(req: QueryRequest):
    previous_plan = get_last_plan(req.conversation_id)
    if previous_plan and ("华东" in req.question or "华南" in req.question):
        plan = apply_followup(req.question, previous_plan)
    else:
        intent = parse_intent(req.question)
        plan = build_query_plan(intent)

    save_last_plan(req.conversation_id, plan)
    result = execute_query(plan, scope={"allowed_regions": ["华东", "华南"]})
    result["has_time_series"] = True
    result["has_rank"] = False
    payload = build_response(result)
    payload["trace_id"] = "stub-trace"
    return payload
