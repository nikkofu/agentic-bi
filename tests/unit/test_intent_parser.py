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


def test_parse_gross_profit_for_region_last_month():
    intent = parse_intent("上个月华东区毛利额是多少？")
    assert intent.metric == "gross_profit"
    assert intent.filters["region"] == "华东"
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


def test_parse_last_month_margin_rate_with_previous_month_phrase():
    intent = parse_intent("上个月华东区毛利率和上月比怎么样？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
    assert intent.compare_to == "prev_month"


def test_parse_last_month_margin_rate_year_over_year_question():
    intent = parse_intent("上个月华东区毛利率同比怎么样？")
    assert intent.metric == "gross_margin_rate"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
    assert intent.compare_to == "prev_year"


def test_parse_recent_three_months_alias_for_revenue_trend():
    intent = parse_intent("最近三个月华东区营收走势")
    assert intent.metric == "revenue"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "recent_3_months"


def test_parse_last_month_revenue_grouped_by_channel():
    intent = parse_intent("上个月华东区销售额按渠道看")
    assert intent.metric == "revenue"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
    assert intent.group_by == ["channel"]


def test_parse_last_month_revenue_grouped_by_region():
    intent = parse_intent("上个月销售额按区域看")
    assert intent.metric == "revenue"
    assert intent.filters == {}
    assert intent.time_window == "last_month"
    assert intent.group_by == ["region"]


def test_parse_revenue_alias_with_channel_phrase():
    intent = parse_intent("上个月华东大区营收按销售渠道看")
    assert intent.metric == "revenue"
    assert intent.filters["region"] == "华东"
    assert intent.time_window == "last_month"
    assert intent.group_by == ["channel"]


def test_parse_invalid_multi_dimension_grouping_request():
    intent = parse_intent("上个月华东区销售额按渠道和品类看")
    assert intent.metric == "revenue"
    assert intent.group_by == ["channel", "category"]


def test_parse_invalid_region_and_channel_grouping_request():
    intent = parse_intent("上个月销售额按区域和渠道看")
    assert intent.metric == "revenue"
    assert intent.group_by == ["region", "channel"]
