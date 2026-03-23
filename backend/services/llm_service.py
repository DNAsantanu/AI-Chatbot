"""
LLM Service — Factory for creating LangChain LLM instances.
Supports Groq (primary) with HuggingFace Hub fallback.
"""

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel

from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


def create_llm(
    settings: Optional[Settings] = None,
    model_override: Optional[str] = None,
) -> BaseChatModel:
    """
    Create and return an LLM instance.

    Priority:
        1. Groq (fast inference, requires GROQ_API_KEY)
        2. HuggingFace Hub (fallback, requires HUGGINGFACEHUB_API_TOKEN)

    Args:
        settings: Application settings. Uses cached singleton if None.
        model_override: Override the model name from settings.

    Returns:
        A LangChain chat model instance.

    Raises:
        ValueError: If no API key is configured for any provider.
    """
    if settings is None:
        settings = get_settings()

    model_name = model_override or settings.llm_model_name
    temperature = settings.llm_temperature

    # --- Try Groq first ---
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq

            llm = ChatGroq(
                model=model_name,
                api_key=settings.groq_api_key,
                temperature=temperature,
                max_tokens=2048,
                request_timeout=30,
            )
            logger.info("LLM initialized: Groq (%s)", model_name)
            return llm
        except Exception as e:
            logger.warning("Groq initialization failed: %s. Trying fallback.", e)

    # --- Fallback to HuggingFace Hub ---
    if settings.huggingfacehub_api_token:
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

            endpoint = HuggingFaceEndpoint(
                repo_id=model_name if "/" in model_name else f"mistralai/Mistral-7B-Instruct-v0.3",
                huggingfacehub_api_token=settings.huggingfacehub_api_token,
                temperature=temperature,
                max_new_tokens=2048,
                task="text-generation",
            )
            llm = ChatHuggingFace(llm=endpoint)
            logger.info("LLM initialized: HuggingFace Hub (%s)", endpoint.repo_id)
            return llm
        except Exception as e:
            logger.warning("HuggingFace initialization failed: %s", e)

    raise ValueError(
        "No LLM provider configured. "
        "Set GROQ_API_KEY or HUGGINGFACEHUB_API_TOKEN in your .env file."
    )


def get_llm_provider_name(settings: Optional[Settings] = None) -> str:
    """Return the name of the active LLM provider."""
    if settings is None:
        settings = get_settings()

    if settings.groq_api_key:
        return "groq"
    if settings.huggingfacehub_api_token:
        return "huggingface"
    return "none"
