from sqlalchemy.engine import Connection

from uuid import uuid4

from app.infra.repositories.audit_repo import AuditRepository

_AUDIT_EVENTS: list[dict] = []


def new_trace_id() -> str:
    return f"trace-{uuid4().hex[:12]}"


def append_audit_event(
    event: dict,
    *,
    audit_repo: AuditRepository | None = None,
    connection: Connection | None = None,
) -> None:
    _AUDIT_EVENTS.append(event)
    active_audit_repo = audit_repo or AuditRepository()
    active_audit_repo.save(event, connection=connection)
