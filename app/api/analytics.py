from fastapi import APIRouter, Depends
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, Transaction, Review, Favorite, BrowseHistory, Follow

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/")
async def get_my_analytics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取我的数据统计"""
    
    # Items count
    result = await session.execute(
        select(func.count(Item.id)).where(Item.seller_id == current_user.id)
    )
    items_count = result.scalar() or 0
    
    # Active items
    result = await session.execute(
        select(func.count(Item.id)).where(Item.seller_id == current_user.id, Item.status == 0)
    )
    active_items = result.scalar() or 0
    
    # Sold items
    result = await session.execute(
        select(func.count(Item.id)).where(Item.seller_id == current_user.id, Item.status == 2)
    )
    sold_items = result.scalar() or 0
    
    # Favorites received
    result = await session.execute(
        select(func.count(Favorite.id)).join(Item).where(Item.seller_id == current_user.id)
    )
    favorites_received = result.scalar() or 0
    
    # My favorites
    result = await session.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    my_favorites = result.scalar() or 0
    
    # Completed transactions as seller
    result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.seller_id == current_user.id,
            Transaction.status == "completed"
        )
    )
    sales_completed = result.scalar() or 0
    
    # Completed transactions as buyer
    result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.buyer_id == current_user.id,
            Transaction.status == "completed"
        )
    )
    purchases_completed = result.scalar() or 0
    
    # Reviews received
    result = await session.execute(
        select(func.count(Review.id)).where(Review.reviewed_user_id == current_user.id)
    )
    reviews_received = result.scalar() or 0
    
    # Followers
    result = await session.execute(
        select(func.count(Follow.id)).where(Follow.following_id == current_user.id)
    )
    followers = result.scalar() or 0
    
    # Following
    result = await session.execute(
        select(func.count(Follow.id)).where(Follow.follower_id == current_user.id)
    )
    following = result.scalar() or 0
    
    # Total views on items
    result = await session.execute(
        select(func.sum(Item.view_count)).where(Item.seller_id == current_user.id)
    )
    total_views = result.scalar() or 0
    
    return {
        "items": {
            "total": items_count,
            "active": active_items,
            "sold": sold_items
        },
        "favorites": {
            "received": favorites_received,
            "given": my_favorites
        },
        "transactions": {
            "sales_completed": sales_completed,
            "purchases_completed": purchases_completed
        },
        "reviews": {
            "received": reviews_received
        },
        "social": {
            "followers": followers,
            "following": following
        },
        "views": {
            "total": total_views
        }
    }
