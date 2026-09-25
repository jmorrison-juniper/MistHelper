"""Build the one Cancellation text of a multi-site child job.

Why:
    Issue #3225. The progress page printed the cancel status word and the
    cloud message with no separator. The poll then printed a second format
    with other labels, so the cell text changed after the first poll. The
    server now builds one text, and the page and the poll print that text.
"""

from __future__ import annotations  # Keep modern annotations available at runtime.

import logging  # Record each build of a text.
from collections.abc import Mapping  # Name the read-only shape of a stored cancel result.

logger = logging.getLogger(__name__)  # Use the module logger without secret fields.


class OrgCancelText:
    """Join the parts of one stored cancel result into one text."""

    LISTS = (  # Each device list and its label, in the order of the cancel outcome panel.
        ("cancelled", "Cancelled"),
        ("already_writing", "Writing firmware"),
        ("no_cancel_available", "No cancel available"),
    )

    @classmethod
    def text(cls, cancellation: object) -> str:
        """Return the Cancellation text of one child job.

        Args:
            cancellation: The stored cancel result of the child job, or None.

        Returns:
            The text, or an empty text for a child job with no cancel result.
        """
        if not isinstance(cancellation, Mapping):  # No result, so the cell must not imply a cancel request.
            return ""  # The cell stays empty.
        parts = cls._lead(cancellation) + cls._lists(cancellation)  # The status, the message, and each list.
        logger.debug("Built a Cancellation text of %s part(s)", len(parts))  # After the build, with no device.
        return " ".join(parts)  # One space between two parts, so each part reads as its own sentence.

    @staticmethod
    def _lead(cancellation: Mapping[str, object]) -> list[str]:
        """Return the labeled status word and the exact cloud message, when each one exists."""
        status = str(cancellation.get("status") or "").strip()  # The cancel status word.
        message = str(cancellation.get("message") or "").strip()  # The exact words of the cancel answer.
        lead = [f"Status: {status}."] if status else []  # A label keeps the word apart from the message.
        return lead + ([message] if message else [])  # The message keeps the exact cloud words.

    @classmethod
    def _lists(cls, cancellation: Mapping[str, object]) -> list[str]:
        """Return one labeled sentence for each filled device list."""
        parts: list[str] = []  # The sentences in panel order.
        for key, label in cls.LISTS:  # Each list of the cancel result.
            devices = cancellation.get(key)  # The device addresses of this list.
            if isinstance(devices, list) and devices:  # A damaged or empty list adds no words.
                parts.append(f"{label}: {', '.join(str(device) for device in devices)}.")  # Name each device.
        return parts  # An empty list when no device list holds an entry.
