"""Sentinel test proving lazy logging defers argument formatting.

Installs an argument whose `__str__` raises `AssertionError`, sets the
logger level above the call's level, and verifies no exception fires.
This is the canonical proof that `%`-style logging is genuinely lazy --
if the formatter ran eagerly, the sentinel would raise.
"""

from __future__ import annotations  # PEP 604 union syntax for Python 3.13.

import logging  # Test target is the stdlib logger.

import pytest  # Test framework used across the project.


class _ExplodingValue:
    """Sentinel object whose every string-conversion path raises."""

    def __str__(self) -> str:  # logging's `%s` calls __str__ when it formats.
        raise AssertionError("lazy formatting failed: __str__ was called")  # Loud failure.

    def __repr__(self) -> str:  # `%r` would call __repr__ -- guard that too.
        raise AssertionError("lazy formatting failed: __repr__ was called")  # Loud failure.

    def __format__(self, spec: str) -> str:  # `format()` and f-strings call __format__.
        raise AssertionError("lazy formatting failed: __format__ was called")  # Loud failure.


def test_lazy_logging_does_not_render_when_disabled(caplog: pytest.LogCaptureFixture) -> None:
    """A debug call with a `%s` arg must NOT invoke __str__ at WARNING level."""
    sentinel = _ExplodingValue()  # The thing that must never get formatted.
    logger = logging.getLogger("issue429.sentinel")  # Dedicated logger name avoids cross-test bleed.
    logger.setLevel(logging.WARNING)  # Set level ABOVE the call we are about to make.
    with caplog.at_level(logging.WARNING, logger="issue429.sentinel"):  # Capture only at WARNING+.
        logger.debug("value=%s", sentinel)  # If formatting ran, sentinel.__str__ would raise.
    assert not caplog.records, "expected no records emitted at DEBUG when level is WARNING"  # Confirm filter.


def test_eager_fstring_would_have_rendered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Negative control: an f-string DOES eagerly format, which is what we are fixing."""
    sentinel = _ExplodingValue()  # Same sentinel.
    with pytest.raises(AssertionError, match="__format__ was called"):  # Eager rendering MUST raise.
        _ = f"value={sentinel}"  # The f-string is evaluated immediately, calling __format__.
