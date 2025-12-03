import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database.core import session_factory
from database.model import Url

logger = logging.getLogger(__name__)

async def get_url(session: AsyncSession, short_id: str) -> Url | None:
    logger.info(f"Query object with short_id: {short_id}")
    query = await session.execute(
        select(Url).where(Url.short_id == short_id)
    )
    res = query.scalar_one_or_none()
    logger.info(f"Loaded object with short_id: {short_id}" if res is not None else f"No object with such short_id: {short_id}")
    return res

async def create_url(session: AsyncSession, source_url: str, short_id: str) -> Url:
    logger.info(f"Creating object for source_url: {source_url} with short_id: {short_id}")
    url = Url(source_url=source_url, short_id=short_id)
    session.add(url)
    await session.flush()
    logger.info(f"Created shorted link with short_id: {short_id}")
    return url

async def get_url_by_source_url(session: AsyncSession, source_url: str) -> Url | None:
    logger.info(f"Query object with source_url: {source_url}")
    query = await session.execute(
        select(Url).where(Url.source_url == source_url)
    )
    res = query.scalar_one_or_none()
    logger.info(f"Loaded object from source_url with short_id: {res.short_id}" if res is not None else f"No object with such source_url: {source_url}")
    return res

async def increment_visits(short_id: str) -> None:
    stmt = (
        update(Url)
        .where(Url.short_id == short_id)
        .values(visits=Url.visits + 1)
    )
    async with session_factory() as session:
        try:
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Incrimented url object with id: {short_id}")
        except Exception as e:
            logger.error(f"Error while incrementing url object with id: {short_id}, error: {str(e)}")
            await session.rollback()
