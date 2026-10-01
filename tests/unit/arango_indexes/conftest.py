"""Isolate declared-index writer tests from live database connections."""

from collections.abc import Iterator

import pytest

from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness


@pytest.fixture
def writer_harness() -> Iterator[ArangoIndexWriterHarness]:
    """Provide an owned fake scope and release its writer handles."""
    harness = ArangoIndexWriterHarness()
    try:
        yield harness
    finally:
        harness.close()
