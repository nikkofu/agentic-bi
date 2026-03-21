from app.domain.metrics_catalog import SUPPORTED_DIMENSIONS
from app.domain.models import ValidationErrorCode


def validate_plan(plan, allowed_regions: list[str]) -> None:
    if not plan.metric:
        raise ValueError(ValidationErrorCode.UNKNOWN_METRIC.value)

    group_by = getattr(plan, "group_by", [])
    if len(group_by) > 1:
        raise ValueError(ValidationErrorCode.INVALID_DIMENSION_COMBO.value)

    if any(dimension not in SUPPORTED_DIMENSIONS for dimension in group_by):
        raise ValueError(ValidationErrorCode.INVALID_DIMENSION_COMBO.value)

    if not allowed_regions:
        raise PermissionError(ValidationErrorCode.PERMISSION_DENIED.value)

    region = plan.filters.get("region")
    if region and region not in allowed_regions:
        raise PermissionError(ValidationErrorCode.PERMISSION_DENIED.value)
