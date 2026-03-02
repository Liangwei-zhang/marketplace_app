from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.api.auth import get_current_user
from app.models import User, Report

router = APIRouter(prefix="/reports", tags=["reports"])


# Report types
REPORT_TYPES = ["fraud", "fake", "harassment", "other"]


class ReportCreate(BaseModel):
    """Schema for creating a report"""
    item_id: Optional[int] = None
    reported_user_id: Optional[int] = None
    report_type: str = Field(..., pattern="^(fraud|fake|harassment|other)$")
    description: str = Field(..., min_length=10, max_length=1000)


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    item_id: Optional[int] = None
    reported_user_id: Optional[int] = None
    report_type: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """创建举报"""
    # Validate at least one of item_id or reported_user_id
    if not report_data.item_id and not report_data.reported_user_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either item_id or reported_user_id"
        )
    
    # Validate report_type
    if report_data.report_type not in REPORT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type. Must be one of: {REPORT_TYPES}"
        )
    
    # Can't report yourself
    if report_data.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    # Check if item exists (if provided)
    if report_data.item_id:
        from app.models import Item
        result = await session.execute(
            select(Item).where(Item.id == report_data.item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user exists (if provided)
    if report_data.reported_user_id:
        result = await session.execute(
            select(User).where(User.id == report_data.reported_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Check for duplicate report
    result = await session.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.item_id == report_data.item_id,
            Report.status == "pending"
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already reported this item")
    
    # Create report
    report = Report(
        reporter_id=current_user.id,
        item_id=report_data.item_id,
        reported_user_id=report_data.reported_user_id,
        report_type=report_data.report_type,
        description=report_data.description,
        status="pending"
    )
    
    session.add(report)
    await session.commit()
    await session.refresh(report)
    
    return report


@router.get("/my", response_model=List[ReportResponse])
async def my_reports(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取我发出的举报"""
    result = await session.execute(
        select(Report)
        .where(Report.reporter_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    return result.scalars().all()


# Admin endpoints (for production, add admin check)
@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    status: str = "pending",
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """列出举报（管理员）"""
    result = await session.execute(
        select(Report)
        .where(Report.status == status)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


@router.put("/{report_id}/resolve", response_model=ReportResponse)
async def resolve_report(
    report_id: int,
    action: str = "reviewed",  # reviewed or rejected
    session: AsyncSession = Depends(get_async_session)
):
    """处理举报（管理员）"""
    result = await session.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if action == "rejected":
        report.status = "rejected"
    else:
        report.status = "reviewed"
    
    session.add(report)
    await session.commit()
    await session.refresh(report)
    
    return report
