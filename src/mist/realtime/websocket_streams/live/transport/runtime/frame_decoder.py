"""Decode Mist stream frames into safe Python values."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Mist stream data frames use JSON text.
import logging  # Decoder actions use the shared structured logger.
from collections.abc import Mapping  # Nested event payloads use mapping access.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Keep decoder logs bounded and free of frame content.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Share the transport logging boundary.


class SubscribeError(Exception):
    """A stream channel subscription failed."""

    def __init__(self, channel: str, detail: str) -> None:
        """Store the failed channel and the safe refusal detail."""
        super().__init__(f"Subscription failed for channel {channel}.")  # Keep the public error behavior.
        self.channel = channel  # Runners report the failed channel.
        self.detail = detail  # Runners report the refusal detail.


class FrameDecoder:
    """Decode Mist stream frames."""

    @staticmethod
    def event(frame: str | bytes) -> dict[str, object]:
        """Decode one WebSocket frame."""
        logger.emit(logging.DEBUG, "frame_decode_started", {"byte_count": len(frame)})  # Log before normalization.
        text = FrameDecoder._text(frame)  # Remove NUL bytes and decode binary frames.
        try:  # Preserve non-JSON stream text as raw data.
            decoded = json.loads(text)  # Decode the outer Mist event.
        except json.JSONDecodeError:
            logger.emit(logging.DEBUG, "frame_decode_completed", {"status": "raw"})  # Log the fallback result.
            return {"raw": text}  # Match the SDK fallback for non-JSON text.
        logger.emit(logging.DEBUG, "frame_decode_completed", {"status": "json"})  # Log the JSON result type.
        return decoded if isinstance(decoded, dict) else {"data": decoded}  # Preserve the prior event shape.

    @staticmethod
    def data_payload(event: Mapping[str, object]) -> object:
        """Decode the nested data field when it contains JSON text."""
        payload = event.get("data")  # Mist stores command and capture data under this key.
        if not isinstance(payload, str) or payload == "":  # Non-text and empty values need no JSON action.
            return payload  # Preserve dictionaries, lists, numbers, None, and empty text.
        return FrameDecoder._decode_payload(payload)  # Decode non-empty nested JSON text.

    @staticmethod
    def _decode_payload(payload: str) -> object:
        """Decode one non-empty nested payload."""
        logger.emit(logging.DEBUG, "payload_decode_started", {"byte_count": len(payload)})  # Log before decoding.
        try:  # Decode nested JSON only when the data field contains JSON text.
            decoded = json.loads(payload)  # Convert the nested JSON text to its Python value.
        except json.JSONDecodeError:
            logger.emit(logging.DEBUG, "payload_decode_completed", {"status": "raw"})  # Log the fallback result.
            return payload  # Keep malformed JSON text unchanged.
        logger.emit(logging.DEBUG, "payload_decode_completed", {"status": "json"})  # Log successful decoding.
        return decoded  # Return the decoded nested value.

    @staticmethod
    def _text(frame: str | bytes) -> str:
        """Return NUL-free frame text."""
        if isinstance(frame, bytes):  # Binary SDK frames can contain NUL bytes.
            return frame.replace(b"\x00", b"").decode("utf-8", errors="replace")  # Match SDK cleanup.
        return frame.replace("\x00", "")  # Apply the same cleanup to text frames.
