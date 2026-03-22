import json

from sqlalchemy.engine import Connection
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import inspect
from sqlalchemy import insert
from sqlalchemy import text

from app.infra.db import get_engine

metadata = MetaData()

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", String, nullable=False),
    Column("status", String, nullable=False),
    Column("question", String, nullable=False),
    Column("conversation_id", String, nullable=False),
    Column("query_plan", Text, nullable=True),
    Column("response_type", String, nullable=True),
    Column("error_code", String, nullable=True),
    Column("result_summary", Text, nullable=True),
)


class AuditRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)
        self._ensure_columns()

    def _ensure_columns(self) -> None:
        inspector = inspect(self.engine)
        existing_columns = {column["name"] for column in inspector.get_columns("audit_events")}
        expected_columns = {
            "query_plan": "TEXT",
            "response_type": "VARCHAR",
            "error_code": "VARCHAR",
            "result_summary": "TEXT",
        }
        for column_name, column_type in expected_columns.items():
            if column_name not in existing_columns:
                with self.engine.begin() as connection:
                    connection.execute(
                        text(f"ALTER TABLE audit_events ADD COLUMN {column_name} {column_type}")
                    )

    def save(self, record: dict, connection: Connection | None = None) -> dict:
        def _persist(active_connection: Connection) -> None:
            active_connection.execute(
                insert(audit_events).values(
                    trace_id=record["trace_id"],
                    status=record["status"],
                    question=record["question"],
                    conversation_id=record["conversation_id"],
                    query_plan=json.dumps(record.get("query_plan"), ensure_ascii=False)
                    if record.get("query_plan") is not None
                    else None,
                    response_type=record.get("response_type"),
                    error_code=record.get("error_code"),
                    result_summary=json.dumps(record.get("result_summary"), ensure_ascii=False)
                    if record.get("result_summary") is not None
                    else None,
                )
            )

        if connection is None:
            with self.engine.begin() as owned_connection:
                _persist(owned_connection)
        else:
            _persist(connection)

        return record
