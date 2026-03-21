from app.services.insight_attribution import compute_single_layer_attribution


def test_single_layer_attribution_returns_top_dimension_item():
    rows = [
        {"region": "华东", "value": -120},
        {"region": "华南", "value": -30},
    ]
    item = compute_single_layer_attribution(rows, dimension="region")
    assert item["dimension"] == "region"
    assert item["key"] == "华东"
