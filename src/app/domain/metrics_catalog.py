METRIC_ALIASES = {
    "毛利率": "gross_margin_rate",
    "销售额": "revenue",
}

METRIC_LABELS = {
    "gross_margin_rate": "毛利率",
    "revenue": "销售额",
}

METRIC_AGGREGATIONS = {
    "gross_margin_rate": "average",
    "revenue": "sum",
}

SUPPORTED_DIMENSIONS = ["region", "category", "channel", "date"]
