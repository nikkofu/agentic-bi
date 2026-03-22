from app.services.query_plan_resolver import is_followup_question


def test_followup_detection_accepts_combined_scope_metric_compare_question():
    assert is_followup_question("那华南销售额同比呢", has_previous_plan=True) is True


def test_followup_detection_accepts_grouped_breakdown_question():
    assert is_followup_question("按渠道看", has_previous_plan=True) is True
