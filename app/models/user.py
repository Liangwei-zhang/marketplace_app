from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.chat import ChatRoom, Message


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Password reset
    reset_token: Optional[str] = Field(default=None, index=True)
    reset_token_expires: Optional[datetime] = Field(default=None)

    # Relationships
    items: List["Item"] = Relationship(back_populates="seller", sa_relationship_kwargs={"foreign_keys": "Item.seller_id"})
    chat_rooms: List["ChatRoom"] = Relationship(back_populates="buyer", sa_relationship_kwargs={"foreign_keys": "ChatRoom.buyer_id"})
    messages: List["Message"] = Relationship(back_populates="sender", sa_relationship_kwargs={"foreign_keys": "Message.sender_id"})
