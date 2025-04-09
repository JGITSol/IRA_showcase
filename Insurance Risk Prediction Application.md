<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Insurance Risk Prediction Application

This project implements a comprehensive insurance risk prediction system using Streamlit, machine learning, and SQLite for data persistence. The application enables users to predict insurance charges based on personal information, visualize risk assessments, and manage prediction records through CRUD operations.

## Project Components

The application consists of four main files: `app.py` (main Streamlit interface), `model.py` (for model training), `database.py` (for data persistence), and `utils.py` (for helper functions).

### 1. Model Training Script (`model.py`)

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import pickle
import os

def train_model():
    """
    Train a machine learning model for insurance risk prediction.
    The model predicts insurance charges based on demographic and health information.
    """
    # Create synthetic data for demonstration
    np.random.seed(42)
    n_samples = 1000
    
    age = np.random.randint(18, 65, n_samples)
    gender = np.random.choice(['male', 'female'], n_samples)
    bmi = np.random.normal(26, 4, n_samples)
    children = np.random.randint(0, 5, n_samples)
    smoker = np.random.choice(['yes', 'no'], n_samples, p=[0.2, 0.8])
    region = np.random.choice(['northeast', 'northwest', 'southeast', 'southwest'], n_samples)
    
    # Calculate synthetic insurance charges
    charges = 5000 + 100 * age
    charges += 200 * (bmi - 25) * (bmi &gt; 25)
    charges += 20000 * (smoker == 'yes')
    charges += 2000 * children
    charges += np.random.normal(0, 2000, n_samples)
    
    # Create DataFrame
    data = pd.DataFrame({
        'age': age,
        'gender': gender,
        'bmi': bmi,
        'children': children,
        'smoker': smoker,
        'region': region,
        'charges': charges
    })
    
    # Split features and target
    X = data.drop('charges', axis=1)
    y = data['charges']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define preprocessing for categorical and numerical features
    categorical_features = ['gender', 'smoker', 'region']
    numerical_features = ['age', 'bmi', 'children']
    
    categorical_transformer = OneHotEncoder(drop='first')
    numerical_transformer = StandardScaler()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # Create and train the model pipeline
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluate the model
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Model R² on training data: {train_score:.4f}")
    print(f"Model R² on test data: {test_score:.4f}")
    
    # Save the model
    if not os.path.exists('models'):
        os.makedirs('models')
    
    with open('models/insurance_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    print("Model saved to models/insurance_model.pkl")
    
    # Save sample data for reference
    if not os.path.exists('data'):
        os.makedirs('data')
    data.to_csv('data/insurance_data.csv', index=False)
    
    return model

if __name__ == "__main__":
    model = train_model()
```


### 2. Database Operations (`database.py`)

```python
import sqlite3
import os
import datetime

class Database:
    def __init__(self, db_name='insurance_predictions.db'):
        """Initialize database connection and create table if it doesn't exist."""
        # Create the data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.conn = sqlite3.connect(f'data/{db_name}')
        self.cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            bmi REAL,
            children INTEGER,
            smoker TEXT,
            region TEXT,
            predicted_charges REAL,
            prediction_date TEXT
        )
        ''')
        self.conn.commit()
    
    def add_prediction(self, age, gender, bmi, children, smoker, region, predicted_charges):
        """Add a new prediction to the database."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
        INSERT INTO predictions (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_predictions(self):
        """Retrieve all predictions from the database."""
        self.cursor.execute('SELECT * FROM predictions ORDER BY prediction_date DESC')
        columns = [desc[^0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        # Convert to list of dictionaries
        predictions = []
        for row in results:
            predictions.append(dict(zip(columns, row)))
        
        return predictions
    
    def get_prediction_by_id(self, prediction_id):
        """Retrieve a specific prediction by ID."""
        self.cursor.execute('SELECT * FROM predictions WHERE id = ?', (prediction_id,))
        columns = [desc[^0] for desc in self.cursor.description]
        result = self.cursor.fetchone()
        
        if result:
            return dict(zip(columns, result))
        return None
    
    def update_prediction(self, prediction_id, age, gender, bmi, children, smoker, region, predicted_charges):
        """Update an existing prediction."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
        UPDATE predictions
        SET age = ?, gender = ?, bmi = ?, children = ?, smoker = ?, region = ?, 
            predicted_charges = ?, prediction_date = ?
        WHERE id = ?
        ''', (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date, prediction_id))
        
        self.conn.commit()
        return self.cursor.rowcount &gt; 0
    
    def delete_prediction(self, prediction_id):
        """Delete a prediction from the database."""
        self.cursor.execute('DELETE FROM predictions WHERE id = ?', (prediction_id,))
        self.conn.commit()
        return self.cursor.rowcount &gt; 0
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
```


### 3. Utility Functions (`utils.py`)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pickle
import os

def load_model():
    """Load the trained model."""
    model_path = 'models/insurance_model.pkl'
    
    if not os.path.exists(model_path):
        st.error("Model file not found. Please train the model first.")
        return None
    
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    
    return model

def predict_insurance_charges(model, age, gender, bmi, children, smoker, region):
    """Make a prediction using the trained model."""
    if model is None:
        return None
    
    # Create a DataFrame with the input data
    input_data = pd.DataFrame({
        'age': [age],
        'gender': [gender],
        'bmi': [bmi],
        'children': [children],
        'smoker': [smoker],
        'region': [region]
    })
    
    # Make prediction
    prediction = model.predict(input_data)[^0]
    
    return prediction

def generate_risk_score(prediction, max_charge=50000):
    """Generate a risk score from 1-10 based on the predicted charges."""
    # Normalize the prediction to a score between 1 and 10
    score = min(10, max(1, round((prediction / max_charge) * 10)))
    return score

def plot_risk_gauge(risk_score):
    """Create a gauge chart to visualize risk score."""
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    
    # Configure the gauge
    angles = np.linspace(0, 1.5*np.pi, 11)
    angles = np.append(angles, [1.5*np.pi])
    
    # Set the labels
    labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '']
    
    # Plot the gauge
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)
    
    # Add colored regions for different risk levels
    ax.fill_between(np.linspace(0, 0.5*np.pi, 100), 0.9, 1, alpha=0.1, color='green')
    ax.fill_between(np.linspace(0.5*np.pi, np.pi, 100), 0.9, 1, alpha=0.1, color='yellow')
    ax.fill_between(np.linspace(np.pi, 1.5*np.pi, 100), 0.9, 1, alpha=0.1, color='red')
    
    # Plot the needle
    angle = (risk_score - 1) / 10 * 1.5 * np.pi
    ax.plot([0, angle], [0, 0.8], color='black', linewidth=2)
    ax.plot([angle, angle], [0.8, 0.9], color='black', linewidth=2)
    
    # Add a circle at the center
    ax.plot(0, 0, 'o', color='black', markersize=5)
    
    # Remove unnecessary parts of the plot
    ax.set_rticks([])
    ax.set_title('Risk Score', pad=20)
    ax.grid(True)
    
    return fig

def plot_feature_importance(model):
    """Plot feature importance for the model."""
    if not hasattr(model, 'named_steps'):
        return None
    
    if 'regressor' not in model.named_steps:
        return None
    
    regressor = model.named_steps['regressor']
    
    if not hasattr(regressor, 'feature_importances_'):
        return None
    
    # Get feature names after preprocessing
    preprocessor = model.named_steps['preprocessor']
    categorical_features = ['gender', 'smoker', 'region']
    numerical_features = ['age', 'bmi', 'children']
    
    # Get the one-hot encoded feature names
    cat_encoder = preprocessor.named_transformers_['cat']
    encoded_features = []
    
    for i, feature in enumerate(categorical_features):
        categories = cat_encoder.categories_[i][1:]  # Skip the first category (dropped)
        encoded_features.extend([f"{feature}_{category}" for category in categories])
    
    feature_names = numerical_features + encoded_features
    
    # Get feature importances
    importances = regressor.feature_importances_
    
    # Sort features by importance
    indices = np.argsort(importances)[::-1]
    
    # Create DataFrame for plotting
    importance_df = pd.DataFrame({
        'Feature': [feature_names[i] for i in indices],
        'Importance': importances[indices]
    })
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, ax=ax)
    ax.set_title('Feature Importance')
    
    return fig

def plot_prediction_comparison(prediction, avg_charges):
    """Plot the prediction compared to average charges."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create data for plotting
    categories = ['Your Prediction', 'Average Charges']
    values = [prediction, avg_charges]
    
    # Plot
    bars = ax.bar(categories, values, color=['#3498db', '#2ecc71'])
    
    # Add labels
    ax.set_ylabel('Insurance Charges ($)')
    ax.set_title('Prediction vs. Average Charges')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 500,
                f'${height:.2f}', ha='center', va='bottom')
    
    return fig
```


### 4. Main Streamlit Application (`app.py`)

```python
import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# Import custom modules
from database import Database
from utils import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

# Set page configuration
st.set_page_config(
    page_title="Insurance Risk Predictor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the database
db = Database()

# Define functions
def make_prediction():
    """Make a prediction based on user inputs and save to database."""
    # Load model
    model = load_model()
    
    if model is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return
    
    # Get user inputs
    age = st.session_state.age
    gender = st.session_state.gender
    bmi = st.session_state.bmi
    children = st.session_state.children
    smoker = st.session_state.smoker
    region = st.session_state.region
    
    # Make prediction
    prediction = predict_insurance_charges(model, age, gender, bmi, children, smoker, region)
    
    if prediction is not None:
        # Calculate risk score
        risk_score = generate_risk_score(prediction)
        
        # Update session state
        st.session_state.prediction = prediction
        st.session_state.risk_score = risk_score
        
        # Save prediction to database
        prediction_id = db.add_prediction(age, gender, bmi, children, smoker, region, prediction)
        
        st.session_state.prediction_made = True
        
        # Show success message
        st.success(f"Prediction saved with ID: {prediction_id}")
    else:
        st.error("Failed to make prediction.")

def view_predictions():
    """View all saved predictions."""
    predictions = db.get_all_predictions()
    
    if not predictions:
        st.info("No predictions found in the database.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(predictions)
    
    # Format currency values
    df['predicted_charges'] = df['predicted_charges'].apply(lambda x: f"${x:.2f}")
    
    # Display as table
    st.dataframe(df)
    
    # Allow user to select a prediction to view details
    prediction_ids = df['id'].tolist()
    selected_id = st.selectbox("Select a prediction to view details:", prediction_ids)
    
    if selected_id:
        view_prediction_details(selected_id)

def view_prediction_details(prediction_id):
    """View details of a specific prediction."""
    prediction = db.get_prediction_by_id(prediction_id)
    
    if not prediction:
        st.error(f"Prediction with ID {prediction_id} not found.")
        return
    
    # Display prediction details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Parameters")
        st.write(f"**Age:** {prediction['age']}")
        st.write(f"**Gender:** {prediction['gender']}")
        st.write(f"**BMI:** {prediction['bmi']:.2f}")
        st.write(f"**Children:** {prediction['children']}")
        st.write(f"**Smoker:** {prediction['smoker']}")
        st.write(f"**Region:** {prediction['region']}")
    
    with col2:
        st.subheader("Prediction Result")
        st.write(f"**Predicted Charges:** ${prediction['predicted_charges']:.2f}")
        st.write(f"**Prediction Date:** {prediction['prediction_date']}")
    
    # Show actions for this prediction
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load this prediction for editing"):
            # Set session state variables to this prediction's values
            st.session_state.age = prediction['age']
            st.session_state.gender = prediction['gender']
            st.session_state.bmi = prediction['bmi']
            st.session_state.children = prediction['children']
            st.session_state.smoker = prediction['smoker']
            st.session_state.region = prediction['region']
            
            # Switch to the prediction tab
            st.session_state.active_tab = "Predict"
            st.experimental_rerun()
    
    with col2:
        if st.button("Delete this prediction"):
            if db.delete_prediction(prediction_id):
                st.success(f"Prediction with ID {prediction_id} deleted.")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error(f"Failed to delete prediction with ID {prediction_id}.")

def display_model_insights():
    """Display insights and visualizations about the model."""
    model = load_model()
    
    if model is None:
        st.error("Failed to load model. Please ensure the model has been trained.")
        return
    
    st.subheader("Model Insights")
    
    # Feature importance
    st.write("### Feature Importance")
    st.write("This chart shows which factors have the most influence on insurance charges:")
    
    feature_imp_fig = plot_feature_importance(model)
    
    if feature_imp_fig:
        st.pyplot(feature_imp_fig)
    else:
        st.warning("Feature importance visualization is not available for this model.")
    
    # Example predictions
    st.write("### Example Predictions")
    st.write("See how different profiles affect insurance charges:")
    
    # Create example profiles
    profiles = [
        {"name": "Young Non-Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "no", "region": "northeast"},
        {"name": "Young Smoker", "age": 25, "gender": "male", "bmi": 22, "children": 0, "smoker": "yes", "region": "northeast"},
        {"name": "Middle-Aged Family", "age": 45, "gender": "female", "bmi": 28, "children": 2, "smoker": "no", "region": "southeast"},
        {"name": "Senior Citizen", "age": 65, "gender": "male", "bmi": 30, "children": 0, "smoker": "no", "region": "southwest"}
    ]
    
    # Make predictions for each profile
    results = []
    for profile in profiles:
        pred = predict_insurance_charges(
            model, profile["age"], profile["gender"], profile["bmi"], 
            profile["children"], profile["smoker"], profile["region"]
        )
        results.append({"Profile": profile["name"], "Predicted Charges": f"${pred:.2f}"})
    
    # Display as table
    st.table(pd.DataFrame(results))

# Main app layout
def main():
    # Add logo or header
    st.title("Insurance Risk Predictor")
    st.write("Predict insurance charges and assess risk factors")
    
    # Initialize session state variables if they don't exist
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Predict"
    
    if 'prediction_made' not in st.session_state:
        st.session_state.prediction_made = False
    
    if 'prediction' not in st.session_state:
        st.session_state.prediction = None
    
    if 'risk_score' not in st.session_state:
        st.session_state.risk_score = None
    
    # Input form default values
    if 'age' not in st.session_state:
        st.session_state.age = 30
    
    if 'gender' not in st.session_state:
        st.session_state.gender = "male"
    
    if 'bmi' not in st.session_state:
        st.session_state.bmi = 25.0
    
    if 'children' not in st.session_state:
        st.session_state.children = 0
    
    if 'smoker' not in st.session_state:
        st.session_state.smoker = "no"
    
    if 'region' not in st.session_state:
        st.session_state.region = "northeast"
    
    # Create tabs
    tabs = ["Predict", "History", "Insights"]
    
    # Display tabs and set active tab
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Predict", use_container_width=True):
            st.session_state.active_tab = "Predict"
    
    with col2:
        if st.button("History", use_container_width=True):
            st.session_state.active_tab = "History"
    
    with col3:
        if st.button("Insights", use_container_width=True):
            st.session_state.active_tab = "Insights"
    
    st.markdown(f"**Current Tab:** {st.session_state.active_tab}")
    st.markdown("---")
    
    # Display content based on active tab
    if st.session_state.active_tab == "Predict":
        # Create a form for user inputs
        with st.form("prediction_form"):
            st.subheader("Enter Your Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.number_input("Age", min_value=18, max_value=100, value=st.session_state.age, key="age")
                st.selectbox("Gender", options=["male", "female"], index=0 if st.session_state.gender == "male" else 1, key="gender")
                st.number_input("BMI", min_value=10.0, max_value=50.0, value=st.session_state.bmi, step=0.1, key="bmi")
            
            with col2:
                st.number_input("Number of Children", min_value=0, max_value=10, value=st.session_state.children, key="children")
                st.selectbox("Smoker", options=["yes", "no"], index=0 if st.session_state.smoker == "yes" else 1, key="smoker")
                st.selectbox("Region", options=["northeast", "northwest", "southeast", "southwest"], 
                             index=["northeast", "northwest", "southeast", "southwest"].index(st.session_state.region), key="region")
            
            # Submit button
            submitted = st.form_submit_button("Calculate Risk")
            
            if submitted:
                make_prediction()
        
        # Display prediction results if available
        if st.session_state.prediction_made:
            st.markdown("---")
            st.subheader("Prediction Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Predicted Insurance Charges", f"${st.session_state.prediction:.2f}")
                st.metric("Risk Score", f"{st.session_state.risk_score}/10")
            
            with col2:
                # Risk gauge visualization
                risk_gauge = plot_risk_gauge(st.session_state.risk_score)
                st.pyplot(risk_gauge)
            
            # Comparison with average
            st.markdown("---")
            st.subheader("Comparison with Average")
            
            avg_charges = 13270.42  # Example average value
            comparison_fig = plot_prediction_comparison(st.session_state.prediction, avg_charges)
            st.pyplot(comparison_fig)
            
            # Risk factors explanation
            st.markdown("---")
            st.subheader("Risk Factors")
            
            # Simplified risk factor explanation
            if st.session_state.smoker == "yes":
                st.warning("Being a smoker significantly increases your insurance risk.")
            
            if st.session_state.bmi &gt; 30:
                st.warning("A BMI over 30 (considered obese) increases health risks and insurance costs.")
            
            if st.session_state.age &gt; 50:
                st.info("Age is a factor in insurance pricing, with older individuals typically paying more.")
            
            # Action to make a new prediction
            if st.button("Make a New Prediction"):
                st.session_state.prediction_made = False
                st.experimental_rerun()
    
    elif st.session_state.active_tab == "History":
        view_predictions()
    
    elif st.session_state.active_tab == "Insights":
        display_model_insights()

if __name__ == "__main__":
    main()
```


## Setup and Installation

To run this application, you'll need to set up the environment and install required dependencies.

### 1. Requirements File (`requirements.txt`)

```
streamlit&gt;=1.12.0
pandas&gt;=1.3.0
numpy&gt;=1.20.0
matplotlib&gt;=3.4.0
seaborn&gt;=0.11.0
scikit-learn&gt;=1.0.0
```


### 2. Project Directory Structure

```
insurance-risk-predictor/
│
├── app.py                # Main Streamlit application
├── model.py              # Model training script
├── database.py           # Database operations
├── utils.py              # Helper functions
├── requirements.txt      # Dependencies
│
├── data/                 # Data directory (created automatically)
│   ├── insurance_data.csv           # Sample dataset
│   └── insurance_predictions.db     # SQLite database
│
└── models/               # Model directory (created automatically)
    └── insurance_model.pkl          # Trained model
```


## Key Features and Implementation Details

### Machine Learning Model

The application uses a Random Forest Regressor to predict insurance charges based on several features:

1. Age: Numeric input, 18-100 years
2. Gender: Categorical (male/female)
3. BMI (Body Mass Index): Numeric input
4. Number of Children: Numeric input
5. Smoker Status: Categorical (yes/no)
6. Region: Categorical (northeast, northwest, southeast, southwest)

The model is implemented with scikit-learn's Pipeline API, which handles both preprocessing (scaling numeric features and encoding categorical features) and the regression model itself[^5][^7].

### Interactive Web Interface

The Streamlit interface is organized into three main tabs:

1. **Predict**: Allows users to input their information and receive a prediction
2. **History**: Displays previous predictions with CRUD functionality
3. **Insights**: Shows model insights including feature importance and example predictions

The application uses Streamlit's form components, columns, and interactive elements to create an intuitive user experience[^1][^6].

### Data Visualization

The application includes several visualizations to help users understand their predictions:

1. **Risk Gauge**: A polar plot showing the risk score on a scale of 1-10
2. **Feature Importance**: A bar chart showing which factors have the greatest impact on predictions
3. **Comparison Chart**: A bar chart comparing the user's predicted charges to average charges

These visualizations are implemented using matplotlib and seaborn[^3][^7].

### CRUD Operations

The application provides full CRUD (Create, Read, Update, Delete) functionality for prediction records:

1. **Create**: New predictions are saved to the SQLite database
2. **Read**: Users can view all previous predictions and their details
3. **Update**: Users can load previous predictions for modification
4. **Delete**: Users can delete unwanted predictions

These operations are implemented using SQLite for data persistence[^4].

## Conclusion

This Insurance Risk Prediction application demonstrates how Streamlit can be combined with machine learning, data visualization, and database operations to create a complete, interactive web application. The system provides valuable insights into insurance risk factors and can be used as a template for similar prediction tools in other domains.

The modular structure of the codebase allows for easy maintenance and extension, while the interactive Streamlit interface makes it accessible to non-technical users. By leveraging Random Forest Regression and intuitive visualizations, the application provides both accurate predictions and clear explanations of risk factors.

<div>⁂</div>

[^1]: https://github.com/Prem07a/Heart-Disease

[^2]: https://towardsdatascience.com/end-to-end-automl-train-and-serve-with-h2o-mlflow-fastapi-and-streamlit-5d36eedfe606/

[^3]: https://github.com/Muhammad-Sheraz-ds/Predicting-Insurance-Claim

[^4]: https://proxlight.hashnode.dev/building-a-student-management-system-with-python-and-streamlit-a-step-by-step-guide

[^5]: https://github.com/Aftellez98/insurance-predictor-streamlit-app

[^6]: https://github.com/YashSDholam/Stroke-Prediction-Web-Application

[^7]: https://www.youtube.com/watch?v=2A9Vfru8tq8

[^8]: https://www.youtube.com/watch?v=JIeE_dM8u9M

[^9]: https://www.youtube.com/watch?v=T6lMgciw8o8

[^10]: https://www.cittabase.com/patient-condition-analysis-and-prediction-using-streamlit/

[^11]: https://discuss.streamlit.io/t/new-zritter2050-cormeum-streamlit-app-to-predict-the-risk-of-a-heart-attack/12631

[^12]: https://github.com/senihberkay/car-price-prediction-with-streamlit

[^13]: https://dev.to/jagroop2001/streamlit-the-magic-wand-for-ml-app-creation-43i8

[^14]: https://discuss.streamlit.io/t/create-database-web-apps-with-streamlit-sqlmodel-tutorial-spanish-code-avaliable/85402

[^15]: https://github.com/Raviteja-5976/CRUD-operations-using-streamlit

[^16]: https://discuss.streamlit.io/t/machine-learning-process-from-the-idea-to-the-app-stroke-prediction/53193

[^17]: https://www.youtube.com/watch?v=HQdCSbu1BSU

[^18]: https://github.com/aswintechguy/Machine-Learning-Projects/blob/master/Medical-Insurance-Cost-Predictor-Web-App-with-Streamlit/Medical_Insurance_Cost_Prediction.ipynb

[^19]: https://discuss.streamlit.io/t/can-a-simple-crud-app-be-made-with-streamlit/727

[^20]: https://discuss.streamlit.io/t/carlosishimwe-predicting-medical-insurance-charges/11370

