"""Translation service using OpenAI."""

from typing import Optional

from openai import OpenAI

from src.config import get_settings


class TranslatorService:
    """Service for translating tweet content to Chinese."""

    SYSTEM_PROMPT = """你是一个专业的翻译专家，专门将英文推文翻译成自然流畅的中文。

翻译要求：
1. 保持原文的语气和风格
2. 对于技术术语，保留英文并在括号中给出中文解释
3. 对于网络流行语和 meme，给出中文等效表达
4. 保留原文中的 @用户名 和 #话题标签
5. URL 链接保持原样
6. 表情符号保留

请直接输出翻译结果，不要添加任何解释。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize OpenAI client."""
        settings = get_settings()
        self.api_key = api_key or settings.openai.api_key
        self.model = model or settings.openai.model
        self.base_url = base_url or settings.openai.base_url
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Get or create the OpenAI client."""
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def translate(self, text: str) -> str:
        """
        Translate English text to Chinese.

        Args:
            text: English text to translate

        Returns:
            Translated Chinese text
        """
        if not text.strip():
            return ""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        return response.choices[0].message.content or ""

    def translate_with_context(
        self,
        text: str,
        author_name: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Translate with additional context for better quality.

        Args:
            text: English text to translate
            author_name: Name of the tweet author for context
            additional_context: Any additional context

        Returns:
            Translated Chinese text
        """
        context_parts = []
        if author_name:
            context_parts.append(f"作者: {author_name}")
        if additional_context:
            context_parts.append(f"背景: {additional_context}")

        context = "\n".join(context_parts)
        prompt = f"{context}\n\n原文:\n{text}" if context else text

        return self.translate(prompt)
