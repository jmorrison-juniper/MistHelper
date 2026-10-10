"""Guard nested Python package child counts under src."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("nested_package_baseline.json")
SOURCE_ROOT = "src"
MAX_CHILDREN = 5


@dataclass(frozen=True)
class BaselineViolation:
    """Store one accepted nested package violation."""

    child_count: int
    remediation_issue: int


def _baseline_error(path: Path, examined_count: int, detail: str) -> AssertionError:
    """Create a baseline error that reports the measured directory scope."""
    return AssertionError(
        f"Cannot read nested package baseline {path}: {detail}. Examined {examined_count} directories."
    )


def load_baseline(path: Path, examined_count: int = 0) -> dict[str, BaselineViolation]:
    """Load and validate the nested package baseline."""
    if not path.is_file():
        raise _baseline_error(path, examined_count, "file is missing")
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise _baseline_error(path, examined_count, str(error)) from error
    if not isinstance(payload, dict):
        raise _baseline_error(path, examined_count, "root is not an object")
    if payload.get("version") != 1 or payload.get("source_root") != SOURCE_ROOT:
        raise _baseline_error(path, examined_count, "header is invalid")
    if payload.get("max_children") != MAX_CHILDREN:
        raise _baseline_error(path, examined_count, "maximum child count is invalid")
    entries = payload.get("violations")
    if not isinstance(entries, list) or not entries:
        raise _baseline_error(path, examined_count, "violations is not a nonempty list")
    return _parse_entries(path, entries, examined_count)


def _parse_entries(
    path: Path,
    entries: list[Any],
    examined_count: int,
) -> dict[str, BaselineViolation]:
    """Validate baseline entries and return them by path."""
    violations: dict[str, BaselineViolation] = {}
    entry_paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise _baseline_error(path, examined_count, "an entry is not an object")
        entry_path = entry.get("path")
        child_count = entry.get("child_count")
        remediation_issue = entry.get("remediation_issue")
        if (
            not isinstance(entry_path, str)
            or not entry_path.startswith(f"{SOURCE_ROOT}/")
            or "\\" in entry_path
            or ".." in entry_path.split("/")
        ):
            raise _baseline_error(path, examined_count, "an entry path is invalid")
        if not isinstance(child_count, int) or child_count <= MAX_CHILDREN:
            raise _baseline_error(path, examined_count, "an entry child count is invalid")
        if not isinstance(remediation_issue, int) or remediation_issue <= 0:
            raise _baseline_error(path, examined_count, "an entry remediation issue is invalid")
        if entry_path in violations:
            raise _baseline_error(path, examined_count, "an entry path is duplicated")
        entry_paths.append(entry_path)
        violations[entry_path] = BaselineViolation(child_count, remediation_issue)
    if entry_paths != sorted(entry_paths):
        raise _baseline_error(path, examined_count, "entries are not sorted by path")
    return violations


def tracked_python_paths(repository_root: Path) -> list[str]:
    """Return tracked Python paths below src."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "src/**/*.py"],
            cwd=repository_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise AssertionError(f"Cannot read tracked Python paths. Examined 0 directories: {error}") from error
    paths = [value.decode("utf-8") for value in result.stdout.split(b"\0") if value]
    if not paths:
        raise AssertionError("Cannot read tracked Python paths. Examined 0 directories.")
    return sorted(paths)


def measure_direct_children(paths: list[str]) -> dict[str, int]:
    """Count direct Python modules and child directories for each source directory."""
    children: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        parts = path.split("/")
        for index in range(1, len(parts) - 1):
            children["/".join(parts[:index])].add(parts[index])
        children["/".join(parts[:-1])].add(parts[-1])
    return {directory: _child_count(names) for directory, names in children.items() if directory != SOURCE_ROOT}


def _child_count(names: set[str]) -> int:
    """Count direct modules and child directories without using package markers."""
    modules = sum(name.endswith(".py") and name != "__init__.py" for name in names)
    directories = sum(not name.endswith(".py") for name in names)
    return modules + directories


def measure_repository(repository_root: Path) -> dict[str, int]:
    """Measure all source directories with tracked Python descendants."""
    return measure_direct_children(tracked_python_paths(repository_root))


def validate_ratchet(
    actual: dict[str, int],
    baseline: dict[str, BaselineViolation],
) -> None:
    """Reject unknown, increased, stale, and excess nested package findings."""
    actual_violations = {path: count for path, count in actual.items() if count > MAX_CHILDREN}
    messages: list[str] = []
    unknown = sorted(set(actual_violations) - set(baseline))
    stale = sorted(set(baseline) - set(actual_violations))
    if unknown:
        messages.append(f"Unknown violations: {unknown}")
    if stale:
        messages.append(f"Stale baseline entries: {stale}")
    for path in sorted(set(actual_violations) & set(baseline)):
        expected = baseline[path].child_count
        measured = actual_violations[path]
        if measured > expected:
            messages.append(f"Increased child count: {path} {expected} -> {measured}")
    for path, count in sorted(actual.items()):
        if path in baseline and count <= MAX_CHILDREN:
            messages.append(f"Stale baseline entry reached five children: {path}")
    actual_excess = sum(count - MAX_CHILDREN for count in actual_violations.values())
    baseline_excess = sum(max(0, violation.child_count - MAX_CHILDREN) for violation in baseline.values())
    if actual_excess > baseline_excess:
        messages.append(f"Total excess increased: {baseline_excess} -> {actual_excess}")
    assert not messages, "\n".join(messages)


def report_measurement(actual: dict[str, int]) -> str:
    """Report the measured source directory counts."""
    violations = {path: count for path, count in actual.items() if count > MAX_CHILDREN}
    total_excess = sum(count - MAX_CHILDREN for count in violations.values())
    message = (
        f"nested_package_scope: {len(actual)} directories examined, "
        f"{len(violations)} violations, {total_excess} total excess"
    )
    print(message)
    return message


def test_nested_package_ratchet_matches_main() -> None:
    """Keep the baseline aligned with the current tracked source tree."""
    actual = measure_repository(REPOSITORY_ROOT)
    baseline = load_baseline(BASELINE_PATH, examined_count=len(actual))
    message = report_measurement(actual)
    validate_ratchet(actual, baseline)
    assert message == "nested_package_scope: 170 directories examined, 36 violations, 243 total excess"


def test_new_sixth_child_fails() -> None:
    """Reject a new sixth structural child."""
    with pytest.raises(AssertionError, match="Unknown violations"):
        validate_ratchet({"src/example": 6}, {})


def test_increased_grandfathered_count_fails() -> None:
    """Reject an increased count for a baseline path."""
    baseline = {"src/example": BaselineViolation(6, 3824)}
    with pytest.raises(AssertionError, match="Increased child count"):
        validate_ratchet({"src/example": 7}, baseline)


def test_unknown_violation_fails() -> None:
    """Reject a violation absent from the baseline."""
    baseline = {"src/known": BaselineViolation(6, 3824)}
    with pytest.raises(AssertionError, match="Unknown violations"):
        validate_ratchet({"src/new": 6}, baseline)


def test_missing_baseline_fails(tmp_path: Path) -> None:
    """Reject a missing baseline and report the examined scope."""
    with pytest.raises(AssertionError, match="Examined 166 directories"):
        load_baseline(tmp_path / "missing.json", examined_count=166)


def test_missing_git_input_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Reject a failed Git source query and report the empty scope."""

    def raise_git_error(*_: Any, **__: Any) -> None:
        raise OSError("git is unavailable")

    monkeypatch.setattr(subprocess, "run", raise_git_error)
    with pytest.raises(AssertionError, match="Examined 0 directories"):
        tracked_python_paths(tmp_path)


def test_malformed_baseline_fails(tmp_path: Path) -> None:
    """Reject malformed baseline JSON."""
    path = tmp_path / "baseline.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(AssertionError, match="Cannot read nested package baseline"):
        load_baseline(path, examined_count=166)


def test_stale_entry_after_reduction_fails() -> None:
    """Reject a baseline entry after its directory reaches five children."""
    baseline = {"src/example": BaselineViolation(6, 3824)}
    with pytest.raises(AssertionError, match="Stale baseline entry reached five"):
        validate_ratchet({"src/example": 5}, baseline)


def test_total_excess_increase_fails() -> None:
    """Reject a total excess increase."""
    baseline = {
        "src/first": BaselineViolation(6, 3824),
        "src/second": BaselineViolation(6, 3824),
    }
    with pytest.raises(AssertionError, match="Total excess increased"):
        validate_ratchet({"src/first": 7, "src/second": 7}, baseline)
