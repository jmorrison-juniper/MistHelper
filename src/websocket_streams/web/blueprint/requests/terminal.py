"""Validate terminal query and JSON request values."""

from __future__ import annotations  # Keep annotations lazy.

import math  # Reject nonfinite waits.

from flask import request  # Read terminal query text.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Return the shared error contract.


class TerminalRequest:
    """Convert terminal request values to checked Python values."""

    MAX_WAIT_SECONDS = 25.0  # Keep one long poll below the contract limit.

    @classmethod
    def read_query(cls) -> tuple[int, float]:
        """Return the checked byte position and wait."""
        after_text = request.args.get("after", "0")  # Start at the oldest retained byte by default.
        wait_text = request.args.get("wait", "0")  # Answer at once by default.
        if not after_text.isdecimal():  # Accept only a nonnegative byte position.
            raise StreamRequestError(
                "bad_request", "The after value must be a whole number.", {"field": "after"}
            )  # Return the established query error.
        return int(after_text), cls._wait_seconds(wait_text)  # Return both checked values.

    @staticmethod
    def input_text(body: object) -> str:
        """Return the exact terminal input text."""
        data = body.get("data") if isinstance(body, dict) else None  # Read data only from a JSON object.
        if not isinstance(data, str) or data == "":  # Refuse old line and key body shapes.
            raise StreamRequestError(
                "bad_request", "The input must hold text in the data field.", {"field": "data"}
            )  # Return the established input error.
        return data  # Preserve every input character.

    @staticmethod
    def size(body: object) -> tuple[int, int]:
        """Return checked terminal columns and rows."""
        values = body if isinstance(body, dict) else {}  # Read sizes only from a JSON object.
        for field in ("cols", "rows"):  # Apply one integer rule to both dimensions.
            value = values.get(field)  # Read one untrusted dimension.
            if isinstance(value, bool) or not isinstance(value, int):  # JSON true is not a size.
                raise StreamRequestError(
                    "bad_request", "The terminal size must be whole numbers.", {"field": field}
                )  # Return the established size error.
        return int(values["cols"]), int(values["rows"])  # Let the terminal state enforce ranges.

    @classmethod
    def _wait_seconds(cls, text: str) -> float:
        """Return a finite wait from zero through 25 seconds."""
        try:  # Query values arrive as text.
            wait = float(text)  # Accept whole and decimal seconds.
        except ValueError as error:  # Non-numeric text is a request error.
            raise cls._wait_error() from error  # Preserve one public error shape.
        if not math.isfinite(wait) or not 0.0 <= wait <= cls.MAX_WAIT_SECONDS:  # Enforce the bounded wait.
            raise cls._wait_error()  # Refuse negative, infinite, and excessive waits.
        return wait  # The gateway can use the checked wait.

    @staticmethod
    def _wait_error() -> StreamRequestError:
        """Return the standard wait request error."""
        return StreamRequestError(
            "bad_request", "The wait value must be a number from 0 to 25.", {"field": "wait"}
        )  # Keep the public error stable.
