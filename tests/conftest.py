"""Pytest configuration and fixtures."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import UserModel
from app.models.prediction import PredictionModel
from app.core.security import get_password_hash


# Test database setup
@pytest.fixture(scope="session")
def test_db_url():
    """Create a temporary database URL for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_url = f"sqlite:///{tmp_file.name}"
        yield db_url
        # Cleanup
        try:
            os.unlink(tmp_file.name)
        except OSError:
            pass


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a new session for each test
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
        # Clean up all tables after each test
        for table in reversed(Base.metadata.sorted_tables):
            test_engine.execute(table.delete())


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = UserModel(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_superuser(test_db):
    """Create a test superuser."""
    user = UserModel(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_prediction(test_db, test_user):
    """Create a test prediction."""
    prediction = PredictionModel(
        user_id=test_user.id,
        age=30,
        sex="male",
        bmi=25.0,
        children=2,
        smoker=False,
        region="northeast",
        charges=10000.0,
        risk_score=5.0,
    )
    test_db.add(prediction)
    test_db.commit()
    test_db.refresh(prediction)
    return prediction


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, test_superuser):
    """Get authentication headers for admin user."""
    login_data = {
        "username": test_superuser.email,
        "password": "adminpassword123"
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_model():
    """Create a mock ML model for testing."""
    class MockModel:
        def predict(self, X):
            # Simple mock prediction based on smoker status
            if hasattr(X, 'iloc') and len(X) > 0:
                smoker_val = X.iloc[0].get('smoker', 0)
                base_charge = 10000
                smoker_penalty = 15000 if smoker_val else 0
                return [base_charge + smoker_penalty]
            return [10000]
        
        @property
        def feature_importances_(self):
            return [0.3, 0.2, 0.15, 0.15, 0.1, 0.1]
    
    return MockModel()


@pytest.fixture
def sample_prediction_data():
    """Sample prediction data for testing."""
    return {
        "age": 30,
        "sex": "male",
        "bmi": 25.0,
        "children": 2,
        "smoker": False,
        "region": "northeast"
    }


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
    os.environ["CACHE_ENABLED"] = "false"  # Disable cache for tests
    os.environ["RATE_LIMIT_ENABLED"] = "false"  # Disable rate limiting for tests
    os.environ["METRICS_ENABLED"] = "false"  # Disable metrics for tests
    yield
    # Cleanup is handled by pytest automatically