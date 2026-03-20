from pydantic import BaseModel


class QueryResponse(BaseModel):
    answer: str
    chart: dict
    trace_id: str
