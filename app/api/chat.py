from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Item, ChatRoom, Message, Transaction
from app.schemas import ChatRoomCreate, ChatRoomResponse, MessageCreate, MessageResponse, ChatRoomDetail

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/rooms", response_model=ChatRoomResponse, status_code=201)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create or get existing chat room for an item.
    
    Also creates a Transaction record to link chat with the deal.
    """
    # Check item exists
    result = await session.execute(select(Item).where(Item.id == room_data.item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Can't chat with yourself
    if item.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")
    
    # Check if room already exists
    query = select(ChatRoom).where(
        ChatRoom.item_id == room_data.item_id,
        ChatRoom.buyer_id == current_user.id
    )
    result = await session.execute(query)
    room = result.scalar_one_or_none()
    
    if room:
        return room
    
    # Create transaction first
    transaction = Transaction(
        item_id=room_data.item_id,
        buyer_id=current_user.id,
        seller_id=item.seller_id,
        agreed_price=item.price,  # Start with asking price
        status="pending"
    )
    session.add(transaction)
    await session.flush()  # Get transaction.id
    
    # Create new room with transaction link
    room = ChatRoom(
        item_id=room_data.item_id,
        buyer_id=current_user.id,
        seller_id=item.seller_id,
        transaction_id=transaction.id
    )
    
    session.add(room)
    await session.commit()
    await session.refresh(room)
    
    return room


@router.get("/rooms", response_model=List[ChatRoomDetail])
async def list_chat_rooms(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """List all chat rooms for current user."""
    query = select(ChatRoom).where(
        (ChatRoom.buyer_id == current_user.id) | (ChatRoom.seller_id == current_user.id)
    ).order_by(ChatRoom.updated_at.desc())
    
    result = await session.execute(query)
    rooms = result.scalars().all()
    
    # Build detailed response
    details = []
    for room in rooms:
        # Get item info
        item_result = await session.execute(select(Item).where(Item.id == room.item_id))
        item = item_result.scalar_one_or_none()
        
        # Determine other user
        if room.buyer_id == current_user.id:
            other_user_result = await session.execute(select(User).where(User.id == room.seller_id))
            other_user = other_user_result.scalar_one_or_none()
        else:
            other_user_result = await session.execute(select(User).where(User.id == room.buyer_id))
            other_user = other_user_result.scalar_one_or_none()
        
        # Get last message
        msg_result = await session.execute(
            select(Message).where(Message.room_id == room.id).order_by(Message.created_at.desc()).limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()
        
        # Get unread count
        unread_result = await session.execute(
            select(func.count(Message.id)).where(
                Message.room_id == room.id,
                Message.sender_id != current_user.id,
                Message.is_read == False
            )
        )
        unread_count = unread_result.scalar()
        
        detail = ChatRoomDetail(
            id=room.id,
            item_id=room.item_id,
            buyer_id=room.buyer_id,
            seller_id=room.seller_id,
            created_at=room.created_at,
            updated_at=room.updated_at,
            item_title=item.title if item else None,
            item_price=item.price if item else None,
            item_image=item.images[0] if item and item.images else None,
            other_user_name=other_user.username if other_user else None,
            last_message=last_msg.content if last_msg else None,
            last_message_time=last_msg.created_at if last_msg else None,
            unread_count=unread_count
        )
        details.append(detail)
    
    return details


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    room_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get messages in a chat room."""
    # Verify room exists and user is participant
    result = await session.execute(select(ChatRoom).where(ChatRoom.id == room_id))
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    if room.buyer_id != current_user.id and room.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get messages
    query = select(Message).where(Message.room_id == room_id).order_by(Message.created_at.desc())
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # Mark as read
    for msg in messages:
        if msg.sender_id != current_user.id and not msg.is_read:
            msg.is_read = True
    await session.commit()
    
    return list(reversed(messages))


@router.post("/rooms/{room_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    room_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Send a message in a chat room."""
    # Verify room exists
    result = await session.execute(select(ChatRoom).where(ChatRoom.id == room_id))
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    if room.buyer_id != current_user.id and room.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create message
    message = Message(
        room_id=room_id,
        sender_id=current_user.id,
        content=message_data.content,
        message_type=message_data.message_type
    )
    
    session.add(message)
    
    # Update room timestamp
    room.updated_at = message.created_at
    
    await session.commit()
    await session.refresh(message)
    
    return message
