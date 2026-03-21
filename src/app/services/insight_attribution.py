def compute_single_layer_attribution(rows: list[dict], dimension: str) -> dict:
    if not rows:
        return {"dimension": dimension, "key": "", "contribution": 0.0}

    best = max(rows, key=lambda r: abs(r.get("value", 0)))
    return {
        "dimension": dimension,
        "key": best.get(dimension, ""),
        "contribution": best.get("value", 0),
    }
