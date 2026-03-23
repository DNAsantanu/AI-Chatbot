"""
Tests for /chat and /history endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage


def test_chat_returns_response(client, mock_llm):
    """Chat endpoint returns a valid response."""
    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        response = client.post("/chat", json={
            "message": "Hello, world!",
            "session_id": "test-session-1",
            "use_web_search": False,
        })

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "test-session-1"
    assert "model" in data
    assert "timestamp" in data


def test_chat_auto_generates_session_id(client, mock_llm):
    """Chat endpoint generates session ID if not provided."""
    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        response = client.post("/chat", json={
            "message": "Hello!",
            "use_web_search": False,
        })

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] is not None
    assert len(data["session_id"]) > 0


def test_chat_empty_message_rejected(client):
    """Chat endpoint rejects empty messages."""
    response = client.post("/chat", json={
        "message": "",
        "use_web_search": False,
    })
    assert response.status_code == 422  # Validation error


def test_history_empty_session(client):
    """History endpoint returns empty list for new session."""
    response = client.get("/history/nonexistent-session")
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []
    assert data["message_count"] == 0


def test_history_after_chat(client, mock_llm):
    """History endpoint returns messages after a chat."""
    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        client.post("/chat", json={
            "message": "Test message",
            "session_id": "history-test",
            "use_web_search": False,
        })

    response = client.get("/history/history-test")
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] == 2  # human + assistant
    assert data["messages"][0]["role"] == "human"
    assert data["messages"][1]["role"] == "assistant"


def test_clear_history(client, mock_llm):
    """Delete endpoint clears session history."""
    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        client.post("/chat", json={
            "message": "Test",
            "session_id": "clear-test",
            "use_web_search": False,
        })

    response = client.delete("/history/clear-test")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify cleared
    response = client.get("/history/clear-test")
    assert response.json()["message_count"] == 0


def test_clear_nonexistent_session(client):
    """Delete endpoint returns 404 for nonexistent session."""
    response = client.delete("/history/does-not-exist")
    assert response.status_code == 404


def test_session_isolation(client, mock_llm):
    """Separate sessions have separate histories."""
    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        client.post("/chat", json={
            "message": "Session A message",
            "session_id": "session-a",
            "use_web_search": False,
        })
        client.post("/chat", json={
            "message": "Session B message",
            "session_id": "session-b",
            "use_web_search": False,
        })

    # Check histories are separate
    resp_a = client.get("/history/session-a")
    resp_b = client.get("/history/session-b")
    assert resp_a.json()["messages"][0]["content"] == "Session A message"
    assert resp_b.json()["messages"][0]["content"] == "Session B message"


def test_chat_with_web_search(client, mock_llm):
    """Chat with web search enabled returns web_search_used flag."""
    mock_search = AsyncMock(return_value=[
        {"url": "https://example.com", "content": "Test result", "title": "Test"}
    ])

    mock_settings = MagicMock()
    mock_settings.tavily_api_key = "test-key"
    mock_settings.llm_model_name = "test-model"
    mock_settings.llm_temperature = 0.5

    with patch("backend.services.chat_service._get_cached_llm", return_value=mock_llm):
        with patch("backend.services.chat_service.search_web", mock_search):
            with patch("backend.services.chat_service.get_settings", return_value=mock_settings):
                response = client.post("/chat", json={
                    "message": "What is the weather?",
                    "session_id": "search-test",
                    "use_web_search": True,
                })

    assert response.status_code == 200
    data = response.json()
    assert data["web_search_used"] is True

