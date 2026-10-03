"""Keep the measured CI runtime budgets above complete test durations."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"  # Find CI from this test.


def _jobs() -> dict[str, object]:
    """Load the required job definitions from the CI workflow."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))  # Parse the shipped workflow as data.
    return workflow["jobs"]  # Return the job map for focused budget assertions.


def test_the_root_unit_shard_has_a_twenty_minute_budget() -> None:
    """Keep the root-unit budget above its measured 15-minute runtime."""
    shard_job = _jobs()["pytest_coverage_shards"]  # Select the coverage matrix job.
    assert shard_job["timeout-minutes"] == "${{ matrix.timeout_minutes }}"  # Require the per-shard budget.
    rows = shard_job["strategy"]["matrix"]["include"]  # Read each explicit shard definition.
    budgets = {row["shard"]: row["timeout_minutes"] for row in rows}  # Index each budget by shard name.
    assert budgets == {  # Keep only the measured root-unit shard above the standard budget.
        "root-and-contracts": 15,
        "upgrade-contracts": 15,
        "root-units": 20,
        "upgrade-units": 15,
    }


def test_the_browser_job_has_a_twenty_minute_budget() -> None:
    """Keep browser execution and cleanup inside one measured job budget."""
    browser_job = _jobs()["playwright"]  # Select the required browser job.
    assert browser_job["timeout-minutes"] == 20  # Allow the 13-minute suite to complete its cleanup.
