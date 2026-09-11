"""Prove that four error paths release the resource that they opened.

Each test drives one failure path and then asserts that the code closed the
socket, the thread, or the HTTP body that the happy path would have closed.
Before the fix each test fails, because the failure path dropped the handle.
"""

from __future__ import annotations

import threading  # WHY: the CLI shell test inspects the receive thread state.
import time  # WHY: the capture stream test measures the loop deadline.
from typing import Any  # WHY: the fakes stand in for loosely typed SDK objects.

import pytest  # WHY: fixtures plus the monkeypatch helper.

from src.capture import _packet_capture_exec as capture_exec  # WHY: unit under test for the stream cap.
from src.capture import client_pcap_downloader as pcap_dl  # WHY: unit under test for the streamed body.
from src.ssh import cli_shell_manager as shell_mod  # WHY: unit under test for the receive thread.
from src.ssh.connection import connector as connector_mod  # WHY: unit under test for the paramiko client.


class _FakeSshClient:
    """Record whether the connect flow closed this paramiko client stand-in."""

    def __init__(self) -> None:
        self.closed = False  # WHY: the assertion reads this flag.

    def close(self) -> None:
        """Mark the client closed the way paramiko releases its transport."""
        self.closed = True  # WHY: record the cleanup call.

    def set_missing_host_key_policy(self, _policy: Any) -> None:
        """Accept the reject policy the way paramiko accepts it."""
        return None  # WHY: the test needs no policy behaviour.

    def get_host_keys(self) -> Any:
        """Return an empty host key store, because the test never enrolls a key."""
        return {}  # WHY: the enrollment path raises before it reads this store.


def _build_connector(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Return an SshConnector whose preflight always passes."""
    instance = connector_mod.SshConnector.__new__(connector_mod.SshConnector)  # WHY: skip the real constructor.
    instance.logger = connector_mod.logging.getLogger("test-connector")  # WHY: the helpers log through this.
    instance.managed_known_hosts_path = "known_hosts"  # WHY: the success path returns this value.
    monkeypatch.setattr(instance, "_preflight", lambda *_args, **_kwargs: True)  # WHY: bypass input validation.
    return instance  # WHY: the tests drive connect() on this object.


def test_failed_authentication_closes_the_ssh_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed login must close the paramiko client, because the transport thread stays alive."""
    connector = _build_connector(monkeypatch)  # WHY: an instance with a passing preflight.
    fake_client = _FakeSshClient()  # WHY: stands in for the paramiko SSHClient.
    monkeypatch.setattr(connector, "_build_client_with_tofu", lambda *_a, **_k: fake_client)  # WHY: skip TOFU.
    monkeypatch.setattr(connector, "_attempt_authenticated_connect", lambda *_a, **_k: False)  # WHY: force failure.

    client, kh_path = connector.connect("switch1.example.net", "noc", "wrong-password", 22)  # WHY: drive failure.

    assert client is None  # WHY: the caller must still see the failure sentinel.
    assert kh_path is None  # WHY: no known-hosts path is handed out on failure.
    assert fake_client.closed is True  # WHY: the leak fix must close the abandoned client.


def test_failed_host_key_enrollment_closes_the_ssh_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed host key enrollment must close the client that the builder created."""
    connector = _build_connector(monkeypatch)  # WHY: an instance with a passing preflight.
    fake_client = _FakeSshClient()  # WHY: the builder returns this object.
    monkeypatch.setattr(connector_mod, "SSHClient", lambda: fake_client)  # WHY: intercept the client construction.
    monkeypatch.setattr(connector, "_load_known_hosts", lambda _client: None)  # WHY: no real known-hosts file.

    def _raise_enrollment_error(*_args: Any, **_kwargs: Any) -> None:
        """Fail the way an unreachable host fails during the key fetch."""
        raise OSError("host unreachable")  # WHY: the real failure raises from the socket layer.

    monkeypatch.setattr(connector, "_trust_host_on_first_use", _raise_enrollment_error)  # WHY: force the error path.

    result = connector._build_client_with_tofu("switch1.example.net", 22)  # WHY: drive the enrollment failure.

    assert result is None  # WHY: the caller must still see the failure sentinel.
    assert fake_client.closed is True  # WHY: the leak fix must close the abandoned client.


class _FakeResponse:
    """Record whether the downloader closed the streamed HTTP body."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code  # WHY: the downloader branches on this value.
        self.closed = False  # WHY: the assertion reads this flag.

    def __enter__(self) -> _FakeResponse:
        """Support the context manager form that the fix uses."""
        return self  # WHY: requests returns the response itself.

    def __exit__(self, *_exc: Any) -> None:
        """Close the body the way requests closes it on block exit."""
        self.closed = True  # WHY: record the cleanup call.

    def iter_content(self, chunk_size: int) -> list[bytes]:
        """Return no chunks, because the failure test never reaches the write."""
        assert chunk_size > 0  # nosec B101  # WHY: guard against a zero chunk size regression.
        return []  # WHY: no body content is needed for this test.


def test_non_200_pcap_download_closes_the_streamed_response(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """A non-200 PCAP reply must close the streamed body, because the socket stays checked out."""
    fake_response = _FakeResponse(status_code=404)  # WHY: the Mist pre-signed URL expired.
    monkeypatch.setattr(pcap_dl.requests, "get", lambda *_a, **_k: fake_response)  # WHY: no real HTTP call.
    row = pcap_dl._CaptureRow(  # WHY: the minimum row that the downloader reads.
        capture_id="cap-1",
        filename="cap-1.pcap",
        vlan_id="10",
        pcap_url="https://example.invalid/cap-1.pcap",
    )

    succeeded = pcap_dl.ClientPacketCaptureDownloader._download_one(row, tmp_path)  # WHY: drive the non-200 path.

    assert succeeded is False  # WHY: the caller must still count this row as a failure.
    assert fake_response.closed is True  # WHY: the leak fix must close the streamed body.


class _StubWebSocketManager:
    """A stream source that never sends the Mist end-of-capture signal."""

    def __init__(self) -> None:
        self.results_lock = threading.Lock()  # WHY: the drain helper takes this lock.
        self.command_results: dict[str, Any] = {}  # WHY: an empty dict means no packets arrive.


def test_capture_stream_stops_at_the_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    """The packet stream loop must stop at a deadline, because a dropped socket sends no end signal."""
    executor = capture_exec.PacketCaptureExec.__new__(capture_exec.PacketCaptureExec)  # WHY: skip the constructor.
    manager = type("_Manager", (), {"websocket_manager": _StubWebSocketManager()})()  # WHY: minimal parent stub.
    executor._mm = manager  # WHY: the executor reads the manager through this attribute.
    monkeypatch.setattr(capture_exec, "_STREAM_MAX_SECONDS", 0.3)  # WHY: shrink the cap so the test stays fast.

    started = time.time()  # WHY: measure how long the bounded loop runs.
    executor.read_stream_packets("/sites/s1/pcaps", "cap-1")  # WHY: drive the never-ending stream.
    elapsed = time.time() - started  # WHY: the loop must return on its own.

    assert elapsed < 5.0  # WHY: an unbounded loop never returns, so this bound proves the fix.


def test_cli_shell_receiver_is_a_daemon_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI shell receive thread must be a daemon, because a blocked recv() blocks the interpreter exit."""
    monkeypatch.setattr(  # WHY: replace the blocking receive loop with an immediate return.
        shell_mod.CLIShellManager, "_shell_receive_loop", staticmethod(lambda *_a, **_k: None)
    )

    receiver = shell_mod.CLIShellManager._shell_start_receiver(object(), object(), object(), False)  # WHY: start it.

    assert isinstance(receiver, threading.Thread)  # WHY: the caller needs the handle to join the thread.
    assert receiver.daemon is True  # WHY: a non-daemon thread hangs the process exit.
    receiver.join(timeout=5)  # WHY: keep the test suite free of a stray thread.


class _FakeWebSocket:
    """Record whether the shell shutdown closed the WebSocket."""

    def __init__(self) -> None:
        self.closed = False  # WHY: the assertion reads this flag.

    def close(self) -> None:
        """Close the socket the way the websocket library closes it."""
        self.closed = True  # WHY: record the cleanup call.


def test_cli_shell_shutdown_closes_the_websocket_and_joins_the_thread() -> None:
    """The shell shutdown must close the socket and join the thread, because each session leaks one of each."""
    fake_ws = _FakeWebSocket()  # WHY: stands in for the live WebSocket.
    receiver = threading.Thread(target=lambda: None, daemon=True)  # WHY: a thread that ends at once.
    receiver.start()  # WHY: the shutdown helper joins a started thread.

    shell_mod.CLIShellManager._shell_shutdown(fake_ws, receiver)  # WHY: drive the cleanup path.

    assert fake_ws.closed is True  # WHY: the leak fix must close the socket.
    assert receiver.is_alive() is False  # WHY: the join must reap the receive thread.
