import json
from uuid import uuid4

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, insert, select, update

from app.infra.db import get_engine

metadata = MetaData()

insight_cards = Table(
    "insight_cards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("card_id", String, nullable=False, unique=True),
    Column("trace_id", String, nullable=False),
    Column("metric", String, nullable=False),
    Column("scope", Text, nullable=False),
    Column("severity", String, nullable=False),
    Column("summary", Text, nullable=False),
    Column("attribution", Text, nullable=False),
    Column("suggested_next_question", Text, nullable=False),
    Column("report_id", String, nullable=True),
    Column("dashboard_id", String, nullable=True),
    Column("detail_url", String, nullable=True),
)


class InsightRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save_card(self, card: dict) -> dict:
        card_id = card.get("card_id") or self._fallback_card_id()
        report_id = card.get("report_id")
        dashboard_id = card.get("dashboard_id")
        detail_url = self._build_detail_url(report_id=report_id)

        with self.engine.begin() as connection:
            connection.execute(
                insert(insight_cards).values(
                    card_id=card_id,
                    trace_id=card["trace_id"],
                    metric=card["metric"],
                    scope=json.dumps(card["scope"], ensure_ascii=False),
                    severity=card["severity"],
                    summary=card["summary"],
                    attribution=json.dumps(card["attribution"], ensure_ascii=False),
                    suggested_next_question=card["suggested_next_question"],
                    report_id=report_id,
                    dashboard_id=dashboard_id,
                    detail_url=detail_url,
                )
            )
        return {
            "card_id": card_id,
            "trace_id": card["trace_id"],
            "metric": card["metric"],
            "scope": card["scope"],
            "severity": card["severity"],
            "summary": card["summary"],
            "attribution": card["attribution"],
            "suggested_next_question": card["suggested_next_question"],
            "report_id": report_id,
            "dashboard_id": dashboard_id,
            "detail_url": detail_url,
        }

    def list_by_regions(self, allowed_regions: list[str]) -> list[dict]:
        with self.engine.begin() as connection:
            rows = connection.execute(select(insight_cards)).mappings().all()

        cards = []
        for row in rows:
            scope = json.loads(row["scope"])
            if allowed_regions and scope.get("region") not in allowed_regions:
                continue
            cards.append(
                {
                    "card_id": row["card_id"],
                    "trace_id": row["trace_id"],
                    "metric": row["metric"],
                    "scope": scope,
                    "severity": row["severity"],
                    "summary": row["summary"],
                    "attribution": json.loads(row["attribution"]),
                    "suggested_next_question": row["suggested_next_question"],
                    "report_id": row["report_id"],
                    "dashboard_id": row["dashboard_id"],
                    "detail_url": row["detail_url"],
                }
            )
        return cards

    def get(self, card_id: str, allowed_regions: list[str]) -> dict:
        with self.engine.begin() as connection:
            row = connection.execute(select(insight_cards).where(insight_cards.c.card_id == card_id)).mappings().fetchone()

        if row is None:
            raise KeyError(card_id)

        scope = json.loads(row["scope"])
        if allowed_regions and scope.get("region") not in allowed_regions:
            raise KeyError(card_id)

        return {
            "card_id": row["card_id"],
            "trace_id": row["trace_id"],
            "metric": row["metric"],
            "scope": scope,
            "severity": row["severity"],
            "summary": row["summary"],
            "attribution": json.loads(row["attribution"]),
            "suggested_next_question": row["suggested_next_question"],
            "report_id": row["report_id"],
            "dashboard_id": row["dashboard_id"],
            "detail_url": row["detail_url"],
        }

    def attach_report(self, card_id: str, report_id: str, dashboard_id: str) -> None:
        detail_url = self._build_detail_url(report_id=report_id)
        with self.engine.begin() as connection:
            updated = connection.execute(
                update(insight_cards)
                .where(insight_cards.c.card_id == card_id)
                .values(report_id=report_id, dashboard_id=dashboard_id, detail_url=detail_url)
            )

        if updated.rowcount == 0:
            raise KeyError(card_id)

    @staticmethod
    def _fallback_card_id() -> str:
        return f"card-{uuid4().hex[:12]}"

    @staticmethod
    def _build_detail_url(*, report_id: str | None) -> str | None:
        if report_id:
            return f"/reports/{report_id}"
        return None
