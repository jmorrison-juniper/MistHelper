"""Choose a collision-safe local path for every resolved Juniper PDF.

Two remote PDF files that share a file name once landed on one local path, and
the second write destroyed the first (issue #2738). This module keeps every
distinct remote document on its own local path. It reuses the single stored file
when the same resolved URL returns again, so a resume never duplicates a file. It
reuses the single stored file when a different URL holds identical bytes, so an
identical document is stored one time. It disambiguates the name when a different
URL holds different bytes, so no write destroys an earlier file.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import hashlib  # Derive a stable name hash and confirm identical bytes.
import logging  # Trace each reuse and each disambiguation for observability.
from collections.abc import Callable, Iterator  # Type the lookup and the name stream.
from pathlib import Path  # Build every candidate path in a portable way.

_LOGGER = logging.getLogger(__name__)  # Module logger for the path allocator.

# A lookup that returns the resolved PDF URL that owns a stored path, or None.
OwnerLookup = Callable[[str], str | None]

_HASH_WIDTH = 10  # Hex characters of the URL hash that disambiguate a file name.
_MAX_VARIANTS = 1000  # A generous bound on the disambiguated names for one base name.
_READ_BLOCK = 1024 * 1024  # Read one megabyte at a time when hashing a stored file.


class PdfPathAllocator:
    """Allocate a unique local path for one resolved PDF under a collision policy."""

    def __init__(self, owner_lookup: OwnerLookup) -> None:
        """Store the callback that reports the owning URL of a stored path."""
        self._owner_of = owner_lookup  # Report the URL that produced a stored file.

    def existing_for_url(self, target: Path, url: str) -> Path | None:
        """Return a stored file that this exact URL already produced, or None."""
        _LOGGER.debug("Checking a same-URL stored file for %s", url)  # Trace the resume check.
        for candidate in self._variants(target, url):  # Walk the deterministic names in order.
            if not self._occupied(candidate):  # The first free name ends the search.
                return None  # This URL produced no file yet, so the caller must fetch.
            if self._owner_of(str(candidate)) == url:  # The same URL already owns this file.
                return candidate  # Reuse the stored file with no fetch, for a resume.
        return None  # Every checked name belongs to another URL, so the caller must fetch.

    def plan_bytes(self, target: Path, url: str, payload: bytes) -> tuple[Path, bool]:
        """Return the final path for fetched bytes and whether the caller must write."""
        _LOGGER.debug("Planning a path for %d fetched bytes", len(payload))  # Trace the plan.
        return self._place_path(target, url, len(payload), lambda: self._digest_bytes(payload))

    def plan_file(self, target: Path, url: str, source: Path) -> tuple[Path, bool]:
        """Return the final path for a source file and whether the caller must move it."""
        size = source.stat().st_size  # The byte count of the file that waits to move.
        _LOGGER.debug("Planning a path for the %d byte file %s", size, source.name)  # Trace.
        return self._place_path(target, url, size, lambda: self._digest_file(source))

    def _place_path(self, target: Path, url: str, size: int, digest: Callable[[], str]) -> tuple[Path, bool]:
        """Return the first free, same-URL, or identical name, and the write flag."""
        for candidate in self._variants(target, url):  # Walk the deterministic names in order.
            if not self._occupied(candidate):  # A free name receives the new file.
                return candidate, True  # The caller writes or moves the file to this path.
            if self._owner_of(str(candidate)) == url:  # The same URL already owns this file.
                return candidate, False  # Reuse the stored file, so the caller skips the write.
            if self._same_content(candidate, size, digest):  # A different URL, identical bytes.
                return candidate, False  # Store the identical document one time only.
        raise RuntimeError(f"no free variant name for {target}")  # Unreachable in practice.

    def _variants(self, target: Path, url: str) -> Iterator[Path]:
        """Yield the clean name, then the hash name, then indexed hash names."""
        yield target  # The first document to claim the base name keeps the clean name.
        digest = self._short_hash(url)  # A short, stable hash of the resolved PDF URL.
        yield self._suffixed(target, digest)  # The deterministic disambiguated name.
        for index in range(2, _MAX_VARIANTS):  # A bounded guard against a rare hash clash.
            yield self._suffixed(target, f"{digest}-{index}")  # An indexed disambiguated name.

    def _same_content(self, path: Path, size: int, digest: Callable[[], str]) -> bool:
        """Return True when a stored file matches the new size and hash."""
        if path.stat().st_size != size:  # A cheap size check rejects most collisions first.
            return False  # Two different sizes prove two different documents.
        matched = self._digest_file(path) == digest()  # A hash confirms identical bytes.
        if matched:  # The two documents hold the same bytes.
            _LOGGER.debug("Found identical bytes already stored at %s", path.name)  # Trace.
        return matched  # A match lets the caller store the document one time only.

    @staticmethod
    def _occupied(path: Path) -> bool:
        """Return True when a path holds a non-empty file."""
        return path.exists() and path.stat().st_size > 0  # A zero-byte file is not a real one.

    @staticmethod
    def _suffixed(target: Path, discriminator: str) -> Path:
        """Return the target name with a discriminator inserted before the suffix."""
        renamed = f"{target.stem}-{discriminator}{target.suffix}"  # The name-<disc>.pdf form.
        return target.with_name(renamed)  # A sibling path in the same folder.

    @staticmethod
    def _short_hash(url: str) -> str:
        """Return a short, stable hex hash of the resolved URL."""
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()  # A stable hash of the URL.
        return digest[:_HASH_WIDTH]  # A short prefix keeps the file name readable.

    @staticmethod
    def _digest_bytes(payload: bytes) -> str:
        """Return the SHA-256 hex digest of a byte payload."""
        return hashlib.sha256(payload).hexdigest()  # A full hash confirms byte equality.

    @staticmethod
    def _digest_file(path: Path) -> str:
        """Return the SHA-256 hex digest of a file read in bounded blocks."""
        reader = hashlib.sha256()  # Accumulate the hash over the file blocks.
        with path.open("rb") as handle:  # Read the stored file as raw bytes.
            for block in iter(lambda: handle.read(_READ_BLOCK), b""):  # Bounded one-megabyte blocks.
                reader.update(block)  # Fold each block into the running hash.
        return reader.hexdigest()  # The digest confirms identical bytes cheaply.
