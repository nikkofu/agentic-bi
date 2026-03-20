from dataclasses import dataclass
from typing import Dict


ALIASES = {
    "毛利率": "gross_margin_rate",
    "销售额": "revenue",
}


@dataclass
class ParsedIntent:
    metric: str
    filters: Dict[str, str]
    time_window: str


def parse_intent(question: str) -> ParsedIntent:
    metric = ""
    for alias, canonical in ALIASES.items():
        if alias in question:
            metric = canonical
            break

    filters = {"region": "华东"} if "华东" in question else {}
    time_window = "last_month" if "上个月" in question else "current"
    return ParsedIntent(metric=metric, filters=filters, time_window=time_window)
