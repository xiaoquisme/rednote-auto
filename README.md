# rednote-auto

Automatically sync X (Twitter) posts to 小红书 (XHS) and WeChat Official Account with AI-powered translation.

## Features

- **Automated Twitter Monitoring**: Fetch new tweets from specified users every 30 minutes
- **AI Translation**: Translate English tweets to natural Chinese using OpenAI GPT
- **Multi-Platform Publishing**: Publish to 小红书 and WeChat Official Account
- **Event-Driven Architecture**: Built with Inngest for reliable workflow orchestration
- **Docker Support**: Easy deployment with Docker Compose

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Inngest Event-Driven Architecture                   │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
    │  sync_twitter    │     │ translate_tweet  │     │ publish_content  │
    │  (Cron: */30 *)  │────▶│ (tweet.fetched)  │────▶│ (tweet.translated)
    └──────────────────┘     └──────────────────┘     └──────────────────┘
            │                        │                        │
            ▼                        ▼                        ▼
    ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
    │  Twitter API     │     │  OpenAI API      │     │  XHS + WeChat    │
    └──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- Twitter API Bearer Token
- OpenAI API Key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rednote-auto

# Install dependencies with uv
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Twitter API
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_TARGET_USER_IDS=["user_id_1","user_id_2"]

# OpenAI API
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=  # Optional: custom API gateway

# WeChat Official Account (optional)
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# XHS
XHS_HEADLESS=true
XHS_BROWSER_STATE_DIR=data/browser_state

# Database
DATABASE_URL=sqlite+aiosqlite:///data/posts.db

# Inngest
INNGEST_APP_ID=rednote-auto
INNGEST_IS_PRODUCTION=false
```

### Running Locally

```bash
# Terminal 1: Start Inngest Dev Server
npx inngest-cli@latest dev

# Terminal 2: Start the application
uv run uvicorn src.main:app --reload --port 8000

# Open Inngest Dashboard
open http://localhost:8288
```

### Running with Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

Access:
- **App**: http://localhost:8000
- **Inngest Dashboard**: http://localhost:8288

## XHS Login Setup

XHS requires browser login via QR code:

```bash
# Local
uv run python scripts/setup_xhs_login.py

# Docker (requires display)
docker compose --profile login run xhs-login
```

## Project Structure

```
rednote-auto/
├── src/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration management
│   ├── inngest_client.py          # Inngest client
│   ├── functions/                 # Inngest functions
│   │   ├── sync_twitter.py        # Fetch tweets (cron)
│   │   ├── translate_tweet.py     # Translate (event)
│   │   └── publish_content.py     # Publish (event)
│   ├── services/                  # Business logic
│   │   ├── twitter_service.py     # Twitter API
│   │   ├── translator_service.py  # OpenAI translation
│   │   ├── xhs_service.py         # 小红书 automation
│   │   └── wechat_service.py      # WeChat SDK
│   ├── models/                    # Data models
│   └── persistence/               # Database
├── scripts/
│   └── setup_xhs_login.py         # XHS login helper
├── tests/                         # Test suite
├── config/                        # YAML configuration
├── data/                          # SQLite DB + browser state
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/inngest` | POST | Inngest webhook |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Tech Stack

- **Framework**: FastAPI
- **Workflow Engine**: Inngest
- **Database**: SQLite + SQLAlchemy (async)
- **Twitter**: tweepy
- **Translation**: OpenAI SDK
- **XHS**: Playwright
- **WeChat**: wechatpy
- **Package Manager**: uv

## Notes

- **XHS**: Uses browser automation (no official API). May violate ToS.
- **WeChat**: Service accounts have limited monthly broadcasts. Creates drafts for manual publishing.
- **Twitter**: Free tier has strict rate limits (~100 requests/day).

## License

MIT
