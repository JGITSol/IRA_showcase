"""Database models for the Insurance Risk Analyzer."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Prediction(Base):
    """Insurance risk prediction model."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Input features
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    bmi = Column(Float, nullable=False)
    children = Column(Integer, nullable=False)
    smoker = Column(Boolean, nullable=False)
    region = Column(String(50), nullable=False)
    
    # Prediction results
    predicted_charges = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=False)
    
    # Additional metadata
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    prediction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self) -> str:
        return f"<Prediction {self.id} - {self.predicted_charges}>"


class ModelVersion(Base):
    """Tracks different versions of the ML model."""
    
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    path = Column(String(255), nullable=False)
    is_production = Column(Boolean, default=False, nullable=False)
    metrics = Column(Text, nullable=True)  # Serialized JSON of model metrics
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ModelVersion {self.version}>"


class FeatureImportance(Base):
    """Stores feature importance for model interpretability."""
    
    __tablename__ = "feature_importances"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    feature_name = Column(String(100), nullable=False)
    importance_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<FeatureImportance {self.feature_name}: {self.importance_score}>"
