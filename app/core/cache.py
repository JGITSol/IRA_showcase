"""Caching utilities using Redis."""

import json
import pickle
from types import SimpleNamespace
from typing import Any, Optional
from functools import wraps
import hashlib

import redis
from redis.exceptions import RedisError
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class CacheManager:
    """Redis cache manager with fallback to in-memory cache."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._memory_cache: dict = {}
        self._initialize_redis()
    
    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        if not settings.CACHE_ENABLED:
            logger.info("Cache disabled")
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URI,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized", redis_uri=settings.REDIS_URI)
        except (RedisError, Exception) as e:
            logger.warning("Redis connection failed, using memory cache", error=str(e))
            self.redis_client = None
    
    def _serialize_key(self, key: str) -> str:
        """Create a consistent cache key."""
        return f"ira:{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for simple types
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            try:
                return pickle.dumps(value)
            except Exception:
                payload = getattr(value, "__dict__", None)
                if payload is not None:
                    try:
                        return pickle.dumps(SimpleNamespace(**payload))
                    except Exception:
                        pass
                return pickle.dumps(str(value))
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(value)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._serialize_key(key)
        
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if isinstance(value, bytes):
                    return self._deserialize_value(value)
                if value is not None:
                    return value
            except (RedisError, Exception) as e:  # pragma: no cover - defensive
                logger.warning("Redis get failed", key=key, error=str(e))
        
        # Fallback to memory cache
        return self._memory_cache.get(cache_key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        cache_key = self._serialize_key(key)
        ttl = ttl or settings.CACHE_TTL
        
        if self.redis_client:
            try:
                serialized_value = self._serialize_value(value)
                self.redis_client.setex(cache_key, ttl, serialized_value)
                return True
            except (RedisError, Exception) as e:  # pragma: no cover - defensive
                logger.warning("Redis set failed", key=key, error=str(e))
        
        # Fallback to memory cache
        self._memory_cache[cache_key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._serialize_key(key)
        
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except (RedisError, Exception) as e:  # pragma: no cover - defensive
                logger.warning("Redis delete failed", key=key, error=str(e))
        
        # Also remove from memory cache
        self._memory_cache.pop(cache_key, None)
        return True
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        if self.redis_client:
            try:
                # Delete all keys with our prefix
                keys = self.redis_client.keys("ira:*")
                if isinstance(keys, list) and keys:
                    self.redis_client.delete(*keys)
            except (RedisError, Exception) as e:  # pragma: no cover - defensive
                logger.warning("Redis clear failed", error=str(e))
        
        self._memory_cache.clear()
        return True
    
    def health_check(self) -> dict:
        """Check cache health."""
        status = {
            "redis_available": False,
            "memory_cache_size": len(self._memory_cache)
        }
        
        if self.redis_client:
            try:
                self.redis_client.ping()
                status["redis_available"] = True
                status["redis_info"] = self.redis_client.info("memory")
            except (RedisError, Exception):  # pragma: no cover - defensive
                pass
        
        return status


# Global cache instance
cache = CacheManager()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            if args:
                args_str = str(hash(str(args)))
                key_parts.append(args_str)
            
            # Add kwargs to key
            if kwargs:
                kwargs_str = str(hash(str(sorted(kwargs.items()))))
                key_parts.append(kwargs_str)
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit", function=func.__name__, key=cache_key)
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug("Cache miss", function=func.__name__, key=cache_key)
            
            return result
        return wrapper
    return decorator


def cache_key_for_prediction(age: int, sex: str, bmi: float, children: int, smoker: bool, region: str) -> str:
    """Generate a consistent cache key for predictions."""
    data = f"{age}:{sex}:{bmi:.2f}:{children}:{smoker}:{region}"
    return hashlib.md5(data.encode()).hexdigest()