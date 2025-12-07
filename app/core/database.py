"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config_loader import settings

# engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
async_session = async_sessionmaker(engine)

# Cach 2
# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()


async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
