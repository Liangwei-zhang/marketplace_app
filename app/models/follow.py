from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Follow(SQLModel, table=True):
    """用户关注"""
    __tablename__ = "follows"

    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="users.id")  # 关注者
    following_id: int = Field(foreign_key="users.id")  # 被关注者
    created_at: datetime = Field(default_factory=datetime.utcnow)
