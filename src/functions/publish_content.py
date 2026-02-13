"""Inngest function for publishing translated content."""

import inngest

from src.inngest_client import client
from src.config import get_settings
from src.agents.publisher_agent import (
    run_xhs_publisher_agent,
    run_wechat_publisher_agent,
)
from src.persistence.database import get_db, SyncRecordModel, SyncStatusEnum
from sqlalchemy import select


@client.create_function(
    fn_id="publish-content",
    trigger=inngest.TriggerEvent(event="tweet.translated"),
    retries=2,
)
async def publish_content_fn(ctx: inngest.Context) -> dict:
    """
    Publish translated content to enabled platforms using Claude agents.

    This function:
    1. Receives a tweet.translated event
    2. Publishes to 小红书 via agent (if enabled)
    3. Publishes to 微信公众号 via agent (if enabled)
    4. Updates the database with results
    """
    data = ctx.event.data
    tweet_id = data["tweet_id"]
    translated_text = data["translated_text"]
    original_text = data["original_text"]

    settings = get_settings()
    enabled_platforms = settings.enabled_platforms
    results = {"tweet_id": tweet_id, "published": []}

    # Step 1: Publish to XHS if enabled
    if "xhs" in enabled_platforms:

        async def publish_xhs() -> dict:
            # Create a title from the first line or first 50 chars
            title = translated_text.split("\n")[0][:50]
            if len(translated_text) > 50:
                title = title[:47] + "..."

            return await run_xhs_publisher_agent(
                title=title,
                content=translated_text,
            )

        xhs_result = await ctx.step.run("publish-xhs", publish_xhs)

        if xhs_result["success"]:
            results["published"].append("xhs")

            # Update database
            async def update_xhs_status() -> None:
                db = get_db()
                async with db.session() as session:
                    result = await session.execute(
                        select(SyncRecordModel).where(
                            SyncRecordModel.tweet_id == tweet_id
                        )
                    )
                    record = result.scalar_one_or_none()
                    if record:
                        record.xhs_post_id = xhs_result.get("post_id")
                        if "wechat" not in enabled_platforms:
                            record.status = SyncStatusEnum.PUBLISHED_ALL
                        else:
                            record.status = SyncStatusEnum.PUBLISHED_XHS

            await ctx.step.run("update-xhs-status", update_xhs_status)
        else:
            results["xhs_error"] = xhs_result.get("error")
            if xhs_result.get("login_required"):
                results["xhs_login_required"] = True

    # Step 2: Publish to WeChat if enabled
    if "wechat" in enabled_platforms:

        async def publish_wechat() -> dict:
            # Create a title
            title = translated_text.split("\n")[0][:60]
            if len(translated_text) > 60:
                title = title[:57] + "..."

            return await run_wechat_publisher_agent(
                title=title,
                content=translated_text,
                original_text=original_text,
            )

        wechat_result = await ctx.step.run("publish-wechat", publish_wechat)

        if wechat_result["success"]:
            results["published"].append("wechat")

            # Update database
            async def update_wechat_status() -> None:
                db = get_db()
                async with db.session() as session:
                    result = await session.execute(
                        select(SyncRecordModel).where(
                            SyncRecordModel.tweet_id == tweet_id
                        )
                    )
                    record = result.scalar_one_or_none()
                    if record:
                        record.wechat_article_id = wechat_result.get("media_id")
                        if "xhs" in results["published"]:
                            record.status = SyncStatusEnum.PUBLISHED_ALL
                        else:
                            record.status = SyncStatusEnum.PUBLISHED_WECHAT

            await ctx.step.run("update-wechat-status", update_wechat_status)
        else:
            results["wechat_error"] = wechat_result.get("error")
            if wechat_result.get("login_required"):
                results["wechat_login_required"] = True

    # Mark as failed if nothing was published
    if not results["published"]:

        async def mark_failed() -> None:
            db = get_db()
            async with db.session() as session:
                result = await session.execute(
                    select(SyncRecordModel).where(SyncRecordModel.tweet_id == tweet_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    record.status = SyncStatusEnum.FAILED
                    record.error_message = f"XHS: {results.get('xhs_error', 'N/A')}, WeChat: {results.get('wechat_error', 'N/A')}"

        await ctx.step.run("mark-failed", mark_failed)

    return results
