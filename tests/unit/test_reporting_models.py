from app.domain.reporting_models import ChartPresentation, DashboardSpec, EditorState, ReportIntent


def test_report_intent_requires_version_and_semantic_queries():
    intent = ReportIntent(
        id="ri-1",
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
        semantic_queries=[{"id": "sq-1", "kind": "metric"}],
        explanations=[],
        constraints={},
        trace={"trace_id": "trace-1"},
    )
    assert intent.version == "1.0"
    assert intent.permission_context.principal_id == "u-1"
    assert intent.semantic_queries[0].id == "sq-1"


def test_dashboard_spec_requires_pages_and_widget_bindings():
    dashboard = DashboardSpec(
        id="dash-1",
        version="1.0",
        title="毛利率预览",
        description="preview",
        theme={"name": "paper"},
        refresh_policy={"mode": "manual"},
        variables=[],
        data_bindings=[],
        interactions=[],
        pages=[
            {
                "id": "page-1",
                "title": "Overview",
                "layout": {"columns": 12},
                "sections": [],
            }
        ],
    )
    assert dashboard.pages[0].id == "page-1"


def test_editor_state_stays_separate_from_dashboard_spec():
    state = EditorState(
        version="1.0",
        document_id="dash-1",
        selection={"widget_ids": ["widget-1"]},
        draft_layout_overrides={},
        panel_state={},
        history=[],
        validation_markers=[],
        viewport={"zoom": 1},
    )
    assert state.document_id == "dash-1"
