"""Automated repeatability test: Runs two passes with the same configuration and asserts bit-for-bit parity."""

from pathlib import Path
import pytest

from scripts.verify_reproducibility import run_pipeline_for_reproducibility


def test_reproducibility_bit_for_bit_parity(tmp_path):
    config_path = "config/starter.yaml"
    dir_a = tmp_path / "run_A"
    dir_b = tmp_path / "run_B"

    res_a = run_pipeline_for_reproducibility(config_path, dir_a)
    res_b = run_pipeline_for_reproducibility(config_path, dir_b)

    # 1. Row counts match
    assert res_a["row_counts"] == res_b["row_counts"]

    # 2. Ground truth counts match
    assert res_a["ground_truth_count"] == res_b["ground_truth_count"]

    # 3. All entity file SHA-256 hashes match bit-for-bit
    checksums_a = res_a["checksums"]
    checksums_b = res_b["checksums"]

    assert set(checksums_a.keys()) == set(checksums_b.keys())
    assert len(checksums_a) >= 15

    for filename, hash_a in checksums_a.items():
        hash_b = checksums_b[filename]
        assert hash_a == hash_b, f"Checksum mismatch in {filename}: {hash_a} != {hash_b}"

