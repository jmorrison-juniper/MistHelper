"""Prevent reintroduction of legacy site-insights export shim callsites."""

from __future__ import annotations

from pathlib import Path

import pytest

_GUARD_NAME = "test_no_export_legacy_callsites.py"
_DISALLOWED_TOKEN = "InsightMetricsUtils" + ".export_legacy("


def _check_source_tree(repository_root: Path) -> int:
    """Scan repository Python sources and reject legacy export shim callsites."""
    repository_root = repository_root.resolve()  # Normalize root for reliable relative paths.
    assert repository_root.is_dir(), f"Repository root not found: {repository_root}"  # Reject invalid roots.
    python_files = sorted(repository_root.rglob("*.py"))  # Sort paths for stable evidence and failures.
    violations: list[str] = []  # Collect every matching line for one useful failure.
    checked_files = 0  # Count only files that the guard actually reads.

    for python_file in python_files:  # Inspect each Python source below the repository root.
        path_text = python_file.as_posix()  # Normalize paths for the existing exclusions.
        relative_path = python_file.relative_to(repository_root).as_posix()  # Keep evidence repository-relative.
        is_spec_artifact = "/specs/" in path_text  # Identify generated and planning artifacts.
        is_abandoned_spec = "/abandoned-specs/" in path_text  # Identify archived planning artifacts.
        is_finished_spec = "/finished-specs/" in path_text  # Identify completed planning artifacts.
        if is_spec_artifact or is_abandoned_spec or is_finished_spec:  # Keep scope limited to source.
            continue  # Ignore specification trees.
        if "/data/" in path_text or "/.venv/" in path_text or "__pycache__" in path_text:
            continue  # Ignore runtime outputs, environments, and bytecode caches.
        if python_file.name == _GUARD_NAME:  # Avoid matching this guard's own examples.
            continue  # Keep the guard from scanning itself.
        checked_files += 1  # Record each source before reading its contents.
        content_text = python_file.read_text(encoding="utf-8", errors="ignore")  # Read source safely.
        if _DISALLOWED_TOKEN not in content_text:  # Avoid line work when no callsite exists.
            continue  # Skip clean source files.
        for line_number, line_text in enumerate(content_text.splitlines(), start=1):
            if _DISALLOWED_TOKEN in line_text:  # Locate every banned callsite.
                violations.append(f"{relative_path}:{line_number}")  # Keep precise failure evidence.

    assert checked_files > 0, f"No Python source files found under {repository_root}"  # Reject a vacuous scan.
    print(f"Checked {checked_files} Python source files for legacy export callsites")  # Report scan size.
    assert not violations, f"Legacy export shim callsites found: {violations}"  # Enforce the migration guard.
    return checked_files


def test_no_internal_export_legacy_callsites(request: pytest.FixtureRequest) -> None:
    """Use pytest's configured repository root for the source scan."""
    repository_root = Path(request.config.rootpath)  # Use pytest's root after the test moves.
    checked_files = _check_source_tree(repository_root)  # Run the scanner and retain its examined count.
    assert checked_files > 0  # Require measurable scan work in the passing case.


def test_guard_rejects_missing_repository_root(tmp_path: Path) -> None:
    """Fail when the configured root does not exist."""
    with pytest.raises(AssertionError, match="Repository root not found"):  # Verify an invalid root is rejected.
        _check_source_tree(tmp_path / "missing")  # Exercise the guard with a missing root.


def test_guard_rejects_empty_source_tree(tmp_path: Path) -> None:
    """Fail when the root contains no Python source files."""
    with pytest.raises(AssertionError, match="No Python source files found"):  # Require a non-empty scan.
        _check_source_tree(tmp_path)  # Exercise the guard with an empty source tree.


def test_guard_rejects_legacy_export_callsite(tmp_path: Path) -> None:
    """Prove that a forbidden export callsite fails the guard."""
    source_directory = tmp_path / "src"  # Isolate the negative control from the repository.
    source_directory.mkdir()  # Create one directory for the synthetic source.
    (source_directory / "test_forbidden_callsite.py").write_text(
        "InsightMetricsUtils.export_legacy(\n",
        encoding="utf-8",
    )  # Add a callsite that the guard must detect.
    with pytest.raises(
        AssertionError,
        match="Legacy export shim callsites found",
    ):  # Prove the existing rule rejects the negative control.
        _check_source_tree(tmp_path)  # Run the actual scanner against the synthetic source.
