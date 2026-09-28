"""Guardrail: MistHelper owns the test quality baseline and ignores the ratchet report (issues #3421 and #3422).

Why:
    The `test-quality-analyzer` command comes from the `misthelper-devtools`
    package. Without `--baseline`, the command reads the baseline file of the
    current repository. MistHelper keeps that record of its own findings in
    `.github/test-quality-baseline.json`, and the ratchet job names the file,
    so a later default cannot move the gate to another record (issue #3422).

    Without `--config`, the command reads the rule settings inside the
    installed package, so a rule change needed a devtools release. The ratchet
    job gives `.github/test-quality-config.toml` to the command (issue #3466).

    The analyzer writes its report into `test_quality_analyzer_output/`. The
    `.gitignore` entry `output/` does not match that folder, so a `git add -A`
    after a local run committed the report (issue #3421).

    Issue #3515 moved the scope rule of the ratchet job to the
    `--changed-from` option of the analyzer, and the devtools repository tests
    that rule. These tests read the command of the ratchet step, and they ask
    git which paths it ignores. They fail when a later change drops
    `--baseline` or `--config`, drops a path that must scan the whole suite,
    deletes the baseline or the settings, or deletes the ignore entry.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import tomllib
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
GITIGNORE_PATH = REPOSITORY_ROOT / ".gitignore"
JOB_NAME = "test_quality_gate"
STEP_NAME = "Run test quality ratchet"
ANALYZER = "test-quality-analyzer"  # The console script that the step runs.
SCOPE_ARRAY = "${scope[@]}"  # The shell array that holds the pull request scope options.
EMPTY_SCOPE = "scope=()"  # A push or manual run keeps the array empty.
PULL_REQUEST_TEST = 'if [ "$EVENT_NAME" = "pull_request" ]; then'  # Only a pull request fills the array.

BASELINE = ".github/test-quality-baseline.json"  # The job runs at the repository root.
CONFIG = ".github/test-quality-config.toml"  # The rule settings that MistHelper owns (issue #3466).
FULL_GATE_PATHS = frozenset({".github/workflows/ci.yml", "requirements-dev.txt"})  # A change here can move any finding.
BASELINE_KEYS = frozenset({"category", "file_path", "line_number", "rule_id"})  # The identity of a finding.
CONFIG_TABLES = ("rules", "severity", "exclusions")  # The three tables that the analyzer reads.

IGNORE_ENTRY = "test_quality_analyzer_output/"
REPORT_FILES = (
    "test_quality_analyzer_output/report.json",
    "test_quality_analyzer_output/summary.md",
)  # The two default outputs of the analyzer.


def ratchet_lines() -> list[str]:
    """Return the shell lines of the ratchet step, without indentation or blank lines.

    Returns:
        Each line of the `run` script of the step.
    """
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for step in document["jobs"][JOB_NAME]["steps"]:  # A missing job raises here, which is the correct report.
        if step.get("name") == STEP_NAME:
            return [line.strip() for line in str(step["run"]).splitlines() if line.strip()]
    raise AssertionError(f"{WORKFLOW_PATH.name} holds no step named {STEP_NAME!r}")


def analyzer_command() -> list[str]:
    """Return the one analyzer command of the ratchet step.

    Returns:
        The command, split the way that the shell splits it.
    """
    commands = [shlex.split(line) for line in ratchet_lines() if line.startswith(ANALYZER)]
    assert len(commands) == 1, f"The ratchet step must run the analyzer one time: {commands}"
    return commands[0]


def pull_request_scope() -> list[str]:
    """Return the options that the ratchet step adds for a pull request.

    Returns:
        The words of the `scope` array, split the way that the shell splits them.
    """
    scopes = [line for line in ratchet_lines() if line.startswith("scope=(") and line != EMPTY_SCOPE]
    assert len(scopes) == 1, f"The ratchet step must set the pull request scope one time: {scopes}"
    return shlex.split(scopes[0].removeprefix("scope=(").removesuffix(")"))


def expanded_command(event_name: str, base_ref: str) -> list[str]:
    """Return the analyzer command of one event, with the shell expansion done.

    Args:
        event_name: The workflow event, for example `push` or `pull_request`.
        base_ref: The branch that the pull request targets.

    Returns:
        The analyzer command that the shell starts for that event.
    """
    command = analyzer_command()
    position = command.index(SCOPE_ARRAY)  # A command without the array has no scope, and this raises.
    scope = [word.replace("$BASE_REF", base_ref) for word in pull_request_scope()]
    added = scope if event_name == "pull_request" else []
    return [*command[:position], *added, *command[position + 1 :]]


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


def option_values(command: list[str], option: str) -> list[str]:
    """Return each value of a repeatable option in one analyzer command.

    Args:
        command: One analyzer command.
        option: The option name, for example `--full-gate-path`.

    Returns:
        The values in command order.
    """
    return [command[index + 1] for index, word in enumerate(command[:-1]) if word == option]


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


class TestTheRatchetCommand:
    """The one analyzer command of the ratchet step reads the files of this repository."""

    def test_the_command_runs_the_gate(self) -> None:
        """Without `--gate`, the command writes a report and never fails."""
        command = analyzer_command()
        print(f"The command guard checked {len(command)} words.")
        assert "--gate" in command, f"The ratchet command runs no gate: {command}"

    def test_the_command_reads_the_repository_baseline(self) -> None:
        """This is the fault of issue #3422: a run without `--baseline` reads another record."""
        assert baseline_argument(analyzer_command()) == BASELINE

    def test_the_command_reads_the_repository_settings(self) -> None:
        """Issue #3466: a run without `--config` reads the rule settings of the devtools package."""
        assert config_argument(analyzer_command()) == CONFIG

    def test_only_a_pull_request_gets_a_scope(self) -> None:
        """A push or manual run must prove the whole suite against the baseline."""
        lines = ratchet_lines()
        assert EMPTY_SCOPE in lines, f"The ratchet step never empties the scope: {lines}"
        assert PULL_REQUEST_TEST in lines, f"The ratchet step sets the scope for each event: {lines}"
        assert expanded_command("push", "main") == [word for word in analyzer_command() if word != SCOPE_ARRAY]

    def test_a_pull_request_compares_against_its_base(self) -> None:
        """The job fetches the base branch to `origin/<base>`, and the scope reads that ref."""
        scope = pull_request_scope()
        assert option_values(scope, "--changed-from") == ["origin/$BASE_REF"], f"The scope changed: {scope}"

    def test_a_tooling_change_scans_the_whole_suite(self) -> None:
        """A new devtools pin or a new job step can change each finding."""
        paths = option_values(pull_request_scope(), "--full-gate-path")
        assert len(paths) == len(set(paths)), f"The scope names a path twice: {paths}"
        assert set(paths) == FULL_GATE_PATHS, f"The scope changed its full-gate paths: {paths}"

    def test_the_check_finds_a_command_without_a_baseline(self) -> None:
        """The check must report the command form that issue #3422 describes."""
        assert baseline_argument(["test-quality-analyzer", "--gate"]) is None
        assert baseline_argument(["test-quality-analyzer", "--gate", "--baseline"]) is None

    def test_the_check_finds_a_command_without_settings(self) -> None:
        """The check must report a command that gives no settings file."""
        assert config_argument(["test-quality-analyzer", "--gate", "--baseline", BASELINE]) is None
        assert config_argument(["test-quality-analyzer", "--gate", "--config"]) is None


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
