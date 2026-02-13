"""Publishing agents for XHS and WeChat using Claude Code SDK."""

import logging
from typing import Any, Optional

from src.agents.base import (
    build_playwright_mcp_config,
    parse_json_from_response,
    run_agent,
)
from src.config import get_settings

logger = logging.getLogger(__name__)

XHS_PUBLISHER_SYSTEM_PROMPT = """你是一个小红书发布助手。你的任务是使用浏览器在小红书创作服务平台发布笔记。

操作步骤：
1. 导航到 creator.xiaohongshu.com/publish/publish
2. 检查是否已登录。如果页面跳转到登录页面，停止操作并返回 login_required: true
3. 如果已登录，在标题栏填入标题
4. 在内容编辑区填入内容
5. 点击「发布」按钮
6. 等待发布成功的提示或页面跳转

你必须以如下 JSON 格式返回结果：
```json
{
  "success": true,
  "post_id": "帖子ID（如果能从成功页面获取）",
  "login_required": false
}
```

如果需要登录：
```json
{
  "success": false,
  "post_id": null,
  "login_required": true,
  "error": "需要登录小红书创作者平台"
}
```

如果发布失败：
```json
{
  "success": false,
  "post_id": null,
  "login_required": false,
  "error": "失败原因"
}
```

重要：
- 只返回 JSON，不要添加其他解释
- 如果检测到登录页面，立即停止并返回 login_required
- 发布前仔细检查标题和内容已正确填入"""


WECHAT_PUBLISHER_SYSTEM_PROMPT = """你是一个微信公众号发布助手。你的任务是使用浏览器在微信公众平台创建草稿文章。

操作步骤：
1. 导航到 mp.weixin.qq.com
2. 检查是否已登录。如果页面显示登录/二维码页面，停止操作并返回 login_required: true
3. 如果已登录，导航到图文消息编辑页面（创作管理 → 图文消息）
4. 填入文章标题
5. 填入文章内容
6. 保存为草稿

你必须以如下 JSON 格式返回结果：
```json
{
  "success": true,
  "media_id": "草稿的media_id（如果能获取）",
  "login_required": false
}
```

如果需要登录：
```json
{
  "success": false,
  "media_id": null,
  "login_required": true,
  "error": "需要登录微信公众平台"
}
```

如果创建失败：
```json
{
  "success": false,
  "media_id": null,
  "login_required": false,
  "error": "失败原因"
}
```

重要：
- 只返回 JSON，不要添加其他解释
- 只创建草稿，不要直接发布
- 如果检测到登录页面，立即停止并返回 login_required"""


async def run_xhs_publisher_agent(
    title: str,
    content: str,
    images: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Publish a note to XHS using a browser agent.

    Args:
        title: Note title.
        content: Note content (Chinese).
        images: Optional list of image file paths.

    Returns:
        Dict with keys: success, post_id, login_required, error (optional).
    """
    settings = get_settings()
    headless = settings.agent.headless

    image_instruction = ""
    if images:
        image_instruction = f"\n同时请上传以下图片：{', '.join(images)}"

    prompt = (
        f"请在小红书发布以下笔记：\n\n"
        f"标题：{title}\n\n"
        f"内容：{content}"
        f"{image_instruction}"
    )

    mcp_servers = {"browser": build_playwright_mcp_config(headless=headless)}

    try:
        response = await run_agent(
            prompt=prompt,
            system_prompt=XHS_PUBLISHER_SYSTEM_PROMPT,
            mcp_servers=mcp_servers,
        )

        result = parse_json_from_response(response)
        return {
            "success": result.get("success", False),
            "post_id": result.get("post_id"),
            "login_required": result.get("login_required", False),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.exception("XHS publisher agent failed")
        return {
            "success": False,
            "post_id": None,
            "login_required": False,
            "error": str(e),
        }


async def run_wechat_publisher_agent(
    title: str,
    content: str,
    original_text: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a draft article on WeChat Official Account using a browser agent.

    Args:
        title: Article title.
        content: Article content (Chinese).
        original_text: Original English text for reference.

    Returns:
        Dict with keys: success, media_id, login_required, error (optional).
    """
    settings = get_settings()
    headless = settings.agent.headless

    original_section = ""
    if original_text:
        original_section = f"\n\n---\n原文 (Original)：\n{original_text}"

    prompt = (
        f"请在微信公众平台创建草稿文章：\n\n"
        f"标题：{title}\n\n"
        f"内容：{content}"
        f"{original_section}"
    )

    mcp_servers = {"browser": build_playwright_mcp_config(headless=headless)}

    try:
        response = await run_agent(
            prompt=prompt,
            system_prompt=WECHAT_PUBLISHER_SYSTEM_PROMPT,
            mcp_servers=mcp_servers,
        )

        result = parse_json_from_response(response)
        return {
            "success": result.get("success", False),
            "media_id": result.get("media_id"),
            "login_required": result.get("login_required", False),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.exception("WeChat publisher agent failed")
        return {
            "success": False,
            "media_id": None,
            "login_required": False,
            "error": str(e),
        }
