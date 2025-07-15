"""Alembic environment configuration.

This module configures the Alembic environment for database migrations.
It supports both synchronous and asynchronous database operations.
"""

import asyncio
import logging
import os
from logging.config import fileConfig
from typing import Any, Dict, Optional

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Import the models to ensure they are loaded and their metadata is available
# This is necessary for 'autogenerate' to work properly
from app.db.base import Base  # noqa: F401
from app.core.config import settings

# This is the Alembic Config object, which provides access to the .ini file
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get the SQLAlchemy URL from settings
DATABASE_URL = str(settings.DATABASE_URI)

# Set up logging
logger = logging.getLogger("alembic")

# Target metadata for autogenerate support
target_metadata = Base.metadata

def get_url() -> str:
    """Get the database URL from environment variables or config."""
    # First try to get from environment
    url = os.getenv("DATABASE_URL")
    if url:
        logger.info("Using DATABASE_URL from environment")
        return url
    
    # Then try to get from settings
    if hasattr(settings, "DATABASE_URI") and settings.DATABASE_URI:
        logger.info("Using DATABASE_URI from settings")
        return str(settings.DATABASE_URI)
    
    # Finally, try to get from alembic.ini
    url = config.get_main_option("sqlalchemy.url")
    if url:
        logger.info("Using sqlalchemy.url from alembic.ini")
        return url
    
    raise ValueError("No database URL configured. Set DATABASE_URL or configure sqlalchemy.url in alembic.ini")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create and configure a Connection
    and then run the migrations within a transaction.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine.

    This function creates an async engine and runs the migrations.
    """
    url = get_url()
    
    # Check if we should use async driver
    if url.startswith(('postgresql+asyncpg', 'postgresql+asyncpg', 'mysql+asyncmy', 'sqlite+aiosqlite')):
        # Create async engine
        connectable = create_async_engine(
            url,
            poolclass=pool.NullPool,
            echo=settings.SQL_ECHO,
        )
        
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
            
        await connectable.dispose()
    else:
        # Fall back to synchronous engine for databases without async support
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            url=url,
        )
        
        with connectable.connect() as connection:
            do_run_migrations(connection)
        
        connectable.dispose()


# Main execution
if context.is_offline_mode():
    logger.info("Running migrations in offline mode")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode")
    asyncio.run(run_migrations_online())
