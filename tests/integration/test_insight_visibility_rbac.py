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
