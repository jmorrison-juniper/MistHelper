"""Shared fixtures and a mocked HTTP client for the harvester tests.

The fake client serves recorded fixture text, PDF payloads, and sizes from an
in-memory map. It logs every request so a test can assert the pacing and the
fault tolerance. No test performs a live network call.
"""

from __future__ import annotations

import urllib.error
from pathlib import Path

import pytest

# The fixtures directory sits beside this conftest file.
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class FakeCatalogClient:
    """Serve recorded fixture responses and log every request."""

    def __init__(
        self,
        texts: dict[str, str] | None = None,
        payloads: dict[str, bytes] | None = None,
        sizes: dict[str, int] | None = None,
        fail_urls: tuple[str, ...] = (),
    ) -> None:
        """Store the scripted responses and start an empty request log."""
        self.texts = texts or {}  # URL to page or script text.
        self.payloads = payloads or {}  # URL to PDF bytes.
        self.sizes = sizes or {}  # URL to content length.
        self.fail_urls = set(fail_urls)  # URLs that raise a failure.
        self.requests: list[str] = []  # Every requested URL, in order.

    def fetch_text(self, url: str) -> str:
        """Return the scripted text for one URL or raise a failure."""
        self.requests.append(url)  # Record the request for the assertions.
        if url in self.fail_urls:  # The URL is scripted to fail.
            raise urllib.error.HTTPError(url, 404, "not found", {}, None)  # A 404 failure.
        if url in self.texts:  # The URL has scripted text.
            return self.texts[url]  # Return the recorded fixture text.
        raise urllib.error.URLError(f"no text fixture for {url}")  # Unmapped URL.

    def fetch_bytes(self, url: str) -> bytes:
        """Return the scripted PDF bytes for one URL or raise a failure."""
        self.requests.append(url)  # Record the request for the assertions.
        if url in self.fail_urls:  # The URL is scripted to fail.
            raise urllib.error.URLError(f"download failed for {url}")  # A network failure.
        if url in self.payloads:  # The URL has scripted bytes.
            return self.payloads[url]  # Return the recorded PDF payload.
        raise urllib.error.URLError(f"no payload fixture for {url}")  # Unmapped URL.

    def fetch_size(self, url: str) -> int | None:
        """Return the scripted content length for one URL, or None."""
        return self.sizes.get(url)  # None means the size is unknown.


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the recorded fixtures directory."""
    return FIXTURES  # Every test reads fixtures from here.


def read_fixture(name: str) -> str:
    """Return the text of one fixture file."""
    return (FIXTURES / name).read_text(encoding="utf-8")  # Recorded fixture text.


def read_fixture_bytes(name: str) -> bytes:
    """Return the bytes of one fixture file."""
    return (FIXTURES / name).read_bytes()  # Recorded fixture bytes.
