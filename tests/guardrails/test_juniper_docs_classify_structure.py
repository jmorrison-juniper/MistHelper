"""Guard the direct-child limit for the Juniper documentation classifier."""  # State the package structure contract.

from __future__ import annotations  # Use current annotation behavior in the guard.

from pathlib import Path  # Resolve the repository and temporary package layouts.

import pytest  # Prove that each invalid package layout fails closed.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the active worktree from this guard file.
CLASSIFY_ROOT = REPOSITORY_ROOT / "src/mist/intelligence/juniper_docs/classify"  # Target the live package.
EXPECTED_CHILDREN = {  # Define the approved five-child layout.
    "asset_classifier.py",
    "content_sampler.py",
    "reprocessing",
    "signal_scorer.py",
    "slug_classifier.py",
}
REPROCESSING_MODULES = {  # Require both moved modules in their canonical package.
    "manual_sorter.py",
    "reclassifier.py",
}
MAX_CHILDREN = 5  # Enforce the repository hierarchy limit.


def visible_children(directory: Path) -> list[Path]:
    """Return direct package children without Python package metadata."""
    if not directory.is_dir():  # Fail when the target package cannot be measured.
        raise AssertionError(f"Missing classify package root: {directory}. Checked 0 children.")
    return [  # Exclude package metadata from the structural child count.
        child for child in directory.iterdir() if child.name not in {"__init__.py", "__pycache__"}
    ]


def validate_child_limit(directory: Path) -> list[Path]:
    """Return children when the package has no more than five structural children."""
    children = visible_children(directory)  # Measure the supplied package layout.
    if len(children) > MAX_CHILDREN:  # Reject a hierarchy that exceeds the project limit.
        raise AssertionError(
            f"Checked {len(children)} classify children. "
            f"Maximum is {MAX_CHILDREN}: {sorted(child.name for child in children)}"
        )
    return children  # Supply the measured children for exact-layout assertions.


def validate_reprocessing_modules(directory: Path) -> None:
    """Require both moved modules under the reprocessing package."""
    reprocessing_root = directory / "reprocessing"  # Resolve the canonical moved-module package.
    if not reprocessing_root.is_dir():  # Fail when the canonical package is absent.
        raise AssertionError(f"Missing reprocessing package: {reprocessing_root}.")
    missing = sorted(  # Measure each required module before reporting a failure.
        module_name for module_name in REPROCESSING_MODULES if not (reprocessing_root / module_name).is_file()
    )
    if missing:  # Reject a partial move that loses a canonical module.
        raise AssertionError(f"Missing reprocessing modules: {missing}.")


def test_classify_has_expected_children_and_measured_count() -> None:
    """Require the classify package to hold the approved five-child layout."""
    children = validate_child_limit(CLASSIFY_ROOT)  # Measure the live classification package.
    child_names = {child.name for child in children}  # Compare stable names instead of path objects.
    assert len(children) == 5, f"Checked {len(children)} classify children: {sorted(child_names)}"  # Report the count.
    assert child_names == EXPECTED_CHILDREN, f"Checked children: {sorted(child_names)}"  # Reject layout drift.
    validate_reprocessing_modules(CLASSIFY_ROOT)  # Require both canonical moved modules.


def test_classify_child_limit_rejects_a_controlled_sixth_child(tmp_path: Path) -> None:
    """Prove that a sixth structural child fails the package guard."""
    package_root = tmp_path / "classify"  # Isolate the controlled invalid package.
    package_root.mkdir()  # Create the package root for the direct failure proof.
    for child_name in EXPECTED_CHILDREN:  # Reproduce the approved five-child layout.
        child = package_root / child_name  # Resolve each expected child in the fixture.
        child.mkdir() if child.suffix == "" else child.touch()  # Create a package or module by its shape.
    (package_root / "sixth.py").touch()  # Add one forbidden direct child.

    with pytest.raises(AssertionError, match=r"Checked 6 classify children"):  # Require the measured count.
        validate_child_limit(package_root)  # Exercise the invalid hierarchy directly.


def test_classify_child_limit_rejects_a_missing_root(tmp_path: Path) -> None:
    """Prove that a missing classify package root fails closed."""
    with pytest.raises(AssertionError, match=r"Missing classify package root"):  # Require a fail-closed message.
        validate_child_limit(tmp_path / "missing-classify")  # Exercise an absent root directly.


def test_classify_structure_rejects_a_missing_reprocessing_module(tmp_path: Path) -> None:
    """Prove that a missing moved module fails closed."""
    package_root = tmp_path / "classify"  # Isolate the partial-move fixture.
    (package_root / "reprocessing").mkdir(parents=True)  # Create only the canonical package.
    (package_root / "reprocessing" / "manual_sorter.py").touch()  # Leave reclassifier absent on purpose.

    with pytest.raises(AssertionError, match=r"Missing reprocessing modules"):  # Require the missing-module report.
        validate_reprocessing_modules(package_root)  # Exercise the incomplete package directly.
