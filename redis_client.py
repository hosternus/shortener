import logging

from redis.asyncio import Redis

from config import settings


logger = logging.getLogger(__name__)
redis_pool: Redis | None = None

async def init_redis() -> None:
    global redis_pool
    if redis_pool is None:
        redis_pool = Redis(
            host=settings.redis.HOST,
            port=settings.redis.PORT,
            decode_responses=False,
            max_connections=settings.redis.MAX_CONN
        )
        logger.info("Redis client initialized")

async def close_redis() -> None:
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        logger.info("Redis client closed")

async def get_redis() -> Redis:
    global redis_pool
    if redis_pool:
        return redis_pool
    raise RuntimeError("Redis is not initialized")
