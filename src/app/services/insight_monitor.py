from app.services.insight_attribution import compute_single_layer_attribution
from app.services.insight_cards import build_insight_card
from app.services.insight_rules import evaluate_anomaly
from app.infra.repositories.insight_repo import InsightRepository


def run_monitor_once(*, snapshots: list[dict], abs_thresholds: dict, delta_thresholds: dict) -> int:
    repo = InsightRepository()
    generated = 0

    for snap in snapshots:
        metric = snap["metric"]
        event = evaluate_anomaly(
            metric=metric,
            current_value=snap["current_value"],
            baseline_value=snap["baseline_value"],
            abs_threshold=abs_thresholds.get(metric),
            delta_threshold=delta_thresholds.get(metric, 0.0),
            scope=snap["scope"],
        )
        if event is None:
            continue

        attribution = compute_single_layer_attribution(
            [{"region": snap["scope"].get("region", "全域"), "value": event.delta}],
            dimension="region",
        )
        card = build_insight_card(event=event, attribution=attribution, trace_id=f"insight-{generated+1}")
        repo.save_card(card)
        generated += 1

    return generated
