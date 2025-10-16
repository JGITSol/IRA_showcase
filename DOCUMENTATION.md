# Insurance Risk Prediction Application Documentation

## Overview

The Insurance Risk Prediction Application is a Streamlit-based web application that predicts insurance charges based on demographic and health information. It uses machine learning to provide accurate predictions and visualizations to help understand risk factors.

## Project Components

### Core Modules

1. **Database Module (`database.py`)**
   - Handles all database operations using SQLite
   - Stores prediction history and allows retrieval, updating, and deletion

2. **Model Module (`model.py`)**
   - Creates and trains the machine learning model
   - Generates synthetic insurance data for demonstration
   - Saves the trained model for later use

3. **Utilities Module**
   - **Original (`utils.py`)**: Contains functions for model loading, prediction, and Matplotlib visualizations
   - **Modernized (`utils_plotly.py`)**: Enhanced version with interactive Plotly visualizations

4. **Streamlit Application**
   - **Original (`app.py`)**: Main application using Matplotlib visualizations
   - **Modernized (`app_plotly.py`)**: Enhanced application with Plotly visualizations and modern UI

### Testing Framework

1. **Test Modules**
   - `tests/test_database.py`: Tests for database operations
   - `tests/test_model.py`: Tests for model training and prediction
   - `tests/test_utils.py`: Tests for utility functions
   - `tests/test_app.py`: Integration tests for the Streamlit application

2. **Test Runner**
   - `run_tests.py`: Script to run all tests at once

3. **UI Regression (Puppeteer)**
   - Located in `tests/puppeteer`
   - Uses Node.js and Puppeteer to open project URLs, assert availability, and capture screenshots
   - Run with `cd tests/puppeteer && npm install && npm test`
   - Supports overrides such as `npm test -- --dry-run` (plan only) and `npm test -- --headful` (visible browser)

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. Clone the repository or download the source code

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Train the model (if not already trained):
   ```bash
   python model.py
   ```

## Running the Application

### Original Version (Matplotlib)

```bash
streamlit run app.py
```

### Modernized Version (Plotly)

```bash
streamlit run app_plotly.py
```

The application will be available at `http://localhost:8501` in your web browser.

## Running Tests

### Running All Tests

```bash
python run_tests.py
```

### Running Specific Test Modules

```bash
python -m unittest tests.test_database
python -m unittest tests.test_model
python -m unittest tests.test_utils
python -m unittest tests.test_app
```

## Application Features

### Prediction Tab

- **Input Form**: Enter demographic and health information
  - Age (18-100)
  - Gender (male/female)
  - BMI (10.0-50.0)
  - Number of Children (0-10)
  - Smoker Status (yes/no)
  - Region (northeast, northwest, southeast, southwest)

- **Prediction Results**:
  - Predicted Insurance Charges
  - Risk Score (1-10)
  - Risk Gauge Visualization
  - Comparison with Average Charges
  - Risk Factors Analysis

### History Tab

- View all saved predictions in a table
- Select a prediction to view details
- Load a previous prediction for editing
- Delete predictions from the database

### Insights Tab

- Feature Importance Visualization
- Example Predictions for Different Profiles
- Key Insights about Risk Factors

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

### Utils Module (Original - Matplotlib)

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

# Create visualizations (returns Matplotlib figures)
risk_gauge_fig = plot_risk_gauge(risk_score)
feature_importance_fig = plot_feature_importance(model)
comparison_fig = plot_prediction_comparison(prediction, avg_charges)
```

### Utils Module (Modernized - Plotly)

```python
from utils_plotly import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

# Load the trained model
model = load_model()

# Make a prediction
prediction = predict_insurance_charges(model, age, gender, bmi, children, smoker, region)

# Generate risk score (1-10)
risk_score = generate_risk_score(prediction, max_charge=50000)

# Create visualizations (returns Plotly figures)
risk_gauge_fig = plot_risk_gauge(risk_score)
feature_importance_fig = plot_feature_importance(model)
comparison_fig = plot_prediction_comparison(prediction, avg_charges)
```

## Visualization Improvements

The modernized version (`app_plotly.py` with `utils_plotly.py`) includes several improvements over the original version:

1. **Interactive Visualizations**
   - Hover effects to show detailed information
   - Zoom and pan capabilities
   - Ability to save visualizations as PNG files

2. **Modern Design**
   - Contemporary color schemes
   - Improved typography and layout
   - Responsive design that adapts to different screen sizes

3. **Enhanced User Experience**
   - Animated transitions
   - Tooltips with additional information
   - Improved readability and accessibility

4. **Risk Factor Cards**
   - Visual representation of risk factors
   - Color-coded impact levels
   - Concise explanations of risk implications

## Troubleshooting

### Common Issues

1. **Model Not Found Error**
   - Ensure you've run `python model.py` to train and save the model
   - Check that the `models` directory exists and contains `insurance_model.pkl`

2. **Database Errors**
   - Verify that the `data` directory exists and is writable
   - Check database permissions if you encounter access issues

3. **Visualization Problems**
   - If visualizations don't appear, ensure you have the correct dependencies installed
   - For Plotly visualizations, make sure you're using `app_plotly.py` and not `app.py`

### Getting Help

If you encounter issues not covered in this documentation, please:

1. Run the tests to verify that all components are working correctly
2. Check the console output for error messages
3. Refer to the Streamlit and Plotly documentation for specific issues related to those libraries

## Future Enhancements

- Integration with real insurance data sources
- Additional machine learning models for comparison
- User authentication and personalized dashboards
- Export functionality for reports and visualizations
- Mobile-optimized interface

## Contributing

Contributions to improve the application are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Run the tests to ensure everything works
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.