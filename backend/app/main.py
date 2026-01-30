"""
ClaimIQ — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db
from app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: nothing needed for SQLite."""
    logger.info("Starting ClaimIQ backend...")
    await init_db()
    mode = "MOCK MODE (no Gemini key)" if settings.mock_mode else "LIVE MODE"
    logger.info(f"AI: {mode}")
    logger.info(f"DB: {settings.database_url}")
    logger.info(f"Storage: {settings.storage_backend}")
    yield
    logger.info("ClaimIQ backend shutting down.")


app = FastAPI(
    title="ClaimIQ API",
    description="KI-gestützte Kfz-Schadenanalyse für Versicherungsmakler",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "mock_mode": settings.mock_mode,
    }
