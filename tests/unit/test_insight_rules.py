from app.domain.insight_models import AnomalyEvent
from app.services.insight_rules import evaluate_anomaly


def test_anomaly_event_model_contract():
    event = AnomalyEvent(
        metric="gross_margin_rate",
        scope={"region": "华东"},
        current_value=0.31,
        baseline_value=0.28,
        delta=0.03,
        severity="P2",
        trigger_rule="delta_threshold",
    )
    assert event.metric == "gross_margin_rate"
    assert event.scope["region"] == "华东"


def test_delta_threshold_triggers_event():
    event = evaluate_anomaly(
        metric="gross_margin_rate",
        current_value=0.24,
        baseline_value=0.30,
        abs_threshold=None,
        delta_threshold=0.04,
        scope={"region": "华东"},
    )
    assert event is not None
    assert event.severity in {"P1", "P2", "P3"}
