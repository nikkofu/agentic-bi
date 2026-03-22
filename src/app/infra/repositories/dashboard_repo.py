import json
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import insert
from sqlalchemy import select

from app.infra.db import get_engine

metadata = MetaData()

dashboards = Table(
    "dashboards",
    metadata,
    Column("dashboard_id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("principal_id", String, nullable=False),
    Column("title", String, nullable=False),
    Column("report_intent_id", String, nullable=False),
    Column("current_revision_id", String, nullable=False),
    Column("published_revision_id", String, nullable=False),
)

dashboard_revisions = Table(
    "dashboard_revisions",
    metadata,
    Column("revision_id", String, primary_key=True),
    Column("dashboard_id", String, nullable=False),
    Column("spec_json", Text, nullable=False),
)


class DashboardRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        report_intent_id: str,
        dashboard: dict,
        dashboard_id: str | None = None,
    ) -> dict:
        resolved_dashboard_id = dashboard_id if dashboard_id is not None else f"dash-{uuid4().hex[:12]}"
        revision_id = f"rev-{uuid4().hex[:12]}"
        persisted_dashboard = dict(dashboard)
        persisted_dashboard["id"] = resolved_dashboard_id

        with self.engine.begin() as connection:
            connection.execute(
                insert(dashboard_revisions).values(
                    revision_id=revision_id,
                    dashboard_id=resolved_dashboard_id,
                    spec_json=json.dumps(persisted_dashboard, ensure_ascii=False),
                )
            )
            connection.execute(
                insert(dashboards).values(
                    dashboard_id=resolved_dashboard_id,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    title=persisted_dashboard.get("title", "Untitled Dashboard"),
                    report_intent_id=report_intent_id,
                    current_revision_id=revision_id,
                    published_revision_id=revision_id,
                )
            )

        return {
            "dashboard_id": resolved_dashboard_id,
            "report_intent_id": report_intent_id,
            "current_revision_id": revision_id,
            "published_revision_id": revision_id,
            "dashboard": persisted_dashboard,
        }

    def get_for_owner(self, *, dashboard_id: str, tenant_id: str, principal_id: str) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(
                select(
                    dashboards.c.dashboard_id,
                    dashboards.c.report_intent_id,
                    dashboards.c.current_revision_id,
                    dashboards.c.published_revision_id,
                    dashboard_revisions.c.spec_json,
                ).where(
                    dashboards.c.dashboard_id == dashboard_id,
                    dashboards.c.tenant_id == tenant_id,
                    dashboards.c.principal_id == principal_id,
                    dashboard_revisions.c.revision_id == dashboards.c.current_revision_id,
                )
            ).fetchone()

        if row is None:
            raise KeyError(dashboard_id)

        return {
            "dashboard_id": row.dashboard_id,
            "report_intent_id": row.report_intent_id,
            "current_revision_id": row.current_revision_id,
            "published_revision_id": row.published_revision_id,
            "dashboard": json.loads(row.spec_json),
        }
