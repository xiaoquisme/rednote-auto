"""Tests for Twitter agent."""

import json
from unittest.mock import patch

import pytest

from src.agents.twitter_agent import TWITTER_SYSTEM_PROMPT, run_twitter_agent


class TestRunTwitterAgent:
    """Tests for run_twitter_agent."""

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_fetches_tweets_successfully(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True

        tweets = [
            {
                "id": "123456",
                "text": "Hello world",
                "author_id": "user1",
                "created_at": "2024-01-01T00:00:00Z",
                "media": [],
                "is_retweet": False,
            }
        ]
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": tweets}
        )

        result = await run_twitter_agent("testuser")

        assert result["success"] is True
        assert result["username"] == "testuser"
        assert len(result["tweets"]) == 1
        assert result["tweets"][0]["id"] == "123456"

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_passes_correct_system_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        await run_twitter_agent("testuser")

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs["system_prompt"] == TWITTER_SYSTEM_PROMPT

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_passes_mcp_servers(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        await run_twitter_agent("testuser")

        call_kwargs = mock_run_agent.call_args
        mcp_servers = call_kwargs.kwargs["mcp_servers"]
        assert "browser" in mcp_servers
        assert mcp_servers["browser"]["type"] == "stdio"

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_includes_since_id_in_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        await run_twitter_agent("testuser", since_id="999")

        call_kwargs = mock_run_agent.call_args
        assert "999" in call_kwargs.kwargs["prompt"]

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_includes_max_results_in_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        await run_twitter_agent("testuser", max_results=5)

        call_kwargs = mock_run_agent.call_args
        assert "5" in call_kwargs.kwargs["prompt"]

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_handles_agent_failure(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.side_effect = Exception("Browser crashed")

        result = await run_twitter_agent("testuser")

        assert result["success"] is False
        assert result["username"] == "testuser"
        assert result["tweets"] == []
        assert "Browser crashed" in result["error"]

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_handles_malformed_json(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = "Not valid JSON"

        result = await run_twitter_agent("testuser")

        assert result["success"] is False
        assert result["tweets"] == []

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_handles_empty_tweets(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        result = await run_twitter_agent("testuser")

        assert result["success"] is True
        assert result["tweets"] == []

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_headless_config_passed_to_mcp(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = False
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "testuser", "tweets": []}
        )

        await run_twitter_agent("testuser")

        call_kwargs = mock_run_agent.call_args
        mcp_servers = call_kwargs.kwargs["mcp_servers"]
        # Non-headless should not have --headless flag
        assert "--headless" not in mcp_servers["browser"]["args"]

    @patch("src.agents.twitter_agent.get_settings")
    @patch("src.agents.twitter_agent.run_agent")
    async def test_includes_username_in_prompt(self, mock_run_agent, mock_settings):
        mock_settings.return_value.agent.headless = True
        mock_run_agent.return_value = json.dumps(
            {"success": True, "username": "elonmusk", "tweets": []}
        )

        await run_twitter_agent("elonmusk")

        call_kwargs = mock_run_agent.call_args
        assert "elonmusk" in call_kwargs.kwargs["prompt"]
