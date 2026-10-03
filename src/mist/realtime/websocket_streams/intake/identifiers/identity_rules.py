"""Checks for Mist UUID and MAC identifier text."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.
import re  # Fixed patterns enforce bounded identifier shapes.
from typing import ClassVar  # Compiled patterns are shared by all checks.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep identity logs bounded and content-free.


class IdentityIdentifierRules:
    """Check Mist UUID and MAC identifier text."""

    UUID: ClassVar[re.Pattern[str]] = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    MAC: ClassVar[re.Pattern[str]] = re.compile(r"^(?:[0-9a-fA-F]{12}|(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})$")

    @classmethod
    def is_uuid(cls, value: object) -> bool:
        """Return whether a value has the Mist UUID shape."""
        return cls._match("uuid", cls.UUID, value)  # Use the shared safe pattern check.

    @classmethod
    def is_mac(cls, value: object) -> bool:
        """Return whether a value has a supported MAC shape."""
        return cls._match("mac", cls.MAC, value)  # Accept compact or separated text.

    @staticmethod
    def normalize_mac(value: str) -> str:
        """Return compact lowercase MAC text."""
        return re.sub(r"[:-]", "", value).lower()  # The SDK accepts compact lowercase text.

    @staticmethod
    def _match(kind: str, pattern: re.Pattern[str], value: object) -> bool:
        """Return one pattern result without logging the input."""
        result = isinstance(value, str) and pattern.fullmatch(value) is not None  # Check only text values.
        logger.emit(
            logging.DEBUG, "intake_identifier_checked", {"detail": kind, "status": result}
        )  # Log safe metadata.
        return result  # The caller selects the refusal text.
