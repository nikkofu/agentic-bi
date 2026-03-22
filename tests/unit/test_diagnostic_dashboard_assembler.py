from fixtures_diagnostic_reports import diagnostic_report_fixture
from app.services.diagnostic_dashboard_assembler import assemble_diagnostic_dashboard


def test_assemble_diagnostic_dashboard_outputs_overview_drivers_actions_pages():
    dashboard = assemble_diagnostic_dashboard(
        report=diagnostic_report_fixture(),
        result_bindings={
            "overview": {"value": 0.24, "rows": [{"month": "2026-02", "value": 0.24}]},
            "drivers": {"rows": [{"region": "华东", "value": -0.06}]},
        },
    )
    assert [page.title for page in dashboard.pages] == ["Overview", "Drivers", "Actions"]
    assert [widget.kind for widget in dashboard.pages[0].sections[0].widgets] == ["metric_card", "chart"]
    assert [widget.kind for widget in dashboard.pages[1].sections[0].widgets] == ["chart"]
    assert [widget.kind for widget in dashboard.pages[2].sections[0].widgets] == ["text"]

    bindings_by_source = {binding["source_ref"]: binding for binding in dashboard.data_bindings}
    assert set(bindings_by_source.keys()) == {"overview", "drivers", "actions"}

    overview_metric = dashboard.pages[0].sections[0].widgets[0]
    overview_chart = dashboard.pages[0].sections[0].widgets[1]
    drivers_chart = dashboard.pages[1].sections[0].widgets[0]
    actions_text = dashboard.pages[2].sections[0].widgets[0]

    assert overview_metric.binding.source_ref == "overview"
    assert "value" in bindings_by_source[overview_metric.binding.source_ref]
    assert overview_chart.binding.source_ref == "overview"
    assert "rows" in bindings_by_source[overview_chart.binding.source_ref]
    assert drivers_chart.binding.source_ref == "drivers"
    assert "rows" in bindings_by_source[drivers_chart.binding.source_ref]
    assert actions_text.binding.source_ref == "actions"
    assert "text" in bindings_by_source[actions_text.binding.source_ref]
    assert bindings_by_source[actions_text.binding.source_ref]["text"] == "1. 继续分析渠道: 请分析渠道影响"


def test_assemble_diagnostic_dashboard_preserves_report_dashboard_id():
    dashboard = assemble_diagnostic_dashboard(
        report=diagnostic_report_fixture(dashboard_id="dash-existing-1"),
        result_bindings={"overview": {"value": 0.24, "rows": []}, "drivers": {"rows": []}},
    )
    assert dashboard.id == "dash-existing-1"


def test_assemble_diagnostic_dashboard_data_binding_contract_fields_cannot_be_overridden():
    report = diagnostic_report_fixture()
    dashboard = assemble_diagnostic_dashboard(
        report=report,
        result_bindings={
            "overview": {
                "id": "caller-overview-id",
                "source_ref": "caller-overview-source",
                "kind": "caller-overview-kind",
                "value": 0.24,
                "rows": [{"month": "2026-02", "value": 0.24}],
            },
            "drivers": {
                "id": "caller-drivers-id",
                "source_ref": "caller-drivers-source",
                "kind": "caller-drivers-kind",
                "rows": [{"region": "华东", "value": -0.06}],
            },
        },
    )
    bindings_by_source = {binding["source_ref"]: binding for binding in dashboard.data_bindings}
    assert set(bindings_by_source.keys()) == {"overview", "drivers", "actions"}

    assert bindings_by_source["overview"]["id"] == f"binding-{report.id}-overview"
    assert bindings_by_source["overview"]["kind"] == "materialized_result"
    assert bindings_by_source["drivers"]["id"] == f"binding-{report.id}-drivers"
    assert bindings_by_source["drivers"]["kind"] == "materialized_result"
    assert bindings_by_source["actions"]["id"] == f"binding-{report.id}-actions"
    assert bindings_by_source["actions"]["kind"] == "materialized_result"
