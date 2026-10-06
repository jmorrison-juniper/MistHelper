"""Prove that the bootstrap sweep removes only the orphaned source directories.

A branch switch leaves a package directory behind when a commit moves or deletes
that package. Git does not track an empty directory, so the old name stays on
disk. Ruff then reads the leftover name as a first-party package and sorts an
import into the wrong block. The pipeline never reports the finding, because the
pipeline checks out a clean tree. See issue #3846.

These tests prove the two hard limits of the sweep. The sweep keeps the cache
directory of the source root, and the sweep keeps every directory that holds a
file outside a cache directory.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from scripts.bootstrap_worktree import StaleSourceSweeper

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_source_root(root: Path) -> Path:
    """Create the source root inside a temporary worktree and return it."""
    source_root = root / StaleSourceSweeper.SOURCE_NAME  # Build the path from the class constant, not a literal.
    source_root.mkdir()  # Create the root, because every sweep reads it first.
    logger.info("Created the temporary source root at %s", source_root)
    return source_root  # Give the caller the root it populates.


def build_sweeper(root: Path, tracked: set[str] | None) -> StaleSourceSweeper:
    """Return a sweeper whose tracked-name read answers with a fixed result."""
    sweeper = StaleSourceSweeper(root)  # Build the real object, because the sweep logic is under test.
    sweeper.read_tracked_names = lambda: tracked  # type: ignore[method-assign]
    logger.info("Prepared a sweeper with %s tracked names", "unknown" if tracked is None else len(tracked))
    return sweeper  # Give the caller a sweeper that needs no git repository.


# ---------------------------------------------------------------------------
# The removal cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cached", [False, True])
def test_the_sweep_removes_an_untracked_directory(tmp_path: Path, cached: bool) -> None:
    """The sweep MUST remove an untracked directory that holds no file outside a cache."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    orphan = source_root / "leftover"  # Name the directory that a branch switch left behind.
    orphan.mkdir()  # Create the orphaned directory.
    if cached:  # Prove both the empty case and the cache-only case.
        cache = orphan / StaleSourceSweeper.CACHE_NAME  # Build the cache path from the class constant.
        cache.mkdir()  # Create the cache directory inside the orphan.
        (cache / "module.pyc").write_text("", encoding="utf-8")  # Add the cached byte code the sweep ignores.
    logger.info("Running the sweep against %s", source_root)
    removed = build_sweeper(tmp_path, set()).sweep()  # Run the sweep with no tracked name at all.

    # WHY: the operator reads the removed names, so the sweep must report them.
    assert removed == ["leftover"], f"The sweep reported {removed} instead of the orphaned name."
    # WHY: a reported removal that leaves the directory on disk would not repair the ruff finding.
    assert not orphan.exists(), "The sweep reported the removal but left the directory on disk."


# ---------------------------------------------------------------------------
# The protection cases
# ---------------------------------------------------------------------------


def test_the_sweep_keeps_a_directory_that_holds_a_real_file(tmp_path: Path) -> None:
    """The sweep MUST keep an untracked directory that holds a file outside a cache."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    work = source_root / "uncommitted"  # Name the directory that holds work no commit records yet.
    work.mkdir()  # Create the directory.
    (work / "module.py").write_text("value = 1\n", encoding="utf-8")  # Add the file that must survive.
    logger.info("Running the sweep against %s", source_root)
    removed = build_sweeper(tmp_path, set()).sweep()  # Run the sweep with no tracked name at all.

    # WHY: a removal here would destroy work that no commit holds.
    assert removed == [], f"The sweep removed {removed} although the directory holds a real file."
    # WHY: the file itself proves the directory survived intact.
    assert (work / "module.py").exists(), "The sweep deleted a file that no commit holds."


def test_the_sweep_keeps_the_cache_directory_of_the_source_root(tmp_path: Path) -> None:
    """The sweep MUST keep the cache directory that sits directly inside the source root."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    cache = source_root / StaleSourceSweeper.CACHE_NAME  # Build the cache path from the class constant.
    cache.mkdir()  # Create the cache directory of the source root.
    logger.info("Running the sweep against %s", source_root)
    removed = build_sweeper(tmp_path, set()).sweep()  # Run the sweep with no tracked name at all.

    # WHY: issue #3846 states the sweep must keep this directory.
    assert removed == [], f"The sweep removed {removed} although only the cache directory exists."
    # WHY: the directory itself proves the rule held.
    assert cache.is_dir(), "The sweep removed the cache directory of the source root."


def test_the_sweep_keeps_a_tracked_directory(tmp_path: Path) -> None:
    """The sweep MUST keep a directory that git tracks, even when the worktree copy is empty."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    tracked = source_root / "committed"  # Name the directory that a commit records.
    tracked.mkdir()  # Create the tracked directory with no file inside it.
    logger.info("Running the sweep against %s", source_root)
    removed = build_sweeper(tmp_path, {"committed"}).sweep()  # Report the name as tracked.

    # WHY: a tracked name holds committed work, so a removal would damage the checkout.
    assert removed == [], f"The sweep removed {removed} although git tracks the name."
    # WHY: the directory itself proves the rule held.
    assert tracked.is_dir(), "The sweep removed a directory that git tracks."


def test_the_sweep_removes_nothing_when_the_tracked_names_are_unknown(tmp_path: Path) -> None:
    """The sweep MUST remove nothing when the tracked-name read cannot answer."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    orphan = source_root / "leftover"  # Name a directory that the sweep would otherwise remove.
    orphan.mkdir()  # Create the empty directory.
    logger.info("Running the sweep with an unknown tracked-name answer")
    removed = build_sweeper(tmp_path, None).sweep()  # Report the tracked names as unknown.

    # WHY: a guess could delete committed work, so an unknown answer must stop the sweep.
    assert removed == [], f"The sweep removed {removed} although the tracked names are unknown."
    # WHY: the directory itself proves the rule held.
    assert orphan.is_dir(), "The sweep removed a directory although the tracked names are unknown."


# ---------------------------------------------------------------------------
# The operator report
# ---------------------------------------------------------------------------


def test_the_sweep_reports_the_count_to_the_operator(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """The sweep MUST print the removed count, because the operator reads it."""
    source_root = build_source_root(tmp_path)  # Build the root the sweep reads.
    for name in ("alpha", "beta"):  # Create two orphaned directories, so the count is not one.
        (source_root / name).mkdir()  # Create the empty directory.
    logger.info("Running the sweep and capturing the log records")
    with caplog.at_level(logging.INFO):  # Capture the records the operator sees on the console.
        removed = build_sweeper(tmp_path, set()).sweep()  # Run the sweep with no tracked name at all.

    # WHY: both names must reach the caller in a stable order.
    assert removed == ["alpha", "beta"], f"The sweep reported {removed} instead of both orphaned names."
    # WHY: issue #3846 states the operator must see the count.
    assert "removed 2 orphaned source directories" in caplog.text, "The sweep did not report the removed count."
