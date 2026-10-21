"""Guardrails for the events that start the quality gate workflow.

Issue #1952 recorded that `.github/workflows/ci.yml` started on a pull request
that targeted `main` only. A pull request against any other base ran no gate at
all. It reported zero checks and a `CLEAN` merge state, which a reviewer reads
as safe rather than unmeasured.

Pull request #1890 showed the behavior. It reported 0 successful checks and 0
failed checks, while every pull request against `main` reported 17 to 19.

The repair removes the branch filter from the `pull_request` trigger. These
tests hold the repair in place. A change that restores the filter fails a test.

Issue #2204 recorded a second defect in the same file. The workflow declared no
concurrency group, so a second push to a pull request left the older run alive.
Both runs then spent minutes on the same branch, and the older run measured a
tree that no reviewer would read.

Issue #2205 recorded the same branch filter defect in
`.github/workflows/codeql.yml`. CodeQL reports a required check, so a filter
that named `main` alone stopped that check from ever reporting on a stacked
pull request.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because every test below reads the same file.
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Name the CodeQL workflow once, because it reports a required check too.
CODEQL_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codeql.yml"

# PyYAML turns the bare `on` key into the boolean True, so name that key once.
TRIGGER_KEY = True


def _parse(path: Path) -> dict[str, Any]:
    """Parse one workflow file and return the mapping."""
    # Read with an explicit encoding, because the Windows default differs.
    text = path.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # Fail early with a clear message, because a non-mapping breaks each test.
    assert isinstance(parsed, dict), f"The workflow must be a mapping: {path}"

    return parsed


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    """Parse the quality gate workflow and return the mapping."""
    # Read the quality gate workflow, because most tests below inspect it.
    return _parse(CI_WORKFLOW)


@pytest.fixture(scope="module")
def codeql() -> dict[str, Any]:
    """Parse the CodeQL workflow and return the mapping."""
    # Read the CodeQL workflow, because it reports a required check.
    return _parse(CODEQL_WORKFLOW)


class TestPullRequestTrigger:
    """Check the pull request event that starts the quality gates."""

    def test_workflow_file_exists(self) -> None:
        """The workflow file must exist, because every other test reads it."""
        # A missing file means the gates are gone, so state that plainly.
        assert CI_WORKFLOW.is_file(), f"Missing workflow: {CI_WORKFLOW}"

    def test_pull_request_trigger_is_present(self, workflow: dict[str, Any]) -> None:
        """A pull request must start the quality gates."""
        # Without this trigger no pull request is measured at all.
        assert "pull_request" in workflow[TRIGGER_KEY], "A pull request must run CI."

    def test_pull_request_has_no_branch_filter(self, workflow: dict[str, Any]) -> None:
        """Every pull request must run the gates, whatever its base branch."""
        # Read the trigger. A bare key parses to None, which means every branch.
        trigger = workflow[TRIGGER_KEY]["pull_request"]

        # A None trigger is the repaired shape, so accept it and stop here.
        if trigger is None:
            return

        # A mapping with a branch filter is the exact defect that #1952 records.
        assert "branches" not in trigger, (
            "The pull_request trigger must carry no branch filter. "
            "A filter lets a stacked pull request merge with zero checks."
        )

    def test_stacked_base_branch_is_not_excluded(self, workflow: dict[str, Any]) -> None:
        """A pull request against a feature branch must not be filtered out."""
        # Read the trigger, because the check below inspects any surviving filter.
        trigger = workflow[TRIGGER_KEY]["pull_request"]

        # The repaired shape parses to None, so no branch can be excluded.
        if trigger is None:
            return

        # If a filter survives, it must at least admit a feature branch pattern.
        branches = trigger.get("branches", [])

        # A filter of main alone reproduces the defect, so reject that exact case.
        assert branches != ["main"], "A filter of main alone reproduces issue #1952."

    @pytest.mark.parametrize("workflow_name", ["ci.yml", "codeql.yml"])
    @pytest.mark.parametrize("mutation", [None, "missing", "wrong-type", "filtered", "cancel", "group"])
    def test_merge_group_contract(self, workflow_name: str, mutation: str | None) -> None:
        """Reject missing queue events and unsafe candidate concurrency."""
        candidate = _parse(CI_WORKFLOW.with_name(workflow_name))  # Read each required workflow, not a substitute.
        if mutation == "missing":
            candidate[TRIGGER_KEY].pop("merge_group", None)
        elif mutation == "wrong-type":
            candidate[TRIGGER_KEY]["merge_group"] = {"types": ["destroyed"]}
        elif mutation == "filtered":
            candidate[TRIGGER_KEY]["merge_group"] = {"types": ["checks_requested"], "paths": ["src/**"]}
        elif mutation == "cancel":
            candidate["concurrency"]["cancel-in-progress"] = True
        elif mutation == "group":
            candidate["concurrency"]["group"] = "shared-queue-group"
        blockers = CancellableJobAudit.queue_blockers(candidate)  # Apply the same decision to real and mutated inputs.
        print(f"Checked 1 of 2 required workflows: {workflow_name}, mutation={mutation}, blockers={blockers}.")
        assert (blockers == []) is (mutation is None), f"Invalid merge queue contract: {workflow_name}: {blockers}"


class TestPushTrigger:
    """Check the push event, which must stay narrow."""

    def test_push_stays_pinned_to_main(self, workflow: dict[str, Any]) -> None:
        """The push trigger must stay on main, so no branch runs twice."""
        # Read the push trigger, because a wide filter doubles every run.
        push = workflow[TRIGGER_KEY]["push"]

        # A push run on every branch repeats the pull request run and adds cost.
        assert push["branches"] == ["main"], "The push trigger must stay on main."

    @pytest.mark.parametrize(
        "required_check",
        [
            ("ruff", "Ruff (lint)"),
            ("black", "Black (format check)"),
            ("mypy", "mypy (strict)"),
            ("pytest", "pytest (coverage gate)"),
            ("bandit", "Bandit (security)"),
            ("pip_audit", "pip-audit (CVE scan)"),
            ("pylint", "Pylint (score gate)"),
            ("radon", "Radon (complexity)"),
            ("vulture", "Vulture (dead code)"),
            ("pydocstyle", "pydocstyle (docstring style)"),
            ("interrogate", "Interrogate (docstring coverage)"),
            ("diagram_lint", "Diagram reference lint"),
            ("playwright", "E2E smoke tests"),
            ("ops_platform_pytest", "pytest (ops platform)"),
        ],
    )
    @pytest.mark.parametrize("mutation", [None, "missing", "renamed"])
    def test_required_check_names(
        self, workflow: dict[str, Any], required_check: tuple[str, str], mutation: str | None
    ) -> None:
        """Keep every required CI job ID and context name stable."""
        from copy import deepcopy

        job_id, expected_name = required_check  # Pin protection names independently of the YAML under test.
        jobs = deepcopy(workflow["jobs"])  # Keep module-scoped fixtures intact for later tests.
        if mutation == "missing":
            del jobs[job_id]
        elif mutation == "renamed":
            jobs[job_id]["name"] = "renamed-required-check"
        actual_name = jobs.get(job_id, {}).get("name")  # Missing jobs must fail the same comparison as renamed jobs.
        print(f"Checked 1 of 14 required CI contexts: {job_id}={actual_name!r}, mutation={mutation}.")
        assert (actual_name == expected_name) is (mutation is None), f"Required context changed: {job_id}"

    @pytest.mark.parametrize("mutation", [None, "main", "pr-head", "missing-sha"])
    def test_queue_checkout_contract(self, workflow: dict[str, Any], mutation: str | None) -> None:
        """Every CI checkout must retain the merge-group event commit."""
        from copy import deepcopy

        candidate = deepcopy(workflow)  # Prevent one checkout mutation from contaminating another scenario.
        checkout = candidate["jobs"]["test_quality_gate"]["steps"][0]  # This is the only explicit checkout reference.
        if mutation is not None:
            checkout["with"]["ref"] = {
                "main": "main",
                "pr-head": "${{ github.head_ref }}",
                "missing-sha": "${{ github.event.pull_request.head.sha }}",
            }[mutation]
        references = [
            step.get("with", {}).get("ref")
            for job in candidate["jobs"].values()
            for step in job.get("steps", [])
            if step.get("uses", "").startswith("actions/checkout@")
        ]
        blockers = [
            ref for ref in references if ref not in (None, "${{ github.event.pull_request.head.sha || github.sha }}")
        ]
        print(f"Checked {len(references)} CI checkout references, mutation={mutation}, blockers={len(blockers)}.")
        assert len(references) >= 14, "The checkout audit must not accept an empty or incomplete workflow."
        assert (blockers == []) is (mutation is None), f"Queue checkouts must use the candidate commit: {blockers}"

    @pytest.mark.parametrize(
        ("source", "error"),
        [(None, FileNotFoundError), ("on: [", yaml.YAMLError), ("[]", AssertionError)],
    )
    def test_parser_fails_on_unreadable_input(self, tmp_path: Path, source: str | None, error: type[Exception]) -> None:
        """Missing, malformed, and non-mapping workflow inputs must fail."""
        path = tmp_path / "workflow.yml"  # Never replace a real workflow to prove an error decision.
        if source is not None:
            path.write_text(source, encoding="utf-8")
        print(f"Checked 1 invalid workflow input, expected={error.__name__}.")
        with pytest.raises(error):
            _parse(path)


class TestConcurrency:
    """Check the group that cancels a stale quality gate run."""

    def test_workflow_declares_a_concurrency_group(self, workflow: dict[str, Any]) -> None:
        """The workflow must declare a group, so a stale run stops."""
        # Without a group both runs continue, and the older run wastes minutes.
        assert "concurrency" in workflow, "The workflow must declare a concurrency group."

    def test_group_separates_each_pull_request(self, workflow: dict[str, Any]) -> None:
        """The group must name the pull request, so one branch cancels itself."""
        # Read the group name, because the checks below inspect its parts.
        group = workflow["concurrency"]["group"]

        # A group that reads the pull request number keeps each branch separate.
        assert "github.event.pull_request.number" in group, (
            "The group must name the pull request, " "so a push to one branch cancels that branch alone."
        )

        # A fallback to the reference covers a push and a manual start.
        assert "github.ref" in group, "The group must fall back to the reference."

    def test_group_avoids_the_caller_workflow_name(self, workflow: dict[str, Any]) -> None:
        """The group must not read github.workflow, because a caller renames it."""
        # This workflow accepts workflow_call, and then github.workflow reports
        # the name of the caller. The group would then merge with the caller.
        assert "github.workflow" not in workflow["concurrency"]["group"], (
            "The group must use a literal name. " "github.workflow reports the name of the caller."
        )

    def test_a_main_run_is_never_cancelled(self, workflow: dict[str, Any]) -> None:
        """A push to main must finish, because Auto-merge reads its result."""
        # Read the setting, because a bare true would cancel a main run.
        cancel = workflow["concurrency"]["cancel-in-progress"]

        # The condition must limit the cancel to a pull request event.
        assert "pull_request" in str(cancel), (
            "cancel-in-progress must apply to a pull request alone. "
            "A cancelled main run leaves the merged tree unmeasured."
        )

    @pytest.mark.parametrize("mutation", [None, "missing", "if", "uses", "with"])
    def test_restoration_browser_evidence_contract(self, workflow: dict[str, Any], mutation: str | None) -> None:
        """Preserve restoration screenshots after failed tests without retaining cancelled jobs."""
        expected = {
            "name": "Upload backup restoration browser evidence",
            "if": "${{ !cancelled() && matrix.shard == 'web-portal' }}",
            "uses": "actions/upload-artifact@v7",
            "with": {
                "name": "backup-restoration-browser-evidence",
                "path": "test-artifacts/issue4218-*.png",
                "if-no-files-found": "error",
            },
        }
        uploads = [
            step for step in workflow["jobs"]["playwright_shards"]["steps"] if step.get("name") == expected["name"]
        ]
        if mutation == "missing":
            uploads = []
        elif mutation is not None:
            uploads = [{**step, mutation: "invalid"} for step in uploads]
        print(f"Checked 1 restoration artifact contract with {len(uploads)} matching steps.")
        assert (uploads == [expected]) is (mutation is None)


class CancellableJobAudit:
    """Find each job that a cancelled run cannot stop (issue #3926).

    GitHub Actions does not cancel a job whose `if` condition calls `always()`.
    A cancelled run then keeps each such job, and the jobs that wait on it,
    until they finish. On pull request #3898 the older run held the concurrency
    group for 21 minutes, and the newer run waited for it.
    """

    @staticmethod
    def uncancellable_jobs(workflow: dict[str, Any]) -> list[str]:
        """Return the name of each job whose condition calls always()."""
        jobs = workflow.get("jobs", {})  # Read every job, because any one job can hold the group.
        return sorted(name for name, job in jobs.items() if "always()" in str(job.get("if", "")))  # Name each blocker.

    @staticmethod
    def gated_jobs(workflow: dict[str, Any]) -> list[str]:
        """Return the name of each job that runs after a failed dependency."""
        jobs = workflow.get("jobs", {})  # Read every job, because each one needs a cancel-aware condition.
        return sorted(name for name, job in jobs.items() if "!cancelled()" in str(job.get("if", "")))  # Count them.

    @staticmethod
    def queue_blockers(workflow: dict[str, Any]) -> list[str]:
        """Identify event and concurrency settings that block queue validation."""
        concurrency = workflow["concurrency"]  # Missing configuration must fail instead of assuming isolation.
        contracts = {
            "event": workflow[TRIGGER_KEY].get("merge_group") == {"types": ["checks_requested"]},
            "group": "github.event.pull_request.number || github.ref" in concurrency["group"],
            "cancellation": concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}",
        }
        return sorted(name for name, valid in contracts.items() if not valid)  # Give the rejected contract names.


class TestCancelledRunStops:
    """Check that a cancelled quality gate run stops each job (issue #3926)."""

    def test_no_job_survives_a_cancelled_run(self, workflow: dict[str, Any]) -> None:
        """A job that calls always() keeps a cancelled run alive."""
        blockers = CancellableJobAudit.uncancellable_jobs(workflow)  # Find each job that ignores the cancel.
        checked = len(workflow["jobs"])  # Count the jobs, so the report shows the examined scope.
        print(f"Checked {checked} jobs in ci.yml, found {len(blockers)} that ignore a cancel.")  # Report the count.
        assert blockers == [], f"Use !cancelled(), not always(). These jobs ignore a cancel: {blockers}"

    def test_each_gate_after_a_failure_still_runs(self, workflow: dict[str, Any]) -> None:
        """The jobs that ran after a failed gate keep that behavior through !cancelled()."""
        gated = CancellableJobAudit.gated_jobs(workflow)  # Read the jobs that run after a failed dependency.
        # Issue #4250 adds playwright_shards, so the pinned set holds 9 jobs.
        assert len(gated) == 9, f"Expected 9 jobs with !cancelled(), found {len(gated)}: {gated}"  # Pin the set.
        assert "quality_gate_issues" in gated, "The issue job must still run after a failed gate."

    def test_the_audit_rejects_an_always_condition(self) -> None:
        """The direct proof: a synthetic job with always() must fail the audit."""
        synthetic = {"jobs": {"mypy": {"if": "${{ always() }}"}, "ruff": {}}}  # Model the issue #3926 workflow.
        assert CancellableJobAudit.uncancellable_jobs(synthetic) == ["mypy"]  # The audit names the blocker.

    @pytest.mark.parametrize("workflow_name", ["ci.yml", "codeql.yml"])
    def test_event_concurrency_isolation(self, workflow_name: str) -> None:
        """Exercise candidate, main, and pull request grouping without evaluating arbitrary expressions."""
        concurrency = _parse(CI_WORKFLOW.with_name(workflow_name))["concurrency"]  # Read the actual workflow condition.
        expression = "${{ github.event.pull_request.number || github.ref }}"  # Support this bounded expression only.
        assert concurrency["group"].endswith(expression), "Unrecognized group expression cannot prove queue isolation."
        assert concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"
        contexts = [
            ("merge_group", "", "refs/heads/gh-readonly-queue/main/pr-1-first"),
            ("merge_group", "", "refs/heads/gh-readonly-queue/main/pr-2-second"),
            ("push", "", "refs/heads/main"),
            ("pull_request", "1", "refs/pull/1/merge"),
        ]
        groups = [concurrency["group"].replace(expression, number or ref) for _, number, ref in contexts]
        cancellations = [event == "pull_request" for event, _, _ in contexts]  # Evaluate only the pinned comparison.
        print(f"Checked {len(contexts)} event contexts in {workflow_name}, isolated groups={len(set(groups))}.")
        assert len(set(groups)) == 4, "Queue candidates, main, and pull requests must not share a group."
        assert cancellations == [False, False, False, True]


class TestCodeqlTrigger:
    """Check the events that start the CodeQL scan, a required check."""

    def test_codeql_workflow_exists(self, codeql: dict[str, Any]) -> None:
        """The CodeQL workflow must exist, because it reports a required check."""
        # A missing file means no scan reports, and every merge then blocks.
        assert CODEQL_WORKFLOW.is_file(), f"Missing workflow: {CODEQL_WORKFLOW}"
        job = codeql["jobs"]["codeql"]  # Keep the caller identity that code scanning uses for the required context.
        print("Checked 1 CodeQL analysis identity and 1 application-owned required context.")
        assert job["uses"].startswith("jmorrison-juniper/misthelper-devtools/.github/workflows/reusable-codeql.yml@")
        assert job["with"]["languages"] == '["python"]'
        assert job["with"]["config-file"] == "./.github/codeql/codeql-config.yml"

    def test_pull_request_has_no_branch_filter(self, codeql: dict[str, Any]) -> None:
        """Every pull request must run the scan, whatever its base branch."""
        # Read the trigger. A bare key parses to None, which means every branch.
        trigger = codeql[TRIGGER_KEY]["pull_request"]

        # A None trigger is the repaired shape, so accept it and stop here.
        if trigger is None:
            return

        # CodeQL reports a required check, so a filter blocks a stacked branch.
        assert "branches" not in trigger, (
            "The pull_request trigger must carry no branch filter. "
            "CodeQL is a required check, so a filtered branch never reports."
        )

    def test_push_stays_pinned_to_main(self, codeql: dict[str, Any]) -> None:
        """The push trigger must stay on main, so no branch scans twice."""
        # Read the push trigger, because a wide filter doubles every scan.
        push = codeql[TRIGGER_KEY]["push"]

        # A scan on every push repeats the pull request scan and adds cost.
        assert push["branches"] == ["main"], "The push trigger must stay on main."
