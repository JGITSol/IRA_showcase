"""Tests for monitoring and metrics functionality."""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, Response
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from app.core.monitoring import (
    MetricsMiddleware,
    track_prediction,
    track_cache_operation,
    track_database_operation,
    track_time,
    HealthChecker,
    get_metrics,
    REQUEST_COUNT,
    REQUEST_DURATION,
    PREDICTION_COUNT,
    ERROR_COUNT
)


class TestMetricsMiddleware:
    """Test the MetricsMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create a metrics middleware instance."""
        app = Starlette()
        return MetricsMiddleware(app)
    
    @pytest.mark.asyncio
    async def test_successful_request(self, middleware):
        """Test middleware with successful request."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/test"
        
        response = Mock(spec=Response)
        response.status_code = 200
        
        async def call_next(req):
            return response
        
        with patch('app.core.monitoring.REQUEST_COUNT') as mock_counter, \
             patch('app.core.monitoring.REQUEST_DURATION') as mock_histogram:
            
            result = await middleware.dispatch(request, call_next)
            
            assert result == response
            mock_counter.labels.assert_called_once_with(
                method="GET",
                endpoint="/test",
                status_code=200
            )
            mock_counter.labels.return_value.inc.assert_called_once()
            mock_histogram.labels.assert_called_once_with(
                method="GET",
                endpoint="/test"
            )
            mock_histogram.labels.return_value.observe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_failed_request(self, middleware):
        """Test middleware with failed request."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/error"
        
        async def call_next(req):
            raise ValueError("Test error")
        
        with patch('app.core.monitoring.ERROR_COUNT') as mock_error_counter, \
             patch('app.core.monitoring.logger') as mock_logger:
            
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)
            
            mock_error_counter.labels.assert_called_once_with(
                error_type="ValueError",
                endpoint="/error"
            )
            mock_error_counter.labels.return_value.inc.assert_called_once()
            mock_logger.error.assert_called_once()


class TestTrackingDecorators:
    """Test the tracking decorators."""
    
    def test_track_prediction_success(self):
        """Test prediction tracking decorator with success."""
        with patch('app.core.monitoring.PREDICTION_COUNT') as mock_counter, \
             patch('app.core.monitoring.PREDICTION_DURATION') as mock_histogram:
            
            @track_prediction(model_version="v2.0")
            def test_prediction():
                return "prediction_result"
            
            result = test_prediction()
            
            assert result == "prediction_result"
            mock_counter.labels.assert_called_once_with(
                model_version="v2.0",
                status="success"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
            mock_histogram.labels.assert_called_once_with(model_version="v2.0")
            mock_histogram.labels.return_value.observe.assert_called_once()
    
    def test_track_prediction_error(self):
        """Test prediction tracking decorator with error."""
        with patch('app.core.monitoring.PREDICTION_COUNT') as mock_counter, \
             patch('app.core.monitoring.PREDICTION_DURATION') as mock_histogram, \
             patch('app.core.monitoring.logger') as mock_logger:
            
            @track_prediction(model_version="v2.0")
            def test_prediction():
                raise ValueError("Prediction failed")
            
            with pytest.raises(ValueError):
                test_prediction()
            
            mock_counter.labels.assert_called_once_with(
                model_version="v2.0",
                status="error"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
            mock_logger.error.assert_called_once()
    
    def test_track_cache_operation_success(self):
        """Test cache operation tracking decorator with success."""
        with patch('app.core.monitoring.CACHE_OPERATIONS') as mock_counter:
            
            @track_cache_operation("get")
            def test_cache_get():
                return "cached_value"
            
            result = test_cache_get()
            
            assert result == "cached_value"
            mock_counter.labels.assert_called_once_with(
                operation="get",
                status="success"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
    
    def test_track_cache_operation_error(self):
        """Test cache operation tracking decorator with error."""
        with patch('app.core.monitoring.CACHE_OPERATIONS') as mock_counter:
            
            @track_cache_operation("set")
            def test_cache_set():
                raise Exception("Cache error")
            
            with pytest.raises(Exception):
                test_cache_set()
            
            mock_counter.labels.assert_called_once_with(
                operation="set",
                status="error"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
    
    def test_track_database_operation_success(self):
        """Test database operation tracking decorator with success."""
        with patch('app.core.monitoring.DATABASE_OPERATIONS') as mock_counter:
            
            @track_database_operation("select", "users")
            def test_db_select():
                return [{"id": 1, "name": "test"}]
            
            result = test_db_select()
            
            assert len(result) == 1
            mock_counter.labels.assert_called_once_with(
                operation="select",
                table="users",
                status="success"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
    
    def test_track_database_operation_error(self):
        """Test database operation tracking decorator with error."""
        with patch('app.core.monitoring.DATABASE_OPERATIONS') as mock_counter:
            
            @track_database_operation("insert", "users")
            def test_db_insert():
                raise Exception("Database error")
            
            with pytest.raises(Exception):
                test_db_insert()
            
            mock_counter.labels.assert_called_once_with(
                operation="insert",
                table="users",
                status="error"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
    
    def test_track_time_context_manager(self):
        """Test the track_time context manager."""
        mock_histogram = Mock()
        
        with track_time(mock_histogram):
            time.sleep(0.01)  # Small delay
        
        mock_histogram.observe.assert_called_once()
        # Verify that some time was recorded
        call_args = mock_histogram.observe.call_args[0][0]
        assert call_args > 0


class TestHealthChecker:
    """Test the HealthChecker class."""
    
    @pytest.fixture
    def health_checker(self):
        """Create a health checker instance."""
        return HealthChecker()
    
    def test_add_check(self, health_checker):
        """Test adding a health check."""
        def test_check():
            return {"status": "healthy"}
        
        health_checker.add_check("test", test_check)
        
        assert "test" in health_checker.checks
        assert health_checker.checks["test"] == test_check
    
    @pytest.mark.asyncio
    async def test_run_checks_all_healthy(self, health_checker):
        """Test running health checks when all are healthy."""
        def check1():
            return {"status": "healthy"}
        
        async def check2():
            return {"status": "healthy"}
        
        health_checker.add_check("check1", check1)
        health_checker.add_check("check2", check2)
        
        result = await health_checker.run_checks()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert len(result["checks"]) == 2
        assert result["checks"]["check1"]["status"] == "healthy"
        assert result["checks"]["check2"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_run_checks_some_unhealthy(self, health_checker):
        """Test running health checks when some are unhealthy."""
        def healthy_check():
            return {"status": "healthy"}
        
        def unhealthy_check():
            return {"status": "unhealthy", "error": "Service down"}
        
        health_checker.add_check("healthy", healthy_check)
        health_checker.add_check("unhealthy", unhealthy_check)
        
        result = await health_checker.run_checks()
        
        assert result["status"] == "unhealthy"
        assert result["checks"]["healthy"]["status"] == "healthy"
        assert result["checks"]["unhealthy"]["status"] == "unhealthy"
        assert result["checks"]["unhealthy"]["error"] == "Service down"
    
    @pytest.mark.asyncio
    async def test_run_checks_with_exception(self, health_checker):
        """Test running health checks when one throws an exception."""
        def failing_check():
            raise Exception("Check failed")
        
        def working_check():
            return {"status": "healthy"}
        
        health_checker.add_check("failing", failing_check)
        health_checker.add_check("working", working_check)
        
        with patch('app.core.monitoring.logger') as mock_logger:
            result = await health_checker.run_checks()
        
        assert result["status"] == "unhealthy"
        assert result["checks"]["failing"]["status"] == "unhealthy"
        assert "error" in result["checks"]["failing"]
        assert result["checks"]["working"]["status"] == "healthy"
        mock_logger.error.assert_called_once()


def test_get_metrics():
    """Test getting Prometheus metrics."""
    with patch('app.core.monitoring.generate_latest') as mock_generate:
        mock_generate.return_value = "# HELP test_metric Test metric\n"
        
        result = get_metrics()
        
        assert result == "# HELP test_metric Test metric\n"
        mock_generate.assert_called_once()


def test_get_metrics_content_type():
    """Test getting metrics content type."""
    from app.core.monitoring import get_metrics_content_type, CONTENT_TYPE_LATEST
    
    result = get_metrics_content_type()
    assert result == CONTENT_TYPE_LATEST