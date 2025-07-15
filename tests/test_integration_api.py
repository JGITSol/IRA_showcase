"""Integration tests for the complete API."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


class TestAPIIntegration:
    """Integration tests for the complete API workflow."""
    
    def test_complete_user_workflow(self, client: TestClient):
        """Test complete user workflow from registration to prediction."""
        # Note: Since we don't have user registration endpoint in the current API,
        # we'll use the existing test user from fixtures
        
        # 1. Login
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data=login_data
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test token
        token_test_response = client.post(
            f"{settings.API_V1_STR}/auth/login/test-token",
            headers=headers
        )
        assert token_test_response.status_code == 200
        user_data = token_test_response.json()
        assert user_data["email"] == "test@example.com"
        
        # 3. Create prediction
        prediction_data = {
            "age": 35,
            "sex": "female",
            "bmi": 28.5,
            "children": 1,
            "smoker": True,
            "region": "southwest"
        }
        create_response = client.post(
            f"{settings.API_V1_STR}/predictions/",
            json=prediction_data,
            headers=headers
        )
        assert create_response.status_code == 200
        prediction = create_response.json()
        prediction_id = prediction["id"]
        
        # 4. Get all predictions
        list_response = client.get(
            f"{settings.API_V1_STR}/predictions/",
            headers=headers
        )
        assert list_response.status_code == 200
        predictions = list_response.json()
        assert len(predictions) >= 1
        assert any(p["id"] == prediction_id for p in predictions)
        
        # 5. Get specific prediction
        get_response = client.get(
            f"{settings.API_V1_STR}/predictions/{prediction_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        retrieved_prediction = get_response.json()
        assert retrieved_prediction["id"] == prediction_id
        assert retrieved_prediction["age"] == 35
        
        # 6. Update prediction
        update_data = {
            "age": 36,
            "bmi": 29.0
        }
        update_response = client.put(
            f"{settings.API_V1_STR}/predictions/{prediction_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        updated_prediction = update_response.json()
        assert updated_prediction["age"] == 36
        assert updated_prediction["bmi"] == 29.0
        
        # 7. Delete prediction
        delete_response = client.delete(
            f"{settings.API_V1_STR}/predictions/{prediction_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # 8. Verify deletion
        get_deleted_response = client.get(
            f"{settings.API_V1_STR}/predictions/{prediction_id}",
            headers=headers
        )
        assert get_deleted_response.status_code == 404
    
    def test_admin_workflow(self, client: TestClient, test_superuser):
        """Test admin workflow with user management."""
        # 1. Admin login
        login_data = {
            "username": test_superuser.email,
            "password": "adminpassword123"
        }
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data=login_data
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get all users (admin only)
        users_response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=admin_headers
        )
        assert users_response.status_code == 200
        users = users_response.json()
        assert len(users) >= 1
        
        # 3. Create new user (admin only)
        new_user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "is_superuser": False
        }
        create_user_response = client.post(
            f"{settings.API_V1_STR}/users/",
            json=new_user_data,
            headers=admin_headers
        )
        assert create_user_response.status_code == 200
        new_user = create_user_response.json()
        new_user_id = new_user["id"]
        
        # 4. Get specific user
        get_user_response = client.get(
            f"{settings.API_V1_STR}/users/{new_user_id}",
            headers=admin_headers
        )
        assert get_user_response.status_code == 200
        retrieved_user = get_user_response.json()
        assert retrieved_user["email"] == "newuser@example.com"
        
        # 5. Update user
        update_user_data = {
            "full_name": "Updated User Name"
        }
        update_user_response = client.put(
            f"{settings.API_V1_STR}/users/{new_user_id}",
            json=update_user_data,
            headers=admin_headers
        )
        assert update_user_response.status_code == 200
        updated_user = update_user_response.json()
        assert updated_user["full_name"] == "Updated User Name"
        
        # 6. Delete user
        delete_user_response = client.delete(
            f"{settings.API_V1_STR}/users/{new_user_id}",
            headers=admin_headers
        )
        assert delete_user_response.status_code == 200
    
    def test_unauthorized_access_attempts(self, client: TestClient):
        """Test various unauthorized access attempts."""
        # 1. Access protected endpoints without token
        endpoints = [
            f"{settings.API_V1_STR}/predictions/",
            f"{settings.API_V1_STR}/users/",
            f"{settings.API_V1_STR}/users/me"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
        
        # 2. Access with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        for endpoint in endpoints:
            response = client.get(endpoint, headers=invalid_headers)
            assert response.status_code == 403
    
    def test_regular_user_admin_access_denied(self, client: TestClient, auth_headers):
        """Test that regular users cannot access admin endpoints."""
        # Try to access admin-only endpoints
        admin_endpoints = [
            (client.get, f"{settings.API_V1_STR}/users/"),
            (client.post, f"{settings.API_V1_STR}/users/"),
            (client.get, f"{settings.API_V1_STR}/users/1"),
            (client.put, f"{settings.API_V1_STR}/users/1"),
            (client.delete, f"{settings.API_V1_STR}/users/1")
        ]
        
        for method, endpoint in admin_endpoints:
            if method == client.post or method == client.put:
                response = method(endpoint, json={}, headers=auth_headers)
            else:
                response = method(endpoint, headers=auth_headers)
            
            assert response.status_code == 400  # "doesn't have enough privileges"
    
    def test_data_validation_errors(self, client: TestClient, auth_headers):
        """Test various data validation scenarios."""
        # 1. Invalid prediction data
        invalid_predictions = [
            {
                "age": -5,  # Invalid age
                "sex": "male",
                "bmi": 25.0,
                "children": 2,
                "smoker": False,
                "region": "northeast"
            },
            {
                "age": 30,
                "sex": "invalid_sex",  # Invalid sex
                "bmi": 25.0,
                "children": 2,
                "smoker": False,
                "region": "northeast"
            },
            {
                "age": 30,
                "sex": "male",
                "bmi": -10.0,  # Invalid BMI
                "children": 2,
                "smoker": False,
                "region": "northeast"
            },
            {
                "age": 30,
                "sex": "male",
                "bmi": 25.0,
                "children": -1,  # Invalid children count
                "smoker": False,
                "region": "northeast"
            },
            {
                "age": 30,
                "sex": "male",
                "bmi": 25.0,
                "children": 2,
                "smoker": "maybe",  # Invalid smoker value
                "region": "northeast"
            },
            {
                "age": 30,
                "sex": "male",
                "bmi": 25.0,
                "children": 2,
                "smoker": False,
                "region": "invalid_region"  # Invalid region
            }
        ]
        
        for invalid_data in invalid_predictions:
            response = client.post(
                f"{settings.API_V1_STR}/predictions/",
                json=invalid_data,
                headers=auth_headers
            )
            assert response.status_code == 422
    
    def test_pagination(self, client: TestClient, auth_headers):
        """Test pagination functionality."""
        # Create multiple predictions
        prediction_data = {
            "age": 30,
            "sex": "male",
            "bmi": 25.0,
            "children": 2,
            "smoker": False,
            "region": "northeast"
        }
        
        created_ids = []
        for i in range(5):
            response = client.post(
                f"{settings.API_V1_STR}/predictions/",
                json={**prediction_data, "age": 30 + i},
                headers=auth_headers
            )
            assert response.status_code == 200
            created_ids.append(response.json()["id"])
        
        # Test pagination
        response = client.get(
            f"{settings.API_V1_STR}/predictions/?skip=0&limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        predictions = response.json()
        assert len(predictions) <= 3
        
        # Test second page
        response = client.get(
            f"{settings.API_V1_STR}/predictions/?skip=3&limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        predictions_page2 = response.json()
        
        # Cleanup
        for pred_id in created_ids:
            client.delete(
                f"{settings.API_V1_STR}/predictions/{pred_id}",
                headers=auth_headers
            )