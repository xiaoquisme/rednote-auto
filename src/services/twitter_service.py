"""Twitter API service using tweepy."""

from datetime import datetime
from typing import Optional

import tweepy

from src.config import get_settings
from src.models.tweet import Tweet, TweetMedia


class TwitterService:
    """Service for interacting with Twitter API v2."""

    def __init__(self, bearer_token: Optional[str] = None):
        """Initialize Twitter client."""
        settings = get_settings()
        self.bearer_token = bearer_token or settings.twitter.bearer_token
        self.target_user_ids = settings.twitter.target_user_ids
        self._client: Optional[tweepy.Client] = None

    @property
    def client(self) -> tweepy.Client:
        """Get or create the Twitter client."""
        if self._client is None:
            self._client = tweepy.Client(bearer_token=self.bearer_token)
        return self._client

    def get_user_tweets(
        self,
        user_id: str,
        since_id: Optional[str] = None,
        max_results: int = 10,
    ) -> list[Tweet]:
        """
        Get recent tweets from a user.

        Args:
            user_id: Twitter user ID
            since_id: Only get tweets newer than this ID
            max_results: Maximum number of tweets to retrieve (5-100)

        Returns:
            List of Tweet objects
        """
        response = self.client.get_users_tweets(
            id=user_id,
            since_id=since_id,
            max_results=max_results,
            tweet_fields=["created_at", "referenced_tweets"],
            expansions=["attachments.media_keys"],
            media_fields=["url", "preview_image_url", "type"],
        )

        if not response.data:
            return []

        # Build media lookup
        media_lookup: dict[str, TweetMedia] = {}
        if response.includes and "media" in response.includes:
            for media in response.includes["media"]:
                media_lookup[media.media_key] = TweetMedia(
                    media_key=media.media_key,
                    type=media.type,
                    url=getattr(media, "url", None),
                    preview_image_url=getattr(media, "preview_image_url", None),
                )

        tweets = []
        for tweet in response.data:
            # Check if this is a retweet
            is_retweet = False
            referenced_tweet_id = None
            if tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "retweeted":
                        is_retweet = True
                        referenced_tweet_id = str(ref.id)
                        break

            # Get media attachments
            media = []
            if hasattr(tweet, "attachments") and tweet.attachments:
                media_keys = tweet.attachments.get("media_keys", [])
                for key in media_keys:
                    if key in media_lookup:
                        media.append(media_lookup[key])

            tweets.append(
                Tweet(
                    id=str(tweet.id),
                    author_id=user_id,
                    text=tweet.text,
                    created_at=tweet.created_at or datetime.now(),
                    media=media,
                    referenced_tweet_id=referenced_tweet_id,
                    is_retweet=is_retweet,
                )
            )

        return tweets

    def get_new_tweets_for_all_users(
        self,
        since_ids: Optional[dict[str, str]] = None,
    ) -> list[Tweet]:
        """
        Get new tweets from all monitored users.

        Args:
            since_ids: Dict mapping user_id to the last seen tweet_id

        Returns:
            List of all new tweets
        """
        since_ids = since_ids or {}
        all_tweets = []

        for user_id in self.target_user_ids:
            since_id = since_ids.get(user_id)
            tweets = self.get_user_tweets(user_id, since_id=since_id)

            # Filter out retweets - we only want original content
            original_tweets = [t for t in tweets if not t.is_retweet]
            all_tweets.extend(original_tweets)

        return all_tweets
