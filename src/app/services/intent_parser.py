from dataclasses import dataclass
from typing import Dict

from app.domain.metrics_catalog import METRIC_ALIASES


@dataclass
class ParsedIntent:
    metric: str
    filters: Dict[str, str]
    time_window: str
    compare_to: str = ""


def parse_intent(question: str) -> ParsedIntent:
    metric = ""
    for alias, canonical in METRIC_ALIASES.items():
        if alias in question:
            metric = canonical
            break

    filters = {}
    if "华东" in question:
        filters["region"] = "华东"
    elif "华南" in question:
        filters["region"] = "华南"

    if "同比" in question:
        compare_to = "prev_year"
    elif "环比" in question:
        compare_to = "prev_month"
    else:
        compare_to = ""

    if "近3个月" in question:
        time_window = "recent_3_months"
    elif "上个月" in question:
        time_window = "last_month"
    else:
        time_window = "current"
    return ParsedIntent(metric=metric, filters=filters, time_window=time_window, compare_to=compare_to)
