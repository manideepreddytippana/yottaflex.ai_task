"""Deliverable exports, manifests, and checksums service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.attribution.services.base import BaseService


class ExportService(BaseService):
    """Service for listing generated deliverable files and SHA-256 integrity checksums."""

    def list_exports(self, run_id: str) -> dict[str, Any]:
        """List all generated deliverable files, formats, sizes, and SHA-256 hashes."""
        target_dir = self.data_dir
        if not target_dir.is_dir():
            return {"run_id": run_id, "output_dir": str(target_dir), "exports": []}

        checksums_map: dict[str, str] = {}
        chk_file = target_dir / "checksums.sha256"
        if chk_file.is_file():
            with open(chk_file, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        checksums_map[parts[1]] = parts[0]

        exports = []
        for file_path in target_dir.glob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lstrip(".").lower()
                exports.append({
                    "filename": file_path.name,
                    "file_type": ext or "text",
                    "file_size_bytes": file_path.stat().st_size,
                    "checksum_sha256": checksums_map.get(file_path.name),
                    "relative_path": f"data/generated/starter/{file_path.name}",
                })

        exports.sort(key=lambda x: x["filename"])
        return {
            "run_id": run_id,
            "output_dir": str(target_dir),
            "exports": exports,
        }

