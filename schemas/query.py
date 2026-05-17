from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    id: str
    status: str
    raw_query: str
    llm_provider: Optional[str]
    intent: Optional[str]
    entities: Optional[Any]
    intelligence: Optional[Any]
    sources: Optional[List[str]]
    created_at: datetime
    completed_at: Optional[datetime]
