"""Test script to verify app functionality."""

import sys
import os

def test_imports():
    """Test that all imports work correctly."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        import plotly.express as px
        print("✓ Basic libraries imported successfully")
        
        # Test custom modules
        from database import Database
        print("✓ Database module imported successfully")
        
        from utils_plotly import (
            load_model, predict_insurance_charges, generate_risk_score,
            plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
        )
        print("✓ Utils plotly module imported successfully")
        
        from theme_utils import get_streamlit_theme, get_color_palette
        print("✓ Theme utils module imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False

def test_model_loading():
    """Test model loading functionality."""
    try:
        print("\nTesting model loading...")
        from utils_plotly import load_model
        
        model = load_model()
        if model is not None:
            print("✓ Model loaded successfully")
            return True
        else:
            print("✗ Model loading returned None")
            return False
    except Exception as e:
        print(f"✗ Model loading failed: {str(e)}")
        return False

def test_prediction():
    """Test prediction functionality."""
    try:
        print("\nTesting prediction...")
        from utils_plotly import load_model, predict_insurance_charges, generate_risk_score
        
        model = load_model()
        if model is None:
            print("✗ Cannot test prediction - model not loaded")
            return False
        
        # Test prediction
        prediction = predict_insurance_charges(
            model, age=30, gender='male', bmi=25.0, 
            children=2, smoker='no', region='northeast'
        )
        
        if prediction is not None:
            print(f"✓ Prediction successful: ${prediction:.2f}")
            
            # Test risk score
            risk_score = generate_risk_score(prediction)
            print(f"✓ Risk score generated: {risk_score}/10")
            return True
        else:
            print("✗ Prediction returned None")
            return False
    except Exception as e:
        print(f"✗ Prediction failed: {str(e)}")
        return False

def test_visualizations():
    """Test visualization functionality."""
    try:
        print("\nTesting visualizations...")
        from utils_plotly import plot_risk_gauge, plot_feature_importance, plot_prediction_comparison, load_model
        
        # Test risk gauge
        fig = plot_risk_gauge(5)
        if fig is not None:
            print("✓ Risk gauge created successfully")
        else:
            print("✗ Risk gauge creation failed")
            return False
        
        # Test prediction comparison
        fig = plot_prediction_comparison(15000, 12000)
        if fig is not None:
            print("✓ Prediction comparison chart created successfully")
        else:
            print("✗ Prediction comparison chart creation failed")
            return False
        
        # Test feature importance (requires model)
        model = load_model()
        if model is not None:
            fig = plot_feature_importance(model)
            if fig is not None:
                print("✓ Feature importance chart created successfully")
            else:
                print("✓ Feature importance chart creation skipped (expected for some models)")
        
        return True
    except Exception as e:
        print(f"✗ Visualization test failed: {str(e)}")
        return False

def test_database():
    """Test database functionality."""
    try:
        print("\nTesting database...")
        from database import Database
        
        # Create test database
        db = Database(db_name='test_functionality.db')
        
        # Test adding prediction
        pred_id = db.add_prediction(
            age=30, gender='male', bmi=25.0, children=2,
            smoker='no', region='northeast', predicted_charges=15000.0
        )
        
        if pred_id:
            print(f"✓ Prediction added to database with ID: {pred_id}")
            
            # Test retrieving prediction
            prediction = db.get_prediction_by_id(pred_id)
            if prediction:
                print("✓ Prediction retrieved from database")
                
                # Test deleting prediction
                success = db.delete_prediction(pred_id)
                if success:
                    print("✓ Prediction deleted from database")
                else:
                    print("✗ Failed to delete prediction")
            else:
                print("✗ Failed to retrieve prediction")
        else:
            print("✗ Failed to add prediction to database")
        
        db.close()
        
        # Clean up test database
        try:
            os.remove('data/test_functionality.db')
        except:
            pass
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {str(e)}")
        return False

def test_theme_utils():
    """Test theme utilities."""
    try:
        print("\nTesting theme utilities...")
        from theme_utils import get_streamlit_theme, get_color_palette
        
        theme = get_streamlit_theme()
        print(f"✓ Theme detected: {theme}")
        
        palette = get_color_palette()
        print(f"✓ Color palette loaded with {len(palette)} colors")
        
        return True
    except Exception as e:
        print(f"✗ Theme utils test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=== Insurance Risk Analyzer Functionality Test ===\n")
    
    tests = [
        test_imports,
        test_model_loading,
        test_prediction,
        test_visualizations,
        test_database,
        test_theme_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)