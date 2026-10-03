"""Checks for UUID, MAC, port, name, and filter text."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.
import re  # Fixed patterns enforce bounded safe identifier shapes.
from typing import ClassVar  # Compiled patterns are shared by all checks.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep identifier logs bounded and content-free.


class TextIdentifierRules:
    """Check non-network identifier text."""

    PORT: ClassVar[re.Pattern[str]] = re.compile(r"^[a-z]{2,4}-\d+/\d+/\d+(?:\.\d+)?$")
    NAME: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_.:@ -]{1,128}$")
    FILTER: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9 .:/_()\[\]=!<>&|+-]{0,256}$")

    @classmethod
    def is_port(cls, value: object) -> bool:
        """Return whether a value has a Junos port shape."""
        return cls._match("port", cls.PORT, value)  # Use the bounded Junos pattern.

    @classmethod
    def is_name(cls, value: object) -> bool:
        """Return whether a value is safe plain name text."""
        return cls._match("name", cls.NAME, value)  # Use the bounded printable pattern.

    @classmethod
    def is_filter(cls, value: object) -> bool:
        """Return whether a value uses safe capture filter characters."""
        return cls._match("filter", cls.FILTER, value)  # Use the bounded filter pattern.

    @staticmethod
    def _match(kind: str, pattern: re.Pattern[str], value: object) -> bool:
        """Return one pattern result without logging the input."""
        result = isinstance(value, str) and pattern.fullmatch(value) is not None  # Check only text values.
        logger.emit(
            logging.DEBUG, "intake_identifier_checked", {"detail": kind, "status": result}
        )  # Log safe metadata.
        return result  # The caller selects the refusal text.
