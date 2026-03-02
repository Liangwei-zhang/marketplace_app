from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.item import Item


class ChatRoom(SQLModel, table=True):
    __tablename__ = "chat_rooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id")
    buyer_id: int = Field(foreign_key="users.id")
    seller_id: int = Field(foreign_key="users.id")
    transaction_id: Optional[int] = Field(default=None, foreign_key="transactions.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    item: "Item" = Relationship(back_populates="chat_rooms")
    buyer: "User" = Relationship(back_populates="chat_rooms", sa_relationship_kwargs={"foreign_keys": "ChatRoom.buyer_id"})


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="chat_rooms.id")
    sender_id: int = Field(foreign_key="users.id")
    content: str
    message_type: str = Field(default="text")  # text, image, voice
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sender: "User" = Relationship(back_populates="messages")
