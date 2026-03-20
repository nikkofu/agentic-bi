from uuid import uuid4

_AUDIT_EVENTS: list[dict] = []


def new_trace_id() -> str:
    return f"trace-{uuid4().hex[:12]}"


def append_audit_event(event: dict) -> None:
    _AUDIT_EVENTS.append(event)
