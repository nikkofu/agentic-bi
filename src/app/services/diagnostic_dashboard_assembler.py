from typing import Any

from app.domain.diagnostic_report_models import DiagnosticReport
from app.domain.reporting_models import (
    DashboardPage,
    DashboardSection,
    DashboardSpec,
    DashboardWidget,
    WidgetBinding,
    WidgetPresentation,
)


def _binding_ref(report: DiagnosticReport, source_ref: str) -> str:
    return f"binding-{report.id}-{source_ref}"


def _materialized_binding(
    *,
    report: DiagnosticReport,
    source_ref: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        **payload,
        "id": _binding_ref(report, source_ref),
        "source_ref": source_ref,
        "kind": "materialized_result",
    }


def _actions_text(report: DiagnosticReport) -> str:
    if not report.recommendations:
        return ""
    return "\n".join(
        f"{index}. {recommendation.label}: {recommendation.question}"
        for index, recommendation in enumerate(report.recommendations, start=1)
    )


def build_overview_page(report: DiagnosticReport) -> DashboardPage:
    source_ref = "overview"
    section = DashboardSection(
        id=f"section-overview-{report.id}",
        title="Overview",
        layout={"columns": 12},
        widgets=[
            DashboardWidget(
                id=f"widget-overview-metric-{report.id}",
                kind="metric_card",
                title="核心指标",
                presentation=WidgetPresentation(family="kpi", variant="primary"),
                binding=WidgetBinding(source_ref=source_ref, value_path="value"),
            ),
            DashboardWidget(
                id=f"widget-overview-chart-{report.id}",
                kind="chart",
                title="趋势/分布",
                presentation=WidgetPresentation(
                    family="table_like",
                    variant="auto",
                    config={"metric": report.summary.metric},
                ),
                binding=WidgetBinding(source_ref=source_ref, value_path="rows"),
            ),
        ],
    )
    return DashboardPage(
        id=f"page-overview-{report.id}",
        title="Overview",
        layout={"columns": 12},
        sections=[section],
    )


def build_drivers_page(report: DiagnosticReport) -> DashboardPage:
    source_ref = "drivers"
    section = DashboardSection(
        id=f"section-drivers-{report.id}",
        title="Drivers",
        layout={"columns": 12},
        widgets=[
            DashboardWidget(
                id=f"widget-drivers-chart-{report.id}",
                kind="chart",
                title="Drivers",
                presentation=WidgetPresentation(
                    family="table_like",
                    variant="auto",
                    config={"metric": report.summary.metric},
                ),
                binding=WidgetBinding(source_ref=source_ref, value_path="rows"),
            )
        ],
    )
    return DashboardPage(
        id=f"page-drivers-{report.id}",
        title="Drivers",
        layout={"columns": 12},
        sections=[section],
    )


def build_actions_page(report: DiagnosticReport) -> DashboardPage:
    source_ref = "actions"
    section = DashboardSection(
        id=f"section-actions-{report.id}",
        title="Actions",
        layout={"columns": 12},
        widgets=[
            DashboardWidget(
                id=f"widget-actions-{report.id}",
                kind="text",
                title="Recommended Actions",
                presentation=WidgetPresentation(family="narrative", variant="secondary"),
                binding=WidgetBinding(source_ref=source_ref),
            )
        ],
    )
    return DashboardPage(
        id=f"page-actions-{report.id}",
        title="Actions",
        layout={"columns": 12},
        sections=[section],
    )


def assemble_diagnostic_dashboard(
    *,
    report: DiagnosticReport,
    result_bindings: dict[str, dict[str, Any]],
) -> DashboardSpec:
    overview_binding = _materialized_binding(
        report=report,
        source_ref="overview",
        payload=result_bindings["overview"],
    )
    drivers_binding = _materialized_binding(
        report=report,
        source_ref="drivers",
        payload=result_bindings["drivers"],
    )
    actions_binding = _materialized_binding(
        report=report,
        source_ref="actions",
        payload={"text": _actions_text(report)},
    )

    return DashboardSpec(
        id=report.dashboard_id,
        version="1.0",
        title=report.summary.title,
        description=report.summary.headline,
        theme={"name": "paper"},
        refresh_policy={"mode": "snapshot"},
        variables=[],
        data_bindings=[overview_binding, drivers_binding, actions_binding],
        interactions=[],
        pages=[build_overview_page(report), build_drivers_page(report), build_actions_page(report)],
    )
