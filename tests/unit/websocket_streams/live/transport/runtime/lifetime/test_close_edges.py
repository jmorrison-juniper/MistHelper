"""Verify closure errors and concurrent callers without changing transport outcomes."""

from __future__ import annotations

import threading

import pytest

from tests.unit.websocket_streams.live.transport.runtime.lifetime.test_close_ownership import ConnectionSchedule


@pytest.mark.parametrize("kind", ("runtime", "shell", "stream"))
def test_concurrent_close_releases_reader_without_deadlock(kind: str) -> None:
    """Keep the descriptor until its reader exits despite two close callers."""
    schedule = ConnectionSchedule(kind)  # Share the same active receive across both close callers.
    second_closer = threading.Thread(target=schedule.close, daemon=True)  # Model a second local close request.
    schedule.reader.start()  # Establish active descriptor ownership before either close.
    try:
        assert schedule.socket.receiving.wait(2.0)  # Require the intended concurrent schedule.
        schedule.closer.start()  # The first close interrupts the active reader.
        assert schedule.socket.aborted.wait(2.0)  # Observe interruption before the second close.
        second_closer.start()  # Runtime and connection close must both tolerate another caller.
        assert not schedule.socket.closed.wait(0.05)  # Neither caller may release an active descriptor.
    finally:
        schedule.finish()  # Release the read and join the first close caller.
        if second_closer.ident is not None:  # An earlier assertion can prevent this worker from starting.
            second_closer.join(timeout=2.0)  # Do not leave a second close request behind.
    assert not second_closer.is_alive()  # Require completion without a receive-lock deadlock.
    assert schedule.socket.closed.is_set()  # At least one close caller must release the descriptor.
    assert len(schedule.errors) == 1  # The interrupted receive must exit through its existing error contract.


@pytest.mark.parametrize("kind", ("runtime", "shell", "stream"))
def test_abort_failure_is_visible_without_releasing_active_descriptor(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve abort errors without closing a resource that an active reader owns."""
    schedule = ConnectionSchedule(kind)  # Use an active reader to detect unsafe error cleanup.

    def failed_abort() -> None:
        """Report an explicit interruption failure before any descriptor release."""
        raise OSError("The controlled abort failed.")  # Keep the existing transport error visible.

    monkeypatch.setattr(schedule.socket, "abort", failed_abort)  # Inject only the failure under examination.
    schedule.reader.start()  # Enter receive before the failed close request.
    try:
        assert schedule.socket.receiving.wait(2.0)  # Require an active native-call model.
        with pytest.raises(OSError, match="The controlled abort failed"):  # Preserve the abort exception.
            schedule.close()  # A failed abort must not wait on an uninterruptible receive.
        assert not schedule.socket.closed.is_set()  # Do not release the active descriptor on abort failure.
    finally:
        schedule.finish()  # Release the modeled native call independently of the failed abort.
    assert len(schedule.errors) == 1  # The reader must still exit without a held receive lock.
