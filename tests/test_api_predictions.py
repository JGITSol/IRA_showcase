"""Tests for prediction API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_create_prediction(self, client: TestClient, auth_headers, sample_prediction_data):
        """Test creating a new prediction."""
        response = client.post(
            f"{settings.API_V1_STR}/predictions/",
            json=sample_prediction_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == sample_prediction_data["age"]
        assert data["sex"] == sample_prediction_data["sex"]
        assert data["bmi"] == sample_prediction_data["bmi"]
        assert data["children"] == sample_prediction_data["children"]
        assert data["smoker"] == sample_prediction_data["smoker"]
        assert data["region"] == sample_prediction_data["region"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_prediction_unauthorized(self, client: TestClient, sample_prediction_data):
        """Test creating prediction without authentication."""
        response = client.post(
            f"{settings.API_V1_STR}/predictions/",
            json=sample_prediction_data
        )
        
        assert response.status_code == 401
    
    def test_create_prediction_invalid_data(self, client: TestClient, auth_headers):
        """Test creating prediction with invalid data."""
        invalid_data = {
            "age": 150,  # Invalid age
            "sex": "invalid",  # Invalid sex
            "bmi": -5,  # Invalid BMI
            "children": -1,  # Invalid children count
            "smoker": "maybe",  # Invalid smoker value
            "region": "invalid"  # Invalid region
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/predictions/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_predictions(self, client: TestClient, auth_headers, test_prediction):
        """Test getting user's predictions."""
        response = client.get(
            f"{settings.API_V1_STR}/predictions/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test prediction is in the results
        prediction_ids = [p["id"] for p in data]
        assert test_prediction.id in prediction_ids
    
    def test_get_predictions_pagination(self, client: TestClient, auth_headers):
        """Test predictions pagination."""
        response = client.get(
            f"{settings.API_V1_STR}/predictions/?skip=0&limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_prediction_by_id(self, client: TestClient, auth_headers, test_prediction):
        """Test getting a specific prediction by ID."""
        response = client.get(
            f"{settings.API_V1_STR}/predictions/{test_prediction.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction.id
        assert data["age"] == test_prediction.age
        assert data["sex"] == test_prediction.sex
    
    def test_get_prediction_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent prediction."""
        response = client.get(
            f"{settings.API_V1_STR}/predictions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Prediction not found" in response.json()["detail"]
    
    def test_get_prediction_unauthorized(self, client: TestClient, test_prediction):
        """Test getting prediction without authentication."""
        response = client.get(f"{settings.API_V1_STR}/predictions/{test_prediction.id}")
        
        assert response.status_code == 401
    
    def test_update_prediction(self, client: TestClient, auth_headers, test_prediction):
        """Test updating a prediction."""
        update_data = {
            "age": 35,
            "bmi": 27.5
        }
        
        response = client.put(
            f"{settings.API_V1_STR}/predictions/{test_prediction.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 35
        assert data["bmi"] == 27.5
        assert data["id"] == test_prediction.id
    
    def test_update_prediction_not_found(self, client: TestClient, auth_headers):
        """Test updating non-existent prediction."""
        update_data = {"age": 35}
        
        response = client.put(
            f"{settings.API_V1_STR}/predictions/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Prediction not found" in response.json()["detail"]
    
    def test_update_prediction_invalid_data(self, client: TestClient, auth_headers, test_prediction):
        """Test updating prediction with invalid data."""
        invalid_data = {
            "age": -5,  # Invalid age
            "bmi": 200  # Invalid BMI
        }
        
        response = client.put(
            f"{settings.API_V1_STR}/predictions/{test_prediction.id}",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_delete_prediction(self, client: TestClient, auth_headers, test_prediction):
        """Test deleting a prediction."""
        response = client.delete(
            f"{settings.API_V1_STR}/predictions/{test_prediction.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction.id
        
        # Verify prediction is deleted
        get_response = client.get(
            f"{settings.API_V1_STR}/predictions/{test_prediction.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_prediction_not_found(self, client: TestClient, auth_headers):
        """Test deleting non-existent prediction."""
        response = client.delete(
            f"{settings.API_V1_STR}/predictions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Prediction not found" in response.json()["detail"]
    
    def test_delete_prediction_unauthorized(self, client: TestClient, test_prediction):
        """Test deleting prediction without authentication."""
        response = client.delete(f"{settings.API_V1_STR}/predictions/{test_prediction.id}")
        
        assert response.status_code == 401