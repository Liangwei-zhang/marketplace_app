import os
import json
import redis.asyncio as redis
from typing import Optional, Any
from app.core.config import settings


class RedisCache:
    """Redis caching service"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> Optional[redis.Redis]:
        if not self.enabled:
            return None
        
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = await self.get_client()
        if not client:
            return None
        
        try:
            value = await client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value to cache with TTL (seconds)"""
        client = await self.get_client()
        if not client:
            return False
        
        try:
            await client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = await self.get_client()
        if not client:
            return False
        
        try:
            await client.delete(key)
            return True
        except Exception:
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        client = await self.get_client()
        if not client:
            return 0
        
        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await client.delete(*keys)
        except Exception:
            pass
        return 0
    
    async def close(self):
        """Close connection"""
        if self._client:
            await self._client.close()


# Cache key generators
class CacheKeys:
    # User cache
    USER = "user:{user_id}"
    USER_BY_TOKEN = "token:{token}"
    
    # Item cache
    ITEM = "item:{item_id}"
    ITEMS_BY_CATEGORY = "items:category:{category}"
    ITEMS_NEARBY = "items:nearby:{lat}:{lng}:{radius}"
    POPULAR_ITEMS = "items:popular"
    
    # Category cache
    CATEGORIES = "categories:all"
    
    # Stats cache
    ADMIN_STATS = "admin:stats"
    USER_STATS = "user:{user_id}:stats"


# Singleton instance
cache = RedisCache()
