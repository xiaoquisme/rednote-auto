"""Tests for translator agent."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.translator_agent import TRANSLATOR_SYSTEM_PROMPT, run_translator_agent


class TestRunTranslatorAgent:
    """Tests for run_translator_agent."""

    @patch("src.agents.translator_agent.run_agent")
    async def test_translates_text_successfully(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {"success": True, "translated_text": "这是一条测试推文"}
        )

        result = await run_translator_agent("This is a test tweet")

        assert result["success"] is True
        assert result["translated_text"] == "这是一条测试推文"
        assert result["error"] is None

    @patch("src.agents.translator_agent.run_agent")
    async def test_passes_correct_system_prompt(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {"success": True, "translated_text": "你好"}
        )

        await run_translator_agent("Hello")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["system_prompt"] == TRANSLATOR_SYSTEM_PROMPT

    @patch("src.agents.translator_agent.run_agent")
    async def test_uses_no_tools(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {"success": True, "translated_text": "你好"}
        )

        await run_translator_agent("Hello")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["allowed_tools"] == []

    @patch("src.agents.translator_agent.run_agent")
    async def test_uses_single_turn(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {"success": True, "translated_text": "你好"}
        )

        await run_translator_agent("Hello")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["max_turns"] == 1

    @patch("src.agents.translator_agent.run_agent")
    async def test_empty_text_returns_empty(self, mock_run_agent):
        result = await run_translator_agent("")

        assert result["success"] is True
        assert result["translated_text"] == ""
        mock_run_agent.assert_not_called()

    @patch("src.agents.translator_agent.run_agent")
    async def test_whitespace_text_returns_empty(self, mock_run_agent):
        result = await run_translator_agent("   \n  ")

        assert result["success"] is True
        assert result["translated_text"] == ""
        mock_run_agent.assert_not_called()

    @patch("src.agents.translator_agent.run_agent")
    async def test_handles_agent_failure(self, mock_run_agent):
        mock_run_agent.side_effect = Exception("Connection failed")

        result = await run_translator_agent("Hello")

        assert result["success"] is False
        assert result["translated_text"] == ""
        assert "Connection failed" in result["error"]

    @patch("src.agents.translator_agent.run_agent")
    async def test_handles_malformed_json(self, mock_run_agent):
        mock_run_agent.return_value = "This is not JSON at all"

        result = await run_translator_agent("Hello")

        assert result["success"] is False
        assert result["translated_text"] == ""
        assert result["error"] is not None

    @patch("src.agents.translator_agent.run_agent")
    async def test_handles_json_in_code_fence(self, mock_run_agent):
        mock_run_agent.return_value = (
            '```json\n{"success": true, "translated_text": "测试"}\n```'
        )

        result = await run_translator_agent("Test")

        assert result["success"] is True
        assert result["translated_text"] == "测试"

    @patch("src.agents.translator_agent.run_agent")
    async def test_handles_error_response_from_agent(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {
                "success": False,
                "translated_text": "",
                "error": "Translation model error",
            }
        )

        result = await run_translator_agent("Hello")

        assert result["success"] is False
        assert result["translated_text"] == ""
        assert result["error"] == "Translation model error"

    @patch("src.agents.translator_agent.run_agent")
    async def test_includes_text_in_prompt(self, mock_run_agent):
        mock_run_agent.return_value = json.dumps(
            {"success": True, "translated_text": "你好世界"}
        )

        await run_translator_agent("Hello World")

        call_kwargs = mock_run_agent.call_args
        assert "Hello World" in call_kwargs.kwargs["prompt"]
