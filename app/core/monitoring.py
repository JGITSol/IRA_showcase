"""Monitoring and metrics collection."""

import time
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import contextmanager

import structlog
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions made',
    ['model_version', 'status']
)

PREDICTION_DURATION = Histogram(
    'prediction_duration_seconds',
    'Prediction processing time in seconds',
    ['model_version']
)

MODEL_LOAD_TIME = Gauge(
    'model_load_time_seconds',
    'Time taken to load the model'
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table', 'status']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active database connections'
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

APP_INFO = Info(
    'app_info',
    'Application information'
)

# Set application info
APP_INFO.info({
    'version': settings.VERSION,
    'environment': settings.ENVIRONMENT,
    'python_version': '3.11'
})


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get endpoint path template
        endpoint = request.url.path
        method = request.method
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            # Record error
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            
            logger.error(
                "Request failed",
                method=method,
                endpoint=endpoint,
                error=str(e),
                duration=time.time() - start_time
            )
            raise


def track_prediction(model_version: str = "v1"):
    """Decorator to track prediction metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error("Prediction failed", error=str(e))
                raise
            finally:
                duration = time.time() - start_time
                PREDICTION_COUNT.labels(
                    model_version=model_version,
                    status=status
                ).inc()
                PREDICTION_DURATION.labels(
                    model_version=model_version
                ).observe(duration)
                
        return wrapper
    return decorator


def track_cache_operation(operation: str):
    """Track cache operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                CACHE_OPERATIONS.labels(
                    operation=operation,
                    status=status
                ).inc()
        return wrapper
    return decorator


def track_database_operation(operation: str, table: str):
    """Track database operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                DATABASE_OPERATIONS.labels(
                    operation=operation,
                    table=table,
                    status=status
                ).inc()
        return wrapper
    return decorator


@contextmanager
def track_time(metric: Histogram):
    """Context manager to track execution time."""
    start_time = time.time()
    try:
        yield
    finally:
        metric.observe(time.time() - start_time)


class HealthChecker:
    """Health check utilities."""
    
    def __init__(self):
        self.checks = {}
    
    def add_check(self, name: str, check_func):
        """Add a health check."""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                if callable(check_func):
                    if hasattr(check_func, '__await__'):
                        check_result = await check_func()
                    else:
                        check_result = check_func()
                else:
                    check_result = {"status": "unknown"}
                
                results["checks"][name] = check_result
                
                if check_result.get("status") != "healthy":
                    overall_healthy = False
                    
            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_healthy = False
                logger.error(f"Health check failed: {name}", error=str(e))
        
        if not overall_healthy:
            results["status"] = "unhealthy"
        
        return results


# Global health checker
health_checker = HealthChecker()


def get_metrics() -> str:
    """Get Prometheus metrics."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get metrics content type."""
    return CONTENT_TYPE_LATEST