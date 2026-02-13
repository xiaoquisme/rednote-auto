"""Tests for XHS (小红书) service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.services.xhs_service import XHSService


class TestXHSService:
    """Tests for XHSService class."""

    def test_init_with_params(self):
        """Test initialization with parameters."""
        service = XHSService(
            browser_state_dir=Path("/custom/path"),
            headless=False,
        )
        assert service.browser_state_dir == Path("/custom/path")
        assert service.headless is False

    @patch("src.services.xhs_service.get_settings")
    def test_init_from_settings(self, mock_get_settings):
        """Test initialization from settings."""
        mock_settings = Mock()
        mock_settings.xhs.browser_state_dir = Path("/settings/path")
        mock_settings.xhs.headless = True
        mock_get_settings.return_value = mock_settings

        service = XHSService()
        assert service.browser_state_dir == Path("/settings/path")
        assert service.headless is True

    def test_base_url(self):
        """Test base URL constants."""
        assert XHSService.BASE_URL == "https://www.xiaohongshu.com"
        assert XHSService.CREATOR_URL == "https://creator.xiaohongshu.com"


class TestEnsureBrowser:
    """Tests for _ensure_browser method."""

    @patch("src.services.xhs_service.async_playwright")
    async def test_ensure_browser_creates_browser(self, mock_async_playwright):
        """Test that _ensure_browser creates a browser."""
        # Setup mocks
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        service = XHSService(
            browser_state_dir=Path("/tmp/nonexistent"),
            headless=True,
        )

        result = await service._ensure_browser()

        assert result is mock_context
        mock_playwright.chromium.launch.assert_called_once_with(headless=True)

    @patch("src.services.xhs_service.async_playwright")
    async def test_ensure_browser_cached(self, mock_async_playwright):
        """Test that browser context is cached."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        service = XHSService(
            browser_state_dir=Path("/tmp/nonexistent"),
            headless=True,
        )

        result1 = await service._ensure_browser()
        result2 = await service._ensure_browser()

        assert result1 is result2
        # Launch should only be called once
        mock_playwright.chromium.launch.assert_called_once()

    @patch("src.services.xhs_service.async_playwright")
    async def test_ensure_browser_loads_saved_state(self, mock_async_playwright):
        """Test loading saved browser state."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Create a temp directory with state file
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            state_file = state_dir / "xhs_state.json"
            state_file.write_text(json.dumps({"cookies": []}))

            service = XHSService(
                browser_state_dir=state_dir,
                headless=True,
            )

            await service._ensure_browser()

            # Should be called with storage_state
            call_kwargs = mock_browser.new_context.call_args[1]
            assert "storage_state" in call_kwargs


class TestIsLoggedIn:
    """Tests for is_logged_in method."""

    @patch("src.services.xhs_service.async_playwright")
    async def test_is_logged_in_true(self, mock_async_playwright):
        """Test is_logged_in returns True when logged in."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Simulate logged in - URL is creator dashboard
        mock_page.url = "https://creator.xiaohongshu.com/publish/publish"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/nonexistent"),
            headless=True,
        )

        result = await service.is_logged_in()

        assert result is True
        mock_page.close.assert_called_once()

    @patch("src.services.xhs_service.async_playwright")
    async def test_is_logged_in_false_on_login_page(self, mock_async_playwright):
        """Test is_logged_in returns False on login page."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Simulate login page URL
        mock_page.url = "https://creator.xiaohongshu.com/login"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/nonexistent"),
            headless=True,
        )

        result = await service.is_logged_in()

        assert result is False

    @patch("src.services.xhs_service.async_playwright")
    async def test_is_logged_in_false_on_error(self, mock_async_playwright):
        """Test is_logged_in returns False on error."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Simulate error
        mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
        mock_page.close = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/nonexistent"),
            headless=True,
        )

        result = await service.is_logged_in()

        assert result is False


class TestSaveLoginState:
    """Tests for save_login_state method."""

    async def test_save_login_state_no_context(self):
        """Test save_login_state with no context does nothing."""
        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )
        # Should not raise
        await service.save_login_state()

    @patch("src.services.xhs_service.async_playwright")
    async def test_save_login_state_saves_state(self, mock_async_playwright):
        """Test save_login_state saves browser state."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.storage_state = AsyncMock()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = XHSService(
                browser_state_dir=Path(tmpdir),
                headless=True,
            )

            # Initialize browser
            await service._ensure_browser()

            # Save state
            await service.save_login_state()

            # Should have called storage_state
            mock_context.storage_state.assert_called_once()


class TestLoginWithQr:
    """Tests for login_with_qr method."""

    @patch("src.services.xhs_service.async_playwright")
    async def test_login_with_qr_success(self, mock_async_playwright):
        """Test successful QR login."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.storage_state = AsyncMock()

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.wait_for_url = AsyncMock()
        mock_page.close = AsyncMock()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = XHSService(
                browser_state_dir=Path(tmpdir),
                headless=False,
            )

            result = await service.login_with_qr(timeout=30)

            assert result is True
            mock_page.goto.assert_called()

    @patch("src.services.xhs_service.async_playwright")
    async def test_login_with_qr_timeout(self, mock_async_playwright):
        """Test QR login timeout."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.wait_for_url = AsyncMock(side_effect=Exception("Timeout"))
        mock_page.close = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=False,
        )

        result = await service.login_with_qr(timeout=1)

        assert result is False


class TestPublishNote:
    """Tests for publish_note method."""

    @patch("src.services.xhs_service.async_playwright")
    async def test_publish_note_not_logged_in(self, mock_async_playwright):
        """Test publish_note raises error when not logged in."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Simulate not logged in
        mock_page.url = "https://creator.xiaohongshu.com/login"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        with pytest.raises(RuntimeError, match="Not logged in"):
            await service.publish_note(
                title="Test",
                content="Test content",
            )

    @patch("src.services.xhs_service.async_playwright")
    @patch("src.services.xhs_service.asyncio")
    async def test_publish_note_success(self, mock_asyncio, mock_async_playwright):
        """Test successful note publishing."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page2 = AsyncMock()
        mock_locator = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # First page for login check (logged in)
        mock_page.url = "https://creator.xiaohongshu.com/publish/publish"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        # Second page for actual publish
        mock_page2.url = "https://creator.xiaohongshu.com/publish/success/12345"
        mock_page2.goto = AsyncMock()
        mock_page2.wait_for_load_state = AsyncMock()
        mock_page2.wait_for_url = AsyncMock()
        mock_page2.close = AsyncMock()
        mock_page2.screenshot = AsyncMock()
        mock_page2.locator = Mock(return_value=mock_locator)
        mock_locator.first = mock_locator
        mock_locator.fill = AsyncMock()
        mock_locator.click = AsyncMock()
        mock_locator.set_input_files = AsyncMock()

        mock_context.new_page = AsyncMock(side_effect=[mock_page, mock_page2])
        mock_asyncio.sleep = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        result = await service.publish_note(
            title="Test Title",
            content="Test content",
        )

        assert result is not None
        mock_page2.close.assert_called_once()

    @patch("src.services.xhs_service.async_playwright")
    @patch("src.services.xhs_service.asyncio")
    async def test_publish_note_with_images(self, mock_asyncio, mock_async_playwright):
        """Test note publishing with images."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page2 = AsyncMock()
        mock_locator = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        mock_page.url = "https://creator.xiaohongshu.com/publish/publish"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        mock_page2.url = "https://creator.xiaohongshu.com/publish/success/12345"
        mock_page2.goto = AsyncMock()
        mock_page2.wait_for_load_state = AsyncMock()
        mock_page2.wait_for_url = AsyncMock()
        mock_page2.close = AsyncMock()
        mock_page2.screenshot = AsyncMock()
        mock_page2.locator = Mock(return_value=mock_locator)
        mock_locator.first = mock_locator
        mock_locator.fill = AsyncMock()
        mock_locator.click = AsyncMock()
        mock_locator.set_input_files = AsyncMock()

        mock_context.new_page = AsyncMock(side_effect=[mock_page, mock_page2])
        mock_asyncio.sleep = AsyncMock()

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        result = await service.publish_note(
            title="Test Title",
            content="Test content",
            images=["/path/to/image1.jpg", "/path/to/image2.jpg"],
        )

        assert result is not None
        # Verify set_input_files was called for each image
        assert mock_locator.set_input_files.call_count == 2

    @patch("src.services.xhs_service.async_playwright")
    async def test_publish_note_failure(self, mock_async_playwright):
        """Test publish_note failure handling."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page2 = AsyncMock()
        mock_locator = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        mock_page.url = "https://creator.xiaohongshu.com/publish/publish"
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.close = AsyncMock()

        mock_page2.goto = AsyncMock()
        mock_page2.wait_for_load_state = AsyncMock()
        mock_page2.screenshot = AsyncMock()
        mock_page2.locator = Mock(return_value=mock_locator)
        mock_locator.first = mock_locator
        mock_locator.fill = AsyncMock()
        mock_locator.click = AsyncMock(side_effect=Exception("Click failed"))
        mock_page2.close = AsyncMock()

        mock_context.new_page = AsyncMock(side_effect=[mock_page, mock_page2])

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        with pytest.raises(Exception, match="Click failed"):
            await service.publish_note(
                title="Test Title",
                content="Test content",
            )
        mock_page2.close.assert_called_once()


class TestClose:
    """Tests for close method."""

    @patch("src.services.xhs_service.async_playwright")
    async def test_close_cleans_up(self, mock_async_playwright):
        """Test close cleans up browser resources."""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        # Initialize browser
        await service._ensure_browser()

        # Close
        await service.close()

        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        assert service._context is None
        assert service._browser is None

    async def test_close_no_browser(self):
        """Test close with no browser does nothing."""
        service = XHSService(
            browser_state_dir=Path("/tmp/test"),
            headless=True,
        )

        # Should not raise
        await service.close()
