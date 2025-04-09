import unittest
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from model import train_model

class TestModel(unittest.TestCase):
    """Test cases for the model module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a backup of any existing model file
        self.model_path = 'models/insurance_model.pkl'
        self.backup_path = 'models/insurance_model_backup.pkl'
        
        if os.path.exists(self.model_path):
            if os.path.exists(self.backup_path):
                os.remove(self.backup_path)
            os.rename(self.model_path, self.backup_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore the original model file if it existed
        if os.path.exists(self.backup_path):
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            os.rename(self.backup_path, self.model_path)
        elif os.path.exists(self.model_path):
            os.remove(self.model_path)
    
    def test_train_model(self):
        """Test model training function."""
        # Train the model
        model = train_model()
        
        # Check if model was created
        self.assertIsNotNone(model)
        
        # Check if model file was saved
        self.assertTrue(os.path.exists(self.model_path))
        
        # Check if the model has the expected structure
        self.assertTrue(hasattr(model, 'named_steps'))
        self.assertIn('preprocessor', model.named_steps)
        self.assertIn('regressor', model.named_steps)
        
        # Test model prediction with sample data
        sample_data = pd.DataFrame({
            'age': [30],
            'gender': ['male'],
            'bmi': [25.0],
            'children': [2],
            'smoker': ['no'],
            'region': ['northeast']
        })
        
        prediction = model.predict(sample_data)
        
        # Check if prediction is a reasonable value (positive number)
        self.assertGreater(prediction[0], 0)
    
    def test_model_consistency(self):
        """Test that the model produces consistent predictions."""
        # Train the model
        model = train_model()
        
        # Create two identical input samples
        sample1 = pd.DataFrame({
            'age': [30],
            'gender': ['male'],
            'bmi': [25.0],
            'children': [2],
            'smoker': ['no'],
            'region': ['northeast']
        })
        
        sample2 = pd.DataFrame({
            'age': [30],
            'gender': ['male'],
            'bmi': [25.0],
            'children': [2],
            'smoker': ['no'],
            'region': ['northeast']
        })
        
        # Get predictions
        prediction1 = model.predict(sample1)[0]
        prediction2 = model.predict(sample2)[0]
        
        # Check if predictions are identical
        self.assertEqual(prediction1, prediction2)
    
    def test_model_sensitivity(self):
        """Test that the model is sensitive to important features."""
        # Train the model
        model = train_model()
        
        # Base case - non-smoker
        non_smoker = pd.DataFrame({
            'age': [30],
            'gender': ['male'],
            'bmi': [25.0],
            'children': [2],
            'smoker': ['no'],
            'region': ['northeast']
        })
        
        # Same person but smoker
        smoker = pd.DataFrame({
            'age': [30],
            'gender': ['male'],
            'bmi': [25.0],
            'children': [2],
            'smoker': ['yes'],
            'region': ['northeast']
        })
        
        # Get predictions
        non_smoker_pred = model.predict(non_smoker)[0]
        smoker_pred = model.predict(smoker)[0]
        
        # Smoker should have significantly higher predicted charges
        self.assertGreater(smoker_pred, non_smoker_pred * 1.5)  # At least 50% higher

if __name__ == '__main__':
    unittest.main()