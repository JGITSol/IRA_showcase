#!/usr/bin/env python3
"""Generate test data for the application."""

import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import numpy as np
from faker import Faker
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth import get_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Constants
NUM_TEST_USERS = 10
NUM_PREDICTIONS_PER_USER = 20


def create_test_users(db: Session) -> List[User]:
    """Create test users.
    
    Args:
        db: Database session
        
    Returns:
        List[User]: List of created users
    """
    logger.info("Creating test users...")
    
    # Create superuser if it doesn't exist
    superuser = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    if not superuser:
        superuser = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name="Admin User",
            is_superuser=True,
            is_active=True,
        )
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
    
    # Create regular users
    users = [superuser]
    for i in range(NUM_TEST_USERS):
        email = f"user_{i}@example.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("testpassword"),
                full_name=fake.name(),
                is_superuser=False,
                is_active=random.choice([True, True, True, False]),  # 25% chance of inactive
            )
            db.add(user)
            users.append(user)
    
    db.commit()
    logger.info(f"Created {len(users)} users")
    return users


def create_test_predictions(db: Session, users: List[User]) -> None:
    """Create test predictions.
    
    Args:
        db: Database session
        users: List of users to create predictions for
    """
    logger.info("Creating test predictions...")
    
    # Generate realistic insurance data
    ages = np.random.normal(40, 15, NUM_PREDICTIONS_PER_USER * len(users)).astype(int)
    ages = np.clip(ages, 18, 80)  # Ensure ages are between 18 and 80
    
    bmis = np.random.normal(30, 6, NUM_PREDICTIONS_PER_USER * len(users))
    bmis = np.clip(bmis, 15, 50)  # Ensure BMIs are reasonable
    
    children = np.random.poisson(1, NUM_PREDICTIONS_PER_USER * len(users))
    children = np.clip(children, 0, 5)  # 0 to 5 children
    
    # Generate charges based on age, bmi, and children with some noise
    charges = (
        250 * ages  # Base cost increases with age
        + 200 * bmis  # Higher BMI increases cost
        + 1000 * children  # Each child adds to the cost
        + np.random.normal(0, 1000, NUM_PREDICTIONS_PER_USER * len(users))  # Random noise
    )
    charges = np.maximum(charges, 1000)  # Ensure minimum charge
    
    # Create predictions
    regions = ["southwest", "southeast", "northwest", "northeast"]
    
    predictions = []
    idx = 0
    
    for user in users:
        for _ in range(NUM_PREDICTIONS_PER_USER):
            age = ages[idx]
            bmi = round(float(bmis[idx]), 1)
            children_count = int(children[idx])
            charge = round(float(charges[idx]), 2)
            
            # Generate risk score (0-100) based on age, bmi, and children
            risk_score = min(100, int(age * 0.5 + bmi * 0.8 + children_count * 5))
            
            prediction = Prediction(
                age=age,
                sex=random.choice(["male", "female"]),
                bmi=bmi,
                children=children_count,
                smoker=random.choice([True, False]),
                region=random.choice(regions),
                charges=charge,
                risk_score=risk_score,
                user_id=user.id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
            )
            predictions.append(prediction)
            idx += 1
    
    db.bulk_save_objects(predictions)
    db.commit()
    logger.info(f"Created {len(predictions)} predictions")


def main() -> None:
    """Main function to generate test data."""
    logger.info("Starting test data generation...")
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create test users
        users = create_test_users(db)
        
        # Create test predictions
        create_test_predictions(db, users)
        
        logger.info("✅ Test data generation complete!")
    except Exception as e:
        logger.error(f"❌ Error generating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
