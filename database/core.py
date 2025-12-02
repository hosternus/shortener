import logging
from math import log

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from database.model import Base

logger = logging.getLogger(__name__)

if settings.DATABASE_URL is None:
    logger.error("Database url is None")
    raise RuntimeError("Database URL is None")

engine = create_engine(settings.DATABASE_URL.get_secret_value(), echo=False)
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    logger.info("Database session opening")
    with session_factory() as session:
        logger.info("Databse session opened")
        yield session
    logger.info("Database session closed")

def create_tables():
    logger.info("Creating database tables")
    Base.metadata.create_all(engine)
    logger.info("Created database tables")

def close_db():
    logger.info("Closing database connection")
    engine.dispose()
    logger.info("Database connection closed")