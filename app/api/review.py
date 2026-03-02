from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Transaction, Review
from app.schemas import ReviewCreate, ReviewResponse, ReviewWithUser

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """创建评价 - 交易完成后才能评价"""
    # Check transaction exists and is completed
    result = await session.execute(
        select(Transaction).where(Transaction.id == review_data.transaction_id)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != "completed":
        raise HTTPException(status_code=400, detail="Can only review completed transactions")
    
    # Check user is buyer or seller
    if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
        raise HTTPException(status_code=403, detail="Not authorized to review this transaction")
    
    # Determine reviewed user
    if current_user.id == transaction.buyer_id:
        reviewed_user_id = transaction.seller_id
    else:
        reviewed_user_id = transaction.buyer_id
    
    # Check if already reviewed
    result = await session.execute(
        select(Review).where(
            Review.transaction_id == review_data.transaction_id,
            Review.reviewer_id == current_user.id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed this transaction")
    
    # Create review
    review = Review(
        transaction_id=review_data.transaction_id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
        rating=review_data.rating,
        content=review_data.content
    )
    
    session.add(review)
    await session.commit()
    await session.refresh(review)
    
    return review


@router.get("/user/{user_id}", response_model=List[ReviewWithUser])
async def get_user_reviews(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户收到的评价"""
    result = await session.execute(
        select(Review)
        .where(Review.reviewed_user_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reviews = result.scalars().all()
    
    # Get reviewer info
    review_list = []
    for review in reviews:
        result = await session.execute(
            select(User).where(User.id == review.reviewer_id)
        )
        reviewer = result.scalar_one_or_none()
        
        review_with_user = ReviewWithUser(
            id=review.id,
            transaction_id=review.transaction_id,
            reviewer_id=review.reviewer_id,
            reviewed_user_id=review.reviewed_user_id,
            rating=review.rating,
            content=review.content,
            created_at=review.created_at,
            reviewer_name=reviewer.username if reviewer else "Unknown",
            reviewer_avatar=reviewer.avatar_url if reviewer else None
        )
        review_list.append(review_with_user)
    
    return review_list


@router.get("/transaction/{transaction_id}", response_model=List[ReviewResponse])
async def get_transaction_reviews(
    transaction_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """获取交易的评价"""
    result = await session.execute(
        select(Review).where(Review.transaction_id == transaction_id)
    )
    return result.scalars().all()


@router.get("/stats/{user_id}")
async def get_user_review_stats(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户评价统计"""
    # Get all reviews for user
    result = await session.execute(
        select(Review).where(Review.reviewed_user_id == user_id)
    )
    reviews = result.scalars().all()
    
    if not reviews:
        return {
            "total_reviews": 0,
            "avg_rating": 0,
            "rating_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        }
    
    # Calculate average
    total = sum(r.rating for r in reviews)
    avg_rating = total / len(reviews)
    
    # Rating breakdown
    breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in reviews:
        breakdown[str(r.rating)] += 1
    
    return {
        "total_reviews": len(reviews),
        "avg_rating": round(avg_rating, 2),
        "rating_breakdown": breakdown
    }
