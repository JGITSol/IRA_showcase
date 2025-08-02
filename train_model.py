"""Simple script to train and save the insurance model."""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

def create_synthetic_data():
    """Create synthetic insurance data for training."""
    np.random.seed(42)
    n_samples = 10000
    
    # Generate synthetic data
    data = {
        'age': np.random.randint(18, 65, n_samples),
        'gender': np.random.choice(['male', 'female'], n_samples),
        'bmi': np.random.normal(25, 5, n_samples).clip(15, 50),
        'children': np.random.poisson(1, n_samples).clip(0, 5),
        'smoker': np.random.choice(['yes', 'no'], n_samples, p=[0.2, 0.8]),
        'region': np.random.choice(['southwest', 'southeast', 'northwest', 'northeast'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Create synthetic charges based on realistic factors
    base_charge = 5000
    age_factor = (df['age'] - 18) * 50
    bmi_factor = np.where(df['bmi'] > 30, (df['bmi'] - 30) * 200, 0)
    smoker_factor = np.where(df['smoker'] == 'yes', 15000, 0)
    children_factor = df['children'] * 500
    
    df['charges'] = (
        base_charge + age_factor + bmi_factor + 
        smoker_factor + children_factor + 
        np.random.normal(0, 1000, n_samples)
    ).clip(1000, 50000)
    
    return df

def train_model():
    """Train the insurance prediction model."""
    print("Creating synthetic data...")
    df = create_synthetic_data()
    
    # Prepare features and target
    X = df[['age', 'gender', 'bmi', 'children', 'smoker', 'region']]
    y = df['charges']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create preprocessing pipelines
    numerical_features = ['age', 'bmi', 'children']
    categorical_features = ['gender', 'smoker', 'region']
    
    # Create preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(drop='first'), categorical_features)
        ]
    )
    
    # Create the full pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    print("Training model...")
    model.fit(X_train, y_train)
    
    # Evaluate the model
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Training R² score: {train_score:.4f}")
    print(f"Testing R² score: {test_score:.4f}")
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Save the model
    model_path = 'models/insurance_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {model_path}")
    
    return model

if __name__ == "__main__":
    train_model()