"""Guard tests for the single RRM_DRY_RUN policy resolver."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

from pathlib import Path  # WHY: guard paths must work on each supported platform.

from scripts.rrm_dry_run_read_guard import ALLOWED_PATH, RrmDryRunReadGuard

ROOT = Path(__file__).resolve().parents[2]  # WHY: tests scan the active repository worktree.
FIXTURE = Path("tests/fixtures/rrm_dry_run_read_guard/unauthorized_reader.py")  # WHY: prove bypass rejection.


def test_tracked_product_files_have_one_authorized_read(capsys: object) -> None:
    """The tracked product tree must contain one policy-owned read site."""
    del capsys  # WHY: pytest injects this fixture to keep the test signature compatible with guard conventions.
    paths = RrmDryRunReadGuard.tracked_python_files(ROOT)  # WHY: exercise the same tracked file selection as CI.
    result = RrmDryRunReadGuard.scan_paths(ROOT, paths)  # WHY: scan the live product tree.
    print(
        f"Scanned {result.file_count} tracked non-test Python files. "
        f"Found {len(result.read_sites)} RRM_DRY_RUN read sites."
    )  # WHY: the test output reports the examined scope.
    assert len(result.read_sites) == 1, "the product tree must contain one RRM_DRY_RUN read"
    assert result.read_sites[0][0] == ALLOWED_PATH, "only the policy resolver may read RRM_DRY_RUN"
    assert RrmDryRunReadGuard.validate(result) == (), "the live tracked tree must pass the guard"


def test_negative_fixture_fails_for_an_outside_read(capsys: object) -> None:
    """A fixture outside the policy resolver must produce a guard failure."""
    del capsys  # WHY: keep pytest output capture available for a verbose proof run.
    result = RrmDryRunReadGuard.scan_paths(ROOT, (ALLOWED_PATH, FIXTURE))  # WHY: add one deliberate bypass.
    failures = RrmDryRunReadGuard.validate(result)  # WHY: use the production validator for the proof.
    print(
        f"Scanned {result.file_count} tracked non-test Python files. "
        f"Found {len(result.read_sites)} RRM_DRY_RUN read sites."
    )  # WHY: the negative proof uses the required stable output shape.
    assert len(failures) == 1, "the fixture must create one guard failure"
    assert "unauthorized_reader.py" in failures[0], "the failure must identify the bypass fixture"
