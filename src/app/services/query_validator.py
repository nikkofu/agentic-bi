from app.domain.models import ValidationErrorCode


def validate_plan(plan, allowed_regions: list[str]) -> None:
    region = plan.filters.get("region")
    if region and region not in allowed_regions:
        error = PermissionError(ValidationErrorCode.PERMISSION_DENIED.value)
        raise error
