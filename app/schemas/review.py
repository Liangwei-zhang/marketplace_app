from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewBase(BaseModel):
    transaction_id: int
    rating: int = Field(..., ge=1, le=5)
    content: Optional[str] = Field(None, max_length=500)


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    id: int
    reviewer_id: int
    reviewed_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewWithUser(ReviewResponse):
    """评价详情，包含评价人信息"""
    reviewer_name: Optional[str] = None
    reviewer_avatar: Optional[str] = None
