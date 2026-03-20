from app.services.query_validator import validate_plan


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
