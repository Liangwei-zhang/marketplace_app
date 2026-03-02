from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, Follow

router = APIRouter(prefix="/follow", tags=["follow"])


@router.post("/{user_id}")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """关注用户"""
    # Can't follow yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check user exists
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    result = await session.execute(
        select(Follow).where(
            and_(
                Follow.follower_id == current_user.id,
                Follow.following_id == user_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    
    # Create follow
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    session.add(follow)
    await session.commit()
    
    return {"message": "Following"}


@router.delete("/{user_id}")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """取消关注"""
    result = await session.execute(
        select(Follow).where(
            and_(
                Follow.follower_id == current_user.id,
                Follow.following_id == user_id
            )
        )
    )
    follow = result.scalar_one_or_none()
    
    if not follow:
        raise HTTPException(status_code=404, detail="Not following")
    
    await session.delete(follow)
    await session.commit()
    
    return {"message": "Unfollowed"}


@router.get("/following")
async def my_following(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """我的关注列表"""
    result = await session.execute(
        select(Follow).where(Follow.follower_id == current_user.id)
    )
    follows = result.scalars().all()
    
    users = []
    for f in follows:
        result = await session.execute(select(User).where(User.id == f.following_id))
        user = result.scalar_one_or_none()
        if user:
            users.append(user)
    
    return users


@router.get("/followers")
async def my_followers(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """我的粉丝列表"""
    result = await session.execute(
        select(Follow).where(Follow.following_id == current_user.id)
    )
    follows = result.scalars().all()
    
    users = []
    for f in follows:
        result = await session.execute(select(User).where(User.id == f.follower_id))
        user = result.scalar_one_or_none()
        if user:
            users.append(user)
    
    return users


@router.get("/check/{user_id}")
async def check_follow(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """检查是否关注"""
    result = await session.execute(
        select(Follow).where(
            and_(
                Follow.follower_id == current_user.id,
                Follow.following_id == user_id
            )
        )
    )
    follow = result.scalar_one_or_none()
    
    return {"is_following": follow is not None}
