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
