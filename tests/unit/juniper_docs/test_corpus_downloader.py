"""Unit tests for the corpus downloader (T021, FR-014, FR-015, FR-019)."""

from __future__ import annotations

import io
from pathlib import Path

import pdfplumber

from src.mist.intelligence.juniper_docs.acquire.downloader import CorpusDownloader, JvdDownloader
from src.mist.intelligence.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from tests.unit.juniper_docs.conftest import FakeCatalogClient


def _allocator(owners: dict[str, str] | None = None) -> PdfPathAllocator:
    """Return an allocator whose owner lookup reads a fixed path-to-URL map."""
    resolved = owners or {}  # An empty map means no stored path has a known owner.
    return PdfPathAllocator(resolved.get)  # The lookup returns the owning URL or None.


def _valid_pdf() -> bytes:
    """Return a small parser-usable PDF fixture."""
    directory = Path(__file__).parent / "fixtures"  # Reuse the existing offline fixture folder.
    return (directory / "minimal.pdf").read_bytes()  # Return the recorded PDF bytes.


def test_downloads_a_valid_pdf(tmp_path: Path) -> None:
    """A parser-usable PDF is written and counted downloaded."""
    url = "https://x/a.pdf"  # The PDF URL to download.
    payload = _valid_pdf()  # A valid offline PDF.
    client = FakeCatalogClient(payloads={url: payload})  # A valid PDF.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "downloaded"  # A valid PDF is downloaded.
    assert path is not None and Path(path).exists()  # The file is on disk.
    assert size == len(payload)  # The size is the byte count.
    assert reason is None  # A successful download reports no failure reason.


def test_skips_a_same_url_file_without_a_fetch(tmp_path: Path) -> None:
    """An existing file owned by the same URL is skipped and no network read happens."""
    category = tmp_path / "cat"  # The category folder.
    category.mkdir()  # Create the folder for the pre-existing file.
    stored = category / "a.pdf"  # The pre-existing file path.
    stored.write_bytes(_valid_pdf())  # A pre-existing valid file from a prior run.
    owners = {str(stored): "https://x/a.pdf"}  # The store says this URL owns the file.
    client = FakeCatalogClient()  # No payload, so a fetch would fail.
    downloader = CorpusDownloader(client, tmp_path, _allocator(owners))  # Owner-aware downloader.
    outcome, path, _size, _reason = downloader.download_document("https://x/a.pdf", category)
    assert outcome == "skipped"  # The same-URL file is skipped.
    assert path == str(stored)  # The skip points at the stored file.
    assert client.requests == []  # No network read happened for a same-URL skip.


def test_rejects_a_non_pdf_body(tmp_path: Path) -> None:
    """A body that is not a PDF is rejected and never counted as a success."""
    url = "https://x/a.pdf"  # The URL that returns an HTML error page.
    client = FakeCatalogClient(payloads={url: b"<html>error page</html>"})  # Not a PDF.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "failed"  # A non-PDF body fails.
    assert path is None and size is None  # No file and no size are recorded.
    assert reason == "permanent: invalid PDF"  # A non-PDF body is a permanent failure.


def test_rejects_truncated_pdf_bytes(tmp_path: Path) -> None:
    """Truncated PDF bytes fail and do not create a stored file."""
    url = "https://x/truncated.pdf"  # The URL with truncated PDF data.
    payload = _valid_pdf()[:100]  # Remove the cross-reference data from the parser-usable fixture.
    client = FakeCatalogClient(payloads={url: payload})  # The damaged response.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "failed"  # Truncated bytes fail validation.
    assert path is None and size is None  # No damaged file is stored.
    assert reason == "permanent: invalid PDF"  # The parser failure is permanent.


def test_accepts_pdf_without_eof_when_parser_can_read_it(tmp_path: Path) -> None:
    """A parser-usable PDF without EOF remains a successful download."""
    url = "https://x/no-eof.pdf"  # The URL with a missing EOF marker.
    payload = _valid_pdf().replace(b"%%EOF\n", b"")  # Remove only the optional end marker.
    with pdfplumber.open(io.BytesIO(payload)) as document:  # Confirm the fixture is parser-usable.
        assert len(document.pages) == 1  # The parser accepts the missing marker.
    client = FakeCatalogClient(payloads={url: payload})  # The offline response.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, _size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "downloaded"  # Parser-usable bytes are accepted.
    assert path is not None  # The accepted file has a path.
    assert reason is None  # A successful download has no reason.


def test_rejects_malformed_pdf_objects(tmp_path: Path) -> None:
    """Malformed PDF objects fail and do not create a stored file."""
    url = "https://x/malformed.pdf"  # The URL with malformed object data.
    payload = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\nnot-a-dictionary\n"  # Invalid structure.
    client = FakeCatalogClient(payloads={url: payload})  # The malformed response.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "failed"  # Malformed objects fail validation.
    assert path is None and size is None  # No malformed file is stored.
    assert reason == "permanent: invalid PDF"  # The parser failure is permanent.


def test_refetches_when_same_url_stored_file_is_malformed(tmp_path: Path) -> None:
    """A malformed same-URL file is rejected and replaced by valid fetched bytes."""
    category = tmp_path / "cat"  # The category folder.
    category.mkdir()  # Create the folder for the stored file.
    stored = category / "a.pdf"  # The malformed stored file path.
    stored.write_bytes(b"%PDF-1.4\ntruncated")  # The invalid stored bytes.
    url = "https://x/a.pdf"  # The URL that owns the stored path.
    payload = _valid_pdf()  # The valid replacement bytes.
    client = FakeCatalogClient(payloads={url: payload})  # The replacement response.
    downloader = CorpusDownloader(client, tmp_path, _allocator({str(stored): url}))  # Owner-aware downloader.
    outcome, path, size, reason = downloader.download_document(url, category)
    assert outcome == "downloaded"  # The valid response replaces the malformed file.
    assert path == str(stored)  # The original path remains the same.
    assert size == len(payload)  # The stored file now has valid bytes.
    assert reason is None  # The replacement succeeds.
    assert stored.read_bytes() == payload  # The malformed content is not retained.
    assert client.requests == [url]  # The invalid stored file forces one fetch.


def test_download_failure_is_reported(tmp_path: Path) -> None:
    """A network failure during download is reported as a failed outcome."""
    url = "https://x/a.pdf"  # The URL scripted to fail.
    client = FakeCatalogClient(fail_urls=(url,))  # The read raises a URL error.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, _size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "failed"  # The failure is reported.
    assert path is None  # No file is recorded.
    assert reason is not None and reason.startswith("transient")  # A network error is transient.


def test_base_downloader_writes_a_valid_pdf(tmp_path: Path) -> None:
    """The base downloader writes a valid PDF into its output directory."""
    url = "https://x/a.pdf"  # The PDF URL to download.
    client = FakeCatalogClient(payloads={url: b"%PDF base body"})  # A valid PDF.
    assert JvdDownloader(client, tmp_path).download(url) is True  # The download succeeds.
    assert (tmp_path / "a.pdf").read_bytes() == b"%PDF base body"  # The file is on disk.


def test_base_downloader_skips_an_existing_file(tmp_path: Path) -> None:
    """The base downloader skips an existing non-empty file without a fetch."""
    (tmp_path / "a.pdf").write_bytes(b"%PDF already")  # A pre-existing file.
    client = FakeCatalogClient()  # No payload, so a fetch would fail.
    assert JvdDownloader(client, tmp_path).download("https://x/a.pdf") is True  # Skipped.
    assert client.requests == []  # No network read happened for the skip.


def test_base_downloader_rejects_a_non_pdf_body(tmp_path: Path) -> None:
    """The base downloader rejects a body that is not a PDF."""
    url = "https://x/a.pdf"  # The URL returning an HTML error page.
    client = FakeCatalogClient(payloads={url: b"<html>error</html>"})  # Not a PDF.
    assert JvdDownloader(client, tmp_path).download(url) is False  # The body is rejected.


def test_base_downloader_reports_a_failure(tmp_path: Path) -> None:
    """The base downloader reports a network failure as a failed download."""
    url = "https://x/a.pdf"  # The URL scripted to fail.
    client = FakeCatalogClient(fail_urls=(url,))  # The read raises a URL error.
    assert JvdDownloader(client, tmp_path).download(url) is False  # The failure is reported.
