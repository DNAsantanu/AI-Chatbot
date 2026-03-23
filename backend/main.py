"""
AI ChatBot — FastAPI Application Entry Point.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.routes import chat, health


# ──────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────

def setup_logging() -> None:
    """Configure structured logging."""
    log_format = (
        "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s"
    )
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Quiet noisy libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Application Lifecycle
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    settings = get_settings()
    logger.info("🚀 Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("   LLM Model  : %s", settings.llm_model_name)
    logger.info("   Groq Key   : %s", "✓ configured" if settings.groq_api_key else "✗ not set")
    logger.info("   HF Token   : %s", "✓ configured" if settings.huggingfacehub_api_token else "✗ not set")
    logger.info("   Tavily Key  : %s", "✓ configured" if settings.tavily_api_key else "✗ not set")
    yield
    logger.info("👋 Shutting down %s", settings.app_name)


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A production-ready, context-aware conversational AI chatbot.",
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(health.router)
    app.include_router(chat.router)

    # --- Global Exception Handler ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred.",
            },
        )

    return app


# Create the app instance (used by uvicorn: `uvicorn backend.main:app`)
app = create_app()
