"""Guard the migration-aware structure of the specs process folder."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from misthelper_devtools.speckit_task_audit import TaskFileScanner

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPECS_ROOT = REPOSITORY_ROOT / "specs"
BASELINE_PATH = Path(__file__).with_name("process_folder_baseline.json")
APPROVED_MANAGED_ROOTS = frozenset({"indexes", "live", "numbered", "skills"})


class ManagedSpecTree:
    """Measure structural groups without treating established artifacts as features."""

    def __init__(self) -> None:
        self.directories = 0
        self.records = 0
        self.identities: set[str] = set()

    def visit(self, directory: Path, depth: int = 0) -> None:
        """Reject overflow, unsafe entries, and unsupported group boundaries."""
        self.directories += 1
        if directory.is_symlink():
            raise AssertionError(f"Unsafe structural root: {directory}.")
        children = list(directory.iterdir())
        if len(children) > 5:
            raise AssertionError(f"Managed group exceeds five children: {directory}: {len(children)}.")
        width = 17 if "live" in directory.parts else 8
        for child in children:
            if child.is_symlink() or not child.is_dir():
                raise AssertionError(f"Unsafe structural entry: {child}.")
            if (child / "spec.md").is_file():
                self.record(child, depth, width)
            elif depth < width and re.fullmatch("[0-4]", child.name):
                self.visit(child, depth + 1)
            else:
                raise AssertionError(f"Invalid structural group: {child}.")

    def record(self, directory: Path, depth: int, width: int) -> None:
        """Preserve artifact content while rejecting features beneath a feature."""
        self.records += 1
        if directory.name in self.identities:
            raise AssertionError(f"Duplicate feature identity: {directory.name}.")
        self.identities.add(directory.name)
        direct_timestamp = width == 17 and depth == 0 and re.match(r"^\d{8}-\d{6}-", directory.name)
        if depth != width and not direct_timestamp:
            raise AssertionError(f"Invalid feature route: {directory}.")
        for child in directory.rglob("*"):
            if child.is_symlink():
                raise AssertionError(f"Unsafe feature artifact: {child}.")
            if child.name == "spec.md" and child.parent != directory:
                raise AssertionError(f"Rejected nested feature: {child.parent}.")

    def validate(self, roots: dict[str, Path]) -> str:
        """Report traversal counts even when a structural entry cannot be read."""
        try:
            for name in ("live", "numbered"):
                if name in roots:
                    self.visit(roots[name])
        except (AssertionError, OSError) as error:
            raise AssertionError(
                f"{error} Examined {self.directories} structural directories and {self.records} feature records."
            ) from error
        return f"{self.directories} structural directories, {self.records} feature records"


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
    structural_counts = ManagedSpecTree().validate(children)
    message = (
        f"process_folder_scope: {len(actual_names)} children examined, "
        f"{len(legacy)} legacy grandfathered, {len(managed_present)} managed roots, "
        f"{structural_counts}"
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


@pytest.mark.parametrize("depth", [0, 1, 17])
def test_six_children_fail_at_each_structural_depth(tmp_path: Path, depth: int) -> None:
    """Reject overflow below the root as well as at the root."""
    root = tmp_path / "specs"
    (root / "legacy-feature").mkdir(parents=True)
    parent = root / "live"
    for _ in range(depth):
        parent /= "0"
    parent.mkdir(parents=True)
    for number in range(6):
        (parent / str(number)).mkdir()
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {"managed_roots": sorted(APPROVED_MANAGED_ROOTS), "grandfathered_legacy_children": ["legacy-feature"]}
        )
    )
    with pytest.raises(AssertionError, match="five children"):
        validate_specs_structure(root, baseline)


def test_grouped_timestamp_record_is_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a full timestamp route without treating its groups as features."""
    root = tmp_path / "specs"
    (root / "legacy-feature").mkdir(parents=True)
    feature = root / "live"
    for _ in range(17):
        feature /= "0"
    feature /= "19700101-000000-first"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("**Status**: Specified\n")
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T001 Required grouped work\n")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {"managed_roots": sorted(APPROVED_MANAGED_ROOTS), "grandfathered_legacy_children": ["legacy-feature"]}
        )
    )
    validate_specs_structure(root, baseline)
    assert "1 feature records" in capsys.readouterr().out
    counts = TaskFileScanner().scan(tasks)
    assert (counts.checked, counts.unchecked, counts.malformed) == (0, 1, 0)
    tasks.write_text("- [x] T001 Required grouped work\n")
    counts = TaskFileScanner().scan(tasks)
    assert (counts.checked, counts.unchecked, counts.malformed) == (1, 0, 0)


def test_feature_nested_under_feature_fails(tmp_path: Path) -> None:
    """Reject a feature parent even when the child count is below five."""
    root = tmp_path / "specs"
    (root / "legacy-feature").mkdir(parents=True)
    feature = root / "live" / "20261013-182828-parent"
    nested = feature / "design" / "20261014-050510-child"
    nested.mkdir(parents=True)
    (feature / "spec.md").write_text("# Parent\n")
    (nested / "spec.md").write_text("# Child\n")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {"managed_roots": sorted(APPROVED_MANAGED_ROOTS), "grandfathered_legacy_children": ["legacy-feature"]}
        )
    )
    with pytest.raises(AssertionError, match="nested feature"):
        validate_specs_structure(root, baseline)


def test_duplicate_feature_identity_fails_across_groups(tmp_path: Path) -> None:
    """Reject one feature name that appears in two timestamp routes."""
    root = tmp_path / "specs"
    (root / "legacy-feature").mkdir(parents=True)
    identity = "20261013-182828-duplicate"
    direct = root / "live" / identity
    grouped = root / "live"
    for _ in range(17):
        grouped /= "0"
    grouped /= identity
    direct.mkdir(parents=True)
    grouped.mkdir(parents=True)
    (direct / "spec.md").write_text("# Direct record\n", encoding="utf-8")
    (grouped / "spec.md").write_text("# Grouped record\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {"managed_roots": sorted(APPROVED_MANAGED_ROOTS), "grandfathered_legacy_children": ["legacy-feature"]}
        ),
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="Duplicate feature identity"):
        validate_specs_structure(root, baseline)
