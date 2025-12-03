import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
# from fastapi_cache.decorator import cache
# from fastapi_cache import FastAPICache
# from fastapi_cache.backends.redis import RedisBackend
# from redis.asyncio import Redis as aioredis
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from database.crud import get_url, create_url, get_url_by_source_url, increment_visits
from database.core import get_session, create_tables, close_db
from schemas import ShortedURLRequest, ShortedURLResponse
from utils import generate_short_id
from config import settings

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # redis = None
    # if settings.REDIS_CACHE_URL is not None:
    #     try:
    #         redis = aioredis.from_url(settings.REDIS_CACHE_URL.get_secret_value(), encoding="utf8", decode_responses=True)
    #         FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    #     except:
    #         redis = None
    try:
        create_tables()
    except:
        logger.error("Failed to create database tables")
        raise RuntimeError("Failed to init database tables")
    yield
    try:
        close_db()
    except:
        logger.error("Error while closing database connection")
    # if redis is not None:
    #     await redis.close()

app = FastAPI(lifespan=lifespan, docs_url=None)


@app.get("/{short_id}/stats")
async def get_url_stats(short_id: str, session: Session = Depends(get_session)) -> ShortedURLResponse:
    logger.info(f"Requested stats for short_id: {short_id}")
    try:
        url = get_url(session=session, short_id=short_id)
    except Exception as e:
        logger.error("Error while executing database query")
        raise HTTPException(status_code=500, detail=str(e))
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    if settings.BASE_URL is None:
        logger.error("Base url not provided")
        raise HTTPException(status_code=500, detail="Base url not provided")
    respone = ShortedURLResponse.model_validate(url)
    respone.full_url = HttpUrl(f"{settings.BASE_URL}{respone.short_id}")
    return respone


@app.get("/{short_id}")
# @cache(expire=None)
async def redirect_url(short_id: str, background: BackgroundTasks, session: Session = Depends(get_session)) -> RedirectResponse:
    try:
        url = get_url(session=session, short_id=short_id)
    except Exception as e:
        logger.error("Error while executing database query")
        raise HTTPException(status_code=500, detail=str(e))
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    background.add_task(increment_visits, url.id)
    return RedirectResponse(url=url.source_url)


@app.post("/url")
# @cache(expire=None)
async def create_url_route(url_object: ShortedURLRequest, session: Session = Depends(get_session)) -> ShortedURLResponse:
    try:
        url = get_url_by_source_url(session=session, source_url=str(url_object.source_url))
        if url is None:
            url = create_url(
                session=session,
                source_url=str(url_object.source_url),
                short_id=generate_short_id()
            )
            session.commit()
            logger.info("Transaction commited")
    except Exception as e:
        session.rollback()
        logger.error("Error while executing database query")
        raise HTTPException(status_code=500, detail=str(e))
    if settings.BASE_URL is None:
        logger.error("Base url not provided")
        raise HTTPException(status_code=500, detail="Base url not provided")
    respone = ShortedURLResponse.model_validate(url)
    respone.full_url = HttpUrl(f"{settings.BASE_URL}{respone.short_id}")
    return respone


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=80, log_level='info')
