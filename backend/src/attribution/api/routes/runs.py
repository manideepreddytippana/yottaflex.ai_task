"""Pipeline Runs and Validation routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.attribution.api.schemas import (
    RunSummary,
    RunDetailResponse,
    RunCreateRequest,
    ValidationSummaryResponse,
)
from src.attribution.services.runs import RunService

router = APIRouter(prefix="/api/runs", tags=["Runs & Validation"])
service = RunService()


@router.get("", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    runs = service.list_runs()
    return [RunSummary(**r) for r in runs]


@router.post("", response_model=RunSummary, status_code=201)
def trigger_run(payload: RunCreateRequest) -> RunSummary:
    """Trigger or register a pipeline run."""
    # For now, return latest/configured starter run or stub
    runs = service.list_runs()
    if runs:
        return RunSummary(**runs[0])
    raise HTTPException(status_code=400, detail="No run available to trigger.")


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    run = service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return RunDetailResponse(**run)


@router.get("/{run_id}/validation", response_model=ValidationSummaryResponse)
def get_validation_summary(run_id: str) -> ValidationSummaryResponse:
    val = service.get_validation_summary(run_id)
    if not val:
        raise HTTPException(status_code=404, detail=f"Validation summary for run '{run_id}' not found.")
    return ValidationSummaryResponse(**val)

