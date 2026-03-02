from fastapi import APIRouter, Depends
from sqlmodel import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, BrowseHistory

router = APIRouter(prefix="/history", tags=["history"])


@router.post("/{item_id}")
async def add_to_history(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """添加浏览历史"""
    # Check item exists
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        return {"message": "Item not found"}
    
    # Remove old entry if exists (avoid duplicates)
    result = await session.execute(
        select(BrowseHistory).where(
            and_(
                BrowseHistory.user_id == current_user.id,
                BrowseHistory.item_id == item_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update timestamp
        existing.created_at = datetime.utcnow()
        session.add(existing)
    else:
        # Add new entry
        history = BrowseHistory(user_id=current_user.id, item_id=item_id)
        session.add(history)
    
    await session.commit()
    
    # Keep only last 100 items
    result = await session.execute(
        select(BrowseHistory)
        .where(BrowseHistory.user_id == current_user.id)
        .order_by(BrowseHistory.created_at.desc())
    )
    all_history = result.scalars().all()
    
    if len(all_history) > 100:
        for old in all_history[100:]:
            await session.delete(old)
        await session.commit()
    
    return {"message": "Added to history"}


@router.get("/")
async def get_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取浏览历史"""
    result = await session.execute(
        select(BrowseHistory)
        .where(BrowseHistory.user_id == current_user.id)
        .order_by(BrowseHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    
    # Get item details
    items = []
    for h in history:
        result = await session.execute(select(Item).where(Item.id == h.item_id))
        item = result.scalar_one_or_none()
        if item:
            items.append(item)
    
    return items


@router.delete("/")
async def clear_history(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """清空浏览历史"""
    result = await session.execute(
        select(BrowseHistory).where(BrowseHistory.user_id == current_user.id)
    )
    history = result.scalars().all()
    
    for h in history:
        await session.delete(h)
    
    await session.commit()
    return {"message": "History cleared"}
