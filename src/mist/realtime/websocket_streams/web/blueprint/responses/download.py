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

    BATCH_OUTPUTS = {
        "zip": ("zip_download", "application/zip"),
        "csv": ("csv_download", "text/csv"),
        "xml": ("xml_download", "application/xml"),
    }  # The reader and the media type of each batch output. The keys are the legal values of the format field.

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
        """Return one completed Multi Site result archive, or a combined report of a hardware run."""
        selected = request.args.get("format", "")  # Only three named outputs exist. A missing field is empty.
        if set(request.args) != {"format"} or selected not in DownloadResponse.BATCH_OUTPUTS:  # Known value.
            return JsonResponse.error(  # Refuse any other query.
                StreamRequestError("bad_request", "The batch download requires format=zip, format=csv, or format=xml.")
            )
        reader_name, media_type = DownloadResponse.BATCH_OUTPUTS[selected]  # The reader and the media type.
        try:
            services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
            filename, content = getattr(services.artifacts, reader_name)(session_id)  # A bounded pinned snapshot.
            logger.emit(logging.DEBUG, "web.response.batch_download.ready", {"status": "ready"})  # Log no filename.
            return Response(  # Send the file as an attachment with a server-made name.
                content,
                mimetype=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except StreamRequestError as error:  # The run is not ready, or the session is not a batch.
            return JsonResponse.error(error)  # Keep the standard error shape.
