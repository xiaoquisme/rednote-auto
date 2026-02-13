"""Tests for Twitter service (Playwright-based syndication scraper)."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.services.twitter_service import TwitterService
from src.models.tweet import Tweet


# --- Fixture data simulating syndication __NEXT_DATA__ entries ---

BASIC_ENTRY = {
    "content": {
        "tweet": {
            "id_str": "1234567890",
            "user": {"id_str": "9876", "screen_name": "testuser"},
            "full_text": "Hello world!",
            "created_at": "Mon Jan 01 12:00:00 +0000 2024",
            "entities": {},
        }
    }
}

ENTRY_WITH_MEDIA = {
    "content": {
        "tweet": {
            "id_str": "1234567891",
            "user": {"id_str": "9876", "screen_name": "testuser"},
            "full_text": "Check this photo!",
            "created_at": "Mon Jan 01 12:00:00 +0000 2024",
            "entities": {},
            "extended_entities": {
                "media": [
                    {
                        "id_str": "media_1",
                        "type": "photo",
                        "media_url_https": "https://pbs.twimg.com/media/photo.jpg",
                    }
                ]
            },
        }
    }
}

RETWEET_ENTRY = {
    "content": {
        "tweet": {
            "id_str": "1234567892",
            "user": {"id_str": "9876", "screen_name": "testuser"},
            "full_text": "RT @someone: Something",
            "created_at": "Mon Jan 01 12:00:00 +0000 2024",
            "entities": {},
            "retweeted_status": {
                "id_str": "original_tweet_id",
            },
        }
    }
}

ENTRY_NO_ID = {
    "content": {
        "tweet": {
            "user": {"id_str": "9876"},
            "full_text": "Missing id_str",
        }
    }
}


class TestParseTweetEntry:
    """Tests for the pure _parse_tweet_entry static method."""

    def test_basic_tweet(self):
        tweet = TwitterService._parse_tweet_entry(BASIC_ENTRY)
        assert tweet is not None
        assert tweet.id == "1234567890"
        assert tweet.author_id == "9876"
        assert tweet.text == "Hello world!"
        assert tweet.is_retweet is False
        assert tweet.referenced_tweet_id is None

    def test_tweet_with_media(self):
        tweet = TwitterService._parse_tweet_entry(ENTRY_WITH_MEDIA)
        assert tweet is not None
        assert tweet.has_media
        assert len(tweet.photos) == 1
        assert tweet.photos[0].url == "https://pbs.twimg.com/media/photo.jpg"
        assert tweet.photos[0].media_key == "media_1"

    def test_retweet_detection(self):
        tweet = TwitterService._parse_tweet_entry(RETWEET_ENTRY)
        assert tweet is not None
        assert tweet.is_retweet is True
        assert tweet.referenced_tweet_id == "original_tweet_id"

    def test_entry_without_id_returns_none(self):
        tweet = TwitterService._parse_tweet_entry(ENTRY_NO_ID)
        assert tweet is None

    def test_fallback_text_field(self):
        entry = {
            "content": {
                "tweet": {
                    "id_str": "111",
                    "user": {"id_str": "222"},
                    "text": "fallback text",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {},
                }
            }
        }
        tweet = TwitterService._parse_tweet_entry(entry)
        assert tweet is not None
        assert tweet.text == "fallback text"

    def test_invalid_created_at_uses_fallback(self):
        entry = {
            "content": {
                "tweet": {
                    "id_str": "111",
                    "user": {"id_str": "222"},
                    "full_text": "test",
                    "created_at": "invalid-date",
                    "entities": {},
                }
            }
        }
        tweet = TwitterService._parse_tweet_entry(entry)
        assert tweet is not None
        assert isinstance(tweet.created_at, datetime)

    def test_media_from_entities_fallback(self):
        """Media parsed from entities when extended_entities is absent."""
        entry = {
            "content": {
                "tweet": {
                    "id_str": "111",
                    "user": {"id_str": "222"},
                    "full_text": "test",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {
                        "media": [
                            {
                                "id_str": "m1",
                                "type": "photo",
                                "media_url_https": "https://example.com/img.jpg",
                            }
                        ]
                    },
                }
            }
        }
        tweet = TwitterService._parse_tweet_entry(entry)
        assert tweet is not None
        assert len(tweet.media) == 1
        assert tweet.media[0].url == "https://example.com/img.jpg"


class TestGetUserTweets:
    """Tests for get_user_tweets with mocked _fetch_timeline_entries."""

    @pytest.fixture
    def service(self):
        return TwitterService(
            target_usernames=["testuser"],
            headless=True,
            request_delay=0,
        )

    async def test_returns_parsed_tweets(self, service):
        service._fetch_timeline_entries = AsyncMock(
            return_value=[BASIC_ENTRY, ENTRY_WITH_MEDIA]
        )

        tweets = await service.get_user_tweets("testuser")
        assert len(tweets) == 2
        assert tweets[0].id == "1234567890"
        assert tweets[1].id == "1234567891"

    async def test_filters_by_since_id(self, service):
        service._fetch_timeline_entries = AsyncMock(
            return_value=[BASIC_ENTRY, ENTRY_WITH_MEDIA]
        )

        tweets = await service.get_user_tweets("testuser", since_id="1234567890")
        assert len(tweets) == 1
        assert tweets[0].id == "1234567891"

    async def test_respects_max_results(self, service):
        service._fetch_timeline_entries = AsyncMock(
            return_value=[BASIC_ENTRY, ENTRY_WITH_MEDIA]
        )

        tweets = await service.get_user_tweets("testuser", max_results=1)
        assert len(tweets) == 1

    async def test_skips_invalid_entries(self, service):
        service._fetch_timeline_entries = AsyncMock(
            return_value=[ENTRY_NO_ID, BASIC_ENTRY]
        )

        tweets = await service.get_user_tweets("testuser")
        assert len(tweets) == 1
        assert tweets[0].id == "1234567890"

    async def test_empty_entries(self, service):
        service._fetch_timeline_entries = AsyncMock(return_value=[])

        tweets = await service.get_user_tweets("testuser")
        assert tweets == []


class TestGetNewTweetsForAllUsers:
    """Tests for get_new_tweets_for_all_users."""

    @pytest.fixture
    def service(self):
        return TwitterService(
            target_usernames=["user1", "user2"],
            headless=True,
            request_delay=0,
        )

    async def test_fetches_from_all_users(self, service):
        entry_user1 = {
            "content": {
                "tweet": {
                    "id_str": "100",
                    "user": {"id_str": "u1", "screen_name": "user1"},
                    "full_text": "User 1 tweet",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {},
                }
            }
        }
        entry_user2 = {
            "content": {
                "tweet": {
                    "id_str": "200",
                    "user": {"id_str": "u2", "screen_name": "user2"},
                    "full_text": "User 2 tweet",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {},
                }
            }
        }

        async def mock_fetch(username):
            return [entry_user1] if username == "user1" else [entry_user2]

        service._fetch_timeline_entries = AsyncMock(side_effect=mock_fetch)

        tweets = await service.get_new_tweets_for_all_users()
        assert len(tweets) == 2
        ids = {t.id for t in tweets}
        assert ids == {"100", "200"}

    async def test_filters_retweets(self, service):
        service._fetch_timeline_entries = AsyncMock(
            return_value=[BASIC_ENTRY, RETWEET_ENTRY]
        )

        tweets = await service.get_new_tweets_for_all_users()
        # Retweet should be filtered, only original from each user call
        assert all(not t.is_retweet for t in tweets)

    async def test_filters_by_since_ids(self, service):
        entry = {
            "content": {
                "tweet": {
                    "id_str": "500",
                    "user": {"id_str": "author1", "screen_name": "user1"},
                    "full_text": "Old tweet",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {},
                }
            }
        }
        service._fetch_timeline_entries = AsyncMock(return_value=[entry])
        service.target_usernames = ["user1"]

        tweets = await service.get_new_tweets_for_all_users(
            since_ids={"author1": "500"}
        )
        assert len(tweets) == 0

    async def test_passes_new_tweets_through(self, service):
        entry = {
            "content": {
                "tweet": {
                    "id_str": "600",
                    "user": {"id_str": "author1", "screen_name": "user1"},
                    "full_text": "New tweet",
                    "created_at": "Mon Jan 01 12:00:00 +0000 2024",
                    "entities": {},
                }
            }
        }
        service._fetch_timeline_entries = AsyncMock(return_value=[entry])
        service.target_usernames = ["user1"]

        tweets = await service.get_new_tweets_for_all_users(
            since_ids={"author1": "500"}
        )
        assert len(tweets) == 1
        assert tweets[0].id == "600"


class TestInit:
    """Tests for TwitterService initialization."""

    @patch("src.services.twitter_service.get_settings")
    def test_init_from_settings(self, mock_get_settings):
        from unittest.mock import Mock
        mock_settings = Mock()
        mock_settings.twitter.target_usernames = ["user1", "user2"]
        mock_settings.twitter.headless = True
        mock_settings.twitter.request_delay = 2.0
        mock_get_settings.return_value = mock_settings

        service = TwitterService()
        assert service.target_usernames == ["user1", "user2"]
        assert service.headless is True
        assert service.request_delay == 2.0

    def test_init_with_explicit_params(self):
        service = TwitterService(
            target_usernames=["explicit"],
            headless=False,
            request_delay=5.0,
        )
        assert service.target_usernames == ["explicit"]
        assert service.headless is False
        assert service.request_delay == 5.0
