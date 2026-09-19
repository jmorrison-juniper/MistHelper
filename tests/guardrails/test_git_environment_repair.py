"""Tests for the git environment repair that issue #3022 required.

The helper decides whether the editor git configuration set can reach a child
process. A wrong keep leaves three guards failing inside a full run. A wrong
drop throws away a setting that the developer chose.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support.git_environment import (
    CONFIG_COUNT_NAME,
    git_subprocess_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[2]  # A fixture moves the working folder, so use an absolute path.

WHOLE_SET = {
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "safe.bareRepository",
    "GIT_CONFIG_VALUE_0": "explicit",
    "GIT_CONFIG_KEY_1": "credential.interactive",
    "GIT_CONFIG_VALUE_1": "never",
}

BROKEN_SET = {
    **WHOLE_SET,
    "GIT_CONFIG_COUNT": "3",
    "GIT_CONFIG_KEY_2": "core.fsmonitor",
    "GIT_CONFIG_VALUE_2": "",  # The exact shape the editor terminal produces.
}


def config_names(environment: dict[str, str]) -> set[str]:
    """Return every git configuration name inside one environment."""
    return {name for name in environment if name.startswith("GIT_CONFIG_")}


# The work runs inside a separate interpreter, because the mechanism edits the real
# process environment. A mutation in this interpreter would break git for every later
# test in the session, which is the very defect issue #3022 records.
CHILD_PROGRAM = """
import json, os, subprocess, sys

root = sys.argv[1]
sys.path.insert(0, root)

# Reproduce the editor set. The third value is empty, which is the shape that
# VS Code produces and that Windows drops from the child process block.
os.environ["GIT_CONFIG_COUNT"] = "3"
os.environ["GIT_CONFIG_KEY_0"] = "safe.bareRepository"
os.environ["GIT_CONFIG_VALUE_0"] = "explicit"
os.environ["GIT_CONFIG_KEY_1"] = "credential.interactive"
os.environ["GIT_CONFIG_VALUE_1"] = "never"
os.environ["GIT_CONFIG_KEY_2"] = "core.fsmonitor"
os.environ["GIT_CONFIG_VALUE_2"] = ""

command = ["git", "ls-files", "--error-unmatch", "README.md"]
inherited = subprocess.run(command, cwd=root, capture_output=True, text=True)

from tests.support.git_environment import git_subprocess_environment

repaired = subprocess.run(
    command, cwd=root, capture_output=True, text=True, env=git_subprocess_environment()
)

print(json.dumps({
    "inherited_code": inherited.returncode,
    "inherited_error": inherited.stderr.strip(),
    "repaired_code": repaired.returncode,
    "repaired_error": repaired.stderr.strip(),
}))
"""


@pytest.fixture(scope="module")
def git_outcome() -> dict[str, object]:
    """Run both git calls inside one separate interpreter and return the result."""
    if shutil.which("git") is None:  # A computer without git cannot answer the question.
        pytest.skip("git is absent, so the test cannot read the index")
    finished = subprocess.run(  # The child owns the environment mutation, so this session stays clean.
        [sys.executable, "-c", CHILD_PROGRAM, str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    return json.loads(finished.stdout.strip().splitlines()[-1])


class TestTheHelperKeepsAHealthySet:
    """A whole set must survive, so a developer keeps the settings they chose."""

    def test_an_absent_set_passes_through(self) -> None:
        """Most machines hold no set at all, and nothing must change there."""
        source = {"PATH": "/usr/bin", "HOME": "/home/someone"}
        assert git_subprocess_environment(source) == source

    def test_a_whole_set_survives(self) -> None:
        """Every promised entry holds a name and a value, so git can parse it."""
        assert git_subprocess_environment(WHOLE_SET) == WHOLE_SET

    def test_a_zero_count_survives(self) -> None:
        """A count of zero promises nothing, so git parses it without an entry."""
        source = {CONFIG_COUNT_NAME: "0"}
        assert git_subprocess_environment(source) == source

    def test_the_helper_never_mutates_the_caller_mapping(self) -> None:
        """A helper that edited the caller's dict would change os.environ itself."""
        source = dict(BROKEN_SET)
        git_subprocess_environment(source)
        assert source == BROKEN_SET


class TestTheHelperDropsAnUnusableSet:
    """A set that cannot reach a child process must go, or git refuses the command."""

    def test_an_empty_value_drops_the_whole_set(self) -> None:
        """Issue #3022. An empty value cannot survive the trip on Windows."""
        assert config_names(git_subprocess_environment(BROKEN_SET)) == set()

    def test_a_missing_value_drops_the_whole_set(self) -> None:
        """A count that promises an absent value makes git stop."""
        source = {k: v for k, v in BROKEN_SET.items() if k != "GIT_CONFIG_VALUE_2"}
        assert config_names(git_subprocess_environment(source)) == set()

    def test_a_missing_key_drops_the_whole_set(self) -> None:
        """A count that promises an absent name makes git stop."""
        source = {k: v for k, v in BROKEN_SET.items() if k != "GIT_CONFIG_KEY_2"}
        assert config_names(git_subprocess_environment(source)) == set()

    def test_a_count_that_is_not_a_number_drops_the_whole_set(self) -> None:
        """Git refuses a count it cannot read."""
        source = {**WHOLE_SET, CONFIG_COUNT_NAME: "many"}
        assert config_names(git_subprocess_environment(source)) == set()

    def test_a_negative_count_drops_the_whole_set(self) -> None:
        """A negative count is unusable."""
        source = {**WHOLE_SET, CONFIG_COUNT_NAME: "-1"}
        assert config_names(git_subprocess_environment(source)) == set()

    def test_the_drop_keeps_every_other_variable(self) -> None:
        """The repair must remove the set only, not the rest of the environment."""
        source = {**BROKEN_SET, "PATH": "/usr/bin", "HOME": "/home/someone"}
        repaired = git_subprocess_environment(source)
        assert repaired == {"PATH": "/usr/bin", "HOME": "/home/someone"}


class TestTheRepairSatisfiesGit:
    """Prove the repair against the real git program, not against a stand-in.

    Why:
        Issue #3022 was invisible to every unit test, because the fault lived in
        the process environment and not in the assertion. These tests reproduce
        the real mechanism and then prove the repair against it.

    Mechanism:
        On Windows an assignment of an empty string removes the variable from
        the process block that a child reads. ``os.environ`` keeps the name, so
        only a child process reveals the loss. The work therefore runs inside a
        separate interpreter, which keeps this test from breaking git for every
        later test in the same session.
    """

    def test_the_broken_set_makes_git_stop(self, git_outcome: dict[str, object]) -> None:
        """Prove the failure path, so a pass of the next test carries meaning."""
        if git_outcome["inherited_code"] == 0:  # A platform that keeps an empty value cannot show the defect.
            pytest.skip(
                "This platform keeps an empty environment value, so the child process still holds "
                "GIT_CONFIG_VALUE_2. The failure path of issue #3022 needs a platform that drops it."
            )
        assert "GIT_CONFIG_VALUE_2" in str(
            git_outcome["inherited_error"]
        ), f"Git stopped for another reason: {git_outcome['inherited_error']}"

    def test_the_repaired_set_lets_git_answer(self, git_outcome: dict[str, object]) -> None:
        """Prove the repair, on the same environment that the previous test broke."""
        assert (
            git_outcome["repaired_code"] == 0
        ), f"Git still refused the repaired environment: {git_outcome['repaired_error']}"
