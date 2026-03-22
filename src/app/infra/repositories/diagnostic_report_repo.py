import json
from collections.abc import Callable

from sqlalchemy import Column
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
    UniqueConstraint(
        "tenant_id",
        "principal_id",
        "source_kind",
        "source_ref",
        name="uq_diagnostic_reports_source_owner",
    ),
)


class DiagnosticReportRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save(self, report) -> dict:
        payload = report.model_dump(mode="python") if hasattr(report, "model_dump") else dict(report)
        with self.engine.begin() as connection:
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

    def get_by_source_ref(self, tenant_id: str, principal_id: str, source_kind: str, source_ref: str) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(
                select(diagnostic_reports.c.payload).where(
                    diagnostic_reports.c.tenant_id == tenant_id,
                    diagnostic_reports.c.principal_id == principal_id,
                    diagnostic_reports.c.source_kind == source_kind,
                    diagnostic_reports.c.source_ref == source_ref,
                )
            ).fetchone()

        if row is None:
            raise KeyError(source_ref)

        return json.loads(row[0])

    def get_or_create_default_for_insight(
        self,
        tenant_id: str,
        principal_id: str,
        source_ref: str,
        create_fn: Callable[[], dict],
    ) -> dict:
        source_kind = "insight_card"
        try:
            return self.get_by_source_ref(
                tenant_id=tenant_id,
                principal_id=principal_id,
                source_kind=source_kind,
                source_ref=source_ref,
            )
        except KeyError:
            pass

        payload = create_fn()
        payload = payload.model_dump(mode="python") if hasattr(payload, "model_dump") else dict(payload)
        payload["tenant_id"] = tenant_id
        payload["principal_id"] = principal_id
        payload["source_kind"] = source_kind
        payload["source_ref"] = source_ref

        try:
            return self.save(payload)
        except IntegrityError:
            return self.get_by_source_ref(
                tenant_id=tenant_id,
                principal_id=principal_id,
                source_kind=source_kind,
                source_ref=source_ref,
            )
