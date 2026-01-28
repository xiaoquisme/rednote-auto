"""Tests for Twitter service."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.services.twitter_service import TwitterService
from src.models.tweet import Tweet


class TestTwitterService:
    """Tests for TwitterService class."""

    def test_init_with_bearer_token(self):
        """Test initialization with bearer token."""
        service = TwitterService(bearer_token="test_token")
        assert service.bearer_token == "test_token"

    @patch("src.services.twitter_service.get_settings")
    def test_init_from_settings(self, mock_get_settings):
        """Test initialization from settings."""
        mock_settings = Mock()
        mock_settings.twitter.bearer_token = "settings_token"
        mock_settings.twitter.target_user_ids = ["user1", "user2"]
        mock_get_settings.return_value = mock_settings

        service = TwitterService()
        assert service.bearer_token == "settings_token"
        assert service.target_user_ids == ["user1", "user2"]

    @patch("src.services.twitter_service.tweepy.Client")
    def test_client_property_creates_client(self, mock_client_class):
        """Test that client property creates a tweepy client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        client = service.client

        mock_client_class.assert_called_once_with(bearer_token="test_token")
        assert client is mock_client

    @patch("src.services.twitter_service.tweepy.Client")
    def test_client_property_cached(self, mock_client_class):
        """Test that client is cached."""
        service = TwitterService(bearer_token="test_token")

        # Access twice
        client1 = service.client
        client2 = service.client

        # Should only create once
        mock_client_class.assert_called_once()
        assert client1 is client2

    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_user_tweets_empty_response(self, mock_client_class):
        """Test get_user_tweets with empty response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        tweets = service.get_user_tweets("user123")

        assert tweets == []

    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_user_tweets_with_data(self, mock_client_class):
        """Test get_user_tweets with tweet data."""
        mock_client = Mock()

        # Create mock tweet
        mock_tweet = Mock()
        mock_tweet.id = "123456"
        mock_tweet.text = "Hello world!"
        mock_tweet.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_tweet.referenced_tweets = None
        mock_tweet.attachments = None

        mock_response = Mock()
        mock_response.data = [mock_tweet]
        mock_response.includes = None

        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        tweets = service.get_user_tweets("user123")

        assert len(tweets) == 1
        assert tweets[0].id == "123456"
        assert tweets[0].text == "Hello world!"
        assert tweets[0].author_id == "user123"

    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_user_tweets_with_media(self, mock_client_class):
        """Test get_user_tweets with media attachments."""
        mock_client = Mock()

        # Create mock media
        mock_media = Mock()
        mock_media.media_key = "media_key_1"
        mock_media.type = "photo"
        mock_media.url = "https://example.com/photo.jpg"
        mock_media.preview_image_url = None

        # Create mock tweet with media
        mock_tweet = Mock()
        mock_tweet.id = "123456"
        mock_tweet.text = "Check this photo!"
        mock_tweet.created_at = datetime(2024, 1, 1)
        mock_tweet.referenced_tweets = None
        mock_tweet.attachments = {"media_keys": ["media_key_1"]}

        mock_response = Mock()
        mock_response.data = [mock_tweet]
        mock_response.includes = {"media": [mock_media]}

        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        tweets = service.get_user_tweets("user123")

        assert len(tweets) == 1
        assert tweets[0].has_media
        assert len(tweets[0].photos) == 1
        assert tweets[0].photos[0].url == "https://example.com/photo.jpg"

    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_user_tweets_retweet_detection(self, mock_client_class):
        """Test that retweets are detected."""
        mock_client = Mock()

        # Create mock retweet reference
        mock_ref = Mock()
        mock_ref.type = "retweeted"
        mock_ref.id = "original_tweet_id"

        mock_tweet = Mock()
        mock_tweet.id = "123456"
        mock_tweet.text = "RT: Something"
        mock_tweet.created_at = datetime(2024, 1, 1)
        mock_tweet.referenced_tweets = [mock_ref]
        mock_tweet.attachments = None

        mock_response = Mock()
        mock_response.data = [mock_tweet]
        mock_response.includes = None

        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        tweets = service.get_user_tweets("user123")

        assert len(tweets) == 1
        assert tweets[0].is_retweet is True
        assert tweets[0].referenced_tweet_id == "original_tweet_id"

    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_user_tweets_with_since_id(self, mock_client_class):
        """Test get_user_tweets with since_id parameter."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService(bearer_token="test_token")
        service.get_user_tweets("user123", since_id="12345", max_results=20)

        mock_client.get_users_tweets.assert_called_once()
        call_kwargs = mock_client.get_users_tweets.call_args[1]
        assert call_kwargs["since_id"] == "12345"
        assert call_kwargs["max_results"] == 20

    @patch("src.services.twitter_service.get_settings")
    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_new_tweets_for_all_users(self, mock_client_class, mock_get_settings):
        """Test fetching tweets from all monitored users."""
        mock_settings = Mock()
        mock_settings.twitter.bearer_token = "token"
        mock_settings.twitter.target_user_ids = ["user1", "user2"]
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()

        # Different tweets for different users
        def mock_get_tweets(id, **kwargs):
            mock_response = Mock()
            if id == "user1":
                mock_tweet = Mock()
                mock_tweet.id = "tweet1"
                mock_tweet.text = "User 1 tweet"
                mock_tweet.created_at = datetime(2024, 1, 1)
                mock_tweet.referenced_tweets = None
                mock_tweet.attachments = None
                mock_response.data = [mock_tweet]
            else:
                mock_tweet = Mock()
                mock_tweet.id = "tweet2"
                mock_tweet.text = "User 2 tweet"
                mock_tweet.created_at = datetime(2024, 1, 1)
                mock_tweet.referenced_tweets = None
                mock_tweet.attachments = None
                mock_response.data = [mock_tweet]
            mock_response.includes = None
            return mock_response

        mock_client.get_users_tweets.side_effect = mock_get_tweets
        mock_client_class.return_value = mock_client

        service = TwitterService()
        tweets = service.get_new_tweets_for_all_users()

        assert len(tweets) == 2
        assert tweets[0].id == "tweet1"
        assert tweets[1].id == "tweet2"

    @patch("src.services.twitter_service.get_settings")
    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_new_tweets_filters_retweets(self, mock_client_class, mock_get_settings):
        """Test that retweets are filtered out."""
        mock_settings = Mock()
        mock_settings.twitter.bearer_token = "token"
        mock_settings.twitter.target_user_ids = ["user1"]
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()

        # One original, one retweet
        mock_original = Mock()
        mock_original.id = "original"
        mock_original.text = "Original tweet"
        mock_original.created_at = datetime(2024, 1, 1)
        mock_original.referenced_tweets = None
        mock_original.attachments = None

        mock_ref = Mock()
        mock_ref.type = "retweeted"
        mock_ref.id = "some_id"

        mock_retweet = Mock()
        mock_retweet.id = "retweet"
        mock_retweet.text = "RT something"
        mock_retweet.created_at = datetime(2024, 1, 1)
        mock_retweet.referenced_tweets = [mock_ref]
        mock_retweet.attachments = None

        mock_response = Mock()
        mock_response.data = [mock_original, mock_retweet]
        mock_response.includes = None

        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService()
        tweets = service.get_new_tweets_for_all_users()

        # Only original should be returned
        assert len(tweets) == 1
        assert tweets[0].id == "original"

    @patch("src.services.twitter_service.get_settings")
    @patch("src.services.twitter_service.tweepy.Client")
    def test_get_new_tweets_with_since_ids(self, mock_client_class, mock_get_settings):
        """Test using since_ids to get incremental tweets."""
        mock_settings = Mock()
        mock_settings.twitter.bearer_token = "token"
        mock_settings.twitter.target_user_ids = ["user1"]
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_response.includes = None
        mock_client.get_users_tweets.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = TwitterService()
        service.get_new_tweets_for_all_users(since_ids={"user1": "last_tweet_id"})

        call_kwargs = mock_client.get_users_tweets.call_args[1]
        assert call_kwargs["since_id"] == "last_tweet_id"
