from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import os
import json

from app.core.database import get_async_session
from app.core.config import settings
from app.api.auth import get_current_user
from app.models import User, Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse, ItemSearchRequest
from app.services import image_service

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new item."""
    item = Item(
        title=item_data.title,
        description=item_data.description,
        price=item_data.price,
        category=item_data.category,
        latitude=item_data.latitude,
        longitude=item_data.longitude,
        address=item_data.address,
        images=json.dumps(item_data.images),
        seller_id=current_user.id
    )
    
    session.add(item)
    await session.commit()
    await session.refresh(item)
    
    return item


@router.post("/upload", response_model=List[str])
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload item images with compression."""
    filenames = await image_service.save_uploads(files, current_user.id)
    return [image_service.get_image_url(f) for f in filenames]


@router.get("/", response_model=List[ItemResponse])
async def list_items(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """List all items (no location filter)."""
    query = select(Item).where(Item.status == 0).order_by(Item.created_at.desc())
    
    if category:
        query = query.where(Item.category == category)
    
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    return items


@router.post("/search", response_model=List[ItemResponse])
async def search_items_nearby(
    search: ItemSearchRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Search items by location (LBS) with filters."""
    # PostgreSQL: calculate distance using Haversine formula
    # ST_DistanceSphere is more accurate for earth
    query = text("""
        SELECT *,
        (6371 * acos(
            cos(radians(:lat)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(:lng)) +
            sin(radians(:lat)) * sin(radians(latitude))
        )) AS distance
        FROM items
        WHERE status = 0
        AND (6371 * acos(
            cos(radians(:lat)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(:lng)) +
            sin(radians(:lat)) * sin(radians(latitude))
        )) <= :radius
    """)
    
    params = {
        "lat": search.latitude,
        "lng": search.longitude,
        "radius": search.radius_km
    }
    
    if search.category:
        query = text(str(query).replace("WHERE status = 0", "WHERE status = 0 AND category = :category"))
        params["category"] = search.category
    
    if search.min_price is not None:
        query = text(str(query).replace("WHERE status = 0", "WHERE status = 0 AND price >= :min_price"))
        params["min_price"] = search.min_price
    
    if search.max_price is not None:
        query = text(str(query).replace("WHERE status = 0", "WHERE status = 0 AND price <= :max_price"))
        params["max_price"] = search.max_price
    
    if search.keyword:
        query = text(str(query).replace("WHERE status = 0", 
            "WHERE status = 0 AND (title ILIKE :keyword OR description ILIKE :keyword)"))
        params["keyword"] = f"%{search.keyword}%"
    
    query = text(str(query) + " ORDER BY distance LIMIT :limit OFFSET :offset")
    params["limit"] = search.limit
    params["offset"] = search.offset
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    # Get item IDs and fetch full objects
    item_ids = [row[0] for row in rows]
    if not item_ids:
        return []
    
    items_query = select(Item).where(Item.id.in_(item_ids))
    items_result = await session.execute(items_query)
    items = items_result.scalars().all()
    
    # Sort by distance
    items_dict = {item.id: item for item in items}
    sorted_items = [items_dict[id] for id in item_ids if id in items_dict]
    
    return sorted_items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get item by ID."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Increment view count
    item.view_count += 1
    await session.commit()
    
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update item."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if item_data.title is not None:
        item.title = item_data.title
    if item_data.description is not None:
        item.description = item_data.description
    if item_data.price is not None:
        item.price = item_data.price
    if item_data.category is not None:
        item.category = item_data.category
    if item_data.status is not None:
        item.status = item_data.status
    
    await session.commit()
    await session.refresh(item)
    
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete item."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await session.delete(item)
    await session.commit()
    
    return None


# Serve uploaded files
@router.get("/uploads/{filename}")
async def serve_image(filename: str):
    """Serve uploaded images."""
    path = os.path.join(settings.UPLOAD_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Image not found")
