from enum import Enum

from pydantic import BaseModel


class QueryResponse(BaseModel):
    answer: str
    chart: dict
    trace_id: str


class QueryPlan(BaseModel):
    metric: str
    filters: dict[str, str]
    time_window: str
    group_by: list[str]
    compare_to: str


class ValidationErrorCode(str, Enum):
    MISSING_METRIC = "MISSING_METRIC"
    UNKNOWN_METRIC = "UNKNOWN_METRIC"
    INVALID_DIMENSION_COMBO = "INVALID_DIMENSION_COMBO"
    PERMISSION_DENIED = "PERMISSION_DENIED"
