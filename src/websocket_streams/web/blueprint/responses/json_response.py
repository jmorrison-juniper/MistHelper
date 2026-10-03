"""Convert service payloads and request errors to JSON responses."""

from __future__ import annotations  # Keep Flask annotations lazy.

import logging  # Structured events use repository handlers.
from collections.abc import Callable  # Type one bounded service action.

from flask import Response, jsonify  # Build the established JSON answers.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Convert contract refusals.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep error fields safe and bounded.


class JsonResponse:
    """Run one service action and return the HTTP contract."""

    @staticmethod
    def call(action: Callable[[], dict[str, object] | None], success: int = 200) -> Response | tuple[Response, int]:
        """Return one JSON success or contract error."""
        try:  # Service and request classes use one checked exception type.
            logger.emit(logging.DEBUG, "web.response.json.start")  # Record the bounded response action.
            payload = action() or {"ok": True}  # Preserve the empty-success confirmation.
            logger.emit(logging.DEBUG, "web.response.json.finish", {"count": len(payload)})  # Report key count only.
            return (jsonify(payload), success) if success != 200 else jsonify(payload)  # Preserve status behavior.
        except StreamRequestError as error:  # Convert a checked refusal to JSON.
            return JsonResponse.error(error)  # Keep one error conversion boundary.

    @staticmethod
    def error(error: StreamRequestError) -> tuple[Response, int]:
        """Return the shared error payload and status."""
        logger.emit(logging.DEBUG, "web.response.error", {"code": error.code})  # Log only the bounded error code.
        return jsonify(error.to_payload()), error.status  # Preserve the established error shape.
