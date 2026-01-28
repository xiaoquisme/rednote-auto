"""Configuration management for rednote-auto."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TwitterConfig(BaseSettings):
    """Twitter API configuration."""

    bearer_token: str = Field(default="")
    target_user_ids: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_prefix="TWITTER_")


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(default="")
    model: str = Field(default="gpt-4o")

    model_config = SettingsConfigDict(env_prefix="OPENAI_")


class WeChatConfig(BaseSettings):
    """WeChat Official Account configuration."""

    app_id: str = Field(default="")
    app_secret: str = Field(default="")

    model_config = SettingsConfigDict(env_prefix="WECHAT_")


class XHSConfig(BaseSettings):
    """小红书 configuration."""

    browser_state_dir: Path = Field(default=Path("data/browser_state"))
    headless: bool = Field(default=True)

    model_config = SettingsConfigDict(env_prefix="XHS_")


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = Field(default="sqlite+aiosqlite:///data/posts.db")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class InngestConfig(BaseSettings):
    """Inngest configuration."""

    app_id: str = Field(default="rednote-auto")
    is_production: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="INNGEST_")


class Settings(BaseSettings):
    """Application settings."""

    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    wechat: WeChatConfig = Field(default_factory=WeChatConfig)
    xhs: XHSConfig = Field(default_factory=XHSConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    inngest: InngestConfig = Field(default_factory=InngestConfig)

    # Sync settings
    sync_interval_minutes: int = Field(default=30)
    enabled_platforms: list[str] = Field(default_factory=lambda: ["xhs", "wechat"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    @classmethod
    def from_yaml(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from YAML file, with env overrides."""
        config_path = config_path or Path("config/config.yaml")

        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}

        return cls(**yaml_config)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml()
    return _settings
