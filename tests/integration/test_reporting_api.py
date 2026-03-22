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


def build_multi_query_intent_payload() -> dict:
    payload = build_intent_payload()
    payload["semantic_queries"] = [
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
        },
        {
            "id": "sq-2",
            "kind": "metric_query",
            "measures": ["revenue"],
            "dimensions": ["month"],
            "filters": [{"field": "region", "op": "=", "value": "华东"}],
            "time": {"window": "recent_3_months"},
            "comparison": None,
            "sort": None,
            "limit": None,
            "display_hint": {},
        },
    ]
    return payload


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

    stored = client.get(
        f"/v1/report-intents/{body['id']}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1"},
    )
    assert stored.status_code == 200
    assert stored.json()["id"] == body["id"]


def test_assemble_dashboard_endpoint_returns_preview_dashboard():
    client = TestClient(app)
    intent = build_intent_payload()
    resp = client.post(
        "/v1/dashboards:assemble",
        json={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1", "intent": intent},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dashboard"]["version"] == "1.0"
    assert body["dashboard"]["data_bindings"][0]["kind"] == "materialized_result"


def test_generate_report_intent_endpoint_resolves_followup_from_conversation_context():
    client = TestClient(app)
    conversation_id = "c-followup-reporting-preview"

    initial_resp = client.post(
        "/v1/chat/query",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "conversation_id": conversation_id,
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert initial_resp.status_code == 200

    followup_resp = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": conversation_id,
            "question": "按月看",
        },
    )
    assert followup_resp.status_code == 200
    body = followup_resp.json()
    assert body["semantic_queries"][0]["time"]["window"] == "recent_3_months"
    assert body["semantic_queries"][0]["dimensions"] == ["month"]


def test_assemble_dashboard_endpoint_represents_all_semantic_queries():
    client = TestClient(app)
    intent = build_multi_query_intent_payload()
    resp = client.post(
        "/v1/dashboards:assemble",
        json={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1", "intent": intent},
    )
    assert resp.status_code == 200
    body = resp.json()

    binding_refs = {binding["source_ref"] for binding in body["dashboard"]["data_bindings"]}
    assert binding_refs == {"sq-1", "sq-2"}

    widget_refs = {
        widget["binding"]["source_ref"]
        for page in body["dashboard"]["pages"]
        for section in page["sections"]
        for widget in section["widgets"]
    }
    assert widget_refs == {"sq-1", "sq-2"}


def test_assemble_dashboard_cannot_widen_access_with_forged_role_scope():
    client = TestClient(app)
    intent = build_intent_payload()
    intent["permission_context"]["role_scope"] = ["region:华东", "region:华南"]
    intent["semantic_queries"][0]["filters"] = [{"field": "region", "op": "=", "value": "华东"}]

    resp = client.post(
        "/v1/dashboards:assemble",
        json={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south", "intent": intent},
    )

    assert resp.status_code == 403


def test_get_report_intent_denies_cross_user_access():
    client = TestClient(app)
    generated = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": "c-get-owner",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert generated.status_code == 200
    intent_id = generated.json()["id"]

    denied = client.get(
        f"/v1/report-intents/{intent_id}",
        params={"tenant_id": "t-1", "user_id": "u-south", "principal_id": "u-south"},
    )
    assert denied.status_code == 403


def test_generate_report_intent_rejects_principal_mismatch():
    client = TestClient(app)
    resp = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-other",
            "conversation_id": "c-principal-mismatch",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert resp.status_code == 400


def test_assemble_dashboard_rejects_principal_mismatch():
    client = TestClient(app)
    resp = client.post(
        "/v1/dashboards:assemble",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-other",
            "intent": build_intent_payload(),
        },
    )
    assert resp.status_code == 400


def test_get_report_intent_rejects_principal_mismatch():
    client = TestClient(app)
    generated = client.post(
        "/v1/report-intents:generate",
        json={
            "tenant_id": "t-1",
            "user_id": "u-1",
            "principal_id": "u-1",
            "conversation_id": "c-get-principal-mismatch",
            "question": "上个月华东区毛利率是多少？",
        },
    )
    assert generated.status_code == 200
    intent_id = generated.json()["id"]

    resp = client.get(
        f"/v1/report-intents/{intent_id}",
        params={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-other"},
    )
    assert resp.status_code == 400


def test_assemble_dashboard_rejects_unsupported_semantic_filter_operator():
    client = TestClient(app)
    intent = build_intent_payload()
    intent["semantic_queries"][0]["filters"] = [{"field": "region", "op": "!=", "value": "华南"}]

    resp = client.post(
        "/v1/dashboards:assemble",
        json={"tenant_id": "t-1", "user_id": "u-1", "principal_id": "u-1", "intent": intent},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "UNSUPPORTED_SEMANTIC_FILTER"
