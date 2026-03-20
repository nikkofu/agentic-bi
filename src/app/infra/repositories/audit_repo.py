from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import insert

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
)


class AuditRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save(self, record: dict) -> dict:
        with self.engine.begin() as connection:
            connection.execute(
                insert(audit_events).values(
                    trace_id=record["trace_id"],
                    status=record["status"],
                    question=record["question"],
                    conversation_id=record["conversation_id"],
                )
            )
        return record
