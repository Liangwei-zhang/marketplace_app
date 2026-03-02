from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class BrowseHistory(SQLModel, table=True):
    """浏览历史"""
    __tablename__ = "browse_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    item_id: int = Field(foreign_key="items.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
