"""Prediction API endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_active_user, get_db
from app.schemas.prediction import Prediction, PredictionCreate, PredictionUpdate
from app.services import prediction as prediction_service

router = APIRouter()


@router.post("/", response_model=Prediction)
def create_prediction(
    *,
    db: Session = Depends(get_db),
    prediction_in: PredictionCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Create new prediction.
    
    Args:
        db: Database session
        prediction_in: Prediction input data
        current_user: Current authenticated user
        
    Returns:
        Prediction: Created prediction
    """
    db_prediction = prediction_service.create_prediction(
        db=db, prediction_in=prediction_in, user_id=current_user.id
    )
    return db_prediction


@router.get("/", response_model=List[Prediction])
def read_predictions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Retrieve predictions for the current user.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        
    Returns:
        List[Prediction]: List of predictions
    """
    predictions, _ = prediction_service.get_predictions(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return predictions


@router.get("/{prediction_id}", response_model=Prediction)
def read_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Get prediction by ID.
    
    Args:
        prediction_id: ID of the prediction to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Prediction: The requested prediction
        
    Raises:
        HTTPException: If prediction is not found or not accessible
    """
    db_prediction = prediction_service.get_prediction(
        db=db, prediction_id=prediction_id, user_id=current_user.id
    )
    if not db_prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Prediction not found"
        )
    return db_prediction


@router.put("/{prediction_id}", response_model=Prediction)
def update_prediction(
    prediction_id: int,
    prediction_in: PredictionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Update a prediction.
    
    Args:
        prediction_id: ID of the prediction to update
        prediction_in: Updated prediction data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Prediction: The updated prediction
        
    Raises:
        HTTPException: If prediction is not found or not accessible
    """
    db_prediction = prediction_service.get_prediction(
        db=db, prediction_id=prediction_id, user_id=current_user.id
    )
    if not db_prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Prediction not found"
        )
    
    return prediction_service.update_prediction(
        db=db, db_prediction=db_prediction, prediction_in=prediction_in
    )


@router.delete("/{prediction_id}", response_model=Prediction)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Delete a prediction.
    
    Args:
        prediction_id: ID of the prediction to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Prediction: The deleted prediction
        
    Raises:
        HTTPException: If prediction is not found or not accessible
    """
    db_prediction = prediction_service.get_prediction(
        db=db, prediction_id=prediction_id, user_id=current_user.id
    )
    if not db_prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Prediction not found"
        )
    
    return prediction_service.delete_prediction(db=db, db_prediction=db_prediction)
