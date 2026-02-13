"""Tests for configuration module."""

import pytest
from pathlib import Path

from src.config import Settings, TwitterConfig, OpenAIConfig


def test_default_settings():
    """Test that settings can be created with defaults."""
    settings = Settings()

    assert settings.sync_interval_minutes == 30
    assert "xhs" in settings.enabled_platforms
    assert "wechat" in settings.enabled_platforms


def test_twitter_config(monkeypatch):
    """Test Twitter config with defaults when no env vars set."""
    monkeypatch.delenv("TWITTER_TARGET_USERNAMES", raising=False)
    monkeypatch.delenv("TWITTER_HEADLESS", raising=False)
    monkeypatch.delenv("TWITTER_REQUEST_DELAY", raising=False)
    config = TwitterConfig(_env_file=None)
    assert config.target_usernames == []
    assert config.headless is True
    assert config.request_delay == 2.0


def test_openai_config(monkeypatch):
    """Test OpenAI config with defaults when no env vars set."""
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    config = OpenAIConfig(_env_file=None)
    assert config.model == "gpt-4o"


def test_settings_from_yaml_missing_file():
    """Test loading from non-existent YAML file."""
    settings = Settings.from_yaml(Path("/nonexistent/config.yaml"))
    # Should still work with defaults
    assert settings.sync_interval_minutes == 30
