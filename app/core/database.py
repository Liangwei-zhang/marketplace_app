from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Sync engine for migrations
engine = create_engine(settings.DATABASE_URL_SYNC, echo=True)

# Async engine for runtime
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_session():
    with Session(engine) as session:
        yield session


async def get_async_session():
    async with async_session_maker() as session:
        yield session


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
