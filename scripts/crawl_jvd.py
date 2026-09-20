"""Crawl the Juniper Validated Designs catalog and download every JVD PDF.

The catalog is not a flat list. The landing page embeds a solution list, and
each solution page embeds its own JVD list. This script walks both levels.

The shared HTTP client, the PDF resolver, and the downloader now live in the
``src/juniper_docs/acquire`` package. This script imports them directly and
keeps only the two validated-designs classes: the catalog walker and the run
driver. There is no re-export stub and no compatibility wrapper.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.juniper_docs.acquire.catalog_client import JvdCatalogClient  # noqa: E402
from src.juniper_docs.acquire.downloader import JvdDownloader  # noqa: E402
from src.juniper_docs.acquire.http_config import HttpConfig  # noqa: E402
from src.juniper_docs.acquire.pdf_resolver import JvdPdfResolver  # noqa: E402

SITE = HttpConfig.SITE  # Base origin sourced from the shared HTTP config
LANDING = f"{SITE}/documentation/validated-designs/"  # Solution list page
OUT_DIR = PROJECT_ROOT / "jvd_pdfs"  # Download target
DELAY_SECONDS = HttpConfig.DELAY_SECONDS  # Polite pause sourced from the shared config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class JvdCatalogWalker:
    """Walk the solution list and collect every JVD entry."""

    def __init__(self, client: JvdCatalogClient) -> None:
        """Store the shared client for every catalog read."""
        self.client = client  # Reuse one client for every request

    def list_solutions(self) -> list[dict]:
        """Return every solution defined on the landing page."""
        logging.info("Listing solutions from the validated designs landing page")
        groups = self.client.read_page_data(LANDING) or []  # Top level groups
        solutions: list[dict] = []  # Accumulate the flattened solution records
        for group in groups:  # Each group holds one or more solutions
            for solution in group.get("solutionList", []):  # Walk the inner list
                code_name = solution.get("codeName")  # URL slug of the solution
                if not code_name:  # Skip a malformed record
                    continue
                solutions.append(  # Keep only the fields the crawl needs
                    {"name": solution.get("name", code_name), "code": code_name}
                )
        logging.debug("Found %d solutions", len(solutions))  # Report the count
        return solutions

    def list_jvds(self, code_name: str) -> list[dict]:
        """Return every JVD entry for one solution."""
        url = f"{SITE}/documentation/validated-designs/us/en/{code_name}/"
        data = self.client.read_page_data(url)  # Read the solution page block
        if not isinstance(data, dict):  # The solution page shape is a mapping
            logging.warning("Solution %s returned no catalog mapping", code_name)
            return []
        entries = data.get("jvds", [])  # The JVD array lives under this key
        logging.debug("Solution %s lists %d entries", code_name, len(entries))
        return entries


class JvdCrawlRunner:
    """Run the full two-level crawl and report the outcome."""

    def __init__(self) -> None:
        """Build the client, the walker, the resolver, and the downloader."""
        # The corporate proxy re-signs TLS, so this crawl keeps its proven
        # unverified behavior through the explicit insecure TLS mode.
        self.client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # Shared client
        self.walker = JvdCatalogWalker(self.client)  # Catalog navigation
        self.resolver = JvdPdfResolver(self.client)  # PDF URL resolution
        self.downloader = JvdDownloader(self.client, OUT_DIR)  # File writer

    def run(self) -> None:
        """Crawl every solution and download every JVD PDF."""
        logging.info("Starting the validated designs crawl")  # Log the start
        solutions = self.walker.list_solutions()  # Level one of the catalog
        entries = self._collect_entries(solutions)  # Level two of the catalog
        logging.info("Collected %d unique JVD entries", len(entries))  # Report
        self._download_entries(entries)  # Resolve and download each entry

    def _collect_entries(self, solutions: list[dict]) -> dict[str, dict]:
        """Return every unique JVD entry keyed by its asset URL."""
        entries: dict[str, dict] = {}  # Deduplicate across overlapping solutions
        for solution in solutions:  # Visit each solution page in turn
            logging.info("Scanning solution %s", solution["name"])  # Log intent
            for entry in self.walker.list_jvds(solution["code"]):  # Walk entries
                asset_url = entry.get("assetUrl")  # Detail page of the JVD
                if not asset_url:  # Skip an entry with no destination
                    continue
                record = dict(entry)  # Copy so the source list stays unchanged
                record["solution"] = solution["name"]  # Track the owning category
                entries.setdefault(asset_url, record)  # Keep the first occurrence
            time.sleep(DELAY_SECONDS)  # Pause between solution pages
        return entries

    def _download_entries(self, entries: dict[str, dict]) -> None:
        """Resolve and download every collected entry."""
        saved = 0  # Count of files written or already present
        failed: list[str] = []  # Titles that could not be downloaded
        for asset_url, entry in entries.items():  # Process one entry at a time
            title = entry.get("title", asset_url)  # Human readable label
            pdf_url = self.resolver.resolve(asset_url)  # Find the PDF address
            if pdf_url is None:  # No PDF exists for this entry
                logging.warning("No PDF found for %s", title)  # Record the miss
                failed.append(title)  # Track it for the summary
                time.sleep(DELAY_SECONDS)  # Pause before the next entry
                continue
            if self.downloader.download(pdf_url):  # Attempt the transfer
                saved += 1  # Count the success
            else:
                failed.append(title)  # Track the failure
            time.sleep(DELAY_SECONDS)  # Pause between downloads
        logging.info("Downloaded or confirmed %d PDF files", saved)  # Summary
        for title in failed:  # List every entry without a PDF
            logging.info("No PDF: %s", title)  # Report each miss


if __name__ == "__main__":
    JvdCrawlRunner().run()  # Execute the crawl when run as a script
