"""Prove the shell log completion wait with controlled real log delivery."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from tests.unit.websocket_streams.live.runners import test_ws_shell_runner as shell_tests


class ControlledClock:
    """Advance only the helper's clock without a real sleep or reader thread."""

    def __init__(self, delivery: Callable[[], None] | None = None) -> None:
        """Store optional delivery for the first polling interval."""
        self.elapsed = 0.0
        self.polls = 0
        self.delivery = delivery

    def monotonic(self) -> float:
        """Return deterministic time for the actual helper's deadline."""
        return self.elapsed

    def sleep(self, interval: float) -> None:
        """Deliver the event only after the helper checks the incomplete capture."""
        assert interval == 0.01
        self.elapsed = round(self.elapsed + interval, 2)
        self.polls += 1
        if self.polls == 1 and self.delivery is not None:
            self.delivery()


def test_completion_already_captured_needs_no_poll(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An exact completed event permits an immediate snapshot."""
    caplog.set_level(logging.DEBUG)
    clock = ControlledClock()
    monkeypatch.setattr(shell_tests, "time", clock)
    target = logging.getLogger("src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.outcomes")
    StructuredTransportLogger(target).emit(logging.DEBUG, "terminal_outcome_completed")
    assert shell_tests.ShellLogCompletion.inspect(caplog) == (True, 1)
    shell_tests.ShellLogCompletion.wait(caplog)
    assert clock.polls == 0
    assert clock.elapsed == 0.0
    assert target is logging.getLogger("src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.outcomes")


def test_completion_delivered_after_first_check_permits_snapshot(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The helper waits for the real event instead of accepting an early snapshot."""
    caplog.set_level(logging.DEBUG)
    target = logging.getLogger("src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.outcomes")
    emitter = StructuredTransportLogger(target)

    def deliver() -> None:
        """Emit through the runtime logger only after the first failed predicate."""
        assert shell_tests.ShellLogCompletion.inspect(caplog)[0] is False
        emitter.emit(logging.DEBUG, "terminal_outcome_completed")

    clock = ControlledClock(deliver)
    monkeypatch.setattr(shell_tests, "time", clock)
    assert shell_tests.ShellLogCompletion.inspect(caplog)[0] is False
    shell_tests.ShellLogCompletion.wait(caplog)
    assert clock.polls == 1
    assert clock.elapsed == 0.01
    assert shell_tests.ShellLogCompletion.inspect(caplog)[0] is True


@pytest.mark.parametrize(
    ("event", "logger_name"),
    [
        (None, "src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.outcomes"),
        ("terminal_outcome_started", "src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.outcomes"),
        ("terminal_outcome_completed", "src.mist.realtime.websocket_streams.live.runners.shell.lifecycle.reading"),
    ],
    ids=["missing", "wrong-event", "wrong-logger"],
)
def test_unavailable_completion_refuses_at_existing_bound(
    event: str | None,
    logger_name: str,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing and unrelated records cannot satisfy the actual completion guard."""
    caplog.set_level(logging.DEBUG)
    clock = ControlledClock()
    monkeypatch.setattr(shell_tests, "time", clock)
    if event is not None:
        StructuredTransportLogger(logging.getLogger(logger_name)).emit(logging.DEBUG, event)
    assert shell_tests.ShellLogCompletion.inspect(caplog)[0] is False
    captured_before = len(caplog.records)
    with pytest.raises(
        AssertionError, match=r"Checked \d+ captured records.*shell outcome record is missing"
    ) as failure:
        shell_tests.ShellLogCompletion.wait(caplog)
    assert str(failure.value) == (
        f"Checked {captured_before + 1} captured records. The shell outcome record is missing."
    )
    assert clock.elapsed == 2.0
    assert clock.polls == 200
    assert shell_tests.ShellLogCompletion.inspect(caplog)[0] is False
