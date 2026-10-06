"""Prove the budget boundary between the E2E test phases and the session teardown.

Issue #3517 records the defect. `pytest-timeout` arms one timer for the setup,
the call, and the teardown of each item. Pytest ends every session fixture
inside the teardown phase of the last item, so a slow session teardown once
consumed the budget of one test and ended the process with no report.

How this guard works:
    It writes a synthetic pytest project under a temporary directory and runs
    it in a subprocess, because the thread method of the plugin ends the
    process through `os._exit(1)`. The synthetic project loads the two repair
    hooks from the real `tests/e2e/conftest.py`, so this guard proves the
    shipped code and not a copy. Each synthetic test uses `time.sleep` only.

Why the guard pins the thread method:
    The plugin selects the signal method where `signal.SIGALRM` exists, and the
    signal method raises inside the running frame instead of ending the
    process. The measured evidence of #3517 comes from a Windows workstation,
    which has no `SIGALRM`. The guard passes `--timeout-method=thread` so that
    the same decision runs on every platform.
"""

import json
import logging
import os
import re
import subprocess  # nosec B404 - The guard runs the current interpreter with a fixed argument list.
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

REPO_ROOT = Path(__file__).resolve().parents[3]  # The repository root holds the real E2E conftest.
E2E_CONFTEST_PATH = REPO_ROOT / "tests" / "e2e" / "conftest.py"  # The file under test.
REQUIRED_HOOK_NAMES = ("pytest_runtest_teardown", "pytest_runtest_logreport")  # The two repair hooks.

TEST_BUDGET_SECONDS = 4.0  # The synthetic per-item budget, which stands for E2E_TIMEOUT_SECONDS.
LAST_TEST_SLEEP_SECONDS = 3.5  # The last test spends most of the item budget before the teardown.
TEARDOWN_SLEEP_SECONDS = 6.0  # The synthetic session teardown costs more than one item budget.
GENEROUS_TEARDOWN_BUDGET_SECONDS = 20.0  # A budget that the synthetic teardown cannot exceed.
TIGHT_TEARDOWN_BUDGET_SECONDS = 2.5  # A budget that the synthetic teardown must exceed.
RUN_LIMIT_SECONDS = 120.0  # Stop a stuck subprocess, so this guard cannot block a suite.

SUMMARY_PATTERN = re.compile(r"=+ .*\b(passed|failed|error)\b.* in [0-9.]+s")  # The pytest summary line.

CONFTEST_TEMPLATE = '''"""Synthetic conftest that loads the real MistHelper E2E repair hooks."""

import importlib.util
import sys
import time

import pytest

_SPEC = importlib.util.spec_from_file_location("misthelper_e2e_conftest", r"{conftest_path}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["misthelper_e2e_conftest"] = _MODULE
_SPEC.loader.exec_module(_MODULE)

pytest_runtest_logreport = _MODULE.pytest_runtest_logreport
{teardown_hook_line}

def pytest_collection_modifyitems(config, items):
    mark = pytest.mark.timeout({test_budget})
    for item in items:
        item.add_marker(mark)


@pytest.fixture(scope="session", autouse=True)
def slow_session_teardown(request):
    yield
    root = request.config.rootpath
    (root / "teardown-start.marker").write_text("started", encoding="ascii")
    print("SESSION TEARDOWN START", flush=True)
    time.sleep({teardown_sleep})
    (root / "teardown-end.marker").write_text("ended", encoding="ascii")
    print("SESSION TEARDOWN END", flush=True)
'''

TEST_MODULE_TEMPLATE = '''"""Synthetic tests that use time.sleep only."""

import time


def test_one_passes():
    time.sleep(0.05)
    assert True


def test_two_fails():
    time.sleep(0.05)
    assert 1 == 2, "This failure must appear in the report."


def test_three_is_slow():
    time.sleep({last_test_sleep})
    assert True
'''


@dataclass
class PytestRunResult:
    """Hold the measured result of one synthetic pytest run."""

    label: str  # The scenario name, for the measured summary.
    return_code: int  # The exit code of the subprocess.
    output: str  # The combined standard output and standard error.
    elapsed_seconds: float  # The wall clock cost of the run.
    trail_path: Path  # The phase trail that the run wrote.

    def has_summary(self) -> bool:
        """Report whether pytest printed its report.

        Returns:
            True when the output holds the short summary section or the final
            count line, and False when the process ended before the report.
        """
        if "short test summary info" in self.output:  # The usual short summary section.
            return True  # Pytest reached its reporting stage.
        return SUMMARY_PATTERN.search(self.output) is not None  # The final count line.

    def teardown_started(self) -> bool:
        """Report whether the synthetic session teardown began.

        Returns:
            True when the synthetic fixture wrote its start marker.
        """
        return (self.trail_path.parent / "teardown-start.marker").is_file()  # Read the durable marker.

    def teardown_finished(self) -> bool:
        """Report whether the synthetic session teardown ran to its end.

        Why:
            Pytest discards the captured teardown output of a run that ends
            well, so a marker file is the one durable record of that end.

        Returns:
            True when the synthetic fixture wrote its end marker.
        """
        return (self.trail_path.parent / "teardown-end.marker").is_file()  # Read the durable marker.

    def trail_records(self) -> list[dict[str, object]]:
        """Read the phase trail that this run wrote.

        Returns:
            One dictionary for each JSON line.

        Raises:
            AssertionError: The run wrote no trail file.
        """
        assert self.trail_path.is_file(), f"The run {self.label} wrote no trail at {self.trail_path}."
        lines = self.trail_path.read_text(encoding="ascii").splitlines()  # Read every written record.
        return [json.loads(line) for line in lines if line.strip()]  # Parse one record for each line.


@dataclass
class PytestRunRecorder:
    """Collect the measured cost of every run, so the guard reports what it measured."""

    results: list[PytestRunResult] = field(default_factory=list)  # One entry for each run.

    def add(self, result: PytestRunResult) -> PytestRunResult:
        """Record one run.

        Args:
            result: The measured result of one synthetic pytest run.

        Returns:
            The same result, so a caller can chain the call.
        """
        self.results.append(result)  # Keep the run for the measured summary.
        return result  # Hand the result back to the fixture.

    def summary_lines(self) -> list[str]:
        """Build the measured summary.

        Returns:
            One header line with the run count and the total seconds, and one
            line for each run.
        """
        total = sum(result.elapsed_seconds for result in self.results)  # Add the cost of every run.
        header = f"e2e_timeout_budget guard: measured {len(self.results)} pytest runs in {total:.2f} seconds"
        details = [
            f"  run {result.label}: exit {result.return_code}, {result.elapsed_seconds:.2f} seconds, "
            f"summary printed: {result.has_summary()}"
            for result in self.results  # Report the measured cost of each scenario.
        ]
        return [header, *details]  # Give the header first, then each run.


def load_required_hook_names() -> tuple[str, ...]:
    """Confirm that the real E2E conftest defines the two repair hooks.

    Returns:
        The hook names that this guard found.

    Raises:
        AssertionError: The conftest is absent or it defines no such hook.
    """
    assert E2E_CONFTEST_PATH.is_file(), f"The guard cannot read its input at {E2E_CONFTEST_PATH}."
    source = E2E_CONFTEST_PATH.read_text(encoding="utf-8")  # Read the file under test one time.
    found = tuple(name for name in REQUIRED_HOOK_NAMES if f"def {name}(" in source)  # Look for each hook.
    assert found == REQUIRED_HOOK_NAMES, f"{E2E_CONFTEST_PATH} defines {found}, not {REQUIRED_HOOK_NAMES}."
    return found  # Report the hook names that the guard checked.


def build_project(root: Path, with_repair: bool) -> Path:
    """Write one synthetic pytest project.

    Args:
        root: The directory that receives the project.
        with_repair: Load the teardown repair hook when True.

    Returns:
        The project directory.
    """
    root.mkdir(parents=True, exist_ok=True)  # Create the project directory one time.
    hook_line = "pytest_runtest_teardown = _MODULE.pytest_runtest_teardown" if with_repair else ""
    conftest = CONFTEST_TEMPLATE.format(  # Build the synthetic conftest for this scenario.
        conftest_path=str(E2E_CONFTEST_PATH),  # Load the real hooks from the file under test.
        teardown_hook_line=hook_line,  # Include the repair only in the repaired scenarios.
        test_budget=TEST_BUDGET_SECONDS,  # Stand in for the real per-item budget.
        teardown_sleep=TEARDOWN_SLEEP_SECONDS,  # Stand in for the real session teardown cost.
    )
    (root / "conftest.py").write_text(conftest, encoding="ascii")  # Write the synthetic conftest.
    module = TEST_MODULE_TEMPLATE.format(last_test_sleep=LAST_TEST_SLEEP_SECONDS)  # Build the tests.
    (root / "test_synthetic_suite.py").write_text(module, encoding="ascii")  # Write the synthetic tests.
    (root / "pytest.ini").write_text("[pytest]\n", encoding="ascii")  # Pin the rootdir of the project.
    return root  # Hand the project directory to the caller.


def run_project(root: Path, label: str, teardown_budget: float | None) -> PytestRunResult:
    """Run one synthetic project in a subprocess and measure it.

    Args:
        root: The project directory.
        label: The scenario name for the measured summary.
        teardown_budget: The teardown budget override, or None for no override.

    Returns:
        The measured result of the run.
    """
    trail_path = root / "phase-trail.jsonl"  # Keep the trail inside the temporary project.
    environment = {  # Build a small, explicit environment for the subprocess.
        **_base_environment(),  # Keep the interpreter and the path settings of this machine.
        "MISTHELPER_E2E_PHASE_TRAIL": str(trail_path),  # Point the trail at the temporary file.
    }
    if teardown_budget is not None:  # Only the repaired scenarios set a teardown budget.
        environment["MISTHELPER_E2E_TEARDOWN_BUDGET_SECONDS"] = str(teardown_budget)  # Apply the override.
    command = [  # Run the current interpreter with a fixed argument list.
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:randomly",  # Keep the item order stable, so the last item is the slow test.
        "-p",
        "no:cacheprovider",  # Write no cache directory into the temporary project.
        "--timeout-method=thread",  # Pin the method that the #3517 evidence used.
        str(root),
    ]
    logger.info("Running the synthetic scenario %s", label)  # Log before the subprocess.
    started = time.monotonic()  # Measure the wall clock cost of the run.
    completed = subprocess.run(  # nosec B603 - Fixed argument list, no shell, no external input.
        command,
        cwd=str(root),
        env=environment,
        capture_output=True,
        text=True,
        timeout=RUN_LIMIT_SECONDS,
        check=False,
    )
    elapsed = time.monotonic() - started  # Record the measured seconds of the run.
    logger.debug("Scenario %s ended with code %d in %.2f seconds", label, completed.returncode, elapsed)
    output = completed.stdout + completed.stderr  # Keep both streams, because the dump uses stderr.
    return PytestRunResult(label, completed.returncode, output, elapsed, trail_path)


def _base_environment() -> dict[str, str]:
    """Build the inherited environment without the two guard overrides.

    Returns:
        A copy of the current environment with the overrides removed, so one
        scenario cannot inherit the settings of another.
    """
    environment = dict(os.environ)  # Copy the environment of this process.
    environment.pop("MISTHELPER_E2E_TEARDOWN_BUDGET_SECONDS", None)  # Drop a stale budget override.
    environment.pop("MISTHELPER_E2E_PHASE_TRAIL", None)  # Drop a stale trail override.
    return environment  # Hand the clean environment to the caller.


@pytest.fixture(scope="session")
def run_recorder(request: pytest.FixtureRequest):
    """Collect every measured run and print the measured summary at the end.

    Args:
        request: The pytest request, which gives access to the terminal reporter.

    Yields:
        The recorder that each scenario fixture fills.
    """
    recorder = PytestRunRecorder()  # Start one recorder for the whole guard session.
    yield recorder  # Hand the recorder to each scenario fixture.
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")  # Write past the capture.
    for line in recorder.summary_lines():  # Report the run count and the seconds of each run.
        if reporter is None:  # A run without the terminal plugin still must print the summary.
            print(line, flush=True)  # Fall back to the captured stream.
        else:  # The usual path writes the line straight to the terminal.
            reporter.write_line(line)  # Report what this guard measured.


@pytest.fixture(scope="session")
def shared_budget_run(tmp_path_factory: pytest.TempPathFactory, run_recorder: PytestRunRecorder):
    """Run the red case, which keeps the shared budget of today.

    Args:
        tmp_path_factory: The session temporary directory factory.
        run_recorder: The recorder of the measured runs.

    Returns:
        The measured result of the red case.
    """
    root = build_project(tmp_path_factory.mktemp("shared_budget"), with_repair=False)  # No repair hook.
    return run_recorder.add(run_project(root, "shared_budget", None))  # Measure and record the run.


@pytest.fixture(scope="session")
def separate_budget_run(tmp_path_factory: pytest.TempPathFactory, run_recorder: PytestRunRecorder):
    """Run the repaired case with a budget that the teardown cannot exceed.

    Args:
        tmp_path_factory: The session temporary directory factory.
        run_recorder: The recorder of the measured runs.

    Returns:
        The measured result of the repaired case.
    """
    root = build_project(tmp_path_factory.mktemp("separate_budget"), with_repair=True)  # Load the repair.
    return run_recorder.add(run_project(root, "separate_budget", GENEROUS_TEARDOWN_BUDGET_SECONDS))


@pytest.fixture(scope="session")
def tight_budget_run(tmp_path_factory: pytest.TempPathFactory, run_recorder: PytestRunRecorder):
    """Run the repaired case with a budget that the teardown must exceed.

    Args:
        tmp_path_factory: The session temporary directory factory.
        run_recorder: The recorder of the measured runs.

    Returns:
        The measured result of the overrun case.
    """
    root = build_project(tmp_path_factory.mktemp("tight_budget"), with_repair=True)  # Load the repair.
    return run_recorder.add(run_project(root, "tight_budget", TIGHT_TEARDOWN_BUDGET_SECONDS))


def test_guard_reports_what_it_measured(shared_budget_run: PytestRunResult, run_recorder: PytestRunRecorder) -> None:
    """The guard reads its input and reports the runs and the seconds that it measured."""
    names = load_required_hook_names()  # Fail at once when the guard cannot read the file under test.
    lines = run_recorder.summary_lines()  # Build the measured summary of the runs so far.
    print(f"e2e_timeout_budget guard: checked {len(names)} hook names in {E2E_CONFTEST_PATH}", flush=True)
    print("\n".join(lines), flush=True)  # Report the measured run count and the measured seconds.
    assert names == REQUIRED_HOOK_NAMES, f"The guard checked {names}, not {REQUIRED_HOOK_NAMES}."
    assert len(run_recorder.results) >= 1, "The guard measured no pytest run, so it proved nothing."
    assert "measured" in lines[0] and "seconds" in lines[0], f"The summary line is wrong: {lines[0]!r}."
    assert shared_budget_run.elapsed_seconds > 0.0, "The guard measured no seconds for the red case."


def test_shared_budget_loses_the_report(shared_budget_run: PytestRunResult) -> None:
    """The shared budget of today ends the process before pytest writes its report."""
    print(f"shared_budget: exit {shared_budget_run.return_code} in {shared_budget_run.elapsed_seconds:.2f}s")
    assert shared_budget_run.return_code == 1, f"The red case exited {shared_budget_run.return_code}, not 1."
    assert not shared_budget_run.has_summary(), "The red case printed a summary, so it did not reproduce #3517."
    assert shared_budget_run.teardown_started(), "The red case never reached the session teardown."
    assert not shared_budget_run.teardown_finished(), "The red case completed the session teardown."
    assert shared_budget_run.elapsed_seconds < TEARDOWN_SLEEP_SECONDS, "The red case outlived the teardown."


def test_separate_budget_keeps_the_report(separate_budget_run: PytestRunResult) -> None:
    """The separate teardown budget lets the session teardown finish and the report print."""
    print(f"separate_budget: exit {separate_budget_run.return_code} in {separate_budget_run.elapsed_seconds:.2f}s")
    assert separate_budget_run.return_code == 1, "The repaired case must still report the deliberate failure."
    assert separate_budget_run.has_summary(), "The repaired case printed no summary, so the repair failed."
    assert "test_two_fails" in separate_budget_run.output, "The report does not name the failed test."
    assert separate_budget_run.teardown_finished(), "The session teardown did not run to its end."
    assert separate_budget_run.elapsed_seconds > TEARDOWN_SLEEP_SECONDS, "The teardown did not run in full."


def test_teardown_budget_still_ends_an_overrun(
    tight_budget_run: PytestRunResult, shared_budget_run: PytestRunResult
) -> None:
    """A teardown that exceeds its own budget still ends, and later than the shared budget would."""
    print(f"tight_budget: exit {tight_budget_run.return_code} in {tight_budget_run.elapsed_seconds:.2f}s")
    assert tight_budget_run.return_code == 1, f"The overrun exited {tight_budget_run.return_code}, not 1."
    assert tight_budget_run.teardown_started(), "The overrun never reached the session teardown."
    assert not tight_budget_run.teardown_finished(), "The overrun completed the session teardown."
    assert tight_budget_run.elapsed_seconds < TEARDOWN_SLEEP_SECONDS + LAST_TEST_SLEEP_SECONDS, "No bound fired."
    gap = tight_budget_run.elapsed_seconds - shared_budget_run.elapsed_seconds  # Prove the budgets differ.
    assert gap > 1.0, f"The overrun ran {gap:.2f} seconds longer than the red case, so the budget is not separate."


def test_phase_trail_survives_the_stop(shared_budget_run: PytestRunResult) -> None:
    """The durable phase records of the red case survive the process stop."""
    records = shared_budget_run.trail_records()  # Read the trail that the stopped run wrote.
    print(f"shared_budget trail: {len(records)} durable phase records")
    assert len(records) >= 1, "The stopped run wrote no durable phase record."
    failed = [record for record in records if record["phase"] == "call" and record["outcome"] == "failed"]
    assert len(failed) == 1, f"The trail holds {len(failed)} failed call records, not 1."
    assert "test_two_fails" in str(failed[0]["node_id"]), f"The failed record names {failed[0]['node_id']!r}."
    assert set(records[0]) == {"node_id", "phase", "outcome", "duration_seconds", "timestamp_utc"}
    assert str(failed[0]["timestamp_utc"]).endswith("+00:00"), "The timestamp is not UTC ISO 8601."
