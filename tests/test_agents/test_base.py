"""Tests for agent base utilities."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base import (
    build_playwright_mcp_config,
    parse_json_from_response,
    run_agent,
)


class TestParseJsonFromResponse:
    """Tests for parse_json_from_response."""

    def test_parse_raw_json(self):
        text = '{"success": true, "data": "hello"}'
        result = parse_json_from_response(text)
        assert result == {"success": True, "data": "hello"}

    def test_parse_json_from_code_fence(self):
        text = 'Here is the result:\n```json\n{"success": true, "count": 5}\n```\nDone.'
        result = parse_json_from_response(text)
        assert result == {"success": True, "count": 5}

    def test_parse_json_embedded_in_text(self):
        text = 'The result is {"success": true, "value": 42} as expected.'
        result = parse_json_from_response(text)
        assert result == {"success": True, "value": 42}

    def test_parse_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty response text"):
            parse_json_from_response("")

    def test_parse_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty response text"):
            parse_json_from_response("   \n  ")

    def test_parse_no_json_raises(self):
        with pytest.raises(ValueError, match="No valid JSON found"):
            parse_json_from_response("This is just plain text with no JSON.")

    def test_parse_complex_nested_json(self):
        data = {"success": True, "tweets": [{"id": "1", "text": "hello"}]}
        text = f"```json\n{json.dumps(data)}\n```"
        result = parse_json_from_response(text)
        assert result == data

    def test_parse_json_with_surrounding_whitespace(self):
        text = '  \n  {"key": "value"}  \n  '
        result = parse_json_from_response(text)
        assert result == {"key": "value"}

    def test_fence_takes_precedence_over_raw(self):
        """When both fence and raw JSON exist, fence is preferred."""
        text = '{"outer": 1}\n```json\n{"inner": 2}\n```'
        result = parse_json_from_response(text)
        assert result == {"inner": 2}


class TestBuildPlaywrightMcpConfig:
    """Tests for build_playwright_mcp_config."""

    def test_headless_mode(self):
        config = build_playwright_mcp_config(headless=True)
        assert config["type"] == "stdio"
        assert config["command"] == "npx"
        assert "@anthropic-ai/playwright-mcp@latest" in config["args"]
        assert "--headless" in config["args"]

    def test_non_headless_mode(self):
        config = build_playwright_mcp_config(headless=False)
        assert config["type"] == "stdio"
        assert config["command"] == "npx"
        assert "@anthropic-ai/playwright-mcp@latest" in config["args"]
        assert "--headless" not in config["args"]

    def test_default_is_headless(self):
        config = build_playwright_mcp_config()
        assert "--headless" in config["args"]


class TestRunAgent:
    """Tests for run_agent."""

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_returns_final_text_from_result_message(
        self, mock_query, mock_settings
    ):
        mock_settings.return_value.agent.max_turns = 10

        result_msg = MagicMock()
        result_msg.__class__ = type("ResultMessage", (), {})
        text_block = MagicMock()
        text_block.text = '{"success": true}'
        # Make isinstance checks work
        from claude_code_sdk import ResultMessage, TextBlock

        result_msg = MagicMock(spec=ResultMessage)
        result_msg.content = [MagicMock(spec=TextBlock)]
        result_msg.content[0].text = '{"success": true}'

        async def mock_query_iter(*args, **kwargs):
            yield result_msg

        mock_query.side_effect = mock_query_iter

        result = await run_agent(
            prompt="test prompt",
            system_prompt="test system",
        )
        assert result == '{"success": true}'

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_returns_assistant_text_when_no_result(
        self, mock_query, mock_settings
    ):
        mock_settings.return_value.agent.max_turns = 10

        from claude_code_sdk import AssistantMessage, TextBlock

        assistant_msg = MagicMock(spec=AssistantMessage)
        assistant_msg.content = [MagicMock(spec=TextBlock)]
        assistant_msg.content[0].text = "fallback text"

        async def mock_query_iter(*args, **kwargs):
            yield assistant_msg

        mock_query.side_effect = mock_query_iter

        result = await run_agent(
            prompt="test prompt",
            system_prompt="test system",
        )
        assert result == "fallback text"

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_passes_allowed_tools(self, mock_query, mock_settings):
        mock_settings.return_value.agent.max_turns = 5

        async def mock_query_iter(*args, **kwargs):
            return
            yield  # make it an async generator

        mock_query.side_effect = mock_query_iter

        await run_agent(
            prompt="test",
            system_prompt="test",
            allowed_tools=["Bash", "Read"],
        )

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.allowed_tools == ["Bash", "Read"]

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_passes_mcp_servers(self, mock_query, mock_settings):
        mock_settings.return_value.agent.max_turns = 5

        async def mock_query_iter(*args, **kwargs):
            return
            yield

        mock_query.side_effect = mock_query_iter

        mcp = {"browser": {"type": "stdio", "command": "npx", "args": ["test"]}}
        await run_agent(
            prompt="test",
            system_prompt="test",
            mcp_servers=mcp,
        )

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.mcp_servers == mcp

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_uses_custom_max_turns(self, mock_query, mock_settings):
        mock_settings.return_value.agent.max_turns = 10

        async def mock_query_iter(*args, **kwargs):
            return
            yield

        mock_query.side_effect = mock_query_iter

        await run_agent(
            prompt="test",
            system_prompt="test",
            max_turns=5,
        )

        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.max_turns == 5

    @patch("src.agents.base.get_settings")
    @patch("src.agents.base.query")
    async def test_empty_response_returns_empty_string(
        self, mock_query, mock_settings
    ):
        mock_settings.return_value.agent.max_turns = 10

        async def mock_query_iter(*args, **kwargs):
            return
            yield

        mock_query.side_effect = mock_query_iter

        result = await run_agent(prompt="test", system_prompt="test")
        assert result == ""
