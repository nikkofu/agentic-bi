from copy import deepcopy

from app.domain.metrics_catalog import METRIC_ALIASES
from app.services.intent_parser import parse_compare_to
from app.services.intent_parser import parse_group_by

_conversation_store: dict[str, object] = {}


def apply_followup(question: str, previous_plan):
    plan = deepcopy(previous_plan)
    for alias, metric in METRIC_ALIASES.items():
        if alias in question:
            plan.metric = metric
            break

    group_by = parse_group_by(question)
    if group_by:
        plan.group_by = group_by
        plan.group_requested = True

    if "按月" in question:
        plan.time_window = "recent_3_months"
        plan.group_by = ["month"]
        plan.group_requested = False

    compare_to = parse_compare_to(question)
    if compare_to:
        plan.compare_to = compare_to
    if "华南" in question:
        plan.filters["region"] = "华南"
    elif "华东" in question:
        plan.filters["region"] = "华东"
    return plan


def _conversation_key(tenant_id: str, user_id: str, conversation_id: str) -> str:
    return f"{tenant_id}:{user_id}:{conversation_id}"


def save_last_plan(tenant_id: str, user_id: str, conversation_id: str, plan) -> None:
    _conversation_store[_conversation_key(tenant_id, user_id, conversation_id)] = deepcopy(plan)


def get_last_plan(tenant_id: str, user_id: str, conversation_id: str):
    return deepcopy(_conversation_store.get(_conversation_key(tenant_id, user_id, conversation_id)))
