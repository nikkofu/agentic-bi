from fastapi import APIRouter

from app.infra.repositories.insight_repo import InsightRepository
from app.services.access_policy import resolve_allowed_regions

router = APIRouter(prefix="/v1/insights")


@router.get("/cards")
def list_insight_cards(user_id: str, tenant_id: str):
    allowed_regions = resolve_allowed_regions(user_id=user_id, tenant_id=tenant_id)
    items = InsightRepository().list_by_regions(allowed_regions)
    return {"items": items}
