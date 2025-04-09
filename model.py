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
    charges = 5000 + 100 * age.astype(float)
    charges += 200 * (bmi - 25) * (bmi > 25)
    charges += 20000 * (smoker == 'yes')
    charges += 2000 * children.astype(float)
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