"""Unit tests for the manifest writer (T023, FR-028, SC-004)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.juniper_docs.harvest.manifest_writer import ManifestWriter
from src.juniper_docs.harvest.state_store import HarvestStateStore
from src.juniper_docs.models import DocumentType, InventoryRecord, PdfCandidate


def _seed(tmp_path: Path) -> HarvestStateStore:
    """Return a store seeded with a classified, a dropped, and a failed document."""
    store = HarvestStateStore(tmp_path / "s.db")  # Open a fresh store.
    _seed_classified(store)  # One classified document with candidates.
    store.add_document(InventoryRecord("https://x/rel/", "rel", DocumentType.HTML_ROOT))
    store.set_category("https://x/rel/", "release-notes")  # A release note.
    store.record_dropped("https://x/rel/", "superseded-by-newer-train-member")  # Dropped.
    store.add_document(InventoryRecord("https://x/bad/", "bad", DocumentType.HTML_ROOT))
    store.set_category("https://x/bad/", "design")  # A failed document.
    store.mark_failed("https://x/bad/", "no PDF found")  # Marked failed.
    return store  # The writer renders from this store.


def _seed_classified(store: HarvestStateStore) -> None:
    """Seed one classified document with a chosen and a rejected candidate."""
    root = "https://x/guide/"  # The classified document root.
    store.add_document(InventoryRecord(root, "guide", DocumentType.HTML_ROOT))  # Insert.
    store.set_category(root, "configuration-guides")  # The slug category.
    store.set_resolved(
        root,
        root + "guide.pdf",
        [
            PdfCandidate(root + "guide.pdf", True, "name-match"),  # The chosen companion PDF.
            PdfCandidate(root + "chapter-1.pdf", False, "rejected"),  # A rejected candidate.
        ],
    )
    store.mark_downloaded(root, "data/guide.pdf", 2048)  # The download record.
    store.set_classified(root, None, None)  # The final classified stage.


def test_manifest_covers_every_document(tmp_path: Path) -> None:
    """The manifest covers every inventory document with a final status."""
    store = _seed(tmp_path)  # Seed three documents.
    json_path, _csv_path = ManifestWriter(store, tmp_path).write()  # Render the manifest.
    store.close()  # Release the database file.
    data = json.loads(json_path.read_text(encoding="utf-8"))  # Read the JSON manifest.
    assert len(data) == 3  # Every document appears once (SC-004).
    assert {entry["status"] for entry in data} == {"classified", "dropped", "failed"}


def test_manifest_records_candidates_and_drops(tmp_path: Path) -> None:
    """The manifest records the chosen PDF, the rejects, and the drop reason."""
    store = _seed(tmp_path)  # Seed three documents.
    json_path, _csv_path = ManifestWriter(store, tmp_path).write()  # Render the manifest.
    store.close()  # Release the database file.
    by_url = {entry["source_url"]: entry for entry in json.loads(json_path.read_text("utf-8"))}
    guide = by_url["https://x/guide/"]  # The classified document.
    assert guide["chosen_pdf"] == "https://x/guide/guide.pdf"  # The chosen companion PDF.
    assert guide["rejected_candidates"] == ["https://x/guide/chapter-1.pdf"]  # The rejects.
    assert by_url["https://x/rel/"]["drop_reason"] == "superseded-by-newer-train-member"


def test_manifest_has_no_body_text_field(tmp_path: Path) -> None:
    """No manifest field carries the extracted body text."""
    store = _seed(tmp_path)  # Seed three documents.
    json_path, csv_path = ManifestWriter(store, tmp_path).write()  # Render the manifest.
    store.close()  # Release the database file.
    keys = set(json.loads(json_path.read_text("utf-8"))[0])  # The JSON field names.
    with csv_path.open(encoding="utf-8") as handle:  # Open the CSV manifest.
        header = next(csv.reader(handle))  # Read the header row.
    assert not any("body" in key or key == "text" for key in keys)  # No JSON body field.
    assert not any("body" in column or column == "text" for column in header)  # No CSV field.
