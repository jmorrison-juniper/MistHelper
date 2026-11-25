"""Stream one WebSocket session buffer as JSON Lines."""

from __future__ import annotations  # Keep Flask annotations lazy.

import logging  # Structured events use repository handlers.

from flask import Response, request  # Stream JSON Lines or return one bounded archive.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Convert contract refusals.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Reuse error conversion.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep download fields safe and bounded.


class DownloadResponse:
    """Build the streamed session download response."""

    @staticmethod
    def download(session_id: str) -> Response | tuple[Response, int]:
        """Return one JSON Lines attachment."""
        try:  # An unknown session can refuse the stream setup.
            services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
            filename, lines = services.artifacts.download(session_id)  # Get safe stream parts.
            logger.emit(logging.DEBUG, "web.response.download.ready", {"status": "ready"})  # Log no filename.
            return Response(
                lines,
                mimetype="application/x-ndjson",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )  # Preserve streamed download headers.
        except StreamRequestError as error:  # Convert a checked refusal to JSON.
            return JsonResponse.error(error)  # Preserve the standard error shape.

    @staticmethod
    def batch_zip(session_id: str) -> Response | tuple[Response, int]:
        """Return one completed Multi Site result archive, or the combined CSV report of a hardware run."""
        selected = request.args.get("format")  # Only two named outputs exist.
        if set(request.args) != {"format"} or selected not in {"zip", "csv"}:
            return JsonResponse.error(
                StreamRequestError("bad_request", "The batch download requires format=zip or format=csv.")
            )
        try:
            services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
            reader = services.artifacts.csv_download if selected == "csv" else services.artifacts.zip_download
            filename, content = reader(session_id)  # Copy a bounded pinned snapshot.
            logger.emit(logging.DEBUG, "web.response.batch_download.ready", {"status": "ready"})
            return Response(
                content,
                mimetype="text/csv" if selected == "csv" else "application/zip",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except StreamRequestError as error:
            return JsonResponse.error(error)
