"""Shape channel messages before the page receives them."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Channel data can contain one nested JSON string.
import logging  # Message shaping uses structured JSON records.
from collections.abc import Mapping  # Channel records are mapping-like data.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.


class MessageShaper:
    """Convert raw channel messages to page-safe content."""

    def channel_message(self, message: object) -> tuple[str, object, str | None]:
        """Return the message kind, content, and private source path."""
        logger.emit(logging.INFO, "channel_message_shape_started")  # Log before parsing remote data.
        if isinstance(message, Mapping):  # SDK-compatible channel messages are dictionaries.
            shaped = self._shape_mapping(message)  # Decode one nested data value when possible.
            channel = message.get("channel")  # Read the private routing path once.
            source = channel if isinstance(channel, str) else None  # Return the path only to the router.
            logger.emit(logging.DEBUG, "channel_message_shape_completed", {"status": "json"})
            return "json", shaped, source  # Channel mappings preserve the existing JSON message form.
        logger.emit(logging.DEBUG, "channel_message_shape_completed", {"status": "text"})
        return "text", str(message), None  # Non-mapping values preserve the existing text form.

    def _shape_mapping(self, message: Mapping[object, object]) -> dict[str, object]:
        """Decode the data field when it contains valid JSON text."""
        shaped = {str(key): value for key, value in message.items()}  # Convert keys to JSON object keys.
        data = shaped.get("data")  # Mist channel events often nest the record in this field.
        if not isinstance(data, str):  # Non-text data already has its final form.
            return shaped  # Preserve the original value.
        try:  # Plain output and cut frames are valid channel content.
            shaped["data"] = json.loads(data)  # Decode one complete nested JSON value.
        except json.JSONDecodeError:  # Invalid JSON must not fail the stream.
            logger.emit(logging.DEBUG, "channel_nested_json_unchanged", {"status": "invalid"})
        return shaped  # Preserve empty, invalid, and decoded data semantics.
