from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User
from app.models.push import PushSubscription
from pydantic import BaseModel

router = APIRouter(prefix="/push", tags=["push"])


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: dict


class PushSubscriptionDelete(BaseModel):
    endpoint: str


@router.post("/subscribe")
async def subscribe(
    sub: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """订阅推送通知"""
    # Check if already subscribed
    result = await session.execute(
        select(PushSubscription).where(
            and_(
                PushSubscription.user_id == current_user.id,
                PushSubscription.endpoint == sub.endpoint
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update keys
        existing.keys = json.dumps(sub.keys)
        session.add(existing)
    else:
        # Create new subscription
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=sub.endpoint,
            keys=json.dumps(sub.keys)
        )
        session.add(subscription)
    
    await session.commit()
    return {"message": "Subscribed successfully"}


@router.delete("/unsubscribe")
async def unsubscribe(
    data: PushSubscriptionDelete,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """取消订阅"""
    result = await session.execute(
        select(PushSubscription).where(
            and_(
                PushSubscription.user_id == current_user.id,
                PushSubscription.endpoint == data.endpoint
            )
        )
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        await session.delete(subscription)
        await session.commit()
    
    return {"message": "Unsubscribed successfully"}


@router.get("/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取订阅状态"""
    result = await session.execute(
        select(PushSubscription).where(PushSubscription.user_id == current_user.id)
    )
    subs = result.scalars().all()
    
    return {
        "is_subscribed": len(subs) > 0,
        "subscription_count": len(subs)
    }
