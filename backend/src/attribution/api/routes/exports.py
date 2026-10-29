"""Exports listing and downloads route."""

from fastapi import APIRouter
from src.attribution.api.schemas import RunExportsResponse
from src.attribution.services.exports import ExportService

router = APIRouter(prefix="/api/exports", tags=["Exports"])
service = ExportService()


@router.get("/{run_id}", response_model=RunExportsResponse)
def list_exports(run_id: str) -> RunExportsResponse:
    res = service.list_exports(run_id)
    return RunExportsResponse(**res)

