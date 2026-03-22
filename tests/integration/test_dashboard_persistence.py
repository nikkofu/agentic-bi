from fastapi.testclient import TestClient

from app.main import app
from app.services import access_policy


def build_report_intent_payload() -> dict:
    return {
        "id": "ri-seed-1",
        "version": "1.0",
        "tenant_id": "t-1",
        "dataset_id": "sales-fixture",
        "source": "chat",
        "question": "上个月华东区毛利率是多少？",
        "goal": "answer question",
        "permission_context": {
            "principal_id": "u-1",
            "role_scope": ["region:华东", "region:华南"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        "semantic_queries": [
            {
                "id": "sq-1",
                "kind": "metric_query",
                "measures": ["gross_margin_rate"],
                "dimensions": [],
                "filters": [{"field": "region", "op": "=", "value": "华东"}],
                "time": {"window": "last_month"},
                "comparison": None,
                "sort": None,
                "limit": None,
                "display_hint": {},
            }
        ],
        "explanations": [{"id": "why-chart", "type": "chart_choice_reason", "content": "auto"}],
        "constraints": {},
        "trace": {"trace_id": "trace-seed-1"},
    }


def build_dashboard_spec_payload() -> dict:
    return {
        "id": "dash-preview-seed-1",
        "version": "1.0",
        "title": "毛利率预览",
        "description": "preview",
        "theme": {"name": "paper"},
        "refresh_policy": {"mode": "manual"},
        "variables": [],
        "data_bindings": [
            {
                "id": "binding-1",
                "source_ref": "sq-1",
                "kind": "materialized_result",
                "value": 0.31,
                "rows": [{"region": "华东", "gross_margin_rate": 0.31}],
                "insight": "auto",
            }
        ],
        "interactions": [],
        "pages": [
            {
                "id": "page-1",
                "title": "Overview",
                "layout": {"columns": 12},
                "sections": [
                    {
                        "id": "section-1",
                        "title": "Summary",
                        "layout": {"columns": 12},
                        "widgets": [
                            {
                                "id": "widget-1",
                                "kind": "metric_card",
                                "title": "核心指标",
                                "presentation": {"family": "kpi", "variant": "primary", "config": {}},
                                "binding": {"source_ref": "sq-1", "value_path": "value"},
                            }
                        ],
                    }
                ],
            }
        ],
    }


def dashboard_payload() -> dict:
    return {
        "tenant_id": "t-1",
        "user_id": "u-1",
        "principal_id": "u-1",
        "report_intent": build_report_intent_payload(),
        "dashboard": build_dashboard_spec_payload(),
    }


def test_create_dashboard_persists_current_and_published_revision(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    resp = client.post("/v1/dashboards", json=dashboard_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["dashboard_id"].startswith("dash-")
    assert body["report_intent_id"].startswith("ri-")

    stored = client.get(
        f"/v1/dashboards/{body['dashboard_id']}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert stored.status_code == 200
    assert stored.json()["dashboard"]["version"] == "1.0"
    assert stored.json()["report_intent"]["id"] == body["report_intent_id"]
    assert stored.json()["current_revision_id"] == stored.json()["published_revision_id"]


def test_get_dashboard_denies_cross_user_access(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards-owner.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    created = client.post("/v1/dashboards", json=dashboard_payload())
    assert created.status_code == 201
    dashboard_id = created.json()["dashboard_id"]

    denied = client.get(
        f"/v1/dashboards/{dashboard_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert denied.status_code == 403


def test_create_dashboard_reuses_existing_report_intent_for_owner(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards-existing-intent.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    first = client.post("/v1/dashboards", json=dashboard_payload())
    assert first.status_code == 201

    second = client.post("/v1/dashboards", json=dashboard_payload())
    assert second.status_code == 201
    assert second.json()["dashboard_id"] != first.json()["dashboard_id"]
    assert second.json()["report_intent_id"] == first.json()["report_intent_id"]


def test_create_dashboard_rejects_forged_report_intent_scope(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards-forged-scope.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    payload = dashboard_payload()
    payload["report_intent"]["permission_context"]["role_scope"] = ["region:华北"]

    resp = client.post("/v1/dashboards", json=payload)

    assert resp.status_code == 403


def test_create_dashboard_rejects_reuse_when_stored_intent_scope_has_drifted(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards-stored-intent-scope-drift.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    created = client.post("/v1/dashboards", json=dashboard_payload())
    assert created.status_code == 201

    monkeypatch.setitem(access_policy.USER_REGION_SCOPES, ("t-1", "u-1"), ["华东"])
    payload = dashboard_payload()
    payload["report_intent"]["permission_context"]["role_scope"] = ["region:华东"]

    resp = client.post("/v1/dashboards", json=payload)

    assert resp.status_code == 403


def test_get_dashboard_rejects_scope_drift_for_same_owner(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboards-fetch-scope-drift.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    created = client.post("/v1/dashboards", json=dashboard_payload())
    assert created.status_code == 201
    dashboard_id = created.json()["dashboard_id"]

    monkeypatch.setitem(access_policy.USER_REGION_SCOPES, ("t-1", "u-1"), ["华东"])

    resp = client.get(
        f"/v1/dashboards/{dashboard_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )

    assert resp.status_code == 403
