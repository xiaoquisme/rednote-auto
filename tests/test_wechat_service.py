"""Tests for WeChat service."""

import pytest
from unittest.mock import Mock, patch, mock_open

from src.services.wechat_service import WeChatService


class TestWeChatService:
    """Tests for WeChatService class."""

    def test_init_with_credentials(self):
        """Test initialization with credentials."""
        service = WeChatService(app_id="test_id", app_secret="test_secret")
        assert service.app_id == "test_id"
        assert service.app_secret == "test_secret"

    @patch("src.services.wechat_service.get_settings")
    def test_init_from_settings(self, mock_get_settings):
        """Test initialization from settings."""
        mock_settings = Mock()
        mock_settings.wechat.app_id = "settings_id"
        mock_settings.wechat.app_secret = "settings_secret"
        mock_get_settings.return_value = mock_settings

        service = WeChatService()
        assert service.app_id == "settings_id"
        assert service.app_secret == "settings_secret"

    @patch("src.services.wechat_service.WeChatClient")
    def test_client_property_creates_client(self, mock_client_class):
        """Test that client property creates a WeChatClient."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="test_id", app_secret="test_secret")
        client = service.client

        mock_client_class.assert_called_once_with("test_id", "test_secret")
        assert client is mock_client

    @patch("src.services.wechat_service.WeChatClient")
    def test_client_property_cached(self, mock_client_class):
        """Test that client is cached."""
        service = WeChatService(app_id="test_id", app_secret="test_secret")

        client1 = service.client
        client2 = service.client

        mock_client_class.assert_called_once()
        assert client1 is client2


class TestFormatArticleContent:
    """Tests for format_article_content method."""

    def test_format_basic_content(self):
        """Test formatting basic content."""
        service = WeChatService(app_id="id", app_secret="secret")

        content = service.format_article_content(
            translated_text="这是翻译的内容",
            original_text="This is the original content",
        )

        assert "这是翻译的内容" in content
        assert "This is the original content" in content
        assert "<section>" in content
        assert "</section>" in content

    def test_format_with_author(self):
        """Test formatting with author name."""
        service = WeChatService(app_id="id", app_secret="secret")

        content = service.format_article_content(
            translated_text="翻译文本",
            original_text="Original text",
            author="TestAuthor",
        )

        assert "TestAuthor" in content
        assert "原作者" in content

    def test_format_without_author(self):
        """Test formatting without author name."""
        service = WeChatService(app_id="id", app_secret="secret")

        content = service.format_article_content(
            translated_text="翻译文本",
            original_text="Original text",
        )

        assert "原作者" not in content


class TestCreateDraftArticle:
    """Tests for create_draft_article method."""

    @patch("src.services.wechat_service.WeChatClient")
    def test_create_draft_success(self, mock_client_class):
        """Test successful draft creation."""
        mock_client = Mock()
        mock_client.draft.add.return_value = {"media_id": "draft_media_id"}
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        result = service.create_draft_article(
            title="Test Title",
            content="<p>Test content</p>",
        )

        assert result == "draft_media_id"
        mock_client.draft.add.assert_called_once()

    @patch("src.services.wechat_service.WeChatClient")
    def test_create_draft_with_all_options(self, mock_client_class):
        """Test draft creation with all options."""
        mock_client = Mock()
        mock_client.draft.add.return_value = {"media_id": "draft_id"}
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        service.create_draft_article(
            title="Title",
            content="Content",
            thumb_media_id="thumb_id",
            author="Author",
            digest="Summary",
        )

        call_args = mock_client.draft.add.call_args
        articles = call_args[1]["articles"]
        assert len(articles) == 1
        assert articles[0]["title"] == "Title"
        assert articles[0]["thumb_media_id"] == "thumb_id"
        assert articles[0]["author"] == "Author"
        assert articles[0]["digest"] == "Summary"

    @patch("src.services.wechat_service.WeChatClient")
    def test_create_draft_failure(self, mock_client_class):
        """Test draft creation failure."""
        mock_client = Mock()
        mock_client.draft.add.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        result = service.create_draft_article(
            title="Title",
            content="Content",
        )

        assert result is None


class TestUploadImage:
    """Tests for upload_image method."""

    @patch("src.services.wechat_service.WeChatClient")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    def test_upload_image_success(self, mock_file, mock_client_class):
        """Test successful image upload."""
        mock_client = Mock()
        mock_client.material.add.return_value = {"media_id": "image_media_id"}
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        result = service.upload_image("/path/to/image.jpg")

        assert result == "image_media_id"
        mock_file.assert_called_once_with("/path/to/image.jpg", "rb")

    @patch("src.services.wechat_service.WeChatClient")
    def test_upload_image_file_not_found(self, mock_client_class):
        """Test upload with non-existent file."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        result = service.upload_image("/nonexistent/path.jpg")

        assert result is None

    @patch("src.services.wechat_service.WeChatClient")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    def test_upload_image_api_error(self, mock_file, mock_client_class):
        """Test upload with API error."""
        mock_client = Mock()
        mock_client.material.add.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        result = service.upload_image("/path/to/image.jpg")

        assert result is None


class TestGetDraftCount:
    """Tests for get_draft_count method."""

    @patch("src.services.wechat_service.WeChatClient")
    def test_get_draft_count_success(self, mock_client_class):
        """Test getting draft count."""
        mock_client = Mock()
        mock_client.draft.count.return_value = {"total_count": 5}
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        count = service.get_draft_count()

        assert count == 5

    @patch("src.services.wechat_service.WeChatClient")
    def test_get_draft_count_error(self, mock_client_class):
        """Test getting draft count with error."""
        mock_client = Mock()
        mock_client.draft.count.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        count = service.get_draft_count()

        assert count == 0

    @patch("src.services.wechat_service.WeChatClient")
    def test_get_draft_count_missing_key(self, mock_client_class):
        """Test getting draft count with missing key in response."""
        mock_client = Mock()
        mock_client.draft.count.return_value = {}
        mock_client_class.return_value = mock_client

        service = WeChatService(app_id="id", app_secret="secret")
        count = service.get_draft_count()

        assert count == 0
