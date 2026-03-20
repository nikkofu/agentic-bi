from dataclasses import dataclass
from typing import Dict

from app.domain.metrics_catalog import METRIC_ALIASES


@dataclass
class ParsedIntent:
    metric: str
    filters: Dict[str, str]
    time_window: str


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

    time_window = "last_month" if "上个月" in question else "current"
    return ParsedIntent(metric=metric, filters=filters, time_window=time_window)
