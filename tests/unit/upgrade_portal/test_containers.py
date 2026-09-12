"""Tests for the container runtime seam of the dependency preflight (issue #2059).

Why:
    This module is the only place in the portal that reaches a container
    runtime, so every guard it holds protects every caller. The tests below
    cover the name guard, the runtime search, each state the runtime can report,
    and every failure path. No test runs a real container.
"""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.upgrade_portal.runtime import containers
from src.upgrade_portal.runtime.containers import (
    ContainerState,
    find_runtime,
    read_container_state,
    start_container,
    valid_container_name,
)

RUNTIME = "/usr/bin/podman"  # An absolute path, which is what `find_runtime` returns.


def _finished(returncode: int, stdout: str = "", stderr: str = "") -> Any:
    """Build a stand-in for a finished child process.

    Args:
        returncode: The exit status the runtime reported.
        stdout: The text the runtime printed.
        stderr: The error text the runtime printed.

    Returns:
        An object with the three fields the module reads.
    """
    result = MagicMock()  # WHY: the module reads three attributes and nothing else.
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestValidContainerName:
    """Cover the name guard, which keeps a crafted name out of the argument list."""

    @pytest.mark.parametrize("name", ["misthelper-arangodb", "misthelper_redis", "a", "app.1"])
    def test_accepts_a_plain_name(self, name: str) -> None:
        """A name of letters, digits, and the three joining marks is safe."""
        assert valid_container_name(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "-flag",  # WHY: a leading hyphen would read as a runtime option.
            "two words",  # WHY: a space would split into two arguments.
            "semi;colon",  # WHY: a shell character, refused even though no shell runs.
            "",  # WHY: an empty name names nothing.
            "a" * 64,  # WHY: longer than the pattern allows.
        ],
    )
    def test_refuses_an_unsafe_name(self, name: str) -> None:
        """A name that could read as an option or a second command is refused."""
        assert valid_container_name(name) is False


class TestFindRuntime:
    """Cover the runtime search, which prefers Podman."""

    def test_prefers_podman_when_both_exist(self) -> None:
        """The project documents Podman first, so Podman wins."""
        with patch.object(containers.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"):
            assert find_runtime() == "/usr/bin/podman"

    def test_falls_back_to_docker(self) -> None:
        """A host with Docker alone still gets a runtime."""
        with patch.object(containers.shutil, "which", side_effect=lambda name: None if name == "podman" else "/d"):
            assert find_runtime() == "/d"

    def test_returns_none_when_no_runtime_exists(self) -> None:
        """A host with neither runtime must report the gap, not raise."""
        with patch.object(containers.shutil, "which", return_value=None):
            assert find_runtime() is None


class TestReadContainerState:
    """Cover every state the runtime can report."""

    def test_reports_running(self) -> None:
        """The word `running` is the one word that means the service is up."""
        with patch.object(containers.subprocess, "run", return_value=_finished(0, "running\n")):
            assert read_container_state("misthelper-redis", RUNTIME) is ContainerState.RUNNING

    @pytest.mark.parametrize("word", ["exited", "created", "paused"])
    def test_reports_stopped_for_every_other_word(self, word: str) -> None:
        """Any state that is not `running` is a container the portal may start."""
        with patch.object(containers.subprocess, "run", return_value=_finished(0, f"{word}\n")):
            assert read_container_state("misthelper-redis", RUNTIME) is ContainerState.STOPPED

    def test_reports_missing_on_a_non_zero_exit(self) -> None:
        """Both runtimes answer non-zero when no container carries the name."""
        with patch.object(containers.subprocess, "run", return_value=_finished(125, "", "no such container")):
            assert read_container_state("misthelper-redis", RUNTIME) is ContainerState.MISSING

    def test_reports_unknown_for_an_unsafe_name(self) -> None:
        """The name guard runs before the runtime call, so no process starts."""
        with patch.object(containers.subprocess, "run") as run_spy:
            assert read_container_state("-flag", RUNTIME) is ContainerState.UNKNOWN
        run_spy.assert_not_called()

    @pytest.mark.parametrize("error", [OSError("no such file"), subprocess.TimeoutExpired("podman", 10)])
    def test_reports_unknown_when_the_command_cannot_run(self, error: Exception) -> None:
        """A dead runtime and a slow runtime both leave the portal without an answer."""
        with patch.object(containers.subprocess, "run", side_effect=error):
            assert read_container_state("misthelper-redis", RUNTIME) is ContainerState.UNKNOWN

    def test_passes_a_list_and_never_a_shell(self) -> None:
        """A list with no shell is what stops an argument becoming a second command."""
        with patch.object(containers.subprocess, "run", return_value=_finished(0, "running")) as run_spy:
            read_container_state("misthelper-redis", RUNTIME)
        args, kwargs = run_spy.call_args
        assert args[0] == [RUNTIME, "inspect", "--format", "{{.State.Status}}", "misthelper-redis"]
        assert kwargs["shell"] is False


class TestStartContainer:
    """Cover the start path and each refusal."""

    def test_returns_true_on_success(self) -> None:
        """A zero exit means the runtime accepted the start."""
        with patch.object(containers.subprocess, "run", return_value=_finished(0)):
            assert start_container("misthelper-redis", RUNTIME) is True

    def test_returns_false_when_the_runtime_refuses(self) -> None:
        """A non-zero exit must report false, and the reason reaches the log."""
        with patch.object(containers.subprocess, "run", return_value=_finished(1, "", "port is in use")):
            assert start_container("misthelper-redis", RUNTIME) is False

    def test_refuses_an_unsafe_name_before_starting_a_process(self) -> None:
        """The name guard runs first, so a crafted name never reaches the runtime."""
        with patch.object(containers.subprocess, "run") as run_spy:
            assert start_container("; rm -rf /", RUNTIME) is False
        run_spy.assert_not_called()

    def test_returns_false_when_the_command_cannot_run(self) -> None:
        """A dead runtime must report false, not raise into the sign-in page."""
        with patch.object(containers.subprocess, "run", side_effect=OSError("boom")):
            assert start_container("misthelper-redis", RUNTIME) is False

    def test_runs_only_the_start_verb(self) -> None:
        """The module starts a container. It never creates, pulls, or removes one."""
        with patch.object(containers.subprocess, "run", return_value=_finished(0)) as run_spy:
            start_container("misthelper-redis", RUNTIME)
        assert run_spy.call_args[0][0] == [RUNTIME, "start", "misthelper-redis"]
