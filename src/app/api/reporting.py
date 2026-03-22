from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from app.domain.models import QueryPlan
from app.domain.reporting_models import DashboardPage
from app.domain.reporting_models import DashboardSection
from app.domain.reporting_models import DashboardSpec
from app.domain.reporting_models import DashboardWidget
from app.domain.reporting_models import ReportIntent
from app.domain.reporting_models import WidgetBinding
from app.domain.reporting_models import WidgetPresentation
from app.infra.repositories.report_intent_repo import ReportIntentRepository
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event, new_trace_id
from app.services.conversation_memory import save_last_plan
from app.services.dashboard_assembler import assemble_dashboard
from app.services.query_executor import execute_query
from app.services.query_plan_resolver import resolve_plan_for_question
from app.services.query_validator import validate_plan
from app.services.report_intent_builder import build_report_intent

router = APIRouter(prefix="/v1")
PRINCIPAL_MISMATCH = "PRINCIPAL_MISMATCH"


class ReportingGenerateRequest(BaseModel):
    tenant_id: str
    user_id: str
    principal_id: str | None = None
    conversation_id: str
    question: str


class ReportingAssembleRequest(BaseModel):
    tenant_id: str
    user_id: str
    principal_id: str | None = None
    intent: ReportIntent


def build_permission_context(*, principal_id: str, role_scope: list[str], row_level_policy_ref: str) -> dict:
    return {
        "principal_id": principal_id,
        "role_scope": role_scope,
        "row_level_policy_ref": row_level_policy_ref,
    }


def _canonical_principal(*, user_id: str, principal_id: str | None) -> str:
    if principal_id is not None and principal_id != user_id:
        raise ValueError(PRINCIPAL_MISMATCH)
    return user_id


def _resolve_identity_context(*, tenant_id: str, user_id: str, principal_id: str | None) -> tuple[str, list[str], dict]:
    canonical_principal = _canonical_principal(user_id=user_id, principal_id=principal_id)
    allowed_regions = resolve_allowed_regions(user_id, tenant_id)
    permission_context = build_permission_context(
        principal_id=canonical_principal,
        role_scope=[f"region:{region}" for region in allowed_regions],
        row_level_policy_ref=f"sales-region:{canonical_principal}",
    )
    return canonical_principal, allowed_regions, permission_context


def _safe_permission_context(*, tenant_id: str, user_id: str) -> dict:
    allowed_regions = resolve_allowed_regions(user_id, tenant_id)
    return build_permission_context(
        principal_id=user_id,
        role_scope=[f"region:{region}" for region in allowed_regions],
        row_level_policy_ref=f"sales-region:{user_id}",
    )


def _append_reporting_audit_event(
    *,
    trace_id: str,
    status: str,
    question: str,
    conversation_id: str,
    permission_context: dict,
    error_code: str | None = None,
    query_plan: dict | None = None,
    response_type: str | None = None,
    result_summary: dict | None = None,
) -> None:
    summary = dict(result_summary or {})
    summary["permission_context"] = {
        "principal_id": permission_context["principal_id"],
        "role_scope": permission_context["role_scope"],
        "row_level_policy_ref": permission_context["row_level_policy_ref"],
    }
    append_audit_event(
        {
            "trace_id": trace_id,
            "status": status,
            "question": question,
            "conversation_id": conversation_id,
            "query_plan": query_plan,
            "response_type": response_type,
            "error_code": error_code,
            "result_summary": summary,
        }
    )


def execute_reporting_preview(req: ReportingGenerateRequest, *, allowed_regions: list[str]) -> tuple[QueryPlan, dict]:
    plan = resolve_plan_for_question(
        tenant_id=req.tenant_id,
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        question=req.question,
    )
    validate_plan(plan, allowed_regions=allowed_regions)
    save_last_plan(req.tenant_id, req.user_id, req.conversation_id, plan)
    result = execute_query(plan, scope={"allowed_regions": allowed_regions})
    return plan, result


def _build_query_plan_from_semantic_query(query) -> QueryPlan:
    filters = {}
    for query_filter in query.filters:
        if query_filter.get("op") != "=":
            continue
        field = query_filter.get("field")
        value = query_filter.get("value")
        if isinstance(field, str) and isinstance(value, str):
            filters[field] = value

    return QueryPlan(
        metric=query.measures[0] if query.measures else "",
        filters=filters,
        time_window=query.time.get("window", "current"),
        group_by=query.dimensions,
        compare_to=query.comparison.get("mode", "") if query.comparison else "",
        group_requested=bool(query.dimensions),
    )


def execute_semantic_queries_from_intent(intent: ReportIntent, *, allowed_regions: list[str]) -> list[dict]:
    executed_queries: list[dict] = []
    for query in intent.semantic_queries:
        plan = _build_query_plan_from_semantic_query(query)
        validate_plan(plan, allowed_regions=allowed_regions)
        result = execute_query(plan, scope={"allowed_regions": allowed_regions})
        executed_queries.append({"query_id": query.id, "query": query, "result": result})
    return executed_queries


def _chart_rows(result: dict) -> list[dict]:
    series = result.get("series", [])
    if series:
        return [dict(row) for row in series]

    breakdown = result.get("breakdown", [])
    if breakdown:
        return [dict(row) for row in breakdown]

    return [dict(result)]


def _build_multi_query_dashboard(*, intent: ReportIntent, executed_queries: list[dict]) -> DashboardSpec:
    trace_id = intent.trace.get("trace_id", "unknown")
    data_bindings = []
    sections = []
    for index, executed in enumerate(executed_queries, start=1):
        query = executed["query"]
        result = executed["result"]
        source_ref = executed["query_id"]
        metric = query.measures[0] if query.measures else ""

        data_bindings.append(
            {
                "id": f"binding-{trace_id}-{source_ref}",
                "source_ref": source_ref,
                "kind": "materialized_result",
                "value": result.get("value"),
                "rows": _chart_rows(result),
                "insight": "auto",
            }
        )
        sections.append(
            DashboardSection(
                id=f"section-overview-{trace_id}-{source_ref}",
                title=f"Query {index}",
                layout={"columns": 12},
                widgets=[
                    DashboardWidget(
                        id=f"widget-metric-{trace_id}-{source_ref}",
                        kind="metric_card",
                        title="核心指标",
                        presentation=WidgetPresentation(family="kpi", variant="primary"),
                        binding=WidgetBinding(source_ref=source_ref, value_path="value"),
                    ),
                    DashboardWidget(
                        id=f"widget-chart-{trace_id}-{source_ref}",
                        kind="chart",
                        title="趋势/分布",
                        presentation=WidgetPresentation(
                            family="table_like",
                            variant="auto",
                            config={"metric": metric},
                        ),
                        binding=WidgetBinding(source_ref=source_ref, value_path="rows"),
                    ),
                    DashboardWidget(
                        id=f"widget-insight-{trace_id}-{source_ref}",
                        kind="insight",
                        title="解读",
                        presentation=WidgetPresentation(family="narrative", variant="auto"),
                        binding=WidgetBinding(source_ref=source_ref, value_path="insight"),
                    ),
                ],
            )
        )

    return DashboardSpec(
        id=f"dash-preview-{trace_id}",
        version="1.0",
        title=intent.question,
        description="Auto-generated dashboard preview",
        theme={"name": "paper"},
        refresh_policy={"mode": "manual"},
        variables=[],
        data_bindings=data_bindings,
        interactions=[],
        pages=[
            DashboardPage(
                id=f"page-overview-{trace_id}",
                title="Overview",
                layout={"columns": 12},
                sections=sections,
            )
        ],
    )


def _normalize_dashboard_binding_kinds(dashboard_payload: dict) -> dict:
    bindings = dashboard_payload.get("data_bindings", [])
    for binding in bindings:
        if binding.get("kind") == "materialized":
            binding["kind"] = "materialized_result"
    return dashboard_payload


@router.post("/report-intents:generate")
def generate_report_intent(req: ReportingGenerateRequest):
    trace_id = new_trace_id()
    try:
        _, allowed_regions, permission_context = _resolve_identity_context(
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            principal_id=req.principal_id,
        )
        plan, result = execute_reporting_preview(req, allowed_regions=allowed_regions)
    except ValueError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="REPORT_INTENT_GENERATE_FAILED",
            question=req.question,
            conversation_id=req.conversation_id,
            permission_context=permission_context,
            error_code=str(exc),
        )
        raise HTTPException(status_code=400, detail={"error_code": str(exc)}) from exc
    except PermissionError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="REPORT_INTENT_GENERATE_FAILED",
            question=req.question,
            conversation_id=req.conversation_id,
            permission_context=permission_context,
            error_code=str(exc),
        )
        raise HTTPException(status_code=403, detail={"error_code": str(exc)}) from exc

    intent = build_report_intent(
        question=req.question,
        tenant_id=req.tenant_id,
        dataset_id="sales-fixture",
        trace_id=trace_id,
        permission_context=permission_context,
        plan=plan.model_dump(),
        result=result,
    )
    ReportIntentRepository().save(intent)
    _append_reporting_audit_event(
        trace_id=trace_id,
        status="REPORT_INTENT_GENERATED",
        question=req.question,
        conversation_id=req.conversation_id,
        permission_context=permission_context,
        query_plan=plan.model_dump(),
        result_summary={"report_intent_id": intent.id},
    )
    return intent


@router.get("/report-intents/{intent_id}")
def get_report_intent(intent_id: str, tenant_id: str, user_id: str, principal_id: str | None = None):
    trace_id = new_trace_id()
    try:
        canonical_principal, _, permission_context = _resolve_identity_context(
            tenant_id=tenant_id,
            user_id=user_id,
            principal_id=principal_id,
        )
    except ValueError as exc:
        permission_context = _safe_permission_context(tenant_id=tenant_id, user_id=user_id)
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="REPORT_INTENT_FETCH_DENIED",
            question=f"report-intent:{intent_id}",
            conversation_id="",
            permission_context=permission_context,
            error_code=str(exc),
        )
        raise HTTPException(status_code=400, detail={"error_code": str(exc)}) from exc

    try:
        intent = ReportIntentRepository().get_for_owner(
            intent_id=intent_id,
            tenant_id=tenant_id,
            principal_id=canonical_principal,
        )
    except KeyError as exc:
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="REPORT_INTENT_FETCH_DENIED",
            question=f"report-intent:{intent_id}",
            conversation_id="",
            permission_context=permission_context,
            error_code="PERMISSION_DENIED",
        )
        raise HTTPException(status_code=403, detail={"error_code": "PERMISSION_DENIED"}) from exc

    _append_reporting_audit_event(
        trace_id=trace_id,
        status="REPORT_INTENT_FETCHED",
        question=intent.get("question", f"report-intent:{intent_id}"),
        conversation_id="",
        permission_context=permission_context,
        result_summary={"report_intent_id": intent_id},
    )
    return intent


@router.post("/dashboards:assemble")
def assemble_dashboard_preview(req: ReportingAssembleRequest):
    trace_id = new_trace_id()
    try:
        _, allowed_regions, permission_context = _resolve_identity_context(
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            principal_id=req.principal_id,
        )
        executed_queries = execute_semantic_queries_from_intent(
            req.intent,
            allowed_regions=allowed_regions,
        )
    except ValueError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="DASHBOARD_PREVIEW_ASSEMBLE_FAILED",
            question=req.intent.question,
            conversation_id=req.intent.trace.get("trace_id", ""),
            permission_context=permission_context,
            error_code=str(exc),
        )
        raise HTTPException(status_code=400, detail={"error_code": str(exc)}) from exc
    except PermissionError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_reporting_audit_event(
            trace_id=trace_id,
            status="DASHBOARD_PREVIEW_ASSEMBLE_FAILED",
            question=req.intent.question,
            conversation_id=req.intent.trace.get("trace_id", ""),
            permission_context=permission_context,
            error_code=str(exc),
        )
        raise HTTPException(status_code=403, detail={"error_code": str(exc)}) from exc

    if len(executed_queries) == 1:
        dashboard = assemble_dashboard(intent=req.intent, result=executed_queries[0]["result"])
    else:
        dashboard = _build_multi_query_dashboard(intent=req.intent, executed_queries=executed_queries)
    dashboard_payload = _normalize_dashboard_binding_kinds(dashboard.model_dump(mode="python"))
    _append_reporting_audit_event(
        trace_id=trace_id,
        status="DASHBOARD_PREVIEW_ASSEMBLED",
        question=req.intent.question,
        conversation_id=req.intent.trace.get("trace_id", ""),
        permission_context=permission_context,
        query_plan={
            "query_ids": [query["query_id"] for query in executed_queries],
            "query_count": len(executed_queries),
        },
        response_type="dashboard_preview",
        result_summary={
            "dashboard_id": dashboard_payload.get("id"),
            "query_count": len(executed_queries),
        },
    )
    return {"dashboard": dashboard_payload}
