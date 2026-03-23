"""
Tests for /health endpoint.
"""


def test_health_returns_200(client):
    """Health endpoint returns 200 with expected fields."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "llm_provider" in data
    assert "web_search_available" in data
    assert "timestamp" in data


def test_health_shows_provider(client):
    """Health endpoint reports the active LLM provider."""
    response = client.get("/health")
    data = response.json()
    # With mock settings, groq should be detected
    assert data["llm_provider"] in ("groq", "huggingface", "none")
