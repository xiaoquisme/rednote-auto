"""Tests for Inngest client module."""

from unittest.mock import patch, Mock

import inngest

from src.inngest_client import create_inngest_client, client


class TestCreateInngestClient:
    """Tests for create_inngest_client function."""

    @patch("src.inngest_client.get_settings")
    def test_creates_inngest_client(self, mock_get_settings):
        """Test that create_inngest_client creates an Inngest instance."""
        mock_settings = Mock()
        mock_settings.inngest.app_id = "test-app"
        mock_settings.inngest.is_production = False
        mock_get_settings.return_value = mock_settings

        result = create_inngest_client()

        assert isinstance(result, inngest.Inngest)

    @patch("src.inngest_client.get_settings")
    def test_uses_app_id_from_settings(self, mock_get_settings):
        """Test that app_id comes from settings."""
        mock_settings = Mock()
        mock_settings.inngest.app_id = "my-custom-app"
        mock_settings.inngest.is_production = True
        mock_get_settings.return_value = mock_settings

        result = create_inngest_client()

        assert result.app_id == "my-custom-app"


class TestClientInstance:
    """Tests for the global client instance."""

    def test_client_is_inngest_instance(self):
        """Test that client is an Inngest instance."""
        assert isinstance(client, inngest.Inngest)

    def test_client_has_app_id(self):
        """Test that client has an app_id."""
        assert client.app_id is not None
        assert isinstance(client.app_id, str)
