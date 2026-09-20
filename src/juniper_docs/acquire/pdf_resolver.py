"""Resolve the companion PDF URL for one Juniper document page.

This class is promoted from ``scripts/crawl_jvd.py`` with its behavior intact.
It reads the index page first and the sibling ``__toc.js`` script second, which
keeps the proven resolution order. The base origin now comes from ``HttpConfig``.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each resolution step for observability.
import re  # Scan the markup and the script for a PDF path.
import urllib.error  # Classify a URL error or an HTTP error during a read.
from urllib.parse import urljoin  # Resolve a relative PDF reference, including a parent path.

from src.juniper_docs.acquire.catalog_client import JvdCatalogClient, is_transient_error  # Client.
from src.juniper_docs.acquire.http_config import HttpConfig  # Base origin for absolute URLs.
from src.juniper_docs.models import PdfCandidate, ResolveOutcome  # Candidate and outcome types.

_LOGGER = logging.getLogger(__name__)  # Module logger for every resolution.

MAX_WALKUP_LEVELS = 2  # How many parent directories to try when a root does not serve.


class JvdPdfResolver:
    """Resolve the PDF download URL for one JVD detail page."""

    def __init__(self, client: JvdCatalogClient) -> None:
        """Store the shared HTTP client for every page and script read."""
        self.client = client  # Reuse one client for every request.

    def resolve(self, asset_url: str) -> str | None:
        """Return the absolute PDF URL for one JVD asset page."""
        if asset_url.lower().endswith(".pdf"):  # The entry already names a PDF file.
            return asset_url if asset_url.startswith("http") else HttpConfig.SITE + asset_url
        page_url = asset_url if asset_url.startswith("http") else HttpConfig.SITE + asset_url
        _LOGGER.info("Resolving the PDF link for %s", page_url)  # Log the intent.
        try:
            html = self.client.fetch_text(page_url)  # Read the detail page markup.
        except (urllib.error.URLError, urllib.error.HTTPError) as error:  # A read may fail.
            _LOGGER.error("Cannot open %s: %s", page_url, error)  # Record the failure.
            return None  # A missing page yields no PDF for this document.
        direct = self._find_pdf_reference(html)  # Try the page markup first.
        if direct:  # The markup already names the PDF file.
            return self._absolutize(direct, page_url)  # Build the absolute URL.
        return self._resolve_from_toc(page_url)  # Fall back to the TOC script.

    def _resolve_from_toc(self, page_url: str) -> str | None:
        """Return the PDF URL named by the sibling ``__toc.js`` script."""
        base = page_url.rsplit("/", 1)[0]  # Directory that holds the document.
        toc_url = f"{base}/__toc.js"  # The site ships one TOC per document.
        _LOGGER.debug("Reading the TOC script at %s", toc_url)  # Trace the read.
        try:
            toc = self.client.fetch_text(toc_url)  # Download the TOC payload.
        except (urllib.error.URLError, urllib.error.HTTPError) as error:  # A read may fail.
            _LOGGER.warning("No TOC at %s: %s", toc_url, error)  # Record the miss.
            return None  # A missing TOC yields no PDF for this document.
        reference = self._find_pdf_reference(toc)  # Search the TOC for a PDF path.
        if reference is None:  # The TOC names no PDF file.
            _LOGGER.warning("The TOC at %s names no PDF", toc_url)  # Record the miss.
            return None  # No PDF path means no companion PDF.
        return self._absolutize(reference, page_url)  # Build the absolute URL.

    @staticmethod
    def _find_pdf_reference(text: str) -> str | None:
        """Return the first PDF path found in one block of text."""
        match = re.search(r'["\'(]([^"\'()\s]+\.pdf)', text)  # Scan for a PDF path.
        return match.group(1) if match else None  # Return the captured path or nothing.

    @staticmethod
    def _absolutize(reference: str, page_url: str) -> str:
        """Return an absolute URL for a possibly relative PDF reference."""
        if reference.startswith("http"):  # The reference is already absolute.
            return reference  # Nothing to join.
        if reference.startswith("/"):  # The reference is origin relative.
            return HttpConfig.SITE + reference  # Join the origin and the path.
        base = page_url.rsplit("/", 1)[0]  # Directory of the detail page.
        return f"{base}/{reference}"  # Join the directory and the file name.


class CompanionPdfResolver(JvdPdfResolver):
    """Resolve one companion PDF for a document root by the fixed order."""

    def resolve_companion(self, root_url: str) -> tuple[str | None, list[PdfCandidate], ResolveOutcome, str]:
        """Return the chosen PDF, the candidates, the outcome, and a reason."""
        _LOGGER.info("Resolving the companion PDF for %s", root_url)  # Log the intent.
        refs, reached, last_error = self._collect_with_walkup(root_url)  # Walk up on error.
        if refs:  # A live page named at least one PDF.
            return self._resolved(refs, root_url)  # Select and return the companion PDF.
        if reached:  # A live page was reached, but it named no PDF.
            _LOGGER.info("No companion PDF for %s", root_url)  # Record the clean no-PDF.
            return None, [], ResolveOutcome.NO_PDF, "no companion PDF found"  # Clean outcome.
        reason = _failure_reason(last_error)  # A permanent or transient failure reason.
        _LOGGER.warning("Resolution failed for %s: %s", root_url, reason)  # Record the failure.
        return None, [], ResolveOutcome.FAILED, reason  # A real resolution failure.

    def _resolved(self, refs: list[str], root_url: str) -> tuple[str | None, list[PdfCandidate], ResolveOutcome, str]:
        """Return the chosen PDF, the candidates, and the resolved outcome."""
        chosen, rule = self._select(refs, root_url)  # Apply the fixed selection order.
        candidates = [
            PdfCandidate(url, url == chosen, rule if url == chosen else "rejected") for url in refs
        ]  # One candidate record per reference, with its selection or rejection reason.
        _LOGGER.debug("Chose %s for %s by %s", chosen, root_url, rule)  # Result and reason.
        return chosen, candidates, ResolveOutcome.RESOLVED, rule  # The resolved companion PDF.

    def _collect_with_walkup(self, root_url: str) -> tuple[list[str], bool, BaseException | None]:
        """Return the PDF references, walking up a parent when a root does not serve."""
        current = root_url  # Start at the composed document root.
        last_error: BaseException | None = None  # The last fetch error for the reason.
        for _level in range(MAX_WALKUP_LEVELS + 1):  # Try the root, then bounded parents.
            refs, reached, error = self._references_at(current)  # Read this level.
            if reached:  # A live page answered at this level.
                return refs, True, None  # Return its references, which may be empty.
            last_error = error or last_error  # Keep the fetch error for the reason.
            parent = self._parent_dir(current)  # Move up one directory level.
            if parent == current:  # The origin cannot go up any further.
                break  # Stop the walk-up at the top of the path.
            current = parent  # Try the parent directory next.
        return [], False, last_error  # No live page was reached at any level.

    def _references_at(self, url: str) -> tuple[list[str], bool, BaseException | None]:
        """Return the PDF references from the index page, then the TOC, at one level."""
        index_refs, index_reached, index_error = self._fetch_refs(url)  # Read the index page.
        if index_refs:  # The index page named a PDF.
            return index_refs, True, None  # Use the index references.
        toc_refs, toc_reached, _toc_error = self._fetch_refs(url.rstrip("/") + "/__toc.js")
        reached = index_reached or toc_reached  # A 200 from either page is a live page.
        return toc_refs, reached, None if reached else index_error  # TOC references or the error.

    def _fetch_refs(self, url: str) -> tuple[list[str], bool, BaseException | None]:
        """Return the absolute PDF references at one URL, and whether it answered."""
        try:
            text = self.client.fetch_text(url)  # Read the page or the script.
        except (urllib.error.URLError, OSError) as error:  # A network or HTTP error.
            _LOGGER.debug("No references from %s: %s", url, error)  # Trace the miss.
            return [], False, error  # A failed fetch reached no live page.
        refs = [urljoin(url, ref) for ref in self._find_all_pdf_references(text)]  # Absolute.
        return list(dict.fromkeys(refs)), True, None  # A live page, with its references.

    @staticmethod
    def _parent_dir(url: str) -> str:
        """Return the parent directory URL of one document root."""
        parent = url.rstrip("/").rsplit("/", 1)[0]  # Drop the last path segment.
        return parent + "/"  # Keep the trailing slash on the parent directory.

    def _select(self, refs: list[str], root_url: str) -> tuple[str, str]:
        """Return the chosen PDF URL and the rule name by the fixed order."""
        name_choice = self._name_choice(refs, root_url)  # First, the best name match.
        if name_choice is not None:  # A single best name match wins outright.
            return name_choice, "name-match"  # Prefer the name that matches the slug.
        same_folder = [url for url in refs if self._same_folder(url, root_url)]  # Second.
        if same_folder:  # A same-folder reference wins next.
            return same_folder[0], "same-folder-first"  # Prefer the first same-folder PDF.
        sized = [(self.client.fetch_size(url) or 0, url) for url in refs]  # Third, probe size.
        largest = max(sized, key=lambda pair: pair[0])  # The whole document is the largest.
        return largest[1], "largest"  # Prefer the largest file as the final tiebreak.

    def _name_choice(self, refs: list[str], root_url: str) -> str | None:
        """Return the single best name match, or None when it is ambiguous."""
        target = self._root_name(root_url)  # The last path segment of the document root.
        scored = [(self._name_score(self._filename(url), target), url) for url in refs]  # Score.
        best = max(score for score, _ in scored)  # The highest name-match score.
        winners = [url for score, url in scored if score == best]  # Every top scorer.
        return winners[0] if best > 0 and len(winners) == 1 else None  # One clear winner.

    @staticmethod
    def _find_all_pdf_references(text: str) -> list[str]:
        """Return every PDF path found in one block of text, in read order."""
        return re.findall(r'["\'(]([^"\'()\s]+\.pdf)', text)  # Scan for each PDF path.

    @staticmethod
    def _root_name(root_url: str) -> str:
        """Return the last path segment of one document root URL."""
        return root_url.rstrip("/").rsplit("/", 1)[-1]  # The document name segment.

    @staticmethod
    def _filename(url: str) -> str:
        """Return the file name of one PDF URL without any query string."""
        return url.rsplit("/", 1)[-1].split("?")[0]  # The bare file name.

    @staticmethod
    def _same_folder(url: str, root_url: str) -> bool:
        """Return True when a PDF URL sits in the same folder as the index page."""
        root_dir = root_url if root_url.endswith("/") else root_url.rsplit("/", 1)[0] + "/"
        url_dir = url.rsplit("/", 1)[0] + "/"  # The folder that holds the candidate.
        return url_dir == root_dir  # Same folder means the folders match exactly.

    @staticmethod
    def _name_score(filename: str, target: str) -> int:
        """Return a name-match score between a PDF file name and the root name."""
        stem = filename.removesuffix(".pdf").lower()  # The file name without the suffix.
        name = target.lower()  # The document root name in one case.
        if stem == name:  # An exact match is the strongest signal.
            return 3  # The whole-document PDF often matches the slug exactly.
        if name in stem or stem in name:  # A contained match is the next strongest.
            return 2  # A prefixed or suffixed name still matches the slug.
        return 1 if set(stem.split("-")) & set(name.split("-")) else 0  # Shared tokens.


def _failure_reason(error: BaseException | None) -> str:
    """Return a permanent or transient failure reason for a resolution error."""
    if error is None:  # No error was captured during the walk-up.
        return "permanent: resolution failed"  # A generic permanent failure.
    prefix = "transient" if is_transient_error(error) else "permanent"  # Classify the error.
    return f"{prefix}: {error}"  # The reason names the kind and the error text.
