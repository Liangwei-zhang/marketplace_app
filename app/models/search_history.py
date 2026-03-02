from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class SearchHistory(SQLModel, table=True):
    """搜索历史"""
    __tablename__ = "search_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    keyword: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
