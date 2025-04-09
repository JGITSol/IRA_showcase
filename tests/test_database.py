import unittest
import os
import sys
import sqlite3
import datetime
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Database

class TestDatabase(unittest.TestCase):
    """Test cases for the Database class."""
    
    def setUp(self):
        """Set up a test database before each test."""
        self.test_db_name = 'test_insurance_predictions.db'
        # Ensure we're using a test database
        self.db = Database(db_name=self.test_db_name)
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.close()
        # Remove the test database file
        if os.path.exists(f'data/{self.test_db_name}'):
            os.remove(f'data/{self.test_db_name}')
    
    def test_init(self):
        """Test database initialization."""
        # Check if the database file was created
        self.assertTrue(os.path.exists(f'data/{self.test_db_name}'))
        
        # Check if the predictions table exists
        conn = sqlite3.connect(f'data/{self.test_db_name}')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        self.assertTrue(table_exists)
    
    def test_add_prediction(self):
        """Test adding a prediction to the database."""
        # Add a test prediction
        prediction_id = self.db.add_prediction(
            age=30, 
            gender='male', 
            bmi=25.0, 
            children=2, 
            smoker='no', 
            region='northeast', 
            predicted_charges=10000.0
        )
        
        # Check if the prediction was added successfully
        self.assertIsNotNone(prediction_id)
        self.assertGreater(prediction_id, 0)
        
        # Verify the prediction exists in the database
        prediction = self.db.get_prediction_by_id(prediction_id)
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction['age'], 30)
        self.assertEqual(prediction['gender'], 'male')
        self.assertEqual(prediction['bmi'], 25.0)
        self.assertEqual(prediction['children'], 2)
        self.assertEqual(prediction['smoker'], 'no')
        self.assertEqual(prediction['region'], 'northeast')
        self.assertEqual(prediction['predicted_charges'], 10000.0)
    
    def test_get_all_predictions(self):
        """Test retrieving all predictions from the database."""
        # Add multiple test predictions
        self.db.add_prediction(30, 'male', 25.0, 2, 'no', 'northeast', 10000.0)
        self.db.add_prediction(40, 'female', 30.0, 1, 'yes', 'southwest', 20000.0)
        self.db.add_prediction(50, 'male', 28.0, 0, 'no', 'southeast', 15000.0)
        
        # Retrieve all predictions
        predictions = self.db.get_all_predictions()
        
        # Check if all predictions were retrieved
        self.assertEqual(len(predictions), 3)
    
    def test_get_prediction_by_id(self):
        """Test retrieving a specific prediction by ID."""
        # Add a test prediction
        prediction_id = self.db.add_prediction(
            age=30, 
            gender='male', 
            bmi=25.0, 
            children=2, 
            smoker='no', 
            region='northeast', 
            predicted_charges=10000.0
        )
        
        # Retrieve the prediction by ID
        prediction = self.db.get_prediction_by_id(prediction_id)
        
        # Check if the correct prediction was retrieved
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction['id'], prediction_id)
        self.assertEqual(prediction['age'], 30)
        
        # Test retrieving a non-existent prediction
        non_existent_prediction = self.db.get_prediction_by_id(9999)
        self.assertIsNone(non_existent_prediction)
    
    def test_update_prediction(self):
        """Test updating an existing prediction."""
        # Add a test prediction
        prediction_id = self.db.add_prediction(
            age=30, 
            gender='male', 
            bmi=25.0, 
            children=2, 
            smoker='no', 
            region='northeast', 
            predicted_charges=10000.0
        )
        
        # Update the prediction
        success = self.db.update_prediction(
            prediction_id=prediction_id,
            age=35, 
            gender='male', 
            bmi=26.0, 
            children=3, 
            smoker='yes', 
            region='northwest', 
            predicted_charges=15000.0
        )
        
        # Check if the update was successful
        self.assertTrue(success)
        
        # Verify the prediction was updated
        updated_prediction = self.db.get_prediction_by_id(prediction_id)
        self.assertEqual(updated_prediction['age'], 35)
        self.assertEqual(updated_prediction['bmi'], 26.0)
        self.assertEqual(updated_prediction['children'], 3)
        self.assertEqual(updated_prediction['smoker'], 'yes')
        self.assertEqual(updated_prediction['region'], 'northwest')
        self.assertEqual(updated_prediction['predicted_charges'], 15000.0)
    
    def test_delete_prediction(self):
        """Test deleting a prediction from the database."""
        # Add a test prediction
        prediction_id = self.db.add_prediction(
            age=30, 
            gender='male', 
            bmi=25.0, 
            children=2, 
            smoker='no', 
            region='northeast', 
            predicted_charges=10000.0
        )
        
        # Delete the prediction
        success = self.db.delete_prediction(prediction_id)
        
        # Check if the deletion was successful
        self.assertTrue(success)
        
        # Verify the prediction no longer exists
        deleted_prediction = self.db.get_prediction_by_id(prediction_id)
        self.assertIsNone(deleted_prediction)

if __name__ == '__main__':
    unittest.main()