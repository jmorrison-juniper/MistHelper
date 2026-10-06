"""Unit tests for the bounded portal start wait used by browser tests.

Why:
    The browser fixture starts a child process before Playwright opens a page.
    These tests replace the port and process seams, so they start no process,
    bind no port, open no browser, and make no Mist request.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from tests.e2e.upgrade_portal import conftest as portal


class StandInProcess:
    """Return a controlled sequence of child process states."""

    def __init__(self, states: Iterator[int | None]) -> None:
        """Store the process states that each poll must return."""
        self._states = states  # Keep one deterministic process state sequence for the test.

    def poll(self) -> int | None:
        """Return the next child process state."""
        return next(self._states)  # A finite sequence makes an unexpected extra poll fail.


def _clock(*values: float) -> Iterator[float]:
    """Return the monotonic clock values for one wait path."""
    return iter(values)  # Each wait path states each clock read in its test.


def test_wait_for_port_reports_ready_before_the_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ready listener returns its measured startup time."""
    probes = iter((False, True))  # The first probe waits, and the second probe finds the portal.
    sleeps: list[float] = []  # Record the pause instead of delaying the unit test.
    clock = _clock(10.0, 10.5)  # The portal becomes ready after one half-second pause.
    process = StandInProcess(iter((None,)))  # The child stays live while its first import completes.
    monkeypatch.setattr(portal, "_probe_port", lambda _port: next(probes))  # Keep all network access mocked.
    monkeypatch.setattr(portal.time, "sleep", sleeps.append)  # Record the one readiness pause.
    monkeypatch.setattr(portal.time, "monotonic", lambda: next(clock))  # Give the wait an exact duration.
    result = portal._wait_for_port(9606, process)  # Use an ephemeral-range value without binding it.
    assert result == portal.PortalStartWait(True, 0.5, None)
    assert sleeps == [portal.READY_PAUSE_SECONDS]


def test_wait_for_port_reports_an_early_child_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stopped child returns at once with its exit code."""
    sleeps: list[float] = []  # An early exit must add no readiness pause.
    clock = _clock(20.0, 20.1)  # The child fails one tenth of a second after the wait starts.
    process = StandInProcess(iter((17,)))  # A nonzero code represents an import failure.
    monkeypatch.setattr(portal, "_probe_port", lambda _port: False)  # Keep all network access mocked.
    monkeypatch.setattr(portal.time, "sleep", sleeps.append)  # Detect an incorrect pause after process exit.
    monkeypatch.setattr(portal.time, "monotonic", lambda: next(clock))  # Give the wait an exact duration.
    result = portal._wait_for_port(9606, process)  # Use an ephemeral-range value without binding it.
    assert result == portal.PortalStartWait(False, pytest.approx(0.1), 17)
    assert sleeps == []


def test_wait_for_port_reports_the_timeout_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A live child that never answers uses the complete bounded wait."""
    sleeps: list[float] = []  # Record each bounded pause without delaying the unit test.
    clock = _clock(30.0, 31.0)  # Two stand-in pauses consume one measured second.
    process = StandInProcess(iter((None, None, None)))  # The child stays live through the final state read.
    monkeypatch.setattr(portal, "READY_TRIES", 2)  # Keep the timeout proof small and deterministic.
    monkeypatch.setattr(portal, "_probe_port", lambda _port: False)  # Keep all network access mocked.
    monkeypatch.setattr(portal.time, "sleep", sleeps.append)  # Record both readiness pauses.
    monkeypatch.setattr(portal.time, "monotonic", lambda: next(clock))  # Give the wait an exact duration.
    result = portal._wait_for_port(9606, process)  # Use an ephemeral-range value without binding it.
    assert result == portal.PortalStartWait(False, 1.0, None)
    assert sleeps == [portal.READY_PAUSE_SECONDS, portal.READY_PAUSE_SECONDS]


def test_start_failure_names_an_early_child_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The setup failure gives the child exit code without a stop signal."""
    stopped: list[StandInProcess] = []  # A stopped child must not receive another stop request.
    process = StandInProcess(iter(()))  # The failure helper must not poll the process again.
    wait = portal.PortalStartWait(False, 0.1, 17)  # Preserve the measured early-exit result.
    monkeypatch.setattr(portal, "_stop_server", stopped.append)  # Detect an incorrect stop signal.
    monkeypatch.setattr(portal, "_report_server_output", lambda: None)  # Keep file access outside the unit test.
    with pytest.raises(pytest.fail.Exception, match=r"exit code 17 after 0\.10 seconds"):
        portal._fail_start(process, wait)  # The helper raises the setup failure after it states the cause.
    assert stopped == []


def test_default_start_budget_is_sixty_seconds() -> None:
    """The default budget covers the measured 12.2-second loaded start."""
    budget = portal.READY_TRIES * portal.READY_PAUSE_SECONDS  # Read the effective default, not a copied value.
    assert budget == portal.DEFAULT_READY_BUDGET_SECONDS
