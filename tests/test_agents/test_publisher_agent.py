"""Tests for publisher agents."""

import json
from unittest.mock import patch

import pytest

from src.agents.publisher_agent import (
    XHS_PUBLISHER_SYSTEM_PROMPT,
    WECHAT_PUBLISHER_SYSTEM_PROMPT,
    run_xhs_publisher_agent,
    run_wechat_publisher_agent,
)


class TestRunXhsPublisherAgent:
    """Tests for run_xhs_publisher_agent."""

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_publishes_successfully(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "post_id": "abc123", "login_required": False}
        )

        result = await run_xhs_publisher_agent(
            title="测试标题", content="测试内容"
        )

        assert result["success"] is True
        assert result["post_id"] == "abc123"
        assert result["login_required"] is False

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_passes_correct_system_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "post_id": "abc123", "login_required": False}
        )

        await run_xhs_publisher_agent(title="测试", content="内容")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["system_prompt"] == XHS_PUBLISHER_SYSTEM_PROMPT

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_includes_title_and_content_in_prompt(
        self, mock_run_agent, mock_settings
    ):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "post_id": None, "login_required": False}
        )

        await run_xhs_publisher_agent(title="我的标题", content="我的内容")

        call_kwargs = mock_run_agent.call_args
        prompt = call_kwargs.kwargs["prompt"]
        assert "我的标题" in prompt
        assert "我的内容" in prompt

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_includes_images_in_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "post_id": None, "login_required": False}
        )

        await run_xhs_publisher_agent(
            title="测试", content="内容", images=["/tmp/img1.jpg", "/tmp/img2.jpg"]
        )

        call_kwargs = mock_run_agent.call_args
        prompt = call_kwargs.kwargs["prompt"]
        assert "/tmp/img1.jpg" in prompt
        assert "/tmp/img2.jpg" in prompt

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_handles_login_required(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {
                "success": False,
                "post_id": None,
                "login_required": True,
                "error": "需要登录小红书创作者平台",
            }
        )

        result = await run_xhs_publisher_agent(title="测试", content="内容")

        assert result["success"] is False
        assert result["login_required"] is True

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_handles_agent_failure(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.side_effect = Exception("Browser timeout")

        result = await run_xhs_publisher_agent(title="测试", content="内容")

        assert result["success"] is False
        assert result["post_id"] is None
        assert "Browser timeout" in result["error"]

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_passes_mcp_servers(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "post_id": None, "login_required": False}
        )

        await run_xhs_publisher_agent(title="测试", content="内容")

        call_kwargs = mock_run_agent.call_args
        mcp_servers = call_kwargs.kwargs["mcp_servers"]
        assert "browser" in mcp_servers
        assert mcp_servers["browser"]["type"] == "stdio"


class TestRunWechatPublisherAgent:
    """Tests for run_wechat_publisher_agent."""

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_creates_draft_successfully(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "media_id": "media_123", "login_required": False}
        )

        result = await run_wechat_publisher_agent(
            title="测试文章", content="文章内容"
        )

        assert result["success"] is True
        assert result["media_id"] == "media_123"
        assert result["login_required"] is False

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_passes_correct_system_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "media_id": None, "login_required": False}
        )

        await run_wechat_publisher_agent(title="测试", content="内容")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["system_prompt"] == WECHAT_PUBLISHER_SYSTEM_PROMPT

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_includes_title_and_content_in_prompt(
        self, mock_run_agent, mock_settings
    ):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "media_id": None, "login_required": False}
        )

        await run_wechat_publisher_agent(title="我的标题", content="我的内容")

        call_kwargs = mock_run_agent.call_args
        prompt = call_kwargs.kwargs["prompt"]
        assert "我的标题" in prompt
        assert "我的内容" in prompt

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_includes_original_text_in_prompt(
        self, mock_run_agent, mock_settings
    ):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "media_id": None, "login_required": False}
        )

        await run_wechat_publisher_agent(
            title="测试", content="内容", original_text="Original English text"
        )

        call_kwargs = mock_run_agent.call_args
        prompt = call_kwargs.kwargs["prompt"]
        assert "Original English text" in prompt

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_handles_login_required(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {
                "success": False,
                "media_id": None,
                "login_required": True,
                "error": "需要登录微信公众平台",
            }
        )

        result = await run_wechat_publisher_agent(title="测试", content="内容")

        assert result["success"] is False
        assert result["login_required"] is True

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_handles_agent_failure(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.side_effect = Exception("Network error")

        result = await run_wechat_publisher_agent(title="测试", content="内容")

        assert result["success"] is False
        assert result["media_id"] is None
        assert "Network error" in result["error"]

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_passes_mcp_servers(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "media_id": None, "login_required": False}
        )

        await run_wechat_publisher_agent(title="测试", content="内容")

        call_kwargs = mock_run_agent.call_args
        mcp_servers = call_kwargs.kwargs["mcp_servers"]
        assert "browser" in mcp_servers
        assert mcp_servers["browser"]["type"] == "stdio"

    @patch("src.agents.publisher_agent.get_settings")
    @patch("src.agents.publisher_agent.run_agent")
    async def test_handles_malformed_json(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = "Not JSON"

        result = await run_wechat_publisher_agent(title="测试", content="内容")

        assert result["success"] is False
        assert result["media_id"] is None
