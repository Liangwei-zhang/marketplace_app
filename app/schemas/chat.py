from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatRoomCreate(BaseModel):
    item_id: int


class ChatRoomResponse(BaseModel):
    id: int
    item_id: int
    buyer_id: int
    seller_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    room_id: int
    content: str
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: str
    message_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRoomDetail(ChatRoomResponse):
    item_title: Optional[str] = None
    item_price: Optional[float] = None
    item_image: Optional[str] = None
    other_user_name: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
