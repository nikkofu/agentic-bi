from app.api.chat import _is_followup_question


def test_followup_detection_accepts_combined_scope_metric_compare_question():
    assert _is_followup_question("那华南销售额同比呢", has_previous_plan=True) is True
