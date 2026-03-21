from collections.abc import Mapping
from typing import Any

from app.domain.reporting_models import ReportIntent, SemanticQuery


def _lookup(container: Any, key: str, default: Any = None) -> Any:
    if isinstance(container, Mapping):
        return container.get(key, default)
    return getattr(container, key, default)


def _extract_region(plan: Any, result: Mapping[str, Any]) -> str:
    explicit_region = _lookup(plan, "region")
    if explicit_region:
        return explicit_region

    filters = _lookup(plan, "filters", {})
    if isinstance(filters, Mapping) and filters.get("region"):
        return str(filters["region"])

    return str(result.get("region", "全域"))


def _derive_dimensions(plan: Any) -> list[str]:
    group_by = _lookup(plan, "group_by", []) or []
    if not isinstance(group_by, list):
        return []

    if group_by == ["month"]:
        return [dimension for dimension in group_by]

    if bool(_lookup(plan, "group_requested", False)):
        return [dimension for dimension in group_by]

    return []


def build_report_intent(
    *,
    question: str,
    tenant_id: str,
    dataset_id: str,
    trace_id: str,
    permission_context: dict,
    plan: Any,
    result: Mapping[str, Any],
) -> ReportIntent:
    metric = _lookup(plan, "metric") or result.get("metric")
    compare_to = _lookup(plan, "compare_to")
    region = _extract_region(plan=plan, result=result)
    time_window = _lookup(plan, "time_window") or result.get("time_window") or "current"

    semantic_query = SemanticQuery(
        id=f"sq-{trace_id}",
        kind="metric_query",
        measures=[metric] if metric else [],
        dimensions=_derive_dimensions(plan),
        filters=[{"field": "region", "op": "=", "value": region}],
        time={"window": time_window},
        comparison={"mode": compare_to} if compare_to else None,
    )

    return ReportIntent(
        id=f"ri-{trace_id}",
        version="1.0",
        tenant_id=tenant_id,
        dataset_id=dataset_id,
        source="chat",
        question=question,
        goal="answer question",
        permission_context=permission_context,
        semantic_queries=[semantic_query],
        explanations=[{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
        trace={"trace_id": trace_id},
    )
