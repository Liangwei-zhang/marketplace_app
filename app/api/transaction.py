from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, ChatRoom, Transaction
from app.schemas import TransactionCreate, TransactionResponse, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    trans_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """创建交易意向 - 当买家"想要"时创建"""
    # Check item exists
    result = await session.execute(select(Item).where(Item.id == trans_data.item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.status == 2:  # Already sold
        raise HTTPException(status_code=400, detail="Item already sold")
    
    # Can't buy your own item
    if item.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot buy your own item")
    
    # Check if transaction already exists for this buyer+item
    result = await session.execute(
        select(Transaction).where(
            Transaction.item_id == trans_data.item_id,
            Transaction.buyer_id == current_user.id,
            Transaction.status.in_(["pending", "confirmed"])
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Transaction already exists")
    
    # Create transaction
    transaction = Transaction(
        item_id=trans_data.item_id,
        buyer_id=current_user.id,
        seller_id=item.seller_id,
        agreed_price=trans_data.agreed_price,
        note=trans_data.note,
        status="pending"
    )
    
    # Update item status to reserved
    item.status = 1
    
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    
    return transaction


@router.get("/my", response_model=List[TransactionResponse])
async def my_transactions(
    role: str = "buyer",  # buyer or seller
    status: str = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取我的交易列表"""
    if role == "seller":
        query = select(Transaction).where(Transaction.seller_id == current_user.id)
    else:
        query = select(Transaction).where(Transaction.buyer_id == current_user.id)
    
    if status:
        query = query.where(Transaction.status == status)
    
    query = query.order_by(Transaction.created_at.desc())
    result = await session.execute(query)
    
    return result.scalars().all()


@router.get("/{trans_id}", response_model=TransactionResponse)
async def get_transaction(
    trans_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取交易详情"""
    result = await session.execute(select(Transaction).where(Transaction.id == trans_id))
    trans = result.scalar_one_or_none()
    
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check permission
    if trans.buyer_id != current_user.id and trans.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return trans


@router.put("/{trans_id}/confirm", response_model=TransactionResponse)
async def confirm_transaction(
    trans_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """确认交易 - 双方确认后标记为 confirmed"""
    result = await session.execute(select(Transaction).where(Transaction.id == trans_id))
    trans = result.scalar_one_or_none()
    
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Must be buyer or seller
    if trans.buyer_id != current_user.id and trans.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if trans.status != "pending":
        raise HTTPException(status_code=400, detail="Transaction already processed")
    
    trans.status = "confirmed"
    await session.commit()
    await session.refresh(trans)
    
    return trans


@router.put("/{trans_id}/complete", response_model=TransactionResponse)
async def complete_transaction(
    trans_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """完成交易 - 见面交易后确认"""
    result = await session.execute(select(Transaction).where(Transaction.id == trans_id))
    trans = result.scalar_one_or_none()
    
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Must be buyer or seller
    if trans.buyer_id != current_user.id and trans.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if trans.status != "confirmed":
        raise HTTPException(status_code=400, detail="Transaction must be confirmed first")
    
    trans.status = "completed"
    trans.completed_at = datetime.now(timezone.utc)
    
    # Update item status to sold
    result = await session.execute(select(Item).where(Item.id == trans.item_id))
    item = result.scalar_one_or_none()
    if item:
        item.status = 2  # sold
    
    await session.commit()
    await session.refresh(trans)
    
    return trans


@router.put("/{trans_id}/cancel", response_model=TransactionResponse)
async def cancel_transaction(
    trans_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """取消交易"""
    result = await session.execute(select(Transaction).where(Transaction.id == trans_id))
    trans = result.scalar_one_or_none()
    
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Must be buyer or seller
    if trans.buyer_id != current_user.id and trans.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if trans.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed transaction")
    
    # Save old status for item revert check
    was_active = trans.status in ["pending", "confirmed"]
    
    trans.status = "cancelled"
    
    # If this was the active transaction, revert item status
    if was_active:
        result = await session.execute(select(Item).where(Item.id == trans.item_id))
        item = result.scalar_one_or_none()
        if item and item.status == 1:
            item.status = 0  # Available again
    
    await session.commit()
    await session.refresh(trans)
    
    return trans
