from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class PushSubscription(SQLModel, table=True):
    """用户推送订阅"""
    __tablename__ = "push_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    endpoint: str
    keys: str  # JSON: { "p256dh": ..., "auth": ... }
    created_at: datetime = Field(default_factory=datetime.utcnow)
