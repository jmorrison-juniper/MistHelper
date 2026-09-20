"""Render the manifest from the SQLite store to JSON and CSV.

The manifest is an operational artifact that describes local files and run
state. It maps each document to its source URL, category, sub-category, size,
and status, and it records the chosen companion PDF, each rejected candidate,
and each dropped release note. The manifest holds no body-text field, so the
privacy invariant holds at the output layer (FR-028, SC-004, SC-005).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import csv  # Render the spreadsheet form of the manifest.
import json  # Render the machine form of the manifest.
import logging  # Trace the manifest render for observability.
import sqlite3  # Type the document rows read from the store.
from pathlib import Path  # Build the manifest paths in a portable way.

from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED  # Default category name.
from src.juniper_docs.harvest.state_store import HarvestStateStore  # The manifest source.
from src.juniper_docs.models import HarvestStage, ManifestEntry  # Shared record types.

_LOGGER = logging.getLogger(__name__)  # Module logger for the manifest render.

# The CSV columns match the JSON fields, one row per document.
_CSV_FIELDS = (
    "source_url",
    "resolved_pdf_url",
    "category",
    "sub_category",
    "local_path",
    "file_size",
    "status",
    "chosen_pdf",
    "rejected_candidates",
    "drop_reason",
    "error_reason",
)


class ManifestWriter:
    """Render the manifest JSON and CSV from the durable state store."""

    def __init__(self, store: HarvestStateStore, output_dir: Path) -> None:
        """Store the source state store and the output directory."""
        self.store = store  # The single source of truth for the manifest.
        self.output_dir = output_dir  # The directory that receives the manifest files.

    def write(self) -> tuple[Path, Path]:
        """Render both manifest files and return the JSON and CSV paths."""
        _LOGGER.info("Rendering the manifest to %s", self.output_dir)  # Log the intent.
        entries = [self._entry(row) for row in self.store.document_rows()]  # One per document.
        json_path = self._write_json(entries)  # Render the machine form.
        csv_path = self._write_csv(entries)  # Render the spreadsheet form.
        _LOGGER.debug("Manifest rendered for %d documents", len(entries))  # Result count.
        return json_path, csv_path  # The runner reports both manifest paths.

    def _entry(self, row: sqlite3.Row) -> ManifestEntry:
        """Return the joined manifest entry for one document row."""
        root = str(row["root_url"])  # The document root URL is the natural key.
        chosen, rejected = self._candidates(root)  # The chosen and rejected PDF URLs.
        return ManifestEntry(
            source_url=root,  # The document root URL.
            resolved_pdf_url=_text(row["resolved_pdf_url"]),  # The resolved PDF URL or null.
            category=_text(row["category"]) or UNCATEGORIZED,  # The slug category.
            sub_category=_text(row["sub_category"]),  # The content label when uncategorized.
            local_path=_text(row["local_path"]),  # The saved file path or null.
            file_size=_int(row["file_size"]),  # The byte count or null.
            status=HarvestStage(str(row["stage"])),  # The final stage of the document.
            chosen_pdf=chosen,  # The selected companion PDF URL.
            rejected_candidates=rejected,  # Each rejected PDF reference.
            drop_reason=self.store.dropped_reason(root),  # The drop reason or null.
            error_reason=_text(row["error_reason"]),  # The failure or no-PDF reason or null.
        )

    def _candidates(self, root_url: str) -> tuple[str | None, list[str]]:
        """Return the chosen PDF URL and every rejected candidate for one document."""
        rows = self.store.candidates_for(root_url)  # Read the recorded candidates.
        chosen = next((str(row["url"]) for row in rows if row["chosen"]), None)  # The winner.
        rejected = [str(row["url"]) for row in rows if not row["chosen"]]  # The rejects.
        return chosen, rejected  # The manifest records both for the audit trail.

    def _write_json(self, entries: list[ManifestEntry]) -> Path:
        """Write the JSON manifest and return its path."""
        path = self.output_dir / "manifest.json"  # The machine-format manifest path.
        data = [_to_dict(entry) for entry in entries]  # Convert each entry to a plain dict.
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")  # Persist the JSON.
        return path  # The runner reports this path.

    def _write_csv(self, entries: list[ManifestEntry]) -> Path:
        """Write the CSV manifest and return its path."""
        path = self.output_dir / "manifest.csv"  # The spreadsheet-format manifest path.
        with path.open("w", encoding="utf-8", newline="") as handle:  # Open with newline off.
            writer = csv.DictWriter(handle, fieldnames=list(_CSV_FIELDS))  # Fixed columns.
            writer.writeheader()  # Write the header row first.
            writer.writerows(_to_csv_row(entry) for entry in entries)  # One row per document.
        return path  # The runner reports this path.


def _to_dict(entry: ManifestEntry) -> dict[str, object]:
    """Return the JSON-ready dictionary for one manifest entry."""
    return {
        "source_url": entry.source_url,  # The document root URL.
        "resolved_pdf_url": entry.resolved_pdf_url,  # The resolved PDF URL or null.
        "category": entry.category,  # The slug category.
        "sub_category": entry.sub_category,  # The content label when uncategorized.
        "local_path": entry.local_path,  # The saved file path or null.
        "file_size": entry.file_size,  # The byte count or null.
        "status": entry.status.value,  # The final stage as a plain string.
        "chosen_pdf": entry.chosen_pdf,  # The selected companion PDF URL.
        "rejected_candidates": entry.rejected_candidates,  # Each rejected PDF reference.
        "drop_reason": entry.drop_reason,  # The drop reason or null.
        "error_reason": entry.error_reason,  # The failure or no-PDF reason or null.
    }


def _to_csv_row(entry: ManifestEntry) -> dict[str, object]:
    """Return the CSV row for one manifest entry with a flattened candidate list."""
    row = _to_dict(entry)  # Start from the JSON-ready dictionary.
    row["rejected_candidates"] = ";".join(entry.rejected_candidates)  # Flatten to one cell.
    return row  # The writer maps this to the fixed columns.


def _text(value: object) -> str | None:
    """Return a string for a non-null value, or None."""
    return None if value is None else str(value)  # Normalize a nullable text column.


def _int(value: int | None) -> int | None:
    """Return an integer for a non-null value, or None."""
    return None if value is None else int(value)  # Normalize a nullable integer column.
