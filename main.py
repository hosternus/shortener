import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from database.crud import get_url, create_url, get_url_by_source_url, increment_visits
from database.core import get_session, create_tables, close_db
from schemas import ShortedURLRequest, ShortedURLResponse
from utils import generate_short_id
from config import settings
from redis_client import get_redis, init_redis, close_redis

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_redis()
        redis = await get_redis()
        FastAPICache.init(RedisBackend(redis=redis), prefix="fastapi-cache")
        create_tables()
    except Exception as e:
        logger.error(f"Failed to initialize app: {str(e)}")
        raise e
    yield
    try:
        close_db()
    except Exception as e:
        logger.error(f"Failed to close database connection: {str(e)}")
    try:
        await close_redis()
    except Exception as e:
        logger.error(f"Failed to close redis connection: {str(e)}")

app = FastAPI(lifespan=lifespan, docs_url=None)


@app.get("/{short_id}/stats")
@cache(expire=120)
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
async def redirect_url(short_id: str, background: BackgroundTasks, session: Session = Depends(get_session), redis: Redis = Depends(get_redis)) -> RedirectResponse:
    source_url: str | None = None
    r_key: str = f"short_id:{short_id}"
    try:
        cached = await redis.get(r_key)
        if cached:
            source_url = cached
    except Exception as e:
        logger.error(f"Failed to retrieve cache from redis: {str(e)}")
    if source_url is None:
        try:
            url = get_url(session=session, short_id=short_id)
            if url:
                source_url = url.source_url
                try:
                    await redis.set(r_key, source_url, ex=43200)
                except Exception as e:
                    logger.error(f"Failed to cache url with short_id: {short_id} in redis: {str(e)}")
        except Exception as e:
            logger.error("Error while executing database query")
            raise HTTPException(status_code=500, detail=str(e))
    if source_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    background.add_task(increment_visits, short_id)
    return RedirectResponse(url=source_url)


@app.post("/url")
@cache(expire=3600)
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
    uvicorn.run(app, host='0.0.0.0', port=80, log_level='info', log_config=None)
