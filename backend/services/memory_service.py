"""
Memory Service — Session-based conversation memory management.
Uses a simple windowed message store with LangChain message objects.
"""

import logging
from collections import deque

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.config import get_settings

logger = logging.getLogger(__name__)

# In-memory session store — maps session_id → deque of BaseMessage
_session_store: dict[str, deque[BaseMessage]] = {}


def _get_window_size() -> int:
    """Get the configured memory window size (number of message pairs)."""
    return get_settings().memory_window_size


def get_memory(session_id: str) -> deque[BaseMessage]:
    """
    Get or create a conversation memory for a session.

    Args:
        session_id: Unique session identifier.

    Returns:
        Deque of BaseMessage for the session.
    """
    if session_id not in _session_store:
        # maxlen = window_size * 2 (each turn = human + assistant)
        _session_store[session_id] = deque(maxlen=_get_window_size() * 2)
        logger.info("Created new memory for session: %s", session_id)

    return _session_store[session_id]


def get_chat_history(session_id: str) -> list[dict[str, str]]:
    """
    Get chat history for a session as a list of message dicts.

    Args:
        session_id: Unique session identifier.

    Returns:
        List of {"role": "human"|"assistant", "content": "..."} dicts.
    """
    if session_id not in _session_store:
        return []

    messages = _session_store[session_id]
    history = []

    for msg in messages:
        if isinstance(msg, HumanMessage):
            history.append({"role": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            history.append({"role": "assistant", "content": msg.content})

    return history


def get_history_messages(session_id: str) -> list[BaseMessage]:
    """
    Get raw LangChain message objects for a session.

    Args:
        session_id: Unique session identifier.

    Returns:
        List of LangChain BaseMessage objects.
    """
    if session_id not in _session_store:
        return []

    return list(_session_store[session_id])


def save_messages(session_id: str, human_message: str, ai_message: str) -> None:
    """
    Save a human-AI message pair to session memory.

    Args:
        session_id: Unique session identifier.
        human_message: The user's message.
        ai_message: The assistant's response.
    """
    memory = get_memory(session_id)
    memory.append(HumanMessage(content=human_message))
    memory.append(AIMessage(content=ai_message))
    logger.debug("Saved messages to session %s", session_id)


def clear_memory(session_id: str) -> bool:
    """
    Clear conversation memory for a session.

    Args:
        session_id: Unique session identifier.

    Returns:
        True if session existed and was cleared, False if not found.
    """
    if session_id in _session_store:
        del _session_store[session_id]
        logger.info("Cleared memory for session: %s", session_id)
        return True
    return False


def get_active_sessions() -> list[str]:
    """Return list of active session IDs."""
    return list(_session_store.keys())
