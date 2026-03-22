from app.api.reporting import build_permission_context
from app.infra.repositories.audit_repo import AuditRepository
from app.infra.repositories.diagnostic_report_repo import DiagnosticReportRepository
from app.infra.repositories.insight_repo import InsightRepository
from app.services.access_policy import resolve_allowed_regions
from app.services.audit_log import append_audit_event
from app.services.audit_log import new_trace_id
from app.services.diagnostic_dashboard_assembler import assemble_diagnostic_dashboard
from app.services.diagnostic_report_builder import build_diagnostic_report
from app.services.diagnostic_snapshot_store import DiagnosticSnapshotRepositories
from app.services.diagnostic_snapshot_store import prepare_diagnostic_snapshot_repositories
from app.services.diagnostic_snapshot_store import persist_diagnostic_snapshot
from app.services.insight_attribution import compute_single_layer_attribution
from app.services.insight_cards import build_insight_card
from app.services.insight_rules import evaluate_anomaly
from app.services.report_intent_builder import build_report_intent

DEFAULT_REPORT_SNAPSHOT_CREATE_FAILED = "DEFAULT_REPORT_SNAPSHOT_CREATE_FAILED"


def _build_monitor_permission_context(*, tenant_id: str, principal_id: str) -> dict:
    return build_permission_context(
        principal_id=principal_id,
        role_scope=[f"region:{region}" for region in resolve_allowed_regions(user_id=principal_id, tenant_id=tenant_id)],
        row_level_policy_ref=f"sales-region:{principal_id}",
    )


def _append_monitor_report_audit_event(
    *,
    trace_id: str,
    status: str,
    tenant_id: str,
    principal_id: str,
    question: str,
    error_code: str | None = None,
    result_summary: dict | None = None,
    audit_repo: AuditRepository | None = None,
    connection=None,
) -> None:
    permission_context = _build_monitor_permission_context(tenant_id=tenant_id, principal_id=principal_id)
    summary = dict(result_summary or {})
    summary["permission_context"] = {
        "principal_id": permission_context["principal_id"],
        "role_scope": permission_context["role_scope"],
        "row_level_policy_ref": permission_context["row_level_policy_ref"],
    }
    append_audit_event(
        {
            "trace_id": trace_id,
            "status": status,
            "question": question,
            "conversation_id": "",
            "error_code": error_code,
            "result_summary": summary,
        },
        audit_repo=audit_repo,
        connection=connection,
    )


def _build_monitor_report_intent(*, tenant_id: str, principal_id: str, card: dict, event) -> object:
    permission_context = _build_monitor_permission_context(tenant_id=tenant_id, principal_id=principal_id)
    return build_report_intent(
        question=card["suggested_next_question"],
        tenant_id=tenant_id,
        dataset_id="sales-fixture",
        trace_id=card["trace_id"],
        permission_context=permission_context,
        plan={
            "metric": event.metric,
            "filters": event.scope,
            "time_window": "last_month",
            "group_by": ["month"],
        },
        result={"metric": event.metric, "time_window": "last_month"},
    )


def _create_default_report_snapshot(
    *,
    tenant_id: str,
    principal_id: str,
    card: dict,
    event,
    attribution: dict,
    repositories: DiagnosticSnapshotRepositories | None = None,
    connection=None,
) -> dict:
    trace_id = card["trace_id"]
    dashboard_id = f"dash-{trace_id}"
    report_intent = _build_monitor_report_intent(
        tenant_id=tenant_id,
        principal_id=principal_id,
        card=card,
        event=event,
    )
    report = build_diagnostic_report(
        tenant_id=tenant_id,
        principal_id=principal_id,
        source_kind="insight_card",
        source_ref=card["card_id"],
        report_intent=report_intent,
        metric_result={"metric": card["metric"], "time_window": "last_month"},
        finding_inputs=[
            {
                "kind": "trend",
                "title": "异常延续",
                "statement": card["summary"],
                "evidence_refs": [trace_id],
            }
        ],
        recommendations=[
            {
                "kind": "question",
                "label": "继续诊断",
                "question": card["suggested_next_question"],
                "rationale": "从洞察卡片继续分析",
            }
        ],
        dashboard_id=dashboard_id,
    )
    dashboard = assemble_diagnostic_dashboard(
        report=report,
        result_bindings={
            "overview": {
                "value": event.current_value,
                "rows": [{"region": card["scope"]["region"], "value": event.current_value}],
            },
            "drivers": {"rows": [{"region": attribution["key"], "value": attribution["contribution"]}]},
        },
    )
    return persist_diagnostic_snapshot(
        tenant_id=tenant_id,
        principal_id=principal_id,
        report_intent=report_intent,
        dashboard=dashboard,
        report=report,
        repositories=repositories,
        connection=connection,
    )


def run_monitor_once(*, snapshots: list[dict], abs_thresholds: dict, delta_thresholds: dict) -> int:
    repo = InsightRepository()
    report_repo = DiagnosticReportRepository()
    audit_repo = AuditRepository()
    generated = 0

    for snap in snapshots:
        metric = snap["metric"]
        event = evaluate_anomaly(
            metric=metric,
            current_value=snap["current_value"],
            baseline_value=snap["baseline_value"],
            abs_threshold=abs_thresholds.get(metric),
            delta_threshold=delta_thresholds.get(metric, 0.0),
            scope=snap["scope"],
        )
        if event is None:
            continue

        attribution = compute_single_layer_attribution(
            [{"region": snap["scope"].get("region", "全域"), "value": event.delta}],
            dimension="region",
        )
        card_payload = build_insight_card(event=event, attribution=attribution, trace_id=new_trace_id())
        card = repo.save_card(card_payload)
        snapshot_repositories = prepare_diagnostic_snapshot_repositories()

        try:
            report_snapshot = report_repo.get_or_create_default_for_insight(
                tenant_id="t-1",
                principal_id="u-1",
                source_ref=card["card_id"],
                create_fn=lambda connection: _create_default_report_snapshot(
                    tenant_id="t-1",
                    principal_id="u-1",
                    card=card,
                    event=event,
                    attribution=attribution,
                    repositories=snapshot_repositories,
                    connection=connection,
                ),
            )
        except Exception:
            _append_monitor_report_audit_event(
                trace_id=card["trace_id"],
                status="DIAGNOSTIC_REPORT_GENERATE_FAILED",
                tenant_id="t-1",
                principal_id="u-1",
                question=card["suggested_next_question"],
                error_code=DEFAULT_REPORT_SNAPSHOT_CREATE_FAILED,
                result_summary={"card_id": card["card_id"]},
                audit_repo=audit_repo,
            )
            generated += 1
            continue

        repo.attach_report(
            card_id=card["card_id"],
            report_id=report_snapshot["id"],
            dashboard_id=report_snapshot["dashboard_id"],
        )
        _append_monitor_report_audit_event(
            trace_id=card["trace_id"],
            status="DIAGNOSTIC_REPORT_GENERATED",
            tenant_id="t-1",
            principal_id="u-1",
            question=card["suggested_next_question"],
            result_summary={
                "card_id": card["card_id"],
                "report_id": report_snapshot["id"],
                "dashboard_id": report_snapshot["dashboard_id"],
            },
            audit_repo=audit_repo,
        )
        generated += 1

    return generated
