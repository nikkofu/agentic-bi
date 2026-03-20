from fastapi.testclient import TestClient

from app.main import app
from app.services.query_validator import validate_plan

client = TestClient(app)


class DummyPlan:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    group_by = ["category"]


def test_rbac_scope_blocks_out_of_scope_region():
    try:
        validate_plan(DummyPlan(), allowed_regions=["华南"])
    except PermissionError:
        assert True
        return
    assert False, "expected PermissionError"


def test_chat_query_returns_403_for_out_of_scope_region():
    payload = {
        "user_id": "u-south",
        "tenant_id": "t-1",
        "question": "上个月华东区毛利率是多少？",
        "conversation_id": "c-rbac",
    }

    resp = client.post("/v1/chat/query", json=payload)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "PERMISSION_DENIED"
