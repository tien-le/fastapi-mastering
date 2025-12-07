"""Main FastAPI application module."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

from app.core.config import DevConfig
from app.core.config_loader import settings
from app.core.database import engine
from app.core.logging_config import configure_logging
from app.models.orm import Base
from app.routers.post import router as post_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown tasks:
    - Configures logging
    - Creates database tables in development mode
    - Disposes database engine on shutdown

    Note: Table creation should be replaced with Alembic migrations in production.
    """
    configure_logging()
    logger.info("Application starting up...")

    # Auto-create tables in local development to speed up iteration.
    # This should NOT be used in production; prefer Alembic migrations.
    if isinstance(settings, DevConfig):
        try:
            logger.info("Creating database tables...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}", exc_info=True)
            raise

    yield

    # Shutdown: dispose database engine
    logger.info("Application shutting down...")
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="FastAPI Mastering",
    description="A FastAPI application demonstrating clean code practices",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(CorrelationIdMiddleware)

# Routers
app.include_router(post_router)


@app.get("/", response_model=dict[str, str])
async def get_home() -> dict[str, str]:
    """Root endpoint returning a welcome message."""
    return {"message": "Hello world!"}


@app.exception_handler(HTTPException)
async def http_exception_handler_with_logging(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Custom HTTP exception handler with logging.

    Logs all HTTP exceptions before delegating to the default handler.
    """
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={"path": request.url.path, "method": request.method},
    )
    return await http_exception_handler(request, exc)
