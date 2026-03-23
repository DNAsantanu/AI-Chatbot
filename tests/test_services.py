"""
Tests for backend services.
"""

import pytest

from backend.services.memory_service import (
    clear_memory,
    get_active_sessions,
    get_chat_history,
    get_memory,
    save_messages,
)
from backend.services.prompt_service import create_chat_prompt, format_web_context


# ──────────────────────────────────────────────
# Memory Service Tests
# ──────────────────────────────────────────────

class TestMemoryService:
    """Tests for the memory service."""

    def test_get_memory_creates_new(self):
        """get_memory creates a new memory for unknown session."""
        memory = get_memory("new-session")
        assert memory is not None
        assert len(memory) == 0

    def test_get_memory_returns_same(self):
        """get_memory returns the same memory for the same session."""
        m1 = get_memory("same-session")
        m2 = get_memory("same-session")
        assert m1 is m2

    def test_save_and_retrieve_messages(self):
        """save_messages stores messages retrievable via get_chat_history."""
        save_messages("msg-test", "Hello", "Hi there!")
        history = get_chat_history("msg-test")
        assert len(history) == 2
        assert history[0]["role"] == "human"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    def test_clear_memory(self):
        """clear_memory removes session data."""
        save_messages("clear-test", "msg", "response")
        result = clear_memory("clear-test")
        assert result is True
        assert get_chat_history("clear-test") == []

    def test_clear_nonexistent_returns_false(self):
        """clear_memory returns False for unknown session."""
        assert clear_memory("does-not-exist") is False

    def test_active_sessions(self):
        """get_active_sessions returns all session IDs."""
        get_memory("s1")
        get_memory("s2")
        sessions = get_active_sessions()
        assert "s1" in sessions
        assert "s2" in sessions

    def test_empty_history_for_unknown_session(self):
        """get_chat_history returns empty list for unknown session."""
        assert get_chat_history("unknown") == []


# ──────────────────────────────────────────────
# Prompt Service Tests
# ──────────────────────────────────────────────

class TestPromptService:
    """Tests for the prompt service."""

    def test_create_chat_prompt(self):
        """create_chat_prompt returns a valid prompt template."""
        prompt = create_chat_prompt()
        assert prompt is not None
        # Check it has the expected input variables
        input_vars = prompt.input_variables
        assert "input" in input_vars
        assert "web_context" in input_vars

    def test_format_web_context_empty(self):
        """format_web_context returns empty string for no results."""
        result = format_web_context(None)
        assert result == ""

        result = format_web_context([])
        assert result == ""

    def test_format_web_context_with_results(self):
        """format_web_context formats search results properly."""
        results = [
            {"url": "https://example.com", "content": "Example content"},
            {"url": "https://test.com", "content": "Test content"},
        ]
        formatted = format_web_context(results)
        assert "Web Search Results" in formatted
        assert "https://example.com" in formatted
        assert "Example content" in formatted
        assert "[1]" in formatted
        assert "[2]" in formatted
