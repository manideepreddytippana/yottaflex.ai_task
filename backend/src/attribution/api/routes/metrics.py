"""Evaluation and Pipeline Metrics routes."""

from fastapi import APIRouter
from src.attribution.api.schemas import EvaluationMetricsResponse
from src.attribution.services.metrics import MetricsService

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])
service = MetricsService()


@router.get("", response_model=EvaluationMetricsResponse)
def get_metrics() -> EvaluationMetricsResponse:
    res = service.get_pipeline_metrics()
    return EvaluationMetricsResponse(**res)

