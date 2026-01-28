"""Tweet data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TweetMedia(BaseModel):
    """Media attached to a tweet."""

    media_key: str
    type: str  # photo, video, animated_gif
    url: Optional[str] = None
    preview_image_url: Optional[str] = None


class Tweet(BaseModel):
    """Tweet data model."""

    id: str = Field(description="Tweet ID")
    author_id: str = Field(description="Author user ID")
    text: str = Field(description="Tweet text content")
    created_at: datetime = Field(description="Tweet creation time")
    media: list[TweetMedia] = Field(default_factory=list, description="Attached media")
    referenced_tweet_id: Optional[str] = Field(
        default=None, description="ID of referenced tweet (retweet/quote)"
    )
    is_retweet: bool = Field(default=False, description="Is this a retweet")

    @property
    def has_media(self) -> bool:
        """Check if tweet has media attachments."""
        return len(self.media) > 0

    @property
    def photos(self) -> list[TweetMedia]:
        """Get photo media only."""
        return [m for m in self.media if m.type == "photo"]
