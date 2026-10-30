"""Exercise local close while an active receive retains its descriptor."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import pytest
import websocket

from src.mist.realtime.websocket_streams.live.transport.endpoint import ShellAddressPolicy
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.socket_runtime import SocketRuntime
from src.mist.realtime.websocket_streams.live.transport.shell_client import ShellConnection
from src.mist.realtime.websocket_streams.live.transport.stream_client import StreamConnection
from tests.unit.websocket_streams.live.runners.test_ws_shell_runner import _endpoint
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import FakeApiSession
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import FakeMistCloud


class PausedSocket:
    """Keep receive active after abort until the test releases its native-call model."""

    def __init__(self) -> None:
        """Create explicit scheduling signals without a real descriptor."""
        self.receiving = threading.Event()  # Mark the active descriptor use.
        self.aborted = threading.Event()  # Allow the test to observe close before release.
        self.release = threading.Event()  # Model a native read that has not returned yet.
        self.closed = threading.Event()  # Detect premature descriptor release.

    def settimeout(self, _timeout: float) -> None:
        """Accept the normal open timeout without changing the schedule."""

    def recv_data(self, control_frame: bool = False) -> tuple[int, bytes]:
        """Retain the descriptor until the native-call schedule resumes."""
        assert control_frame is True  # Preserve the production control-frame contract.
        self.receiving.set()  # Signal that close must now retain this resource.
        assert self.release.wait(2.0)  # Bound the controlled native-call model.
        raise websocket.WebSocketConnectionClosedException("The read was aborted.")  # Model the interrupted read.

    def abort(self) -> None:
        """Interrupt receive without releasing its descriptor."""
        self.aborted.set()  # Abort must precede the wait for receive completion.

    def close(self) -> None:
        """Record descriptor release for the ownership assertion."""
        self.closed.set()  # A close before receive exits permits descriptor reuse.


class ConnectionSchedule:
    """Bind the same ownership schedule to runtime, shell, and stream callers."""

    def __init__(self, kind: str) -> None:
        """Construct one real connection owner around the controlled socket."""
        self.socket = PausedSocket()  # Keep the native-call model local to this test.
        self.errors: list[BaseException] = []  # Preserve thread failures for the test thread.
        self.receive, self.close = self._operations(kind)  # Bind the actual production owner.
        self.reader = threading.Thread(target=self._read, daemon=True)  # Exercise a separate reader.
        self.closer = threading.Thread(target=self.close, daemon=True)  # Close must wait without holding the GIL.

    def _operations(self, kind: str) -> tuple[Callable[[], object], Callable[[], None]]:
        """Select the concrete owner without network or credentials."""
        if kind == "runtime":  # Unit coverage isolates the lifetime mechanism.
            runtime = SocketRuntime(self.socket)  # Receive and close must share this owner.
            return lambda: runtime.receive(0.1), runtime.close  # Use normal runtime entry points.
        endpoint = _endpoint(FakeApiSession(FakeMistCloud()))  # Reuse the offline endpoint contract.

        def factory(*_args: object, **_options: object) -> PausedSocket:
            """Supply the controlled socket without network access."""
            return self.socket  # Keep both connection integrations on the same scheduling model.

        if kind == "shell":  # Shell and screen share this connection implementation.
            shell = ShellConnection(endpoint, ShellAddressPolicy(endpoint.cloud_host, True), factory, time.monotonic)
            shell.open("ws://127.0.0.1:9600/shell")  # The factory prevents any network request.
            return lambda: shell.resource("reader").read(0.1), shell.close  # Preserve local-close mapping.
        stream = StreamConnection(endpoint, factory, time.monotonic, threading.Event())  # Test the event path too.
        stream.open()  # Opening publishes the shared runtime without a subscription.
        return lambda: stream.receive(0.1), stream.close  # Keep the existing stream read contract.

    def _read(self) -> None:
        """Preserve the expected interruption from the reader thread."""
        try:  # Thread errors must reach an explicit assertion.
            self.receive()  # Pause inside the controlled native-call model.
        except (ConnectionClosed, websocket.WebSocketConnectionClosedException) as error:
            self.errors.append(error)  # Require one real interruption, not silent success.

    def finish(self) -> None:
        """Release and join both workers even after an assertion fails."""
        self.socket.release.set()  # Allow the active native-call model to return.
        self.reader.join(timeout=2.0)  # Do not leave a reader behind.
        if self.closer.ident is not None:  # An earlier failure can prevent the close thread from starting.
            self.closer.join(timeout=2.0)  # Do not leave a blocked close behind.
        assert not self.reader.is_alive() and not self.closer.is_alive()  # Detect deadlocks explicitly.


@pytest.mark.parametrize("kind", ("runtime", "shell", "stream"))
def test_close_retains_descriptor_until_receive_exits(kind: str) -> None:
    """Abort first, but release no descriptor while receive still uses it."""
    schedule = ConnectionSchedule(kind)  # Cover unit ownership and both connection integrations.
    schedule.reader.start()  # Enter the active receive before local closure.
    try:  # Always release the controlled read before leaving the test.
        assert schedule.socket.receiving.wait(2.0)  # Require the intended interleaving.
        schedule.closer.start()  # Request local close while native receive still owns its descriptor.
        assert schedule.socket.aborted.wait(2.0)  # A receive lock must not prevent the wake operation.
        assert not schedule.socket.closed.wait(0.05)  # This assertion fails before the repair.
    finally:
        schedule.finish()  # Release the read so close can finish safely.
    assert schedule.socket.closed.is_set()  # Close must release the descriptor after receive exits.
    assert len(schedule.errors) == 1  # A real close result must end the read.
    with pytest.raises((ConnectionClosed, websocket.WebSocketConnectionClosedException)):  # Refuse later reads.
        schedule.receive()  # No closed descriptor can reach readiness or native receive.


@pytest.mark.parametrize("kind", ("runtime", "shell", "stream"))
def test_closed_owner_refuses_receive_after_repeated_close(kind: str) -> None:
    """Keep repeated closure safe and reject reads before descriptor access."""
    schedule = ConnectionSchedule(kind)  # Use the same owners without starting a reader thread.
    schedule.close()  # Close without an active read must not wait.
    schedule.close()  # A repeated close must remain safe for every connection owner.
    assert schedule.socket.closed.is_set()  # Require physical closure, not only a local event.
    assert schedule.socket.aborted.is_set()  # Closure must interrupt native socket operations.
    with pytest.raises((ConnectionClosed, websocket.WebSocketConnectionClosedException)):  # Preserve close outcomes.
        schedule.receive()  # A closed owner must reject the read before it reaches the socket.
    assert not schedule.socket.receiving.is_set()  # Prove that no native read accessed the closed descriptor.
