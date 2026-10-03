"""Validate numeric input before a caller selects its fallback or refusal."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AsciiWholeNumberReader:
    """Read bounded ASCII decimal text without exposing the input in logs."""

    maximum: int
    field: str

    def read(self, text: str) -> int | None:
        """Return a usable whole number, or report why the field is invalid."""
        logger.info("Read the numeric field %s.", self.field)
        length = len(text)
        if not text:
            logger.debug("Numeric input checked=1 field=%s reason=empty characters=0.", self.field)
            return None
        if length > self._representation_limit():
            self._report_refusal("too_long", length)
            return None
        if not text.isascii() or not text.isdecimal():
            self._report_refusal("invalid_digits", length)
            return None
        significant = text.lstrip("0") or "0"  # Check raw length first so excessive zeros never become valid.
        highest = str(self.maximum)
        if (len(significant), significant) > (len(highest), highest):  # Compare decimal lengths before values.
            self._report_refusal("out_of_range", length)
            return None
        value = int(significant)
        logger.debug("Numeric input checked=1 field=%s reason=accepted characters=%s.", self.field, length)
        return value

    @staticmethod
    def _representation_limit() -> int:
        """Keep the backend's default bound or its stricter active bound."""
        default = sys.int_info.default_max_str_digits
        active = sys.get_int_max_str_digits()
        return min(active or default, default)

    def _report_refusal(self, reason: str, length: int) -> None:
        """Report one invalid field without its raw value."""
        logger.warning("Numeric input checked=1 field=%s reason=%s characters=%s.", self.field, reason, length)
