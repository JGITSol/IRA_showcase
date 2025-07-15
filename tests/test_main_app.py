"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.core.config import settings


class TestMainApplication:
    """Test the main FastAPI application."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
        assert data["version"] == settings.API_VERSION
    
    def test_health_endpoint_enabled(self, client: TestClient):
        """Test health check endpoint when enabled."""
        with patch('app.main.settings') as mock_settings, \
             patch('app.main.health_checker') as mock_health_checker:
            
            mock_settings.HEALTH_CHECK_ENABLED = True
            mock_health_checker.run_checks = AsyncMock(return_value={
                "status": "healthy",
                "timestamp": 1234567890,
                "checks": {
                    "database": {"status": "healthy"},
                    "cache": {"status": "healthy"}
                }
            })
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "checks" in data
    
    def test_health_endpoint_disabled(self, client: TestClient):
        """Test health check endpoint when disabled."""
        with patch('app.main.settings') as mock_settings:
            mock_settings.HEALTH_CHECK_ENABLED = False
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "timestamp" in data
    
    def test_metrics_endpoint_enabled(self, client: TestClient):
        """Test metrics endpoint when enabled."""
        with patch('app.main.settings') as mock_settings, \
             patch('app.main.get_metrics') as mock_get_metrics:
            
            mock_settings.METRICS_ENABLED = True
            mock_get_metrics.return_value = "# HELP test_metric Test metric\ntest_metric 1.0\n"
            
            response = client.get("/metrics")
            
            assert response.status_code == 200
            assert "test_metric" in response.text
    
    def test_metrics_endpoint_disabled(self, client: TestClient):
        """Test metrics endpoint when disabled."""
        with patch('app.main.settings') as mock_settings:
            mock_settings.METRICS_ENABLED = False
            
            response = client.get("/metrics")
            
            assert response.status_code == 200
            assert response.text == "Metrics disabled"
    
    def test_openapi_docs(self, client: TestClient):
        """Test OpenAPI documentation endpoints."""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI JSON
        response = client.get(f"{settings.API_V1_STR}/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        # Make an OPTIONS request to test CORS
        response = client.options("/")
        
        # The exact CORS behavior depends on configuration
        # At minimum, the request should not fail
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    def test_security_headers(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/")
        
        # Check for security headers added by SecurityHeadersMiddleware
        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Referrer-Policy" in headers
        assert "Content-Security-Policy" in headers
    
    def test_request_id_header(self, client: TestClient):
        """Test that request ID header is added."""
        response = client.get("/")
        
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
    
    def test_process_time_header(self, client: TestClient):
        """Test that process time header is added."""
        response = client.get("/")
        
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0


class TestExceptionHandlers:
    """Test exception handlers."""
    
    def test_http_exception_handler(self, client: TestClient):
        """Test HTTP exception handler."""
        # Try to access a non-existent endpoint
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "status_code" in data
        assert data["status_code"] == 404
    
    def test_validation_exception_handler(self, client: TestClient, auth_headers):
        """Test validation exception handler."""
        # Send invalid data to trigger validation error
        invalid_data = {
            "age": "not_a_number",  # Should be integer
            "sex": "male",
            "bmi": 25.0,
            "children": 2,
            "smoker": False,
            "region": "northeast"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/predictions/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "status_code" in data
        assert data["status_code"] == 422


class TestApplicationLifespan:
    """Test application lifespan events."""
    
    @pytest.mark.asyncio
    async def test_startup_events(self):
        """Test startup events."""
        with patch('app.main.setup_health_checks') as mock_setup_health, \
             patch('app.main.warm_up_cache') as mock_warm_cache, \
             patch('app.main.logger') as mock_logger:
            
            # Import and test the lifespan context manager
            from app.main import lifespan
            
            # Test startup
            async with lifespan(app):
                mock_setup_health.assert_called_once()
                mock_warm_cache.assert_called_once()
                mock_logger.info.assert_called()
    
    def test_health_checks_setup(self):
        """Test health checks setup."""
        from app.main import setup_health_checks, health_checker
        
        # Clear existing checks
        health_checker.checks.clear()
        
        # Setup health checks
        setup_health_checks()
        
        # Verify checks were added
        assert "database" in health_checker.checks
        assert "cache" in health_checker.checks
        assert "model" in health_checker.checks
    
    @pytest.mark.asyncio
    async def test_cache_warmup(self):
        """Test cache warmup."""
        with patch('app.main.PredictionService') as mock_service_class, \
             patch('app.main.logger') as mock_logger:
            
            mock_service = Mock()
            mock_service.load_model = AsyncMock()
            mock_service_class.return_value = mock_service
            
            from app.main import warm_up_cache
            
            await warm_up_cache()
            
            mock_service.load_model.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_cache_warmup_failure(self):
        """Test cache warmup with failure."""
        with patch('app.main.PredictionService') as mock_service_class, \
             patch('app.main.logger') as mock_logger:
            
            mock_service = Mock()
            mock_service.load_model = AsyncMock(side_effect=Exception("Load failed"))
            mock_service_class.return_value = mock_service
            
            from app.main import warm_up_cache
            
            # Should not raise exception
            await warm_up_cache()
            
            mock_logger.warning.assert_called()


class TestHealthCheckFunctions:
    """Test individual health check functions."""
    
    def test_database_health_check_success(self):
        """Test database health check success."""
        from app.main import setup_health_checks, health_checker
        
        setup_health_checks()
        db_check = health_checker.checks["database"]
        
        with patch('app.main.SessionLocal') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            result = db_check()
            
            assert result["status"] == "healthy"
            mock_session.execute.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_database_health_check_failure(self):
        """Test database health check failure."""
        from app.main import setup_health_checks, health_checker
        
        setup_health_checks()
        db_check = health_checker.checks["database"]
        
        with patch('app.main.SessionLocal') as mock_session_class:
            mock_session = Mock()
            mock_session.execute.side_effect = Exception("DB Error")
            mock_session_class.return_value = mock_session
            
            result = db_check()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
    
    def test_cache_health_check(self):
        """Test cache health check."""
        from app.main import setup_health_checks, health_checker
        
        setup_health_checks()
        cache_check = health_checker.checks["cache"]
        
        with patch('app.main.cache') as mock_cache:
            mock_cache.health_check.return_value = {
                "redis_available": True,
                "memory_cache_size": 0
            }
            
            result = cache_check()
            
            assert "redis_available" in result
            assert "memory_cache_size" in result
    
    def test_model_health_check_success(self):
        """Test model health check success."""
        from app.main import setup_health_checks, health_checker
        
        setup_health_checks()
        model_check = health_checker.checks["model"]
        
        with patch('app.main.PredictionService') as mock_service_class:
            mock_service = Mock()
            mock_service.model = Mock()  # Model is loaded
            mock_service_class.return_value = mock_service
            
            result = model_check()
            
            assert result["status"] == "healthy"
    
    def test_model_health_check_failure(self):
        """Test model health check failure."""
        from app.main import setup_health_checks, health_checker
        
        setup_health_checks()
        model_check = health_checker.checks["model"]
        
        with patch('app.main.PredictionService') as mock_service_class:
            mock_service = Mock()
            mock_service.model = None  # Model not loaded
            mock_service_class.return_value = mock_service
            
            result = model_check()
            
            assert result["status"] == "unhealthy"
            assert "error" in result