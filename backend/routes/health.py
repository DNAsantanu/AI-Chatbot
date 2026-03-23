"""
Health Routes — System health and status endpoint.
"""

from datetime import datetime

from fastapi import APIRouter

from backend.config import get_settings
from backend.models.schemas import HealthResponse
from backend.services.llm_service import get_llm_provider_name
from backend.services.search_service import is_search_available

router = APIRouter(tags=["Health"])

_start_time = datetime.utcnow()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns system status, LLM provider info, and search availability.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        llm_provider=get_llm_provider_name(settings),
        web_search_available=is_search_available(settings),
    )
