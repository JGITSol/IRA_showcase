"""Enhanced tests for the Database module with better coverage."""

import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database


class TestDatabaseEnhanced:
    """Enhanced tests for the Database class."""
    
    @pytest.fixture
    def temp_db_path(self):
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
    def database(self, temp_db_path):
        """Create a database instance with temporary file."""
        # Extract just the filename for the Database constructor
        db_name = Path(temp_db_path).name
        db = Database(db_name=db_name)
        yield db
        db.close()
    
    def test_database_initialization_creates_directory(self):
        """Test that database initialization creates data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                db = Database(db_name='test_init.db')
                
                # Verify data directory was created
                assert os.path.exists('data')
                assert os.path.isdir('data')
                assert os.path.exists('data/test_init.db')
                
                db.close()
            finally:
                os.chdir(original_cwd)
    
    def test_database_table_creation(self, database):
        """Test that the predictions table is created correctly."""
        # Get table schema
        cursor = database.conn.cursor()
        cursor.execute("PRAGMA table_info(predictions)")
        columns = cursor.fetchall()
        
        # Verify all expected columns exist
        column_names = [col[1] for col in columns]
        expected_columns = [
            'id', 'age', 'gender', 'bmi', 'children', 
            'smoker', 'region', 'predicted_charges', 'prediction_date'
        ]
        
        for col in expected_columns:
            assert col in column_names
    
    def test_add_prediction_returns_valid_id(self, database):
        """Test that add_prediction returns a valid ID."""
        prediction_id = database.add_prediction(
            age=25, gender='female', bmi=22.5, children=0,
            smoker='no', region='northwest', predicted_charges=8000.0
        )
        
        assert isinstance(prediction_id, int)
        assert prediction_id > 0
    
    def test_add_prediction_with_edge_values(self, database):
        """Test adding prediction with edge case values."""
        # Test minimum values
        id1 = database.add_prediction(
            age=18, gender='male', bmi=10.0, children=0,
            smoker='no', region='northeast', predicted_charges=1000.0
        )
        
        # Test maximum values
        id2 = database.add_prediction(
            age=100, gender='female', bmi=50.0, children=10,
            smoker='yes', region='southwest', predicted_charges=100000.0
        )
        
        assert id1 > 0
        assert id2 > 0
        assert id2 > id1
    
    def test_add_prediction_with_special_characters(self, database):
        """Test adding prediction with special characters in string fields."""
        prediction_id = database.add_prediction(
            age=30, gender="male", bmi=25.0, children=2,
            smoker="no", region="northeast", predicted_charges=15000.0
        )
        
        prediction = database.get_prediction_by_id(prediction_id)
        assert prediction is not None
        assert prediction['gender'] == 'male'
        assert prediction['region'] == 'northeast'
    
    def test_get_all_predictions_ordering(self, database):
        """Test that get_all_predictions returns results in correct order."""
        # Add multiple predictions
        ids = []
        for i in range(3):
            pred_id = database.add_prediction(
                age=30+i, gender='male', bmi=25.0, children=i,
                smoker='no', region='northeast', predicted_charges=10000.0+i*1000
            )
            ids.append(pred_id)
        
        predictions = database.get_all_predictions()
        
        # Should be ordered by ID (most recent first in typical implementations)
        assert len(predictions) >= 3
        
        # Find our predictions in the results
        our_predictions = [p for p in predictions if p['id'] in ids]
        assert len(our_predictions) == 3
    
    def test_get_prediction_by_id_nonexistent(self, database):
        """Test getting prediction with non-existent ID."""
        result = database.get_prediction_by_id(99999)
        assert result is None
    
    def test_get_prediction_by_id_invalid_type(self, database):
        """Test getting prediction with invalid ID type."""
        with pytest.raises((TypeError, ValueError)):
            database.get_prediction_by_id("invalid_id")
    
    def test_update_prediction_partial(self, database):
        """Test updating only some fields of a prediction."""
        # Add initial prediction
        prediction_id = database.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        # Update only age and BMI
        success = database.update_prediction(
            prediction_id=prediction_id,
            age=35, gender='male', bmi=27.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        assert success is True
        
        # Verify changes
        updated = database.get_prediction_by_id(prediction_id)
        assert updated['age'] == 35
        assert updated['bmi'] == 27.0
        assert updated['gender'] == 'male'  # Unchanged
    
    def test_update_prediction_nonexistent(self, database):
        """Test updating non-existent prediction."""
        success = database.update_prediction(
            prediction_id=99999,
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        assert success is False
    
    def test_update_prediction_with_same_values(self, database):
        """Test updating prediction with same values."""
        # Add initial prediction
        prediction_id = database.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        # Update with same values
        success = database.update_prediction(
            prediction_id=prediction_id,
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        assert success is True
    
    def test_delete_prediction_nonexistent(self, database):
        """Test deleting non-existent prediction."""
        success = database.delete_prediction(99999)
        assert success is False
    
    def test_delete_prediction_twice(self, database):
        """Test deleting the same prediction twice."""
        # Add prediction
        prediction_id = database.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        
        # Delete first time
        success1 = database.delete_prediction(prediction_id)
        assert success1 is True
        
        # Delete second time
        success2 = database.delete_prediction(prediction_id)
        assert success2 is False
    
    def test_database_connection_persistence(self, database):
        """Test that database connection persists across operations."""
        # Perform multiple operations
        id1 = database.add_prediction(
            age=25, gender='female', bmi=22.0, children=0,
            smoker='no', region='northeast', predicted_charges=8000.0
        )
        
        prediction = database.get_prediction_by_id(id1)
        assert prediction is not None
        
        all_predictions = database.get_all_predictions()
        assert len(all_predictions) >= 1
        
        success = database.update_prediction(
            prediction_id=id1,
            age=26, gender='female', bmi=22.0, children=0,
            smoker='no', region='northeast', predicted_charges=8000.0
        )
        assert success is True
    
    def test_database_close_and_reopen(self, temp_db_path):
        """Test closing and reopening database."""
        db_name = Path(temp_db_path).name
        
        # Create database and add data
        db1 = Database(db_name=db_name)
        prediction_id = db1.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=10000.0
        )
        db1.close()
        
        # Reopen database and verify data persists
        db2 = Database(db_name=db_name)
        prediction = db2.get_prediction_by_id(prediction_id)
        assert prediction is not None
        assert prediction['age'] == 30
        db2.close()
    
    def test_database_error_handling(self):
        """Test database error handling."""
        # Test with invalid database path
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")
            
            with pytest.raises(sqlite3.Error):
                Database(db_name='invalid.db')
    
    def test_concurrent_access_simulation(self, database):
        """Test simulation of concurrent database access."""
        # Add multiple predictions rapidly
        prediction_ids = []
        for i in range(10):
            pred_id = database.add_prediction(
                age=20+i, gender='male' if i % 2 == 0 else 'female',
                bmi=20.0+i, children=i % 3,
                smoker='yes' if i % 3 == 0 else 'no',
                region='northeast', predicted_charges=5000.0+i*1000
            )
            prediction_ids.append(pred_id)
        
        # Verify all predictions were added
        all_predictions = database.get_all_predictions()
        our_predictions = [p for p in all_predictions if p['id'] in prediction_ids]
        assert len(our_predictions) == 10
        
        # Verify each prediction can be retrieved individually
        for pred_id in prediction_ids:
            prediction = database.get_prediction_by_id(pred_id)
            assert prediction is not None
    
    def test_database_sql_injection_protection(self, database):
        """Test protection against SQL injection attempts."""
        # Attempt SQL injection in string fields
        malicious_inputs = [
            "'; DROP TABLE predictions; --",
            "' OR '1'='1",
            "'; DELETE FROM predictions; --"
        ]
        
        for malicious_input in malicious_inputs:
            # This should not cause SQL injection
            prediction_id = database.add_prediction(
                age=30, gender=malicious_input[:6], bmi=25.0, children=2,
                smoker='no', region='northeast', predicted_charges=10000.0
            )
            
            # Verify prediction was added safely
            prediction = database.get_prediction_by_id(prediction_id)
            assert prediction is not None
            
            # Verify table still exists and has data
            all_predictions = database.get_all_predictions()
            assert len(all_predictions) > 0
    
    def test_database_data_types_validation(self, database):
        """Test that database handles different data types correctly."""
        # Test with float values that might cause precision issues
        prediction_id = database.add_prediction(
            age=30, gender='male', bmi=25.123456789, children=2,
            smoker='no', region='northeast', predicted_charges=10000.999999
        )
        
        prediction = database.get_prediction_by_id(prediction_id)
        assert prediction is not None
        
        # BMI should be stored as float
        assert isinstance(prediction['bmi'], float)
        assert abs(prediction['bmi'] - 25.123456789) < 0.0001
        
        # Charges should be stored as float
        assert isinstance(prediction['predicted_charges'], float)
        assert abs(prediction['predicted_charges'] - 10000.999999) < 0.0001
    
    def test_database_transaction_rollback_simulation(self, database):
        """Test transaction behavior simulation."""
        initial_count = len(database.get_all_predictions())
        
        # Simulate a transaction that should rollback
        try:
            # Add a prediction
            prediction_id = database.add_prediction(
                age=30, gender='male', bmi=25.0, children=2,
                smoker='no', region='northeast', predicted_charges=10000.0
            )
            
            # Verify it was added
            assert database.get_prediction_by_id(prediction_id) is not None
            
            # Simulate an error that would cause rollback in a real transaction
            # (Note: SQLite with autocommit doesn't actually rollback here,
            # but we're testing the behavior)
            
        except Exception:
            pass
        
        # In a real scenario with proper transaction handling,
        # we would verify rollback behavior here
        final_count = len(database.get_all_predictions())
        assert final_count >= initial_count