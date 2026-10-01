"""A short local WebSocket fixture for the actual mistapi client."""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import socketserver
import struct
import threading
from contextlib import suppress
from types import SimpleNamespace
from typing import cast

from tests.unit.websocket_streams.live.captures.support.portal import PacketEvents
from tests.unit.websocket_streams.live.captures.support.sdk import FakeMistSession, Identities


class PacketStreamServer(socketserver.ThreadingTCPServer):
    """Keep each connection in the local fixture's ownership group."""

    daemon_threads = True
    block_on_close = True

    def __init__(self, stream: LocalPacketStream) -> None:
        """Bind only the loopback interface and an unused ephemeral port."""
        self.stream = stream
        super().__init__(("127.0.0.1", 0), PacketStreamHandler)


class PacketStreamHandler(socketserver.StreamRequestHandler):
    """Handle only the WebSocket frames that the SDK capture tests need."""

    def handle(self) -> None:
        """Confirm a real subscribe frame and release the connection on close."""
        stream = cast(PacketStreamServer, self.server).stream
        try:
            self.upgrade(stream)
            opcode, payload = self.read_frame()
            command = json.loads(payload)
            if opcode != 1 or command != {"subscribe": f"/sites/{Identities.SITE}/pcaps"}:
                raise ValueError("The local fixture received an unexpected subscription.")
            with stream.state.lock:
                stream.state.clients.add(self)
                self.send_frame(
                    1, json.dumps({"event": "channel_subscribed", "channel": command["subscribe"]}).encode()
                )
                stream.state.acknowledgements += 1
                stream.state.subscribed.set()
            while True:
                opcode, payload = self.read_frame()
                if opcode == 8:
                    self.send_frame(8, payload)
                    break
                if opcode == 9:
                    self.send_frame(10, payload)
        except (ConnectionError, OSError, EOFError):
            stream.state.disconnected.set()
        finally:
            with stream.state.lock:
                stream.state.clients.discard(self)

    def upgrade(self, stream: LocalPacketStream) -> None:
        """Check synthetic authentication and perform the standard handshake."""
        self.request.settimeout(15.0)
        request_line = self.rfile.readline(4096)
        if request_line != b"GET /api-ws/v1/stream HTTP/1.1\r\n":
            raise ValueError("The local fixture received an unexpected stream path.")
        headers: dict[str, str] = {}
        for _header in range(32):
            line = self.rfile.readline(4096)
            if line == b"\r\n":
                break
            name, _, value = line.decode("ascii").partition(":")
            headers[name.lower()] = value.strip()
        expected = "Token " + stream.api._apitoken[stream.api._apitoken_index]
        if headers.get("authorization") != expected:
            raise ValueError("The local fixture received invalid synthetic authentication.")
        key = headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        accept = base64.b64encode(hashlib.sha1(key.encode("ascii"), usedforsecurity=False).digest()).decode("ascii")
        self.request.sendall(
            (
                "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii")
        )

    def read_frame(self) -> tuple[int, bytes]:
        """Decode a bounded masked client frame."""
        head = self.rfile.read(2)
        if len(head) != 2:
            raise EOFError("The local stream ended.")
        length = head[1] & 127
        if length == 126:
            length = struct.unpack("!H", self.rfile.read(2))[0]
        if length == 127 or length > 8192 or not head[1] & 128:
            raise ValueError("The local fixture refused an invalid frame.")
        mask = self.rfile.read(4)
        payload = self.rfile.read(length)
        if len(mask) != 4 or len(payload) != length:
            raise EOFError("The local frame ended early.")
        return head[0] & 15, bytes(value ^ mask[index % 4] for index, value in enumerate(payload))

    def send_frame(self, opcode: int, payload: bytes) -> None:
        """Send one unmasked server frame through the owned local socket."""
        head = (
            struct.pack("!BB", 128 | opcode, len(payload))
            if len(payload) < 126
            else struct.pack("!BBH", 128 | opcode, 126, len(payload))
        )
        self.request.sendall(head + payload)


class LocalPacketStream:
    """Own a real local stream, its server thread, and its connection count."""

    def __init__(self, api: FakeMistSession) -> None:
        """Start a bounded server with no remote address or production packet data."""
        self.api = api
        self.state = SimpleNamespace(
            clients=set(),
            lock=threading.RLock(),
            subscribed=threading.Event(),
            acknowledgements=0,
            disconnected=threading.Event(),
        )
        self.server = PacketStreamServer(self)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        """Return the controlled local endpoint for the SDK fixture."""
        return f"ws://127.0.0.1:{self.server.server_address[1]}/api-ws/v1/stream"

    def packet(self, timestamp: int) -> None:
        """Send one synthetic nested JSON event through the real socket."""
        message = PacketEvents.packet(timestamp)
        message["data"] = json.dumps(message["data"])
        payload = json.dumps(message).encode("ascii")
        with self.state.lock:
            clients = tuple(self.state.clients)
            if not clients:
                raise AssertionError("The local packet stream has no confirmed subscriber.")
            for client in clients:
                client.send_frame(1, payload)

    def close(self) -> None:
        """Release every owned connection and the local server thread."""
        with self.state.lock:
            clients = tuple(self.state.clients)
        for client in clients:
            with suppress(OSError):
                client.request.shutdown(socket.SHUT_RDWR)
            client.request.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3.0)
        assert not self.thread.is_alive(), "The fixture left a local stream server running."
        assert not self.state.clients, "The fixture left a local stream connection open."
