"""Privacy-invariant proof for the harvester (T036, FR-024, SC-005).

These tests prove the extracted body text never reaches a durable artifact.
The content record has no text field, the content_scores table has no text
column, the manifest has no body-text field, and a real classify run leaves the
sampled body text in no file under the output tree and in no store row.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

from src.juniper_docs.classify.content_sampler import ContentSampler
from src.juniper_docs.classify.signal_scorer import SignalScorer
from src.juniper_docs.harvest.manifest_writer import ManifestWriter
from src.juniper_docs.harvest.state_store import HarvestStateStore
from src.juniper_docs.models import ContentAnalysisResult, DocumentType, InventoryRecord
from tests.unit.juniper_docs.conftest import FIXTURES

_MARKER = "UNIQUE-BODY-MARKER-DO-NOT-PERSIST-7F3A"  # A token from the fixture body text.


def test_content_result_has_no_text_field() -> None:
    """The content analysis record carries no field for the body text."""
    names = {field.name for field in dataclasses.fields(ContentAnalysisResult)}  # The fields.
    assert names == {"sub_category", "detected_signals", "scores", "is_fallback"}  # No text.


def test_content_scores_table_has_no_text_column(tmp_path: Path) -> None:
    """The content_scores schema holds only the signal names and the scores."""
    store = HarvestStateStore(tmp_path / "s.db")  # Open a fresh store.
    columns = [row[1] for row in store._conn.execute("PRAGMA table_info(content_scores)")]
    store.close()  # Release the database file.
    assert not any("text" in name.lower() for name in columns)  # No text column exists.


def test_manifest_has_no_body_text_field() -> None:
    """The manifest field set carries no body-text field."""
    from src.juniper_docs.harvest.manifest_writer import _CSV_FIELDS  # The manifest columns.

    assert not any("body" in name or name == "text" for name in _CSV_FIELDS)  # No text field.


def test_sampled_body_text_is_never_persisted(tmp_path: Path) -> None:
    """A real classify run leaves the body text in no file and no store row."""
    text = ContentSampler().sample(FIXTURES / "sample_uncategorized.pdf")  # Sample the PDF.
    assert _MARKER in text  # Sanity: the marker is in the sampled body text.
    _run_classify(tmp_path, SignalScorer().score(text))  # Persist the label and scores.
    _assert_marker_absent_in_files(tmp_path)  # No file under the tree holds the marker.
    _assert_marker_absent_in_store(tmp_path / "s.db")  # No store row holds the marker.


def _run_classify(tmp_path: Path, result: ContentAnalysisResult) -> None:
    """Persist the label, the scores, and the manifest for one document."""
    store = HarvestStateStore(tmp_path / "s.db")  # Open the store.
    root = "https://x/uncategorized-doc/"  # The document root URL.
    store.add_document(InventoryRecord(root, "software/uncategorized-doc", DocumentType.HTML_ROOT))
    store.set_category(root, "uncategorized")  # The slug category.
    store.mark_downloaded(root, str(tmp_path / "file.pdf"), 100)  # The download record.
    rows = [(key.split(":")[0], key.split(":")[1], score) for key, score in result.scores.items()]
    store.record_scores(root, rows)  # Persist only the numeric scores.
    store.set_classified(root, result.sub_category, result.is_fallback)  # Persist the label.
    ManifestWriter(store, tmp_path).write()  # Render the manifest files.
    store.close()  # Release the database file.


def _assert_marker_absent_in_files(tmp_path: Path) -> None:
    """Assert the body-text marker appears in no file under the output tree."""
    for path in tmp_path.rglob("*"):  # Walk every file under the output tree.
        if path.is_file():  # Read only regular files.
            assert _MARKER.encode() not in path.read_bytes()  # The marker never leaks.


def _assert_marker_absent_in_store(db_path: Path) -> None:
    """Assert the body-text marker appears in no row of the store."""
    connection = sqlite3.connect(str(db_path))  # Reopen the store for the audit.
    tables = ["documents", "pdf_candidates", "content_scores", "dropped_release_notes", "run_meta"]
    dump = "".join(str(connection.execute(f"SELECT * FROM {table}").fetchall()) for table in tables)
    connection.close()  # Release the database file.
    assert _MARKER not in dump  # No store row holds the body text.
