"""Base service class and common utilities for attribution services."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# PROJECT_ROOT anchors to backend directory: backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class BaseService:
    """Base class for all business logic and data access services."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir:
            self.data_dir = data_dir
        elif (PROJECT_ROOT / "data" / "generated" / "full").is_dir():
            self.data_dir = PROJECT_ROOT / "data" / "generated" / "full"
        else:
            self.data_dir = PROJECT_ROOT / "data" / "generated" / "starter"

