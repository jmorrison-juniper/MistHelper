"""Guard the direct-child limit for the Juniper documentation classifier."""

from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLASSIFY_ROOT = REPOSITORY_ROOT / "src/mist/intelligence/juniper_docs/classify"
EXPECTED_CHILDREN = {
    "asset_classifier.py",
    "content_sampler.py",
    "reprocessing",
    "signal_scorer.py",
    "slug_classifier.py",
}
REPROCESSING_MODULES = {
    "manual_sorter.py",
    "reclassifier.py",
}
MAX_CHILDREN = 5


def visible_children(directory: Path) -> list[Path]:
    """Return direct package children without Python package metadata."""
    if not directory.is_dir():
        raise AssertionError(f"Missing classify package root: {directory}. Checked 0 children.")
    return [child for child in directory.iterdir() if child.name not in {"__init__.py", "__pycache__"}]


def validate_child_limit(directory: Path) -> list[Path]:
    """Return children when the package has no more than five structural children."""
    children = visible_children(directory)
    if len(children) > MAX_CHILDREN:
        raise AssertionError(
            f"Checked {len(children)} classify children. "
            f"Maximum is {MAX_CHILDREN}: {sorted(child.name for child in children)}"
        )
    return children


def validate_reprocessing_modules(directory: Path) -> None:
    """Require both moved modules under the reprocessing package."""
    reprocessing_root = directory / "reprocessing"
    if not reprocessing_root.is_dir():
        raise AssertionError(f"Missing reprocessing package: {reprocessing_root}.")
    missing = sorted(
        module_name for module_name in REPROCESSING_MODULES if not (reprocessing_root / module_name).is_file()
    )
    if missing:
        raise AssertionError(f"Missing reprocessing modules: {missing}.")


def test_classify_has_expected_children_and_measured_count() -> None:
    """Require the classify package to hold the approved five-child layout."""
    children = validate_child_limit(CLASSIFY_ROOT)
    child_names = {child.name for child in children}
    assert len(children) == 5, f"Checked {len(children)} classify children: {sorted(child_names)}"
    assert child_names == EXPECTED_CHILDREN, f"Checked children: {sorted(child_names)}"
    validate_reprocessing_modules(CLASSIFY_ROOT)


def test_classify_child_limit_rejects_a_controlled_sixth_child(tmp_path: Path) -> None:
    """Prove that a sixth structural child fails the package guard."""
    package_root = tmp_path / "classify"
    package_root.mkdir()
    for child_name in EXPECTED_CHILDREN:
        child = package_root / child_name
        child.mkdir() if child.suffix == "" else child.touch()
    (package_root / "sixth.py").touch()

    with pytest.raises(AssertionError, match=r"Checked 6 classify children"):
        validate_child_limit(package_root)


def test_classify_child_limit_rejects_a_missing_root(tmp_path: Path) -> None:
    """Prove that a missing classify package root fails closed."""
    with pytest.raises(AssertionError, match=r"Missing classify package root"):
        validate_child_limit(tmp_path / "missing-classify")


def test_classify_structure_rejects_a_missing_reprocessing_module(tmp_path: Path) -> None:
    """Prove that a missing moved module fails closed."""
    package_root = tmp_path / "classify"
    (package_root / "reprocessing").mkdir(parents=True)
    (package_root / "reprocessing" / "manual_sorter.py").touch()

    with pytest.raises(AssertionError, match=r"Missing reprocessing modules"):
        validate_reprocessing_modules(package_root)
