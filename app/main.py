"""Main FastAPI application."""

import asyncio
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.monitoring import (
    MetricsMiddleware, 
    health_checker, 
    get_metrics, 
    get_metrics_content_type
)
from app.core.rate_limiting import RateLimitMiddleware
from app.core.cache import cache
from app.db.session import engine

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Insurance Risk Analyzer API")
    
    # Initialize health checks
    setup_health_checks()
    
    # Warm up cache
    await warm_up_cache()
    
    logger.info("Startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Insurance Risk Analyzer API")
    
    # Close database connections
    if engine:
        await engine.dispose()
    
    logger.info("Shutdown completed")


def setup_health_checks():
    """Set up health check functions."""
    
    def database_health():
        """Check database connectivity."""
        try:
            # Simple database check
            from app.db.session import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def cache_health():
        """Check cache connectivity."""
        return cache.health_check()
    
    def model_health():
        """Check if model is available."""
        try:
            from app.services.prediction import PredictionService
            service = PredictionService()
            if service.model is not None:
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": "Model not loaded"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    # Register health checks
    health_checker.add_check("database", database_health)
    health_checker.add_check("cache", cache_health)
    health_checker.add_check("model", model_health)


async def warm_up_cache():
    """Warm up the cache with frequently used data."""
    try:
        # Pre-load model if needed
        from app.services.prediction import PredictionService
        service = PredictionService()
        await service.load_model()
        logger.info("Model pre-loaded successfully")
    except Exception as e:
        logger.warning("Failed to pre-load model", error=str(e))


# Set up logging first
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}{settings.OPENAPI_URL}",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)

# Set up middleware
setup_middleware(app)

# Add monitoring middleware
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(
        "Validation error",
        errors=exc.errors(),
        url=str(request.url)
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "status_code": 422}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url)
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Comprehensive health check endpoint.
    
    Returns:
        dict: Detailed health status of all components
    """
    if settings.HEALTH_CHECK_ENABLED:
        return await health_checker.run_checks()
    else:
        return {"status": "ok", "timestamp": time.time()}


# Metrics endpoint
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    if settings.METRICS_ENABLED:
        return PlainTextResponse(
            get_metrics(),
            media_type=get_metrics_content_type()
        )
    else:
        return PlainTextResponse("Metrics disabled")


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Welcome to the Insurance Risk Analyzer API",
        "version": settings.API_VERSION,
        "docs_url": settings.DOCS_URL,
        "health_url": "/health",
        "metrics_url": "/metrics" if settings.METRICS_ENABLED else None
    }
