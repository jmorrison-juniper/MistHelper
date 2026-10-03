"""Return message pages without decoding stored JSON text."""

from __future__ import annotations  # Keep Flask annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any  # Accept the session service by behavior.

from flask import Response  # Return the prebuilt JSON text.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Convert contract refusals.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.websocket_streams.web.blueprint.requests.message import MessageQuery  # Validate poll query values.
from src.websocket_streams.web.blueprint.responses.json_response import JsonResponse  # Reuse error conversion.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep polling fields safe and bounded.


class MessageResponse:
    """Read and return one message page."""

    @staticmethod
    def read(service: Any, session_id: str) -> Response | tuple[Response, int]:
        """Return one direct JSON message response."""
        try:  # Query and service checks share the request error type.
            after, limit = MessageQuery.values()  # Validate both query values.
            page = service.read(session_id, after, limit)  # Read one bounded message page.
            body = page.to_json_text()  # Join stored message JSON without a decode step.
            logger.emit(logging.DEBUG, "web.response.messages", {"byte_count": len(body)})  # Report size only.
            return Response(body, mimetype="application/json")  # Preserve the direct JSON response.
        except StreamRequestError as error:  # Convert a checked refusal to JSON.
            return JsonResponse.error(error)  # Preserve the standard error shape.
