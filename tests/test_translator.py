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


@patch("src.services.translator_service.OpenAI")
def test_translate_with_context_author(mock_openai_class):
    """Test translate_with_context with author name."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "翻译结果"
    mock_client.chat.completions.create.return_value = mock_response

    service = TranslatorService(api_key="test-key")
    result = service.translate_with_context(
        text="Hello world",
        author_name="TestAuthor",
    )

    assert result == "翻译结果"
    # Check that the prompt includes author info
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    user_message = messages[1]["content"]
    assert "TestAuthor" in user_message
    assert "作者" in user_message


@patch("src.services.translator_service.OpenAI")
def test_translate_with_context_additional(mock_openai_class):
    """Test translate_with_context with additional context."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "翻译结果"
    mock_client.chat.completions.create.return_value = mock_response

    service = TranslatorService(api_key="test-key")
    result = service.translate_with_context(
        text="Hello world",
        additional_context="This is a tech tweet",
    )

    assert result == "翻译结果"
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    user_message = messages[1]["content"]
    assert "This is a tech tweet" in user_message
    assert "背景" in user_message


@patch("src.services.translator_service.OpenAI")
def test_translate_with_context_no_context(mock_openai_class):
    """Test translate_with_context without any context."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "翻译结果"
    mock_client.chat.completions.create.return_value = mock_response

    service = TranslatorService(api_key="test-key")
    result = service.translate_with_context(text="Hello world")

    assert result == "翻译结果"
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    user_message = messages[1]["content"]
    # Without context, just the text
    assert "作者" not in user_message
    assert "背景" not in user_message


@patch("src.services.translator_service.OpenAI")
def test_translate_with_context_both(mock_openai_class):
    """Test translate_with_context with both author and context."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "翻译结果"
    mock_client.chat.completions.create.return_value = mock_response

    service = TranslatorService(api_key="test-key")
    result = service.translate_with_context(
        text="Hello world",
        author_name="TestAuthor",
        additional_context="Tech context",
    )

    assert result == "翻译结果"
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    user_message = messages[1]["content"]
    assert "TestAuthor" in user_message
    assert "Tech context" in user_message
