"""Tests for alert digest output writers."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from dataclasses import dataclass, field  # Build a compact fake exporter.
from pathlib import Path  # Validate files through pytest temporary directories.
from typing import Any  # Accept writer row values.

from src.reports.alert_digest.model import AlertDigestModel  # Build realistic digest groups.
from src.reports.alert_digest.writer import AlertDigestWriter  # Test output writing.

from .conftest import alarm, definition  # Reuse synthetic Mist rows.


@dataclass
class FakeExporter:
    """Fake DataExporter that records requested CSV writes."""

    writes: list[dict[str, Any]] = field(default_factory=list)  # Keep each write for assertions.

    def write_with_format_selection(
        self,
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Record one CSV write request."""
        self.writes.append(  # Preserve the export request without touching shared data files.
            {
                "data": data,
                "filename": filename_or_table,
                "api_function_name": api_function_name,
                "fieldnames": fieldnames,
            }
        )
        return True  # Simulate a successful DataExporter write.


def test_write_digest_creates_csv_request_and_ascii_markdown(tmp_path: Path) -> None:
    """Digest writing creates the required CSV target and ASCII Markdown."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build category lookup.
    records = AlertDigestModel.records_from_rows([alarm(1)], definitions)  # Build one realistic alarm row.
    groups = AlertDigestModel.group_records(records)  # Group data as menu 280 does.
    exporter = FakeExporter()  # Capture the CSV write request.
    writer = AlertDigestWriter(exporter=exporter, data_dir=tmp_path)  # Direct Markdown into a safe temp path.
    assert writer.write_digest(groups) is True  # Write both digest outputs.
    assert exporter.writes[0]["filename"] == "AlertDigest.csv"  # Confirm required CSV file name.
    markdown = (tmp_path / "AlertDigest.md").read_text(encoding="utf-8")  # Read the handover summary.
    assert "## infrastructure" in markdown  # Confirm the category section exists.
    assert all(ord(character) < 128 for character in markdown)  # Confirm ASCII-only operator output.
