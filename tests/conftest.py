"""
Pytest configuration and shared fixtures.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings with test values."""
    return Settings(
        groq_api_key="test-groq-key",
        huggingfacehub_api_token="test-hf-token",
        tavily_api_key="test-tavily-key",
        llm_model_name="test-model",
        llm_temperature=0.5,
        memory_window_size=5,
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns predictable responses."""
    from langchain_core.messages import AIMessage

    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="This is a test response."))
    mock.invoke = MagicMock(return_value=AIMessage(content="This is a test response."))
    return mock


@pytest.fixture
def client(mock_llm):
    """Create a FastAPI test client with mocked LLM."""
    with patch("backend.services.chat_service.create_llm", return_value=mock_llm):
        with patch("backend.services.search_service.search_web", new_callable=AsyncMock, return_value=[]):
            from backend.main import app
            with TestClient(app) as c:
                yield c


@pytest.fixture(autouse=True)
def clear_memory_store():
    """Clear memory store before each test."""
    from backend.services.memory_service import _session_store
    _session_store.clear()
    yield
    _session_store.clear()


@pytest.fixture(autouse=True)
def clear_llm_cache():
    """Clear LLM cache before each test."""
    from backend.services.chat_service import _llm_cache
    _llm_cache.clear()
    yield
    _llm_cache.clear()
