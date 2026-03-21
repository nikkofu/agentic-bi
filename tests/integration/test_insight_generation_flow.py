import sqlite3

from app.services.insight_monitor import run_monitor_once


def test_monitor_generates_and_persists_insight_card(tmp_path, monkeypatch):
    db_path = tmp_path / "insights.db"
    monkeypatch.setenv("AGENTIC_BI_DB_URL", f"sqlite:///{db_path}")

    count = run_monitor_once(
        snapshots=[
            {
                "metric": "gross_margin_rate",
                "scope": {"region": "华东"},
                "current_value": 0.24,
                "baseline_value": 0.30,
            }
        ],
        abs_thresholds={"gross_margin_rate": 0.26},
        delta_thresholds={"gross_margin_rate": 0.04},
    )

    assert count == 1

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT metric, severity, summary, suggested_next_question
            FROM insight_cards
            """
        ).fetchall()

    assert len(rows) == 1
    metric, severity, summary, next_question = rows[0]
    assert metric == "gross_margin_rate"
    assert severity in {"P1", "P2", "P3"}
    assert summary
    assert next_question
