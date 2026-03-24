from app.domain.insight_models import AnomalyEvent
from app.services.insight_cards import build_insight_card


def test_card_builder_outputs_required_fields():
    event = AnomalyEvent(
        metric="gross_margin_rate",
        scope={"region": "华东"},
        current_value=0.24,
        baseline_value=0.30,
        delta=-0.06,
        severity="P1",
        trigger_rule="delta_threshold",
    )
    attribution = {"dimension": "region", "key": "华东", "contribution": -0.06}
    card = build_insight_card(event=event, attribution=attribution, trace_id="trace-1")
    assert card["summary"]
    assert card["severity"] == event.severity
    assert card["suggested_next_question"]
    assert card["report_status"] is None
    assert card["report_error_code"] is None
