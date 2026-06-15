"""Unit tests for :class:`MistWebSocketAdapter`.

The adapter wraps ``mistapi.websockets.sites.DeviceCmdEvents``. These
tests mock the SDK client entirely — no live WebSocket traffic — and
verify the lifecycle, frame filtering, timeout, error translation, and
idempotent disconnect contracts documented in
``specs/websocket-migration/contracts/adapter-interface.md``.
"""

from __future__ import annotations  # Defer annotation evaluation for cleaner type hints

from typing import Any  # Generic shapes for fake frames
from unittest.mock import MagicMock, patch  # Standard mocking utilities

import pytest  # Test framework

from src.websocket.adapter import MistWebSocketAdapter  # System under test

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_adapter(timeout: int = 5) -> MistWebSocketAdapter:
    """Construct an adapter with a stub session for tests."""
    session = MagicMock(name="APISession")  # Placeholder APISession — never actually used by mocks
    return MistWebSocketAdapter(  # Build adapter with deterministic defaults for assertions
        session,
        site_id="site-uuid",
        device_id="device-uuid",
        timeout=timeout,
        auto_reconnect=False,
    )


def _frame(session_id: str, status: str | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a fake SDK frame matching the shapes the adapter expects."""
    frame: dict[str, Any] = {"session_id": session_id}  # Top-level session_id — common case
    if status is not None:  # Only include status when caller wants a terminal marker
        frame["status"] = status  # Adapter looks for "completed" / "failed"
    if data is not None:  # Attach payload only when caller wants it
        frame["data"] = data  # Adapter returns this dict in the result
    return frame  # Caller iterates a list of these


# --------------------------------------------------------------------------- #
# Lifecycle: connect / disconnect
# --------------------------------------------------------------------------- #


def test_connect_returns_true_when_ready() -> None:
    """connect() returns True after DeviceCmdEvents reports ready."""
    adapter = _make_adapter()  # Build adapter under test
    fake_client = MagicMock()  # Stand-in for DeviceCmdEvents instance
    fake_client.ready.return_value = True  # Simulate immediate readiness
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client) as ctor:  # Intercept SDK ctor
        result = adapter.connect()  # Exercise the connect path
    assert result is True  # Contract: True on success
    ctor.assert_called_once()  # SDK client built exactly once
    fake_client.connect.assert_called_once_with(run_in_background=True)  # Background thread requested
    assert adapter._connected is True  # Internal state coherent for downstream methods


def test_connect_returns_false_when_never_ready() -> None:
    """connect() returns False if the socket never becomes ready in time."""
    adapter = _make_adapter(timeout=1)  # Short timeout keeps the test fast
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = False  # Never flips to True
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock client
        result = adapter.connect()  # Exercise — should give up after timeout
    assert result is False  # Legacy parity: False on timeout, no raise
    assert adapter._connected is False  # State must reflect failure


def test_connect_returns_false_on_sdk_exception() -> None:
    """connect() swallows SDK exceptions and returns False (legacy parity)."""
    adapter = _make_adapter()  # Build adapter
    with patch("src.websocket.adapter.DeviceCmdEvents", side_effect=RuntimeError("boom")):  # Force ctor failure
        result = adapter.connect()  # Should not propagate
    assert result is False  # Match WebSocketManager error contract
    assert adapter._ws_client is None  # Half-built client must be dropped


def test_disconnect_is_idempotent() -> None:
    """disconnect() can be called multiple times without raising."""
    adapter = _make_adapter()  # Build adapter
    adapter.disconnect()  # First call against an un-connected adapter — no-op
    adapter.disconnect()  # Second call — still no-op
    # No exception => contract satisfied; nothing else to assert
    assert adapter._ws_client is None  # State remains clean


def test_disconnect_after_connect_calls_sdk() -> None:
    """disconnect() forwards to the SDK client and clears internal state."""
    adapter = _make_adapter()  # Build adapter
    fake_client = MagicMock()  # Stand-in for DeviceCmdEvents
    fake_client.ready.return_value = True  # Make connect() succeed
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Establish connection so disconnect has something to tear down
    adapter.disconnect()  # Exercise teardown path
    fake_client.disconnect.assert_called_once()  # SDK disconnect invoked exactly once
    assert adapter._ws_client is None  # Reference dropped
    assert adapter._connected is False  # State reset


def test_disconnect_swallows_sdk_errors() -> None:
    """disconnect() must not raise even when the SDK disconnect throws."""
    adapter = _make_adapter()  # Build adapter
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = True  # Allow connect() to succeed
    fake_client.disconnect.side_effect = RuntimeError("cleanup failure")  # Force tear-down error
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Get into connected state
    adapter.disconnect()  # Should swallow the exception
    assert adapter._ws_client is None  # State still reset
    assert adapter._connected is False  # Coherent post-failure


# --------------------------------------------------------------------------- #
# send_and_wait
# --------------------------------------------------------------------------- #


def test_send_and_wait_returns_completed_result() -> None:
    """Happy path: receives a completed frame and returns the structured dict."""
    adapter = _make_adapter()  # Build adapter
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = True  # Make connect() succeed
    frames = [  # Generator output: one off-target frame, then the completion
        _frame("other-session", status="completed", data={"foo": "bar"}),
        _frame("target", status="completed", data={"output": "ok"}),
    ]
    fake_client.receive.return_value = iter(frames)  # Generator returns our scripted frames
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Move adapter into connected state
        result = adapter.send_and_wait("target", timeout=5)  # Exercise the wait
    assert result["session_id"] == "target"  # Contract: echo back session id
    assert result["status"] == "completed"  # Terminal status detected
    assert result["data"] == {"output": "ok"}  # Payload extracted from matching frame
    assert len(result["raw"]) == 1  # Only the matching frame counts toward raw


def test_send_and_wait_filters_by_session_id() -> None:
    """Frames from other sessions never reach the caller's raw list."""
    adapter = _make_adapter()  # Build adapter
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = True  # Allow connect()
    frames = [  # Three frames, only one matches
        _frame("nope-1"),
        _frame("nope-2"),
        _frame("target", status="completed", data={"x": 1}),
    ]
    fake_client.receive.return_value = iter(frames)  # Wire up generator
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Connect first
        result = adapter.send_and_wait("target", timeout=5)  # Wait for our session
    assert result["status"] == "completed"  # Reached terminal status
    assert len(result["raw"]) == 1  # Off-session frames filtered out


def test_send_and_wait_raises_timeout_when_no_frames() -> None:
    """If no frame ever arrives the adapter raises TimeoutError."""
    adapter = _make_adapter(timeout=1)  # Short default timeout
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = True  # Allow connect()
    fake_client.receive.return_value = iter([])  # Empty generator — exhausts immediately with no frames
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Connect first
        with pytest.raises(TimeoutError):  # Contract: TimeoutError on no result
            adapter.send_and_wait("target", timeout=1)  # Should raise immediately


def test_send_and_wait_before_connect_raises() -> None:
    """Calling send_and_wait before connect is a RuntimeError."""
    adapter = _make_adapter()  # Build adapter but skip connect()
    with pytest.raises(RuntimeError):  # Guard against misuse
        adapter.send_and_wait("target")  # Should refuse to run


def test_send_and_wait_translates_sdk_failure_to_failed_status() -> None:
    """Unexpected SDK exceptions become status='failed' instead of propagating."""
    adapter = _make_adapter()  # Build adapter
    fake_client = MagicMock()  # Stand-in client
    fake_client.ready.return_value = True  # Allow connect()

    def boom_generator() -> Any:  # Local generator that raises mid-iteration
        yield _frame("target")  # First frame is benign
        raise RuntimeError("socket exploded")  # Simulate transport blow-up

    fake_client.receive.return_value = boom_generator()  # Wire up exploding generator
    with patch("src.websocket.adapter.DeviceCmdEvents", return_value=fake_client):  # Inject mock
        adapter.connect()  # Connect first
        result = adapter.send_and_wait("target", timeout=5)  # Should swallow the explosion
    assert result["status"] == "failed"  # Failure surfaced via status field, not exception
    assert result["session_id"] == "target"  # Contract preserved even on failure


# --------------------------------------------------------------------------- #
# Version gate
# --------------------------------------------------------------------------- #


def test_version_gate_parser_handles_three_part_versions() -> None:
    """Internal version parser yields the expected 3-tuple for common inputs."""
    from src.websocket.adapter import _parse_version  # Local import — gate already passed at module load

    assert _parse_version("0.61.0") == (0, 61, 0)  # Standard release
    assert _parse_version("0.62.0") == (0, 62, 0)  # Installed version in this env
    assert _parse_version("1.0") == (1, 0, 0)  # Short versions pad with zeros
    # Pre-release/build suffixes are tolerated — digits in the segment win
    parsed = _parse_version("0.61.0a1")  # Lenient parser keeps digit chars only
    assert parsed[:2] == (0, 61)  # Major/minor unaffected by suffix noise
