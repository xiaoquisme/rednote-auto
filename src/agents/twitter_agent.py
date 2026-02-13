"""Twitter browsing agent using Claude Code SDK."""

import logging
from typing import Any, Optional

from src.agents.base import (
    build_playwright_mcp_config,
    parse_json_from_response,
    run_agent,
)
from src.config import get_settings

logger = logging.getLogger(__name__)

TWITTER_SYSTEM_PROMPT = """你是一个 Twitter 数据采集助手。你的任务是使用浏览器访问 X (Twitter) 用户的主页，提取他们最近的推文。

操作步骤：
1. 使用浏览器导航到用户的 Twitter 主页 (x.com/{username})
2. 等待页面加载完成
3. 提取页面上可见的推文信息
4. 跳过转推 (retweet)，只提取原创推文

对于每条推文，提取以下信息：
- id: 推文 ID（从推文链接中提取，格式为纯数字字符串）
- text: 推文文本内容
- author_id: 作者用户名
- created_at: 发布时间（ISO 8601 格式）
- media: 媒体列表（图片/视频的 URL）
- is_retweet: 是否为转推（应该都是 false，因为我们跳过转推）

你必须以如下 JSON 格式返回结果：
```json
{
  "success": true,
  "username": "用户名",
  "tweets": [
    {
      "id": "推文ID",
      "text": "推文内容",
      "author_id": "作者ID",
      "created_at": "2024-01-01T00:00:00Z",
      "media": [],
      "is_retweet": false
    }
  ]
}
```

如果出错，返回：
```json
{
  "success": false,
  "username": "用户名",
  "tweets": [],
  "error": "错误描述"
}
```

重要：
- 只返回 JSON，不要添加其他解释
- 跳过所有转推
- 如果需要登录才能查看，在 error 中说明"""


async def run_twitter_agent(
    username: str,
    since_id: Optional[str] = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Fetch tweets from a Twitter user using a browser agent.

    Args:
        username: Twitter username (without @).
        since_id: Only return tweets newer than this ID.
        max_results: Maximum number of tweets to return.

    Returns:
        Dict with keys: success, username, tweets[], error (optional).
    """
    settings = get_settings()
    headless = settings.agent.headless

    since_instruction = ""
    if since_id:
        since_instruction = f"\n注意：只提取 ID 大于 {since_id} 的推文。"

    prompt = (
        f"请访问 x.com/{username} 并提取最近的 {max_results} 条原创推文（跳过转推）。"
        f"{since_instruction}"
    )

    mcp_servers = {"browser": build_playwright_mcp_config(headless=headless)}

    try:
        response = await run_agent(
            prompt=prompt,
            system_prompt=TWITTER_SYSTEM_PROMPT,
            mcp_servers=mcp_servers,
        )

        result = parse_json_from_response(response)
        return {
            "success": result.get("success", True),
            "username": result.get("username", username),
            "tweets": result.get("tweets", []),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.exception("Twitter agent failed for @%s", username)
        return {
            "success": False,
            "username": username,
            "tweets": [],
            "error": str(e),
        }
