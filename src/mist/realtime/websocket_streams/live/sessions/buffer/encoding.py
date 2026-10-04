"""Encode and bound one WebSocket message content value."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Content stays as compact ASCII JSON text.
import logging  # Content shaping uses the shared structured logger.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.


class MessageContentEncoder:
    """Encode message content and shorten oversized values."""

    MAX_MESSAGE_BYTES = 256 * 1024  # Preserve the existing single-message limit.

    def __init__(self) -> None:
        """Build one encoder with the shared structured logger."""
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep records bounded and content-free.

    def encode(self, content: object) -> tuple[str, int, bool]:
        """Return compact content text, original size, and shortening state."""
        encoded = json.dumps(
            content, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":")
        )  # Encode once.
        if len(encoded) <= self.MAX_MESSAGE_BYTES:  # Keep content that fits the existing limit.
            return encoded, len(encoded), False  # Report the unchanged compact text.
        self._logger.emit(logging.INFO, "session_message_shorten_start", {"byte_count": len(encoded)})  # Log size only.
        shortened = self._shortened(encoded)  # Build the bounded preview payload.
        self._logger.emit(logging.DEBUG, "session_message_shorten_complete", {"status": "shortened"})  # Confirm safely.
        return shortened, len(encoded), True  # Preserve the original size and shortening flag.

    def _shortened(self, encoded: str) -> str:
        """Return the compact shortened-content payload."""
        preview = {
            "shortened": True,
            "preview": encoded[: self.MAX_MESSAGE_BYTES],
        }  # Preserve the existing safe prefix.
        return json.dumps(preview, ensure_ascii=True, sort_keys=True, separators=(",", ":"))  # Keep compact ASCII JSON.
