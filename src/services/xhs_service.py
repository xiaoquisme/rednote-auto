"""小红书 (XHS) publishing service using Playwright."""

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from src.config import get_settings


class XHSService:
    """Service for publishing content to 小红书 using browser automation."""

    BASE_URL = "https://www.xiaohongshu.com"
    CREATOR_URL = "https://creator.xiaohongshu.com"

    def __init__(
        self,
        browser_state_dir: Optional[Path] = None,
        headless: Optional[bool] = None,
    ):
        """Initialize XHS service."""
        settings = get_settings()
        self.browser_state_dir = browser_state_dir or settings.xhs.browser_state_dir
        self.headless = headless if headless is not None else settings.xhs.headless
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def _ensure_browser(self) -> BrowserContext:
        """Ensure browser and context are initialized."""
        if self._context is not None:
            return self._context

        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=self.headless)

        # Try to load saved state
        state_file = self.browser_state_dir / "xhs_state.json"
        if state_file.exists():
            self._context = await self._browser.new_context(
                storage_state=str(state_file)
            )
        else:
            self._context = await self._browser.new_context()

        return self._context

    async def is_logged_in(self) -> bool:
        """Check if we're logged in to XHS."""
        context = await self._ensure_browser()
        page = await context.new_page()

        try:
            await page.goto(self.CREATOR_URL)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Check if we're on the login page or creator dashboard
            url = page.url
            return "creator.xiaohongshu.com" in url and "login" not in url
        except Exception:
            return False
        finally:
            await page.close()

    async def save_login_state(self) -> None:
        """Save the current browser state for future use."""
        if self._context is None:
            return

        self.browser_state_dir.mkdir(parents=True, exist_ok=True)
        state_file = self.browser_state_dir / "xhs_state.json"
        await self._context.storage_state(path=str(state_file))

    async def login_with_qr(self, timeout: int = 120) -> bool:
        """
        Display QR code for login and wait for user to scan.

        Args:
            timeout: Seconds to wait for login

        Returns:
            True if login successful
        """
        context = await self._ensure_browser()
        page = await context.new_page()

        try:
            await page.goto(f"{self.CREATOR_URL}/login")
            await page.wait_for_load_state("networkidle")

            print("Please scan the QR code in the browser to log in...")
            print(f"Waiting up to {timeout} seconds...")

            # Wait for redirect away from login page (login not in URL)
            await page.wait_for_url(
                lambda url: "creator.xiaohongshu.com" in url and "login" not in url,
                timeout=timeout * 1000,
            )

            # Save state after successful login
            await self.save_login_state()
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
        finally:
            await page.close()

    async def publish_note(
        self,
        title: str,
        content: str,
        images: Optional[list[str]] = None,
    ) -> Optional[str]:
        """
        Publish a note to 小红书.

        Args:
            title: Note title
            content: Note content (Chinese)
            images: List of image file paths or URLs

        Returns:
            Post ID if successful, None otherwise
        """
        if not await self.is_logged_in():
            raise RuntimeError("Not logged in to XHS. Please run login first.")

        context = await self._ensure_browser()
        page = await context.new_page()

        try:
            # Go to publish page
            await page.goto(f"{self.CREATOR_URL}/publish/publish")
            await page.wait_for_load_state("networkidle")

            # Upload images if provided
            if images:
                file_input = page.locator('input[type="file"]').first
                for image_path in images:
                    await file_input.set_input_files(image_path)
                    await asyncio.sleep(2)  # Wait for upload

            # Fill title
            title_input = page.locator('[placeholder*="标题"]').first
            await title_input.fill(title)

            # Fill content
            content_editor = page.locator('[contenteditable="true"]').first
            await content_editor.fill(content)

            # Click publish button
            publish_btn = page.locator('button:has-text("发布")').first
            await publish_btn.click()

            # Wait for success
            await page.wait_for_url(f"{self.CREATOR_URL}/publish/success**", timeout=30000)

            # Extract post ID from success page if possible
            success_url = page.url
            # Note ID would be in the URL or page content
            return success_url.split("/")[-1] if "/" in success_url else None

        except Exception as e:
            print(f"Publish failed: {e}")
            return None
        finally:
            await page.close()

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
