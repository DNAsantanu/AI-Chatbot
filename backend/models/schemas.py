"""
Pydantic request/response schemas for the API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4096, description="User message")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity. Auto-generated if omitted.",
    )
    use_web_search: bool = Field(
        default=True,
        description="Whether to augment the response with web search results.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Override the default model name.",
    )


# ──────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────

class ChatResponse(BaseModel):
    """Response from the /chat endpoint."""

    response: str = Field(..., description="Assistant response text")
    session_id: str = Field(..., description="Session ID used for this conversation")
    web_search_used: bool = Field(
        default=False,
        description="Whether web search was used to augment the response",
    )
    model: str = Field(..., description="Model used for inference")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageItem(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="Message role: 'human' or 'assistant'")
    content: str = Field(..., description="Message content")


class HistoryResponse(BaseModel):
    """Response from the /history endpoint."""

    session_id: str
    messages: list[MessageItem] = []
    message_count: int = 0


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_provider: str = "unknown"
    web_search_available: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
