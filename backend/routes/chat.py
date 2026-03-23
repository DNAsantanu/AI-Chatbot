"""
Chat Routes — API endpoints for chat and conversation history.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    MessageItem,
)
from backend.services.chat_service import process_chat
from backend.services.memory_service import clear_memory, get_chat_history

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Process a user chat message and return an AI response.

    The response is augmented with web search results if enabled,
    and maintains conversation context through session memory.
    """
    try:
        result = await process_chat(
            message=request.message,
            session_id=request.session_id,
            use_web_search=request.use_web_search,
            model_override=request.model,
        )

        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            web_search_used=result["web_search_used"],
            model=result["model"],
            timestamp=datetime.utcnow(),
        )

    except ValueError as e:
        logger.error("Configuration error: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Service not configured: {e}",
        )
    except RuntimeError as e:
        logger.error("Chat processing failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {e}",
        )
    except Exception as e:
        logger.error("Unexpected error in chat: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        )


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history_endpoint(session_id: str) -> HistoryResponse:
    """Fetch the conversation history for a given session."""
    history = get_chat_history(session_id)
    messages = [MessageItem(role=m["role"], content=m["content"]) for m in history]

    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        message_count=len(messages),
    )


@router.delete("/history/{session_id}")
async def clear_history_endpoint(session_id: str) -> dict:
    """Clear conversation history for a given session."""
    cleared = clear_memory(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": f"Session {session_id} cleared", "success": True}
