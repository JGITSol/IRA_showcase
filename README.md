# Insurance Risk Prediction Application

## Overview

This application predicts insurance charges and assesses risk factors based on demographic and health information. It uses machine learning to provide accurate predictions and visualizations to help understand risk factors.

## Features

- Predict insurance charges based on personal information
- Calculate risk scores to assess insurance risk
- Store and retrieve prediction history
- Visualize risk factors and prediction comparisons
- Explore model insights and feature importance

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/insurance-risk-predictor.git
   cd insurance-risk-predictor
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Train the model (if not already trained):
   ```
   python model.py
   ```

## Usage

### Running the Application

Start the Streamlit application:

```
streamlit run app.py
```

This will launch the application in your default web browser at `http://localhost:8501`.

### Making Predictions

1. Navigate to the "Predict" tab
2. Enter your information:
   - Age
   - Gender
   - BMI (Body Mass Index)
   - Number of children
   - Smoker status
   - Region
3. Click "Calculate Risk" to see your prediction

### Viewing History

Navigate to the "History" tab to view all previous predictions. You can:
- View details of any prediction
- Load a previous prediction for editing
- Delete predictions from the database

### Exploring Insights

Navigate to the "Insights" tab to:
- View feature importance charts
- Compare example predictions for different profiles

## Running Tests

The application includes comprehensive tests to ensure functionality:

```
python run_tests.py
```

Or run individual test modules:

```
python -m unittest tests.test_database
python -m unittest tests.test_model
python -m unittest tests.test_utils
```

## API Documentation

### Database Module

```python
from database import Database

# Initialize database
db = Database(db_name='insurance_predictions.db')

# Add a prediction
prediction_id = db.add_prediction(age, gender, bmi, children, smoker, region, predicted_charges)

# Get all predictions
predictions = db.get_all_predictions()

# Get prediction by ID
prediction = db.get_prediction_by_id(prediction_id)

# Update prediction
success = db.update_prediction(prediction_id, age, gender, bmi, children, smoker, region, predicted_charges)

# Delete prediction
success = db.delete_prediction(prediction_id)

# Close database connection
db.close()
```

### Model Module

```python
from model import train_model

# Train and save the model
model = train_model()
```

### Utils Module

```python
from utils import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

# Load the trained model
model = load_model()

# Make a prediction
prediction = predict_insurance_charges(model, age, gender, bmi, children, smoker, region)

# Generate risk score (1-10)
risk_score = generate_risk_score(prediction, max_charge=50000)

# Create visualizations
risk_gauge_fig = plot_risk_gauge(risk_score)
feature_importance_fig = plot_feature_importance(model)
comparison_fig = plot_prediction_comparison(prediction, avg_charges)
```

## Project Structure

```
insurance-risk-predictor/
├── app.py                  # Main Streamlit application
├── database.py             # Database operations
├── model.py                # Model training and creation
├── utils.py                # Utility functions and visualizations
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
├── run_tests.py            # Test runner script
├── data/                   # Data directory
│   ├── insurance_data.csv  # Sample data
│   └── insurance_predictions.db  # SQLite database
├── models/                 # Model directory
│   └── insurance_model.pkl  # Trained model
└── tests/                  # Test directory
    ├── __init__.py         # Makes tests a package
    ├── test_database.py    # Database tests
    ├── test_model.py       # Model tests
    └── test_utils.py       # Utility tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project uses Streamlit for the web interface
- Machine learning models are built with scikit-learn
- Visualizations use Matplotlib and Seaborn