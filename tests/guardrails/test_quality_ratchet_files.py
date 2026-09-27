"""Guardrail: MistHelper owns the test quality baseline and ignores the ratchet report (issues #3421 and #3422).

Why:
    The `test-quality-analyzer` command comes from the `misthelper-devtools`
    package. Without `--baseline`, the command reads the baseline file inside
    the installed package. MistHelper could not repair or prune that record of
    its own findings, so a line shift in a test failed the gate with no local
    repair (issue #3422). The ratchet job now gives the file in this repository
    to each analyzer run.

    Without `--config`, the command also reads the rule settings inside the
    installed package, so a rule change needed a devtools release. The ratchet
    job now gives `.github/test-quality-config.toml` to each run (issue #3466).

    The analyzer writes its report into `test_quality_analyzer_output/`. The
    `.gitignore` entry `output/` does not match that folder, so a `git add -A`
    after a local run committed the report (issue #3421).

    These tests run the ratchet script of the workflow with a fake
    `subprocess` module, and they ask git which paths it ignores. They fail
    when a later change drops `--baseline` or `--config` from one run, deletes
    the baseline or the settings, or deletes the ignore entry.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import types
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
GITIGNORE_PATH = REPOSITORY_ROOT / ".gitignore"
JOB_NAME = "test_quality_gate"
STEP_NAME = "Run test quality ratchet"
HEREDOC_START = "python - <<'PY'\n"  # The step feeds the script to Python on standard input.
HEREDOC_END = "\nPY"  # The line that ends the script.

BASELINE = ".github/test-quality-baseline.json"  # The job runs at the repository root.
CONFIG = ".github/test-quality-config.toml"  # The rule settings that MistHelper owns (issue #3466).
FULL_GATE = ["test-quality-analyzer", "--gate", "--config", CONFIG, "--baseline", BASELINE]  # The whole suite.
CHANGED_TEST = "tests/guardrails/test_quality_ratchet_files.py"  # This file exists, so a scoped run keeps it.
EXPECTED_ANALYZER_RUNS = 3  # The push run, the full pull request run, and the scoped pull request run.
BASELINE_KEYS = frozenset({"category", "file_path", "line_number", "rule_id"})  # The identity of a finding.
CONFIG_TABLES = ("rules", "severity", "exclusions")  # The three tables that the analyzer reads.

IGNORE_ENTRY = "test_quality_analyzer_output/"
REPORT_FILES = (
    "test_quality_analyzer_output/report.json",
    "test_quality_analyzer_output/summary.md",
)  # The two default outputs of the analyzer.


class RecordingSubprocess:
    """Stand in for `subprocess`, so that the ratchet script starts no process.

    Why:
        The test must see each analyzer command that the script builds, on
        each branch of the script, without a real analyzer or a real git
        history.
    """

    def __init__(self, changed_paths: tuple[str, ...]) -> None:
        self.changed_paths = changed_paths  # The file list that `git diff` gives to the script.
        self.commands: list[list[str]] = []  # Each analyzer command, in call order.

    def check_output(self, command: list[str], text: bool = False) -> str:
        """Return the changed file list for the one `git diff` call of the script.

        Args:
            command: The command that the script runs.
            text: The text mode flag of the real function. The script sets it.

        Returns:
            One changed path on each line.
        """
        if command[:3] != ["git", "diff", "--name-only"]:  # The script asks git for nothing else.
            raise AssertionError(f"The ratchet script ran an unexpected command: {command}")
        return "".join(f"{path}\n" for path in self.changed_paths)

    def call(self, command: list[str]) -> int:
        """Record one analyzer command and report a clean gate.

        Args:
            command: The analyzer command that the script starts.

        Returns:
            Zero, the exit status of a clean gate.
        """
        self.commands.append(list(command))
        return 0

    def as_module(self) -> types.ModuleType:
        """Return a module that the `import subprocess` line of the script can bind."""
        module = types.ModuleType("subprocess")
        module.check_output = self.check_output
        module.call = self.call
        return module


def ratchet_script() -> str:
    """Return the Python source that the ratchet step gives to the interpreter.

    Returns:
        The script text between the two heredoc lines.
    """
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for step in document["jobs"][JOB_NAME]["steps"]:  # A missing job raises here, which is the correct report.
        if step.get("name") == STEP_NAME:
            run = str(step["run"])
            start = run.index(HEREDOC_START) + len(HEREDOC_START)  # A missing heredoc raises too.
            return run[start : run.rindex(HEREDOC_END)]
    raise AssertionError(f"{WORKFLOW_PATH.name} holds no step named {STEP_NAME!r}")


def run_ratchet(
    monkeypatch: pytest.MonkeyPatch, event_name: str, changed_paths: tuple[str, ...] = ()
) -> list[list[str]]:
    """Run the ratchet script for one event, and return the analyzer commands.

    Args:
        monkeypatch: The pytest fixture that removes each patch after the test.
        event_name: The workflow event, for example `push` or `pull_request`.
        changed_paths: The files that the pull request changes.

    Returns:
        Each analyzer command that the script started, in call order.
    """
    recorder = RecordingSubprocess(changed_paths)
    monkeypatch.setitem(sys.modules, "subprocess", recorder.as_module())  # The script imports it by name.
    monkeypatch.setenv("EVENT_NAME", event_name)
    monkeypatch.setenv("BASE_REF", "main")
    monkeypatch.chdir(REPOSITORY_ROOT)  # The scoped branch keeps only the changed tests that exist.
    code = compile(ratchet_script(), str(WORKFLOW_PATH), "exec")
    with pytest.raises(SystemExit) as stop:  # Each branch of the script ends with SystemExit.
        exec(code, {"__name__": "__main__"})
    assert stop.value.code == 0, f"The ratchet script exited with {stop.value.code!r}"
    return recorder.commands


def option_argument(command: list[str], option: str) -> str | None:
    """Return the value of one option in one analyzer command.

    Args:
        command: One analyzer command.
        option: The option name, for example `--baseline`.

    Returns:
        The value, or None when the command gives no value for the option.
    """
    if option not in command:
        return None
    position = command.index(option)
    return command[position + 1] if position + 1 < len(command) else None


def baseline_argument(command: list[str]) -> str | None:
    """Return the value of the `--baseline` option in one analyzer command.

    Args:
        command: One analyzer command.

    Returns:
        The baseline path, or None when the command gives no baseline.
    """
    return option_argument(command, "--baseline")


def config_argument(command: list[str]) -> str | None:
    """Return the value of the `--config` option in one analyzer command.

    Args:
        command: One analyzer command.

    Returns:
        The settings path, or None when the command gives no settings file.
    """
    return option_argument(command, "--config")


def every_analyzer_command(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Return the analyzer commands of the three branches that start the analyzer.

    Args:
        monkeypatch: The pytest fixture that removes each patch after the test.

    Returns:
        The commands of the push run, the full pull request run, and the scoped run.
    """
    runs = (
        run_ratchet(monkeypatch, "push"),
        run_ratchet(monkeypatch, "pull_request", ("requirements-dev.txt",)),
        run_ratchet(monkeypatch, "pull_request", (CHANGED_TEST,)),
    )
    return [command for run in runs for command in run]


def git_ignored(paths: tuple[str, ...], root: Path) -> list[str]:
    """Return the paths that the ignore rules under one root match.

    Why:
        `--no-index` makes git test each path against the rules only. Thus
        the answer does not change with the files that exist or that git
        tracks.

    Args:
        paths: The paths to test, relative to the root.
        root: The work tree that holds the `.gitignore` file.

    Returns:
        The paths that git ignores, in the order of the input.
    """
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", *paths],
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=False,  # Exit status 1 means that no path matched, and the test must see that.
    )
    if result.returncode not in (0, 1):  # Exit status 128 is a git fault, not an answer.
        raise AssertionError(f"git check-ignore failed: {result.stderr}")
    return result.stdout.splitlines()


class TestEachRunReadsTheRepositoryBaseline:
    """Each branch of the ratchet script gives the baseline in this repository."""

    def test_a_push_run_checks_the_whole_suite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A push to main proves the whole suite against the repository baseline."""
        assert run_ratchet(monkeypatch, "push") == [FULL_GATE]

    def test_a_tooling_change_checks_the_whole_suite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A new devtools pin can change each finding, so it must prove the whole suite."""
        assert run_ratchet(monkeypatch, "pull_request", ("requirements-dev.txt",)) == [FULL_GATE]

    def test_a_baseline_change_checks_the_whole_suite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A pruned or rewritten baseline must still hold each current finding."""
        assert run_ratchet(monkeypatch, "pull_request", (BASELINE,)) == [FULL_GATE]

    def test_a_rule_change_checks_the_whole_suite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A changed rule can add or remove a finding in any test file."""
        assert run_ratchet(monkeypatch, "pull_request", (CONFIG,)) == [FULL_GATE]

    def test_a_test_change_checks_only_that_test(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A scoped run still compares against the repository baseline."""
        commands = run_ratchet(monkeypatch, "pull_request", (CHANGED_TEST, "README.md"))
        assert commands == [[*FULL_GATE, "--roots", CHANGED_TEST]]

    def test_a_change_without_a_test_starts_no_analyzer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A pull request that changes no test cannot add a test quality finding."""
        assert run_ratchet(monkeypatch, "pull_request", ("README.md",)) == []

    def test_no_run_reads_the_installed_baseline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """This is the fault of issue #3422: a run without `--baseline` reads the devtools copy."""
        commands = every_analyzer_command(monkeypatch)
        missing = [command for command in commands if baseline_argument(command) != BASELINE]
        print(f"The baseline guard checked {len(commands)} analyzer commands.")
        assert len(commands) == EXPECTED_ANALYZER_RUNS, f"The script started these commands: {commands}"
        assert missing == [], f"These analyzer commands do not give {BASELINE}: {missing}"

    def test_no_run_reads_the_installed_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issue #3466: a run without `--config` reads the rule settings of the devtools package."""
        commands = every_analyzer_command(monkeypatch)
        missing = [command for command in commands if config_argument(command) != CONFIG]
        print(f"The settings guard checked {len(commands)} analyzer commands.")
        assert len(commands) == EXPECTED_ANALYZER_RUNS, f"The script started these commands: {commands}"
        assert missing == [], f"These analyzer commands do not give {CONFIG}: {missing}"

    def test_the_check_finds_a_command_without_a_baseline(self) -> None:
        """The check must report the command form that issue #3422 describes."""
        assert baseline_argument(["test-quality-analyzer", "--gate"]) is None
        assert baseline_argument(["test-quality-analyzer", "--gate", "--baseline"]) is None

    def test_the_check_finds_a_command_without_settings(self) -> None:
        """The check must report a command that gives no settings file."""
        assert config_argument(["test-quality-analyzer", "--gate", "--baseline", BASELINE]) is None
        assert config_argument(["test-quality-analyzer", "--gate", "--config"]) is None


class TestTheBaselineFile:
    """The repository holds the record of its accepted findings."""

    def test_the_baseline_holds_complete_findings(self) -> None:
        """An empty file would let the gate compare against nothing."""
        entries = json.loads((REPOSITORY_ROOT / BASELINE).read_text(encoding="utf-8"))
        assert isinstance(entries, list), f"{BASELINE} must hold a JSON list"
        incomplete = [entry for entry in entries if not BASELINE_KEYS <= set(entry)]
        print(f"The baseline guard checked {len(entries)} baseline entries.")
        assert len(entries) >= 1, f"{BASELINE} holds no finding"
        assert incomplete == [], f"These entries have no identity field: {incomplete[:3]}"


class TestTheSettingsFile:
    """The repository holds the rule settings of its gate (issue #3466)."""

    def test_the_settings_give_a_severity_for_each_enabled_rule(self) -> None:
        """A rule with no severity would take a default that no file in this repository states."""
        settings = tomllib.loads((REPOSITORY_ROOT / CONFIG).read_text(encoding="utf-8"))
        absent = [table for table in CONFIG_TABLES if not isinstance(settings.get(table), dict)]
        assert absent == [], f"{CONFIG} holds no table named {absent}"
        rules = settings["rules"]
        enabled = [rule for rule, on in rules.items() if on is True]
        no_severity = [rule for rule in enabled if rule not in settings["severity"]]
        print(f"The settings guard checked {len(rules)} rules.")
        assert len(enabled) >= 1, f"{CONFIG} enables no rule, so the gate would measure nothing"
        assert no_severity == [], f"These enabled rules have no severity in {CONFIG}: {no_severity}"

    def test_git_keeps_the_settings(self) -> None:
        """The gate needs the settings in each checkout, so no rule may ignore the file."""
        assert git_ignored((CONFIG,), REPOSITORY_ROOT) == []


class TestTheReportIsIgnored:
    """Git never offers the analyzer report for a commit."""

    def test_git_ignores_both_report_files(self) -> None:
        """This is the fault of issue #3421: the report showed as untracked after a local run."""
        ignored = git_ignored(REPORT_FILES, REPOSITORY_ROOT)
        print(f"The ignore guard checked {len(REPORT_FILES)} report paths.")
        assert ignored == list(REPORT_FILES)

    def test_git_keeps_the_baseline(self) -> None:
        """The gate needs the baseline in each checkout, so no rule may ignore it."""
        assert git_ignored((BASELINE,), REPOSITORY_ROOT) == []

    def test_the_entry_is_the_rule_that_ignores_the_report(self, tmp_path: Path) -> None:
        """Without the entry, git shows the report again, so the entry is the repair."""
        lines = GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        assert IGNORE_ENTRY in lines, f".gitignore holds no {IGNORE_ENTRY!r} line"
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        kept = [line for line in lines if line != IGNORE_ENTRY]
        (tmp_path / ".gitignore").write_text("\n".join(kept) + "\n", encoding="utf-8")
        assert git_ignored(REPORT_FILES, tmp_path) == []
