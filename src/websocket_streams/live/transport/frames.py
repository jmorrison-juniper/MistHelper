"""Decode Mist stream frames into safe Python values.

Why:
    Issue #3671 replaces the Mist SDK frame decoding. The runners need one
    small decoder that matches the SDK for NUL removal and JSON fallback.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Mist stream data frames use JSON text.
import logging  # The frame reader logs safe keepalive state.
import select  # Read waits must not change the shared socket timeout.
import threading  # The close event comes from the client.
from collections.abc import Callable, Mapping  # The frame reader accepts a clock and mapping events.
from dataclasses import dataclass  # FrameRead is a small immutable value.
from typing import Any  # websocket-client is partly untyped.

import websocket  # The frame reader catches websocket-client exceptions.
from websocket import ABNF  # Opcode constants come from websocket-client.

logger = logging.getLogger(__name__)  # Keep frame read log records under this module.


class ConnectionClosed(Exception):
    """A WebSocket connection ended.

    Args:
        code: The close code, 1005 for an empty close frame, or None when no close frame arrived.
        dropped: True when the network or far side ended the connection.
    """

    def __init__(self, code: int | None = None, dropped: bool = True) -> None:
        """Build the connection close error.

        Args:
            code: The close code, 1005, or None when no close frame arrived.
            dropped: True for a remote or network end.
        """
        super().__init__("The WebSocket connection closed.")  # The caller reads structured fields.
        self.code = code  # Tests and runners distinguish close codes.
        self.dropped = dropped  # Local close is not a dropped connection.


class SubscribeError(Exception):
    """A stream channel subscription failed.

    Args:
        channel: The channel that failed.
        detail: The refusal detail or ``timeout``.
    """

    def __init__(self, channel: str, detail: str) -> None:
        """Build the subscription error.

        Args:
            channel: The channel that failed.
            detail: The refusal detail or timeout marker.
        """
        super().__init__(f"Subscription failed for channel {channel}.")  # The detail stays in a field.
        self.channel = channel  # Runners report the failed channel.
        self.detail = detail  # Runners report a safe refusal detail.


@dataclass(frozen=True, slots=True)
class FrameRead:
    """One application data frame.

    Args:
        opcode: The WebSocket opcode.
        payload: The raw frame payload bytes.
    """

    opcode: int  # The WebSocket opcode.
    payload: bytes  # The raw frame payload.


class FrameReader:
    """Read frames with keepalive and close-code handling."""

    def __init__(
        self,
        socket: Any,
        closed: threading.Event,
        clock: Callable[[], float],
        read_timeout_seconds: float,
    ) -> None:
        """Build one frame reader.

        Args:
            socket: The websocket-client socket.
            closed: The client close event.
            clock: A callable monotonic clock.
            read_timeout_seconds: The quiet interval before ping.
        """
        self._socket = socket  # The caller owns socket creation and close.
        self._closed = closed  # Local close changes the dropped marker.
        self._clock = clock  # Tests can inject a fake clock.
        self._read_timeout_seconds = read_timeout_seconds  # Keepalive timing comes from the profile.
        self._last_rx = self._now()  # A new reader starts with a live connection.
        self._ping_sent = False  # One ping is outstanding at most.

    def read(self, timeout: float) -> FrameRead | None:
        """Read one application frame or one control frame.

        Args:
            timeout: The application wait for this attempt.

        Returns:
            A data frame, or None after timeout or a control frame.

        Raises:
            ConnectionClosed: The socket closed or missed two intervals.
        """
        try:  # Map websocket-client errors to the runner close contract.
            if self._closed.is_set():  # A local close should not wait for network data.
                raise ConnectionClosed(code=None, dropped=False)  # Report a local close to the runner.
            if not self._wait_until_ready(timeout):  # Keep application waits independent of socket timeout.
                self._check_keepalive()  # A timeout can trigger ping or dead detection.
                return None  # A quiet period is not data.
            opcode, payload = self._socket.recv_data(control_frame=True)  # Read data and control frames.
        except websocket.WebSocketTimeoutException:
            self._check_keepalive()  # A timeout can trigger ping or dead detection.
            return None  # A quiet period is not data.
        except websocket.WebSocketConnectionClosedException as exc:
            raise ConnectionClosed(code=None, dropped=not self._closed.is_set()) from exc  # Preserve close origin.
        except websocket.WebSocketException as exc:
            raise ConnectionClosed(code=None, dropped=not self._closed.is_set()) from exc  # Map client errors.
        except OSError as exc:
            raise ConnectionClosed(code=None, dropped=not self._closed.is_set()) from exc  # TCP loss has no close code.
        return self._frame_or_control(opcode, payload)  # Control frames update liveness and return no data.

    @staticmethod
    def close_socket(socket: Any) -> None:
        """Abort, close, and shut down one websocket-client socket.

        Args:
            socket: The websocket-client socket.
        """
        if hasattr(socket, "abort"):  # websocket-client abort wakes a blocked reader.
            socket.abort()  # Abort before close so recv_data stops promptly.
        socket.close()  # Ask websocket-client to send or process close state.
        if hasattr(socket, "shutdown"):  # websocket-client shutdown handles CLOSE_WAIT sockets.
            socket.shutdown()  # Shutdown is safe when close already ran.

    def _frame_or_control(self, opcode: int, payload: object) -> FrameRead | None:
        """Process one received frame.

        Args:
            opcode: The WebSocket opcode.
            payload: The frame payload from websocket-client.

        Returns:
            A data frame, or None for ping or pong.

        Raises:
            ConnectionClosed: The frame is a close frame.
        """
        data = self._payload_bytes(payload)  # Normalize payloads to bytes.
        if opcode == ABNF.OPCODE_CLOSE:  # A WebSocket close frame carries an optional code.
            raise ConnectionClosed(code=self._close_code(data), dropped=not self._closed.is_set())  # Report the code.
        if opcode in {ABNF.OPCODE_PING, ABNF.OPCODE_PONG}:  # Any control reply proves the peer is alive.
            self._mark_rx()  # Keepalive must not drop a healthy quiet connection.
            return None  # Control frames are not application output.
        if opcode in {ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY}:  # Application data reaches the caller.
            self._mark_rx()  # Application data also proves the peer is alive.
            return FrameRead(opcode, data)  # The caller decides how to decode data.
        return None  # Unknown non-close frames do not produce data.

    def _check_keepalive(self) -> None:
        """Send ping or close a silent connection.

        Raises:
            ConnectionClosed: The peer stayed silent for two intervals.
        """
        quiet = self._now() - self._last_rx  # Measure silence since the last data or control frame.
        if quiet >= self._read_timeout_seconds * 2:  # Two quiet intervals means the peer is dead.
            FrameReader.close_socket(self._socket)  # Close before raising so the client loop wakes.
            raise ConnectionClosed(code=None, dropped=True)  # Silent peer close has no close code.
        if quiet >= self._read_timeout_seconds and not self._ping_sent:  # One quiet interval triggers keepalive.
            logger.debug("Sending WebSocket ping after quiet interval")  # High-frequency read path uses debug.
            self._socket.ping()  # websocket-client sends a ping control frame.
            self._ping_sent = True  # Wait for any frame before another ping.
            logger.debug("Sent WebSocket ping")  # Log after the keepalive action.

    def _mark_rx(self) -> None:
        """Mark the connection as recently alive."""
        self._last_rx = self._now()  # Reset the quiet timer.
        self._ping_sent = False  # A received frame answered any outstanding ping.

    def _wait_until_ready(self, timeout: float) -> bool:
        """Wait until the socket can be read without changing its timeout.

        Args:
            timeout: The application wait in seconds.

        Returns:
            True when recv_data can run.
        """
        raw_socket = getattr(self._socket, "sock", None)  # websocket-client stores the TCP or TLS socket here.
        if raw_socket is None:  # Unit-test fakes can expose only recv_data.
            return True  # Let the fake control its own timeout behavior.
        if self._tls_bytes_waiting(raw_socket):  # The TLS layer can hold a frame that select cannot see.
            return True  # recv_data reads the held frame without a network wait.
        readable, _writable, errored = select.select(
            [raw_socket], [], [raw_socket], max(0.0, timeout)
        )  # Wait without changing the socket timeout.
        if errored:  # Exceptional socket state is a transport loss.
            raise OSError("The WebSocket socket reported an error.")  # Map through read() to ConnectionClosed.
        return bool(readable)  # A readable socket can run recv_data now.

    @staticmethod
    def _tls_bytes_waiting(raw_socket: Any) -> bool:
        """Tell whether the TLS layer holds decrypted bytes.

        Why:
            One TLS record can carry two WebSocket frames. The TLS layer
            decrypts the full record, but recv_data reads only the first
            frame. The kernel buffer is then empty, so select reports no
            data. Without this check, the second frame waits until more
            network data arrives, which can take a full keepalive interval.

        Args:
            raw_socket: The TCP or TLS socket from websocket-client.

        Returns:
            True when the TLS layer holds bytes that recv_data can read now.
        """
        pending = getattr(raw_socket, "pending", None)  # Only an ssl.SSLSocket has pending().
        if not callable(pending):  # A plain TCP socket has no TLS buffer.
            return False  # select alone is correct for plain TCP.
        waiting = int(pending())  # Count the decrypted bytes that no read has taken yet.
        if waiting > 0:  # Log only the skip, because this check runs on every read.
            logger.debug("Skipping the socket wait: the TLS layer holds %d bytes.", waiting)  # Trace the skip.
        return waiting > 0  # Held bytes mean that recv_data can run now.

    def _now(self) -> float:
        """Return the current monotonic time.

        Returns:
            The clock value as a float.
        """
        return float(self._clock())  # The injected clock is callable.

    def _payload_bytes(self, payload: object) -> bytes:
        """Return payload bytes.

        Args:
            payload: The websocket-client frame payload.

        Returns:
            The payload as bytes.
        """
        if isinstance(payload, bytes):  # recv_data normally returns bytes.
            return payload  # Preserve exact bytes.
        if isinstance(payload, str):  # Some fakes can return text.
            return payload.encode("utf-8")  # Encode text fakes as UTF-8.
        return bytes(payload) if isinstance(payload, bytearray) else b""  # Unknown payloads become empty bytes.

    def _close_code(self, payload: bytes) -> int | None:
        """Return the WebSocket close code.

        Args:
            payload: The close frame payload.

        Returns:
            The close code, or 1005 when the close frame has no status code.
        """
        if len(payload) < 2:  # RFC 6455 section 7.1.5 defines 1005 for no status code.
            return 1005  # A close frame arrived, but it carried no status code.
        return int.from_bytes(payload[:2], "big")  # WebSocket close codes use big-endian bytes.


class FrameDecoder:
    """Decode Mist stream frames."""

    @staticmethod
    def event(frame: str | bytes) -> dict[str, object]:
        """Decode one WebSocket frame.

        Args:
            frame: One text or binary frame.

        Returns:
            A decoded event dictionary.
        """
        if isinstance(frame, bytes):  # Binary SDK frames can carry NUL bytes.
            text = frame.replace(b"\x00", b"").decode("utf-8", errors="replace")  # Match the SDK cleanup.
        else:
            text = frame.replace("\x00", "")  # Text frames get the same NUL removal for consistency.
        try:  # Preserve non-JSON stream text as raw data.
            decoded = json.loads(text)  # Mist stream frames are usually JSON objects.
        except json.JSONDecodeError:
            return {"raw": text}  # The SDK wraps non-JSON text this way.
        if isinstance(decoded, dict):  # Dict events are the normal stream shape.
            return decoded  # Preserve the event shape for filters.
        return {"data": decoded}  # Non-dict JSON stays available to callers.

    @staticmethod
    def data_payload(event: Mapping[str, object]) -> object:
        """Return the nested payload of a data event.

        Args:
            event: A decoded stream event.

        Returns:
            The decoded ``data`` value, or the original value when it is not JSON text.
        """
        payload = event.get("data")  # Mist puts command and capture data under this key.
        if not isinstance(payload, str):  # Already decoded payloads need no work.
            return payload  # Preserve dictionaries, lists, None, and numbers.
        if payload == "":  # Empty data is a valid edge value.
            return ""  # Do not convert an empty body to None.
        try:  # Decode nested JSON only when the data field holds JSON text.
            return json.loads(payload)  # Command data can be JSON text inside the event.
        except json.JSONDecodeError:
            return payload  # Malformed JSON stays as text for the caller to decide.
