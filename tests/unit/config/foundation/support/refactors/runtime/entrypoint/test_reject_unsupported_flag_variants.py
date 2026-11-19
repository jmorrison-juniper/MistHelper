"""Regression tests for command-line parsing through `MainEntrypoint.run`."""

from __future__ import annotations  # WHY: Keep annotations lazy for the test module.

import argparse  # WHY: Build the parser double used by the parse-once regression test.
import json  # WHY: Decode the fresh-interpreter side-effect report.
import subprocess  # WHY: Start a fresh interpreter so import state cannot leak from conftest.
import sys  # WHY: Reuse the active test interpreter for subprocess checks.
from pathlib import Path  # WHY: Build repository paths without hardcoded separators.
from typing import Any  # WHY: Type the mixed parser arguments in the test double.

import pytest  # WHY: Use pytest fixtures and SystemExit assertions.

from src.foundation.support.refactors.main_entrypoint import MainEntrypoint  # WHY: Test the public CLI path.

_REPOSITORY_ROOT = Path(__file__).resolve().parents[8]  # WHY: Locate the worktree root from this nested test file.


def test_import_misthelper_has_no_startup_side_effects() -> None:
    """Importing `MistHelper` must not run the bootstrap side effects."""
    script = """
import json
import logging
import os
import platform
import socket
import subprocess

events = []
watched_env = {
    "CONSOLE_LOG_LEVEL",
    "LOGGING_LOG_LEVEL",
    "DISABLE_AUTO_INSTALL",
    "DISABLE_UV_CHECK",
    "MIST_SITE_EXCLUDE_PREFIX",
}
real_getenv = os.getenv
real_environ_get = os.environ.get
platform.uname()

def record(event, value):
    events.append([event, str(value)])

def guarded_getenv(key, default=None):
    if key in watched_env:
        record("getenv", key)
    return real_getenv(key, default)

def guarded_environ_get(key, default=None):
    if key in watched_env:
        record("environ.get", key)
    return real_environ_get(key, default)

def guarded_basic_config(*args, **kwargs):
    record("basicConfig", len(args) + len(kwargs))

def guarded_makedirs(path, *args, **kwargs):
    record("makedirs", path)

def guarded_create_connection(*args, **kwargs):
    record("socket.create_connection", len(args) + len(kwargs))
    raise AssertionError("network connection during import")

def guarded_run(*args, **kwargs):
    record("subprocess.run", len(args) + len(kwargs))
    raise AssertionError("subprocess during import")

os.getenv = guarded_getenv
os.environ.get = guarded_environ_get
os.makedirs = guarded_makedirs
logging.basicConfig = guarded_basic_config
socket.create_connection = guarded_create_connection
subprocess.run = guarded_run
import MistHelper
print(json.dumps(events))
"""  # WHY: Patch the listed side-effect APIs before a fresh import.
    result = subprocess.run(  # WHY: Run in a fresh process so previous imports do not hide side effects.
        [sys.executable, "-c", script],  # WHY: Use the active venv interpreter and inline probe script.
        cwd=_REPOSITORY_ROOT,  # WHY: Match normal project-root import behavior.
        check=True,  # WHY: Surface import failures as test failures.
        capture_output=True,  # WHY: Read the JSON event report without polluting pytest output.
        text=True,  # WHY: Decode stdout as text for json.loads.
    )
    events = json.loads(result.stdout.strip())  # WHY: Convert the probe report into a Python list.
    assert events == []  # WHY: Import must not run startup side effects.


class CountingParser(argparse.ArgumentParser):
    """Parser double that records how many times startup parses arguments."""

    def __init__(self, parsed_args: argparse.Namespace) -> None:
        super().__init__(description="Counting parser")  # WHY: Keep normal argparse behavior available if needed.
        self.parsed_args = parsed_args  # WHY: Return one stable Namespace to prove bootstrap stores it.
        self.parse_count = 0  # WHY: Count parser calls for the regression assertion.

    def parse_args(self, args: Any = None, namespace: Any = None) -> argparse.Namespace:
        self.parse_count += 1  # WHY: Detect any second parse inside the bootstrap path.
        return self.parsed_args  # WHY: Let the test compare object identity after parsing.


class _StartupReachedError(Exception):
    """Stop `MainEntrypoint.run` at the first startup side effect."""


def test_main_entrypoint_parses_command_line_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI path must parse the command line once and reuse that Namespace."""
    parsed_args = argparse.Namespace(skip_deps=True, test=False, testinteractive=False)  # WHY: Minimal stored result.
    parser = CountingParser(parsed_args)  # WHY: Count parse calls without running real argparse behavior.
    stored_namespaces: list[argparse.Namespace] = []  # WHY: Capture the Namespace that startup receives.

    def stop_at_startup(bootstrap: Any) -> None:
        """Record the stored Namespace, then stop before any startup side effect."""
        stored_namespaces.append(bootstrap.parsed_args)  # WHY: Later startup must reuse this object.
        raise _StartupReachedError  # WHY: Skip logging, dependency, and session work in this unit test.

    monkeypatch.setattr("MistHelper._build_argument_parser", lambda: parser)  # WHY: Use the parser double.
    monkeypatch.setattr(  # WHY: Stop the bootstrap at its first side-effect boundary.
        "src.foundation.support.refactors.main_entrypoint.ApplicationBootstrap._run_common_startup", stop_at_startup
    )
    monkeypatch.setattr(sys, "argv", ["MistHelper.py", "--skip-deps"])  # WHY: The CLI reads process arguments.
    with pytest.raises(_StartupReachedError):  # WHY: The stub ends the run after the parse is stored.
        MainEntrypoint.run()  # WHY: Exercise the public path that owns the single parse.
    assert parser.parse_count == 1  # WHY: The command line must be parsed exactly one time.
    assert len(stored_namespaces) == 1  # WHY: Startup must receive exactly one stored Namespace.
    assert stored_namespaces[0] is parsed_args  # WHY: Later startup must reuse the stored Namespace object.


def test_hyphenated_test_flag_uses_standard_argparse_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A misspelled flag must fail through argparse with status code 2."""
    monkeypatch.setattr(sys, "argv", ["MistHelper.py", "--test-interactive"])  # WHY: Set the CLI argv.
    with pytest.raises(SystemExit) as excinfo:  # WHY: argparse exits on an unsupported option.
        MainEntrypoint.run()  # WHY: The public entry point must reach the real parser before startup work.
    captured = capsys.readouterr()  # WHY: Inspect the user-facing parser error.
    assert excinfo.value.code == 2  # WHY: argparse uses exit code 2 for usage errors.
    assert "unrecognized arguments" in captured.err  # WHY: The standard parser error must own this failure.
    assert "Did you mean" not in captured.err  # WHY: The removed compatibility guard must not run.
