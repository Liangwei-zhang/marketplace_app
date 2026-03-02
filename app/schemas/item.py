from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ItemBase(BaseModel):
    title: str
    description: str
    price: float
    category: str
    latitude: float
    longitude: float
    address: Optional[str] = None


class ItemCreate(ItemBase):
    images: List[str] = []


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    status: Optional[int] = None


class ItemResponse(ItemBase):
    id: int
    images: List[str] = []
    status: int
    seller_id: int
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemSearchRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = Field(default=5.0, ge=0.1, le=50)
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    keyword: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
