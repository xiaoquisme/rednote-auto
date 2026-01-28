"""Tests for data models."""

from datetime import datetime

from src.models.tweet import Tweet, TweetMedia
from src.models.sync_record import SyncRecord, SyncStatus


def test_tweet_model():
    """Test Tweet model creation."""
    tweet = Tweet(
        id="123456",
        author_id="user123",
        text="Hello world!",
        created_at=datetime.now(),
    )

    assert tweet.id == "123456"
    assert tweet.author_id == "user123"
    assert tweet.has_media is False
    assert tweet.is_retweet is False


def test_tweet_with_media():
    """Test Tweet with media attachments."""
    media = TweetMedia(
        media_key="key123",
        type="photo",
        url="https://example.com/photo.jpg",
    )

    tweet = Tweet(
        id="123456",
        author_id="user123",
        text="Check out this photo!",
        created_at=datetime.now(),
        media=[media],
    )

    assert tweet.has_media is True
    assert len(tweet.photos) == 1


def test_sync_record_model():
    """Test SyncRecord model."""
    record = SyncRecord(
        tweet_id="123456",
        author_id="user123",
        original_text="Hello world!",
    )

    assert record.status == SyncStatus.PENDING
    assert record.translated_text is None
    assert record.xhs_post_id is None
