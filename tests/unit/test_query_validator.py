import pytest

from app.services.query_validator import validate_plan


class DummyPlan:
    metric = "gross_margin_rate"
    filters = {"region": "华东"}
    group_by = ["category"]


def test_validator_blocks_out_of_scope_region():
    with pytest.raises(PermissionError):
        validate_plan(DummyPlan(), allowed_regions=["华南"])
