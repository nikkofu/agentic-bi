from app.services.intent_parser import parse_intent


def test_parse_margin_rate_for_region_last_month():
    intent = parse_intent("上个月华东区毛利率是多少？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"


def test_parse_margin_rate_for_south_region_last_month():
    intent = parse_intent("上个月华南区毛利率是多少？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华南"
    assert intent.time_window == "last_month"


def test_parse_recent_three_month_trend_for_east_region():
    intent = parse_intent("近3个月华东区毛利率趋势")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "recent_3_months"


def test_parse_last_month_margin_rate_month_over_month_question():
    intent = parse_intent("上个月华东区毛利率环比怎么样？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
    assert intent.compare_to == "prev_month"
