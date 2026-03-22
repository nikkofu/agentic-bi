import json

from sqlalchemy.engine import Connection
from sqlalchemy import Column
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import insert
from sqlalchemy import select

from app.infra.db import get_engine

metadata = MetaData()

report_intents = Table(
    "report_intents",
    metadata,
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("principal_id", String, nullable=False),
    Column("trace_id", String, nullable=False),
    Column("payload", Text, nullable=False),
)


class ReportIntentRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save(self, intent, connection: Connection | None = None) -> dict:
        payload = intent.model_dump(mode="python") if hasattr(intent, "model_dump") else dict(intent)
        if connection is None:
            with self.engine.begin() as owned_connection:
                owned_connection.execute(
                    insert(report_intents).values(
                        id=payload["id"],
                        tenant_id=payload["tenant_id"],
                        principal_id=payload["permission_context"]["principal_id"],
                        trace_id=payload.get("trace", {}).get("trace_id", ""),
                        payload=json.dumps(payload, ensure_ascii=False),
                    )
                )
        else:
            connection.execute(
                insert(report_intents).values(
                    id=payload["id"],
                    tenant_id=payload["tenant_id"],
                    principal_id=payload["permission_context"]["principal_id"],
                    trace_id=payload.get("trace", {}).get("trace_id", ""),
                    payload=json.dumps(payload, ensure_ascii=False),
                )
            )
        return payload

    def get(self, intent_id: str) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(
                select(report_intents.c.payload).where(report_intents.c.id == intent_id)
            ).fetchone()

        if row is None:
            raise KeyError(intent_id)

        return json.loads(row[0])

    def get_for_owner(self, *, intent_id: str, tenant_id: str, principal_id: str) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(
                select(report_intents.c.payload).where(
                    report_intents.c.id == intent_id,
                    report_intents.c.tenant_id == tenant_id,
                    report_intents.c.principal_id == principal_id,
                )
            ).fetchone()

        if row is None:
            raise KeyError(intent_id)

        return json.loads(row[0])
