from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException

from app.api.reporting import build_permission_context
from app.api.reports import DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED
from app.api.reports import _ensure_default_report_bundle_for_insight_card
from app.infra.repositories.insight_repo import InsightRepository
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event
from app.services.audit_log import new_trace_id

router = APIRouter(prefix="/v1/insights")


def _safe_permission_context(*, tenant_id: str, user_id: str) -> dict:
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    return build_permission_context(
        principal_id=user_id,
        role_scope=[f"region:{region}" for region in allowed_regions],
        row_level_policy_ref=f"sales-region:{user_id}",
    )


def _lazy_report_failure_error_code(exc: Exception) -> str:
    if isinstance(exc, (ValueError, PermissionError)):
        return str(exc)
    return DIAGNOSTIC_REPORT_SNAPSHOT_PERSIST_FAILED


def _append_lazy_report_failure_audit_event(*, tenant_id: str, user_id: str, card: dict, exc: Exception) -> None:
    permission_context = _safe_permission_context(tenant_id=tenant_id, user_id=user_id)
    append_audit_event(
        {
            "trace_id": new_trace_id(),
            "status": "DIAGNOSTIC_REPORT_GENERATE_FAILED",
            "question": card.get("suggested_next_question", f"insight-card:{card.get('card_id', 'unknown')}"),
            "conversation_id": "",
            "error_code": _lazy_report_failure_error_code(exc),
            "result_summary": {
                "card_id": card.get("card_id"),
                "entry_mode": "insight_card_lazy",
                "permission_context": {
                    "principal_id": permission_context["principal_id"],
                    "role_scope": permission_context["role_scope"],
                    "row_level_policy_ref": permission_context["row_level_policy_ref"],
                },
            },
        }
    )


def _build_lazy_failure_card(card: dict, exc: Exception) -> dict:
    return {
        **card,
        "report_id": None,
        "dashboard_id": None,
        "detail_url": None,
        "report_status": "unavailable",
        "report_error_code": _lazy_report_failure_error_code(exc),
    }


def _build_contextual_detail_url(*, report_id: str, tenant_id: str, user_id: str) -> str:
    params = urlencode(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "principal_id": user_id,
        }
    )
    return f"/reports/{report_id}?{params}"


@router.get("/cards")
def list_insight_cards(user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    if not allowed_regions:
        return {"items": []}
    items = InsightRepository().list_by_regions(allowed_regions)
    hydrated_items = []
    for item in items:
        try:
            report_bundle, _ = _ensure_default_report_bundle_for_insight_card(
                tenant_id=tenant_id,
                principal_id=user_id,
                card=item,
            )
        except Exception as exc:
            _append_lazy_report_failure_audit_event(
                tenant_id=tenant_id,
                user_id=user_id,
                card=item,
                exc=exc,
            )
            hydrated_items.append(_build_lazy_failure_card(item, exc))
            continue

        hydrated_items.append(
            {
                **item,
                "report_id": report_bundle["report"]["id"],
                "dashboard_id": report_bundle["report"]["dashboard_id"],
                "detail_url": _build_contextual_detail_url(
                    report_id=report_bundle["report"]["id"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                ),
                "report_status": "ready",
                "report_error_code": None,
            }
        )
    return {"items": hydrated_items}


@router.get("/cards/{card_id}")
def get_insight_card(card_id: str, user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    if not allowed_regions:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND"})
    try:
        card = InsightRepository().get(card_id, allowed_regions)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND"}) from exc

    report_summary = None
    try:
        report_bundle, _ = _ensure_default_report_bundle_for_insight_card(
            tenant_id=tenant_id,
            principal_id=user_id,
            card=card,
        )
        report = report_bundle["report"]
        card = {
            **card,
            "report_id": report["id"],
            "dashboard_id": report["dashboard_id"],
            "detail_url": _build_contextual_detail_url(
                report_id=report["id"],
                tenant_id=tenant_id,
                user_id=user_id,
            ),
            "report_status": "ready",
            "report_error_code": None,
        }
        report_summary = {
            "report_id": report["id"],
            "dashboard_id": report["dashboard_id"],
            "headline": report["summary"].get("headline"),
            "snapshot_time": report.get("snapshot_time"),
        }
    except Exception as exc:
        _append_lazy_report_failure_audit_event(
            tenant_id=tenant_id,
            user_id=user_id,
            card=card,
            exc=exc,
        )
        card = _build_lazy_failure_card(card, exc)
        report_summary = None

    return {"card": card, "report_summary": report_summary}
