"""Rate limiting utilities."""

import time
from typing import Dict, Optional
from functools import wraps

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.cache import cache

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 100):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.tokens_per_second = requests_per_minute / 60.0
    
    def _get_bucket_key(self, identifier: str) -> str:
        """Get the cache key for the rate limit bucket."""
        return f"rate_limit:{identifier}"
    
    def _get_bucket(self, identifier: str) -> Dict[str, float]:
        """Get or create a token bucket for the identifier."""
        key = self._get_bucket_key(identifier)
        bucket = cache.get(key)
        
        if bucket is None:
            bucket = {
                "tokens": float(self.burst),
                "last_refill": time.time()
            }
            cache.set(key, bucket, ttl=3600)  # 1 hour TTL
        
        return bucket
    
    def _refill_bucket(self, bucket: Dict[str, float]) -> None:
        """Refill the token bucket based on elapsed time."""
        now = time.time()
        elapsed = now - bucket["last_refill"]
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.tokens_per_second
        bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now
    
    def is_allowed(self, identifier: str, tokens: int = 1) -> bool:
        """Check if the request is allowed."""
        if not settings.RATE_LIMIT_ENABLED:
            return True
        
        bucket = self._get_bucket(identifier)
        self._refill_bucket(bucket)
        
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            # Update the bucket in cache
            cache.set(self._get_bucket_key(identifier), bucket, ttl=3600)
            return True
        
        return False
    
    def get_retry_after(self, identifier: str) -> int:
        """Get the number of seconds to wait before retrying."""
        bucket = self._get_bucket(identifier)
        self._refill_bucket(bucket)
        
        if bucket["tokens"] >= 1:
            return 0
        
        # Calculate time needed to get one token
        tokens_needed = 1 - bucket["tokens"]
        return int(tokens_needed / self.tokens_per_second) + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(
            requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            burst=settings.RATE_LIMIT_BURST
        )
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get a unique identifier for the client."""
        # Try to get real IP from headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Include user agent for additional uniqueness
        user_agent = request.headers.get("User-Agent", "")[:50]  # Limit length
        
        return f"{client_ip}:{hash(user_agent)}"
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        identifier = self._get_client_identifier(request)
        
        if not self.rate_limiter.is_allowed(identifier):
            retry_after = self.rate_limiter.get_retry_after(identifier)
            
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                path=request.url.path,
                retry_after=retry_after
            )
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)}
            )
        
        return await call_next(request)


def rate_limit(requests_per_minute: int = 60, burst: int = 100):
    """Decorator for rate limiting specific endpoints."""
    limiter = RateLimiter(requests_per_minute, burst)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get client identifier
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            
            identifier = f"endpoint:{func.__name__}:{client_ip}"
            
            if not limiter.is_allowed(identifier):
                retry_after = limiter.get_retry_after(identifier)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {func.__name__}",
                    headers={"Retry-After": str(retry_after)}
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# Global rate limiter instance
default_rate_limiter = RateLimiter(
    requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    burst=settings.RATE_LIMIT_BURST
)