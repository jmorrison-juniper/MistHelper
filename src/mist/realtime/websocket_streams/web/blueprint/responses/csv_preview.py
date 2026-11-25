"""Return one page of the combined CSV report of a hardware run as JSON."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read the query and type the response.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Convert contract refusals.
from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Reuse the shared answer and error shape.


class PreviewQuery:
    """Validate the page position and the filter text of a report preview."""

    FIELDS = frozenset({"offset", "limit", "q"})  # The only query fields that the route accepts.
    PAGE_MAX = 1000  # The most rows in one page. A request with no size asks for this many.
    TEXT_MAX = 100  # The most characters in a filter text.

    @classmethod
    def values(cls) -> tuple[int, int, str] | StreamRequestError:
        """Return the checked offset, page size, and filter text, or the refusal."""
        if set(request.args) - cls.FIELDS:  # Refuse a field outside the endpoint contract.
            return StreamRequestError("bad_request", "The report preview has an unknown query field.")
        text = request.args.get("q", "")  # A plain text that a cell must hold.
        if len(text) > cls.TEXT_MAX:  # Bound the work of one filter.
            return StreamRequestError("bad_request", "The filter text has more than 100 characters.")
        try:  # Parse only whole numbers for the position and the size.
            offset = int(request.args.get("offset", "0"))  # The first page starts at row 0.
            limit = int(request.args.get("limit", str(cls.PAGE_MAX)))  # Ask for a full page unless told otherwise.
        except ValueError:  # Refuse malformed text before any service call.
            return StreamRequestError("bad_request", "The page position or size is not a whole number.")
        if offset < 0 or limit < 1:  # Require a nonnegative position and a positive size.
            return StreamRequestError("bad_request", "The page position or size is not valid.")
        return offset, min(limit, cls.PAGE_MAX), text  # Apply the documented maximum page size.


class CsvPreviewResponse:
    """Build the JSON answer for one report preview."""

    @staticmethod
    def preview(session_id: str) -> Response | tuple[Response, int]:
        """Return one page of the combined CSV report of a completed hardware run."""
        values = PreviewQuery.values()  # Refuse a bad query before any file access.
        if isinstance(values, StreamRequestError):  # A refusal carries its own status.
            return JsonResponse.error(values)  # Keep the shared error shape.
        offset, limit, text = values  # Keep the checked values together.
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(lambda: services.artifacts.csv_preview(session_id, offset, limit, text))
