from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid


class Query(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    raw_query: str
    status: str = "processing"
    llm_provider: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    intent: Optional[str] = None
    entities: Optional[str] = None
    intelligence: Optional[str] = None
    sources: Optional[str] = None
    error: Optional[str] = None
