"""Database initialization script."""

import logging
from typing import Any

from sqlalchemy.engine import Engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, get_db
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth import get_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Any) -> None:
    """Initialize the database with initial data.
    
    Args:
        db: Database session
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Create default superuser if it doesn't exist
    user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name="Admin",
            is_superuser=True,
        )
        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created superuser {settings.FIRST_SUPERUSER}")
    else:
        logger.info(f"Superuser {settings.FIRST_SUPERUSER} already exists")


def reset_db(engine: Engine) -> None:
    """Drop and recreate all database tables.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("Dropped all tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Recreated all tables")


if __name__ == "__main__":
    # Initialize the database
    db = next(get_db())
    try:
        init_db(db)
    finally:
        db.close()
