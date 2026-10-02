"""Download and save each resolved Juniper PDF.

The base class is promoted from ``scripts/crawl_jvd.py`` with its behavior
intact. The corpus downloader adds a collision-safe policy through the shared
path allocator, so two remote PDF files that share a file name no longer land on
one local path (issue #2738). It rejects a body that does not start with the
``%PDF`` marker, and it writes the file only when the body is a real PDF.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each download step for observability.
import os
import urllib.error  # Classify a URL error or an HTTP error during a read.
from pathlib import Path  # Build every output path in a portable way.
from urllib.parse import urlsplit

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
        self._allocator.index_corpus(out_dir)

    def download_document(self, pdf_url: str, category_dir: Path) -> tuple[str, str | None, int | None, str | None]:
        """Return the outcome, the local path, the size, and a failure reason."""
        _LOGGER.info("Acquiring 1 corpus document into %s", category_dir)
        try:
            target = self._prepare_target(pdf_url, category_dir)
            return self._download_prepared(pdf_url, target)
        except OSError as error:
            _LOGGER.exception("The local corpus document operation failed")
            return "failed", None, None, f"permanent: local corpus operation failed: {error}"

    def _download_prepared(self, pdf_url: str, target: Path) -> tuple[str, str | None, int | None, str | None]:
        """Reuse verified URL state or fetch and compare one new response."""
        reuse = self._allocator.existing_for_url(target, pdf_url)
        if reuse is not None:
            self._allocator.record_download(reuse, pdf_url)
            _LOGGER.debug("Skipped 1 verified existing payload")
            return "skipped", str(reuse), reuse.stat().st_size, None
        payload, reason = self._fetch_valid(pdf_url)
        if payload is None:
            return "failed", None, None, reason
        final, write = self._allocator.plan_bytes(target, pdf_url, payload)
        return self._store_payload(final, payload, write, pdf_url)

    def _store_payload(self, final: Path, payload: bytes, write: bool, pdf_url: str) -> tuple[str, str, int, None]:
        """Write the payload when needed, then report the outcome, path, and size."""
        if write:
            self._atomic_write(final, payload)
        self._allocator.record_download(final, pdf_url)
        outcome = "downloaded" if write else "skipped"
        _LOGGER.debug("Acquired 1 document: outcome=%s bytes=%d", outcome, len(payload))
        return outcome, str(final), len(payload), None

    @staticmethod
    def _atomic_write(target: Path, payload: bytes) -> None:
        """Write the payload to a temp file, then rename it onto the target.

        An interruption leaves the partial bytes in the temp file, never at the
        target path, so a resume never treats a partial download as complete.
        """
        temp = target.with_name(target.name + ".part")
        if temp.is_symlink():
            raise OSError("The temporary corpus path cannot be a symbolic link.")
        _LOGGER.info("Writing 1 temporary payload with %d bytes", len(payload))
        try:
            with temp.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            _LOGGER.debug("Wrote 1 complete temporary payload with %d bytes", len(payload))
            _LOGGER.info("Publishing 1 complete corpus payload")
            if target.is_symlink() or (target.exists() and target.stat().st_size > 0):
                raise FileExistsError("A complete corpus destination appeared before publication.")
            temp.replace(target)
            _LOGGER.debug("Published 1 complete corpus payload")
        finally:
            temp.unlink(missing_ok=True)  # Remove only this operation's transient file.

    def _prepare_target(self, pdf_url: str, category_dir: Path) -> Path:
        """Return the target path and make sure the category folder exists."""
        name = urlsplit(pdf_url).path.rsplit("/", 1)[-1]
        if not name or name in (".", "..") or Path(name).suffix.lower() == ".part":
            raise OSError("The corpus URL has no usable PDF file name.")
        target = category_dir / name
        self._allocator._key(target)
        _LOGGER.info("Preparing 1 corpus category directory")
        category_dir.mkdir(parents=True, exist_ok=True)
        _LOGGER.debug("Prepared 1 corpus category directory")
        return target

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
