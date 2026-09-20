"""Unit tests for the collision-safe PDF path allocator (issue #2738).

Every test drives the allocator with an in-memory owner map, so no test reads
the network. The map mirrors the state store: it maps a stored local path to the
resolved PDF URL that produced it, exactly as the runner records after a write.
"""

from __future__ import annotations

from pathlib import Path

from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator


def _store(owners: dict[str, str], path: Path, url: str, payload: bytes) -> None:
    """Write a file and record its owning URL, as one download step does."""
    path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the destination folder.
    path.write_bytes(payload)  # Persist the document bytes on disk.
    owners[str(path)] = url  # Record the URL that produced this stored file.


def test_two_different_urls_same_name_get_two_paths(tmp_path: Path) -> None:
    """Two URLs with one base name and different bytes each get a distinct path."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    target = tmp_path / "cat" / "guide.pdf"  # The shared base-name target path.
    first, write_first = allocator.plan_bytes(target, "https://a/guide.pdf", b"%PDF-A body")
    assert write_first is True and first == target  # The first document keeps the clean name.
    _store(owners, first, "https://a/guide.pdf", b"%PDF-A body")  # Record the stored file.
    second, write_second = allocator.plan_bytes(target, "https://b/guide.pdf", b"%PDF-B longer body")
    assert write_second is True  # The second document is distinct, so it must be written.
    assert second != first  # The second document gets its own disambiguated path.
    assert second.name.startswith("guide-") and second.suffix == ".pdf"  # A readable stem stays.


def test_same_url_reuses_the_single_file(tmp_path: Path) -> None:
    """The same URL maps to the one stored file, so a resume needs no fetch."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    target = tmp_path / "cat" / "guide.pdf"  # The stored target path.
    _store(owners, target, "https://a/guide.pdf", b"%PDF-A body")  # A prior download.
    reuse = allocator.existing_for_url(target, "https://a/guide.pdf")  # Check the resume path.
    assert reuse == target  # The same URL reuses the stored file with no new path.


def test_identical_bytes_from_two_urls_stay_one_file(tmp_path: Path) -> None:
    """Two different URLs with identical bytes keep exactly one stored file."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    target = tmp_path / "cat" / "guide.pdf"  # The stored target path.
    body = b"%PDF identical bytes for both urls"  # One byte payload for both URLs.
    _store(owners, target, "https://a/guide.pdf", body)  # The first URL stored the file.
    assert allocator.existing_for_url(target, "https://b/guide.pdf") is None  # A different URL must compare.
    final, write = allocator.plan_bytes(target, "https://b/guide.pdf", body)  # Plan the second.
    assert final == target and write is False  # The identical document is stored one time only.


def test_disambiguated_name_is_stable_for_a_url(tmp_path: Path) -> None:
    """The disambiguated name is a stable function of the URL, so a resume is safe."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    target = tmp_path / "cat" / "guide.pdf"  # The shared base-name target path.
    _store(owners, target, "https://a/guide.pdf", b"%PDF-A body")  # The clean name is taken.
    url_b = "https://b/guide.pdf"  # A different URL with the same base name.
    first, _first_write = allocator.plan_bytes(target, url_b, b"%PDF-B one body")  # Plan once.
    second, _second_write = allocator.plan_bytes(target, url_b, b"%PDF-B one body")  # Plan again.
    assert first == second  # The same URL always maps to the same disambiguated name.


def test_plan_file_keeps_a_distinct_document_and_spares_the_existing(tmp_path: Path) -> None:
    """A move plan disambiguates a different document and never touches the existing file."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    existing = tmp_path / "uncategorized" / "guides" / "guide.pdf"  # A stored label file.
    _store(owners, existing, "https://a/guide.pdf", b"%PDF-A body")  # A prior placement.
    source = tmp_path / "uncategorized" / "guide.pdf"  # The staged new download.
    source.parent.mkdir(parents=True, exist_ok=True)  # Ensure the staging folder.
    source.write_bytes(b"%PDF-B different larger body")  # A different document to place.
    final, move = allocator.plan_file(existing, "https://b/guide.pdf", source)  # Plan the move.
    assert move is True and final != existing  # A distinct document gets its own path.
    assert existing.read_bytes() == b"%PDF-A body"  # The existing file is not destroyed.


def test_plan_file_dedupes_an_identical_document(tmp_path: Path) -> None:
    """A move plan reuses the stored file when the staged bytes are identical."""
    owners: dict[str, str] = {}  # The path-to-URL owner map for the run.
    allocator = PdfPathAllocator(owners.get)  # The allocator reads the owner map.
    existing = tmp_path / "uncategorized" / "guides" / "guide.pdf"  # A stored label file.
    body = b"%PDF identical placement bytes"  # One byte payload for both documents.
    _store(owners, existing, "https://a/guide.pdf", body)  # A prior placement.
    source = tmp_path / "uncategorized" / "guide.pdf"  # The staged new download.
    source.parent.mkdir(parents=True, exist_ok=True)  # Ensure the staging folder.
    source.write_bytes(body)  # The staged bytes match the stored file.
    final, move = allocator.plan_file(existing, "https://b/guide.pdf", source)  # Plan the move.
    assert move is False and final == existing  # One stored file remains for identical bytes.
