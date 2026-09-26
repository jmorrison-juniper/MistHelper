"""Guardrail: the Radon job runs the shared complexity gate at the documented limit (issue #3456).

Why:
    The `radon` job in `ci.yml` pipes the JSON report of `radon cc -j` into
    the `complexity-gate` command of the `misthelper-devtools` package. The
    job held an inline copy of that logic before, and two copies can drift.

    The limit is in three places: the `--max` option in `ci.yml`, the gate
    table in `documentation/quality-gates.md`, and the gate table in
    `.github/copilot-instructions.md`. A change to one place and not to the
    others gives a wrong rule to each reader of the other places.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
JOB_NAME = "radon"
STEP_NAME = "Check cyclomatic complexity"
INSTALL_COMMAND = "pip install -r requirements-dev.txt"  # The devtools pin in this file supplies the command.
EXPECTED_LIMIT = 10  # The limit of the earlier inline script. A change must be deliberate.

GATE_COMMAND = re.compile(
    r"^radon cc \$\{\{ env\.RADON_PATHS \}\} -j \| complexity-gate --max (\d+)$",
    re.MULTILINE,
)  # The step pipes the full report into the shared gate.
DOCUMENTED_LIMIT = re.compile(r"No block above cyclomatic complexity (\d+)")  # The sentence in each gate table.
LIMIT_DOCUMENTS = (
    REPOSITORY_ROOT / "documentation" / "quality-gates.md",
    REPOSITORY_ROOT / ".github" / "copilot-instructions.md",
)  # The two documents that state the limit to a reader.


def radon_steps() -> list[dict[str, object]]:
    """Return the steps of the `radon` job, in order.

    Returns:
        Each step mapping of the job.
    """
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return list(document["jobs"][JOB_NAME]["steps"])  # A missing job raises here, which is the correct report.


def gate_step_text(steps: list[dict[str, object]]) -> str:
    """Return the shell text of the complexity step.

    Args:
        steps: The steps of the `radon` job.

    Returns:
        The `run` text of the step.
    """
    for step in steps:
        if step.get("name") == STEP_NAME:
            return str(step["run"])
    raise AssertionError(f"The {JOB_NAME} job holds no step named {STEP_NAME!r}")


def gate_limit(run_text: str) -> int | None:
    """Return the `--max` value of the gate command in one step.

    Args:
        run_text: The shell text of the step.

    Returns:
        The limit, or None when the step does not pipe the report into the gate.
    """
    match = GATE_COMMAND.search(run_text)
    return int(match.group(1)) if match else None


def documented_limits(text: str) -> list[int]:
    """Return each limit that one document states, in document order.

    Args:
        text: The text of the document.

    Returns:
        The limits of each gate table sentence.
    """
    return [int(value) for value in DOCUMENTED_LIMIT.findall(text)]


class TestTheRadonJobRunsTheSharedGate:
    """The job runs the devtools command instead of its own copy of the logic."""

    def test_the_step_pipes_the_report_into_the_gate(self) -> None:
        """The step must apply the limit of the earlier inline script."""
        run_text = gate_step_text(radon_steps())
        assert gate_limit(run_text) == EXPECTED_LIMIT, f"The {STEP_NAME!r} step runs this text: {run_text}"

    def test_the_step_holds_no_inline_script(self) -> None:
        """A second copy of the gate logic can drift from the shared command."""
        run_text = gate_step_text(radon_steps())
        assert "python" not in run_text, f"The {STEP_NAME!r} step still holds a script: {run_text}"

    def test_the_job_installs_the_command_before_the_gate(self) -> None:
        """Without the install step, the shell cannot find `complexity-gate`."""
        steps = radon_steps()
        installs = [index for index, step in enumerate(steps) if INSTALL_COMMAND in str(step.get("run", ""))]
        gate_index = [step.get("name") for step in steps].index(STEP_NAME)
        assert len(installs) == 1, f"The {JOB_NAME} job holds {len(installs)} install steps"
        assert installs[0] < gate_index, "The install step must come before the gate step"


class TestTheDocumentedLimitMatches:
    """Each document states the limit that the job applies."""

    def test_each_document_states_the_gate_limit(self) -> None:
        """A reader of either gate table must get the limit that CI applies."""
        limit = gate_limit(gate_step_text(radon_steps()))
        found = {path.name: documented_limits(path.read_text(encoding="utf-8")) for path in LIMIT_DOCUMENTS}
        print(f"The complexity guard checked {sum(len(limits) for limits in found.values())} documented limits.")
        assert found == {path.name: [limit] for path in LIMIT_DOCUMENTS}

    def test_the_checks_find_a_wrong_limit_and_the_old_script(self) -> None:
        """Each check must report the fault that it exists to find."""
        wrong_table_row = "| `radon` | `radon cc -j` | No block above cyclomatic complexity 12. |"
        old_step = 'radon cc ${{ env.RADON_PATHS }} -j | python3 -c "\n'
        assert documented_limits(wrong_table_row) == [12]
        assert gate_limit(old_step) is None
