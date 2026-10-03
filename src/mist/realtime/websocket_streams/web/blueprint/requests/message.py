"""Validate message polling query values."""

from __future__ import annotations  # Keep annotations lazy.

from flask import request  # Read query text from the active request.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Return the shared error contract.


class MessageQuery:
    """Read checked message sequence and limit values."""

    @staticmethod
    def values() -> tuple[int, int]:
        """Return the checked after and limit values."""
        after_text = request.args.get("after", "0")  # Start at the first retained message by default.
        limit_text = request.args.get("limit", "200")  # Use the established default page limit.
        if not after_text.isdecimal():  # Accept only nonnegative whole numbers.
            raise StreamRequestError(
                "bad_request", "The after value must be a whole number.", {"field": "after"}
            )  # Return the established query error.
        if not limit_text.isdecimal():  # Accept only nonnegative whole numbers.
            raise StreamRequestError(
                "bad_request", "The limit value must be a whole number.", {"field": "limit"}
            )  # Return the established query error.
        return int(after_text), int(limit_text)  # Let the manager clamp the limit.
