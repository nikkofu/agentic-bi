from fastapi import APIRouter
from pydantic import BaseModel

from app.services.intent_parser import parse_intent
from app.services.query_executor import execute_query
from app.services.query_planner import build_query_plan

router = APIRouter(prefix="/v1/chat")


class QueryRequest(BaseModel):
    user_id: str
    tenant_id: str
    question: str
    conversation_id: str


@router.post("/query")
def query(req: QueryRequest):
    intent = parse_intent(req.question)
    plan = build_query_plan(intent)
    result = execute_query(plan, scope={"allowed_regions": ["华东", "华南"]})
    answer = f"上个月{result['region']}区毛利率为{result['value']:.2%}"
    return {
        "answer": answer,
        "chart": {"type": "table", "data": [result]},
        "trace_id": "stub-trace",
    }
