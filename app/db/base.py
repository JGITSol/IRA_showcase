"""Database configuration and base model."""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings

# Type variables for generic model and schema types
ModelType = TypeVar("ModelType", bound="Base")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Base(DeclarativeBase):
    """Base database model with common fields and methods.
    
    Uses SQLAlchemy 2.0 style declarative base.
    """
    
    # Common columns with type annotations
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    @classmethod
    def get_db(cls) -> Session:
        """Get database session.
        
        Returns:
            Session: Database session
        """
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def create(cls, db: Session, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> "Base":
        """Create a new record."""
        obj_in_data = obj_in if isinstance(obj_in, dict) else obj_in.dict()
        db_obj = cls(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @classmethod
    def get(cls, db: Session, id: Any) -> Optional["Base"]:
        """Get a record by ID."""
        return db.query(cls).filter(cls.id == id).first()
    
    @classmethod
    def get_multi(
        cls, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List["Base"]:
        """Get multiple records with pagination."""
        return db.query(cls).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> "Base":
        """Update a record."""
        obj_data = self.to_dict()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(self, field, update_data[field])
        
        db.add(self)
        db.commit()
        db.refresh(self)
        return self
    
    def delete(self, db: Session) -> "Base":
        """Delete a record."""
        db.delete(self)
        db.commit()
        return self
