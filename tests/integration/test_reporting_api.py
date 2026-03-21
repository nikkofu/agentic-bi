from fastapi.testclient import TestClient

from app.main import app


def build_intent_payload() -> dict:
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
        "trace": {"trace_id": "trace-1"},
    }


def test_generate_report_intent_endpoint_returns_protocol_document(tmp_path, monkeypatch):
    db_path = tmp_path / "report-intents.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")
    client = TestClient(app)

    resp = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": "c-1",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    assert body["permission_context"]["principal_id"] == "u-1"
    assert body["permission_context"]["role_scope"] == ["region:华东", "region:华南"]
    assert body["permission_context"]["row_level_policy_ref"] == "sales-region:u-1"
    assert body["semantic_queries"][0]["measures"] == ["gross_margin_rate"]

    stored = client.get(f"/v1/report-intents/{body['id']}")
    assert stored.status_code == 200
    assert stored.json()["id"] == body["id"]


def test_assemble_dashboard_endpoint_returns_preview_dashboard():
    client = TestClient(app)
    intent = build_intent_payload()
    resp = client.post("/v1/dashboards:assemble", json={"intent": intent})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dashboard"]["version"] == "1.0"
    assert body["dashboard"]["data_bindings"][0]["kind"] == "materialized_result"
