from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from database.model import Url, Base

if settings.DATABASE_URL is None:
    raise RuntimeError("DATABASE URL is None")

engine = create_engine(settings.DATABASE_URL, echo=False)
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    with session_factory() as session:
        yield session

def create_tables():
    Base.metadata.create_all(engine)

def close_db():
    engine.dispose()
