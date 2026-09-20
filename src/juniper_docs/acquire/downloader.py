"""Download and save each resolved Juniper PDF.

The base class is promoted from ``scripts/crawl_jvd.py`` with its behavior
intact. The corpus downloader adds a collision-safe policy through the shared
path allocator, so two remote PDF files that share a file name no longer land on
one local path (issue #2738). It rejects a body that does not start with the
``%PDF`` marker, and it writes the file only when the body is a real PDF.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each download step for observability.
import urllib.error  # Classify a URL error or an HTTP error during a read.
from pathlib import Path  # Build every output path in a portable way.

from src.juniper_docs.acquire.catalog_client import JvdCatalogClient, is_transient_error  # Client.
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator  # Collision-safe path policy.

_LOGGER = logging.getLogger(__name__)  # Module logger for every download.


class JvdDownloader:
    """Download and save each resolved JVD PDF."""

    def __init__(self, client: JvdCatalogClient, out_dir: Path) -> None:
        """Store the client and make sure the output directory exists."""
        self.client = client  # Reuse the shared HTTP client.
        self.out_dir = out_dir  # Directory that receives the PDF files.
        self.out_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists.

    def download(self, pdf_url: str) -> bool:
        """Save one PDF and report whether the file now exists."""
        name = pdf_url.rsplit("/", 1)[-1].split("?")[0]  # Strip any query string.
        target = self.out_dir / name  # Full path of the saved file.
        if target.exists() and target.stat().st_size > 0:  # Skip a repeat download.
            _LOGGER.info("Already downloaded %s", name)  # Report the skip.
            return True  # The file is already present, so report success.
        _LOGGER.info("Downloading %s", pdf_url)  # Log before the transfer.
        try:
            payload = self.client.fetch_bytes(pdf_url)  # Pull the PDF bytes.
        except (urllib.error.URLError, urllib.error.HTTPError) as error:  # A read may fail.
            _LOGGER.error("Download failed for %s: %s", pdf_url, error)  # Record failure.
            return False  # A failed read is not a successful download.
        if not payload.startswith(b"%PDF"):  # Guard against an HTML error page.
            _LOGGER.error("The response for %s is not a PDF", pdf_url)  # Record the reject.
            return False  # A non-PDF body is not a successful download.
        target.write_bytes(payload)  # Persist the file to disk.
        _LOGGER.debug("Saved %s (%d bytes)", name, len(payload))  # Report the size.
        return True  # The file is written, so report success.


class CorpusDownloader(JvdDownloader):
    """Download one companion PDF into its category folder and report the outcome."""

    def __init__(self, client: JvdCatalogClient, out_dir: Path, allocator: PdfPathAllocator) -> None:
        """Store the client, the output directory, and the collision-safe allocator."""
        super().__init__(client, out_dir)  # Reuse the base client and output directory.
        self._allocator = allocator  # Choose a unique path so no write destroys a file.

    def download_document(self, pdf_url: str, category_dir: Path) -> tuple[str, str | None, int | None, str | None]:
        """Return the outcome, the local path, the size, and a failure reason."""
        _LOGGER.info("Fetching %s into %s", pdf_url, category_dir)  # Log the intent.
        target = self._prepare_target(pdf_url, category_dir)  # Build the clean target path.
        reuse = self._allocator.existing_for_url(target, pdf_url)  # A same-URL file, if any.
        if reuse is not None:  # This exact URL already produced a stored file.
            _LOGGER.debug("Skipped existing %s", reuse.name)  # Report the resume skip.
            return "skipped", str(reuse), reuse.stat().st_size, None  # Reuse it with no fetch.
        payload, reason = self._fetch_valid(pdf_url)  # Fetch the bytes and check the marker.
        if payload is None:  # The read failed or the body is not a PDF.
            return "failed", None, None, reason  # A bad response reports its reason.
        final, write = self._allocator.plan_bytes(target, pdf_url, payload)  # Resolve the path.
        return self._store_payload(final, payload, write)  # Write or reuse, then report it.

    def _store_payload(self, final: Path, payload: bytes, write: bool) -> tuple[str, str, int, None]:
        """Write the payload when needed, then report the outcome, path, and size."""
        if write:  # The resolved path is free, so this is a fresh distinct document.
            self._atomic_write(final, payload)  # Write to a temp file, then rename onto it.
            _LOGGER.debug("Downloaded %s (%d bytes)", final.name, len(payload))  # Report size.
            return "downloaded", str(final), len(payload), None  # Count it as a fresh download.
        _LOGGER.debug("Reused identical %s (%d bytes)", final.name, final.stat().st_size)  # Dedup.
        return "skipped", str(final), final.stat().st_size, None  # An identical document is one file.

    @staticmethod
    def _atomic_write(target: Path, payload: bytes) -> None:
        """Write the payload to a temp file, then rename it onto the target.

        An interruption leaves the partial bytes in the temp file, never at the
        target path, so a resume never treats a partial download as complete.
        """
        temp = target.parent / (target.name + ".part")  # The temporary write path.
        temp.write_bytes(payload)  # Write the full payload to the temp file.
        temp.replace(target)  # Rename the temp file onto the target atomically.

    @staticmethod
    def _prepare_target(pdf_url: str, category_dir: Path) -> Path:
        """Return the target path and make sure the category folder exists."""
        category_dir.mkdir(parents=True, exist_ok=True)  # Ensure the category folder.
        name = pdf_url.rsplit("/", 1)[-1].split("?")[0]  # Strip any query string.
        return category_dir / name  # The full path of the saved file.

    def _fetch_valid(self, pdf_url: str) -> tuple[bytes | None, str | None]:
        """Return the PDF bytes and no reason, or None and a failure reason."""
        try:
            payload = self.client.fetch_bytes(pdf_url)  # Pull the response bytes.
        except (urllib.error.URLError, OSError) as error:  # A network or HTTP error.
            _LOGGER.error("Download failed for %s: %s", pdf_url, error)  # Record failure.
            prefix = "transient" if is_transient_error(error) else "permanent"  # Classify.
            return None, f"{prefix}: {error}"  # A failed read reports its reason.
        if not payload.startswith(b"%PDF"):  # Guard against an HTML error page.
            _LOGGER.error("The response for %s is not a PDF", pdf_url)  # Record the reject.
            return None, "permanent: not a PDF"  # A non-PDF body is a permanent failure.
        return payload, None  # The body is a real PDF, so return the bytes.
