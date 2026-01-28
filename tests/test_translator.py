"""Tests for translator service."""

import pytest
from unittest.mock import Mock, patch

from src.services.translator_service import TranslatorService


def test_translator_system_prompt():
    """Test that system prompt contains expected instructions."""
    service = TranslatorService()

    assert "中文" in service.SYSTEM_PROMPT
    assert "翻译" in service.SYSTEM_PROMPT


def test_translate_empty_text():
    """Test translating empty text."""
    service = TranslatorService()
    result = service.translate("")

    assert result == ""


def test_translate_whitespace_only():
    """Test translating whitespace-only text."""
    service = TranslatorService()
    result = service.translate("   ")

    assert result == ""


@patch("src.services.translator_service.OpenAI")
def test_translate_calls_openai(mock_openai_class):
    """Test that translate calls OpenAI API correctly."""
    # Setup mock
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "你好世界"
    mock_client.chat.completions.create.return_value = mock_response

    # Create service and translate
    service = TranslatorService(api_key="test-key")
    result = service.translate("Hello world")

    # Verify
    assert result == "你好世界"
    mock_client.chat.completions.create.assert_called_once()
