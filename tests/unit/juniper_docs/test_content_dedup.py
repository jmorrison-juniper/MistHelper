"""Unit tests for SHA256 content deduplication in the corpus harvest (issue #2977)."""

from __future__ import annotations

from pathlib import Path

from src.mist.intelligence.juniper_docs.acquire.downloader import CorpusDownloader
from src.mist.intelligence.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.mist.intelligence.juniper_docs.harvest.content_index import CorpusContentIndex
from tests.unit.juniper_docs.conftest import FakeCatalogClient

_PDF = (Path(__file__).parent / "fixtures" / "minimal.pdf").read_bytes()  # Valid offline PDF.


def _downloader(tmp_path: Path, payloads: dict[str, bytes]) -> CorpusDownloader:
    """Return a downloader over a fake client with no known URL owners."""
    return CorpusDownloader(FakeCatalogClient(payloads=payloads), tmp_path, PdfPathAllocator({}.get))


def test_same_bytes_under_different_names_keep_one_file(tmp_path: Path) -> None:
    """A second URL with a different name and category reuses the first file."""
    downloader = _downloader(tmp_path, {"https://x/a.pdf": _PDF, "https://x/b-copy.pdf": _PDF})
    first = downloader.download_document("https://x/a.pdf", tmp_path / "cat1")
    second = downloader.download_document("https://x/b-copy.pdf", tmp_path / "cat2")
    assert first[0] == "downloaded"  # The first document is written.
    assert second[0] == "skipped"  # The duplicate is not written.
    assert second[1] == first[1]  # Both URLs point at one canonical path.
    assert len(list(tmp_path.rglob("*.pdf"))) == 1  # Exactly one file exists.


def test_existing_file_from_earlier_run_is_canonical(tmp_path: Path) -> None:
    """A file stored before this run is found by content under a new name."""
    old = tmp_path / "old" / "legacy.pdf"
    old.parent.mkdir()
    old.write_bytes(_PDF)  # Stored by an earlier run.
    outcome, path, _size, _reason = _downloader(tmp_path, {"https://x/new.pdf": _PDF}).download_document(
        "https://x/new.pdf", tmp_path / "other"
    )
    assert outcome == "skipped"  # Nothing new is written.
    assert path == str(old)  # The earlier file stays canonical.
    assert not (tmp_path / "other" / "new.pdf").exists()  # No duplicate appears.


def test_different_bytes_are_both_kept(tmp_path: Path) -> None:
    """Distinct documents of equal size are not merged."""
    other = _PDF + b"\n%%x"  # Different bytes, still a valid PDF tail.
    downloader = _downloader(tmp_path, {"https://x/a.pdf": _PDF, "https://x/b.pdf": other})
    downloader.download_document("https://x/a.pdf", tmp_path / "c1")
    outcome = downloader.download_document("https://x/b.pdf", tmp_path / "c2")[0]
    assert outcome == "downloaded"  # A distinct document is stored.
    assert len(list(tmp_path.rglob("*.pdf"))) == 2  # Both files exist.


def test_index_reads_only_and_ignores_empty_and_missing(tmp_path: Path) -> None:
    """The index never changes the folder and skips an empty file."""
    (tmp_path / "empty.pdf").write_bytes(b"")  # Zero-byte file is not a document.
    before = sorted(p.name for p in tmp_path.rglob("*"))
    index = CorpusContentIndex(tmp_path)
    assert index.find(_PDF) is None  # Nothing matches.
    assert sorted(p.name for p in tmp_path.rglob("*")) == before  # Folder unchanged.


def test_index_drops_canonical_path_that_was_removed(tmp_path: Path) -> None:
    """A registered file that disappears no longer matches."""
    index = CorpusContentIndex(tmp_path)
    stored = tmp_path / "a.pdf"
    stored.write_bytes(_PDF)
    index.register(stored, _PDF)
    assert index.find(_PDF) == stored  # Present, so it matches.
    stored.unlink()
    assert index.find(_PDF) is None  # Removed, so it no longer matches.


def test_index_finds_canonical_file_after_reclassification_move(tmp_path: Path) -> None:
    """A canonical PDF remains findable after reclassification moves its path."""
    original = tmp_path / "uncategorized" / "guide.pdf"  # Initial harvest path.
    original.parent.mkdir(parents=True)  # Make the temporary source folder.
    original.write_bytes(_PDF)  # Store a valid PDF before indexing.
    index = CorpusContentIndex(tmp_path)  # Index the configured test corpus.
    assert index.find(_PDF) == original  # Cache the original canonical path.
    moved = tmp_path / "uncategorized" / "classified" / "guide.pdf"  # Reclassified path.
    moved.parent.mkdir(parents=True)  # Make the target category folder.
    original.replace(moved)  # Simulate the runner moving the PDF after indexing.
    assert index.find(_PDF) == moved  # Return the current path instead of writing a copy.


def test_index_finds_remaining_duplicate_after_canonical_is_removed(tmp_path: Path) -> None:
    """A remaining matching PDF replaces a removed canonical path."""
    canonical = tmp_path / "a.pdf"  # Stable sorting selects this path first.
    remaining = tmp_path / "b.pdf"  # This copy remains after the first path disappears.
    canonical.write_bytes(_PDF)  # Create the first identical PDF.
    remaining.write_bytes(_PDF)  # Create a second identical PDF.
    index = CorpusContentIndex(tmp_path)  # Index both temporary files.
    assert index.find(_PDF) == canonical  # Confirm the first path is canonical.
    canonical.unlink()  # Simulate removal of the canonical copy.
    assert index.find(_PDF) == remaining  # Reuse the remaining matching path.
