from fastapi import APIRouter, HTTPException

from app.api.reports import _ensure_default_report_bundle_for_insight_card
from app.infra.repositories.insight_repo import InsightRepository
from app.services.access_policy import resolve_allowed_regions

router = APIRouter(prefix="/v1/insights")


@router.get("/cards")
def list_insight_cards(user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    if not allowed_regions:
        return {"items": []}
    items = InsightRepository().list_by_regions(allowed_regions)
    hydrated_items = []
    for item in items:
        report_bundle, _ = _ensure_default_report_bundle_for_insight_card(
            tenant_id=tenant_id,
            principal_id=user_id,
            card=item,
        )
        hydrated_items.append(
            {
                **item,
                "report_id": report_bundle["report"]["id"],
                "dashboard_id": report_bundle["report"]["dashboard_id"],
                "detail_url": f"/reports/{report_bundle['report']['id']}",
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
            "detail_url": f"/reports/{report['id']}",
        }
        report_summary = {
            "report_id": report["id"],
            "dashboard_id": report["dashboard_id"],
            "headline": report["summary"].get("headline"),
            "snapshot_time": report.get("snapshot_time"),
        }
    except KeyError:
        report_summary = None

    return {"card": card, "report_summary": report_summary}
