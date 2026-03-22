from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.reporting import PERMISSION_DENIED
from app.api.reporting import build_permission_context
from app.api.reporting import _resolve_identity_context
from app.domain.models import QueryPlan
from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.infra.repositories.report_intent_repo import ReportIntentRepository
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event, new_trace_id
from app.services.diagnostic_dashboard_assembler import assemble_diagnostic_dashboard
from app.services.diagnostic_report_builder import build_diagnostic_report
from app.services.insight_attribution import compute_single_layer_attribution
from app.services.query_executor import execute_query
from app.services.report_intent_builder import build_report_intent

router = APIRouter(prefix="/v1")


class ReportGenerateRequest(BaseModel):
    tenant_id: str
    user_id: str
    principal_id: str | None = None
    mode: Literal["from_insight", "direct"]
    insight_card_id: str | None = None
    metric: str | None = None
    scope: dict[str, str] | None = None
    time_window: str | None = None


def _safe_permission_context(*, tenant_id: str, user_id: str) -> dict:
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    return build_permission_context(
        principal_id=user_id,
        role_scope=[f"region:{region}" for region in allowed_regions],
        row_level_policy_ref=f"sales-region:{user_id}",
    )


def _append_report_audit_event(
    *,
    trace_id: str,
    status: str,
    permission_context: dict,
    question: str,
    error_code: str | None = None,
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
            "conversation_id": "",
            "error_code": error_code,
            "result_summary": summary,
        }
    )


def _load_report_bundle(*, report_id: str, tenant_id: str, principal_id: str) -> dict:
    reports = DiagnosticReportRepository()
    dashboards = DashboardRepository()
    stored_report = reports.get_for_owner(report_id=report_id, tenant_id=tenant_id, principal_id=principal_id)
    stored_dashboard = dashboards.get_for_owner(
        dashboard_id=stored_report["dashboard_id"],
        tenant_id=tenant_id,
        principal_id=principal_id,
    )
    return {"report": stored_report, "dashboard": stored_dashboard["dashboard"]}


def _ensure_default_report_bundle_for_insight_card(
    *,
    tenant_id: str,
    principal_id: str,
    card: dict,
) -> tuple[dict, bool]:
    report_repo = DiagnosticReportRepository()
    report_id = card.get("report_id")
    if report_id:
        try:
            return (
                _load_report_bundle(
                    report_id=report_id,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                ),
                True,
            )
        except KeyError:
            pass

    existing_report = report_repo.get_by_source_ref(
        tenant_id=tenant_id,
        principal_id=principal_id,
        source_kind="insight_card",
        source_ref=card["card_id"],
    )
    if existing_report is not None:
        return (
            _load_report_bundle(
                report_id=existing_report["id"],
                tenant_id=tenant_id,
                principal_id=principal_id,
            ),
            True,
        )

    created_or_existing = report_repo.get_or_create_default_for_insight(
        tenant_id=tenant_id,
        principal_id=principal_id,
        source_ref=card["card_id"],
        create_fn=lambda: _persist_snapshot(
            tenant_id=tenant_id,
            principal_id=principal_id,
            question=card.get("suggested_next_question") or card.get("summary", "diagnostic-report"),
            metric=card["metric"],
            scope=card["scope"],
            time_window="current",
            source_kind="insight_card",
            source_ref=card["card_id"],
        )["report"],
    )
    return (
        _load_report_bundle(
            report_id=created_or_existing["id"],
            tenant_id=tenant_id,
            principal_id=principal_id,
        ),
        False,
    )


def _persist_snapshot(
    *,
    tenant_id: str,
    principal_id: str,
    question: str,
    metric: str,
    scope: dict[str, str],
    time_window: str,
    source_kind: str,
    source_ref: str,
    findings: list[dict] | None = None,
    recommendations: list[dict] | None = None,
) -> dict:
    trace_id = new_trace_id()
    allowed_regions = resolve_allowed_regions(user_id=principal_id, tenant_id=tenant_id)
    permission_context = build_permission_context(
        principal_id=principal_id,
        role_scope=[f"region:{region}" for region in allowed_regions],
        row_level_policy_ref=f"sales-region:{principal_id}",
    )
    intent = build_report_intent(
        question=question,
        tenant_id=tenant_id,
        dataset_id="sales-fixture",
        trace_id=trace_id,
        permission_context=permission_context,
        plan={"metric": metric, "filters": scope, "time_window": time_window, "group_by": ["month"]},
        result={"metric": metric, "time_window": time_window},
    )
    ReportIntentRepository().save(intent)
    dashboard_id = f"dash-{trace_id}"
    report = build_diagnostic_report(
        tenant_id=tenant_id,
        principal_id=principal_id,
        source_kind=source_kind,
        source_ref=source_ref,
        report_intent=intent,
        metric_result={"metric": metric, "time_window": time_window},
        finding_inputs=findings or [],
        recommendations=recommendations or [],
        dashboard_id=dashboard_id,
    )
    overview_result = execute_query(
        QueryPlan(
            metric=metric,
            filters=scope,
            time_window=time_window,
            group_by=["month"],
            compare_to="",
            group_requested=True,
        ),
        scope={"allowed_regions": allowed_regions},
    )
    driver_attribution = compute_single_layer_attribution(
        [{"region": scope.get("region", "全域"), "value": overview_result.get("value", 0.0) or 0.0}],
        dimension=next(iter(scope.keys()), "region"),
    )
    dashboard = assemble_diagnostic_dashboard(
        report=report,
        result_bindings={
            "overview": {
                "value": overview_result.get("value"),
                "rows": overview_result.get("series", [])
                or overview_result.get("breakdown", [])
                or [overview_result],
            },
            "drivers": {"rows": [driver_attribution]},
        },
    )
    DashboardRepository().save(
        tenant_id=tenant_id,
        principal_id=principal_id,
        report_intent_id=intent.id,
        dashboard=dashboard.model_dump(mode="python"),
        dashboard_id=dashboard.id,
    )
    saved_report = DiagnosticReportRepository().save(report=report.model_dump(mode="python"))
    _append_report_audit_event(
        trace_id=trace_id,
        status="DIAGNOSTIC_REPORT_GENERATED",
        permission_context=permission_context,
        question=question,
        result_summary={
            "report_id": saved_report["id"],
            "dashboard_id": saved_report["dashboard_id"],
            "entry_mode": source_kind,
        },
    )
    return _load_report_bundle(
        report_id=saved_report["id"],
        tenant_id=tenant_id,
        principal_id=principal_id,
    )


@router.get("/reports/{report_id}")
def get_report(report_id: str, tenant_id: str, user_id: str, principal_id: str | None = None):
    trace_id = new_trace_id()
    try:
        canonical_principal, _, permission_context = _resolve_identity_context(
            tenant_id=tenant_id,
            user_id=user_id,
            principal_id=principal_id,
        )
    except ValueError as exc:
        permission_context = _safe_permission_context(tenant_id=tenant_id, user_id=user_id)
        _append_report_audit_event(
            trace_id=trace_id,
            status="DIAGNOSTIC_REPORT_FETCH_DENIED",
            permission_context=permission_context,
            question=f"diagnostic-report:{report_id}",
            error_code=str(exc),
        )
        raise HTTPException(status_code=400, detail={"error_code": str(exc)}) from exc

    try:
        payload = _load_report_bundle(
            report_id=report_id,
            tenant_id=tenant_id,
            principal_id=canonical_principal,
        )
    except KeyError as exc:
        _append_report_audit_event(
            trace_id=trace_id,
            status="DIAGNOSTIC_REPORT_FETCH_DENIED",
            permission_context=permission_context,
            question=f"diagnostic-report:{report_id}",
            error_code=PERMISSION_DENIED,
        )
        raise HTTPException(status_code=403, detail={"error_code": PERMISSION_DENIED}) from exc

    _append_report_audit_event(
        trace_id=trace_id,
        status="DIAGNOSTIC_REPORT_FETCHED",
        permission_context=permission_context,
        question=payload["report"].get("summary", {}).get("title", f"diagnostic-report:{report_id}"),
        result_summary={"report_id": report_id, "dashboard_id": payload["report"]["dashboard_id"]},
    )
    return payload


@router.post("/reports:generate")
def generate_report(req: ReportGenerateRequest):
    trace_id = new_trace_id()
    try:
        canonical_principal, allowed_regions, permission_context = _resolve_identity_context(
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            principal_id=req.principal_id,
        )
        if req.mode == "from_insight":
            if not req.insight_card_id:
                raise ValueError("MISSING_INSIGHT_CARD")
            card = InsightRepository().get(req.insight_card_id, allowed_regions)
            payload, reused_existing = _ensure_default_report_bundle_for_insight_card(
                tenant_id=req.tenant_id,
                principal_id=canonical_principal,
                card=card,
            )
            if reused_existing:
                _append_report_audit_event(
                    trace_id=trace_id,
                    status="DIAGNOSTIC_REPORT_GENERATED",
                    permission_context=permission_context,
                    question=card.get("summary", "diagnostic-report"),
                    result_summary={
                        "report_id": payload["report"]["id"],
                        "dashboard_id": payload["report"]["dashboard_id"],
                        "entry_mode": "insight_card_cached",
                    },
                )
            return payload

        if req.mode == "direct":
            if not req.metric or not req.scope or not req.time_window:
                raise ValueError("MISSING_DIRECT_REQUEST")
            source_ref = f"direct:{canonical_principal}:{req.metric}:{req.time_window}"
            question = f"{req.metric} {req.time_window} 诊断"
            return _persist_snapshot(
                tenant_id=req.tenant_id,
                principal_id=canonical_principal,
                question=question,
                metric=req.metric,
                scope=req.scope,
                time_window=req.time_window,
                source_kind="on_demand",
                source_ref=source_ref,
            )

        raise ValueError("UNSUPPORTED_MODE")
    except ValueError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_report_audit_event(
            trace_id=trace_id,
            status="DIAGNOSTIC_REPORT_GENERATE_FAILED",
            permission_context=permission_context,
            question="diagnostic-report:generate",
            error_code=str(exc),
        )
        raise HTTPException(status_code=400, detail={"error_code": str(exc)}) from exc
    except KeyError as exc:
        permission_context = _safe_permission_context(tenant_id=req.tenant_id, user_id=req.user_id)
        _append_report_audit_event(
            trace_id=trace_id,
            status="DIAGNOSTIC_REPORT_GENERATE_FAILED",
            permission_context=permission_context,
            question="diagnostic-report:generate",
            error_code=PERMISSION_DENIED,
        )
        raise HTTPException(status_code=403, detail={"error_code": PERMISSION_DENIED}) from exc
