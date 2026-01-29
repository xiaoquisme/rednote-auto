"""Sync record models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SyncStatus(str, Enum):
    """Status of a sync record."""

    PENDING = "pending"
    TRANSLATED = "translated"
    PUBLISHED_XHS = "published_xhs"
    PUBLISHED_WECHAT = "published_wechat"
    PUBLISHED_ALL = "published_all"
    FAILED = "failed"


class SyncRecord(BaseModel):
    """Sync record for tracking tweet sync status."""

    id: Optional[int] = None
    tweet_id: str = Field(description="Original tweet ID")
    author_id: str = Field(description="Tweet author ID")
    original_text: str = Field(description="Original tweet text")
    translated_text: Optional[str] = Field(default=None, description="Translated text")
    status: SyncStatus = Field(default=SyncStatus.PENDING)
    xhs_post_id: Optional[str] = Field(default=None, description="小红书 post ID")
    wechat_article_id: Optional[str] = Field(
        default=None, description="WeChat article ID"
    )
    error_message: Optional[str] = Field(default=None, description="Error if failed")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
