from dataclasses import dataclass
from dataclasses import field
from typing import Dict

from app.domain.metrics_catalog import METRIC_ALIASES


REGION_GROUP_PHRASES = ["按区域看", "按大区看"]
CHANNEL_GROUP_PHRASES = ["按渠道看", "按销售渠道看"]
CATEGORY_GROUP_PHRASES = ["按品类看", "按产品品类看"]
INVALID_MULTI_GROUP_PHRASES = {
    ("region", "channel"): ["按区域和渠道看", "按大区和渠道看"],
    ("region", "category"): ["按区域和品类看", "按大区和品类看"],
    ("channel", "category"): ["按渠道和品类看", "按销售渠道和产品品类看"],
}
PREVIOUS_YEAR_COMPARE_PHRASES = ["同比", "和去年同期比"]
PREVIOUS_MONTH_COMPARE_PHRASES = ["环比", "和上月比", "和上个月比"]
RECENT_THREE_MONTHS_PHRASES = ["近3个月", "最近3个月", "最近三个月"]
LAST_MONTH_PHRASES = ["上个月"]


@dataclass
class ParsedIntent:
    metric: str
    filters: Dict[str, str]
    time_window: str
    compare_to: str = ""
    group_by: list[str] = field(default_factory=list)


def parse_group_by(question: str) -> list[str]:
    for dimensions, phrases in INVALID_MULTI_GROUP_PHRASES.items():
        if any(phrase in question for phrase in phrases):
            return list(dimensions)
    if any(phrase in question for phrase in REGION_GROUP_PHRASES):
        return ["region"]
    if any(phrase in question for phrase in CHANNEL_GROUP_PHRASES):
        return ["channel"]
    if any(phrase in question for phrase in CATEGORY_GROUP_PHRASES):
        return ["category"]
    return []


def parse_compare_to(question: str) -> str:
    if any(phrase in question for phrase in PREVIOUS_YEAR_COMPARE_PHRASES):
        return "prev_year"
    if any(phrase in question for phrase in PREVIOUS_MONTH_COMPARE_PHRASES):
        return "prev_month"
    return ""


def parse_time_window(question: str) -> str:
    if any(phrase in question for phrase in RECENT_THREE_MONTHS_PHRASES):
        return "recent_3_months"
    if any(phrase in question for phrase in LAST_MONTH_PHRASES):
        return "last_month"
    return "current"


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

    compare_to = parse_compare_to(question)
    group_by = parse_group_by(question)
    return ParsedIntent(
        metric=metric,
        filters=filters,
        time_window=parse_time_window(question),
        compare_to=compare_to,
        group_by=group_by,
    )
