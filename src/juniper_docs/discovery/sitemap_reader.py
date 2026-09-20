"""Read the sitemap index and each United States and English child sitemap.

The reader fetches the sitemap index, keeps the United States and English child
sitemaps, and extracts every document URL. It reads a remote source through the
shared HTTP client and a local source through the file system, so a recorded
subset drives a test without a network call (FR-001, FR-002).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each sitemap read for observability.
import re  # Extract the loc values and tokenize a child sitemap URL.
import urllib.error  # Tolerate a per-child sitemap fetch failure.
from pathlib import Path  # Read a local sitemap source in a portable way.

from src.juniper_docs.acquire.catalog_client import JvdCatalogClient  # Shared HTTP client.

_LOGGER = logging.getLogger(__name__)  # Module logger for every sitemap read.

_LOC_PATTERN = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE | re.DOTALL)  # Loc tags.


class SitemapReader:
    """Read the sitemap index and every United States and English child sitemap."""

    def __init__(self, client: JvdCatalogClient) -> None:
        """Store the shared HTTP client for every remote sitemap read."""
        self.client = client  # Reuse one client for every request.

    def read_all_urls(self, source: str) -> list[str]:
        """Return every document URL from an index source or a single child."""
        _LOGGER.info("Reading every document URL from %s", source)  # Log the intent.
        text = self._fetch(source)  # Fetch the index or the single child once.
        if "<sitemapindex" in text:  # The source is an index of child sitemaps.
            urls = self._read_children(self._us_en_children(text))  # Walk each child.
        else:  # The source is a single urlset child sitemap.
            urls = self._extract_locs(text)  # Extract the document URLs directly.
        _LOGGER.debug("Read %d document URLs from %s", len(urls), source)  # Result count.
        return urls  # The builder turns these URLs into inventory records.

    def read_pdf_urls(self, source: str) -> list[str]:
        """Return every direct-PDF URL from one flat sitemap source.

        The marketing sitemap holds a flat list of asset URLs. A marketing PDF
        entry already names the file, so the runner downloads it with no
        companion-PDF resolution (FR-011).
        """
        _LOGGER.info("Reading direct-PDF URLs from %s", source)  # Log the intent.
        pdfs = [url for url in self.read_all_urls(source) if url.lower().endswith(".pdf")]  # PDFs.
        _LOGGER.debug("Kept %d direct-PDF URLs from %s", len(pdfs), source)  # Result count.
        return pdfs  # Each URL flows straight to the downloader as a direct PDF.

    def read_index(self, source: str) -> list[str]:
        """Return the United States and English child sitemap URLs of an index."""
        _LOGGER.info("Reading the sitemap index at %s", source)  # Log the intent.
        children = self._us_en_children(self._fetch(source))  # Filter to US and EN.
        _LOGGER.debug("Kept %d US and EN child sitemaps", len(children))  # Result count.
        return children  # The reader fetches each child in turn.

    def read_child(self, source: str) -> list[str]:
        """Return every document URL from one child sitemap."""
        _LOGGER.debug("Reading a child sitemap at %s", source)  # Trace the child read.
        return self._extract_locs(self._fetch(source))  # Extract the document URLs.

    def _read_children(self, children: list[str]) -> list[str]:
        """Return every document URL across the given child sitemaps."""
        urls: list[str] = []  # Accumulate every document URL across the children.
        for child in children:  # Read each United States and English child in turn.
            try:
                urls.extend(self.read_child(child))  # Add this child's document URLs.
            except (urllib.error.URLError, urllib.error.HTTPError) as error:  # One bad child.
                _LOGGER.warning("Skipping child sitemap %s: %s", child, error)  # Record the miss.
        return urls  # The combined URL list feeds the inventory builder.

    def _us_en_children(self, text: str) -> list[str]:
        """Return the child sitemap URLs that carry the US and EN language."""
        return [loc for loc in self._extract_locs(text) if self._is_us_en(loc)]  # Filter.

    def _fetch(self, source: str) -> str:
        """Return the sitemap text from a remote URL or a local file path."""
        if source.startswith(("http://", "https://")):  # A remote sitemap source.
            return self.client.fetch_text(source)  # Read it through the HTTP client.
        return Path(source).read_text(encoding="utf-8")  # Read a local recorded subset.

    @staticmethod
    def _extract_locs(text: str) -> list[str]:
        """Return every loc value found in one sitemap document."""
        return [match.strip() for match in _LOC_PATTERN.findall(text)]  # Loc values.

    @staticmethod
    def _is_us_en(url: str) -> bool:
        """Return True when a child sitemap URL carries the US and EN tokens."""
        tokens = re.split(r"[^a-z0-9]+", url.lower())  # Split the URL into tokens.
        return "us" in tokens and "en" in tokens  # Keep only US and English children.
