"""Tests for prediction service."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.prediction import PredictionService, prediction_service


def _default_metadata() -> dict:
    """Construct representative metadata payload for tests."""
    return {
        "trained_at": "2024-01-01T00:00:00",
        "target_summary": {"std": 2500.0, "mean": 18000.0},
        "target_quantiles": [float(x) for x in np.linspace(2000, 60000, 101)],
        "feature_importance": {
            "age": 0.3,
            "sex": 0.05,
            "bmi": 0.25,
            "children": 0.1,
            "smoker": 0.2,
            "region": 0.1,
        },
        "categorical_levels": {
            "sex": ["female", "male"],
            "region": ["northeast", "northwest", "southeast", "southwest"],
            "smoker": [False, True],
        },
        "metrics": {
            "train": {"r2": 0.95, "mae": 1050.0, "rmse": 1800.0},
            "test": {"r2": 0.88, "mae": 1600.0, "rmse": 2400.0},
        },
    }


class TestPredictionService:
    """Test the PredictionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh prediction service instance."""
        return PredictionService()
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline with predictable behaviour."""
        preprocessor = Mock()
        preprocessor.transform.return_value = np.array([[0.1, 0.2, 0.3]])

        regressor = Mock()
        estimators = [Mock(), Mock(), Mock()]
        outputs = [np.array([14500.0]), np.array([15000.0]), np.array([15500.0])]
        for estimator, output in zip(estimators, outputs):
            estimator.predict.return_value = output
        regressor.estimators_ = estimators

        pipeline = Mock()
        pipeline.predict.return_value = np.array([15000.0])
        pipeline.named_steps = {"preprocessor": preprocessor, "regressor": regressor}
        return pipeline
    
    def test_init(self, service):
        """Test service initialization."""
        assert service.model is None
        assert service.metadata == {}
        assert service.model_version == "v1.0"
        assert service.feature_columns == ['age', 'sex', 'bmi', 'children', 'smoker', 'region']
    
    @pytest.mark.asyncio
    async def test_load_model_from_cache(self, service, mock_pipeline):
        """Test loading model from cache."""
        metadata = _default_metadata()
        payload = {
            'model': mock_pipeline,
            'metadata': metadata,
            'feature_columns': service.feature_columns,
        }

        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = payload

            result = await service.load_model()

            assert result is True
            assert service.model == mock_pipeline
            assert service.metadata == metadata
            mock_cache.get.assert_called_once_with(f"model:{service.model_version}")
    
    @pytest.mark.asyncio
    async def test_load_model_from_file(self, service, mock_pipeline):
        """Test loading model from file."""
        metadata = _default_metadata()
        model_data = {
            'model': mock_pipeline,
            'metadata': metadata,
            'feature_columns': service.feature_columns,
        }

        with patch('app.services.prediction.cache') as mock_cache, \
             patch('app.services.prediction.Path') as mock_path, \
             patch('app.services.prediction.joblib') as mock_joblib:

            mock_cache.get.return_value = None
            mock_path.return_value.exists.return_value = True
            mock_joblib.load.return_value = model_data

            result = await service.load_model()

            assert result is True
            assert service.model == mock_pipeline
            assert service.metadata == metadata
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_model_train_new(self, service):
        """Test training new model when file doesn't exist."""
        with patch('app.services.prediction.cache') as mock_cache, \
             patch('app.services.prediction.Path') as mock_path, \
             patch.object(service, '_train_model') as mock_train:
            
            # Cache miss
            mock_cache.get.return_value = None
            
            # File doesn't exist
            mock_path.return_value.exists.return_value = False
            
            result = await service.load_model()
            
            assert result is True
            mock_train.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_train_model(self, service, mock_pipeline):
        """Test model training."""
        metadata = _default_metadata()
        artifact = SimpleNamespace(model=mock_pipeline, metadata=metadata)

        with patch('app.services.prediction.load_training_dataframe') as mock_load, \
             patch('app.services.prediction.train_model_from_dataframe') as mock_train, \
             patch('app.services.prediction.joblib') as mock_joblib, \
             patch('app.services.prediction.cache') as mock_cache, \
             patch('app.services.prediction.Path') as mock_path:

            mock_load.return_value = pd.DataFrame()
            mock_train.return_value = artifact
            mock_path.return_value.parent.mkdir = Mock()

            await service._train_model()

            assert service.model == mock_pipeline
            assert service.metadata == metadata
            mock_joblib.dump.assert_called_once()
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_success(self, service, mock_pipeline):
        """Test successful prediction."""
        service.model = mock_pipeline
        service.metadata = _default_metadata()

        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = None

            result = await service.predict(
                age=40,
                sex="male",
                bmi=28.5,
                children=2,
                smoker=False,
                region="northeast"
            )

            assert pytest.approx(result["predicted_charges"], rel=1e-6) == 15000.0
            assert 0 <= result["risk_score"] <= 100
            assert 0 <= result["confidence"] <= 1
            assert "confidence_interval" in result
            assert result["confidence_interval"]["lower"] <= result["predicted_charges"] <= result["confidence_interval"]["upper"]
            assert result["feature_importance"] == service.metadata["feature_importance"]
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_cache_hit(self, service):
        """Test prediction with cache hit."""
        cached_result = {
            "predicted_charges": 12000.0,
            "risk_score": 35.0,
            "feature_importance": {},
            "model_version": "v1.0",
            "confidence": 0.9,
            "confidence_interval": {"lower": 10000.0, "upper": 14000.0},
        }
        
        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = cached_result
            
            result = await service.predict(
                age=30,
                sex="male",
                bmi=25.0,
                children=2,
                smoker=False,
                region="northeast"
            )
            
            assert result == cached_result
    
    @pytest.mark.asyncio
    async def test_predict_model_not_loaded(self, service):
        """Test prediction when model is not loaded."""
        with patch.object(service, 'load_model') as mock_load:
            mock_load.return_value = True
            service.model = None  # Simulate load failure
            
            with pytest.raises(ValueError, match="Model not available"):
                await service.predict(
                    age=30,
                    sex="male",
                    bmi=25.0,
                    children=2,
                    smoker=False,
                    region="northeast"
                )
    
    @pytest.mark.asyncio
    async def test_predict_invalid_category(self, service, mock_pipeline):
        """Test prediction with invalid category."""
        service.model = mock_pipeline
        service.metadata = _default_metadata()

        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = None

            with pytest.raises(ValueError, match="Unknown category for sex"):
                await service.predict(
                    age=30,
                    sex="invalid",
                    bmi=25.0,
                    children=2,
                    smoker=False,
                    region="northeast"
                )
    
    def test_get_model_info_not_loaded(self, service):
        """Test getting model info when model is not loaded."""
        result = service.get_model_info()
        assert result["status"] == "not_loaded"
    
    def test_get_model_info_loaded(self, service, mock_pipeline):
        """Test getting model info when model is loaded."""
        service.model = mock_pipeline
        service.metadata = _default_metadata()

        result = service.get_model_info()

        assert result["status"] == "loaded"
        assert result["version"] == "v1.0"
        assert result["feature_columns"] == service.feature_columns
        assert result["metrics"] == service.metadata["metrics"]
        assert result["categorical_levels"] == service.metadata["categorical_levels"]
        assert result["n_features"] == len(service.feature_columns)


def test_prediction_service_singleton() -> None:
    """Ensure the module-level prediction service is instantiated."""
    assert isinstance(prediction_service, PredictionService)