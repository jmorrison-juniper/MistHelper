"""Unit tests for the corpus downloader (T021, FR-014, FR-015, FR-019)."""

from __future__ import annotations

from pathlib import Path

from src.juniper_docs.acquire.downloader import CorpusDownloader, JvdDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from tests.unit.juniper_docs.conftest import FakeCatalogClient


def _allocator(owners: dict[str, str] | None = None) -> PdfPathAllocator:
    """Return an allocator whose owner lookup reads a fixed path-to-URL map."""
    resolved = owners or {}  # An empty map means no stored path has a known owner.
    return PdfPathAllocator(resolved.get)  # The lookup returns the owning URL or None.


def test_downloads_a_valid_pdf(tmp_path: Path) -> None:
    """A body that starts with the marker is written and counted downloaded."""
    url = "https://x/a.pdf"  # The PDF URL to download.
    client = FakeCatalogClient(payloads={url: b"%PDF-1.4 minimal body"})  # A valid PDF.
    downloader = CorpusDownloader(client, tmp_path, _allocator())  # A fresh downloader.
    outcome, path, size, reason = downloader.download_document(url, tmp_path / "cat")
    assert outcome == "downloaded"  # A valid PDF is downloaded.
    assert path is not None and Path(path).exists()  # The file is on disk.
    assert size == len(b"%PDF-1.4 minimal body")  # The size is the byte count.
    assert reason is None  # A successful download reports no failure reason.


def test_skips_a_same_url_file_without_a_fetch(tmp_path: Path) -> None:
    """An existing file owned by the same URL is skipped and no network read happens."""
    category = tmp_path / "cat"  # The category folder.
    category.mkdir()  # Create the folder for the pre-existing file.
    stored = category / "a.pdf"  # The pre-existing file path.
    stored.write_bytes(b"%PDF already here")  # A pre-existing file from a prior run.
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
    assert reason == "permanent: not a PDF"  # A non-PDF body is a permanent failure.


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
