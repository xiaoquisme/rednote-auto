"""Configuration management for rednote-auto."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TwitterConfig(BaseSettings):
    """Twitter scraping configuration (Playwright-based)."""

    target_usernames: list[str] = Field(default_factory=list)
    headless: bool = Field(default=True)
    request_delay: float = Field(default=2.0)

    model_config = SettingsConfigDict(
        env_prefix="TWITTER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(default="")
    model: str = Field(default="gpt-4o")
    base_url: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WeChatConfig(BaseSettings):
    """WeChat Official Account configuration."""

    app_id: str = Field(default="")
    app_secret: str = Field(default="")

    model_config = SettingsConfigDict(
        env_prefix="WECHAT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class XHSConfig(BaseSettings):
    """小红书 configuration."""

    browser_state_dir: Path = Field(default=Path("data/browser_state"))
    headless: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_prefix="XHS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = Field(default="sqlite+aiosqlite:///data/posts.db")

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class InngestConfig(BaseSettings):
    """Inngest configuration."""

    app_id: str = Field(default="rednote-auto")
    is_production: bool = Field(default=False)
    dev_server_url: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_prefix="INNGEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Application settings."""

    # Lazy load nested configs to ensure env vars are read at access time
    _twitter: Optional[TwitterConfig] = None
    _openai: Optional[OpenAIConfig] = None
    _wechat: Optional[WeChatConfig] = None
    _xhs: Optional[XHSConfig] = None
    _database: Optional[DatabaseConfig] = None
    _inngest: Optional[InngestConfig] = None

    @property
    def twitter(self) -> TwitterConfig:
        if self._twitter is None:
            self._twitter = TwitterConfig()
        return self._twitter

    @property
    def openai(self) -> OpenAIConfig:
        if self._openai is None:
            self._openai = OpenAIConfig()
        return self._openai

    @property
    def wechat(self) -> WeChatConfig:
        if self._wechat is None:
            self._wechat = WeChatConfig()
        return self._wechat

    @property
    def xhs(self) -> XHSConfig:
        if self._xhs is None:
            self._xhs = XHSConfig()
        return self._xhs

    @property
    def database(self) -> DatabaseConfig:
        if self._database is None:
            self._database = DatabaseConfig()
        return self._database

    @property
    def inngest(self) -> InngestConfig:
        if self._inngest is None:
            self._inngest = InngestConfig()
        return self._inngest

    # Sync settings
    sync_interval_minutes: int = Field(default=30)
    enabled_platforms: list[str] = Field(default_factory=lambda: ["xhs", "wechat"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",  # Ignore env vars meant for nested configs
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
