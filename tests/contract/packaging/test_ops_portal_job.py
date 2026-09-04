"""Test the shape of the ops portal job that issue #2257 asked for.

The job held one 10 minute budget for four steps, and no step had a budget of
its own. The audit step reaches a remote service that this repository does not
own, and that service consumed the whole budget twice. Both runs reported a
failure that graded no code, because the three later steps never ran.

Two rules close that gap. Every step that reaches the network carries its own
budget, and the three steps that read the code run before the audit.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflow that holds the job under test.
_WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"

# The three steps that read the code. Each one needs no network, so a registry
# outage must never hide the result of any of them.
_CODE_STEPS = ("Type check", "Lint", "Unit tests")

# The step that reaches the npm advisory service.
_AUDIT_STEP = "Audit the npm dependency tree"

# The step that reaches the npm registry.
_INSTALL_STEP = "Install from the lockfile"


@pytest.fixture(name="ops_portal_job", scope="module")
def fixture_ops_portal_job() -> dict[str, Any]:
    """Read the ops portal job out of the workflow file."""
    logging.info("Reading the ops portal job from %s", _WORKFLOW)  # Report the read before the work.
    document = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    job = document["jobs"]["ops_portal"]
    logging.debug("The job holds %d steps", len(job["steps"]))  # Record the shape after the read.
    return dict(job)


def _named_steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every step of the job that carries a name."""
    return [step for step in job["steps"] if step.get("name")]


def _step_order(job: dict[str, Any]) -> list[str]:
    """Return the names of the job steps, in the order they run."""
    return [str(step["name"]) for step in _named_steps(job)]


@pytest.mark.parametrize("name", (*_CODE_STEPS, _AUDIT_STEP, _INSTALL_STEP))
def test_every_step_carries_its_own_budget(ops_portal_job: dict[str, Any], name: str) -> None:
    """Each step MUST carry a budget, so one slow step never consumes the job.

    Why:
        A step with no budget can use the whole job budget. The steps that
        follow it then never run, and the job reports a failure that graded no
        code.
    """
    logging.info("Checking the budget of the step %s", name)  # Report the plan.
    budgets = {str(step["name"]): step.get("timeout-minutes") for step in _named_steps(ops_portal_job)}

    assert budgets.get(name), f"the step {name!r} must carry its own timeout-minutes"


@pytest.mark.parametrize("name", _CODE_STEPS)
def test_every_code_step_runs_before_the_audit(ops_portal_job: dict[str, Any], name: str) -> None:
    """Each code step MUST run before the audit, which needs a remote service.

    Why:
        The type check, the lint, and the unit tests read the code and reach no
        network. An outage of the advisory service must not hide their result.
    """
    logging.info("Checking that %s runs before the audit", name)  # Report the plan.
    order = _step_order(ops_portal_job)

    assert order.index(name) < order.index(_AUDIT_STEP), f"{name} must run before the audit"


def test_the_job_budget_exceeds_the_sum_of_the_step_budgets(ops_portal_job: dict[str, Any]) -> None:
    """The job budget MUST exceed the sum of the step budgets.

    Why:
        A step timeout names the step that ran long. A job timeout reports
        `cancelled` with no cause, and that is what made the first report of
        issue #2257 hard to read.
    """
    logging.info("Checking the job budget against the step budgets")  # Report the plan.
    steps = sum(int(step.get("timeout-minutes", 0)) for step in _named_steps(ops_portal_job))
    job = int(ops_portal_job["timeout-minutes"])
    logging.debug("The steps ask for %d minutes and the job allows %d", steps, job)  # Record both.

    assert job > steps, f"the job budget {job} must exceed the step total {steps}"


def test_the_audit_retries_an_unreachable_endpoint(ops_portal_job: dict[str, Any]) -> None:
    """The audit MUST retry once, because a brief outage is not an advisory.

    Why:
        The advisory service answered `Service Unavailable` on one run. One
        retry after a short pause clears a brief outage, and a longer outage
        then fails this step alone.
    """
    logging.info("Checking the retry of the audit step")  # Report the plan before the work.
    audit = next(step for step in _named_steps(ops_portal_job) if step["name"] == _AUDIT_STEP)
    body = str(audit["run"])

    assert "while [" in body, "the audit must retry an unreachable endpoint"
    assert "attempt" in body, "the retry must count its attempts"
    assert "sleep" in body, "the retry must pause before the second attempt"


def test_the_audit_still_fails_on_a_real_advisory(ops_portal_job: dict[str, Any]) -> None:
    """A real advisory MUST still fail the step, because the audit is a gate.

    Why:
        A retry that swallowed an advisory would turn the one security check of
        this job into no check at all.
    """
    logging.info("Checking that the audit still fails on an advisory")  # Report the plan.
    audit = next(step for step in _named_steps(ops_portal_job) if step["name"] == _AUDIT_STEP)
    body = str(audit["run"])

    assert "--audit-level=high" in body, "the audit must keep its severity threshold"
    # WHY: the retry path tests for an error body, so an advisory takes the exit path instead.
    assert "exit 1" in body, "an advisory must fail the step"
