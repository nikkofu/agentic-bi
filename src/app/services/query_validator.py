from app.domain.models import ValidationErrorCode


def validate_plan(plan, allowed_regions: list[str]) -> None:
    if not plan.metric:
        raise ValueError(ValidationErrorCode.UNKNOWN_METRIC.value)

    region = plan.filters.get("region")
    if region and region not in allowed_regions:
        raise PermissionError(ValidationErrorCode.PERMISSION_DENIED.value)
