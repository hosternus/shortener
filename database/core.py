import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings
from database.model import Base

logger = logging.getLogger(__name__)

if settings.DATABASE_URL is None:
    logger.error("Database url is None")
    raise RuntimeError("Database URL is None")

engine = create_async_engine(settings.DATABASE_URL.get_secret_value(), echo=False)
session_factory = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

async def get_session():
    logger.info("Database session opening")
    async with session_factory() as session:
        logger.info("Databse session opened")
        yield session
    logger.info("Database session closed")

async def create_tables():
    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Created database tables")

async def close_db():
    logger.info("Closing database connection")
    await engine.dispose()
    logger.info("Database connection closed")