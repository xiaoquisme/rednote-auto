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


def test_twitter_config():
    """Test Twitter config."""
    config = TwitterConfig()
    assert config.bearer_token == ""
    assert config.target_user_ids == []


def test_openai_config():
    """Test OpenAI config."""
    config = OpenAIConfig()
    assert config.model == "gpt-4o"


def test_settings_from_yaml_missing_file():
    """Test loading from non-existent YAML file."""
    settings = Settings.from_yaml(Path("/nonexistent/config.yaml"))
    # Should still work with defaults
    assert settings.sync_interval_minutes == 30
