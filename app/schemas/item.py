from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union
import json
from datetime import datetime
from app.core.constants import ItemCategory, MAX_ITEM_IMAGES


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    price: float = Field(..., gt=0)
    category: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v not in ItemCategory.choices():
            raise ValueError(f'Category must be one of: {ItemCategory.choices()}')
        return v


class ItemCreate(ItemBase):
    images: List[str] = Field(default_factory=list, max_length=MAX_ITEM_IMAGES)


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    status: Optional[int] = Field(None, ge=0, le=2)


class ItemResponse(ItemBase):
    id: int
    images: List[str] = []
    status: int
    seller_id: int
    view_count: int
    created_at: datetime
    updated_at: datetime

    @field_validator('images', mode='before')
    @classmethod
    def parse_images(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v or []

    class Config:
        from_attributes = True


class ItemSearchRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = Field(default=5.0, ge=0.1, le=50)
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    keyword: Optional[str] = None
    sort_by: str = Field(default="created_at")  # created_at or price
    sort_order: str = Field(default="desc")  # asc or desc
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CategoryListResponse(BaseModel):
    categories: List[str]
