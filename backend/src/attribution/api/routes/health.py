"""Health check route."""

from fastapi import APIRouter
from src.attribution.api.schemas import HealthResponse
from src.attribution.services.health import HealthService

router = APIRouter(tags=["Health"])
service = HealthService()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    res = service.check_health()
    return HealthResponse(**res)

