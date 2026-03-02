from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_async_session
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserResponse, Token, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    """Register a new user."""
    # Check username
    result = await session.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check email
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    """Login and get access token."""
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user info."""
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url
    if user_data.latitude is not None:
        current_user.latitude = user_data.latitude
    if user_data.longitude is not None:
        current_user.longitude = user_data.longitude
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    
    return current_user


# Password reset schemas
from pydantic import BaseModel as PydanticBaseModel


class PasswordResetRequest(PydanticBaseModel):
    email: str


class PasswordResetConfirm(PydanticBaseModel):
    token: str
    new_password: str


@router.post("/password-reset/request")
async def request_password_reset(
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Request password reset - sends reset token to email."""
    # Find user by email
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generate reset token
    import secrets
    from datetime import timedelta
    
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    session.add(user)
    await session.commit()
    
    # In production, send email here
    # For now, return the token (development only!)
    return {
        "message": "Reset token generated",
        "token": token,  # TODO: Remove in production - send via email instead
        "expires": user.reset_token_expires.isoformat()
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_async_session)
):
    """Confirm password reset with token."""
    # Find user by token
    result = await session.execute(
        select(User).where(
            User.reset_token == data.token,
            User.reset_token_expires > datetime.utcnow()
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    session.add(user)
    await session.commit()
    
    return {"message": "Password reset successful"}
