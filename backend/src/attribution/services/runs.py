"""Pipeline runs and data validation inspection service."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import desc, select

from src.attribution.db.models import PipelineRun, ValidationResult
from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class RunService(BaseService):
    """Service for managing and querying pipeline execution runs and validation reports."""

    def list_runs(self) -> list[dict[str, Any]]:
        """List historical pipeline execution runs with validation statuses and entity counts."""
        with get_db_session() as session:
            runs = session.scalars(select(PipelineRun).order_by(desc(PipelineRun.started_at))).all()
            if runs:
                return [
                    {
                        "run_id": r.run_id,
                        "status": r.status,
                        "started_at": r.started_at,
                        "completed_at": r.completed_at,
                        "seed": r.seed,
                        "generator_version": r.generator_version,
                        "dataset_scale": r.dataset_scale,
                        "total_entities": sum(r.row_counts_json.values()) if r.row_counts_json else 0,
                    }
                    for r in runs
                ]

        # Fallback to manifest on disk if DB empty
        manifest_path = self.data_dir / "manifest.json"
        if manifest_path.is_file():
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            return [
                {
                    "run_id": m.get("run_id", "RUN-20261022-starter"),
                    "status": m.get("validation_status", "PASS"),
                    "started_at": datetime.fromisoformat(m["generated_at"]) if "generated_at" in m else datetime.now(timezone.utc),
                    "completed_at": datetime.fromisoformat(m["generated_at"]) if "generated_at" in m else None,
                    "seed": m.get("seed", 20261022),
                    "generator_version": m.get("generator_version", "1.0.0"),
                    "dataset_scale": m.get("dataset_scale", "starter"),
                    "total_entities": sum(m.get("row_counts", {}).values()),
                }
            ]
        return []

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Retrieve full execution metadata, provenance, and row count breakdown for a run."""
        with get_db_session() as session:
            r = session.scalar(select(PipelineRun).where(PipelineRun.run_id == run_id))
            if r:
                return {
                    "run_id": r.run_id,
                    "status": r.status,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "seed": r.seed,
                    "generator_version": r.generator_version,
                    "config_hash": r.config_hash,
                    "dataset_scale": r.dataset_scale,
                    "row_counts": r.row_counts_json or {},
                    "checksums": r.checksums_json or {},
                }

        manifest_path = self.data_dir / "manifest.json"
        if manifest_path.is_file():
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("run_id") == run_id or run_id == "latest" or run_id.lower() == "starter":
                return {
                    "run_id": m.get("run_id"),
                    "status": m.get("validation_status", "PASS"),
                    "started_at": datetime.fromisoformat(m["generated_at"]) if "generated_at" in m else datetime.now(timezone.utc),
                    "completed_at": datetime.fromisoformat(m["generated_at"]) if "generated_at" in m else None,
                    "seed": m.get("seed", 20261022),
                    "generator_version": m.get("generator_version", "1.0.0"),
                    "config_hash": m.get("config_hash", ""),
                    "dataset_scale": m.get("dataset_scale", "starter"),
                    "row_counts": m.get("row_counts", {}),
                    "checksums": m.get("checksums", {}),
                }
        return None

    def get_validation_summary(self, run_id: str) -> Optional[dict[str, Any]]:
        """Retrieve automated data quality check results for a run."""
        with get_db_session() as session:
            val_results = session.scalars(select(ValidationResult)).all()
            if val_results:
                passed = sum(1 for v in val_results if v.status == "PASS")
                failed = sum(1 for v in val_results if v.status != "PASS")
                return {
                    "run_id": run_id,
                    "overall_status": "PASS" if failed == 0 else "FAIL",
                    "total_checks": len(val_results),
                    "passed_checks": passed,
                    "failed_checks": failed,
                    "checks": [
                        {
                            "check_name": v.check_name,
                            "entity_name": v.entity_name,
                            "records_checked": v.records_checked,
                            "failure_count": v.failure_count,
                            "status": v.status,
                            "details": v.details_json,
                        }
                        for v in val_results
                    ],
                }

        summary_path = self.data_dir / "validation_summary.json"
        if summary_path.is_file():
            with open(summary_path, "r", encoding="utf-8") as f:
                s = json.load(f)
            return {
                "run_id": run_id,
                "overall_status": s.get("overall_status", "PASS"),
                "total_checks": s.get("total_checks", 0),
                "passed_checks": s.get("passed_checks", 0),
                "failed_checks": s.get("failed_checks", 0),
                "checks": s.get("checks", []),
            }

        # Fallback to computing on-the-fly from data_dir
        try:
            from src.attribution.pipeline.validate import DataValidator
            validator = DataValidator(self.data_dir)
            report = validator.execute_all()
            return {
                "run_id": run_id,
                "overall_status": report.overall_status,
                "total_checks": report.total_checks,
                "passed_checks": report.passed_checks,
                "failed_checks": report.failed_checks,
                "checks": [
                    {
                        "check_name": f.check_name,
                        "entity_name": f.entity_name,
                        "records_checked": f.records_checked,
                        "failure_count": f.failure_count,
                        "status": f.status,
                        "details": f.details,
                    }
                    for f in report.findings
                ],
            }
        except Exception:
            return None

