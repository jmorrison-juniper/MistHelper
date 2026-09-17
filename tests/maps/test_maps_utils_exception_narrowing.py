"""Tests for narrowed CSV writer exception handlers in map utilities."""

from __future__ import annotations  # Use postponed annotations for modern typing.

import csv  # Use csv.Error as the expected writer failure type.

import pytest  # Use monkeypatch for isolated collaborator replacement.

from src.maps import _maps_utils as maps_utils  # Import the module under test.


def test_write_data_returns_false_on_csv_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A CSV writer failure logs and returns False."""

    def _raise_csv_error(_data: list[dict[str, object]], _filepath: str) -> None:  # Match the writer signature.
        raise csv.Error("bad csv")  # Simulate a CSV module write failure.

    monkeypatch.setattr(maps_utils, "_write_csv_rows", _raise_csv_error)  # Replace the file writer.
    result = maps_utils.write_data_with_format_selection([{"name": "map"}], "maps")  # Run the narrowed handler.
    assert result is False  # The visible soft-fail result stays unchanged.


def test_write_data_propagates_unexpected_writer_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-CSV writer fault reaches the caller."""

    def _raise_runtime_error(_data: list[dict[str, object]], _filepath: str) -> None:  # Match the writer signature.
        raise RuntimeError("writer broke")  # Prove the handler no longer hides all faults.

    monkeypatch.setattr(maps_utils, "_write_csv_rows", _raise_runtime_error)  # Replace the file writer.
    with pytest.raises(RuntimeError, match="writer broke"):  # The narrowed handler lets runtime faults surface.
        maps_utils.write_data_with_format_selection([{"name": "map"}], "maps")  # Run the write path.
