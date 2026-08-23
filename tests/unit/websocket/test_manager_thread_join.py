"""Unit tests for the WebSocket reader thread teardown in the manager module.

Issue #1875 reports a thread leak. ``WebSocketManager`` starts a reader thread
that runs ``run_forever``. The old ``disconnect`` called ``close`` and returned.
``close`` only requests a shutdown, so the reader thread was still alive when
the caller read the collected output. Each ARP run through
``ArpDeviceExecutor`` therefore added one live thread to a long-lived process.

These tests pin the teardown contract. ``disconnect`` must wait a bounded time
for the reader thread, must warn when the wait expires, must run the wait after
a ``close`` failure, and must not try to join itself.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

from src.websocket import manager as manager_mod
from src.websocket.manager import WebSocketManager

_MANAGER_LOGGER = "src.websocket.manager"  # WHY: Same logger name the sibling manager tests assert on.
_JOIN_WAIT_SECONDS = 5.0  # WHY: Upper bound the fake reader waits for the stop signal.
_EXIT_DELAY_SECONDS = 0.25  # WHY: Reader stays alive long enough to expose a missing join.


class _FakeConnection:
    """Stand-in for ``websocket.WebSocketApp`` that models a slow shutdown."""

    def __init__(self, exit_delay: float = _EXIT_DELAY_SECONDS) -> None:
        """Create the fake connection with a stop event and a shutdown delay."""
        self.stop_event = threading.Event()  # WHY: ``close`` signals the reader through this event.
        self.exit_delay = exit_delay  # WHY: Models the time ``run_forever`` needs to unwind.
        self.close_calls = 0  # WHY: Lets a test prove ``disconnect`` asked for the shutdown.

    def close(self) -> None:
        """Request the shutdown without waiting for the reader to stop."""
        self.close_calls += 1  # WHY: Record the request so a test can assert on it.
        self.stop_event.set()  # WHY: Release the reader, which still needs time to unwind.

    def run_forever(self) -> None:
        """Block until ``close`` fires, then take a short time to unwind."""
        self.stop_event.wait(timeout=_JOIN_WAIT_SECONDS)  # WHY: Bounded so a failed test cannot hang.
        time.sleep(self.exit_delay)  # WHY: Keeps the thread alive after ``close`` returns.


class _StuckConnection:
    """Stand-in for a connection whose reader ignores the shutdown request."""

    def __init__(self) -> None:
        """Create the stuck connection with an event the test controls."""
        self.release_event = threading.Event()  # WHY: Only the test releases this reader.

    def close(self) -> None:
        """Accept the shutdown request and do nothing, which models a stuck socket."""
        return None  # WHY: A stuck reader is the case the join timeout must report.

    def run_forever(self) -> None:
        """Block until the test releases the thread."""
        self.release_event.wait(timeout=_JOIN_WAIT_SECONDS)  # WHY: Bounded so the suite cannot hang.


def _make_session() -> MagicMock:
    """Return a mock Mist session with the attributes the manager reads."""
    session = MagicMock()  # WHY: The manager only reads two attributes off the session.
    session.host = "api.mist.com"  # WHY: Drives the derived WebSocket URL.
    session.apitoken = "tok"  # WHY: Present so credential resolution succeeds.
    return session  # WHY: Callers pass this straight into the manager constructor.


def _start_reader(manager: WebSocketManager, connection: Any) -> threading.Thread:
    """Attach the fake connection to the manager and start a daemon reader thread."""
    manager.websocket_connection = connection  # WHY: The fake stands in for WebSocketApp.
    reader = threading.Thread(target=connection.run_forever, daemon=True)  # WHY: Mirrors the real reader.
    manager.websocket_thread = reader  # WHY: Mirrors what _start_websocket_thread records.
    reader.start()  # WHY: The leak only appears once the reader is running.
    return reader  # WHY: Test asserts on the thread state after disconnect.


def test_start_websocket_thread_creates_daemon_reader() -> None:
    """The reader thread must be a daemon, so a stuck reader cannot block interpreter exit."""
    manager = WebSocketManager(_make_session())  # WHY: Real manager under test.
    fake_app = MagicMock()  # WHY: Replaces WebSocketApp so no socket is opened.
    fake_app.run_forever = lambda: None  # WHY: Returns at once, which keeps the test fast.
    with patch("src.websocket.manager.websocket.WebSocketApp", return_value=fake_app):
        manager._start_websocket_thread(["Authorization: Token tok"])  # WHY: Exercises the real starter.
    assert manager.websocket_thread is not None  # WHY: The handle must be stored for the later join.
    assert manager.websocket_thread.daemon is True  # WHY: Acceptance criterion from issue #1875.
    manager.websocket_thread.join(timeout=_JOIN_WAIT_SECONDS)  # WHY: Leave no thread behind for other tests.


def test_disconnect_joins_reader_thread_and_leaves_no_extra_thread() -> None:
    """After disconnect returns, the reader thread has stopped and the thread count is back to baseline."""
    manager = WebSocketManager(_make_session())  # WHY: Real manager under test.
    baseline = threading.active_count()  # WHY: Reference count taken before the reader starts.
    connection = _FakeConnection()  # WHY: Models a socket that needs time to unwind.
    reader = _start_reader(manager, connection)  # WHY: Reproduces the state left by connect().
    manager.connected = True  # WHY: Matches the state a live connection would leave.
    manager.disconnect()  # WHY: The call under test must wait for the reader.
    assert connection.close_calls == 1  # WHY: Proves disconnect still requests the shutdown.
    assert reader.is_alive() is False  # WHY: Core defect of issue #1875 is a reader that outlives the call.
    assert threading.active_count() == baseline  # WHY: Acceptance criterion asks for a thread-count check.
    assert manager.websocket_thread is None  # WHY: A stopped thread must not keep a stale handle.


def test_disconnect_joins_reader_thread_even_when_close_raises() -> None:
    """A close() failure must not skip the join or leave stale manager state."""
    manager = WebSocketManager(_make_session())  # WHY: Real manager under test.
    connection = _FakeConnection(exit_delay=0.0)  # WHY: Reader exits as soon as the test releases it.
    reader = _start_reader(manager, connection)  # WHY: Reproduces the state left by connect().
    manager.connected = True  # WHY: Matches the state a live connection would leave.
    manager.subscribed_channels.add("/sites/a/devices/b/cmd")  # WHY: Proves the state clear still runs.
    connection.stop_event.set()  # WHY: Releases the reader, because the raising close cannot.

    def raising_close() -> None:
        """Raise from close so the test can prove the stop path still runs."""
        raise OSError("socket already gone")  # WHY: Models a socket that fails during teardown.

    connection.close = raising_close  # type: ignore[method-assign]  # WHY: Injects the failure.
    try:  # WHY: disconnect re-raises the close failure after the stop path runs.
        manager.disconnect()  # WHY: The call under test.
    except OSError:  # WHY: The caller decides what to do with the failure.
        pass  # WHY: The test only checks the teardown side effects.
    assert reader.is_alive() is False  # WHY: The join must run on the exception path too.
    assert manager.connected is False  # WHY: State reset must not depend on a clean close.
    assert manager.subscribed_channels == set()  # WHY: Stale subscriptions would break the next connect.


def test_disconnect_warns_and_keeps_handle_when_join_times_out(caplog) -> None:  # type: ignore[no-untyped-def]
    """A join that expires logs a warning naming the endpoint and keeps the thread handle."""
    manager = WebSocketManager(_make_session())  # WHY: Real manager under test.
    connection = _StuckConnection()  # WHY: Models a reader that ignores the shutdown request.
    reader = _start_reader(manager, connection)  # WHY: Reproduces the state left by connect().
    # WHY: Short bound keeps the test fast while still exercising the timeout branch.
    patcher = patch.object(manager_mod, "_WS_THREAD_JOIN_SECONDS", 0.05)
    with patcher, caplog.at_level(logging.WARNING, logger=_MANAGER_LOGGER):
        manager.disconnect()  # WHY: The call under test must not block on the stuck reader.
    assert "still alive" in caplog.text  # WHY: A silent leak gives the operator nothing to act on.
    assert manager.websocket_url in caplog.text  # WHY: The warning must name the endpoint.
    assert manager.websocket_thread is reader  # WHY: Keep the handle so a later disconnect can retry.
    connection.release_event.set()  # WHY: Release the reader so the suite leaves no thread behind.
    reader.join(timeout=_JOIN_WAIT_SECONDS)  # WHY: Wait for the released reader before the test ends.


def test_disconnect_from_reader_thread_skips_the_self_join() -> None:
    """A callback that calls disconnect on the reader thread must not raise a self-join error."""
    manager = WebSocketManager(_make_session())  # WHY: Real manager under test.
    manager.websocket_connection = MagicMock()  # WHY: close() is a no-op mock here.
    failures: list[BaseException] = []  # WHY: Collects any error raised inside the reader thread.

    def disconnect_from_reader() -> None:
        """Call disconnect from inside the reader thread, which models an on_close callback."""
        try:  # WHY: A raised error inside a thread would otherwise be lost.
            manager.disconnect()  # WHY: The self-join branch under test.
        except BaseException as thread_error:  # noqa: BLE001  # WHY: Report any error to the main thread.
            failures.append(thread_error)  # WHY: Main thread asserts the list is empty.

    reader = threading.Thread(target=disconnect_from_reader, daemon=True)  # WHY: Stands in for the reader.
    manager.websocket_thread = reader  # WHY: Makes the running thread its own join target.
    reader.start()  # WHY: Runs disconnect on the thread the manager would try to join.
    reader.join(timeout=_JOIN_WAIT_SECONDS)  # WHY: Bounded wait keeps a failure from hanging the suite.
    assert failures == []  # WHY: A self-join would raise RuntimeError from threading.
    assert manager.connected is False  # WHY: The state reset must still run on this path.
