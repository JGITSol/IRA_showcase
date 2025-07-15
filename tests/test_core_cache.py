"""Tests for caching functionality."""

import json
import pickle
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.cache import CacheManager, cache, cached, cache_key_for_prediction


class TestCacheManager:
    """Test the CacheManager class."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a fresh cache manager instance."""
        return CacheManager()
    
    def test_init_redis_disabled(self, cache_manager):
        """Test initialization when cache is disabled."""
        with patch('app.core.cache.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = False
            
            cache_manager._initialize_redis()
            
            assert cache_manager.redis_client is None
    
    def test_init_redis_success(self, cache_manager):
        """Test successful Redis initialization."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        
        with patch('app.core.cache.redis.from_url') as mock_from_url, \
             patch('app.core.cache.settings') as mock_settings:
            
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URI = "redis://localhost:6379/0"
            mock_from_url.return_value = mock_redis
            
            cache_manager._initialize_redis()
            
            assert cache_manager.redis_client == mock_redis
            mock_redis.ping.assert_called_once()
    
    def test_init_redis_failure(self, cache_manager):
        """Test Redis initialization failure."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        with patch('app.core.cache.redis.from_url') as mock_from_url, \
             patch('app.core.cache.settings') as mock_settings:
            
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URI = "redis://localhost:6379/0"
            mock_from_url.return_value = mock_redis
            
            cache_manager._initialize_redis()
            
            assert cache_manager.redis_client is None
    
    def test_serialize_key(self, cache_manager):
        """Test cache key serialization."""
        key = cache_manager._serialize_key("test_key")
        assert key == "ira:test_key"
    
    def test_serialize_value_json(self, cache_manager):
        """Test value serialization with JSON."""
        value = {"key": "value", "number": 123}
        serialized = cache_manager._serialize_value(value)
        
        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode('utf-8'))
        assert deserialized == value
    
    def test_serialize_value_pickle(self, cache_manager):
        """Test value serialization with pickle for complex objects."""
        class CustomObject:
            def __init__(self, value):
                self.value = value
        
        value = CustomObject("test")
        serialized = cache_manager._serialize_value(value)
        
        assert isinstance(serialized, bytes)
        deserialized = pickle.loads(serialized)
        assert deserialized.value == "test"
    
    def test_deserialize_value_json(self, cache_manager):
        """Test value deserialization from JSON."""
        original = {"key": "value", "number": 123}
        serialized = json.dumps(original).encode('utf-8')
        
        deserialized = cache_manager._deserialize_value(serialized)
        assert deserialized == original
    
    def test_get_redis_success(self, cache_manager):
        """Test getting value from Redis."""
        mock_redis = Mock()
        mock_redis.get.return_value = b'{"key": "value"}'
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.get("test_key")
        
        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("ira:test_key")
    
    def test_get_redis_failure_fallback_memory(self, cache_manager):
        """Test fallback to memory cache when Redis fails."""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis error")
        cache_manager.redis_client = mock_redis
        cache_manager._memory_cache["ira:test_key"] = {"key": "value"}
        
        result = cache_manager.get("test_key")
        
        assert result == {"key": "value"}
    
    def test_get_not_found(self, cache_manager):
        """Test getting non-existent key."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.get("nonexistent_key")
        
        assert result is None
    
    def test_set_redis_success(self, cache_manager):
        """Test setting value in Redis."""
        mock_redis = Mock()
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.set("test_key", {"key": "value"}, ttl=3600)
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_set_redis_failure_fallback_memory(self, cache_manager):
        """Test fallback to memory cache when Redis set fails."""
        mock_redis = Mock()
        mock_redis.setex.side_effect = Exception("Redis error")
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.set("test_key", {"key": "value"})
        
        assert result is True
        assert cache_manager._memory_cache["ira:test_key"] == {"key": "value"}
    
    def test_delete_redis_success(self, cache_manager):
        """Test deleting value from Redis."""
        mock_redis = Mock()
        cache_manager.redis_client = mock_redis
        cache_manager._memory_cache["ira:test_key"] = {"key": "value"}
        
        result = cache_manager.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("ira:test_key")
        assert "ira:test_key" not in cache_manager._memory_cache
    
    def test_clear_redis_success(self, cache_manager):
        """Test clearing all cache entries."""
        mock_redis = Mock()
        mock_redis.keys.return_value = ["ira:key1", "ira:key2"]
        cache_manager.redis_client = mock_redis
        cache_manager._memory_cache["ira:key1"] = "value1"
        cache_manager._memory_cache["ira:key2"] = "value2"
        
        result = cache_manager.clear()
        
        assert result is True
        mock_redis.delete.assert_called_once_with("ira:key1", "ira:key2")
        assert len(cache_manager._memory_cache) == 0
    
    def test_health_check_redis_available(self, cache_manager):
        """Test health check when Redis is available."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {"used_memory": 1024}
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.health_check()
        
        assert result["redis_available"] is True
        assert "redis_info" in result
        assert "memory_cache_size" in result
    
    def test_health_check_redis_unavailable(self, cache_manager):
        """Test health check when Redis is unavailable."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Redis error")
        cache_manager.redis_client = mock_redis
        
        result = cache_manager.health_check()
        
        assert result["redis_available"] is False
        assert "memory_cache_size" in result


class TestCachedDecorator:
    """Test the cached decorator."""
    
    def test_cached_decorator_cache_hit(self):
        """Test cached decorator with cache hit."""
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = "cached_result"
            
            @cached(ttl=3600)
            def test_function(arg1, arg2):
                return f"result_{arg1}_{arg2}"
            
            result = test_function("a", "b")
            
            assert result == "cached_result"
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_not_called()
    
    def test_cached_decorator_cache_miss(self):
        """Test cached decorator with cache miss."""
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            @cached(ttl=3600)
            def test_function(arg1, arg2):
                return f"result_{arg1}_{arg2}"
            
            result = test_function("a", "b")
            
            assert result == "result_a_b"
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
    
    def test_cached_decorator_with_kwargs(self):
        """Test cached decorator with keyword arguments."""
        with patch('app.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            @cached(ttl=3600, key_prefix="test")
            def test_function(arg1, kwarg1=None):
                return f"result_{arg1}_{kwarg1}"
            
            result = test_function("a", kwarg1="b")
            
            assert result == "result_a_b"
            # Verify cache key includes prefix and arguments
            call_args = mock_cache.get.call_args[0][0]
            assert call_args.startswith("test:")


def test_cache_key_for_prediction():
    """Test prediction cache key generation."""
    key1 = cache_key_for_prediction(30, "male", 25.0, 2, True, "northeast")
    key2 = cache_key_for_prediction(30, "male", 25.0, 2, True, "northeast")
    key3 = cache_key_for_prediction(31, "male", 25.0, 2, True, "northeast")
    
    # Same inputs should generate same key
    assert key1 == key2
    
    # Different inputs should generate different keys
    assert key1 != key3
    
    # Key should be a valid MD5 hash
    assert len(key1) == 32
    assert all(c in "0123456789abcdef" for c in key1)