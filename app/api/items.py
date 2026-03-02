from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlmodel import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import os
import json

from app.core.database import get_async_session
from app.core.config import settings
from app.core.constants import ItemCategory, MAX_ITEM_IMAGES, ALLOWED_IMAGE_EXTENSIONS
from app.api.auth import get_current_user
from app.models import User, Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse, ItemSearchRequest, CategoryListResponse
from app.services import image_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories():
    """Get all available categories."""
    return CategoryListResponse(categories=ItemCategory.choices())


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new item."""
    # Validate image count
    if len(item_data.images) > MAX_ITEM_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_ITEM_IMAGES} images allowed"
        )
    
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
    # Check max files
    if len(files) > MAX_ITEM_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_ITEM_IMAGES} images allowed"
        )
    
    # Validate file extensions
    for f in files:
        ext = f.filename.split(".")[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )
    
    filenames = await image_service.save_uploads(files, current_user.id)
    return [image_service.get_image_url(f) for f in filenames]


@router.get("/", response_model=List[ItemResponse])
async def list_items(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """List all items (no location filter) - sorted by newest first."""
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
    """Search items by location using PostGIS.
    
    Uses ST_DWithin with geography for efficient spatial queries.
    If no results found in initial radius, automatically expands:
    5km → 10km → 20km → unlimited
    """
    # Try with increasing radius until we find results
    radii_to_try = [search.radius_km, 10, 20, 100]  # 100 means unlimited
    seen_ids = set()
    
    for radius in radii_to_try:
        if radius == 100:
            # Unlimited search - use basic query
            base_query = """
                SELECT id FROM items
                WHERE status = 0
            """
            params = {}
        else:
            # PostGIS spatial query using ST_DWithin with lat/lng
            # Uses functional index for performance
            base_query = """
                SELECT id FROM items
                WHERE status = 0
                AND ST_DWithin(
                    ST_MakePoint(longitude, latitude)::geography,
                    ST_MakePoint(:lng, :lat)::geography,
                    :radius * 1000
                )
            """
            params = {
                "lat": search.latitude,
                "lng": search.longitude,
                "radius": radius
            }
        
        # Build where clause
        conditions = ["status = 0"]
        
        if search.category:
            conditions.append("category = :category")
            params["category"] = search.category
        
        if search.min_price is not None:
            conditions.append("price >= :min_price")
            params["min_price"] = search.min_price
        
        if search.max_price is not None:
            conditions.append("price <= :max_price")
            params["max_price"] = search.max_price
        
        if search.keyword:
            conditions.append("(title ILIKE :keyword OR description ILIKE :keyword)")
            params["keyword"] = f"%{search.keyword}%"
        
        where_clause = " AND ".join(conditions)
        
        # Sort by distance when using spatial query
        if radius < 100 and search.sort_by == "created_at":
            # Sort by distance for nearby searches
            sort_clause = f"""
                ORDER BY ST_Distance(
                    ST_MakePoint(longitude, latitude)::geography,
                    ST_MakePoint(:sort_lng, :sort_lat)::geography
                ) {"ASC" if search.sort_order == "asc" else "DESC"}
            """
            params["sort_lat"] = search.latitude
            params["sort_lng"] = search.longitude
        elif search.sort_by == "price":
            sort_clause = "ORDER BY price " + ("ASC" if search.sort_order == "asc" else "DESC")
        else:
            sort_clause = "ORDER BY created_at " + ("ASC" if search.sort_order == "asc" else "DESC")
        
        query_str = f"SELECT id FROM items WHERE {where_clause} {sort_clause} LIMIT :limit OFFSET :offset"
        params["limit"] = search.limit
        params["offset"] = search.offset
        
        result = await session.execute(text(query_str), params)
        rows = result.fetchall()
        
        # Get new IDs
        new_ids = [row[0] for row in rows if row[0] not in seen_ids]
        seen_ids.update(new_ids)
        
        if new_ids:
            break
    
    if not seen_ids:
        return []
    
    # Fetch full items
    items_query = select(Item).where(Item.id.in_(list(seen_ids)))
    result = await session.execute(items_query)
    items = list(result.scalars().all())
    
    # Sort according to search criteria
    if search.sort_by == "price":
        items.sort(
            key=lambda x: x.price,
            reverse=(search.sort_order == "desc")
        )
    else:
        items.sort(
            key=lambda x: x.created_at,
            reverse=(search.sort_order == "desc")
        )
    
    return items[:search.limit]


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
    if item_data.images is not None:
        item.images = json.dumps(item_data.images)
    
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
