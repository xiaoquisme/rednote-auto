# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**rednote-auto** syncs X (Twitter) posts to Chinese social media platforms (小红书/XHS and WeChat Official Account) with AI-powered translation. It uses an event-driven architecture powered by Inngest: cron fetches tweets → translates via OpenAI → publishes to enabled platforms.

## Commands

```bash
# Install dependencies
uv sync

# Install Playwright browsers (required for XHS service)
uv run playwright install chromium

# Run all tests
uv run pytest

# Run tests with coverage (80% minimum enforced)
uv run pytest --cov=src --cov-report=term-missing

# Run a single test file / class / method
uv run pytest tests/test_twitter_service.py
uv run pytest tests/test_config.py::TestTwitterConfig
uv run pytest tests/test_config.py::TestTwitterConfig::test_init_from_settings

# Lint
uv run ruff check src/
uv run ruff format --check src/

# Auto-format
uv run ruff format src/

# Start the app locally (requires Inngest dev server running separately)
uv run uvicorn src.main:app --reload --port 8000

# Start Inngest dev server
npx inngest-cli@latest dev
```

## Architecture

### Event Flow (Inngest)

```
sync_twitter (cron */30) → emit tweet.fetched
  → translate_tweet (event handler) → emit tweet.translated
    → publish_content (event handler) → XHS + WeChat
```

### Layer Structure

- **`src/main.py`** — FastAPI app with Inngest webhook at `/api/inngest` and health check at `/health`
- **`src/functions/`** — Inngest workflow functions (sync, translate, publish). Each function uses `ctx.step.run()` for idempotent steps and emits events to trigger the next stage
- **`src/services/`** — Business logic: `TwitterService` (syndication API scraping), `TranslatorService` (OpenAI), `XHSService` (Playwright browser automation), `WeChatService` (wechatpy SDK)
- **`src/models/`** — Pydantic dataclasses: `Tweet`, `TweetMedia`, `SyncRecord`, `SyncStatus`
- **`src/persistence/database.py`** — SQLAlchemy async ORM with SQLite, global singleton via `get_db()`
- **`src/config.py`** — Pydantic Settings with YAML base config + env var overrides (prefixed: `TWITTER_`, `OPENAI_`, `WECHAT_`, `XHS_`, `DATABASE_`, `INNGEST_`)

### Configuration Loading Order

1. Pydantic model defaults → 2. `config/config.yaml` → 3. Environment variables → 4. Runtime overrides

### Key Technical Decisions

- **Twitter**: Uses syndication endpoint (no API key), httpx only (no browser)
- **XHS**: Full Playwright browser required (anti-bot), QR code login, state persisted to `data/browser_state/`
- **WeChat**: Creates drafts only (manual publish required due to broadcast limits)
- **Database**: SQLite via aiosqlite, single-file at `data/posts.db`
- **Inngest functions** are excluded from coverage (`src/functions/*.py`) since they require full integration to test

### Service Initialization Pattern

Services accept optional constructor args, falling back to `get_settings()`. Clients are lazily initialized via properties.

## Testing Conventions

- Fully async tests (`pytest-asyncio` with `asyncio_mode = "auto"`)
- Heavy mocking — no external API calls in tests
- Test names: `TestClassName::test_method_describes_behavior`
