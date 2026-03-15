"""
Асинхронный клиент Redis для кэширования данных (например, колоды профилей).
"""
from typing import Optional

import redis.asyncio as redis

from app.core.config import settings

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Возвращает singleton-подключение к Redis.
    
    Используется как dependency в эндпоинтах.
    """
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


