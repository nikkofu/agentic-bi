from app.services.report_intent_builder import build_report_intent


def test_build_report_intent_maps_existing_query_plan_to_semantic_query():
    intent = build_report_intent(
        question="上个月华东区毛利率是多少？",
        tenant_id="t-1",
        dataset_id="sales-fixture",
        trace_id="trace-1",
        permission_context={
            "principal_id": "u-1",
            "role_scope": ["region:华东"],
            "row_level_policy_ref": "sales-region:u-1",
        },
        plan={"metric": "gross_margin_rate", "region": "华东", "time_window": "last_month"},
        result={"metric": "gross_margin_rate", "value": 0.32, "region": "华东"},
    )
    assert intent.semantic_queries[0].measures == ["gross_margin_rate"]
    assert intent.permission_context.principal_id == "u-1"
    assert intent.trace["trace_id"] == "trace-1"
