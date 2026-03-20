from copy import deepcopy

_conversation_store: dict[str, object] = {}


def apply_followup(question: str, previous_plan):
    plan = deepcopy(previous_plan)
    if "按月" in question:
        plan.time_window = "recent_3_months"
        plan.group_by = ["month"]
    if "同比" in question:
        plan.compare_to = "prev_year"
    elif "环比" in question:
        plan.compare_to = "prev_month"
    if "华南" in question:
        plan.filters["region"] = "华南"
    elif "华东" in question:
        plan.filters["region"] = "华东"
    return plan


def save_last_plan(conversation_id: str, plan) -> None:
    _conversation_store[conversation_id] = deepcopy(plan)


def get_last_plan(conversation_id: str):
    return deepcopy(_conversation_store.get(conversation_id))
