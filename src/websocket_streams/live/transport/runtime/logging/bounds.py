"""Bounds for transport structured log records."""

from typing import Final  # Constants remain explicit to the type checker.

MAX_EVENT_LENGTH: Final = 48  # Event names stay short for bounded records.
MAX_FIELD_LENGTH: Final = 96  # Safe text fields cannot grow with remote input.
MAX_FIELDS: Final = 8  # One record cannot collect an unbounded field set.
REDACTED_VALUE: Final = "[REDACTED]"  # One marker replaces all sensitive values.
