"""Application configuration settings."""

import os
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator, ConfigDict, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be overridden by environment variables with the same name.
    """
    # Pydantic configuration
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__"
    )

    # Application
    PROJECT_NAME: str = "Insurance Risk Analyzer"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    FRONTEND_URL: str = "http://localhost:3000"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]
    
    # Database
    DB_DRIVER: str = "postgresql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "insurance_risk"
    DB_POOL_SIZE: int = 10
    DB_POOL_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO_SQL: bool = False
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    SQLALCHEMY_ECHO: bool = False
    
    # Connection pool settings
    POOL_SIZE: int = 10
    POOL_OVERFLOW: int = 20
    POOL_RECYCLE: int = 3600
    SQL_ECHO: bool = False
    
    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        """Get the database URI based on the current configuration."""
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
            
        if self.DB_DRIVER == "sqlite":
            return f"sqlite:///./{self.DB_NAME}.db"
            
        return str(PostgresDsn.build(
            scheme="postgresql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        ))
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if v is not None:
            return v
            
        values = info.data
        if not all(key in values for key in ["DB_DRIVER", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]):
            return None
            
        if values["DB_DRIVER"] == "sqlite":
            return f"sqlite:///./{values.get('DB_NAME', 'app')}.db"
            
        return str(PostgresDsn.build(
            scheme="postgresql",
            username=values.get("DB_USER"),
            password=values.get("DB_PASSWORD"),
            host=values.get("DB_HOST"),
            port=values.get("DB_PORT", 5432),
            path=values.get('DB_NAME') or None,
        ))
    
    # Redis/Caching
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_ENABLED: bool = True
    
    @computed_field
    @property
    def REDIS_URI(self) -> str:
        """Get the Redis URI based on the current configuration."""
        if self.REDIS_URL:
            return self.REDIS_URL
        
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Model
    MODEL_PATH: str = "models/insurance_risk_model.pkl"
    FEATURE_STORE_PATH: str = "data/feature_store"
    MODEL_CACHE_TTL: int = 86400  # 24 hours
    PREDICTION_CACHE_TTL: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_MAX_SIZE: int = 10485760  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # Monitoring & Metrics
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus"
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True
    PERFORMANCE_MONITORING: bool = True
    
    # API Configuration
    API_TITLE: str = "Insurance Risk Analyzer API"
    API_DESCRIPTION: str = "Advanced Insurance Risk Analysis and Prediction System"
    API_VERSION: str = "1.0.0"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".json", ".xlsx"]
    UPLOAD_DIR: str = "uploads"
    
    # Email Configuration (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Celery Configuration (for async tasks)
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @computed_field
    @property
    def CELERY_BROKER(self) -> str:
        """Get the Celery broker URL."""
        return self.CELERY_BROKER_URL or self.REDIS_URI
    
    @computed_field
    @property
    def CELERY_BACKEND(self) -> str:
        """Get the Celery result backend URL."""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URI


# Create settings instance
settings = Settings()
