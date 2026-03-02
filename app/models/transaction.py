from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.item import Item


class Transaction(SQLModel, table=True):
    """交易记录 - 当买家"想要"并确认交易时创建"""
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id")
    buyer_id: int = Field(foreign_key="users.id")
    seller_id: int = Field(foreign_key="users.id")
    
    # 协商的价格（可能和原价不同）
    agreed_price: float
    
    # 状态: pending(待确认) / confirmed(已确认) / cancelled(已取消) / completed(已完成)
    status: str = Field(default="pending")
    
    # 备注
    note: Optional[str] = None
    
    # 创建/更新时间
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # 关联
    # item: "Item" = Relationship(sa_relationship_kwargs={"foreign_keys": [item_id]})
    # buyer: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": [buyer_id]})
    # seller: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": [seller_id]})


class Report(SQLModel, table=True):
    """举报记录"""
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 举报人
    reporter_id: int = Field(foreign_key="users.id")
    
    # 被举报商品/用户
    item_id: Optional[int] = Field(default=None, foreign_key="items.id")
    reported_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    # 举报类型: fraud(欺诈) / fake(虚假商品) / harassment(骚扰) / other(其他)
    report_type: str
    
    # 详细描述
    description: str
    
    # 状态: pending(待处理) / reviewed(已处理) / rejected(已驳回)
    status: str = Field(default="pending")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Review(SQLModel, table=True):
    """评价记录"""
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 交易ID（评价必须关联交易）
    transaction_id: int = Field(foreign_key="transactions.id")
    
    # 评价人
    reviewer_id: int = Field(foreign_key="users.id")
    
    # 被评价人
    reviewed_user_id: int = Field(foreign_key="users.id")
    
    # 评分 1-5
    rating: int
    
    # 评价内容
    content: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
