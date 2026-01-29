"""Inngest function for translating tweets."""

import inngest

from src.inngest_client import client
from src.services.translator_service import TranslatorService
from src.persistence.database import get_db, SyncRecordModel, SyncStatusEnum
from sqlalchemy import select


@client.create_function(
    fn_id="translate-tweet",
    trigger=inngest.TriggerEvent(event="tweet.fetched"),
    retries=3,
)
async def translate_tweet_fn(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """
    Translate a fetched tweet to Chinese.

    This function:
    1. Receives a tweet.fetched event
    2. Translates the tweet text
    3. Updates the database
    4. Sends a tweet.translated event
    """
    tweet = ctx.event.data

    # Step 1: Translate the tweet
    async def translate() -> str:
        translator = TranslatorService()
        return translator.translate(tweet["text"])

    translated_text = await step.run("translate", translate)

    # Step 2: Update database with translation
    async def update_db() -> None:
        db = get_db()
        async with db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == tweet["id"])
            )
            record = result.scalar_one_or_none()
            if record:
                record.translated_text = translated_text
                record.status = SyncStatusEnum.TRANSLATED

    await step.run("update-db", update_db)

    # Step 3: Send translated event
    await step.send_event(
        "send-translated-event",
        events=[
            inngest.Event(
                name="tweet.translated",
                data={
                    "tweet_id": tweet["id"],
                    "author_id": tweet["author_id"],
                    "original_text": tweet["text"],
                    "translated_text": translated_text,
                    "media": tweet.get("media", []),
                    "created_at": tweet.get("created_at"),
                },
            )
        ],
    )

    return {
        "tweet_id": tweet["id"],
        "translated": True,
        "text_preview": translated_text[:100] if translated_text else "",
    }
