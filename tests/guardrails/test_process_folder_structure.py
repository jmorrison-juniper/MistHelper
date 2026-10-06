"""Guard the migration-aware structure of the specs process folder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPECS_ROOT = REPOSITORY_ROOT / "specs"
BASELINE_PATH = Path(__file__).with_name("process_folder_baseline.json")
APPROVED_MANAGED_ROOTS = frozenset({"indexes", "live", "numbered", "skills"})


def load_baseline(baseline_path: Path, examined_count: int = 0) -> tuple[set[str], set[str]]:
    """Read the nonempty legacy manifest and its managed roots."""
    count_message = f" Examined {examined_count} specs children before failure."
    if not baseline_path.is_file():
        raise AssertionError(f"Cannot read specs baseline: {baseline_path}.{count_message}")
    try:
        payload: Any = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"Cannot read specs baseline: {baseline_path}: {error}.{count_message}") from error
    if not isinstance(payload, dict):
        raise AssertionError(f"Specs baseline must contain a JSON object.{count_message}")
    legacy = payload.get("grandfathered_legacy_children")
    managed = payload.get("managed_roots")
    if not isinstance(legacy, list) or not legacy or not all(isinstance(item, str) for item in legacy):
        raise AssertionError(f"Specs baseline must contain a nonempty legacy list.{count_message}")
    if len(legacy) != len(set(legacy)):
        raise AssertionError(f"Specs baseline contains duplicate legacy entries.{count_message}")
    if not isinstance(managed, list) or set(managed) != APPROVED_MANAGED_ROOTS:
        raise AssertionError(f"Specs baseline managed roots do not match the approved set.{count_message}")
    return set(legacy), set(managed)


def read_specs_children(specs_root: Path) -> dict[str, Path]:
    """Read direct specs children before validating the migration baseline."""
    if not specs_root.is_dir():
        raise AssertionError(f"Cannot read specs root: {specs_root}. Examined 0 children.")
    try:
        return {child.name: child for child in specs_root.iterdir()}
    except OSError as error:
        raise AssertionError(f"Cannot read specs root: {specs_root}: {error}. Examined 0 children.") from error


def validate_specs_structure(specs_root: Path, baseline_path: Path) -> str:
    """Validate the current direct children against the migration baseline."""
    children = read_specs_children(specs_root)
    legacy, managed = load_baseline(baseline_path, examined_count=len(children))
    actual_names = set(children)
    unexpected = actual_names - legacy - managed
    missing = legacy - actual_names
    if unexpected or missing:
        raise AssertionError(f"Specs intake violation. Unexpected: {sorted(unexpected)}. Missing: {sorted(missing)}.")
    managed_present = sorted(actual_names & managed)
    non_directories = [name for name in managed_present if not children[name].is_dir()]
    if non_directories:
        raise AssertionError(f"Managed specs roots must be directories: {non_directories}")
    level_counts = {name: len([child for child in children[name].iterdir()]) for name in managed_present}
    violations = {name: count for name, count in level_counts.items() if count > 5}
    if violations:
        raise AssertionError(f"Managed specs roots exceed five children: {violations}")
    message = (
        f"process_folder_scope: {len(actual_names)} children examined, "
        f"{len(legacy)} legacy grandfathered, {len(managed_present)} managed roots"
    )
    print(message)
    return message


def test_specs_structure_matches_baseline() -> None:
    """Keep current legacy entries while rejecting new flat intake."""
    message = validate_specs_structure(SPECS_ROOT, BASELINE_PATH)
    assert "792 legacy grandfathered" in message


def test_no_new_root_level_feature(tmp_path: Path) -> None:
    """Reject a direct feature entry that is absent from the baseline."""
    specs_root = tmp_path / "specs"
    specs_root.mkdir()
    (specs_root / "legacy-feature").mkdir()
    (specs_root / "live").mkdir()
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "version": 1,
                "managed_roots": sorted(APPROVED_MANAGED_ROOTS),
                "grandfathered_legacy_children": ["legacy-feature"],
            }
        ),
        encoding="utf-8",
    )
    (specs_root / "999-new-feature").mkdir()
    with pytest.raises(AssertionError, match="Unexpected"):
        validate_specs_structure(specs_root, baseline)


def test_unreadable_baseline_fails(tmp_path: Path) -> None:
    """Fail when the baseline cannot be read."""
    specs_root = tmp_path / "specs"
    specs_root.mkdir()
    (specs_root / "legacy-feature").mkdir()
    with pytest.raises(AssertionError, match=r"Cannot read specs baseline.*Examined 1 specs children"):
        validate_specs_structure(specs_root, tmp_path / "missing.json")


def test_malformed_baseline_fails(tmp_path: Path) -> None:
    """Fail when the baseline is not valid JSON."""
    specs_root = tmp_path / "specs"
    specs_root.mkdir()
    (specs_root / "legacy-feature").mkdir()
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{", encoding="utf-8")
    with pytest.raises(AssertionError, match=r"Cannot read specs baseline.*Examined 1 specs children"):
        validate_specs_structure(specs_root, baseline)


def test_examined_counts_are_reported(capsys: pytest.CaptureFixture[str]) -> None:
    """Report the measured child and managed-root counts."""
    validate_specs_structure(SPECS_ROOT, BASELINE_PATH)
    assert "children examined" in capsys.readouterr().out
