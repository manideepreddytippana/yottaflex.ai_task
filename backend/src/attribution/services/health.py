"""Health check service for database connectivity and system status."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class HealthService(BaseService):
    """Service for system health verification."""

    def check_health(self) -> dict[str, Any]:
        """Verify database connectivity and application status."""
        try:
            with get_db_session() as session:
                session.execute(select(1)).scalar_one()
            return {
                "status": "healthy",
                "version": "1.0.0",
                "database_connected": True,
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as e:
            return {
                "status": "degraded",
                "version": "1.0.0",
                "database_connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc),
            }

