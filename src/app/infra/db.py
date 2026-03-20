from sqlalchemy import create_engine


def get_engine(db_url: str = "sqlite:///./agentic_bi.db"):
    return create_engine(db_url)
