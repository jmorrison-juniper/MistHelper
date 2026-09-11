"""Idempotency test for the issue #429 logging codemod.

Applies the codemod to a synthetic input file twice; asserts the second
pass produces a zero-byte diff. Phase 0 only verifies the scaffold's
no-op behavior on a small fixture; Phase 1 will extend this to assert
actual rewrites are stable across re-applications.
"""

from __future__ import annotations  # PEP 604 union syntax for Python 3.13.

import subprocess  # Drive the codemod CLI as a subprocess so we test the public surface.
import sys  # Path to the active python interpreter for the subprocess call.
from pathlib import Path  # Portable filesystem handling.

REPO_ROOT = Path(__file__).resolve().parent.parent  # tests/ -> repo root.
SYNTHETIC_INPUT = REPO_ROOT / "tests" / "fixtures" / "issue_429_codemod_synthetic_input.py"  # Test target.
CODEMOD = REPO_ROOT / "tools" / "codemod_logging_lazy.py"  # CLI we are exercising.


def test_codemod_dry_run_is_idempotent(tmp_path: Path) -> None:
    """Running the codemod in --dry-run twice produces an unchanged file."""
    target = tmp_path / "subject.py"  # Copy the synthetic input to a temp dir per test.
    target.write_text(SYNTHETIC_INPUT.read_text(encoding="utf-8"), encoding="utf-8")  # Seed input.
    before = target.read_text(encoding="utf-8")  # Snapshot byte content prior to first pass.
    _run_codemod(target, dry_run=True)  # First pass: dry-run so no write should occur.
    after_first = target.read_text(encoding="utf-8")  # Snapshot after first invocation.
    _run_codemod(target, dry_run=True)  # Second pass: dry-run again.
    after_second = target.read_text(encoding="utf-8")  # Snapshot after second invocation.
    assert before == after_first, "dry-run modified the file on first pass"  # Dry-run contract.
    assert after_first == after_second, "dry-run not idempotent across two passes"  # Stability check.


def _run_codemod(target: Path, *, dry_run: bool) -> None:
    """Invoke `tools/codemod_logging_lazy.py` via subprocess and assert exit 0."""
    cmd = [sys.executable, str(CODEMOD), str(target)]  # Always pass python explicitly.
    if dry_run:  # Forward the dry-run flag when requested.
        cmd.append("--dry-run")  # Tell the codemod to write nothing.
    result = subprocess.run(  # nosec B603 - subprocess args constructed from trusted paths.
        cmd,
        capture_output=True,  # Suppress stderr noise in pytest output unless we need it.
        text=True,  # Decode stdout/stderr as text for easy debug printing.
        check=False,  # We assert below so failures show stderr.
    )
    assert (
        result.returncode == 0
    ), f"codemod exited {result.returncode}\nSTDERR:\n{result.stderr}"  # Surface the captured stderr on failure.
