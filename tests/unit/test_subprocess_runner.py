"""Unit tests for src.utils.subprocess_runner.SubprocessRunner.

Covers the audited dispatch path and every validator branch so that the
central B404/B603 justification remains trustworthy:

- Argv validation: empty sequence, non-allow-listed executable, non-str
  element, empty-string element, disallowed-character element.
- Executable allow-list: sys.executable exact-match, uv/uv.exe basename
  match (including nested venv path), rejected 'python3' basename.
- Timeout validation: bool rejection, non-numeric rejection, NaN, +inf,
  zero, negative.
- Dispatch success: CompletedProcess round-trip via a mocked subprocess.run.
- Dispatch failures: TimeoutExpired + CalledProcessError propagation with
  argv[1:] elided from log records.
- check=False: caller inspects non-zero returncode without exception.
"""

from __future__ import annotations  # PEP 604 unions.

import logging  # Capture Principle VII before/after log lines.
import math  # NaN + inf constants for timeout validation tests.
import os  # Path construction for basename allow-list scenarios.
import subprocess  # Real exception classes for propagation tests.
import sys  # sys.executable for the fast-path allow-list case.
from unittest.mock import patch  # Stub subprocess.run to avoid real spawn.

import pytest  # Fixtures + expected-exception assertions.

from src.utils.subprocess_runner import (  # System under test + re-exports.
    CalledProcessError,
    SubprocessError,
    SubprocessRunner,
    TimeoutExpired,
)

# ---------------------------------------------------------------------------
# _validate_argv
# ---------------------------------------------------------------------------


def test_run_rejects_empty_argv():
    """Empty sequences fail before any spawn attempt."""
    with pytest.raises(ValueError, match="non-empty sequence"):
        SubprocessRunner.run([], timeout=1.0)  # Empty list is never legitimate.


def test_run_rejects_disallowed_executable():
    """Executables outside the allow-list raise before any spawn."""
    with pytest.raises(ValueError, match="not an allowed executable"):
        SubprocessRunner.run(["python3", "-V"], timeout=1.0)  # Not on allow-list.


def test_run_rejects_non_string_argv_element():
    """Non-str argv elements would bypass the char allow-list; must reject."""
    with pytest.raises(ValueError, match=r"argv\[1\] must be a str"):
        SubprocessRunner.run(["uv", 123], timeout=1.0)  # type: ignore[list-item]


def test_run_rejects_empty_string_argv_element():
    """Empty-string args are almost certainly a caller bug."""
    with pytest.raises(ValueError, match=r"argv\[1\] must be non-empty"):
        SubprocessRunner.run(["uv", ""], timeout=1.0)  # Empty arg.


def test_run_rejects_disallowed_characters_in_argv():
    """Shell metacharacters must be rejected up-front."""
    with pytest.raises(ValueError, match="disallowed characters"):
        SubprocessRunner.run(["uv", "pip; rm -rf /"], timeout=1.0)  # Semicolon banned.


def test_run_rejects_pipe_in_argv():
    """Pipe character is not in the conservative allow-list."""
    with pytest.raises(ValueError, match="disallowed characters"):
        SubprocessRunner.run(["uv", "a|b"], timeout=1.0)  # Pipe is banned.


# ---------------------------------------------------------------------------
# _is_allowed_executable
# ---------------------------------------------------------------------------


def test_sys_executable_is_allowed():
    """The running interpreter must be usable for '-m pip ...' style calls."""
    assert SubprocessRunner._is_allowed_executable(sys.executable)  # Exact match.


def test_uv_basename_is_allowed():
    """Bare 'uv' basename is permitted."""
    assert SubprocessRunner._is_allowed_executable("uv")  # Direct name.


def test_uv_exe_basename_is_allowed():
    """Windows 'uv.exe' basename is permitted."""
    assert SubprocessRunner._is_allowed_executable("uv.exe")  # Windows form.


def test_uv_in_nested_path_is_allowed():
    """Full paths that end in an allow-listed basename are permitted."""
    nested = os.path.join("some", "venv", "bin", "uv")  # Simulated venv path.
    assert SubprocessRunner._is_allowed_executable(nested)  # Basename match.


def test_python3_basename_is_rejected():
    """Bare 'python3' is not on the allow-list."""
    assert not SubprocessRunner._is_allowed_executable("python3")  # Not allow-listed.


# ---------------------------------------------------------------------------
# _validate_timeout
# ---------------------------------------------------------------------------


def test_run_rejects_bool_timeout():
    """bool is a subclass of int in Python; reject explicitly."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout=True)  # type: ignore[arg-type]


def test_run_rejects_non_numeric_timeout():
    """Strings and other non-numerics fail the isinstance check."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout="1.0")  # type: ignore[arg-type]


def test_run_rejects_nan_timeout():
    """NaN is not a valid deadline."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout=math.nan)  # NaN.


def test_run_rejects_infinite_timeout():
    """Positive infinity is not a valid deadline."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout=math.inf)  # +inf.


def test_run_rejects_zero_timeout():
    """Zero timeouts trip subprocess.run behaviour we don't want."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout=0)  # Zero.


def test_run_rejects_negative_timeout():
    """Negative timeouts are always a caller bug."""
    with pytest.raises(ValueError, match="positive finite number"):
        SubprocessRunner.run(["uv", "--version"], timeout=-5.0)  # Negative.


# ---------------------------------------------------------------------------
# Successful dispatch
# ---------------------------------------------------------------------------


def test_run_dispatches_and_returns_completed_process(caplog):
    """A valid call reaches subprocess.run and returns its CompletedProcess."""
    fake = subprocess.CompletedProcess(args=["uv", "--version"], returncode=0, stdout="uv 0.0.0\n", stderr="")
    with patch("subprocess.run", return_value=fake) as spy, caplog.at_level(logging.INFO):
        result = SubprocessRunner.run(["uv", "--version"], timeout=5.0)  # Happy path.
    assert result is fake  # Same object returned untouched.
    spy.assert_called_once()  # Exactly one subprocess.run dispatch.
    kwargs = spy.call_args.kwargs  # Verify pinned keyword arguments.
    assert kwargs["capture_output"] is True  # Always captured.
    assert kwargs["text"] is True  # Always decoded.
    assert kwargs["timeout"] == 5.0  # Timeout propagated.
    assert kwargs["check"] is True  # Default check policy preserved.
    assert "dispatching" in caplog.text  # Principle VII before-action log emitted.


def test_run_passes_check_false_through_to_subprocess():
    """check=False lets the caller inspect non-zero returncodes."""
    fake = subprocess.CompletedProcess(args=["uv", "pip"], returncode=1, stdout="", stderr="err")
    with patch("subprocess.run", return_value=fake) as spy:
        result = SubprocessRunner.run(["uv", "pip"], timeout=5.0, check=False)  # check=False path.
    assert result.returncode == 1  # Non-zero rc surfaces without exception.
    assert spy.call_args.kwargs["check"] is False  # Forwarded verbatim.


def test_run_copies_argv_to_plain_list():
    """The argv passed to subprocess.run is a fresh list, not the caller's sequence."""
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    caller_argv = ["uv", "--version"]  # Sequence retained by caller.
    with patch("subprocess.run", return_value=fake) as spy:
        SubprocessRunner.run(caller_argv, timeout=1.0)  # Normal dispatch.
    forwarded = spy.call_args.args[0]  # First positional arg to subprocess.run.
    assert forwarded == caller_argv  # Same contents.
    assert forwarded is not caller_argv  # But a distinct object (no aliasing).


# ---------------------------------------------------------------------------
# Failure propagation
# ---------------------------------------------------------------------------


def test_run_propagates_timeout_expired(caplog):
    """TimeoutExpired is re-raised and logged without argv[1:]."""
    exc = subprocess.TimeoutExpired(cmd=["uv", "secret-value"], timeout=1.0)  # Simulated timeout.
    with patch("subprocess.run", side_effect=exc), caplog.at_level(logging.ERROR):
        with pytest.raises(TimeoutExpired):
            SubprocessRunner.run(["uv", "secret-value"], timeout=1.0)  # Trigger timeout path.
    assert "timed out" in caplog.text  # Error log emitted.
    assert "secret-value" not in caplog.text  # argv[1:] never logged (secret safety).


def test_run_propagates_called_process_error(caplog):
    """CalledProcessError from check=True is re-raised and logged with rc only."""
    exc = subprocess.CalledProcessError(returncode=2, cmd=["uv", "secret-value"])  # Simulated failure.
    with patch("subprocess.run", side_effect=exc), caplog.at_level(logging.ERROR):
        with pytest.raises(CalledProcessError):
            SubprocessRunner.run(["uv", "secret-value"], timeout=1.0)  # check=True default.
    assert "failed" in caplog.text  # Error log emitted.
    assert "rc=2" in caplog.text  # Return code surfaced.
    assert "secret-value" not in caplog.text  # argv[1:] never logged (secret safety).


# ---------------------------------------------------------------------------
# Re-exports
# ---------------------------------------------------------------------------


def test_reexports_are_subprocess_types():
    """The re-exported exception classes are the real subprocess symbols."""
    assert CalledProcessError is subprocess.CalledProcessError  # Same class.
    assert TimeoutExpired is subprocess.TimeoutExpired  # Same class.
    assert SubprocessError is subprocess.SubprocessError  # Same class.


def test_allowed_executables_attribute_includes_sys_executable():
    """ALLOWED_EXECUTABLES advertises sys.executable for discoverability."""
    assert sys.executable in SubprocessRunner.ALLOWED_EXECUTABLES  # Includes interpreter.
    assert "uv" in SubprocessRunner.ALLOWED_EXECUTABLES  # Includes uv basename.
    assert "uv.exe" in SubprocessRunner.ALLOWED_EXECUTABLES  # Includes Windows form.
