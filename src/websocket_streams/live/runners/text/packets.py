"""Build bounded display summaries for packet records."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Packet shaping uses structured JSON records.
from collections.abc import Mapping  # Packet records are mapping-like data.

from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.


class PacketSummary:
    """Build one plain summary line for a packet record."""

    @staticmethod
    def summarize(record: object) -> str:
        """Return time, source, destination, protocol, and length."""
        logger.emit(logging.INFO, "packet_summary_started")  # Log before reading packet fields.
        time_value, source, destination, protocol, length = PacketSummary._values(record)  # Read display fields.
        summary = f"{time_value} {source} -> {destination} {protocol} {length}"  # Preserve display form.
        logger.emit(logging.DEBUG, "packet_summary_completed", {"count": 5})  # Do not log packet content.
        return summary  # The session stores this short line with the packet record.

    @staticmethod
    def _values(record: object) -> tuple[str, str, str, str, str]:
        """Return packet display fields in summary order."""
        packet = record if isinstance(record, Mapping) else {}  # Non-mapping records have no fields.
        return (
            PacketSummary._text(packet, "timestamp", "time"),  # Use either common time field.
            PacketSummary._text(packet, "src_ip", "src", "src_port"),  # Use any source field.
            PacketSummary._text(packet, "dst_ip", "dst", "dst_port"),  # Use any destination field.
            PacketSummary._text(packet, "proto", "protocol", "frame_type"),  # Use any protocol field.
            PacketSummary._text(packet, "length", "len"),  # Use either length field.
        )

    @staticmethod
    def _text(packet: Mapping[object, object], *names: str) -> str:
        """Return the first present packet field as text."""
        for name in names:  # Wired and wireless packets use different field names.
            value = packet.get(name)  # Missing fields are valid.
            if value not in (None, ""):  # Empty values do not help the operator.
                return str(value)  # Preserve the existing display conversion.
        return "-"  # The page contract uses a dash for a missing value.
