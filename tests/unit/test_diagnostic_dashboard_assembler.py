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
    assert dashboard.pages[1].sections[0].widgets[0].kind in {"chart", "text", "insight"}
    binding_keys = {binding["source_ref"] for binding in dashboard.data_bindings}
    assert binding_keys == {"overview", "drivers"}
    assert dashboard.pages[0].sections[0].widgets[0].binding.source_ref == "overview"
    assert dashboard.pages[0].sections[0].widgets[1].binding.source_ref == "overview"
    assert dashboard.pages[1].sections[0].widgets[0].binding.source_ref == "drivers"
    assert dashboard.pages[2].sections[0].widgets[0].binding.source_ref in binding_keys


def test_assemble_diagnostic_dashboard_preserves_report_dashboard_id():
    dashboard = assemble_diagnostic_dashboard(
        report=diagnostic_report_fixture(dashboard_id="dash-existing-1"),
        result_bindings={"overview": {"value": 0.24, "rows": []}, "drivers": {"rows": []}},
    )
    assert dashboard.id == "dash-existing-1"
