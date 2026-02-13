"""Inngest function for syncing Twitter tweets."""

import inngest

from src.inngest_client import client
from src.services.twitter_service import TwitterService
from src.persistence.database import get_db, SyncRecordModel, SyncStatusEnum
from sqlalchemy import select


@client.create_function(
    fn_id="sync-twitter",
    trigger=inngest.TriggerCron(cron="*/30 * * * *"),
    retries=3,
)
async def sync_twitter_fn(ctx: inngest.Context) -> dict:
    """
    Periodically sync new tweets from monitored Twitter users.

    This function:
    1. Gets the last synced tweet ID for each user
    2. Fetches new tweets since that ID
    3. Sends a tweet.fetched event for each new tweet
    """

    # Step 1: Get last synced tweet IDs from database
    async def get_since_ids() -> dict[str, str]:
        db = get_db()
        async with db.session() as session:
            result = await session.execute(
                select(
                    SyncRecordModel.author_id,
                    SyncRecordModel.tweet_id,
                )
                .order_by(SyncRecordModel.tweet_id.desc())
                .distinct(SyncRecordModel.author_id)
            )
            rows = result.all()
            return {row.author_id: row.tweet_id for row in rows}

    since_ids = await ctx.step.run("get-since-ids", get_since_ids)

    # Step 2: Fetch new tweets
    async def fetch_tweets() -> list[dict]:
        twitter = TwitterService()
        try:
            tweets = await twitter.get_new_tweets_for_all_users(since_ids=since_ids)
            return [tweet.model_dump(mode="json") for tweet in tweets]
        finally:
            await twitter.close()

    tweets = await ctx.step.run("fetch-tweets", fetch_tweets)

    if not tweets:
        return {"synced": 0, "message": "No new tweets found"}

    # Step 3: Save tweets to database and send events
    events_sent = 0
    for tweet in tweets:
        # Save to database
        async def save_tweet(t: dict = tweet) -> None:
            db = get_db()
            async with db.session() as session:
                existing = await session.execute(
                    select(SyncRecordModel).where(
                        SyncRecordModel.tweet_id == str(t["id"])
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    return
                record = SyncRecordModel(
                    tweet_id=t["id"],
                    author_id=t["author_id"],
                    original_text=t["text"],
                    status=SyncStatusEnum.PENDING,
                )
                session.add(record)

        await ctx.step.run(f"save-tweet-{tweet['id']}", save_tweet)

        # Send event for translation
        await ctx.step.send_event(
            f"send-event-{tweet['id']}",
            events=[
                inngest.Event(
                    name="tweet.fetched",
                    data=tweet,
                )
            ],
        )
        events_sent += 1

    return {"synced": events_sent, "tweets": [t["id"] for t in tweets]}
