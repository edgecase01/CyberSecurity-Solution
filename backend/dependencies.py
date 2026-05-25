from collections.abc import AsyncGenerator

from redis.asyncio import Redis

_redis: Redis | None = None


def init_redis(url: str) -> Redis:
    global _redis
    _redis = Redis.from_url(url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    if _redis is None:
        raise RuntimeError("Redis client is not initialized.")
    yield _redis
