from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.metrics_catalog import GROUP_DIMENSION_SUGGESTION_MAP, GROUP_DIMENSION_SUGGESTIONS, PRIMARY_METRIC_SUGGESTIONS
from app.domain.models import ValidationErrorCode
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event, new_trace_id
from app.services.conversation_memory import save_last_plan
from app.services.query_plan_resolver import resolve_plan_for_question
from app.services.query_executor import execute_query
from app.services.query_validator import validate_plan
from app.services.response_builder import build_response_with_reporting

router = APIRouter(prefix="/v1/chat")


class QueryRequest(BaseModel):
    user_id: str
    tenant_id: str
    question: str
    conversation_id: str


def _build_result_summary(result: dict) -> dict:
    return {
        "metric": result.get("metric"),
        "region": result.get("region"),
        "time_window": result.get("time_window"),
        "value": result.get("value"),
        "compare_to": result.get("compare_to"),
        "series_points": len(result.get("series", [])),
    }


def _normalize_dashboard_binding_kinds(dashboard_payload: dict) -> dict:
    bindings = dashboard_payload.get("data_bindings", [])
    for binding in bindings:
        if binding.get("kind") == "materialized":
            binding["kind"] = "materialized_result"
    return dashboard_payload


def _looks_like_metric_request(question: str) -> bool:
    return any(
        token in question
        for token in ["指标", "率", "额", "利润", "营收", "收入", "销售额", "毛利"]
    )


def _build_unknown_metric_suggestions(question: str) -> list[str]:
    if any(token in question for token in ["利润率", "盈利率"]):
        return ["毛利率", "毛利额"]
    if any(token in question for token in ["利润", "盈利", "毛利"]):
        return ["毛利额", "毛利率"]
    if any(token in question for token in ["营收", "收入", "销售"]):
        return ["销售额"]
    return PRIMARY_METRIC_SUGGESTIONS


def _build_unknown_metric_message(suggestions: list[str]) -> str:
    if suggestions == PRIMARY_METRIC_SUGGESTIONS:
        return "未识别指标，请改问毛利率、销售额或毛利额"
    if len(suggestions) == 1:
        return f"未识别指标，可能想问{suggestions[0]}"
    if len(suggestions) == 2:
        return f"未识别指标，可能想问{suggestions[0]}或{suggestions[1]}"
    return "未识别指标，请改问毛利率、销售额或毛利额"


def _build_invalid_dimension_suggestions(plan) -> list[str]:
    group_by = getattr(plan, "group_by", [])
    suggestions = [
        GROUP_DIMENSION_SUGGESTION_MAP[dimension]
        for dimension in group_by
        if dimension in GROUP_DIMENSION_SUGGESTION_MAP
    ]
    return suggestions or GROUP_DIMENSION_SUGGESTIONS


def _build_validation_error_content(error_code: str, trace_id: str, plan=None, question: str = "") -> dict:
    if error_code == ValidationErrorCode.UNKNOWN_METRIC.value:
        suggestions = _build_unknown_metric_suggestions(question)
        return {
            "error_code": error_code,
            "message": _build_unknown_metric_message(suggestions),
            "suggestions": suggestions,
            "trace_id": trace_id,
        }

    if error_code == ValidationErrorCode.INVALID_DIMENSION_COMBO.value:
        return {
            "error_code": error_code,
            "message": "暂不支持同时按多个维度查看，请只保留一个分组维度",
            "suggestions": _build_invalid_dimension_suggestions(plan),
            "trace_id": trace_id,
        }

    return {"error_code": error_code, "message": "invalid metric", "trace_id": trace_id}


@router.post("/query")
def query(req: QueryRequest):
    trace_id = new_trace_id()
    allowed_regions = resolve_allowed_regions(req.user_id, req.tenant_id)
    plan = resolve_plan_for_question(
        tenant_id=req.tenant_id,
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        question=req.question,
    )

    if not plan.metric and not _looks_like_metric_request(req.question):
        save_last_plan(req.tenant_id, req.user_id, req.conversation_id, plan)
        append_audit_event(
            {
                "trace_id": trace_id,
                "status": ValidationErrorCode.MISSING_METRIC.value,
                "error_code": ValidationErrorCode.MISSING_METRIC.value,
                "question": req.question,
                "conversation_id": req.conversation_id,
                "query_plan": plan.model_dump(),
            }
        )
        return JSONResponse(
            status_code=422,
            content={
                "error_code": ValidationErrorCode.MISSING_METRIC.value,
                "message": "请补充要查询的指标",
                "suggestions": PRIMARY_METRIC_SUGGESTIONS,
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
                "error_code": str(exc),
                "question": req.question,
                "conversation_id": req.conversation_id,
                "query_plan": plan.model_dump(),
            }
        )
        return JSONResponse(
            status_code=400,
            content=_build_validation_error_content(str(exc), trace_id, plan=plan, question=req.question),
        )
    except PermissionError as exc:
        append_audit_event(
            {
                "trace_id": trace_id,
                "status": str(exc),
                "error_code": str(exc),
                "question": req.question,
                "conversation_id": req.conversation_id,
                "query_plan": plan.model_dump(),
            }
        )
        return JSONResponse(
            status_code=403,
            content={"error_code": str(exc), "message": "permission denied", "trace_id": trace_id},
        )

    save_last_plan(req.tenant_id, req.user_id, req.conversation_id, plan)
    result = execute_query(plan, scope={"allowed_regions": allowed_regions})
    result["has_time_series"] = bool(result.get("series"))
    result["has_rank"] = False
    reporting_payload = build_response_with_reporting(
        question=req.question,
        tenant_id=req.tenant_id,
        dataset_id="sales-fixture",
        trace_id=trace_id,
        permission_context={
            "principal_id": req.user_id,
            "role_scope": [f"region:{region}" for region in allowed_regions],
            "row_level_policy_ref": f"sales-region:{req.user_id}",
        },
        plan=plan,
        result=result,
    )
    payload = {
        "answer": reporting_payload["answer"],
        "chart": reporting_payload["chart"],
        "report_preview": {
            "intent": reporting_payload["report_intent"],
            "dashboard": _normalize_dashboard_binding_kinds(reporting_payload["dashboard_spec"]),
        },
        "trace_id": trace_id,
    }

    append_audit_event(
        {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "question": req.question,
            "conversation_id": req.conversation_id,
            "query_plan": plan.model_dump(),
            "response_type": payload["chart"]["type"],
            "result_summary": _build_result_summary(result),
        }
    )
    return payload
