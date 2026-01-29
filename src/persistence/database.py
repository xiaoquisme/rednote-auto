"""SQLite database operations with SQLAlchemy."""

from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Optional

from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class SyncStatusEnum(str, Enum):
    """Status of a sync record."""

    PENDING = "pending"
    TRANSLATED = "translated"
    PUBLISHED_XHS = "published_xhs"
    PUBLISHED_WECHAT = "published_wechat"
    PUBLISHED_ALL = "published_all"
    FAILED = "failed"


class SyncRecordModel(Base):
    """Database model for tracking synced tweets."""

    __tablename__ = "sync_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tweet_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    author_id: Mapped[str] = mapped_column(String(64), index=True)
    original_text: Mapped[str] = mapped_column(Text)
    translated_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[SyncStatusEnum] = mapped_column(
        SQLEnum(SyncStatusEnum), default=SyncStatusEnum.PENDING
    )
    xhs_post_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    wechat_article_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Database:
    """Database connection and operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database with URL from settings or override."""
        self.database_url = database_url or get_settings().database.url
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global database instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
