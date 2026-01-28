"""Inngest client initialization."""

import inngest

from src.config import get_settings


def create_inngest_client() -> inngest.Inngest:
    """Create and configure the Inngest client."""
    settings = get_settings()
    return inngest.Inngest(
        app_id=settings.inngest.app_id,
        is_production=settings.inngest.is_production,
    )


# Global client instance
client = create_inngest_client()
