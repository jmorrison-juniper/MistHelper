"""Build the document inventory from the raw sitemap URLs.

The builder maps each chapter page under a ``/topics/`` path to its parent
document root, removes a URL that appears in more than one child sitemap, and
splits the inventory into HTML roots and direct PDF URLs. Each document then
appears once, keyed by its normalized root URL (FR-003, FR-004).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace the inventory build for observability.
from urllib.parse import urlsplit  # Parse the path portion of one document URL.

from src.juniper_docs.models import DocumentType, InventoryRecord  # Shared record types.

_LOGGER = logging.getLogger(__name__)  # Module logger for the inventory build.

_LOCALE_TOKENS = ("us", "en", "en_us")  # Leading locale segments to drop from a slug.

# Path segments that hold the chapters of one guide. A page below one of these
# belongs to the guide above it, so the builder maps it to that guide root.
_CHAPTER_MARKERS = ("/topics/", "/topic/", "/Other/")


class InventoryBuilder:
    """Turn the raw sitemap URLs into a deduplicated document inventory."""

    def build(self, urls: list[str]) -> list[InventoryRecord]:
        """Return one inventory record per document, keyed by its root URL."""
        _LOGGER.info("Building the inventory from %d URLs", len(urls))  # Log the intent.
        seen: dict[str, InventoryRecord] = {}  # One record per document root URL.
        for url in urls:  # Map, classify, and deduplicate each URL in turn.
            record = self._to_record(url)  # Build the record for this URL.
            seen.setdefault(record.source_url, record)  # Keep the first occurrence.
        _LOGGER.debug("Built %d unique inventory records", len(seen))  # Result count.
        return list(seen.values())  # The runner saves these before any download.

    def _to_record(self, url: str) -> InventoryRecord:
        """Return the inventory record for one sitemap URL."""
        if url.lower().endswith(".pdf"):  # The sitemap entry already names a PDF.
            return InventoryRecord(url, self._slug(url), DocumentType.DIRECT_PDF)  # Direct.
        root = self._root_of(url)  # Map a chapter page to its parent document root.
        return InventoryRecord(root, self._slug(root), DocumentType.HTML_ROOT)  # HTML root.

    @staticmethod
    def _root_of(url: str) -> str:
        """Return the parent document root for one page URL.

        A chapter container cuts back to the guide root, because the guide root
        holds the ``__toc.js`` script that names the one compiled PDF. A chapter
        folder holds no script of its own, so a chapter kept as its own root
        costs one wasted request and then records no PDF. A live check of six
        guides confirmed the guide TOC lists each chapter, so the chapter
        belongs to that guide.
        """
        for marker in _CHAPTER_MARKERS:  # Cut at the first chapter container found.
            if marker in url:  # The page sits inside a chapter container.
                return url.split(marker, 1)[0] + "/"  # Cut back to the guide root.
        if url.endswith("/index.html"):  # An index page serves its own directory.
            return url.rsplit("/", 1)[0] + "/"  # Use the directory as the root.
        if url.endswith(".html"):  # A legacy page names its own companion PDF.
            return url  # Keep the page as the root; never append a trailing slash.
        return url if url.endswith("/") else url + "/"  # Normalize a directory URL.

    @staticmethod
    def _slug(url: str) -> str:
        """Return the normalized document path used for classification."""
        parts = urlsplit(url).path.strip("/").split("/")  # Path segments only.
        if parts and parts[0] == "documentation":  # Drop the documentation prefix.
            parts = parts[1:]  # Keep the segments after documentation.
        while parts and parts[0].lower() in _LOCALE_TOKENS:  # Drop a leading locale.
            parts = parts[1:]  # Keep the segments after the locale.
        return "/".join(parts)  # The joined path is the normalized slug.
