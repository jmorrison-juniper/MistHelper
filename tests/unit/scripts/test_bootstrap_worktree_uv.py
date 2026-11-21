"""Prove the bootstrap finds uv in each supported place and names a lock failure.

A Windows host kept uv in a per-user folder, outside PATH. The bootstrap then
tried to install uv with pip into an externally managed Python, and that install
failed. A lock that did not match the configured index failed without a cause.
See issue #4876.

These tests replace every process and every lookup, so they need no network and
no installed uv. Each test pins one rule of the search, of the install guard, or
of the cause text.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import bootstrap_worktree as bootstrap
from scripts.bootstrap_worktree import (
    EXTERNALLY_MANAGED_MESSAGE,
    INDEX_MISMATCH_MESSAGE,
    LOCK_DRIFT_MESSAGE,
    PUBLIC_INDEX_URL,
    UV_EXECUTABLE_NAME,
    WorktreeBootstrapper,
    build_parser,
    find_uv_command,
    normalize_index,
    read_lock_registry,
)

LOGGER = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.
INTERPRETER = "C:/Python/python.exe"  # A fixed interpreter path keeps the command lists readable.
MIRROR_URL = "https://mirror.example.test/simple/"  # A non-public index that the lock does not name.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class ScriptedRun:
    """Record each subprocess call and answer with the next scripted return code."""

    def __init__(self, codes: tuple[int, ...] = ()) -> None:
        """Store the return codes that the next calls return, in order."""
        self.codes = list(codes)  # Pop one code for each call, and return zero after the list ends.
        self.commands: list[list[str]] = []  # Keep every argument list, so a test can assert the order.
        self.environments: list[dict[str, str] | None] = []  # Copy each child environment at call time.

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Record the call and return the scripted result."""
        self.commands.append(list(command))  # Copy the argument list, so a later edit cannot change the record.
        env = kwargs.get("env")  # Read the child environment that the code under test passed.
        self.environments.append(dict(env) if isinstance(env, dict) else None)  # Keep a copy for the assertions.
        code = self.codes.pop(0) if self.codes else 0  # Return success after the scripted codes end.
        return subprocess.CompletedProcess(command, code, stdout="", stderr="")


def _fail_if_called(*args: object, **kwargs: object) -> bool:
    """Fail the test when a probe runs that the rule under test must skip."""
    raise AssertionError("This probe must not run for this rule.")


def _failing_sync(command: list[str], environment: dict[str, str], context: str, root: Path | None = None) -> None:
    """Stand in for the locked sync, and fail it the way uv fails on a lock mismatch."""
    raise RuntimeError(f"{context} failed with code 1.")


def _write_lock(root: Path, registry: str) -> None:
    """Write a minimal uv.lock whose package entry names one registry."""
    lock_text = f'[[package]]\nsource = {{ registry = "{registry}" }}\n'  # Match the line shape that uv writes.
    (root / "uv.lock").write_text(lock_text, encoding="utf-8")
    LOGGER.info("Wrote a lockfile that names %s", registry)


def _policy_with_uv() -> WorktreeBootstrapper.InstallationPolicy:
    """Return a policy whose uv command already exists, so only the sync path runs."""
    return WorktreeBootstrapper.InstallationPolicy(["C:/Tools/uv.exe"], {}, None, INTERPRETER)


# ---------------------------------------------------------------------------
# Search order
# ---------------------------------------------------------------------------


def test_find_uv_command_prefers_the_path_installation(monkeypatch: pytest.MonkeyPatch) -> None:
    """A uv executable on PATH is used before any per-user folder or module."""
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "C:/Tools/uv.exe" if name == "uv" else None)
    monkeypatch.setattr(bootstrap, "module_runs_uv", _fail_if_called)  # PATH answered, so no probe may run.
    assert find_uv_command(INTERPRETER) == ["C:/Tools/uv.exe"]


def test_find_uv_command_uses_a_per_user_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A uv executable in a per-user folder is used when PATH does not hold uv."""
    folder = tmp_path / "Scripts"  # A stand-in for the pip --user scripts folder.
    folder.mkdir()
    (folder / UV_EXECUTABLE_NAME).write_bytes(b"")  # The file name is the only fact that the search reads.
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)
    monkeypatch.setattr(bootstrap, "uv_candidate_folders", lambda: [folder])
    monkeypatch.setattr(bootstrap, "module_runs_uv", _fail_if_called)  # The folder answered, so no probe may run.
    assert find_uv_command(INTERPRETER) == [str(folder / UV_EXECUTABLE_NAME)]


def test_find_uv_command_falls_back_to_the_bootstrap_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bootstrap interpreter runs uv as a module when no executable is found."""
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)
    monkeypatch.setattr(bootstrap, "uv_candidate_folders", lambda: [])
    monkeypatch.setattr(bootstrap, "module_runs_uv", lambda interpreter: interpreter == INTERPRETER)
    assert find_uv_command(INTERPRETER) == [INTERPRETER, "-m", "uv"]


def test_find_uv_command_reports_absence_when_nothing_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    """No PATH entry, no folder, and no module means the caller must decide about an install."""
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)
    monkeypatch.setattr(bootstrap, "uv_candidate_folders", lambda: [])
    monkeypatch.setattr(bootstrap, "module_runs_uv", lambda interpreter: False)
    assert find_uv_command(INTERPRETER) is None


def test_module_probe_treats_a_launch_failure_as_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A probe that cannot start the interpreter reports the module as absent."""

    def broken_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Raise the launch error that a missing interpreter raises."""
        raise OSError("the interpreter cannot start")

    monkeypatch.setattr(bootstrap.subprocess, "run", broken_run)
    assert bootstrap.module_runs_uv(INTERPRETER) is False


def test_module_probe_accepts_a_zero_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """A zero exit code from the version command means the module runs uv."""
    runner = ScriptedRun(codes=(0,))
    monkeypatch.setattr(bootstrap.subprocess, "run", runner)
    assert bootstrap.module_runs_uv(INTERPRETER) is True
    assert runner.commands == [[INTERPRETER, "-m", "uv", "--version"]]


def test_user_folder_search_uses_the_per_user_scheme_of_this_platform() -> None:
    """The first folder that the search reads is the per-user scripts folder of the platform."""
    scheme = "nt_user" if bootstrap.os.name == "nt" else "posix_user"  # The scheme that pip --user uses.
    expected = Path(bootstrap.sysconfig.get_path("scripts", scheme))
    assert bootstrap.uv_candidate_folders()[0] == expected


def test_windows_user_folder_does_not_depend_on_appdata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A shell that hides APPDATA still finds the Windows per-user folder under the profile."""
    monkeypatch.setattr(bootstrap.os, "name", "nt")  # Take the Windows branch on any host.
    monkeypatch.setenv("APPDATA", "")  # The shell that runs the bootstrap may hide APPDATA.
    monkeypatch.setattr(
        bootstrap.Path, "home", classmethod(lambda cls: tmp_path)
    )  # Point the profile at the temp folder.
    expected = tmp_path / "AppData" / "Roaming" / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}"
    assert expected / "Scripts" in bootstrap.uv_candidate_folders()


# ---------------------------------------------------------------------------
# Install guard
# ---------------------------------------------------------------------------


def test_install_uv_refuses_pip_in_an_externally_managed_python(monkeypatch: pytest.MonkeyPatch) -> None:
    """pip never starts when the interpreter is externally managed, and the error names the next action."""
    runner = ScriptedRun()
    monkeypatch.setattr(bootstrap, "is_externally_managed", lambda: True)
    monkeypatch.setattr(bootstrap.subprocess, "run", runner)
    policy = WorktreeBootstrapper.InstallationPolicy(None, {}, None, INTERPRETER)
    with pytest.raises(RuntimeError, match="externally managed") as raised:
        policy.install_uv({})
    assert str(raised.value) == EXTERNALLY_MANAGED_MESSAGE
    assert runner.commands == []  # No install command may start, because pip would fail by design.


def test_install_uv_runs_pip_when_the_python_allows_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Python without the marker keeps the per-user pip install of uv."""
    runner = ScriptedRun()
    monkeypatch.setattr(bootstrap, "is_externally_managed", lambda: False)
    monkeypatch.setattr(bootstrap.subprocess, "run", runner)
    policy = WorktreeBootstrapper.InstallationPolicy(None, {}, None, INTERPRETER)
    policy.install_uv({})
    assert runner.commands == [[INTERPRETER, "-m", "pip", "install", "--user", "uv"]]


def test_install_uv_is_skipped_when_uv_was_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """An existing uv command starts no installation at all."""
    runner = ScriptedRun()
    monkeypatch.setattr(bootstrap.subprocess, "run", runner)
    _policy_with_uv().install_uv({})
    assert runner.commands == []


def test_is_externally_managed_reads_the_pep_668_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The marker file in the standard library is the only signal that the guard reads."""
    real_get_path = bootstrap.sysconfig.get_path

    def stdlib_in_tmp(name: str, *args: object, **kwargs: object) -> str:
        """Point the standard library at the temporary folder and leave other paths alone."""
        return str(tmp_path) if name == "stdlib" else real_get_path(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(bootstrap.sysconfig, "get_path", stdlib_in_tmp)
    assert bootstrap.is_externally_managed() is False
    (tmp_path / "EXTERNALLY-MANAGED").write_text("", encoding="utf-8")
    assert bootstrap.is_externally_managed() is True


# ---------------------------------------------------------------------------
# Lock cause and the public option
# ---------------------------------------------------------------------------


def test_sync_names_an_index_mismatch_without_the_mirror_address(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mirror that differs from the lock is named as the cause, and its address stays out of the message."""
    _write_lock(tmp_path, PUBLIC_INDEX_URL)
    policy = _policy_with_uv()
    monkeypatch.setattr(policy, "_run", _failing_sync)  # The locked sync fails.
    monkeypatch.setattr(policy, "lock_is_current", lambda root, env: False)  # The lock check reports a stale lock.
    with pytest.raises(RuntimeError) as raised:
        policy.sync(tmp_path, {"UV_INDEX_URL": MIRROR_URL})
    assert str(raised.value) == INDEX_MISMATCH_MESSAGE
    assert "mirror.example.test" not in str(raised.value)  # The internal address must not reach the console.
    assert "--public-lock-index" in str(raised.value)  # The message names the repair option.


def test_sync_names_lock_drift_when_the_indexes_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stale lock on the index that the lock names is reported as drift, not as a mirror problem."""
    _write_lock(tmp_path, PUBLIC_INDEX_URL)
    policy = _policy_with_uv()
    monkeypatch.setattr(policy, "_run", _failing_sync)
    monkeypatch.setattr(policy, "lock_is_current", lambda root, env: False)
    with pytest.raises(RuntimeError) as raised:
        policy.sync(tmp_path, {"UV_INDEX_URL": PUBLIC_INDEX_URL})
    assert str(raised.value) == LOCK_DRIFT_MESSAGE


@pytest.mark.parametrize("verdict", (True, None), ids=("current-lock", "unknown-verdict"))
def test_sync_keeps_the_original_error_when_the_lock_has_no_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verdict: bool | None
) -> None:
    """A current lock, or a lock check that cannot run, leaves the original failure unchanged."""
    _write_lock(tmp_path, PUBLIC_INDEX_URL)
    policy = _policy_with_uv()
    monkeypatch.setattr(policy, "_run", _failing_sync)
    monkeypatch.setattr(policy, "lock_is_current", lambda root, env: verdict)
    with pytest.raises(RuntimeError, match="The locked UV sync failed with code 1.") as raised:
        policy.sync(tmp_path, {"UV_INDEX_URL": MIRROR_URL})
    assert str(raised.value) == "The locked UV sync failed with code 1."


def test_public_lock_index_points_only_this_run_at_the_public_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The option removes every competing index source from the child and keeps the lock check honest."""
    runner = ScriptedRun(codes=(0,))
    monkeypatch.setattr(bootstrap.subprocess, "run", runner)
    environment = {
        "UV_INDEX_URL": MIRROR_URL,
        "UV_DEFAULT_INDEX": MIRROR_URL,
        "UV_INDEX": "https://extra.example.test/simple/",
        "UV_EXTRA_INDEX_URL": "https://extra.example.test/simple/",
    }
    _policy_with_uv().sync(tmp_path, environment, public_lock_index=True)
    child_environment = runner.environments[0] or {}  # An absent copy becomes empty, so the next line names the missing key.
    assert child_environment.get("UV_INDEX_URL") == PUBLIC_INDEX_URL  # The public index must be the only index for this run.
    for name in ("UV_DEFAULT_INDEX", "UV_INDEX", "UV_EXTRA_INDEX_URL"):
        assert name not in child_environment  # No competing source may survive the public choice.


def test_public_lock_index_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser keeps the mirror unless the operator passes the option."""
    assert build_parser().parse_args([]).public_lock_index is False
    assert build_parser().parse_args(["--public-lock-index"]).public_lock_index is True


# ---------------------------------------------------------------------------
# Lock registry reader
# ---------------------------------------------------------------------------


def test_read_lock_registry_returns_the_first_registry(tmp_path: Path) -> None:
    """The first registry line names the index, even when a later line names another one."""
    lock = tmp_path / "uv.lock"
    lock.write_text(
        'source = { registry = "https://pypi.org/simple" }\nsource = { registry = "https://other.example/simple" }\n',
        encoding="utf-8",
    )
    assert read_lock_registry(lock) == PUBLIC_INDEX_URL


def test_read_lock_registry_returns_none_when_the_lock_names_no_registry(tmp_path: Path) -> None:
    """A lockfile without a registry line, or without a file, leaves the registry unknown."""
    empty = tmp_path / "empty.lock"
    empty.write_text("version = 1\n", encoding="utf-8")
    assert read_lock_registry(empty) is None
    assert read_lock_registry(tmp_path / "missing.lock") is None


def test_normalize_index_ignores_case_and_a_trailing_slash() -> None:
    """Two spellings of one index compare equal, so a slash alone never causes a false mismatch."""
    assert normalize_index("https://PyPI.org/simple/") == normalize_index(PUBLIC_INDEX_URL)
