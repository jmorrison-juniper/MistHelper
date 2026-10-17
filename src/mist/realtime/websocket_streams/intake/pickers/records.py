"""Safe row and payload construction for picker results."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Page reads use the shared structured event format.
from typing import NoReturn  # A status refusal always exits before record parsing.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Keep incomplete discovery separate from an empty result.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Keep page logs bounded and free of response content.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep page events under the picker module.


class PickerPageReader:
    """Read and validate every page from one authenticated Mist SDK response."""

    def __init__(self, apisession: object) -> None:
        """Store the authenticated SDK session for cursor requests."""
        self._apisession = apisession  # Later pages must use the same authenticated session.

    def read(self, response: object) -> list[dict[str, object]]:
        """Return every validated row or fail without exposing partial results."""
        logger.emit(logging.INFO, "intake_picker_pages_started")  # Record the complete discovery action.
        rows: list[dict[str, object]] = []  # Keep page rows private until all pages pass validation.
        seen_cursors: set[str] = set()  # Refuse a repeated cursor instead of looping.
        page: object | None = response  # Start with the already authenticated first response.
        while page is not None:  # Continue only while the SDK supplies a later page.
            rows.extend(self._page_rows(page))  # Validate the status and shape before retaining rows.
            cursor = self._cursor(page)  # Read only the SDK-provided next-page cursor.
            if cursor is None:  # A missing cursor proves that the page sequence is complete.
                break  # Return the full validated result.
            if cursor in seen_cursors:  # A repeated cursor cannot make progress.
                raise StreamRequestError("picker_incomplete", "Mist returned a repeated page cursor.")  # Refuse.
            seen_cursors.add(cursor)  # Track the cursor before the next authenticated request.
            page = self._next(page)  # Fetch the next page through the Mist SDK.
        logger.emit(logging.DEBUG, "intake_picker_pages_finished", {"count": len(rows)})  # Report row count only.
        return rows  # Expose rows only after every page passes validation.

    def _page_rows(self, response: object) -> list[dict[str, object]]:
        """Validate one response status and return its mapping rows."""
        status = getattr(response, "status_code", None)  # Read the SDK status without the upstream body.
        if status != 200:  # List endpoints must return a successful HTTP status.
            self._raise_status(status)  # Report refusal or service failure with a safe status only.
        data = getattr(response, "data", None)  # Read the SDK-decoded response body.
        rows = self._row_list(data)  # Accept only documented list or result-envelope shapes.
        if rows is None or any(not isinstance(row, dict) for row in rows):  # Reject malformed page records.
            raise StreamRequestError("picker_unavailable", "Mist returned an unsupported picker response.")
        return [dict(row) for row in rows]  # Copy mappings before the caller can retain or change them.

    def _row_list(self, data: object) -> list[object] | None:
        """Return the documented record list from a decoded response."""
        if isinstance(data, list):  # Most Mist list endpoints return a list directly.
            return data  # Keep the complete list for page validation.
        if not isinstance(data, dict):  # Only documented SDK envelopes can hold list records.
            return None  # Let the caller report the unsupported shape.
        for key in ("results", "items", "sdkclients"):  # Accept known Mist result envelope names.
            value = data.get(key)  # Read one documented record field.
            if isinstance(value, list):  # A list proves the response shape.
                return value  # Preserve empty lists as complete page results.
        return None  # Do not interpret an unknown object as an empty list.

    def _cursor(self, response: object) -> str | None:
        """Return a valid next cursor or reject an unsupported cursor shape."""
        cursor = getattr(response, "next", None)  # APIResponse exposes the server-provided cursor.
        if cursor is None:  # No cursor marks the final page.
            return None  # The caller can finish the read.
        if not isinstance(cursor, str) or not cursor.strip():  # A cursor must be usable by the SDK.
            raise StreamRequestError("picker_incomplete", "Mist returned an invalid page cursor.")
        return cursor  # Keep the cursor private to the SDK request.

    def _next(self, response: object) -> object:
        """Fetch one cursor through the authenticated Mist SDK."""
        try:  # Keep SDK transport failures inside the picker error contract.
            import mistapi  # Load the installed SDK only when a later page exists.

            logger.emit(logging.INFO, "intake_picker_next_page_started")  # Log before the external request.
            page = mistapi.get_next(mist_session=self._apisession, response=response)  # Follow SDK pagination.
        except Exception as error:  # SDK request failures cannot become empty picker results.
            logger.emit(
                logging.ERROR, "intake_picker_next_page_failed", {"detail": type(error).__name__}
            )  # Log a safe exception type only.
            raise StreamRequestError(
                "picker_service_failed", "Mist could not complete the picker request."
            ) from error  # Keep upstream content and credentials private.
        if page is None:  # A cursor that produces no response is an incomplete list.
            raise StreamRequestError("picker_incomplete", "Mist did not return the requested page.")
        logger.emit(logging.DEBUG, "intake_picker_next_page_finished", {"status": "received"})
        return page  # The caller validates this page before accepting its rows.

    @staticmethod
    def _raise_status(status: object) -> NoReturn:
        """Raise a safe picker error for one unsuccessful page."""
        details = {"upstream_status": status} if isinstance(status, int) else {}  # Expose only an HTTP code.
        if isinstance(status, int) and 400 <= status < 500:  # Mist rejected the request or current access.
            raise StreamRequestError(
                "picker_request_failed", "Mist refused the picker request.", details
            )  # Keep access failure distinct from an empty result.
        raise StreamRequestError(
            "picker_service_failed", "Mist could not complete the picker request.", details
        )  # Treat missing and server statuses as service failures.


class PickerRuntime:
    """Hold shared picker state and normalize response records."""

    _apisession: object  # Every picker behavior uses the authenticated SDK session.
    _org_id: str  # Organization-scope reads use the trusted portal identifier.
    _device_cache: dict[str, tuple[float, list[dict[str, object]]]]  # Device reads use the short cache.
    _page_reader: PickerPageReader  # Every picker shares one authenticated pagination reader.

    def _payload(self, rows: list[dict[str, object]], empty_reason: str) -> dict[str, object]:
        """Return the stable picker response shape."""
        rows.sort(key=lambda row: str(row.get("label") or "").casefold())  # Keep operator lists stable.
        reason = None if rows else empty_reason  # Explain only an empty result.
        return {"rows": rows, "total_count": len(rows), "reason": reason}  # Return the contract fields.

    def _row(
        self,
        record: dict[str, object],
        label_fields: tuple[str, ...],
        detail_fields: tuple[str, ...],
        family: str | None,
    ) -> dict[str, object]:
        """Return one normalized picker row."""
        identifier = str(record.get("id") or record.get("mac") or "")  # Select a stable picker value.
        label = self._first_text(record, label_fields) or identifier  # Prefer an operator-readable label.
        detail = self._first_text(record, detail_fields)  # Add bounded identification detail.
        return {"id": identifier, "label": label, "family": family, "detail": detail}  # Keep the page contract.

    @staticmethod
    def _first_text(record: dict[str, object], fields: tuple[str, ...]) -> str:
        """Return the first non-empty field text."""
        for field in fields:  # Search preferred display fields in order.
            value = str(record.get(field) or "").strip()  # Normalize missing values.
            if value:  # The first useful value wins.
                return value  # Return operator-readable text.
        return ""  # No configured field held text.

    @staticmethod
    def _device_family(record: dict[str, object]) -> str | None:
        """Return the utility family for one device."""
        device_type = str(record.get("type") or "").casefold()  # Mist sends AP, switch, or gateway.
        model = str(record.get("model") or "").casefold()  # Gateway model text separates SRX and SSR.
        families = {"ap": "ap", "switch": "ex"}  # Direct device types have fixed utility families.
        if device_type in families:  # Access points and switches need no model check.
            return families[device_type]  # Return the fixed catalog family.
        if device_type == "gateway":  # Gateways use one of two utility families.
            return "srx" if "srx" in model else "ssr"  # Select the family from model text.
        return None  # Unknown types have no utility list.
