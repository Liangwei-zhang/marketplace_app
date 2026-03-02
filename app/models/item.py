from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chat import ChatRoom


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str
    price: float = Field(index=True)
    category: str = Field(index=True)
    
    # Location
    latitude: float
    longitude: float
    address: Optional[str] = None
    
    # Images
    images: str = Field(default="[]")  # JSON array of URLs
    
    # Status: 0=在售, 1=交易中, 2=已完成
    status: int = Field(default=0)
    
    # Foreign keys
    seller_id: int = Field(foreign_key="users.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Views counter
    view_count: int = Field(default=0)

    # Relationships
    seller: "User" = Relationship(back_populates="items")
    chat_rooms: List["ChatRoom"] = Relationship(back_populates="item")
