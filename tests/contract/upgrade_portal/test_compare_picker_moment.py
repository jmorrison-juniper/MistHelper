"""Contract tests for the moment that the comparison picker shows.

Why:
    Issue #2227 records the gap. The history page showed a readable moment in
    UTC, and the picker of the comparison page showed the stored text.

    The operator picks two captures on that page, and the moment is the one
    value that tells the two apart. A 32-character stamp with a microsecond and
    an offset is the hardest form to read, and it appeared exactly where the
    reader must compare.

    Warning: the stored text carries the offset of the machine that wrote it.
    Two captures of one afternoon can read as two different hours, so an
    operator can pick the wrong pair without noticing.
"""

from __future__ import annotations

import re

from src.upgrade_portal.app.routes import review

# The stored shape of a real record of the database. The offset is seven hours
# behind UTC, so the readable form must name a different hour.
STORED_MOMENT = "2026-09-02T08:49:45.214567-07:00"
READABLE_MOMENT = "2026-09-02 15:49 UTC"

# Any epoch second of the last few years reads as ten digits.
EPOCH_PATTERN = re.compile(r"\b1[78]\d{8}\b")


def test_the_picker_moment_reads_as_utc() -> None:
    """The stored offset must reach the picker as UTC, never as the local hour.

    Why:
        The stored text names 08:49 with an offset seven hours behind UTC. That
        moment is 15:49 UTC. A picker that showed the stored hour would place
        this capture before one that really came first.
    """
    assert review.short_moment(STORED_MOMENT) == READABLE_MOMENT


def test_the_picker_moment_holds_no_microsecond() -> None:
    """The stored text holds 32 characters, and the picker must not."""
    assert "." not in review.short_moment(STORED_MOMENT)


def test_the_picker_moment_holds_no_epoch_second() -> None:
    """No page of the portal shows a raw stamp of the store to an operator."""
    assert not EPOCH_PATTERN.search(review.short_moment(STORED_MOMENT))


def test_a_missing_moment_reads_as_empty_text() -> None:
    """A partial record must not raise inside the picker."""
    assert review.short_moment(None) == ""
