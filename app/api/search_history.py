from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, SearchHistory

router = APIRouter(prefix="/search-history", tags=["search"])


@router.post("/")
async def add_search_history(
    keyword: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """添加搜索历史"""
    if not keyword or len(keyword.strip()) == 0:
        return {"message": "Keyword required"}
    
    # Add to history
    history = SearchHistory(user_id=current_user.id, keyword=keyword.strip())
    session.add(history)
    
    # Keep only last 20 searches
    result = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
    )
    all_history = result.scalars().all()
    
    if len(all_history) > 20:
        for old in all_history[20:]:
            await session.delete(old)
    
    await session.commit()
    
    return {"message": "Search saved"}


@router.get("/")
async def get_search_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取搜索历史"""
    result = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    
    return [h.keyword for h in history]


@router.delete("/")
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """清空搜索历史"""
    result = await session.execute(
        select(SearchHistory).where(SearchHistory.user_id == current_user.id)
    )
    history = result.scalars().all()
    
    for h in history:
        await session.delete(h)
    
    await session.commit()
    return {"message": "Search history cleared"}
