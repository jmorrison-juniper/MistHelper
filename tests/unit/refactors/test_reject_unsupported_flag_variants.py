"""Regression tests for command-line parsing in the explicit bootstrap."""

from __future__ import annotations  # WHY: Keep annotations lazy for the test module.

import argparse  # WHY: Build the parser double used by the parse-once regression test.
import json  # WHY: Decode the fresh-interpreter side-effect report.
import subprocess  # WHY: Start a fresh interpreter so import state cannot leak from conftest.
import sys  # WHY: Reuse the active test interpreter for subprocess checks.
from pathlib import Path  # WHY: Build repository paths without hardcoded separators.
from typing import Any  # WHY: Type the mixed parser arguments in the test double.

import pytest  # WHY: Use pytest fixtures and SystemExit assertions.

from src.refactors.main_entrypoint import ApplicationBootstrap  # WHY: Exercise the new bootstrap seam directly.

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # WHY: Locate the worktree root from this nested test file.


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


def test_application_bootstrap_parses_command_line_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bootstrap must store the only parsed command-line namespace."""
    parsed_args = argparse.Namespace(skip_deps=True, test=False, testinteractive=False)  # WHY: Minimal stored result.
    parser = CountingParser(parsed_args)  # WHY: Count parse calls without running real argparse behavior.
    monkeypatch.setattr(  # WHY: Route bootstrap to the parser double.
        "MistHelper._build_argument_parser", lambda: parser
    )
    bootstrap = ApplicationBootstrap(argv=["--skip-deps"])  # WHY: Constructing bootstrap is the only parse location.
    assert parser.parse_count == 1  # WHY: The command line must be parsed exactly one time.
    assert bootstrap.parsed_args is parsed_args  # WHY: Later startup must reuse the stored Namespace object.


def test_hyphenated_test_flag_uses_standard_argparse_error(capsys: pytest.CaptureFixture[str]) -> None:
    """A misspelled flag must fail through argparse with status code 2."""
    with pytest.raises(SystemExit) as excinfo:  # WHY: argparse exits on an unsupported option.
        ApplicationBootstrap(argv=["--test-interactive"])  # WHY: The removed raw variant guard no longer runs.
    captured = capsys.readouterr()  # WHY: Inspect the user-facing parser error.
    assert excinfo.value.code == 2  # WHY: argparse uses exit code 2 for usage errors.
    assert "unrecognized arguments" in captured.err  # WHY: The standard parser error must own this failure.
    assert "Did you mean" not in captured.err  # WHY: The removed compatibility guard must not run.


def test_observable_failure_mode_contracts() -> None:
    """Failure-mode contracts stay explicit for this test module."""
    from tests.support import failure_mode_observations as failure_modes  # Import shared contracts.

    failure_modes.assert_http_status_observation(400)  # HTTP 4xx status stays observable.
    failure_modes.assert_http_status_observation(500)  # HTTP 5xx status stays observable.
