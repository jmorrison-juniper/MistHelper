"""A reusable fake Mist cloud WebSocket server for issue #3671 tests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import base64  # The WebSocket handshake needs a base64 accept value.
import hashlib  # The WebSocket handshake uses SHA-1 by RFC 6455.
import socket  # The fake cloud uses standard-library TCP sockets only.
import struct  # Frame headers use network byte order integer fields.
import threading  # Each accepted connection runs in one daemon thread.
from dataclasses import dataclass  # Records make tests clear and exact.
from typing import Any  # Device handlers are duck-typed test objects.


@dataclass(frozen=True, slots=True)
class FrameRecord:
    """One frame that the fake cloud received."""

    opcode: int  # The RFC 6455 opcode.
    payload: bytes  # The unmasked payload bytes.
    path: str  # The request path for this connection.
    connection: int  # The connection number.


@dataclass(frozen=True, slots=True)
class RequestRecord:
    """One WebSocket opening request."""

    path: str  # The request path.
    headers: dict[str, str]  # The request headers by lower-case name.
    connection: int  # The connection number.


class FakeConnection:
    """One accepted WebSocket connection."""

    def __init__(self, sock: socket.socket, path: str, number: int) -> None:
        """Build one connection handle."""
        self._sock = sock  # Device handlers send frames through this socket.
        self.path = path  # Tests and handlers need the request path.
        self.number = number  # Tests use stable connection numbers.
        self._send_lock = threading.Lock()  # Multiple handler threads can send safely.

    def send_text(self, text: str) -> None:
        """Send a text frame."""
        self._send_frame(0x1, text.encode("utf-8"))  # Text frames carry UTF-8 bytes.

    def send_text_bytes(self, data: bytes) -> None:
        """Send raw bytes in a text frame."""
        self._send_frame(0x1, data)  # Tests use this to split UTF-8 across frames.

    def send_binary(self, data: bytes) -> None:
        """Send a binary frame."""
        self._send_frame(0x2, data)  # Binary frames carry raw bytes.

    def send_pong(self, data: bytes) -> None:
        """Send a pong control frame."""
        self._send_frame(0xA, data)  # Pong replies to client ping frames.

    def send_close(self, code: int | None = 1000) -> None:
        """Send a close control frame and close the TCP socket."""
        payload = b"" if code is None else struct.pack("!H", code)  # None sends an empty close payload.
        self._send_frame(0x8, payload)  # RFC 6455 close frame.
        self.drop()  # End the underlying socket after the close frame.

    def drop(self) -> None:
        """Drop the TCP connection without a WebSocket close."""
        self._sock.close()  # Tests use this to simulate a broken network.

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        """Send one unmasked server frame."""
        header = self._frame_header(opcode, len(payload))  # Server frames are not masked.
        with self._send_lock:  # Do not interleave frames from concurrent handlers.
            self._sock.sendall(header + payload)  # Send the complete frame.

    def _frame_header(self, opcode: int, length: int) -> bytes:
        """Return an RFC 6455 frame header."""
        first = 0x80 | opcode  # The fake cloud sends complete frames.
        if length < 126:  # Small payloads use the short length field.
            return bytes([first, length])  # Return the two-byte header.
        if length <= 0xFFFF:  # Medium payloads use a 16-bit length.
            return bytes([first, 126]) + struct.pack("!H", length)  # Return header and length.
        return bytes([first, 127]) + struct.pack("!Q", length)  # Large payloads use a 64-bit length.


class FakeMistCloud:
    """A loopback RFC 6455 server with path-based device handlers."""

    def __init__(self) -> None:
        """Build a stopped fake cloud."""
        self._server: socket.socket | None = None  # The listening socket exists after start.
        self._stop = threading.Event()  # stop() asks all loops to end.
        self._accept_thread: threading.Thread | None = None  # The accept loop thread.
        self._threads: list[threading.Thread] = []  # Per-connection worker threads.
        self._connections: list[FakeConnection] = []  # Active handles can be dropped on stop.
        self._routes: dict[str, Any] = {}  # Request paths map to device handlers.
        self._lock = threading.Lock()  # Shared records and counters need protection.
        self._condition = threading.Condition(self._lock)  # Tests wait for requests and pings with a bound.
        self._connection_count = 0  # Each connection gets a stable number.
        self.frames: list[FrameRecord] = []  # Tests assert exact received frames.
        self.pings: list[FrameRecord] = []  # Tests assert keepalive pings.
        self.requests: list[RequestRecord] = []  # Tests assert headers and cookies.
        self.answer_pings = True  # Tests can simulate a dead peer by disabling pong answers.
        self.port = 0  # The OS assigns the port during start.

    @property
    def base_ws_url(self) -> str:
        """Return the loopback WebSocket base URL."""
        return f"ws://127.0.0.1:{self.port}"  # Tests compose paths from this base.

    def register(self, path: str, handler: Any) -> None:
        """Register a device handler for a request path."""
        self._routes[path] = handler  # The accept worker uses this route table.

    def wait_for_requests(self, expected_count: int, timeout: float) -> list[RequestRecord]:
        """Wait until the fake cloud records enough requests."""
        with self._condition:  # Wait on the same condition that records requests.
            self._condition.wait_for(lambda: len(self.requests) >= expected_count, timeout=timeout)  # Bound the wait.
            return list(self.requests)  # Return a snapshot for exact assertions.

    def wait_for_pings(self, expected_count: int, timeout: float) -> list[FrameRecord]:
        """Wait until the fake cloud records enough pings."""
        with self._condition:  # Wait on the same condition that records pings.
            self._condition.wait_for(lambda: len(self.pings) >= expected_count, timeout=timeout)  # Bound the wait.
            return list(self.pings)  # Return a snapshot for exact assertions.

    def start(self) -> FakeMistCloud:
        """Start the fake cloud."""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP listener.
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse loopback quickly in tests.
        self._server.bind(("127.0.0.1", 0))  # Bind to a free loopback port.
        self._server.listen()  # Start accepting connections.
        self.port = int(self._server.getsockname()[1])  # Publish the selected port.
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)  # Build the accept worker.
        self._accept_thread.start()  # Start accepting in the background.
        return self  # Context managers and fixtures use the server value.

    def stop(self) -> None:
        """Stop the fake cloud and all connections."""
        self._stop.set()  # Tell worker loops to end.
        if self._server is not None:  # The server may never have started.
            self._server.close()  # Closing the listener wakes accept.
        for connection in list(self._connections):  # Copy so drops cannot mutate while iterating.
            connection.drop()  # End each client socket.
        if self._accept_thread is not None:  # The accept thread exists after start.
            self._accept_thread.join(timeout=1.0)  # Bound shutdown time.
        for thread in list(self._threads):  # Copy so completed workers are safe.
            thread.join(timeout=1.0)  # Each test must leave no live worker.

    def __enter__(self) -> FakeMistCloud:
        """Start and return the fake cloud."""
        return self.start()  # Context managers should start the server.

    def __exit__(self, *_args: object) -> None:
        """Stop the fake cloud."""
        self.stop()  # Context managers must clean up threads.

    def _accept_loop(self) -> None:
        """Accept connections until stop."""
        assert self._server is not None  # start() sets the listener before the thread starts.
        while not self._stop.is_set():  # stop() ends the accept loop.
            try:  # Accept sockets until stop closes the listener.
                client, _address = self._server.accept()  # Wait for one client.
            except OSError:
                break  # The listener closed during stop.
            thread = threading.Thread(target=self._serve_client, args=(client,), daemon=True)  # Build worker.
            self._threads.append(thread)  # stop() joins every worker.
            thread.start()  # Serve this connection in the background.

    def _serve_client(self, client: socket.socket) -> None:
        """Handle one accepted TCP client."""
        client.settimeout(0.2)  # Timeouts let stop() end the loop.
        try:  # Drop incomplete or closed connections without failing the test.
            path, headers = self._handshake(client)  # Complete the WebSocket opening handshake.
            connection = self._new_connection(client, path, headers)  # Record the accepted connection.
            handler = self._routes.get(path)  # Route the request path to a device.
            if hasattr(handler, "on_connect"):  # Devices can send a banner immediately.
                handler.on_connect(connection)  # Notify the handler after the handshake.
            self._read_loop(client, connection, handler)  # Process frames until the connection ends.
        except OSError:
            client.close()  # Drop incomplete connections quietly.
        finally:
            client.close()  # Ensure the socket is closed on every path.

    def _handshake(self, client: socket.socket) -> tuple[str, dict[str, str]]:
        """Read and answer one opening handshake."""
        request = self._read_http_request(client)  # The request ends at a blank line.
        lines = request.decode("iso-8859-1").split("\r\n")  # HTTP headers are ISO-8859-1 bytes.
        path = lines[0].split(" ")[1]  # The request line is GET <path> HTTP/1.1.
        headers = self._parse_headers(lines[1:])  # Keep lower-case header names for assertions.
        accept = self._accept_value(headers["sec-websocket-key"])  # RFC 6455 accept value.
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )  # The minimal server handshake.
        client.sendall(response.encode("ascii"))  # Send the handshake answer.
        return path, headers  # The worker records this request.

    def _read_http_request(self, client: socket.socket) -> bytes:
        """Read the HTTP opening request."""
        data = b""  # Accumulate headers until the blank line.
        while b"\r\n\r\n" not in data:  # The handshake ends with a blank line.
            chunk = client.recv(4096)  # Handshake headers are small.
            if chunk == b"":  # The client closed before finishing the request.
                raise OSError("handshake closed")  # The worker drops the socket.
            data += chunk  # Keep reading until the header terminator.
        return data  # Return the complete header block.

    def _parse_headers(self, lines: list[str]) -> dict[str, str]:
        """Parse HTTP headers."""
        headers: dict[str, str] = {}  # Tests use lower-case header names.
        for line in lines:  # Each non-empty line can hold one header.
            if ":" in line:  # Skip the final empty line.
                name, value = line.split(":", 1)  # Header names cannot contain a colon.
                headers[name.strip().lower()] = value.strip()  # Normalize for assertions.
        return headers  # Return parsed request headers.

    def _accept_value(self, key: str) -> str:
        """Return the RFC 6455 accept value."""
        magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # RFC 6455 GUID.
        digest = hashlib.sha1((key + magic).encode("ascii")).digest()  # RFC 6455 uses SHA-1 here.
        return base64.b64encode(digest).decode("ascii")  # The response header is base64 text.

    def _new_connection(self, client: socket.socket, path: str, headers: dict[str, str]) -> FakeConnection:
        """Record and return one connection."""
        with self._lock:  # Protect the counter and request records.
            self._connection_count += 1  # Assign the next connection number.
            number = self._connection_count  # Keep the number stable outside the lock.
            self.requests.append(RequestRecord(path, headers, number))  # Tests can assert headers later.
            self._condition.notify_all()  # Wake tests that wait for a connection.
        connection = FakeConnection(client, path, number)  # Device handlers use this connection handle.
        self._connections.append(connection)  # stop() closes each active connection.
        return connection  # The worker uses this object for frames.

    def _read_loop(self, client: socket.socket, connection: FakeConnection, handler: Any) -> None:
        """Read WebSocket frames from one client."""
        partial_opcode = 0  # Continuation frames need the first opcode.
        partial_payload = b""  # Continuation frames append to this buffer.
        while not self._stop.is_set():  # stop() ends each connection loop.
            frame = self._read_frame(client)  # Read one frame or raise on close.
            if frame is None:  # A timeout lets the loop check the stop event.
                continue  # Keep the connection open.
            opcode, payload, fin = frame  # Unpack the RFC 6455 frame.
            if opcode == 0x8:  # The client requested a WebSocket close.
                connection.send_close()  # Echo a normal close.
                break  # End this connection worker.
            if opcode == 0x9:  # The client sent a ping.
                with self._condition:  # Protect ping records and wake waiters.
                    self.pings.append(FrameRecord(opcode, payload, connection.path, connection.number))  # Record pings.
                    self._condition.notify_all()  # Wake tests that wait for keepalive.
                if self.answer_pings:  # Tests can disable pongs to simulate a dead peer.
                    connection.send_pong(payload)  # RFC 6455 requires a pong.
                continue  # Control frames are not device input.
            if opcode == 0x0:  # Continuation frame.
                partial_payload += payload  # Append to the in-progress message.
                if fin:  # The complete message is now ready.
                    self._dispatch_frame(handler, connection, partial_opcode, partial_payload)  # Deliver combined data.
                    partial_payload = b""  # Reset continuation state.
                continue  # Wait for the next frame.
            if not fin:  # Start a fragmented message.
                partial_opcode = opcode  # Remember the original opcode.
                partial_payload = payload  # Store the first fragment.
                continue  # Wait for continuations.
            self._dispatch_frame(handler, connection, opcode, payload)  # Deliver complete unfragmented data.

    def _dispatch_frame(self, handler: Any, connection: FakeConnection, opcode: int, payload: bytes) -> None:
        """Record and route one client frame."""
        self.frames.append(FrameRecord(opcode, payload, connection.path, connection.number))  # Keep exact bytes.
        if hasattr(handler, "receive"):  # A device can react to client input.
            handler.receive(connection, opcode, payload)  # Deliver the frame to the device.

    def _read_frame(self, client: socket.socket) -> tuple[int, bytes, bool] | None:
        """Read and unmask one client frame."""
        try:  # Return None on timeout so the worker can check stop state.
            header = client.recv(2)  # Every WebSocket frame starts with two bytes.
        except TimeoutError:
            return None  # A quiet socket stays open.
        if header == b"":  # The TCP connection closed.
            raise OSError("socket closed")  # End the connection worker.
        first, second = header  # Split the base frame header.
        fin = bool(first & 0x80)  # The high bit marks the final fragment.
        opcode = first & 0x0F  # The low four bits hold the opcode.
        masked = bool(second & 0x80)  # Clients must mask all frames.
        length = second & 0x7F  # The low seven bits hold or signal the payload length.
        if length == 126:  # A 16-bit length follows.
            length = struct.unpack("!H", self._recv_exact(client, 2))[0]  # Read medium length.
        elif length == 127:  # A 64-bit length follows.
            length = struct.unpack("!Q", self._recv_exact(client, 8))[0]  # Read large length.
        mask = self._recv_exact(client, 4) if masked else b"\x00\x00\x00\x00"  # RFC clients always send this.
        payload = self._recv_exact(client, length) if length else b""  # Read the payload bytes.
        unmasked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))  # Remove client mask.
        return opcode, unmasked, fin  # Return a complete decoded frame.

    def _recv_exact(self, client: socket.socket, count: int) -> bytes:
        """Read an exact byte count."""
        data = b""  # Accumulate until enough bytes arrive.
        while len(data) < count:  # TCP can split reads.
            chunk = client.recv(count - len(data))  # Ask only for the missing bytes.
            if chunk == b"":  # The client closed early.
                raise OSError("socket closed")  # End the worker.
            data += chunk  # Append this TCP segment.
        return data  # Return the requested byte count.
