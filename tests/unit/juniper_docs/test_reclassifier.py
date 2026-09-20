"""Unit tests for the corpus reclassifier (issue #2738 follow-up).

These tests build a small fixture corpus under the pytest temporary folder. They
copy committed PDF fixtures from the ``fixtures/`` directory and create a state
database with the real schema through ``HarvestStateStore``. The pytest
``tmp_path`` fixture removes the whole fixture tree when each test ends, so no
fixture survives the run.

The fixtures live in the repository, so the tests never read the harvested
corpus. The harvested corpus is a gitignored artifact, and a test that read it
would fail on a fresh checkout.

The tests prove the six required behaviors: a changed label moves the file and
updates the row, an unchanged label is left alone, a dry run writes nothing, a
name collision disambiguates instead of overwriting, an unreadable file is
counted without stopping the pass, and no body text reaches any durable file.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.juniper_docs.classify.content_sampler import ContentSampler
from src.juniper_docs.classify.reclassifier import CorpusReclassifier
from src.juniper_docs.classify.signal_scorer import SignalScorer
from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED
from src.juniper_docs.harvest.state_store import HarvestStateStore
from src.juniper_docs.models import (
    ContentAnalysisResult,
    DocumentType,
    InventoryRecord,
    PdfCandidate,
)
from tests.unit.juniper_docs.conftest import FIXTURES

_OPTICS = FIXTURES / "sample_routing.pdf"  # A committed PDF that scores "qfx__routing".
_EVPN = FIXTURES / "sample_evpn_fabric.pdf"  # A committed PDF that scores "evpn-vxlan".
_MARKER = "UNIQUE-BODY-MARKER-DO-NOT-PERSIST-7F3A"  # A token in the fixture body text.


class _ConstantScorer:
    """A scorer test double that returns one fixed label for any sample."""

    def __init__(self, label: str) -> None:
        """Store the fixed label that every score call returns."""
        self._label = label  # The one label this stub always reports.

    def score(self, text: str, source_name: str = "") -> ContentAnalysisResult:
        """Return the fixed label with one numeric score and no body text."""
        scores = {f"technology_domain:{self._label}": 1.0}  # One numeric score entry.
        return ContentAnalysisResult(self._label, (self._label,), scores, is_fallback=False)


def _real_label(pdf_path: Path) -> str:
    """Return the label the current rules assign to one PDF."""
    text = ContentSampler().sample(pdf_path)  # Read the bounded text sample.
    return SignalScorer().score(text, pdf_path.name).sub_category  # The current label.


def _place_file(corpus: Path, label: str, name: str, source_pdf: Path) -> Path:
    """Copy one PDF into a label folder and return the copied path."""
    folder = corpus / UNCATEGORIZED / label  # The label folder under the bucket.
    folder.mkdir(parents=True, exist_ok=True)  # Ensure the label folder exists.
    destination = folder / name  # The copied file path under the label folder.
    shutil.copy(source_pdf, destination)  # Copy the real PDF into the fixture.
    return destination  # The caller records this path in the store.


def _seed_classified(store: HarvestStateStore, root: str, label: str, is_fallback: bool, local_path: Path) -> None:
    """Insert one classified uncategorized document into the store."""
    slug = "software/" + root.rstrip("/").rsplit("/", 1)[-1]  # A stable slug for the record.
    store.add_document(InventoryRecord(root, slug, DocumentType.HTML_ROOT))  # Add the row.
    store.set_category(root, UNCATEGORIZED)  # The uncategorized bucket needs content analysis.
    pdf_url = root + "doc.pdf"  # A resolved PDF URL unique to this document root.
    store.set_resolved(root, pdf_url, [PdfCandidate(pdf_url, True, "direct-pdf")])  # Resolution.
    store.mark_downloaded(root, str(local_path), local_path.stat().st_size)  # The saved file.
    store.set_classified(root, label, is_fallback)  # The stored label and fallback flag.


def _fetch_document(db_path: Path, root: str) -> sqlite3.Row:
    """Return one document row read through a fresh, closed connection."""
    connection = sqlite3.connect(str(db_path))  # Open a fresh read connection.
    connection.row_factory = sqlite3.Row  # Read each column by name.
    try:
        row = connection.execute("SELECT * FROM documents WHERE root_url = ?", (root,)).fetchone()
    finally:
        connection.close()  # Always release the database file for cleanup.
    assert row is not None  # The seeded document must exist.
    return row  # The caller reads the stored fields.


def _score_names(db_path: Path, root: str) -> set[tuple[str, str]]:
    """Return the (group, name) pairs stored for one document."""
    connection = sqlite3.connect(str(db_path))  # Open a fresh read connection.
    try:
        rows = connection.execute(
            "SELECT signal_group, signal_name FROM content_scores WHERE root_url = ?", (root,)
        ).fetchall()  # Every score row for the document.
    finally:
        connection.close()  # Always release the database file for cleanup.
    return {(row[0], row[1]) for row in rows}  # The distinct group and name pairs.


def _dump_all_text(db_path: Path) -> str:
    """Return the string of every row of every table, for a privacy audit."""
    connection = sqlite3.connect(str(db_path))  # Open a fresh read connection.
    tables = ["documents", "pdf_candidates", "content_scores", "dropped_release_notes", "run_meta"]
    try:
        return "".join(str(connection.execute(f"SELECT * FROM {table}").fetchall()) for table in tables)
    finally:
        connection.close()  # Always release the database file for cleanup.


def test_changed_label_moves_file_and_updates_row(tmp_path: Path) -> None:
    """A document whose label changes is moved and its row is updated."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    new_label = _real_label(_OPTICS)  # The current rules assign this label.
    old_label = new_label + "-old"  # The stored label differs, so a change happens.
    old_file = _place_file(corpus, old_label, _OPTICS.name, _OPTICS)  # File in the old folder.
    root = "https://x/optics/"  # The document root URL.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, root, old_label, True, old_file)  # Seed the stored label.
        store.record_scores(root, [("task_type", "licensing", 0.105)])  # The old noisy score.
    stats = CorpusReclassifier(corpus, ContentSampler(), SignalScorer(), dry_run=False).run()  # Apply.
    moved = corpus / UNCATEGORIZED / new_label / _OPTICS.name  # The expected new path.
    assert moved.exists()  # The file moved into the new label folder.
    assert not old_file.exists()  # The file left the old label folder.
    assert not (corpus / UNCATEGORIZED / old_label).exists()  # The emptied folder was removed.
    row = _fetch_document(corpus / "harvest_state.db", root)  # Read the updated row.
    assert row["sub_category"] == new_label  # The stored label is the new label.
    assert row["is_fallback"] == 0  # The new real label is not a fallback.
    assert Path(row["local_path"]) == moved  # The stored path is the new path.
    assert ("task_type", "licensing") not in _score_names(corpus / "harvest_state.db", root)  # Replaced.
    assert stats.inspected == 1 and stats.changed == 1 and stats.unchanged == 0  # The counts.


def test_unchanged_label_is_left_alone(tmp_path: Path) -> None:
    """A document whose label does not change is left alone."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    label = _real_label(_OPTICS)  # The stored label already matches the current rules.
    resting = _place_file(corpus, label, _OPTICS.name, _OPTICS)  # File already in the folder.
    root = "https://x/optics/"  # The document root URL.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, root, label, False, resting)  # Seed the matching label.
        store.record_scores(root, [("technology_domain", "routing", 0.5)])  # The stored score.
    before = resting.stat().st_mtime_ns  # The file modification time before the pass.
    stats = CorpusReclassifier(corpus, ContentSampler(), SignalScorer(), dry_run=False).run()  # Apply.
    assert resting.exists()  # The file did not move.
    assert resting.stat().st_mtime_ns == before  # The file was not rewritten.
    row = _fetch_document(corpus / "harvest_state.db", root)  # Read the row.
    assert row["sub_category"] == label  # The stored label is unchanged.
    assert row["local_path"] == str(resting)  # The stored path is unchanged.
    assert stats.inspected == 1 and stats.changed == 0 and stats.unchanged == 1  # The counts.


def test_dry_run_changes_nothing(tmp_path: Path) -> None:
    """A dry run changes nothing on disk and nothing in the database."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    new_label = _real_label(_OPTICS)  # The current rules would assign this label.
    old_label = new_label + "-old"  # The stored label differs, so a change would happen.
    old_file = _place_file(corpus, old_label, _OPTICS.name, _OPTICS)  # File in the old folder.
    root = "https://x/optics/"  # The document root URL.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, root, old_label, True, old_file)  # Seed the stored label.
        store.record_scores(root, [("task_type", "licensing", 0.105)])  # The old noisy score.
    row_before = dict(_fetch_document(corpus / "harvest_state.db", root))  # Snapshot the row.
    stats = CorpusReclassifier(corpus, ContentSampler(), SignalScorer()).run()  # Dry run default.
    assert old_file.exists()  # The file stayed in the old folder.
    assert not (corpus / UNCATEGORIZED / new_label).exists()  # No new folder was created.
    assert dict(_fetch_document(corpus / "harvest_state.db", root)) == row_before  # The row is intact.
    assert ("task_type", "licensing") in _score_names(corpus / "harvest_state.db", root)  # Scores intact.
    assert stats.inspected == 1 and stats.changed == 1  # The dry run still reports the change.


def test_collision_disambiguates_instead_of_overwriting(tmp_path: Path) -> None:
    """A move that would overwrite a different file disambiguates instead."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    file_a = _place_file(corpus, "label-a", "report.pdf", _OPTICS)  # Document A, one name.
    file_b = _place_file(corpus, "label-b", "report.pdf", _EVPN)  # Document B, same name.
    size_a, size_b = file_a.stat().st_size, file_b.stat().st_size  # The two distinct sizes.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, "https://x/a/", "label-a", False, file_a)  # Document A row.
        _seed_classified(store, "https://x/b/", "label-b", False, file_b)  # Document B row.
    scorer = _ConstantScorer("shared")  # Both documents now score the one shared label.
    stats = CorpusReclassifier(corpus, ContentSampler(), scorer, dry_run=False).run()  # Apply.
    shared = corpus / UNCATEGORIZED / "shared"  # The shared destination folder.
    stored = sorted(shared.glob("*.pdf"), key=lambda path: path.stat().st_size)  # The two files.
    assert len(stored) == 2  # Two distinct documents landed, so neither overwrote the other.
    assert [path.stat().st_size for path in stored] == sorted([size_a, size_b])  # Both kept.
    assert stats.inspected == 2 and stats.changed == 2  # Both documents changed label.
    assert stats.labels_before == 2 and stats.labels_after == 1  # Two labels became one.


def test_unreadable_pdf_is_counted_and_pass_continues(tmp_path: Path) -> None:
    """An unreadable PDF is counted and does not stop the pass."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    bad_folder = corpus / UNCATEGORIZED / "label-bad"  # The unreadable document folder.
    bad_folder.mkdir(parents=True)  # Create the folder for the unreadable file.
    bad_file = bad_folder / "broken.pdf"  # The unreadable file path.
    bad_file.write_bytes(b"this is not a valid pdf body")  # Bytes that yield no text.
    new_label = _real_label(_OPTICS)  # The readable document scores this label.
    good_file = _place_file(corpus, new_label + "-old", _OPTICS.name, _OPTICS)  # Readable file.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, "https://x/a-bad/", "label-bad", False, bad_file)  # First row.
        _seed_classified(store, "https://x/b-good/", new_label + "-old", True, good_file)  # Second.
    stats = CorpusReclassifier(corpus, ContentSampler(), SignalScorer(), dry_run=False).run()  # Apply.
    assert stats.inspected == 2 and stats.unreadable == 1 and stats.changed == 1  # The counts.
    assert bad_file.exists()  # The unreadable file was left alone.
    assert (corpus / UNCATEGORIZED / new_label / _OPTICS.name).exists()  # The pass continued.


def test_no_body_text_is_written_anywhere(tmp_path: Path) -> None:
    """No body text is written into the database or any durable file."""
    corpus = tmp_path / "juniper_corpus"  # The fixture corpus root.
    marker_pdf = FIXTURES / "sample_uncategorized.pdf"  # A PDF with a unique body marker.
    new_label = _real_label(marker_pdf)  # The current label for the marker PDF.
    old_file = _place_file(corpus, new_label + "-old", marker_pdf.name, marker_pdf)  # Old folder.
    root = "https://x/marker/"  # The document root URL.
    with HarvestStateStore(corpus / "harvest_state.db") as store:  # Build the fixture store.
        _seed_classified(store, root, new_label + "-old", True, old_file)  # Seed a change.
    CorpusReclassifier(corpus, ContentSampler(), SignalScorer(), dry_run=False).run()  # Apply.
    assert _MARKER not in _dump_all_text(corpus / "harvest_state.db")  # No marker in the store.
    for path in corpus.rglob("*"):  # Walk every file under the corpus tree.
        if path.is_file() and path.suffix != ".pdf":  # A PDF legitimately holds its own text.
            assert _MARKER.encode() not in path.read_bytes()  # No marker in a non-PDF file.
