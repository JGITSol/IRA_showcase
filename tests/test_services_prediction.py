"""Tests for prediction service."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from app.services.prediction import PredictionService, prediction_service


class TestPredictionService:
    """Test the PredictionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh prediction service instance."""
        return PredictionService()
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock ML model."""
        model = Mock()
        model.predict.return_value = np.array([15000.0])
        model.feature_importances_ = np.array([0.3, 0.2, 0.15, 0.15, 0.1, 0.1])
        return model
    
    @pytest.fixture
    def mock_encoders(self):
        """Create mock label encoders."""
        sex_encoder = Mock()
        sex_encoder.transform.return_value = np.array([0])  # male = 0
        
        region_encoder = Mock()
        region_encoder.transform.return_value = np.array([0])  # northeast = 0
        
        return {
            'sex': sex_encoder,
            'region': region_encoder
        }
    
    def test_init(self, service):
        """Test service initialization."""
        assert service.model is None
        assert service.label_encoders == {}
        assert service.model_version == "v1.0"
        assert service.feature_columns == ['age', 'sex', 'bmi', 'children', 'smoker', 'region']
    
    @pytest.mark.asyncio
    async def test_load_model_from_cache(self, service):
        """Test loading model from cache."""
        mock_model = Mock()
        mock_encoders = {'sex': Mock(), 'region': Mock()}
        
        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = {
                'model': mock_model,
                'encoders': mock_encoders
            }
            
            result = await service.load_model()
            
            assert result is True
            assert service.model == mock_model
            assert service.label_encoders == mock_encoders
            mock_cache.get.assert_called_once_with(f"model:{service.model_version}")
    
    @pytest.mark.asyncio
    async def test_load_model_from_file(self, service):
        """Test loading model from file."""
        mock_model = Mock()
        mock_encoders = {'sex': Mock(), 'region': Mock()}
        model_data = {
            'model': mock_model,
            'encoders': mock_encoders
        }
        
        with patch('app.services.prediction.cache') as mock_cache, \
             patch('app.services.prediction.Path') as mock_path, \
             patch('app.services.prediction.joblib') as mock_joblib:
            
            # Cache miss
            mock_cache.get.return_value = None
            
            # File exists
            mock_path.return_value.exists.return_value = True
            
            # Load from file
            mock_joblib.load.return_value = model_data
            
            result = await service.load_model()
            
            assert result is True
            assert service.model == mock_model
            assert service.label_encoders == mock_encoders
            
            # Verify caching
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
    async def test_train_model(self, service):
        """Test model training."""
        mock_model = Mock()
        mock_model.fit.return_value = None
        
        with patch('app.services.prediction.RandomForestRegressor') as mock_rf, \
             patch('app.services.prediction.LabelEncoder') as mock_le, \
             patch('app.services.prediction.joblib') as mock_joblib, \
             patch('app.services.prediction.cache') as mock_cache, \
             patch('app.services.prediction.Path') as mock_path:
            
            mock_rf.return_value = mock_model
            mock_le.return_value.fit_transform.return_value = np.array([0, 1])
            mock_path.return_value.parent.mkdir = Mock()
            
            await service._train_model()
            
            assert service.model == mock_model
            assert 'sex' in service.label_encoders
            assert 'region' in service.label_encoders
            
            # Verify model was saved
            mock_joblib.dump.assert_called_once()
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_success(self, service, mock_model, mock_encoders):
        """Test successful prediction."""
        service.model = mock_model
        service.label_encoders = mock_encoders
        
        with patch('app.services.prediction.cache') as mock_cache:
            # Cache miss
            mock_cache.get.return_value = None
            
            result = await service.predict(
                age=30,
                sex="male",
                bmi=25.0,
                children=2,
                smoker=False,
                region="northeast"
            )
            
            assert result["predicted_charges"] == 15000.0
            assert "risk_score" in result
            assert "feature_importance" in result
            assert result["model_version"] == "v1.0"
            assert "confidence" in result
            
            # Verify caching
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_cache_hit(self, service):
        """Test prediction with cache hit."""
        cached_result = {
            "predicted_charges": 12000.0,
            "risk_score": 4.0,
            "feature_importance": {},
            "model_version": "v1.0",
            "confidence": 0.85
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
    async def test_predict_invalid_category(self, service, mock_model):
        """Test prediction with invalid category."""
        service.model = mock_model
        service.label_encoders = {'sex': Mock(), 'region': Mock()}
        
        # Make encoder raise ValueError for unknown category
        service.label_encoders['sex'].transform.side_effect = ValueError("Unknown category")
        
        with patch('app.services.prediction.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            with pytest.raises(ValueError, match="Unknown category"):
                await service.predict(
                    age=30,
                    sex="invalid_sex",
                    bmi=25.0,
                    children=2,
                    smoker=False,
                    region="northeast"
                )
    
    def test_get_model_info_not_loaded(self, service):
        """Test getting model info when model is not loaded."""
        result = service.get_model_info()
        assert result["status"] == "not_loaded"
    
    def test_get_model_info_loaded(self, service, mock_model):
        """Test getting model info when model is loaded."""
        service.model = mock_model
        
        result = service.get_model_info()
        
        assert result["status"] == "loaded"
        assert result["version"] == "v1.0"
        assert result["feature_columns"] == service.feature_columns
        assert "model_type" in result
        assert result["n_features"] == len(service.feature_columns)