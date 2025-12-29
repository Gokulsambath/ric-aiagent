import redis.asyncio as redis
from typing import Optional, List, Any
import json
from app.configs.settings import settings
import logging

logger = logging.getLogger(__name__)

class RedisService:
    _instance = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self.redis_url = f"redis://{settings.redis.redis_host}:{settings.redis.redis_port}/{settings.redis.redis_db}"
            if settings.redis.redis_password:
                self.redis_url = f"redis://:{settings.redis.redis_password}@{settings.redis.redis_host}:{settings.redis.redis_port}/{settings.redis.redis_db}"
            
            logger.info(f"Redis Service initialized with URL: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis config: {e}")

    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self.get_client()
            val = await client.get(key)
            if val:
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return val
            return None
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            client = await self.get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")

    async def delete(self, key: str):
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")

    # List operations for chat history
    async def lpush(self, key: str, value: Any):
        try:
            client = await self.get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await client.lpush(key, value)
        except Exception as e:
            logger.error(f"Redis LPUSH failed for key {key}: {e}")
            
    async def rpush(self, key: str, value: Any, max_len: int = 50, ttl: int = 86400):
        try:
            client = await self.get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await client.rpush(key, value)
            # Trim list to keep only last `max_len` items
            await client.ltrim(key, -max_len, -1)
            # Refresh TTL
            await client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis RPUSH failed for key {key}: {e}")

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        try:
            client = await self.get_client()
            items = await client.lrange(key, start, end)
            results = []
            for item in items:
                try:
                    results.append(json.loads(item))
                except json.JSONDecodeError:
                    results.append(item)
            return results
        except Exception as e:
            logger.error(f"Redis LRANGE failed for key {key}: {e}")
            return []

# Singleton
redis_service = RedisService()
