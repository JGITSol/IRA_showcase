"""API v1 package for Insurance Risk Analyzer."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["v1"])

# Import all endpoints to register them with the router
from . import endpoints  # noqa
