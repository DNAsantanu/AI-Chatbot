"""
Chat Service — Main orchestrator combining LLM, memory, search, and prompts.
This is the central service that processes user chat messages.
"""

import logging
import uuid
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage

from backend.config import Settings, get_settings
from backend.services.llm_service import create_llm, get_llm_provider_name
from backend.services.memory_service import (
    get_history_messages,
    save_messages,
)
from backend.services.prompt_service import create_chat_prompt, format_web_context
from backend.services.search_service import search_web

logger = logging.getLogger(__name__)

# Cache the LLM instance across requests
_llm_cache: dict[str, object] = {}


def _get_cached_llm(model_name: Optional[str] = None, settings: Optional[Settings] = None):
    """Get or create a cached LLM instance."""
    if settings is None:
        settings = get_settings()

    cache_key = model_name or settings.llm_model_name
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = create_llm(settings=settings, model_override=model_name)
    return _llm_cache[cache_key]


async def process_chat(
    message: str,
    session_id: Optional[str] = None,
    use_web_search: bool = True,
    model_override: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> dict:
    """
    Process a user chat message through the full pipeline:
    1. Generate/validate session ID
    2. Optionally search the web for context
    3. Build the prompt with history and web context
    4. Invoke the LLM
    5. Save messages to memory
    6. Return structured response

    Args:
        message: User's chat message.
        session_id: Session ID. Auto-generated if None.
        use_web_search: Whether to use Tavily web search.
        model_override: Override the default model name.
        settings: Application settings.

    Returns:
        Dict with response, session_id, web_search_used, model.
    """
    if settings is None:
        settings = get_settings()

    # 1. Session ID
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info("Generated new session: %s", session_id)

    # 2. Web search (if enabled)
    web_context = ""
    web_search_used = False
    if use_web_search and settings.tavily_api_key:
        try:
            search_results = await search_web(query=message, settings=settings)
            if search_results:
                web_context = format_web_context(search_results)
                web_search_used = True
                logger.info("Web search augmented response for session %s", session_id)
        except Exception as e:
            logger.warning("Web search failed, proceeding without: %s", e)

    # 3. Build prompt chain
    llm = _get_cached_llm(model_name=model_override, settings=settings)
    prompt = create_chat_prompt()

    # Get chat history
    chat_history = get_history_messages(session_id)

    # 4. Create and invoke the LCEL chain
    chain = prompt | llm

    try:
        result = await chain.ainvoke({
            "input": message,
            "chat_history": chat_history,
            "web_context": web_context,
        })

        # Extract response text
        if isinstance(result, AIMessage):
            response_text = result.content
        else:
            response_text = str(result)

        # 5. Save to memory
        save_messages(session_id, message, response_text)

        # 6. Return structured response
        model_name = model_override or settings.llm_model_name
        logger.info(
            "Chat processed — session=%s, model=%s, search=%s",
            session_id, model_name, web_search_used,
        )

        return {
            "response": response_text,
            "session_id": session_id,
            "web_search_used": web_search_used,
            "model": model_name,
        }

    except Exception as e:
        logger.error("LLM invocation failed: %s", e)
        raise RuntimeError(f"Failed to generate response: {e}") from e
