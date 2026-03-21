import copy

import pytest
from pydantic import ValidationError

from app.domain.reporting_models import DashboardSpec, EditorState, ReportIntent


def _build_report_intent_payload():
    return {
        "id": "ri-1",
        "version": "1.0",
        "tenant_id": "t-1",
        "dataset_id": "sales-fixture",
        "source": "chat",
        "question": "上个月华东区毛利率是多少？",
        "goal": "answer question",
        "permission_context": {
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        "semantic_queries": [{"id": "sq-1", "kind": "metric"}],
        "explanations": [],
        "constraints": {},
        "trace": {"trace_id": "trace-1"},
    }


def _build_dashboard_payload():
    return {
        "id": "dash-1",
        "version": "1.0",
        "title": "毛利率预览",
        "description": "preview",
        "theme": {"name": "paper"},
        "refresh_policy": {"mode": "manual"},
        "variables": [],
        "data_bindings": [],
        "interactions": [],
        "pages": [
            {
                "id": "page-1",
                "title": "Overview",
                "layout": {"columns": 12},
                "sections": [],
            }
        ],
    }


def test_report_intent_accepts_valid_payload():
    intent = ReportIntent(**_build_report_intent_payload())
    assert intent.version == "1.0"
    assert intent.permission_context.principal_id == "u-1"
    assert intent.semantic_queries[0].id == "sq-1"


@pytest.mark.parametrize(
    "modifier",
    [
        lambda payload: payload.__setitem__("unexpected_root", "value"),
        lambda payload: payload["permission_context"].__setitem__("unexpected_child", "value"),
    ],
)
def test_report_intent_rejects_unknown_fields(modifier):
    payload = _build_report_intent_payload()
    modifier(payload)
    with pytest.raises(ValidationError):
        ReportIntent(**payload)


def test_report_intent_rejects_empty_semantic_queries():
    payload = _build_report_intent_payload()
    payload["semantic_queries"] = []
    with pytest.raises(ValidationError):
        ReportIntent(**payload)


def test_report_intent_rejects_missing_permission_context():
    payload = _build_report_intent_payload()
    payload.pop("permission_context")
    with pytest.raises(ValidationError):
        ReportIntent(**payload)


def test_dashboard_spec_accepts_valid_payload():
    dashboard = DashboardSpec(**_build_dashboard_payload())
    assert dashboard.pages[0].id == "page-1"


@pytest.mark.parametrize(
    "modifier",
    [
        lambda payload: payload.__setitem__("unexpected_root", "value"),
        lambda payload: payload["pages"][0].__setitem__("unexpected_page", "value"),
    ],
)
def test_dashboard_spec_rejects_unknown_fields(modifier):
    payload = copy.deepcopy(_build_dashboard_payload())
    modifier(payload)
    with pytest.raises(ValidationError):
        DashboardSpec(**payload)


def test_dashboard_spec_rejects_empty_pages():
    payload = copy.deepcopy(_build_dashboard_payload())
    payload["pages"] = []
    with pytest.raises(ValidationError):
        DashboardSpec(**payload)


def test_dashboard_spec_rejects_missing_pages():
    payload = copy.deepcopy(_build_dashboard_payload())
    payload.pop("pages")
    with pytest.raises(ValidationError):
        DashboardSpec(**payload)


def test_editor_state_accepts_valid_payload():
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


def test_editor_state_rejects_unknown_fields():
    payload = {
        "version": "1.0",
        "document_id": "dash-1",
        "selection": {},
        "draft_layout_overrides": {},
        "panel_state": {},
        "history": [],
        "validation_markers": [],
        "viewport": {},
        "extra": "value",
    }
    with pytest.raises(ValidationError):
        EditorState(**payload)
