import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from app.core.config_loader import DevConfig, settings
from app.core.database import engine
from app.core.logging_config import configure_logging
from app.models.orm import Base
from app.routers.post import router as post_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Optional: Create DB tables on startup (only for local dev/testing)
    Remove in production.
    """
    # Example if you want auto-create tables in dev
    # from app.models.orm import Base
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # Auto-create tables in local development to speed up iteration.
    # This should NOT be used in production; prefer Alembic migrations.
    if isinstance(settings, DevConfig):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    configure_logging()
    logger.info("App Starting up...")

    yield

    # Nothing to close — SQLAlchemy AsyncSession is managed per-request
    # using dependency injection.
    # --- Shutdown (after the app stops) ---
    logger.info("App Shutting down...")
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(post_router)  # , prefix="/posts")


@app.get("/")
async def get_home() -> dict:
    return {"message": "Hello world!"}


@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)
