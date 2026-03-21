from collections.abc import Mapping
from typing import Any

from app.domain.reporting_models import (
    DashboardPage,
    DashboardSection,
    DashboardSpec,
    DashboardWidget,
    ReportIntent,
    WidgetBinding,
    WidgetPresentation,
)


def _chart_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    series = result.get("series", [])
    if isinstance(series, list) and series:
        return [dict(row) for row in series]

    breakdown = result.get("breakdown", [])
    if isinstance(breakdown, list) and breakdown:
        return [dict(row) for row in breakdown]

    return [dict(result)]


def build_materialized_binding(*, intent: ReportIntent, result: Mapping[str, Any]) -> dict:
    source_ref = intent.semantic_queries[0].id
    return {
        "id": f"binding-{intent.trace['trace_id']}",
        "source_ref": source_ref,
        "kind": "materialized",
        "rows": _chart_rows(result),
    }


def build_overview_page(*, intent: ReportIntent, result: Mapping[str, Any]) -> DashboardPage:
    trace_id = intent.trace["trace_id"]
    source_ref = intent.semantic_queries[0].id
    metric = result.get("metric", intent.semantic_queries[0].measures[0] if intent.semantic_queries[0].measures else "")

    metric_widget = DashboardWidget(
        id=f"widget-metric-{trace_id}",
        kind="metric_card",
        title="核心指标",
        presentation=WidgetPresentation(family="kpi", variant="primary"),
        binding=WidgetBinding(source_ref=source_ref, value_path="value"),
    )
    chart_widget = DashboardWidget(
        id=f"widget-chart-{trace_id}",
        kind="chart",
        title="趋势/分布",
        presentation=WidgetPresentation(
            family="table_like",
            variant="auto",
            config={"metric": metric},
        ),
        binding=WidgetBinding(source_ref=source_ref, value_path="rows"),
    )
    insight_widget = DashboardWidget(
        id=f"widget-insight-{trace_id}",
        kind="insight",
        title="解读",
        presentation=WidgetPresentation(family="narrative", variant="auto"),
        binding=WidgetBinding(source_ref=source_ref, value_path="insight"),
    )

    section = DashboardSection(
        id=f"section-overview-{trace_id}",
        title="Overview",
        layout={"columns": 12},
        widgets=[metric_widget, chart_widget, insight_widget],
    )
    return DashboardPage(
        id=f"page-overview-{trace_id}",
        title="Overview",
        layout={"columns": 12},
        sections=[section],
    )


def assemble_dashboard(*, intent: ReportIntent, result: Mapping[str, Any]) -> DashboardSpec:
    return DashboardSpec(
        id=f"dash-preview-{intent.trace['trace_id']}",
        version="1.0",
        title=intent.question,
        description="Auto-generated dashboard preview",
        theme={"name": "paper"},
        refresh_policy={"mode": "manual"},
        variables=[],
        data_bindings=[build_materialized_binding(intent=intent, result=result)],
        interactions=[],
        pages=[build_overview_page(intent=intent, result=result)],
    )
