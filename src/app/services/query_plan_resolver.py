from app.domain.metrics_catalog import METRIC_ALIASES
from app.services.conversation_memory import apply_followup
from app.services.conversation_memory import get_last_plan
from app.services.intent_parser import parse_compare_to
from app.services.intent_parser import parse_group_by
from app.services.intent_parser import parse_intent
from app.services.intent_parser import parse_time_window
from app.services.query_planner import build_query_plan


def is_followup_question(question: str, has_previous_plan: bool) -> bool:
    if not has_previous_plan:
        return False

    has_metric_alias = any(alias in question for alias in METRIC_ALIASES)
    has_explicit_scope = any(token in question for token in ["华东", "华南"])
    has_explicit_time = parse_time_window(question) != "current"
    has_followup_cue = any(token in question for token in ["那", "呢", "按月"])
    has_compare_phrase = bool(parse_compare_to(question))
    has_grouping_request = bool(parse_group_by(question))

    if has_metric_alias and not has_explicit_scope and not has_explicit_time:
        return True
    if has_metric_alias and (has_followup_cue or has_compare_phrase or has_grouping_request) and not has_explicit_time:
        return True
    if has_metric_alias:
        return False

    return has_explicit_scope or has_followup_cue or has_compare_phrase or has_grouping_request


def resolve_plan_for_question(*, tenant_id: str, user_id: str, conversation_id: str, question: str):
    previous_plan = get_last_plan(tenant_id, user_id, conversation_id)
    if is_followup_question(question, previous_plan is not None):
        return apply_followup(question, previous_plan)

    parsed_intent = parse_intent(question)
    return build_query_plan(parsed_intent)
