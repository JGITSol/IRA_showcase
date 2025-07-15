"""Test script for the Insurance Risk Analyzer API."""

import sys
import time
import subprocess
import requests
from typing import Dict, Any

# API configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "1111"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.process = None

    def start_server(self):
        """Start the FastAPI server in a subprocess."""
        print("🚀 Starting FastAPI server...")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Give the server time to start
        time.sleep(5)
        print("✅ Server started")

    def stop_server(self):
        """Stop the FastAPI server."""
        if self.process:
            print("🛑 Stopping server...")
            self.process.terminate()
            self.process.wait()
            print("✅ Server stopped")

    def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, token: str = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error making {method} request to {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

    def test_authentication(self):
        """Test the authentication endpoints."""
        print("\n🔐 Testing authentication...")
        
        # Test login with correct credentials
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            # Test login
            print("Testing login...")
            response = self.make_request("POST", "/auth/login/access-token", 
                                      data=login_data)
            self.token = response.get("access_token")
            if not self.token:
                raise ValueError("No access token in response")
            print(f"✅ Login successful. Token: {self.token[:20]}...")
            
            # Test token verification
            print("Testing token verification...")
            self.make_request("POST", "/auth/login/test-token", 
                            token=self.token)
            print("✅ Token verification successful")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False

    def test_predictions(self):
        """Test the prediction endpoints."""
        if not self.token:
            print("❌ Not authenticated. Run test_authentication first.")
            return False
            
        print("\n📊 Testing predictions...")
        
        try:
            # Create a new prediction
            print("Creating a new prediction...")
            prediction_data = {
                "age": 35,
                "sex": "male",
                "bmi": 28.5,
                "children": 2,
                "smoker": False,
                "region": "northeast"
            }
            
            response = self.make_request(
                "POST", 
                "/predictions/", 
                data=prediction_data,
                token=self.token
            )
            prediction_id = response.get("id")
            if not prediction_id:
                raise ValueError("No prediction ID in response")
                
            print(f"✅ Prediction created with ID: {prediction_id}")
            
            # Get all predictions
            print("Fetching all predictions...")
            predictions = self.make_request(
                "GET",
                "/predictions/",
                token=self.token
            )
            print(f"✅ Retrieved {len(predictions)} predictions")
            
            # Get the created prediction
            print(f"Fetching prediction with ID: {prediction_id}")
            prediction = self.make_request(
                "GET",
                f"/predictions/{prediction_id}",
                token=self.token
            )
            print(f"✅ Retrieved prediction: {prediction}")
            
            # Update the prediction
            print(f"Updating prediction {prediction_id}...")
            update_data = {"bmi": 30.0}
            updated_prediction = self.make_request(
                "PUT",
                f"/predictions/{prediction_id}",
                data=update_data,
                token=self.token
            )
            print(f"✅ Prediction updated: {updated_prediction}")
            
            # Delete the prediction
            print(f"Deleting prediction {prediction_id}...")
            self.make_request(
                "DELETE",
                f"/predictions/{prediction_id}",
                token=self.token
            )
            print("✅ Prediction deleted")
            
            return True
            
        except Exception as e:
            print(f"❌ Prediction test failed: {e}")
            return False

    def run_tests(self):
        """Run all tests."""
        try:
            self.start_server()
            
            if not self.test_authentication():
                return False
                
            if not self.test_predictions():
                return False
                
            print("\n🎉 All tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
        finally:
            self.stop_server()

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)
