"""Guard against adding tests that import deprecated top-level facade names."""

from __future__ import annotations

from pathlib import Path

import pytest

_GUARD_PATH = "tests/unit/config/standalone/foundation/support/quality/imports/" "test_no_new_legacy_facade_imports.py"
_ALLOWED_EXISTING_REFERENCES = {
    "tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py",
    "tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py",
    "tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_19_device_port_stats.py",
    "tests/integration/test_mistapi_sdk_compatibility.py",
    "tests/guardrails/test_wave1_safety_classification_guardrails.py",
    "tests/guardrails/test_wave1_entry_routing_guardrails.py",
}
_BANNED_TOKENS = (
    "MistHelper.SiteExportUtils",
    "MistHelper.InsightMetricsUtils",
    "MistHelper.OperationRegistry",
    "MistHelper.TimeUtils",
)


def _check_test_sources(repository_root: Path) -> int:
    """Scan test sources and reject new imports from selected legacy facades."""
    test_root = repository_root / "tests"  # Keep the scan inside the repository test tree.
    assert test_root.is_dir(), f"Test root not found: {test_root}"  # Refuse a missing scan root.
    python_files = sorted(test_root.rglob("*.py"))  # Sort paths for stable evidence and failures.
    violations: list[str] = []  # Collect all hits for one useful failure.
    checked_files = 0  # Count only files that the guard actually reads.

    for python_file in python_files:  # Inspect each source file below the test root.
        relative_path = python_file.relative_to(repository_root).as_posix()  # Normalize exceptions.
        if relative_path == _GUARD_PATH or relative_path in _ALLOWED_EXISTING_REFERENCES:
            continue  # Exclude this guard and documented migration exceptions.
        checked_files += 1  # Record each file before reading its contents.
        content_text = python_file.read_text(encoding="utf-8", errors="ignore")  # Read source safely.
        for banned_token in _BANNED_TOKENS:  # Check every facade name that this guard retires.
            if banned_token in content_text:  # Detect a new reference in test code.
                violations.append(f"{relative_path}: contains {banned_token}")  # Keep actionable evidence.

    assert checked_files > 0, f"No Python test files found under {test_root}"  # Reject a vacuous scan.
    print(f"Checked {checked_files} Python test files for legacy facade imports")  # Report scan size.
    assert not violations, f"New legacy facade test references detected: {violations}"  # Enforce the guard.
    return checked_files


def test_no_new_test_imports_of_selected_legacy_facades(
    request: pytest.FixtureRequest,
) -> None:
    """Use pytest's configured repository root to scan the current test tree."""
    repository_root = Path(request.config.rootpath)  # Use pytest's repository configuration after relocation.
    checked_files = _check_test_sources(repository_root)  # Run the scanner and retain its examined count.
    assert checked_files > 0  # Require measurable scan work in the passing case.


def test_guard_rejects_missing_test_root(tmp_path: Path) -> None:
    """Fail when the configured root has no tests directory."""
    with pytest.raises(AssertionError, match="Test root not found"):  # Verify a missing root is not accepted.
        _check_test_sources(tmp_path)  # Exercise the guard with no tests directory.


def test_guard_rejects_empty_test_root(tmp_path: Path) -> None:
    """Fail when the tests directory contains no Python source files."""
    (tmp_path / "tests").mkdir()  # Create an empty scan root for the vacuous-scan regression.
    with pytest.raises(AssertionError, match="No Python test files found"):  # Require a non-empty scan.
        _check_test_sources(tmp_path)  # Exercise the guard with no source files.


def test_guard_rejects_forbidden_legacy_facade_import(tmp_path: Path) -> None:
    """Prove that a forbidden facade import fails the guard."""
    test_root = tmp_path / "tests"  # Isolate the negative control from the repository.
    test_root.mkdir()  # Create one source file for the guard to examine.
    (test_root / "test_forbidden_import.py").write_text(
        "import MistHelper.TimeUtils\n",
        encoding="utf-8",
    )  # Add a forbidden import that the scan must detect.
    with pytest.raises(
        AssertionError,
        match="New legacy facade test references detected",
    ):  # Prove the existing rule rejects the negative control.
        _check_test_sources(tmp_path)  # Run the actual scanner against the synthetic source.
