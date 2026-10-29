"""Data Issues and Exceptions routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.attribution.api.schemas import (
    DataIssueListResponse,
    DataIssueDetailResponse,
)
from src.attribution.services.issues import IssueService

router = APIRouter(prefix="/api/issues", tags=["Exceptions & Data Quality"])
service = IssueService()


@router.get("", response_model=DataIssueListResponse)
def list_issues(
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    resolution_status: Optional[str] = Query(None, description="Filter by status (OPEN, RESOLVED, IGNORED)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (order, touchpoint, cost, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
) -> DataIssueListResponse:
    itype = issue_type if isinstance(issue_type, str) else None
    sev = severity if isinstance(severity, str) else None
    rstatus = resolution_status if isinstance(resolution_status, str) else None
    etype = entity_type if isinstance(entity_type, str) else None
    p = page if isinstance(page, int) else 1
    ps = page_size if isinstance(page_size, int) else 20

    res = service.list_issues(
        issue_type=itype,
        severity=sev,
        resolution_status=rstatus,
        entity_type=etype,
        page=p,
        page_size=ps,
    )
    return DataIssueListResponse(**res)


@router.get("/{issue_id}", response_model=DataIssueDetailResponse)
def get_issue_detail(issue_id: str) -> DataIssueDetailResponse:
    res = service.get_issue_detail(issue_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Data issue '{issue_id}' not found.")
    return DataIssueDetailResponse(**res)
