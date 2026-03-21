import json

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, insert, select

from app.infra.db import get_engine

metadata = MetaData()

insight_cards = Table(
    "insight_cards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", String, nullable=False),
    Column("metric", String, nullable=False),
    Column("scope", Text, nullable=False),
    Column("severity", String, nullable=False),
    Column("summary", Text, nullable=False),
    Column("attribution", Text, nullable=False),
    Column("suggested_next_question", Text, nullable=False),
)


class InsightRepository:
    def __init__(self, db_url: str | None = None):
        self.engine = get_engine(db_url)
        metadata.create_all(self.engine)

    def save_card(self, card: dict) -> dict:
        with self.engine.begin() as connection:
            connection.execute(
                insert(insight_cards).values(
                    trace_id=card["trace_id"],
                    metric=card["metric"],
                    scope=json.dumps(card["scope"], ensure_ascii=False),
                    severity=card["severity"],
                    summary=card["summary"],
                    attribution=json.dumps(card["attribution"], ensure_ascii=False),
                    suggested_next_question=card["suggested_next_question"],
                )
            )
        return card

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
                    "trace_id": row["trace_id"],
                    "metric": row["metric"],
                    "scope": scope,
                    "severity": row["severity"],
                    "summary": row["summary"],
                    "attribution": json.loads(row["attribution"]),
                    "suggested_next_question": row["suggested_next_question"],
                }
            )
        return cards
