"""Translation agent using Claude Code SDK."""

import logging
from typing import Any

from src.agents.base import parse_json_from_response, run_agent

logger = logging.getLogger(__name__)

TRANSLATOR_SYSTEM_PROMPT = """你是一个专业的翻译专家，专门将英文推文翻译成自然流畅的中文。

翻译要求：
1. 保持原文的语气和风格
2. 对于技术术语，保留英文并在括号中给出中文解释
3. 对于网络流行语和 meme，给出中文等效表达
4. 保留原文中的 @用户名 和 #话题标签
5. URL 链接保持原样
6. 表情符号保留

请直接输出翻译结果，不要添加任何解释。

你必须以如下 JSON 格式返回结果：
```json
{
  "success": true,
  "translated_text": "翻译后的中文文本"
}
```

如果无法翻译，返回：
```json
{
  "success": false,
  "translated_text": "",
  "error": "错误原因"
}
```"""


async def run_translator_agent(text: str) -> dict[str, Any]:
    """
    Translate English text to Chinese using a Claude agent.

    Args:
        text: English text to translate.

    Returns:
        Dict with keys: success, translated_text, error (optional).
    """
    if not text.strip():
        return {"success": True, "translated_text": ""}

    try:
        response = await run_agent(
            prompt=f"请翻译以下英文文本为中文：\n\n{text}",
            system_prompt=TRANSLATOR_SYSTEM_PROMPT,
            allowed_tools=[],
            max_turns=1,
        )

        result = parse_json_from_response(response)
        return {
            "success": result.get("success", True),
            "translated_text": result.get("translated_text", ""),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.exception("Translator agent failed")
        return {
            "success": False,
            "translated_text": "",
            "error": str(e),
        }
