from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User


class Favorite(SQLModel, table=True):
    """用户收藏"""
    __tablename__ = "favorites"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    item_id: int = Field(foreign_key="items.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
