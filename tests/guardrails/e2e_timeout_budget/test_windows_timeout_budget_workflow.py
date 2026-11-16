"""Protect the optional native Windows acceptance workflow for issue #4777."""

import logging  # Keep the contract decision visible in pytest diagnostics.
import re  # Validate action references without blocking future major versions.
import subprocess  # Execute the workflow validator against synthetic reports.
import sys  # Reuse the active Python interpreter for validator behavior.
from copy import deepcopy  # Keep mutation checks away from the loaded workflow.
from pathlib import Path  # Resolve the workflow from this repository.
from typing import Any  # Describe the parsed YAML mapping.

import pytest  # Provide shared test setup for both contract cases.
import yaml  # Parse workflow YAML without executing it.

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # Locate the repository root.
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "windows-timeout-budget.yml"  # Locate the contract.


class TimeoutBudgetWorkflowPolicy:
    """Check that the optional workflow keeps its acceptance boundary."""

    EXPECTED_PATHS = {
        ".github/workflows/windows-timeout-budget.yml",
        "tests/guardrails/e2e_timeout_budget/test_windows_timeout_budget_workflow.py",
        "tests/guardrails/e2e_timeout_budget/test_timeout_budget.py",
        "tests/e2e/conftest.py",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    }  # Restrict runs to files that can affect this acceptance result.

    @staticmethod
    def trigger_violations(workflow: dict[str, Any]) -> list[str]:
        """Return trigger errors that could widen or skip the intended run."""
        findings = []  # Collect every trigger contract error.
        events = workflow.get("on", workflow.get(True, {}))  # Accept PyYAML's Boolean key form.
        if not isinstance(events, dict) or set(events) != {"push"}:  # Limit the event types.
            findings.append("The workflow must use only the push event.")  # Name the trigger failure.
        push = events.get("push", {}) if isinstance(events, dict) else {}  # Read only a valid push mapping.
        if not isinstance(push, dict) or push.get("branches-ignore") != ["main"]:  # Exclude main.
            findings.append("The push event must exclude main.")  # Name the branch failure.
        paths = push.get("paths", []) if isinstance(push, dict) else []  # Read the narrow path list.
        expected = TimeoutBudgetWorkflowPolicy.EXPECTED_PATHS  # Read the approved path list.
        if not isinstance(paths, list) or set(paths) != expected:  # Keep the trigger narrow.
            findings.append("The push event must use the exact path list.")  # Name the path failure.
        return findings  # Return all trigger errors to the contract test.

    @staticmethod
    def action_violations(workflow: dict[str, Any]) -> list[str]:
        """Return checkout and Python setup errors."""
        findings = []  # Collect every action contract error.
        job = workflow.get("jobs", {}).get("windows_timeout_budget", {})  # Read the one acceptance job.
        steps = job.get("steps", [])  # Read its execution steps.
        checkout = next(
            (step for step in steps if step.get("uses", "").startswith("actions/checkout@")),
            {},
        )  # Find checkout.
        setup = next(
            (step for step in steps if step.get("uses", "").startswith("actions/setup-python@")),
            {},
        )  # Find Python setup.
        if not re.fullmatch(r"actions/checkout@v[1-9]\d*", checkout.get("uses", "")):  # Require a version tag.
            findings.append("Checkout must use a versioned action.")  # Name the checkout action failure.
        if checkout.get("with", {}).get("persist-credentials") is not False:  # Prevent stored checkout credentials.
            findings.append("Checkout must not persist credentials.")  # Name the credential failure.
        if not re.fullmatch(r"actions/setup-python@v[1-9]\d*", setup.get("uses", "")):  # Require a version tag.
            findings.append("Python setup must use a versioned action.")  # Name the Python action failure.
        if setup.get("with", {}).get("python-version") != "3.15":  # Use the project Python release.
            findings.append("Python setup must select version 3.15.")  # Name the runtime failure.
        return findings  # Return all action errors to the contract test.

    @staticmethod
    def acceptance_violations(workflow: dict[str, Any]) -> list[str]:
        """Return native runtime and full-module result errors."""
        findings = []  # Collect each acceptance execution error.
        steps = workflow.get("jobs", {}).get("windows_timeout_budget", {}).get("steps", [])  # Read all job steps.
        platform_step = next(
            (step for step in steps if step.get("name") == "Confirm native Windows Python"),
            {},
        )  # Find the native check.
        platform = platform_step.get("run", "")  # Read its platform decision.
        runtime_tokens = ("Windows_NT", 'os.name == "nt"', "sys.version_info[:2] == (3, 15)")  # Require both checks.
        if not all(token in platform for token in runtime_tokens):  # Confirm Windows and Python.
            findings.append("The workflow must confirm native Windows and Python 3.15.")  # Name runtime failure.
        test_step = next(
            (step for step in steps if step.get("name") == "Run native timeout budget guard"),
            {},
        )  # Find the full-module run.
        test_run = test_step.get("run", "")  # Read its command and result check.
        required = (
            "python -m pytest -q",
            "--junitxml=",
            "tests/guardrails/e2e_timeout_budget/test_timeout_budget.py",
            "total == 7",
            "skipped == 0",
            "failures == 0",
            "errors == 0",
        )  # Require the full module and exact result counts.
        if not all(token in test_run for token in required):  # Check the result policy.
            findings.append("Seven tests must pass without skips, failures, or errors.")  # Name result failure.
        return findings  # Return every acceptance execution error.

    @staticmethod
    def junit_validator(workflow: dict[str, Any]) -> str:
        """Return the exact inline result validator from the workflow."""
        steps = workflow["jobs"]["windows_timeout_budget"]["steps"]  # Read the validated job steps.
        test_step = next(
            step  # Keep the selected workflow step.
            for step in steps  # Inspect each workflow step.
            if step.get("name") == "Run native timeout budget guard"  # Select the guard command.
        )  # Fail when the guard step is absent.
        command = next(
            line.strip()  # Remove indentation from the shell command.
            for line in test_step["run"].splitlines()  # Inspect each command in the step.
            if line.strip().startswith("python -c '")  # Select the inline Python validator.
        )  # Fail when the validator command is absent.
        prefix = "python -c '"  # Identify the shell command prefix.
        suffix = "' $junitPath"  # Identify the JUnit argument suffix.
        return command[len(prefix) : -len(suffix)] if command.endswith(suffix) else ""  # Extract only the real script.


class TimeoutBudgetJobPolicy:
    """Check that the job has safe permissions and a bounded test scope."""

    @staticmethod
    def permission_violations(workflow: dict[str, Any]) -> list[str]:
        """Return permission and concurrency errors."""
        findings = []  # Collect permission and concurrency errors.
        if workflow.get("permissions") != {"contents": "read"}:  # Keep repository access read-only.
            findings.append("The workflow must grant contents read access only.")  # Name the permission failure.
        allowed_env = {"FORCE_JAVASCRIPT_ACTIONS_TO_NODE24": "true"}  # Pin the action runtime only.
        if workflow.get("env") != allowed_env:  # Reject global credentials.
            findings.append("The workflow must not add global credentials.")  # Name the global environment failure.
        concurrency = workflow.get("concurrency", {})  # Read the branch cancellation policy.
        cancel = concurrency.get("cancel-in-progress") is True  # Require cancellation.
        group = concurrency.get("group", "")  # Read the per-branch group.
        if not cancel or "github.ref" not in group:  # Isolate concurrent branch runs.
            findings.append("The workflow must cancel older runs for this branch.")  # Name cancellation failure.
        return findings  # Return permission and concurrency errors.

    @staticmethod
    def runner_violations(workflow: dict[str, Any]) -> list[str]:
        """Return runner, timeout, service, and credential errors."""
        findings = []  # Collect runner boundary errors.
        jobs = workflow.get("jobs", {})  # Read the acceptance job.
        if not isinstance(jobs, dict):  # Reject an invalid job mapping.
            return ["The workflow must define one Windows job."]  # Stop before reading invalid data.
        job = jobs.get("windows_timeout_budget", {})  # Select the acceptance job.
        runner_ok = job.get("runs-on") == "windows-latest"  # Require the native runner.
        timeout_ok = job.get("timeout-minutes") == 20  # Require a bounded run.
        if len(jobs) != 1 or not runner_ok or not timeout_ok:  # Enforce one bounded job.
            findings.append("The workflow must have one bounded Windows job.")  # Name the runner failure.
        if "services" in job:  # Reject live services.
            findings.append("The Windows job must not start services.")  # Name the service failure.
        if job.get("env"):  # Reject job-level credentials.
            findings.append("The Windows job must not define credentials.")  # Name the job environment failure.
        return findings  # Return runner boundary errors.

    @staticmethod
    def step_violations(workflow: dict[str, Any]) -> list[str]:
        """Return errors for steps outside local setup and test execution."""
        expected_steps = (
            "Checkout without persisted credentials",
            "Set up Python",
            "Install runtime dependencies",
            "Install test dependencies",
            "Confirm native Windows Python",
            "Run native timeout budget guard",
        )  # Allow only local test setup and execution.
        jobs = workflow.get("jobs", {})  # Read the workflow jobs.
        job = jobs.get("windows_timeout_budget", {}) if isinstance(jobs, dict) else {}  # Select the Windows job.
        actual_steps = tuple(step.get("name") for step in job.get("steps", []))  # Read the complete job flow.
        if actual_steps != expected_steps:  # Reject browser and live-operation steps.
            return ["The job must contain only the required acceptance steps."]  # Name the step failure.
        return []  # Report no step sequence errors.


class TestWindowsTimeoutBudgetWorkflow:
    """Keep the Windows acceptance workflow optional and complete."""

    @pytest.fixture
    def workflow(self) -> dict[str, Any]:
        """Read the actual workflow so tests cannot validate a copied example."""
        logging.info("action=%s phase=%s", "read_timeout_workflow", "before")  # Mark the workflow read.
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))  # Parse the repository file.
        assert isinstance(workflow, dict), "The workflow must be a mapping."  # Reject invalid YAML shapes.
        if True in workflow:  # PyYAML treats an unquoted on key as a Boolean.
            assert "on" not in workflow, "The workflow must declare one trigger key."  # Reject duplicate trigger keys.
            workflow["on"] = workflow.pop(True)  # Normalize the parsed trigger key.
        logging.debug("action=%s phase=%s checked=%s", "read_timeout_workflow", "after", 1)  # Report the parsed file.
        return workflow  # Share the parsed workflow with both tests.

    def test_workflow_matches_the_native_acceptance_contract(self, workflow: dict[str, Any]) -> None:
        """Require one filtered Windows run that checks the full test result."""
        policy_checks = (
            TimeoutBudgetWorkflowPolicy.trigger_violations,
            TimeoutBudgetJobPolicy.permission_violations,
            TimeoutBudgetJobPolicy.runner_violations,
            TimeoutBudgetJobPolicy.step_violations,
            TimeoutBudgetWorkflowPolicy.action_violations,
            TimeoutBudgetWorkflowPolicy.acceptance_violations,
        )  # Keep each contract group independent.
        findings = [finding for check in policy_checks for finding in check(workflow)]  # Collect contract failures.
        print(f"Checked 6 workflow contract groups: findings={findings}.")  # Report the examined contract groups.
        assert findings == [], f"The acceptance contract changed: {findings}"  # Fail on policy drift.

    def test_contract_rejects_an_added_pull_request_trigger(self, workflow: dict[str, Any]) -> None:
        """Prove that a wider event trigger fails the same policy decision."""
        candidate = deepcopy(workflow)  # Keep the valid fixture unchanged.
        candidate["on"]["pull_request"] = {}  # Reproduce an unapproved event trigger.
        findings = TimeoutBudgetWorkflowPolicy.trigger_violations(candidate)  # Apply the production contract decision.
        print(f"Checked 1 trigger mutation: findings={findings}.")  # Report the negative test decision.
        assert (
            "The workflow must use only the push event." in findings
        ), "The contract accepted a pull request trigger."  # Prove rejection.

    @pytest.mark.parametrize(
        ("xml_content", "expected_return_code"),
        [
            ('<testsuites><testsuite tests="7" skipped="0" failures="0" errors="0"/></testsuites>', 0),
            ('<testsuites><testsuite tests="0" skipped="0" failures="0" errors="0"/></testsuites>', 1),
            ('<testsuites><testsuite tests="6" skipped="0" failures="0" errors="0"/></testsuites>', 1),
            ('<testsuites><testsuite tests="7" skipped="1" failures="0" errors="0"/></testsuites>', 1),
            ('<testsuites><testsuite tests="7" skipped="0" failures="1" errors="0"/></testsuites>', 1),
            ('<testsuites><testsuite tests="7" skipped="0" failures="0" errors="1"/></testsuites>', 1),
            (None, 1),
            ("<testsuites>", 1),
        ],
        ids=("valid", "zero-tests", "wrong-count", "skipped", "failed", "errored", "unreadable", "malformed"),
    )
    def test_junit_validator_checks_real_result_counts(
        self,
        workflow: dict[str, Any],
        tmp_path: Path,
        xml_content: str | None,
        expected_return_code: int,
    ) -> None:
        """Run the workflow's actual inline validator against synthetic JUnit reports."""
        validator = TimeoutBudgetWorkflowPolicy.junit_validator(workflow)  # Extract the workflow's real script.
        assert validator != "", "The workflow must include its inline JUnit validator."  # Reject a missing validator.
        report_path = tmp_path / "timeout-budget.xml"  # Isolate each synthetic report.
        if xml_content is not None:  # Keep the unreadable case without a file.
            logging.info("action=%s phase=%s", "write_junit_fixture", "before")  # Mark the temporary report write.
            report_path.write_text(xml_content, encoding="utf-8")  # Supply exact synthetic result counts.
            logging.debug("action=%s size=%s", "write_junit_fixture", len(xml_content))  # Report fixture size.
        logging.info("action=%s phase=%s", "run_junit_validator", "before")  # Mark actual validator execution.
        result = subprocess.run(
            [sys.executable, "-c", validator, str(report_path)],  # Execute the extracted Python command.
            capture_output=True,  # Retain validator errors for the assertion.
            text=True,  # Compare the process result without byte conversion.
            check=False,  # Assert the expected pass or fail result below.
        )
        logging.debug("action=%s code=%s", "run_junit_validator", result.returncode)  # Report validator status.
        assert result.returncode == expected_return_code, result.stderr  # Verify the required result policy.
