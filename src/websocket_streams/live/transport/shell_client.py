"""Open one Mist shell or screen WebSocket connection.

Why:
    Issue #3671 needs a terminal-grade bidirectional client. This class sends
    input and resize frames while a reader thread receives output without
    the Mist channel marker byte.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Resize frames use JSON text.
import logging  # The client logs safe connection state.
import threading  # Send and read can run on different threads.
import time  # The default clock is monotonic.
from collections.abc import Callable  # Constructor types stay explicit.
from typing import Any  # websocket-client is not fully typed.

import websocket  # The feature uses websocket-client per the contract.
from src.websocket_streams.intake.fields import StreamRequestError  # Not-open sends use the HTTP contract.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, ShellAddressPolicy  # Connection helpers.
from src.websocket_streams.live.transport.frames import ConnectionClosed, FrameReader  # Shared frame reading.
from websocket import ABNF  # Binary fallback uses the websocket-client opcode.

logger = logging.getLogger(__name__)  # Keep shell client logs under this module.


class ShellClient:
    """Read and write one shell or screen WebSocket without the Mist channel marker."""

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        policy: ShellAddressPolicy,
        factory: Callable[..., Any] = websocket.create_connection,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Build the shell client.

        Args:
            endpoint: The connection parameter source.
            policy: The address policy.
            factory: The websocket factory, or a fake in tests.
            clock: The monotonic clock.
        """
        self._endpoint = endpoint  # The endpoint owns auth and TLS settings.
        self._policy = policy  # The policy prevents credential leaks.
        self._factory = factory  # Tests inject a controlled socket factory.
        self._clock = clock  # Tests can use a fake clock.
        self._socket: Any | None = None  # The socket exists after open.
        self._reader: FrameReader | None = None  # The frame reader exists after open.
        self._closed = threading.Event()  # close() wakes read loops quickly.
        self._lock = threading.Lock()  # Protect the socket reference.
        self._send_lock = threading.Lock()  # Preserve input and resize frame order.

    def open(self, url: str, cols: int, rows: int) -> None:
        """Open the shell WebSocket and send the initial size.

        Args:
            url: The shell address from the Mist REST trigger.
            cols: Initial terminal columns.
            rows: Initial terminal rows.
        """
        safe_url = self._policy.check(url)  # Refuse an unsafe URL before credentials are built.
        host = self._endpoint.host_label(safe_url)  # Logs can hold only the host.
        logger.info("Opening Mist shell WebSocket to host %s", host)  # Log before the network connection.
        socket = self._factory(
            safe_url,
            header=self._endpoint.headers(),
            cookie=self._endpoint.cookie(),
            sslopt=self._endpoint.sslopt(),
            enable_multithread=True,
            skip_utf8_validation=True,
        )  # Open with thread-safe websocket-client mode.
        socket.settimeout(0.1)  # A short timeout lets close() stop a blocked read.
        with self._lock:  # Publish the socket under the lock.
            self._socket = socket  # send(), resize(), and close() can now use it.
            self._reader = FrameReader(
                socket, self._closed, self._clock, self._endpoint.profile.read_timeout_seconds
            )  # Shared reader handles control frames.
            self._closed.clear()  # A new connection starts open.
        logger.debug("Opened Mist shell WebSocket to host %s", host)  # Do not log path or headers.
        self.resize(cols, rows)  # Send the terminal size immediately after open.

    def read(self, timeout: float | None = None) -> bytes | None:
        """Read one shell output frame.

        Args:
            timeout: Maximum wait in seconds, or None for one quiet interval.

        Returns:
            Output bytes with one leading Mist channel NUL removed, or None after a quiet interval.

        Raises:
            ConnectionClosed: The connection ended.
        """
        deadline = None if timeout is None else self._clock() + timeout  # None means one socket quiet interval.
        while not self._closed.is_set():  # Local close ends the read loop quickly.
            wait = (
                self._read_slice() if deadline is None else min(self._read_slice(), max(0.0, deadline - self._clock()))
            )  # Keep every receive shorter than the keepalive interval.
            if deadline is not None and wait <= 0:  # The requested wait expired.
                return None  # A quiet interval is not an error.
            frame = self._recv_once(wait)  # Receive with a short timeout.
            if frame is None:  # The socket timed out or returned a control frame.
                if deadline is None:  # The caller asked for one quiet interval.
                    return None  # Match the contract quiet result.
                continue  # The bounded wait can continue.
            return self._strip_channel_marker(frame)  # Remove only the Mist channel marker byte.
        raise ConnectionClosed(dropped=False)  # A local close is a clean end.

    def send(self, text: str) -> None:
        """Send terminal input as a binary frame.

        Args:
            text: The terminal input text.

        Raises:
            StreamRequestError: The socket is not open.
        """
        payload = b"\x00" + text.encode("utf-8")  # Mist shell input requires a leading NUL byte.
        logger.debug("Sending %s Mist shell input bytes", len(payload))  # Debug level: paste sends many chunks.
        with self._send_lock:  # Preserve input order across web threads.
            socket = self._open_socket()  # Refuse sends after close.
            self._send_binary(socket, payload)  # Send one binary frame.
        logger.debug("Sent %s Mist shell input bytes", len(payload))  # Log only the byte count.

    def resize(self, cols: int, rows: int) -> None:
        """Send the terminal size.

        Args:
            cols: Terminal columns.
            rows: Terminal rows.

        Raises:
            StreamRequestError: The socket is not open.
        """
        message = json.dumps({"resize": {"width": cols, "height": rows}})  # The shell protocol defines this shape.
        logger.debug("Sending Mist shell resize to %s columns and %s rows", cols, rows)  # Debug level: drags are busy.
        with self._send_lock:  # Keep resize order consistent with input frames.
            socket = self._open_socket()  # Refuse resize after close.
            socket.send(message)  # Resize is a text frame.
        logger.debug("Sent Mist shell resize to %s columns and %s rows", cols, rows)  # Log after send.

    def close(self) -> None:
        """Close the shell WebSocket from any thread."""
        logger.info("Closing Mist shell WebSocket")  # Log before changing state.
        self._closed.set()  # Reader loops see the local close within one socket timeout.
        with self._lock:  # Copy the socket while protected.
            socket = self._socket  # The socket can be None before open.
            self._socket = None  # Future sends fail as not open.
            self._reader = None  # Future reads cannot use the old socket.
        if socket is not None:  # close() before open is harmless.
            socket.close()  # websocket-client close wakes recv.
        logger.debug("Closed Mist shell WebSocket")  # Log after the close request.

    def _open_socket(self) -> Any:
        """Return the open socket.

        Returns:
            The current websocket object.

        Raises:
            StreamRequestError: The socket is not open.
        """
        socket = self._socket  # Copy the socket reference.
        if socket is None or self._closed.is_set():  # Sends after close must fail.
            raise StreamRequestError("not_open", "The shell connection is not open.")  # Contract refusal.
        return socket  # The caller can send while holding its own send lock.

    def _recv_once(self, timeout: float) -> bytes | None:
        """Receive one frame with a short timeout.

        Args:
            timeout: The socket timeout for this attempt.

        Returns:
            The frame payload, or None on a timeout or control frame.

        Raises:
            ConnectionClosed: The socket ended.
        """
        reader = self._reader  # Copy the current frame reader.
        if reader is None:  # A local close removed the reader.
            raise ConnectionClosed(dropped=False)  # The caller should end cleanly.
        frame = reader.read(timeout)  # The shared reader handles keepalive and close codes.
        return None if frame is None else frame.payload  # The caller removes any Mist channel marker.

    def _read_slice(self) -> float:
        """Return one bounded socket wait slice.

        Returns:
            A short wait that lets keepalive fire before two intervals pass.
        """
        interval = self._endpoint.profile.read_timeout_seconds  # The profile controls keepalive timing.
        return max(0.01, min(0.1, interval / 2))  # Keep a lower bound so sockets do not spin.

    def _strip_channel_marker(self, frame: bytes) -> bytes:
        """Remove one leading Mist channel marker byte from output.

        Args:
            frame: One shell or screen output frame.

        Returns:
            The frame after one leading NUL byte is removed, or the original frame.
        """
        return frame[1:] if frame.startswith(b"\x00") else frame  # Remove exactly one leading channel marker.

    def _send_binary(self, socket: Any, payload: bytes) -> None:
        """Send one binary frame.

        Args:
            socket: The open websocket object.
            payload: The binary payload.
        """
        if hasattr(socket, "send_binary"):  # websocket-client exposes this helper on real sockets.
            socket.send_binary(payload)  # Use the helper when present.
        else:
            socket.send(payload, opcode=ABNF.OPCODE_BINARY)  # Fakes or older clients can use the opcode form.
