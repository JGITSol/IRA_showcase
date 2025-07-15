"""Main API router for v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, predictions, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    predictions.router, prefix="/predictions", tags=["predictions"]
)
