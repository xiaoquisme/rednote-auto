"""微信公众号 publishing service using wechatpy."""

from typing import Optional

from wechatpy import WeChatClient

from src.config import get_settings


class WeChatService:
    """Service for publishing content to 微信公众号."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        """Initialize WeChat client."""
        settings = get_settings()
        self.app_id = app_id or settings.wechat.app_id
        self.app_secret = app_secret or settings.wechat.app_secret
        self._client: Optional[WeChatClient] = None

    @property
    def client(self) -> WeChatClient:
        """Get or create the WeChat client."""
        if self._client is None:
            self._client = WeChatClient(self.app_id, self.app_secret)
        return self._client

    def format_article_content(
        self,
        translated_text: str,
        original_text: str,
        author: Optional[str] = None,
    ) -> str:
        """
        Format content for WeChat article.

        Args:
            translated_text: Translated Chinese text
            original_text: Original English text
            author: Original author name

        Returns:
            Formatted HTML content
        """
        author_line = f"<p><strong>原作者：</strong>{author}</p>" if author else ""

        return f"""
<section>
    {author_line}
    <h2>内容</h2>
    <p>{translated_text}</p>

    <hr/>

    <h3>原文 (Original)</h3>
    <p style="color: #666; font-style: italic;">{original_text}</p>

    <hr/>
    <p style="font-size: 12px; color: #999;">
        本文由 X (Twitter) 内容自动翻译同步。
    </p>
</section>
        """.strip()

    def create_draft_article(
        self,
        title: str,
        content: str,
        thumb_media_id: Optional[str] = None,
        author: Optional[str] = None,
        digest: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a draft article in WeChat.

        Note: Due to WeChat restrictions, articles are created as drafts.
        Manual review and publishing is required.

        Args:
            title: Article title
            content: HTML content
            thumb_media_id: Cover image media ID (optional)
            author: Article author
            digest: Article summary

        Returns:
            Draft media_id if successful, None otherwise
        """
        try:
            # Build article data
            article = {
                "title": title,
                "content": content,
                "content_source_url": "",  # Optional source URL
                "need_open_comment": 0,  # Disable comments
                "only_fans_can_comment": 0,
            }

            if thumb_media_id:
                article["thumb_media_id"] = thumb_media_id
            if author:
                article["author"] = author
            if digest:
                article["digest"] = digest

            # Create draft
            result = self.client.draft.add(articles=[article])
            return result.get("media_id")

        except Exception as e:
            print(f"Failed to create WeChat draft: {e}")
            return None

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to WeChat and get media_id.

        Args:
            image_path: Path to image file

        Returns:
            media_id if successful, None otherwise
        """
        try:
            with open(image_path, "rb") as f:
                result = self.client.material.add(
                    media_type="image",
                    media_file=f,
                )
                return result.get("media_id")
        except Exception as e:
            print(f"Failed to upload image: {e}")
            return None

    def get_draft_count(self) -> int:
        """Get the count of draft articles."""
        try:
            result = self.client.draft.count()
            return result.get("total_count", 0)
        except Exception:
            return 0
