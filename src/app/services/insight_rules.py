from app.domain.insight_models import AnomalyEvent


def _severity_from_delta(delta: float) -> str:
    abs_delta = abs(delta)
    if abs_delta >= 0.08:
        return "P1"
    if abs_delta >= 0.05:
        return "P2"
    return "P3"


def evaluate_anomaly(
    *,
    metric: str,
    current_value: float,
    baseline_value: float,
    abs_threshold: float | None,
    delta_threshold: float,
    scope: dict[str, str],
):
    delta = current_value - baseline_value
    if abs_threshold is not None and current_value < abs_threshold:
        return AnomalyEvent(
            metric=metric,
            scope=scope,
            current_value=current_value,
            baseline_value=baseline_value,
            delta=delta,
            severity=_severity_from_delta(delta),
            trigger_rule="absolute_threshold",
        )

    if abs(delta) >= delta_threshold:
        return AnomalyEvent(
            metric=metric,
            scope=scope,
            current_value=current_value,
            baseline_value=baseline_value,
            delta=delta,
            severity=_severity_from_delta(delta),
            trigger_rule="delta_threshold",
        )

    return None
