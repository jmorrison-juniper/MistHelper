"""Fake Mist cloud devices for issue #3671 transport tests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The fake stream and shell protocols use JSON frames.
import threading  # Devices expose wait helpers and protect records.
import time  # Some tests need delayed fake output.
from collections.abc import Iterable  # Output helper methods accept line iterables.

from tests.support.fake_mist_cloud.server import FakeConnection  # Device handlers send through server connections.


class StreamDevice:
    """A fake Mist stream device for subscriptions, commands, and captures."""

    def __init__(self) -> None:
        """Build an empty stream device."""
        self.refusals: dict[str, str] = {}  # Tests can refuse selected channels.
        self._connections: list[FakeConnection] = []  # Publish sends to subscribed connections.
        self._subscribed: dict[int, set[str]] = {}  # Track channels per connection.
        self._lock = threading.Lock()  # Protect connection and subscription state.

    def on_connect(self, connection: FakeConnection) -> None:
        """Record a new stream connection."""
        with self._lock:  # Multiple clients can connect during reliability tests.
            self._connections.append(connection)  # Publish methods send to these connections.
            self._subscribed[connection.number] = set()  # The connection starts with no channels.

    def receive(self, connection: FakeConnection, opcode: int, payload: bytes) -> None:
        """Handle a subscribe frame."""
        if opcode != 0x1:  # Stream subscriptions use text frames.
            return  # Binary frames are ignored by this fake stream.
        body = json.loads(payload.decode("utf-8"))  # Tests send valid subscribe JSON.
        channel = str(body.get("subscribe", ""))  # The Mist protocol uses this key.
        if channel in self.refusals:  # Tests can force a subscription failure.
            answer = {"event": "subscribe_failed", "channel": channel, "detail": self.refusals[channel]}  # Shape.
            connection.send_text(json.dumps(answer))  # Send the refusal as a text frame.
            return  # Do not mark a refused channel as subscribed.
        with self._lock:  # Subscription state is shared with publish().
            self._subscribed.setdefault(connection.number, set()).add(channel)  # Mark the channel ready.
        connection.send_text(json.dumps({"event": "channel_subscribed", "channel": channel}))  # Confirm subscribe.

    def refuse(self, channel: str, detail: str) -> None:
        """Refuse a channel with a detail string."""
        self.refusals[channel] = detail  # receive() uses this map.

    def publish(self, channel: str, data: object) -> None:
        """Publish one data event to subscribed connections."""
        payload = json.dumps(data) if not isinstance(data, str) else data  # Mist often sends JSON text in data.
        event = json.dumps({"event": "data", "channel": channel, "data": payload})  # Stream data event shape.
        for connection in self._matching_connections(channel):  # Only subscribed clients should receive this event.
            connection.send_text(event)  # Send one text frame.

    def publish_command_lines(
        self, channel: str, session_id: str, lines: Iterable[str], delay_seconds: float = 0.0
    ) -> None:
        """Publish command raw lines for one session."""
        for line in lines:  # Each line becomes one command event.
            self.publish(channel, {"session": session_id, "raw": line})  # Match the command stream shape.
            if delay_seconds > 0.0:  # Tests can simulate slow devices.
                time.sleep(delay_seconds)  # Keep the delay bounded in tests.

    def publish_command_noise(self, channel: str, session_id: str, raw: str) -> None:
        """Publish a command event for a different session."""
        self.publish(channel, {"session": session_id, "raw": raw})  # Filters must drop this noise.

    def publish_capture(self, channel: str, capture_id: str, pcap_dict: dict[str, object]) -> None:
        """Publish one packet capture event."""
        self.publish(channel, {"capture_id": capture_id, "pcap_dict": pcap_dict})  # Match capture stream shape.

    def drop(self) -> None:
        """Drop each current stream connection."""
        for connection in list(self._connections):  # Copy to avoid mutation during iteration.
            connection.drop()  # Simulate a broken network without a close frame.

    def _matching_connections(self, channel: str) -> list[FakeConnection]:
        """Return connections subscribed to a channel."""
        with self._lock:  # Read connection and subscription state together.
            return [
                connection
                for connection in self._connections
                if channel in self._subscribed.get(connection.number, set())
            ]  # Return a snapshot for sending outside the lock.


class ShellDevice:
    """A fake terminal shell device."""

    def __init__(self, prompt: str = "device> ") -> None:
        """Build one shell device."""
        self.prompt = prompt  # Tests can use a stable prompt.
        self.received_frames: list[bytes] = []  # Keep binary payloads with the NUL prefix intact.
        self.resize_frames: list[dict[str, object]] = []  # Keep resize frame bodies.
        self._input_chunks: list[bytes] = []  # Store input after NUL removal.
        self._line = bytearray()  # The current command line.
        self._condition = threading.Condition()  # wait_for_input uses this condition.
        self._connection: FakeConnection | None = None  # The open shell connection.
        self._fullscreen = False  # Full-screen mode exits on q.

    @property
    def received_input(self) -> bytes:
        """Return all input bytes after NUL removal."""
        with self._condition:  # Protect the chunk list.
            return b"".join(self._input_chunks)  # Tests compare exact paste bytes.

    def on_connect(self, connection: FakeConnection) -> None:
        """Send the shell banner and prompt."""
        self._connection = connection  # Later command handlers send on this connection.
        connection.send_text("Welcome to Fake Mist Shell\r\n")  # Send a banner like a real device.
        self._send_prompt()  # Prompt includes bracketed paste mode.

    def receive(self, connection: FakeConnection, opcode: int, payload: bytes) -> None:
        """Handle input and resize frames."""
        if opcode == 0x1:  # Resize messages are text JSON frames.
            with self._condition:  # Protect resize records and wake waiters.
                self.resize_frames.append(json.loads(payload.decode("utf-8")))  # Tests assert the exact size frame.
                self._condition.notify_all()  # Wake wait_for_resize.
            return  # Resize has no terminal echo.
        if opcode != 0x2:  # Shell input uses binary frames only.
            return  # Ignore unsupported frames.
        self.received_frames.append(payload)  # Keep the NUL prefix for protocol tests.
        data = payload[1:] if payload.startswith(b"\x00") else payload  # The shell protocol uses one NUL prefix.
        with self._condition:  # Protect input chunks and wake waiters.
            self._input_chunks.append(data)  # Tests compare input after NUL removal.
            self._condition.notify_all()  # Wake wait_for_input.
        self._process_input(connection, data)  # Echo and command handling happens after recording.

    def wait_for_input(self, expected_length: int, timeout: float) -> bytes:
        """Wait until at least the expected input length arrives."""
        deadline = time.monotonic() + timeout  # Bound every test wait.
        with self._condition:  # Wait with the same condition that receive() notifies.
            while len(b"".join(self._input_chunks)) < expected_length:  # Stop when enough bytes arrived.
                remaining = deadline - time.monotonic()  # Keep the wait bounded.
                if remaining <= 0:  # The timeout expired.
                    break  # Return what arrived for exact failure evidence.
                self._condition.wait(timeout=remaining)  # Sleep until input or timeout.
            return b"".join(self._input_chunks)  # Return the received bytes.

    def drop(self) -> None:
        """Drop the current shell connection."""
        if self._connection is not None:  # A device can drop only after connect.
            self._connection.drop()  # Simulate a TCP loss with no close frame.

    def wait_for_resize(self, expected_count: int, timeout: float) -> list[dict[str, object]]:
        """Wait until at least the expected resize count arrives."""
        deadline = time.monotonic() + timeout  # Bound every test wait.
        with self._condition:  # Wait with the same condition that receive() notifies.
            while len(self.resize_frames) < expected_count:  # Stop when enough resize frames arrived.
                remaining = deadline - time.monotonic()  # Keep the wait bounded.
                if remaining <= 0:  # The timeout expired.
                    break  # Return what arrived for exact failure evidence.
                self._condition.wait(timeout=remaining)  # Sleep until resize or timeout.
            return list(self.resize_frames)  # Return a snapshot for assertions.

    def _process_input(self, connection: FakeConnection, data: bytes) -> None:
        """Echo input and run complete lines."""
        for byte in data:  # Process byte-by-byte like a terminal.
            if self._fullscreen and byte == ord("q"):  # The fake full-screen program exits on q.
                connection.send_text("\x1b[?1049l")  # Leave the alternate screen.
                self._fullscreen = False  # The shell returns to normal mode.
                self._send_prompt()  # Show the prompt after exiting.
                continue  # Do not echo q as a command.
            if byte == 3:  # Ctrl+C interrupts the shell line.
                self._line.clear()  # The current line is canceled.
                connection.send_text("^C\r\n")  # Real shells echo the interrupt marker.
                self._send_prompt()  # Show a fresh prompt.
                continue  # Continue processing any later bytes.
            connection.send_binary(bytes([byte]))  # Echo typed characters.
            if byte in (10, 13):  # Enter runs the line.
                line = self._line.decode("utf-8", errors="replace").strip()  # Decode the command text.
                self._line.clear()  # Start a new line buffer.
                self._run_line(connection, line)  # Run the fake command.
            else:
                self._line.append(byte)  # Keep text until Enter.

    def _run_line(self, connection: FakeConnection, line: str) -> None:
        """Run one fake shell line."""
        if line == "exit":  # The shell closes normally on exit.
            connection.send_text("\r\nlogout\r\n")  # Send a small close notice.
            connection.send_close(1000)  # Normal close.
            return  # Do not send another prompt.
        if line == "fullscreen":  # Tests use this to exercise alternate screen output.
            self._fullscreen = True  # q exits this fake program.
            connection.send_text("\x1b[?1049h\x1b[2J\x1b[1;1H\x1b[31mRED\x1b[0m")  # Draw colored text.
            return  # The program owns the screen until q.
        if line == "big":  # Performance tests request about 1 MB of output.
            connection.send_text("X" * 1_048_576)  # Send one large text frame.
            self._send_prompt()  # Return to the prompt after output.
            return  # The big command is complete.
        connection.send_text(f"\r\nran: {line}\r\n")  # General command output.
        self._send_prompt()  # Show the prompt after each command.

    def _send_prompt(self) -> None:
        """Send the prompt with bracketed paste mode enabled."""
        if self._connection is not None:  # A prompt can be sent only after connect.
            self._connection.send_text("\x1b[?2004h" + self.prompt)  # Bracketed paste turns on at the prompt.


class ScreenDevice:
    """A fake live screen device that splits control sequences."""

    def __init__(self, updates: int = 1) -> None:
        """Build one screen device."""
        self.updates = updates  # Tests set how many updates to send.

    def on_connect(self, connection: FakeConnection) -> None:
        """Send configured screen updates."""
        for index in range(self.updates):  # Each update splits one CSI sequence.
            connection.send_text("\x1b[")  # Split inside the escape sequence.
            connection.send_text(f"2J\x1b[1;1Hscreen update {index}\r\n")  # Complete and draw the screen.
