"""Shared utilities for Claude Code agents."""

import json
import logging
import re
from typing import Any, Optional

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    query,
)

from src.config import get_settings

logger = logging.getLogger(__name__)


async def run_agent(
    prompt: str,
    system_prompt: str,
    allowed_tools: Optional[list[str]] = None,
    mcp_servers: Optional[dict[str, Any]] = None,
    max_turns: Optional[int] = None,
) -> str:
    """
    Run a Claude Code agent and return the final text response.

    Args:
        prompt: The user prompt to send to the agent.
        system_prompt: System instructions for the agent.
        allowed_tools: List of tools the agent is allowed to use.
        mcp_servers: MCP server configurations.
        max_turns: Maximum conversation turns.

    Returns:
        The final text output from the agent.
    """
    settings = get_settings()
    agent_config = settings.agent

    options = ClaudeCodeOptions(
        system_prompt=system_prompt,
        max_turns=max_turns or agent_config.max_turns,
        permission_mode="acceptEdits",
    )

    if allowed_tools is not None:
        options.allowed_tools = allowed_tools

    if mcp_servers is not None:
        options.mcp_servers = mcp_servers

    final_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            # ResultMessage contains the final result
            if hasattr(message, "content"):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        final_text = block.text
        elif isinstance(message, AssistantMessage):
            # Collect assistant text blocks as fallback
            if hasattr(message, "content"):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        final_text = block.text

    return final_text


def parse_json_from_response(text: str) -> dict[str, Any]:
    """
    Extract JSON from agent response text.

    Handles both raw JSON and JSON wrapped in ```json ``` fences.

    Args:
        text: The raw text response from an agent.

    Returns:
        Parsed dictionary from the JSON content.

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    if not text.strip():
        raise ValueError("Empty response text")

    # Try to extract from ```json ``` fences first
    fence_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing the whole text as JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find any JSON object in the text
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in response: {text[:200]}")


def build_playwright_mcp_config(headless: bool = True) -> dict[str, Any]:
    """
    Build MCP server config for @anthropic-ai/playwright-mcp.

    Args:
        headless: Whether to run the browser in headless mode.

    Returns:
        MCP server configuration dictionary.
    """
    args = ["--headless"] if headless else []
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["@anthropic-ai/playwright-mcp@latest", *args],
    }
