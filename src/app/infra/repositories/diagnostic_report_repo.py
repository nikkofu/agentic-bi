import json
from collections.abc import Callable
from datetime import datetime
from datetime import timezone

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

diagnostic_reports = Table(
    "diagnostic_reports",
    metadata,
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("principal_id", String, nullable=False),
    Column("source_kind", String, nullable=False),
    Column("source_ref", String, nullable=False),
    Column("snapshot_time", String, nullable=False),
    Column("status", String, nullable=False),
    Column("dashboard_id", String, nullable=False),
    Column("report_intent_id", String, nullable=False),
    Column("payload", Text, nullable=False),
)


class DiagnosticReportRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save(self, report, connection: Connection | None = None) -> dict:
        payload = report.model_dump(mode="python") if hasattr(report, "model_dump") else dict(report)
        if connection is None:
            with self.engine.begin() as owned_connection:
                owned_connection.execute(
                    insert(diagnostic_reports).values(
                        id=payload["id"],
                        tenant_id=payload["tenant_id"],
                        principal_id=payload["principal_id"],
                        source_kind=payload["source_kind"],
                        source_ref=payload["source_ref"],
                        snapshot_time=payload["snapshot_time"],
                        status=payload["status"],
                        dashboard_id=payload["dashboard_id"],
                        report_intent_id=payload["report_intent_id"],
                        payload=json.dumps(payload, ensure_ascii=False),
                    )
                )
        else:
            connection.execute(
                insert(diagnostic_reports).values(
                    id=payload["id"],
                    tenant_id=payload["tenant_id"],
                    principal_id=payload["principal_id"],
                    source_kind=payload["source_kind"],
                    source_ref=payload["source_ref"],
                    snapshot_time=payload["snapshot_time"],
                    status=payload["status"],
                    dashboard_id=payload["dashboard_id"],
                    report_intent_id=payload["report_intent_id"],
                    payload=json.dumps(payload, ensure_ascii=False),
                )
            )
        return payload

    def get_for_owner(self, report_id: str, tenant_id: str, principal_id: str) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(
                select(diagnostic_reports.c.payload).where(
                    diagnostic_reports.c.id == report_id,
                    diagnostic_reports.c.tenant_id == tenant_id,
                    diagnostic_reports.c.principal_id == principal_id,
                )
            ).fetchone()

        if row is None:
            raise KeyError(report_id)

        return json.loads(row[0])

    def get_by_source_ref(
        self,
        tenant_id: str,
        principal_id: str,
        source_kind: str,
        source_ref: str,
        connection: Connection | None = None,
    ) -> dict | None:
        if connection is None:
            with self.engine.begin() as owned_connection:
                rows = owned_connection.execute(
                    select(diagnostic_reports.c.payload).where(
                        diagnostic_reports.c.tenant_id == tenant_id,
                        diagnostic_reports.c.principal_id == principal_id,
                        diagnostic_reports.c.source_kind == source_kind,
                        diagnostic_reports.c.source_ref == source_ref,
                    )
                ).fetchall()
        else:
            rows = connection.execute(
                select(diagnostic_reports.c.payload).where(
                    diagnostic_reports.c.tenant_id == tenant_id,
                    diagnostic_reports.c.principal_id == principal_id,
                    diagnostic_reports.c.source_kind == source_kind,
                    diagnostic_reports.c.source_ref == source_ref,
                )
            ).fetchall()

        if not rows:
            return None

        payloads = [json.loads(row[0]) for row in rows]
        return max(payloads, key=self._snapshot_time_sort_key)

    def get_or_create_default_for_insight(
        self,
        tenant_id: str,
        principal_id: str,
        source_ref: str,
        create_fn: Callable[[Connection], dict],
    ) -> dict:
        source_kind = "insight_card"
        with self.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                existing = self.get_by_source_ref(
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    source_kind=source_kind,
                    source_ref=source_ref,
                    connection=connection,
                )
                if existing is not None:
                    connection.commit()
                    return existing

                created = create_fn(connection)
                connection.commit()
                return created
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _snapshot_time_sort_key(report: dict) -> datetime:
        raw_value = str(report["snapshot_time"]).strip()
        normalized = raw_value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
