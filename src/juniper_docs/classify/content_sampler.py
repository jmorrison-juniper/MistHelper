"""Read a bounded, in-memory text sample from one downloaded PDF.

The sampler reads the title page, the table-of-contents pages, and the first
few body pages, up to a fixed page cap. It returns the text as one local string
and adds no network load. When the library is absent, or the PDF holds no
readable text, the sampler returns an empty string so the scorer assigns the
fallback label (FR-022, FR-025, FR-026).

The returned string is held only in memory. No layer writes it to disk, to the
store, or to the manifest, so the privacy invariant holds (FR-024, SC-005).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import importlib  # Import pdfplumber by name so the dependency stays optional.
import logging  # Trace each sample read for observability.
from pathlib import Path  # Accept the PDF path in a portable way.
from typing import Any  # Type the pdfplumber module, which ships no type stubs.

_LOGGER = logging.getLogger(__name__)  # Module logger for the content sampler.

DEFAULT_SAMPLE_PAGES = 8  # The default page cap for the bounded text sample.


class ContentSampler:
    """Read a bounded text sample from one PDF and hold it only in memory."""

    def __init__(self, max_sample_pages: int = DEFAULT_SAMPLE_PAGES) -> None:
        """Store the page cap for the bounded sample."""
        self.max_sample_pages = max_sample_pages  # Read at most this many pages.

    def sample(self, pdf_path: Path) -> str:
        """Return the bounded text sample, or an empty string on any failure."""
        _LOGGER.info("Sampling up to %d pages from %s", self.max_sample_pages, pdf_path)
        module = self._pdfplumber()  # Import the optional PDF library.
        if module is None:  # The library is not installed.
            return ""  # An empty sample yields the fallback label.
        try:
            text = self._read(module, pdf_path)  # Read the bounded page sample.
        except Exception as error:  # Any PDF error yields the fallback label (FR-025).
            _LOGGER.warning("Cannot sample %s: %s", pdf_path, error)  # Record the miss.
            return ""  # An unreadable PDF yields the fallback label (FR-025).
        _LOGGER.debug("Sampled %d characters from %s", len(text), pdf_path)  # Result size.
        return text  # The scorer reads this string and then lets it go out of scope.

    def _read(self, module: Any, pdf_path: Path) -> str:
        """Return the joined text of the first pages up to the page cap."""
        parts: list[str] = []  # Accumulate the text of each sampled page.
        with module.open(str(pdf_path)) as pdf:  # Open the PDF for a bounded read.
            for page in pdf.pages[: self.max_sample_pages]:  # Read up to the page cap.
                parts.append(page.extract_text() or "")  # Add this page's text, if any.
        return "\n".join(parts)  # The joined sample stays in this local string.

    @staticmethod
    def _pdfplumber() -> Any:
        """Return the pdfplumber module, or None when it is not installed."""
        try:
            return importlib.import_module("pdfplumber")  # Load the PDF library by name.
        except ImportError:  # The optional library is absent.
            _LOGGER.warning("pdfplumber is not installed; content sampling is disabled")
            return None  # A missing library disables sampling and yields the fallback.
