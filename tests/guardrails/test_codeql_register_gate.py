"""Hold the CodeQL verdict register gate in place.

Issue #2088 recorded that `documentation/security/codeql-verdict-register.md`
drifted by seven rows and no gate noticed, because no workflow called the tool.
The repair adds the `codeql_register_check` job to `.github/workflows/ci.yml`.
These tests hold that repair in place. A change that removes the job fails a
test, so the register can never drift in silence again.
"""

from pathlib import Path
from typing import Any

import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because every test below reads the same file.
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Name the job once, because the checks below inspect the same entry.
GATE_JOB = "codeql_register_check"


def _parse(path: Path) -> dict[str, Any]:
    """Parse one workflow file and return the mapping."""
    # Read with an explicit encoding, because the Windows default differs.
    text = path.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # Fail early with a clear message, because a non-mapping breaks each test.
    assert isinstance(parsed, dict), f"The workflow must be a mapping: {path}"

    return parsed


def _gate_job() -> dict[str, Any]:
    """Return the gate job entry, because every test below inspects it."""
    # Read the jobs table, because the gate job lives under it.
    jobs = _parse(CI_WORKFLOW)["jobs"]

    # Fail with a clear message, because the other tests need the job too.
    assert GATE_JOB in jobs, (
        f"The workflow must keep the {GATE_JOB} job. "
        "Without it the CodeQL verdict register can drift in silence. See issue #2088."
    )

    return jobs[GATE_JOB]


def test_the_gate_job_runs_the_shipped_check() -> None:
    """The gate must run the check mode of the shipped tool."""
    # Read every run command, because the check must appear in one of them.
    steps = _gate_job()["steps"]
    commands = [str(step.get("run", "")) for step in steps]
    joined = " ".join(commands)

    # The check mode reconciles the register, so the gate must call it.
    assert "scripts/codeql_verdict_register.py" in joined, "The gate must call scripts/codeql_verdict_register.py."
    assert "check" in joined, "The gate must run the check mode."


def test_the_gate_job_carries_a_token_for_the_api_read() -> None:
    """The gate must hand the job a token, because the check reads the API."""
    # Read the step that runs the check, because the token sits on that step.
    steps = _gate_job()["steps"]
    check_step = next(step for step in steps if "codeql_verdict_register" in str(step.get("run", "")))

    # The check shells out to gh api, so the step must carry the token.
    token = check_step.get("env", {}).get("GH_TOKEN", "")
    assert "GITHUB_TOKEN" in str(token), (
        "The check step must carry GITHUB_TOKEN, " "because the tool reads the code scanning API through gh."
    )


def test_the_failure_job_reads_the_gate_result() -> None:
    """The failure job must read the gate, so a drift opens an issue."""
    # Read the jobs table, because the failure job lists its needs there.
    jobs = _parse(CI_WORKFLOW)["jobs"]
    needs = jobs["create_failure_issues"]["needs"]

    # A missing entry leaves the gate outside the issue lifecycle.
    assert GATE_JOB in needs, (
        "create_failure_issues must list the register gate, "
        "so a drift opens a quality-gate issue like every other gate."
    )


def test_the_close_job_reads_the_gate_result() -> None:
    """The close job must read the gate, so a repair closes the issue."""
    # Read the jobs table, because the close job lists its needs there.
    jobs = _parse(CI_WORKFLOW)["jobs"]
    needs = jobs["close_resolved_issues"]["needs"]

    # A missing entry leaves a repaired gate with an open issue.
    assert GATE_JOB in needs, (
        "close_resolved_issues must list the register gate, " "so a passing run closes the matching issue."
    )
