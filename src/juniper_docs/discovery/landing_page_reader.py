"""Read each Juniper product landing page and extract its direct-PDF references.

The documentation sitemap lists one landing page for each product, under the
``/documentation/product/`` path. A landing page names the datasheet, the
release notes, the letter of volatility, and the guides for that product, so it
is a third corpus source beside the documentation tree and the marketing
sitemap.

This reader takes the sitemap URLs, keeps the product landing pages, fetches one
page at a time, and returns every PDF the page names. Each PDF is already a
direct file, so it flows to the downloader with no companion resolution, exactly
like a marketing asset. The reader keeps a Juniper host and skips a third-party
partner host, because the corpus holds Juniper documents only.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each landing page read for observability.
import re  # Extract each PDF reference from the page markup.
from urllib.parse import urljoin, urlsplit  # Resolve a reference and read its host.

from src.juniper_docs.acquire.catalog_client import JvdCatalogClient  # Shared HTTP client.

_LOGGER = logging.getLogger(__name__)  # Module logger for every landing page read.

LANDING_MARKER = "/documentation/product/"  # Path marker of a product landing page.
_KEPT_HOST_SUFFIX = "juniper.net"  # Keep a Juniper host; skip a third-party host.
_PDF_PATTERN = re.compile(r"""["'(]([^"'()\s]+\.pdf)""", re.IGNORECASE)  # Quoted PDF path.


class ProductLandingReader:
    """Read each product landing page and extract its direct-PDF references."""

    def __init__(self, client: JvdCatalogClient) -> None:
        """Store the shared HTTP client for every landing page read."""
        self.client = client  # Reuse one client for every request.

    def landing_pages(self, urls: list[str]) -> list[str]:
        """Return the sorted, unique product landing pages among the sitemap URLs."""
        _LOGGER.info("Selecting product landing pages from %d URLs", len(urls))  # Log intent.
        pages = {url for url in urls if self.is_landing_page(url)}  # Keep the landing pages.
        _LOGGER.debug("Selected %d product landing pages", len(pages))  # Result count.
        return sorted(pages)  # The runner fetches each page in a stable order.

    def pdf_urls_on_page(self, page_url: str) -> list[str]:
        """Return every Juniper-hosted PDF URL that one landing page names."""
        _LOGGER.info("Reading product landing page %s", page_url)  # Log the intent.
        html = self.client.fetch_text(page_url)  # Fetch the landing page markup.
        absolute = {urljoin(page_url, ref) for ref in _PDF_PATTERN.findall(html)}  # Resolve.
        kept = sorted(url for url in absolute if self._is_kept_host(url))  # Keep Juniper hosts.
        _LOGGER.debug("Landing page %s named %d Juniper PDFs", page_url, len(kept))  # Count.
        return kept  # Each URL flows to the downloader as a direct PDF.

    @staticmethod
    def is_landing_page(url: str) -> bool:
        """Return True when a URL is a product landing directory page."""
        lowered = url.lower()  # Compare in one case only.
        return LANDING_MARKER in lowered and lowered.endswith("/")  # A landing directory.

    @staticmethod
    def _is_kept_host(url: str) -> bool:
        """Return True when a PDF URL sits on a Juniper host, not a partner host."""
        host = urlsplit(url).netloc.lower()  # The host of this PDF reference.
        return host == _KEPT_HOST_SUFFIX or host.endswith("." + _KEPT_HOST_SUFFIX)  # Juniper.
