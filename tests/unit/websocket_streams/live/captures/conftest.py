"""Owned local capture fixtures with required cleanup."""

from collections.abc import Iterator

import pytest

from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness


@pytest.fixture
def capture_harness() -> Iterator[CaptureHarness]:
    """Provide real services backed by controlled SDK transport."""
    harness = CaptureHarness()
    try:
        yield harness
    finally:
        harness.close()
