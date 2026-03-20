import os

from sqlalchemy import create_engine

DEFAULT_DB_URL = "sqlite:///./agentic_bi.db"


def get_engine(db_url: str | None = None):
    resolved_db_url = db_url or os.getenv("AGENTIC_BI_DB_URL", DEFAULT_DB_URL)
    return create_engine(resolved_db_url)
