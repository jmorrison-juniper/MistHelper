"""The structured error for one refused WebSocket request."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Mapping  # Extra payload fields arrive as a read-only mapping.
from typing import ClassVar  # The status table is shared by all request errors.


class StreamRequestError(Exception):
    """Hold one request refusal and its HTTP response data."""

    STATUS_BY_CODE: ClassVar[dict[str, int]] = {
        "not_ready": 503,
        "bad_request": 400,
        "unknown_key": 404,
        "locked": 403,
        "confirmation": 403,
        "limit_reached": 429,
        "not_found": 404,
        "not_open": 409,
        "session_live": 409,
        "not_terminal": 409,
        "read_only": 409,
        "input_full": 409,
        "too_large": 413,
        "rate_limited": 429,
    }  # Keep every contract code in one explicit table.

    def __init__(self, code: str, message: str, extra: Mapping[str, object] | None = None) -> None:
        """Build one immutable refusal payload."""
        super().__init__(message)  # Keep the plain operator message as the exception text.
        self.code = code  # The client uses the stable code for behavior.
        self.message = message  # The response shows the plain refusal reason.
        self.status = self.STATUS_BY_CODE.get(code, 400)  # Unknown codes remain bad requests.
        self.extra = dict(extra or {})  # Copy extra fields to prevent later caller mutation.

    def to_payload(self) -> dict[str, object]:
        """Return the JSON response payload."""
        payload: dict[str, object] = {"error": self.message, "code": self.code}  # Start with common fields.
        payload.update(self.extra)  # Add bounded contract context such as the field name.
        return payload  # Return a new response mapping.
