"""Consolidate every Juniper PDF into one deduplicated library tree.

The corpus grew from three sources: the live crawl, the marketing sitemap, and
a local archive folder. The same document therefore appears more than once, and
a converter that walks the tree would read the same file several times.

This module keeps one copy of each document, chosen by content hash. When two
paths hold identical bytes, the module keeps the copy in the most specific
category folder, because a reader finds it there. It writes one library root,
so a later pass has a single place to look.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

_LOGGER = logging.getLogger(__name__)  # Module logger for the consolidation.

_READ_SIZE = 1 << 20  # Hash the file one megabyte at a time, so memory stays flat.

# A folder in this set holds a document that no rule could name. A copy in a
# named category always wins over a copy in one of these, because the named
# folder tells the reader what the document is.
_VAGUE_FOLDERS = frozenset({"archive-unsorted", "uncategorized", "unsorted"})


@dataclass
class ConsolidateStats:
    """Hold the counts that the consolidation reports."""

    scanned: int = 0  # Files read from every source tree.
    unique: int = 0  # Documents that reached the library.
    duplicates: int = 0  # Copies skipped because the content already exists.
    bytes_saved: int = 0  # Bytes that the skipped copies would have used.
    categories: dict[str, int] = field(default_factory=dict)  # Files per folder.


class LibraryConsolidator:
    """Build one deduplicated library tree from several PDF source trees."""

    def __init__(self, library_root: Path) -> None:
        """Store the destination root that receives one copy of each document.

        Args:
            library_root: The single folder that a later converter pass reads.
        """
        self.library_root = library_root  # The one root the converter will read.
        self.stats = ConsolidateStats()  # The counts that the caller reports.

    def run(self, sources: list[Path]) -> ConsolidateStats:
        """Copy one instance of each unique document into the library root."""
        _LOGGER.info("Consolidating %d source trees into %s", len(sources), self.library_root)
        groups = self._group_by_content(sources)  # One entry per unique document.
        self.stats.unique = len(groups)  # Every group becomes exactly one file.
        for paths in groups.values():  # Place the best copy of each document.
            self._place(self._best_copy(paths), paths)  # Copy one, count the rest.
        _LOGGER.debug("Wrote %d unique documents", self.stats.unique)  # Result count.
        return self.stats  # The caller prints the summary.

    def _group_by_content(self, sources: list[Path]) -> dict[str, list[Path]]:
        """Return every source path grouped by the hash of its bytes."""
        groups: dict[str, list[Path]] = defaultdict(list)  # Hash to its copies.
        for source in sources:  # Walk each source tree in turn.
            for path in sorted(source.rglob("*.pdf")):  # A stable order is repeatable.
                self.stats.scanned += 1  # Count every file the pass reads.
                groups[self._hash(path)].append(path)  # Identical bytes group together.
        return groups  # Each group holds one document and its duplicate copies.

    @staticmethod
    def _hash(path: Path) -> str:
        """Return the SHA-256 hash of one file, read in bounded blocks."""
        digest = hashlib.sha256()  # A content hash finds a rename and a copy alike.
        with path.open("rb") as handle:  # Read the raw bytes of the document.
            for block in iter(lambda: handle.read(_READ_SIZE), b""):  # Bounded reads.
                digest.update(block)  # Fold each block into the running hash.
        return digest.hexdigest()  # The stable identity of this document.

    @staticmethod
    def _best_copy(paths: list[Path]) -> Path:
        """Return the copy whose folder tells a reader the most."""
        return min(paths, key=lambda path: (path.parent.name in _VAGUE_FOLDERS, len(path.name)))

    def _place(self, chosen: Path, group: list[Path]) -> None:
        """Copy the chosen document into the library and count its duplicates."""
        folder = chosen.parent.name  # The category folder names the document type.
        target_dir = self.library_root / folder  # The library keeps that category.
        target_dir.mkdir(parents=True, exist_ok=True)  # Ensure the category folder.
        target = self._free_name(target_dir, chosen.name)  # Never replace a file.
        shutil.copy2(chosen, target)  # Copy with the original timestamps intact.
        self.stats.categories[folder] = self.stats.categories.get(folder, 0) + 1
        self.stats.duplicates += len(group) - 1  # Every other copy is a duplicate.
        self.stats.bytes_saved += chosen.stat().st_size * (len(group) - 1)  # Space saved.

    @staticmethod
    def _free_name(target_dir: Path, name: str) -> Path:
        """Return a free path, so one document never replaces a different one."""
        target = target_dir / name  # The preferred name keeps the original.
        stem, suffix = Path(name).stem, Path(name).suffix  # Split for a suffix loop.
        index = 2  # The first clash takes the suffix 2.
        while target.exists():  # A different document already holds this name.
            target = target_dir / f"{stem}-{index}{suffix}"  # Try the next name.
            index += 1  # Keep counting until the name is free.
        return target  # A free path, so the copy destroys nothing.
