"""Find a stored Juniper PDF by content, so one document keeps one file (issue #2977).

The path allocator compares only the names in one category folder. The same
document under a different name or category was therefore written again. This
index compares the SHA256 digest of the bytes across the whole corpus folder.
It reads the folder and never changes it.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import hashlib  # Compute the SHA256 digest that identifies a document.
import logging  # Trace each index build and each match for observability.
from collections import defaultdict  # Group stored files by byte size.
from pathlib import Path  # Build every path in a portable way.

_LOGGER = logging.getLogger(__name__)  # Module logger for the content index.

_READ_BLOCK = 1024 * 1024  # Hash a stored file one megabyte at a time.


class CorpusContentIndex:
    """Map the SHA256 digest of each stored PDF to one canonical path."""

    def __init__(self, root: Path) -> None:
        """Store the corpus root. The first lookup scans it."""
        self._root = root  # Folder that holds every category folder.
        self._by_size: dict[int, list[Path]] | None = None  # Stored files grouped by size.
        self._by_digest: dict[str, Path] = {}  # Canonical path of each known digest.
        self._hashed: set[Path] = set()  # Files whose digest the index already holds.

    def find(self, payload: bytes) -> Path | None:
        """Return the canonical stored path with identical bytes, or None."""
        sizes = self._sizes()  # Build the size groups on first use.
        digest = hashlib.sha256(payload).hexdigest()  # Identity of the fetched bytes.
        known = self._by_digest.get(digest)  # A digest seen earlier in this run.
        if known is not None and not known.exists():  # Reclassification may have moved the file.
            self._refresh_size(len(payload))  # Find its new path among equal-size files.
            known = self._by_digest.get(digest)  # Read the refreshed canonical path.
        if known is not None and known.exists():  # The canonical file is still present.
            return known  # Reuse it, so no second file is written.
        for path in sizes.get(len(payload), []):  # Only equal-size files can match.
            if path in self._hashed or not path.exists():  # Skip a hashed or removed file.
                continue  # Nothing to learn from this path.
            self._remember(path, self._digest_file(path))  # Record its digest once.
        known = self._by_digest.get(digest)  # Look again after hashing the candidates.
        if known is not None and known.exists():  # A candidate matched.
            _LOGGER.debug("Found identical content at %s", known.name)  # Trace the match.
            return known  # The first sorted path is the canonical document.
        return None  # No stored file holds these bytes.

    def _refresh_size(self, size: int) -> None:
        """Refresh one size group after its canonical path disappears."""
        sizes = self._sizes()  # Keep the current index mapping.
        previous_paths = set(sizes.get(size, []))  # Track paths that may have moved.
        _LOGGER.info("Refreshing stored PDFs of size %d under %s", size, self._root)  # Before scan.
        for path in previous_paths:  # Remove stale hash state for this size group.
            self._hashed.discard(path)  # Allow each current path to be checked again.
        self._by_digest = {  # Remove cached matches whose path no longer exists.
            digest: path  # Preserve the cached content identity.
            for digest, path in self._by_digest.items()  # Inspect every cached match.
            if path not in previous_paths or path.exists()  # Keep other and live paths.
        }
        current_paths = [  # Collect current candidates in stable order.
            path  # Preserve the current file path.
            for path in sorted(self._root.rglob("*.pdf"))  # Keep canonical selection repeatable.
            if path.is_file() and path.stat().st_size == size  # Exclude other sizes and nonfiles.
        ]
        sizes[size] = current_paths  # Replace the stale size group with current paths.
        for path in current_paths:  # Refresh each candidate digest.
            self._remember(path, self._digest_file(path))  # Restore valid canonical matches.
        _LOGGER.debug("Refreshed %d PDF candidates of size %d", len(current_paths), size)  # After scan.

    def register(self, path: Path, payload: bytes) -> None:
        """Record a newly written file as the canonical copy of its bytes."""
        self._sizes().setdefault(len(payload), []).append(path)  # Keep the size group current.
        self._remember(path, hashlib.sha256(payload).hexdigest())  # Record its digest.

    def _remember(self, path: Path, digest: str) -> None:
        """Record a digest and keep the first path as the canonical one."""
        self._hashed.add(path)  # Never hash this file again.
        self._by_digest.setdefault(digest, path)  # The first path stays canonical.

    def _sizes(self) -> dict[int, list[Path]]:
        """Return the stored PDF files grouped by size, scanning once."""
        if self._by_size is None:  # The first call builds the groups.
            _LOGGER.info("Indexing stored PDF files under %s", self._root)  # Before the scan.
            groups: dict[int, list[Path]] = defaultdict(list)  # Size to paths.
            for path in sorted(self._root.rglob("*.pdf")):  # Stable order picks the canonical path.
                if path.is_file() and path.stat().st_size > 0:  # Skip empty files.
                    groups[path.stat().st_size].append(path)  # Group by byte size.
            self._by_size = groups  # Keep the groups for later lookups.
            _LOGGER.debug("Indexed %d size groups", len(groups))  # After the scan.
        return self._by_size  # The groups for this run.

    @staticmethod
    def _digest_file(path: Path) -> str:
        """Return the SHA256 digest of a file, read in bounded blocks."""
        reader = hashlib.sha256()  # Accumulate the digest over the blocks.
        with path.open("rb") as handle:  # Read the raw bytes.
            for block in iter(lambda: handle.read(_READ_BLOCK), b""):  # Bounded reads.
                reader.update(block)  # Fold each block into the digest.
        return reader.hexdigest()  # The identity of the stored document.
