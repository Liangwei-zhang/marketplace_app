from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, Transaction, Review, Report

router = APIRouter(prefix="/admin", tags=["admin"])


class DashboardStats(BaseModel):
    total_users: int
    total_items: int
    active_items: int
    sold_items: int
    total_transactions: int
    completed_transactions: int
    total_reviews: int
    pending_reports: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取后台统计数据"""
    # Check if admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count users
    result = await session.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0
    
    # Count items
    result = await session.execute(select(func.count(Item.id)))
    total_items = result.scalar() or 0
    
    # Count by status
    result = await session.execute(select(func.count(Item.id)).where(Item.status == 0))
    active_items = result.scalar() or 0
    
    result = await session.execute(select(func.count(Item.id)).where(Item.status == 2))
    sold_items = result.scalar() or 0
    
    # Count transactions
    result = await session.execute(select(func.count(Transaction.id)))
    total_transactions = result.scalar() or 0
    
    result = await session.execute(select(func.count(Transaction.id)).where(Transaction.status == "completed"))
    completed_transactions = result.scalar() or 0
    
    # Count reviews
    result = await session.execute(select(func.count(Review.id)))
    total_reviews = result.scalar() or 0
    
    # Count pending reports
    result = await session.execute(select(func.count(Report.id)).where(Report.status == "pending"))
    pending_reports = result.scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        total_items=total_items,
        active_items=active_items,
        sold_items=sold_items,
        total_transactions=total_transactions,
        completed_transactions=completed_transactions,
        total_reviews=total_reviews,
        pending_reports=pending_reports
    )


class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserListItem])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """列出用户（管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await session.execute(
        select(User).offset(offset).limit(limit)
    )
    users = result.scalars().all()
    
    return [UserListItem(
        id=u.id,
        username=u.username,
        email=u.email,
        is_active=u.is_active,
        is_superuser=u.is_superuser,
        created_at=u.created_at.isoformat()
    ) for u in users]


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """启用/禁用用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    session.add(user)
    await session.commit()
    
    return {"message": f"User {'enabled' if user.is_active else 'disabled'}"}
