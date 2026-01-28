"""Tests for main FastAPI application."""

import pytest
from unittest.mock import patch, AsyncMock, Mock

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @patch("src.main.get_db")
    def test_health_check(self, mock_get_db):
        """Test health check endpoint returns ok."""
        mock_db = Mock()
        mock_db.init_db = AsyncMock()
        mock_db.close = AsyncMock()
        mock_get_db.return_value = mock_db

        from src.main import app
        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "rednote-auto"


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_title(self):
        """Test app has correct title."""
        from src.main import app
        assert app.title == "RedNote Auto"

    def test_app_version(self):
        """Test app has version."""
        from src.main import app
        assert app.version == "0.1.0"

    def test_app_description(self):
        """Test app has description."""
        from src.main import app
        assert "小红书" in app.description or "sync" in app.description.lower()


class TestLifespan:
    """Tests for application lifespan."""

    @patch("src.main.get_db")
    async def test_lifespan_initializes_db(self, mock_get_db):
        """Test that lifespan initializes database."""
        mock_db = Mock()
        mock_db.init_db = AsyncMock()
        mock_db.close = AsyncMock()
        mock_get_db.return_value = mock_db

        from src.main import lifespan, app

        async with lifespan(app):
            pass

        mock_db.init_db.assert_called_once()
        mock_db.close.assert_called_once()
