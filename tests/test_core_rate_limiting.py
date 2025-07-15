"""Tests for rate limiting functionality."""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, HTTPException
from starlette.applications import Starlette

from app.core.rate_limiting import RateLimiter, RateLimitMiddleware, rate_limit, default_rate_limiter


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance."""
        return RateLimiter(requests_per_minute=60, burst=10)
    
    def test_init(self, rate_limiter):
        """Test rate limiter initialization."""
        assert rate_limiter.requests_per_minute == 60
        assert rate_limiter.burst == 10
        assert rate_limiter.tokens_per_second == 1.0
    
    def test_get_bucket_key(self, rate_limiter):
        """Test bucket key generation."""
        key = rate_limiter._get_bucket_key("test_user")
        assert key == "rate_limit:test_user"
    
    def test_get_bucket_new(self, rate_limiter):
        """Test getting a new bucket."""
        with patch('app.core.rate_limiting.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            bucket = rate_limiter._get_bucket("test_user")
            
            assert bucket["tokens"] == 10.0  # burst size
            assert "last_refill" in bucket
            mock_cache.set.assert_called_once()
    
    def test_get_bucket_existing(self, rate_limiter):
        """Test getting an existing bucket."""
        existing_bucket = {
            "tokens": 5.0,
            "last_refill": time.time()
        }
        
        with patch('app.core.rate_limiting.cache') as mock_cache:
            mock_cache.get.return_value = existing_bucket
            
            bucket = rate_limiter._get_bucket("test_user")
            
            assert bucket == existing_bucket
    
    def test_refill_bucket(self, rate_limiter):
        """Test bucket refilling."""
        past_time = time.time() - 10  # 10 seconds ago
        bucket = {
            "tokens": 0.0,
            "last_refill": past_time
        }
        
        rate_limiter._refill_bucket(bucket)
        
        # Should have added tokens based on elapsed time
        assert bucket["tokens"] > 0
        assert bucket["last_refill"] > past_time
        assert bucket["tokens"] <= rate_limiter.burst
    
    def test_is_allowed_sufficient_tokens(self, rate_limiter):
        """Test allowing request when sufficient tokens available."""
        with patch('app.core.rate_limiting.settings') as mock_settings:
            mock_settings.RATE_LIMIT_ENABLED = True
            
            with patch.object(rate_limiter, '_get_bucket') as mock_get_bucket, \
                 patch.object(rate_limiter, '_refill_bucket') as mock_refill, \
                 patch('app.core.rate_limiting.cache') as mock_cache:
                
                bucket = {"tokens": 5.0, "last_refill": time.time()}
                mock_get_bucket.return_value = bucket
                
                result = rate_limiter.is_allowed("test_user", tokens=1)
                
                assert result is True
                assert bucket["tokens"] == 4.0
                mock_refill.assert_called_once()
                mock_cache.set.assert_called_once()
    
    def test_is_allowed_insufficient_tokens(self, rate_limiter):
        """Test denying request when insufficient tokens available."""
        with patch('app.core.rate_limiting.settings') as mock_settings:
            mock_settings.RATE_LIMIT_ENABLED = True
            
            with patch.object(rate_limiter, '_get_bucket') as mock_get_bucket, \
                 patch.object(rate_limiter, '_refill_bucket') as mock_refill:
                
                bucket = {"tokens": 0.5, "last_refill": time.time()}
                mock_get_bucket.return_value = bucket
                
                result = rate_limiter.is_allowed("test_user", tokens=1)
                
                assert result is False
                mock_refill.assert_called_once()
    
    def test_is_allowed_disabled(self, rate_limiter):
        """Test allowing request when rate limiting is disabled."""
        with patch('app.core.rate_limiting.settings') as mock_settings:
            mock_settings.RATE_LIMIT_ENABLED = False
            
            result = rate_limiter.is_allowed("test_user")
            
            assert result is True
    
    def test_get_retry_after_tokens_available(self, rate_limiter):
        """Test retry after when tokens are available."""
        with patch.object(rate_limiter, '_get_bucket') as mock_get_bucket, \
             patch.object(rate_limiter, '_refill_bucket') as mock_refill:
            
            bucket = {"tokens": 2.0, "last_refill": time.time()}
            mock_get_bucket.return_value = bucket
            
            retry_after = rate_limiter.get_retry_after("test_user")
            
            assert retry_after == 0
    
    def test_get_retry_after_tokens_needed(self, rate_limiter):
        """Test retry after when tokens are needed."""
        with patch.object(rate_limiter, '_get_bucket') as mock_get_bucket, \
             patch.object(rate_limiter, '_refill_bucket') as mock_refill:
            
            bucket = {"tokens": 0.5, "last_refill": time.time()}
            mock_get_bucket.return_value = bucket
            
            retry_after = rate_limiter.get_retry_after("test_user")
            
            assert retry_after > 0


class TestRateLimitMiddleware:
    """Test the RateLimitMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create a rate limit middleware instance."""
        app = Starlette()
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        return RateLimitMiddleware(app, limiter)
    
    def test_get_client_identifier_with_forwarded_for(self, middleware):
        """Test client identifier extraction with X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Forwarded-For": "192.168.1.1, 10.0.0.1",
            "User-Agent": "TestAgent/1.0"
        }.get(key)
        
        identifier = middleware._get_client_identifier(request)
        
        assert identifier.startswith("192.168.1.1:")
    
    def test_get_client_identifier_without_forwarded_for(self, middleware):
        """Test client identifier extraction without X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "User-Agent": "TestAgent/1.0"
        }.get(key, None)
        request.client.host = "127.0.0.1"
        
        identifier = middleware._get_client_identifier(request)
        
        assert identifier.startswith("127.0.0.1:")
    
    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_disabled(self, middleware):
        """Test middleware when rate limiting is disabled."""
        request = Mock(spec=Request)
        response = Mock()
        
        async def call_next(req):
            return response
        
        with patch('app.core.rate_limiting.settings') as mock_settings:
            mock_settings.RATE_LIMIT_ENABLED = False
            
            result = await middleware.dispatch(request, call_next)
            
            assert result == response
    
    @pytest.mark.asyncio
    async def test_dispatch_health_check_skip(self, middleware):
        """Test middleware skipping health check endpoints."""
        request = Mock(spec=Request)
        request.url.path = "/health"
        response = Mock()
        
        async def call_next(req):
            return response
        
        with patch('app.core.rate_limiting.settings') as mock_settings:
            mock_settings.RATE_LIMIT_ENABLED = True
            
            result = await middleware.dispatch(request, call_next)
            
            assert result == response
    
    @pytest.mark.asyncio
    async def test_dispatch_allowed(self, middleware):
        """Test middleware allowing request."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        response = Mock()
        
        async def call_next(req):
            return response
        
        with patch('app.core.rate_limiting.settings') as mock_settings, \
             patch.object(middleware, '_get_client_identifier') as mock_get_id:
            
            mock_settings.RATE_LIMIT_ENABLED = True
            mock_get_id.return_value = "test_client"
            middleware.rate_limiter.is_allowed = Mock(return_value=True)
            
            result = await middleware.dispatch(request, call_next)
            
            assert result == response
            middleware.rate_limiter.is_allowed.assert_called_once_with("test_client")
    
    @pytest.mark.asyncio
    async def test_dispatch_rate_limited(self, middleware):
        """Test middleware blocking rate limited request."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        
        with patch('app.core.rate_limiting.settings') as mock_settings, \
             patch.object(middleware, '_get_client_identifier') as mock_get_id, \
             patch('app.core.rate_limiting.logger') as mock_logger:
            
            mock_settings.RATE_LIMIT_ENABLED = True
            mock_get_id.return_value = "test_client"
            middleware.rate_limiter.is_allowed = Mock(return_value=False)
            middleware.rate_limiter.get_retry_after = Mock(return_value=60)
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, lambda x: None)
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in exc_info.value.detail
            assert exc_info.value.headers["Retry-After"] == "60"
            mock_logger.warning.assert_called_once()


class TestRateLimitDecorator:
    """Test the rate_limit decorator."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_decorator_allowed(self):
        """Test rate limit decorator allowing request."""
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = None
        
        @rate_limit(requests_per_minute=60, burst=10)
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        with patch('app.core.rate_limiting.RateLimiter') as mock_limiter_class:
            mock_limiter = Mock()
            mock_limiter.is_allowed.return_value = True
            mock_limiter_class.return_value = mock_limiter
            
            result = await test_endpoint(request)
            
            assert result == {"message": "success"}
            mock_limiter.is_allowed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_decorator_blocked(self):
        """Test rate limit decorator blocking request."""
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = None
        
        @rate_limit(requests_per_minute=60, burst=10)
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        with patch('app.core.rate_limiting.RateLimiter') as mock_limiter_class:
            mock_limiter = Mock()
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_retry_after.return_value = 30
            mock_limiter_class.return_value = mock_limiter
            
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(request)
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded for test_endpoint" in exc_info.value.detail
            assert exc_info.value.headers["Retry-After"] == "30"


def test_default_rate_limiter():
    """Test the default rate limiter instance."""
    assert isinstance(default_rate_limiter, RateLimiter)
    assert default_rate_limiter.requests_per_minute > 0
    assert default_rate_limiter.burst > 0