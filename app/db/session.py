"""Enhanced database session management with async support, connection pooling, and monitoring."""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

import structlog
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.monitoring import ACTIVE_CONNECTIONS, DATABASE_OPERATIONS, track_database_operation
from app.db.base import Base

logger = structlog.get_logger(__name__)

def get_async_engine() -> AsyncEngine:
    """Get the async database engine with enhanced configuration."""
    db_url = str(settings.DATABASE_URI)
    
    if db_url.startswith("sqlite"):
        # For SQLite, use aiosqlite
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        engine = create_async_engine(
            db_url,
            echo=settings.DB_ECHO_SQL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    elif db_url.startswith("postgresql"):
        # For PostgreSQL, use asyncpg
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(
            db_url,
            echo=settings.DB_ECHO_SQL,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
    else:
        raise ValueError(f"Unsupported database URL: {db_url}")
    
    # Add connection event listeners for monitoring
    @event.listens_for(engine.sync_engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        ACTIVE_CONNECTIONS.inc()
        logger.debug("Database connection established")
    
    @event.listens_for(engine.sync_engine, "close")
    def on_close(dbapi_connection, connection_record):
        ACTIVE_CONNECTIONS.dec()
        logger.debug("Database connection closed")
    
    return engine


def get_sync_engine():
    """Get the synchronous database engine for migrations and tests."""
    db_url = str(settings.DATABASE_URI)
    
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            echo=settings.DB_ECHO_SQL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    elif db_url.startswith("postgresql"):
        engine = create_engine(
            db_url,
            echo=settings.DB_ECHO_SQL,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            poolclass=QueuePool,
        )
    else:
        raise ValueError(f"Unsupported database URL: {db_url}")
    
    return engine


# Create engines and session factories
async_engine = get_async_engine()
sync_engine = get_sync_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=sync_engine
)


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with monitoring.
    
    Yields:
        AsyncSession: An async database session
    """
    start_time = time.time()
    async with AsyncSessionLocal() as session:
        try:
            # Health check
            await session.execute(text("SELECT 1"))
            yield session
            await session.commit()
            
            # Track successful operation
            DATABASE_OPERATIONS.labels(
                operation="session",
                table="all",
                status="success"
            ).inc()
            
        except Exception as e:
            await session.rollback()
            
            # Track failed operation
            DATABASE_OPERATIONS.labels(
                operation="session",
                table="all",
                status="error"
            ).inc()
            
            logger.error(
                "Database session error",
                error=str(e),
                duration=time.time() - start_time
            )
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Get a synchronous database session for migrations and tests.
    
    Yields:
        Session: A synchronous database session
    """
    start_time = time.time()
    db = SessionLocal()
    try:
        yield db
        db.commit()
        
        # Track successful operation
        DATABASE_OPERATIONS.labels(
            operation="sync_session",
            table="all",
            status="success"
        ).inc()
        
    except Exception as e:
        db.rollback()
        
        # Track failed operation
        DATABASE_OPERATIONS.labels(
            operation="sync_session",
            table="all",
            status="error"
        ).inc()
        
        logger.error(
            "Sync database session error",
            error=str(e),
            duration=time.time() - start_time
        )
        raise
    finally:
        db.close()


# Legacy sync function for FastAPI dependencies
def get_db() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection.
    
    Yields:
        Session: Database session
    """
    with get_sync_db() as db:
        yield db


async def init_db() -> None:
    """Initialize the database with proper error handling.
    
    Creates all database tables and sets up initial configuration.
    """
    try:
        logger.info("Initializing database")
        
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # For SQLite, enable foreign key support
        if "sqlite" in str(settings.DATABASE_URI):
            async with async_engine.connect() as conn:
                await conn.execute(text("PRAGMA foreign_keys=ON"))
                await conn.commit()
        
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


async def check_db_health() -> dict:
    """Check database connectivity and health."""
    try:
        async with get_async_db() as db:
            result = await db.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                return {
                    "status": "healthy",
                    "database_type": "postgresql" if "postgresql" in str(settings.DATABASE_URI) else "sqlite",
                    "pool_size": settings.DB_POOL_SIZE,
                    "active_connections": ACTIVE_CONNECTIONS._value._value
                }
            else:
                return {"status": "unhealthy", "error": "Health check query failed"}
                
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as a context manager with automatic transaction handling.
    
    Yields:
        Session: Database session
    """
    with get_sync_db() as db:
        yield db


# Expose the engine for migrations and other uses
engine = sync_engine
