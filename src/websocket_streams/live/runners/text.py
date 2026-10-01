"""Shape stream text before the page receives it.

Why:
    Issue #3551. Mist sends channel data and packet records in different forms.
    The page needs safe JSON and short packet summaries. Issue #3671 keeps the
    raw terminal bytes for xterm.js, so this module no longer changes them.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Channel messages can hold nested JSON strings.
import logging  # The text shapers log each conversion.
import re  # Shell output and SDK logs need pattern-based cleanup.
from collections.abc import Mapping  # Packet records are mapping-like data.

logger = logging.getLogger(__name__)  # Keep text shaper log records under this module.


class MessageShaper:
    """Convert raw stream messages to page-safe content."""

    def channel_message(self, message: object) -> tuple[str, object, str | None]:
        """Return the message kind, content, and channel source path.

        Args:
            message: The raw SDK WebSocket message.

        Returns:
            The message kind, the decoded content, and the source path.
        """
        logger.info("Shaping a WebSockets channel message")  # Log before parsing SDK data.
        if isinstance(message, Mapping):  # SDK channel messages are dictionaries.
            shaped = self._shape_mapping(message)  # Decode nested data when present.
            source = (
                message.get("channel") if isinstance(message.get("channel"), str) else None
            )  # Keep source path server-side.
            logger.debug("Shaped a WebSockets channel mapping")  # Log after parsing a mapping.
            return "json", shaped, source  # Channel mappings render as JSON.
        logger.debug("Shaped a WebSockets channel text message")  # Log after parsing plain text.
        return "text", str(message), None  # Non-mapping messages render as text.

    def _shape_mapping(self, message: Mapping[object, object]) -> dict[str, object]:
        """Decode the ``data`` field of one mapping when it is JSON text.

        Args:
            message: The raw SDK message mapping.

        Returns:
            A JSON-safe dictionary.
        """
        shaped = {str(key): value for key, value in message.items()}  # Convert keys to JSON object keys.
        data = shaped.get("data")  # Mist channel events often nest the record here.
        if isinstance(data, str):  # The WebSocket reference says data can be a JSON string.
            shaped["data"] = self._decode_json_text(data)  # Decode the string once more when possible.
        return shaped  # The message remains JSON-safe for the buffer.

    def _decode_json_text(self, text: str) -> object:
        """Decode JSON text, or return the original text.

        Args:
            text: The possible JSON text.

        Returns:
            The decoded value, or the original text.
        """
        try:  # Not every SDK message uses JSON text.
            decoded = json.loads(text)  # Decode a nested channel payload.
        except json.JSONDecodeError:  # The text is plain output.
            return text  # Keep the original value.
        return decoded  # Return the decoded JSON value.


class PacketSummary:
    """Build one plain summary line for a packet record."""

    @staticmethod
    def summarize(record: object) -> str:
        """Return a packet summary line.

        Args:
            record: The packet record from the SDK.

        Returns:
            A short line with time, source, destination, protocol, and length.
        """
        logger.info("Building a WebSockets packet summary")  # Log before reading packet fields.
        packet = record if isinstance(record, Mapping) else {}  # Non-mapping records have no fields.
        time_value = PacketSummary._text(packet, "timestamp", "time")  # Use either common time field.
        source = PacketSummary._text(packet, "src_ip", "src", "src_port")  # Use wired or wireless source fields.
        destination = PacketSummary._text(
            packet, "dst_ip", "dst", "dst_port"
        )  # Use wired or wireless destination fields.
        protocol = PacketSummary._text(packet, "proto", "protocol", "frame_type")  # Use any protocol-like field.
        length = PacketSummary._text(packet, "length", "len")  # Use either length field.
        summary = f"{time_value} {source} -> {destination} {protocol} {length}"  # The page shows one compact line.
        logger.debug("Built a WebSockets packet summary")  # Do not log packet content.
        return summary  # The buffer stores this line.

    @staticmethod
    def _text(packet: Mapping[object, object], *names: str) -> str:
        """Return the first present packet field as text.

        Args:
            packet: The packet mapping.
            names: The field names to try.

        Returns:
            The field value as text, or a dash.
        """
        for name in names:  # The SDK uses different names for wired and wireless packets.
            value = packet.get(name)  # Missing fields are valid.
            if value not in (None, ""):  # Empty values are not useful on the page.
                return str(value)  # Convert the value to display text.
        return "-"  # The contract asks for a dash when a field is absent.


class ShellAddressFilter(logging.Filter):
    """Remove Mist shell WebSocket addresses from log records."""

    ADDRESS_RE = re.compile(r"wss://\S+")  # The shell address can contain a session credential.

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact a WebSocket address from one log record.

        Args:
            record: The log record to check.

        Returns:
            True, so logging keeps the record.
        """
        rendered = record.getMessage()  # Render args before replacing secret text.
        redacted = self.ADDRESS_RE.sub("wss://[redacted]", rendered)  # Replace each full address.
        if redacted != rendered:  # Only mutate the record when it held a secret address.
            record.msg = redacted  # Store the redacted message.
            record.args = ()  # Clear args, because the message is already rendered.
        return True  # The logger should keep the record.
