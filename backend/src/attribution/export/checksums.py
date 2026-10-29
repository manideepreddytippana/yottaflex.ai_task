"""SHA-256 checksum generation and verification for exported data artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute hex SHA-256 hash of a file."""
    p = Path(file_path)
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_checksums_file(directory: Path | str, output_filename: str = "checksums.sha256") -> Path:
    """Generate a checksums.sha256 manifest of all CSV files in the directory."""
    dir_path = Path(directory)
    checksum_lines: list[str] = []

    # Sort filenames deterministically
    csv_files = sorted(dir_path.glob("*.csv"))
    for file_path in csv_files:
        digest = compute_file_sha256(file_path)
        checksum_lines.append(f"{digest}  {file_path.name}")

    out_file = dir_path / output_filename
    out_file.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return out_file


def verify_checksums(directory: Path | str, checksum_filename: str = "checksums.sha256") -> tuple[bool, list[str]]:
    """Verify all files against the checksum manifest."""
    dir_path = Path(directory)
    manifest = dir_path / checksum_filename
    if not manifest.is_file():
        return False, [f"Manifest {checksum_filename} not found in {dir_path}"]

    errors: list[str] = []
    lines = manifest.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        expected_hash, fname = line.split(maxsplit=1)
        target = dir_path / fname
        if not target.is_file():
            errors.append(f"Missing file: {fname}")
            continue
        actual_hash = compute_file_sha256(target)
        if actual_hash != expected_hash:
            errors.append(f"Checksum mismatch for {fname}: expected {expected_hash}, got {actual_hash}")

    return len(errors) == 0, errors

