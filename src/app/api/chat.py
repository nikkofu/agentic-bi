from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.metrics_catalog import METRIC_ALIASES
from app.domain.models import ValidationErrorCode
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event, new_trace_id
from app.services.conversation_memory import apply_followup, get_last_plan, save_last_plan
from app.services.intent_parser import parse_intent
from app.services.query_executor import execute_query
from app.services.query_planner import build_query_plan
from app.services.query_validator import validate_plan
from app.services.response_builder import build_response

router = APIRouter(prefix="/v1/chat")


class QueryRequest(BaseModel):
    user_id: str
    tenant_id: str
    question: str
    conversation_id: str


def _is_followup_question(question: str, has_previous_plan: bool) -> bool:
    if not has_previous_plan:
        return False

    has_metric_alias = any(alias in question for alias in METRIC_ALIASES)
    has_explicit_scope_or_time = any(
        token in question for token in ["华东", "华南", "上个月", "近3个月"]
    )
    if has_metric_alias and not has_explicit_scope_or_time:
        return True
    if has_metric_alias:
        return False

    return any(token in question for token in ["华东", "华南", "那", "按月", "环比", "同比"])


@router.post("/query")
def query(req: QueryRequest):
    trace_id = new_trace_id()
    previous_plan = get_last_plan(req.conversation_id)
    allowed_regions = resolve_allowed_regions(req.user_id, req.tenant_id)

    if _is_followup_question(req.question, previous_plan is not None):
        plan = apply_followup(req.question, previous_plan)
    else:
        intent = parse_intent(req.question)
        plan = build_query_plan(intent)

    if not plan.metric and "指标" not in req.question:
        append_audit_event(
            {
                "trace_id": trace_id,
                "status": ValidationErrorCode.MISSING_METRIC.value,
                "question": req.question,
                "conversation_id": req.conversation_id,
            }
        )
        return JSONResponse(
            status_code=422,
            content={
                "error_code": ValidationErrorCode.MISSING_METRIC.value,
                "message": "请补充要查询的指标",
                "suggestions": list(METRIC_ALIASES.keys()),
                "trace_id": trace_id,
            },
        )

    try:
        validate_plan(plan, allowed_regions=allowed_regions)
    except ValueError as exc:
        append_audit_event(
            {
                "trace_id": trace_id,
                "status": str(exc),
                "question": req.question,
                "conversation_id": req.conversation_id,
            }
        )
        return JSONResponse(
            status_code=400,
            content={"error_code": str(exc), "message": "invalid metric", "trace_id": trace_id},
        )
    except PermissionError as exc:
        append_audit_event(
            {
                "trace_id": trace_id,
                "status": str(exc),
                "question": req.question,
                "conversation_id": req.conversation_id,
            }
        )
        return JSONResponse(
            status_code=403,
            content={"error_code": str(exc), "message": "permission denied", "trace_id": trace_id},
        )

    save_last_plan(req.conversation_id, plan)
    result = execute_query(plan, scope={"allowed_regions": allowed_regions})
    result["has_time_series"] = bool(result.get("series"))
    result["has_rank"] = False
    payload = build_response(result)
    payload["trace_id"] = trace_id

    append_audit_event(
        {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "question": req.question,
            "conversation_id": req.conversation_id,
        }
    )
    return payload
