"""Twitter scraping service using syndication endpoint."""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional

import httpx

from src.config import get_settings
from src.models.tweet import Tweet, TweetMedia

logger = logging.getLogger(__name__)

SYNDICATION_URL = (
    "https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Regex to extract __NEXT_DATA__ JSON from HTML
_NEXT_DATA_RE = re.compile(
    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*(.*?)\s*</script>',
    re.DOTALL,
)


class TwitterService:
    """Service for scraping tweets via Twitter's syndication endpoint."""

    def __init__(
        self,
        target_usernames: Optional[list[str]] = None,
        headless: Optional[bool] = None,
        request_delay: Optional[float] = None,
    ):
        """Initialize Twitter scraping service."""
        settings = get_settings()
        self.target_usernames = (
            target_usernames or settings.twitter.target_usernames
        )
        self.headless = headless if headless is not None else settings.twitter.headless
        self.request_delay = (
            request_delay if request_delay is not None else settings.twitter.request_delay
        )
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is not None:
            return self._client

        self._client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=30.0,
        )
        return self._client

    async def _fetch_timeline_entries(self, username: str) -> list[dict]:
        """
        Fetch timeline entries from Twitter's syndication endpoint.

        Returns the list of tweet entry dicts from __NEXT_DATA__ JSON.
        """
        client = await self._ensure_client()
        url = SYNDICATION_URL.format(username=username)

        try:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(
                    "Syndication returned HTTP %d for @%s",
                    response.status_code,
                    username,
                )
                return []

            # Extract __NEXT_DATA__ JSON from HTML
            match = _NEXT_DATA_RE.search(response.text)
            if match is None:
                logger.warning("No __NEXT_DATA__ found for @%s", username)
                return []

            data = json.loads(match.group(1))

            # Navigate to the timeline entries
            entries = (
                data.get("props", {})
                .get("pageProps", {})
                .get("timeline", {})
                .get("entries", [])
            )
            return entries

        except Exception:
            logger.exception("Failed to fetch timeline for @%s", username)
            return []

    @staticmethod
    def _parse_tweet_entry(entry: dict) -> Optional[Tweet]:
        """
        Parse a syndication timeline entry into a Tweet model.

        Returns None if the entry is not a valid tweet.
        """
        content = entry.get("content", {})
        tweet_data = content.get("tweet", content)

        tweet_id = tweet_data.get("id_str")
        if not tweet_id:
            return None

        user = tweet_data.get("user", {})
        author_id = user.get("id_str", "")

        text = tweet_data.get("full_text") or tweet_data.get("text", "")

        # Parse created_at
        created_at_str = tweet_data.get("created_at", "")
        try:
            created_at = datetime.strptime(
                created_at_str, "%a %b %d %H:%M:%S %z %Y"
            )
        except (ValueError, TypeError):
            created_at = datetime.now()

        # Detect retweets
        is_retweet = "retweeted_status" in tweet_data
        referenced_tweet_id = None
        if is_retweet:
            rt_status = tweet_data["retweeted_status"]
            referenced_tweet_id = rt_status.get("id_str")

        # Parse media
        media_list: list[TweetMedia] = []
        entities = tweet_data.get("extended_entities") or tweet_data.get("entities", {})
        raw_media = entities.get("media", [])
        for m in raw_media:
            media_list.append(
                TweetMedia(
                    media_key=m.get("id_str", ""),
                    type=m.get("type", "photo"),
                    url=m.get("media_url_https") or m.get("media_url"),
                    preview_image_url=m.get("media_url_https"),
                )
            )

        return Tweet(
            id=tweet_id,
            author_id=author_id,
            text=text,
            created_at=created_at,
            media=media_list,
            referenced_tweet_id=referenced_tweet_id,
            is_retweet=is_retweet,
        )

    async def get_user_tweets(
        self,
        username: str,
        since_id: Optional[str] = None,
        max_results: int = 10,
    ) -> list[Tweet]:
        """
        Get recent tweets from a user via syndication scraping.

        Args:
            username: Twitter screen name (without @)
            since_id: Only return tweets with ID greater than this
            max_results: Maximum number of tweets to return

        Returns:
            List of Tweet objects
        """
        entries = await self._fetch_timeline_entries(username)

        tweets: list[Tweet] = []
        for entry in entries:
            tweet = self._parse_tweet_entry(entry)
            if tweet is None:
                continue

            # Filter by since_id using snowflake ID numeric comparison
            if since_id and int(tweet.id) <= int(since_id):
                continue

            tweets.append(tweet)
            if len(tweets) >= max_results:
                break

        return tweets

    async def get_new_tweets_for_all_users(
        self,
        since_ids: Optional[dict[str, str]] = None,
    ) -> list[Tweet]:
        """
        Get new tweets from all monitored users.

        Args:
            since_ids: Dict mapping author_id to the last seen tweet_id

        Returns:
            List of all new original (non-retweet) tweets
        """
        since_ids = since_ids or {}
        all_tweets: list[Tweet] = []

        for i, username in enumerate(self.target_usernames):
            if i > 0:
                await asyncio.sleep(self.request_delay)

            tweets = await self.get_user_tweets(username)

            for tweet in tweets:
                # Filter retweets
                if tweet.is_retweet:
                    continue

                # Filter by since_id (keyed by author_id from DB)
                author_since_id = since_ids.get(tweet.author_id)
                if author_since_id and int(tweet.id) <= int(author_since_id):
                    continue

                all_tweets.append(tweet)

        return all_tweets

    async def close(self) -> None:
        """Close HTTP client and cleanup."""
        if self._client:
            await self._client.aclose()
            self._client = None
