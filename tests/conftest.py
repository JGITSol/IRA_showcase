"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Environment variables are set in the `setup_test_environment` fixture.


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


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


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment
    os.environ.update({
        "ENVIRONMENT": "testing",
        "SECRET_KEY": "test-secret-key-for-testing",
        "CACHE_ENABLED": "false",
        "RATE_LIMIT_ENABLED": "false",
        "METRICS_ENABLED": "false"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)