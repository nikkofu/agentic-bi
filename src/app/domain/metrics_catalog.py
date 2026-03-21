METRIC_ALIASES = {
    "毛利率": "gross_margin_rate",
    "销售额": "revenue",
    "毛利额": "gross_profit",
    "毛利": "gross_profit",
    "营收": "revenue",
    "收入": "revenue",
}

PRIMARY_METRIC_SUGGESTIONS = ["毛利率", "销售额", "毛利额"]
GROUP_DIMENSION_SUGGESTION_MAP = {
    "region": "按区域看",
    "channel": "按渠道看",
    "category": "按品类看",
}
GROUP_DIMENSION_SUGGESTIONS = list(GROUP_DIMENSION_SUGGESTION_MAP.values())

METRIC_LABELS = {
    "gross_margin_rate": "毛利率",
    "revenue": "销售额",
    "gross_profit": "毛利额",
}

METRIC_AGGREGATIONS = {
    "gross_margin_rate": "average",
    "revenue": "sum",
    "gross_profit": "sum",
}

DIMENSION_LABELS = {
    "region": "区域",
    "channel": "渠道",
    "category": "品类",
    "month": "月份",
}

SUPPORTED_DIMENSIONS = ["region", "category", "channel", "month"]
