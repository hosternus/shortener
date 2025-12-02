from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis as aioredis
from sqlalchemy.orm import Session

from database.crud import get_url, create_url, get_url_by_source_url
from database.core import get_session, create_tables, close_db
from schemas import CreateUrl
from utils import generate_short_id
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = None
    if settings.REDIS_CACHE_URL is not None:
        try:
            redis = aioredis.from_url(settings.REDIS_CACHE_URL.get_secret_value(), encoding="utf8", decode_responses=True)
            FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        except:
            redis = None
    try:
        create_tables()
    except:
        raise RuntimeError("Failed to init database tables")
    yield
    close_db()
    if redis is not None:
        await redis.close()

app = FastAPI(lifespan=lifespan)


@app.get("/{url_id}")
# @cache(expire=None)
async def return_url(url_id: str, session: Session = Depends(get_session)):
    try:
        url = get_url(session=session, short_id=url_id)
        if url is None:
            raise HTTPException(status_code=404, detail="Not found")
        url.visits += 1
        session.commit()
        return RedirectResponse(url=url.source_url)
    except HTTPException as e:
        session.rollback()
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/url")
# @cache(expire=None)
async def create_url_route(url_object: CreateUrl, session: Session = Depends(get_session)):
    try:
        url = get_url_by_source_url(session=session, source_url=str(url_object.source_url))
        if url is None:
            url = create_url(
                session=session,
                source_url=str(url_object.source_url),
                short_id=generate_short_id()
            )
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    if settings.BASE_URL is None:
        raise HTTPException(status_code=500, detail="Base url not provided")
    return {"short_url": f"{settings.BASE_URL}{url.short_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=80)
