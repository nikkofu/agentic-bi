import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.services.insight_monitor import run_monitor_once

client = TestClient(app)


def test_insight_list_only_returns_in_scope_cards(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-rbac.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30},
            {"metric": "gross_margin_rate", "scope": {"region": "华南"}, "current_value": 0.23, "baseline_value": 0.30},
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    resp = client.get("/v1/insights/cards", params={"user_id": "u-south", "tenant_id": "t-1"})
    assert resp.status_code == 200
    body = resp.json()
    assert all(card["scope"]["region"] == "华南" for card in body["items"])

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM insight_cards").fetchone()
    assert rows[0] == 2


def test_insight_list_only_returns_in_scope_cards_and_exposes_report_links(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-rbac-report-links.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30},
            {"metric": "gross_margin_rate", "scope": {"region": "华南"}, "current_value": 0.23, "baseline_value": 0.30},
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    body = client.get("/v1/insights/cards", params={"user_id": "u-south", "tenant_id": "t-1"}).json()
    assert all(card["scope"]["region"] == "华南" for card in body["items"])
    assert all(card["card_id"].startswith("card-") for card in body["items"])
    assert all(card["detail_url"] == f"/reports/{card['report_id']}" for card in body["items"])


def test_insight_list_returns_no_cards_for_unknown_user_scope(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-rbac-unknown-scope.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华东"}, "current_value": 0.24, "baseline_value": 0.30},
            {"metric": "gross_margin_rate", "scope": {"region": "华南"}, "current_value": 0.23, "baseline_value": 0.30},
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    resp = client.get("/v1/insights/cards", params={"user_id": "u-unknown", "tenant_id": "t-1"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_insight_list_creates_distinct_reports_for_multiple_uncached_cards(tmp_path, monkeypatch):
    db_path = tmp_path / "insight-rbac-multiple-uncached.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    run_monitor_once(
        snapshots=[
            {"metric": "gross_margin_rate", "scope": {"region": "华南"}, "current_value": 0.23, "baseline_value": 0.30},
            {"metric": "gross_margin_rate", "scope": {"region": "华南"}, "current_value": 0.22, "baseline_value": 0.30},
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    resp = client.get("/v1/insights/cards", params={"user_id": "u-south", "tenant_id": "t-1"})
    assert resp.status_code == 200

    items = resp.json()["items"]
    assert len(items) == 2
    assert all(item["scope"]["region"] == "华南" for item in items)

    report_ids = {item["report_id"] for item in items}
    dashboard_ids = {item["dashboard_id"] for item in items}
    assert len(report_ids) == 2
    assert len(dashboard_ids) == 2
    assert all(item["detail_url"] == f"/reports/{item['report_id']}" for item in items)
