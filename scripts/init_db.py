#!/usr/bin/env python3
"""Initialize the database with initial data."""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.base import Base
from app.db.init_db import init_db, reset_db
from app.db.session import SessionLocal, engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database() -> None:
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database...")
    reset_db(engine)
    logger.info("Database reset complete")

def initialize_database() -> None:
    """Initialize the database with initial data."""
    logger.info("Initializing database...")
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the database by dropping and recreating all tables",
    )
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    
    initialize_database()
