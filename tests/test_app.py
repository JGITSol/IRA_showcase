import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the app module
import app
from database import Database

class TestApp(unittest.TestCase):
    """Test cases for the Streamlit app."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Streamlit
        self.streamlit_mock = patch('app.st').start()
        
        # Mock session state
        self.session_state_mock = MagicMock()
        self.streamlit_mock.session_state = self.session_state_mock
        
        # Mock Database
        self.db_mock = patch('app.Database').start()
        self.db_instance_mock = MagicMock()
        self.db_mock.return_value = self.db_instance_mock
        
        # Mock utils functions
        self.load_model_mock = patch('app.load_model').start()
        self.predict_insurance_charges_mock = patch('app.predict_insurance_charges').start()
        self.generate_risk_score_mock = patch('app.generate_risk_score').start()
        self.plot_risk_gauge_mock = patch('app.plot_risk_gauge').start()
        self.plot_feature_importance_mock = patch('app.plot_feature_importance').start()
        self.plot_prediction_comparison_mock = patch('app.plot_prediction_comparison').start()
    
    def tearDown(self):
        """Clean up after tests."""
        patch.stopall()
    
    def test_make_prediction(self):
        """Test the make_prediction function."""
        # Set up mocks
        model_mock = MagicMock()
        self.load_model_mock.return_value = model_mock
        self.predict_insurance_charges_mock.return_value = 15000.0
        self.generate_risk_score_mock.return_value = 3
        
        # Set up session state
        self.session_state_mock.age = 30
        self.session_state_mock.gender = 'male'
        self.session_state_mock.bmi = 25.0
        self.session_state_mock.children = 2
        self.session_state_mock.smoker = 'no'
        self.session_state_mock.region = 'northeast'
        self.session_state_mock.prediction = None
        self.session_state_mock.prediction_made = False
        
        # Configure the database mock
        self.db_instance_mock.add_prediction.return_value = 1
        
        # Call the function
        # We patch 'app.db' directly to ensure our mock is used.
        with patch('app.db', self.db_instance_mock):
            result = app.make_prediction()
        
        # Verify the function returned True on success
        self.assertTrue(result)
        
        # Verify the model was loaded
        self.load_model_mock.assert_called_once()
        
        # Verify prediction was made with correct parameters
        self.predict_insurance_charges_mock.assert_called_once_with(
            model_mock, 30, 'male', 25.0, 2, 'no', 'northeast'
        )
        
        # Verify risk score was generated
        self.generate_risk_score_mock.assert_called_once_with(15000.0)
        
        # Verify session state was updated
        self.assertEqual(self.session_state_mock.prediction, 15000.0)
        self.assertEqual(self.session_state_mock.risk_score, 3)
        self.assertEqual(self.session_state_mock.prediction_made, True)
        
        # Verify prediction was saved to database
        self.db_instance_mock.add_prediction.assert_called_once_with(
            30, 'male', 25.0, 2, 'no', 'northeast', 15000.0
        )
        
        # Verify success message was shown
        self.streamlit_mock.success.assert_called_once_with("Prediction saved with ID: 1")
    
    def test_make_prediction_model_none(self):
        """Test make_prediction when model is None."""
        # Set up mocks
        self.load_model_mock.return_value = None
        
        # Call the function
        app.make_prediction()
        
        # Verify error message was shown
        self.streamlit_mock.error.assert_called_once_with(
            "Failed to load model. Please ensure the model has been trained."
        )
    
    def test_make_prediction_prediction_none(self):
        """Test make_prediction when prediction is None."""
        # Set up mocks
        model_mock = MagicMock()
        self.load_model_mock.return_value = model_mock
        self.predict_insurance_charges_mock.return_value = None
        
        # Call the function
        app.make_prediction()
        
        # Verify error message was shown
        self.streamlit_mock.error.assert_called_once_with(
            "Failed to make prediction."
        )
    
    def test_view_predictions_empty(self):
        """Test view_predictions when no predictions exist."""
        # Mock empty predictions
        self.db_instance_mock.get_all_predictions.return_value = []
        
        # Mock the pandas DataFrame to handle empty list
        with patch('app.pd.DataFrame') as df_mock:
            # Setup the mock DataFrame
            mock_df = MagicMock()
            df_mock.return_value = mock_df
            mock_df.__getitem__.return_value.tolist.return_value = []
            
            # This will prevent selectbox from being called with empty list
            self.streamlit_mock.selectbox.return_value = None
        
            # Call the function
            with patch('app.db', self.db_instance_mock):
                app.view_predictions()
            
            # Verify info message was shown
            self.streamlit_mock.info.assert_called_once_with(
                "No predictions found in the database."
            )
        
        # Verify selectbox was not called
        self.streamlit_mock.selectbox.assert_not_called()
    
    def test_view_predictions_with_data(self):
        """Test view_predictions with existing predictions."""
        # Set up mock predictions
        mock_predictions = [
            {'id': 1, 'age': 30, 'gender': 'male', 'bmi': 25.0, 'children': 2, 
             'smoker': 'no', 'region': 'northeast', 'predicted_charges': 10000.0,
             'prediction_date': '2023-01-01 12:00:00'}
        ]
        self.db_instance_mock.get_all_predictions.return_value = mock_predictions
        
        # Mock selectbox to return a valid prediction ID
        self.streamlit_mock.selectbox.return_value = 1
        
        # Mock get_prediction_by_id to return the prediction data
        self.db_instance_mock.get_prediction_by_id.return_value = mock_predictions[0]
        
        # Mock columns
        col_mocks = [MagicMock(), MagicMock()]
        self.streamlit_mock.columns.return_value = col_mocks
        
        # Call the function
        app.view_predictions()
        
        # Verify dataframe was displayed
        self.streamlit_mock.dataframe.assert_called_once()
        
        # Verify selectbox was created
        self.streamlit_mock.selectbox.assert_called_once()

if __name__ == '__main__':
    unittest.main()