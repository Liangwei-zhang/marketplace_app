from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, Favorite

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/{item_id}", status_code=201)
async def add_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """收藏商品"""
    # Check item exists
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if already favorited
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == current_user.id,
                Favorite.item_id == item_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")
    
    # Create favorite
    favorite = Favorite(user_id=current_user.id, item_id=item_id)
    session.add(favorite)
    await session.commit()
    
    return {"message": "Item favorited"}


@router.delete("/{item_id}")
async def remove_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """取消收藏"""
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == current_user.id,
                Favorite.item_id == item_id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    await session.delete(favorite)
    await session.commit()
    
    return {"message": "Favorite removed"}


@router.get("/")
async def my_favorites(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """我的收藏列表"""
    result = await session.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    favorites = result.scalars().all()
    
    # Get item details
    items = []
    for fav in favorites:
        result = await session.execute(select(Item).where(Item.id == fav.item_id))
        item = result.scalar_one_or_none()
        if item:
            items.append(item)
    
    return items


@router.get("/check/{item_id}")
async def check_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """检查是否已收藏"""
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == current_user.id,
                Favorite.item_id == item_id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    return {"is_favorited": favorite is not None}
