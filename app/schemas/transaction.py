from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransactionBase(BaseModel):
    item_id: int
    agreed_price: float
    note: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    buyer_id: int
    seller_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionWithItem(TransactionResponse):
    """交易详情，包含商品信息"""
    item_title: Optional[str] = None
    item_image: Optional[str] = None
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
