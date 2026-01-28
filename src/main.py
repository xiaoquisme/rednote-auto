"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import inngest.fast_api

from src.inngest_client import client
from src.persistence.database import get_db
from src.functions.sync_twitter import sync_twitter_fn
from src.functions.translate_tweet import translate_tweet_fn
from src.functions.publish_content import publish_content_fn


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup: initialize database
    db = get_db()
    await db.init_db()
    yield
    # Shutdown: close database connection
    await db.close()


app = FastAPI(
    title="RedNote Auto",
    description="Auto-sync X (Twitter) content to 小红书 and 微信公众号",
    version="0.1.0",
    lifespan=lifespan,
)


# Register Inngest endpoint
inngest.fast_api.serve(
    app,
    client,
    [sync_twitter_fn, translate_tweet_fn, publish_content_fn],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "rednote-auto"}
