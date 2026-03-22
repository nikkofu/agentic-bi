from dataclasses import dataclass

from sqlalchemy.engine import Connection

from app.infra.repositories.dashboard_repo import DashboardRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.report_intent_repo import ReportIntentRepository


@dataclass(frozen=True)
class DiagnosticSnapshotRepositories:
    intent_repo: ReportIntentRepository
    dashboard_repo: DashboardRepository
    report_repo: DiagnosticReportRepository


def prepare_diagnostic_snapshot_repositories() -> DiagnosticSnapshotRepositories:
    return DiagnosticSnapshotRepositories(
        intent_repo=ReportIntentRepository(),
        dashboard_repo=DashboardRepository(),
        report_repo=DiagnosticReportRepository(),
    )


def persist_diagnostic_snapshot(
    *,
    tenant_id: str,
    principal_id: str,
    report_intent,
    dashboard,
    report,
    repositories: DiagnosticSnapshotRepositories | None = None,
    connection: Connection | None = None,
) -> dict:
    active_repositories = repositories or prepare_diagnostic_snapshot_repositories()
    dashboard_payload = dashboard.model_dump(mode="python") if hasattr(dashboard, "model_dump") else dict(dashboard)
    report_payload = report.model_dump(mode="python") if hasattr(report, "model_dump") else dict(report)

    def _persist(active_connection: Connection) -> dict:
        active_repositories.intent_repo.save(report_intent, connection=active_connection)
        active_repositories.dashboard_repo.save(
            tenant_id=tenant_id,
            principal_id=principal_id,
            report_intent_id=report_payload["report_intent_id"],
            dashboard=dashboard_payload,
            dashboard_id=dashboard_payload["id"],
            connection=active_connection,
        )
        return active_repositories.report_repo.save(report=report_payload, connection=active_connection)

    if connection is not None:
        return _persist(connection)

    with active_repositories.report_repo.engine.begin() as owned_connection:
        return _persist(owned_connection)
