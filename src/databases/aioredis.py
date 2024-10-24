from typing import AsyncIterable
from redis.asyncio import Redis

from config import RedisConfig


async def get_redis_cursor() -> AsyncIterable[Redis]:
    """Возвращает подключение к redis"""

    cursor = Redis.from_url(
        url=RedisConfig.UPL,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield cursor

    finally:
        await cursor.close()
