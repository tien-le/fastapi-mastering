"""Main FastAPI application module."""
import logging
import sentry_sdk

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

from app.core.config import DevConfig, settings
from app.core.config_logging import configure_logging
from app.core.database import engine
from app.models.orm import Base

from app.routers.post import router as post_router
from app.routers.user import router as user_router
from app.routers.bucket import router as bucket_router

logger = logging.getLogger(__name__)


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


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
    logger.info("Application starting up...", extra={"email": "test_email@gmail.com"})

    # Auto-create tables in local development to speed up iteration.
    # This should NOT be used in production; prefer Alembic migrations.
    # Skip table creation on cloud platforms (Render.com, Railway, etc.) - use migrations instead
    is_local_dev = isinstance(settings, DevConfig) and (
        "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI).lower()
        or "localhost" in str(settings.SQLALCHEMY_DATABASE_URI).lower()
        or "127.0.0.1" in str(settings.SQLALCHEMY_DATABASE_URI).lower()
    )

    if is_local_dev:
        try:
            logger.info("Creating database tables (local development only)...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            # Log error but don't crash - database might already exist or connection might fail
            logger.warning(
                f"Failed to create database tables: {e}. "
                "This is expected if tables already exist or if using migrations.",
                exc_info=True
            )
            # Only raise in development if it's a critical error (not connection refused)
            if "Connection refused" not in str(e) and "does not exist" not in str(e):
                logger.error("Critical database error during table creation", exc_info=True)
                raise
    elif isinstance(settings, DevConfig):
        # DevConfig but not local - likely cloud deployment (Render.com, etc.)
        logger.info(
            "Skipping auto table creation - detected cloud deployment. "
            "Please run Alembic migrations: 'alembic upgrade head'"
        )

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
app.include_router(user_router)
app.include_router(bucket_router)


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
