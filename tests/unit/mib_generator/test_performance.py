"""Measures the run time of the generator against the real Mist file.

Why:
    Success criterion SC-008 says one whole run must finish in less than 60
    seconds. The Mist file holds 16 MB of JSON, so a careless reader that walks
    it more than once passes that limit without a warning.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from src.mib_generator.runner import MibGeneratorRunner

REPO_ROOT = Path(__file__).resolve().parents[3]  # A pytest fixture moves the working folder, so paths are absolute.
OPENAPI = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"  # The 16 MB file that Mist ships.
ALLOWLIST = REPO_ROOT / "data" / "mib_generator" / "allowlist.json"  # The checked-in endpoint selection.
LEDGER = REPO_ROOT / "data" / "mib_generator" / "oid_assignments.json"  # The checked-in number of each field.
TIME_LIMIT_SECONDS = 60.0  # The limit that success criterion SC-008 states.


def writable_ledger_copy(tmp_path: Path) -> Path:
    """Return a temporary copy of the checked-in ledger.

    Why:
        ``MibGeneratorRunner.generate`` calls ``OidLedger.save`` at
        ``src/mib_generator/runner.py:180``, because a real run must keep the
        number of every new field. A test that points the runner at the
        checked-in ledger therefore writes into the repository, and the working
        tree stays dirty after the run. Issue #3021 records that defect.

        The copy keeps the real content, so the timing measurement still reads
        the true input size. Only the write moves to a temporary folder.

    Args:
        tmp_path: The per-test temporary folder that pytest provides.

    Returns:
        The path of the writable copy.
    """
    destination = tmp_path / LEDGER.name  # Keep the file name, because the reader logs it.
    shutil.copyfile(LEDGER, destination)  # Copy the real content, so the run reads the true input.
    return destination


@pytest.mark.slow
def test_one_whole_run_finishes_inside_the_limit(tmp_path: Path) -> None:
    """Prove a whole generate run stays inside 60 seconds."""
    ledger = writable_ledger_copy(tmp_path)  # WHY: the run saves the ledger, so it must not write the repository.
    runner = MibGeneratorRunner(OPENAPI, ALLOWLIST, ledger)  # The runner reads all three checked-in inputs.
    start = time.monotonic()  # A monotonic clock cannot move backwards during the run.
    runner.generate(tmp_path / "MISTHELPER-MIB.mib")
    elapsed = time.monotonic() - start
    assert elapsed < TIME_LIMIT_SECONDS, f"The run took {elapsed:.1f} seconds."


def test_the_run_leaves_the_checked_in_ledger_untouched(tmp_path: Path) -> None:
    """Prove a generate run never writes the ledger that the repository tracks.

    Why:
        Issue #3021 records the defect. The run wrote the checked-in ledger, so
        an engineer read a change that nobody made. This test reads the bytes
        before the run and after it, so the defect cannot return in silence.
    """
    before = LEDGER.read_bytes()  # WHY: capture the tracked content before any run touches the disk.
    ledger = writable_ledger_copy(tmp_path)  # WHY: the run must write this copy and nothing else.
    MibGeneratorRunner(OPENAPI, ALLOWLIST, ledger).generate(tmp_path / "MISTHELPER-MIB.mib")
    assert LEDGER.read_bytes() == before, f"{LEDGER} changed during the run, so the suite writes the repository."
    assert ledger.read_bytes(), "The copy holds no content, so the run wrote no ledger and the guard proves nothing."
