from app.domain.reporting_models import ReportIntent
from app.services.dashboard_assembler import assemble_dashboard


def intent_fixture() -> ReportIntent:
    return ReportIntent(
        id="ri-trace-1",
        version="1.0",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        source="chat",
        question="上个月华东区毛利率是多少？",
        goal="answer question",
        permission_context={
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        semantic_queries=[
            {
                "id": "sq-trace-1",
                "kind": "metric_query",
                "measures": ["gross_margin_rate"],
                "dimensions": [],
                "filters": [{"field": "region", "op": "=", "value": "华东"}],
                "time": {"window": "last_month"},
            }
        ],
        explanations=[{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
        trace={"trace_id": "trace-1"},
    )


def test_assemble_dashboard_creates_metric_card_chart_and_insight_widgets():
    dashboard = assemble_dashboard(
        intent=intent_fixture(),
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东", "series": []},
    )
    widget_kinds = [widget.kind for widget in dashboard.pages[0].sections[0].widgets]
    assert widget_kinds == ["metric_card", "chart", "insight"]
    assert dashboard.pages[0].sections[0].widgets[1].presentation.family == "table_like"
    assert (
        dashboard.data_bindings[0]["source_ref"]
        == dashboard.pages[0].sections[0].widgets[1].binding.source_ref
    )


def test_assemble_dashboard_emits_binding_payload_for_all_widget_value_paths():
    dashboard = assemble_dashboard(
        intent=intent_fixture(),
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东", "series": []},
    )

    section = dashboard.pages[0].sections[0]
    binding_payload = dashboard.data_bindings[0]
    assert binding_payload["source_ref"] == section.widgets[0].binding.source_ref

    for widget in section.widgets:
        assert widget.binding.source_ref == binding_payload["source_ref"]
        assert widget.binding.value_path in binding_payload
