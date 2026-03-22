from fastapi import APIRouter, HTTPException

from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.services.access_policy import resolve_allowed_regions

router = APIRouter(prefix="/v1/insights")


@router.get("/cards")
def list_insight_cards(user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    items = InsightRepository().list_by_regions(allowed_regions)
    return {"items": items}


@router.get("/cards/{card_id}")
def get_insight_card(card_id: str, user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    try:
        card = InsightRepository().get(card_id, allowed_regions)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND"}) from exc

    report_summary = None
    report_id = card.get("report_id")
    if report_id:
        try:
            report = DiagnosticReportRepository().get_for_owner(
                report_id=report_id,
                tenant_id=tenant_id,
                principal_id=user_id,
            )
            report_summary = {
                "report_id": report["id"],
                "dashboard_id": report["dashboard_id"],
                "headline": report["summary"].get("headline"),
                "snapshot_time": report.get("snapshot_time"),
            }
        except KeyError:
            report_summary = None

    return {"card": card, "report_summary": report_summary}
