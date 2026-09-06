"""Measures the run time of the generator against the real Mist file.

Why:
    Success criterion SC-008 says one whole run must finish in less than 60
    seconds. The Mist file holds 16 MB of JSON, so a careless reader that walks
    it more than once passes that limit without a warning.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from src.mib_generator.runner import MibGeneratorRunner

REPO_ROOT = Path(__file__).resolve().parents[3]  # A pytest fixture moves the working folder, so paths are absolute.
OPENAPI = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"  # The 16 MB file that Mist ships.
ALLOWLIST = REPO_ROOT / "data" / "mib_generator" / "allowlist.json"  # The checked-in endpoint selection.
LEDGER = REPO_ROOT / "data" / "mib_generator" / "oid_assignments.json"  # The checked-in number of each field.
TIME_LIMIT_SECONDS = 60.0  # The limit that success criterion SC-008 states.


@pytest.mark.slow
def test_one_whole_run_finishes_inside_the_limit(tmp_path: Path) -> None:
    """Prove a whole generate run stays inside 60 seconds."""
    runner = MibGeneratorRunner(OPENAPI, ALLOWLIST, LEDGER)  # The runner reads all three checked-in inputs.
    start = time.monotonic()  # A monotonic clock cannot move backwards during the run.
    runner.generate(tmp_path / "MISTHELPER-MIB.mib")
    elapsed = time.monotonic() - start
    assert elapsed < TIME_LIMIT_SECONDS, f"The run took {elapsed:.1f} seconds."
