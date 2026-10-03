"""Frozen dataclass that reports the true result of one polyglot database write.

``DataExporter._route_to_polyglot`` returned ``None``. A caller could not tell a
stored row from a dropped row, because both looked the same from the outside.
This outcome carries the verdict, the cause of a drop, and the row counts, so a
caller can trust the answer without a read-back.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/2009
"""

from __future__ import annotations  # Enable PEP 604 union syntax on older runtimes.

from dataclasses import dataclass  # The standard library dataclass decorator.


@dataclass(frozen=True, slots=True)
class PolyglotWriteOutcome:
    """The truthful result of one attempted polyglot database write."""

    written: bool  # True only when at least one row reached ArangoDB or Redis.
    skip_reason: str | None = None  # The cause identifier when written is False, else None.
    records_written: int = 0  # The count of rows that the router stored.
    records_failed: int = 0  # The count of rows that the router could not store.
    backend: str | None = None  # The backend name that the router reported.
