"""Integration tests for the Insurance Risk Analyzer API."""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

def setup_test_environment():
    """Set up the test environment."""
    print("Setting up test environment...")
    
    # Set environment variables for testing
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test_ira_showcase.db"
    os.environ["FIRST_SUPERUSER"] = "test@example.com"
    os.environ["FIRST_SUPERUSER_PASSWORD"] = "1111"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    
    # Create test database
    from app.db.base import Base
    from app.db.session import engine
    
    print("Creating test database...")
    Base.metadata.create_all(bind=engine)
    
    # Create test user
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        # Create test user if it doesn't exist
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            user = User(
                email="test@example.com",
                hashed_password=get_password_hash("1111"),
                full_name="Test User",
                is_superuser=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            print("✅ Test user created")
        else:
            print("ℹ️  Test user already exists")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("✅ Test environment setup complete")

def start_test_server():
    """Start the test server in a subprocess."""
    print("\n🚀 Starting test server...")
    
    # Start the server in a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ
    )
    
    # Give the server time to start
    time.sleep(5)
    
    # Check if the server started successfully
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print(f"❌ Server failed to start. Error: {stderr.decode()}")
        return None
    
    print("✅ Test server started")
    return server_process

def stop_test_server(server_process):
    """Stop the test server."""
    if server_process:
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Test server stopped")

def run_api_tests():
    """Run the API tests."""
    print("\n🔍 Running API tests...")
    
    try:
        # Import the test script
        from test_api import APITester
        
        # Configure the tester
        tester = APITester()
        tester.base_url = "http://localhost:8000/api/v1"
        
        # Run the tests
        success = tester.test_authentication()
        if success:
            success = tester.test_predictions()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed")
        
        return success
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the integration tests."""
    server_process = None
    
    try:
        # Set up the test environment
        setup_test_environment()
        
        # Start the test server
        server_process = start_test_server()
        if not server_process:
            return 1
        
        # Run the API tests
        success = run_api_tests()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Stop the test server
        stop_test_server(server_process)
        
        # Clean up test database
        try:
            test_db = Path("test_ira_showcase.db")
            if test_db.exists():
                test_db.unlink()
                print("✅ Cleaned up test database")
        except Exception as e:
            print(f"❌ Error cleaning up test database: {e}")

if __name__ == "__main__":
    sys.exit(main())
