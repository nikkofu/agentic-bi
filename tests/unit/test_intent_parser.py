from app.services.intent_parser import parse_intent


def test_parse_margin_rate_for_region_last_month():
    intent = parse_intent("上个月华东区毛利率是多少？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
