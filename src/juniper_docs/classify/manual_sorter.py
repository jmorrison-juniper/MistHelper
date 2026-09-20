"""Sort the uncategorized documents by an explicit, hand-written rule set.

The content scorer reads the words inside a PDF, so it guesses when a document
uses common vocabulary. This module decides from two facts that carry no doubt:
the source URL path and the file name. A path segment such as ``day-one-books``
names the document series, and a file name such as
``srx1400-letter-of-volatility.pdf`` names the document type.

The rules run in a fixed order, and the first match wins. The order puts the
most specific rule first, so a letter of volatility never lands in the hardware
folder. A document that matches no rule keeps its place, because a wrong folder
is worse than an honest unsorted folder.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

_LOGGER = logging.getLogger(__name__)  # Module logger for the sort pass.

# Each rule is a target folder and a pattern. The pattern reads the source URL
# and the file name joined by one space, so a rule can match either one.
_RULES: tuple[tuple[str, str], ...] = (
    ("letters-of-volatility", r"letter[-_ ]of[-_ ]volatility"),
    ("day-one-books", r"/day-one-books/|/jnbooks/|(?:^|\s)DO_|(?:^|\s)DayOne"),
    (
        "release-notes",
        r"release[-_ ]note|rel[-_ ]notes|relnote|readme|revision[-_ ]history|[-_]rn\.pdf",
    ),
    (
        "quick-starts",
        r"quick[-_ ]?start|[-_]qsg\b|getting[-_ ]started|[-_]gsg\b|how-to-set-?up" r"|day[-_ ]one[-_ ]plus",
    ),
    (
        "security-and-compliance",
        r"fips|common[-_ ]criteria|140sp|security[-_ ]policy|hardening|idp[-_ ]detector",
    ),
    (
        "api",
        r"/api/|[-_ ]api[-_ ]|\bapi-ref|rest[-_ ]api|netconf|openconfig" r"|xml[-_ ]protocol|\bsdk\b",
    ),
    (
        "cli-reference",
        r"cli[-_ ]|[-_ ]cli\b|command[-_ ]reference|[-_ ]commands?\b|show-commands"
        r"|statements?[-_ ]|[-_ ]messages?[-_ ]|/operational/",
    ),
    ("administration-guides", r"admin[-_ ]guide|administration|[-_ ]admin\b"),
    ("migration", r"migration|migrat|transition"),
    ("installation-guides", r"install|deploy|upgrade|hardware[-_ ]guide|/download/"),
    (
        "design",
        r"design|architecture|validated|/jvd|solution[-_ ]brief|reference[-_ ]arch" r"|[-_ ]DG\b|/concept/",
    ),
    (
        "hardware-guides",
        r"/hardware/|/product/|pic-index|chassis|[-_ ]fru[-_ ]|power[-_ ]supply" r"|optic|pluggable|transceiver",
    ),
    ("junos-feature-guides", r"/software/junos/|/release-independent/"),
    (
        "configuration-guides",
        r"config|feature[-_ ]guide|user[-_ ]guide|[-_ ]ug\b|cookbook|[-_ ]CG[-_ ]"
        r"|/verify/|/general/|policy|monitor",
    ),
    ("software-guides", r"/software/|/internal/"),
)

_COMPILED: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (folder, re.compile(pattern, re.IGNORECASE)) for folder, pattern in _RULES
)  # Compile once, because the pass reads hundreds of documents.

UNSORTED = "unsorted"  # The honest folder for a document that matches no rule.


@dataclass
class SortStats:
    """Hold the counts that the sort pass reports."""

    inspected: int = 0  # Documents read from the uncategorized bucket.
    moved: int = 0  # Documents placed in a rule folder.
    unsorted: int = 0  # Documents that matched no rule and kept their place.
    missing: int = 0  # Rows whose file is absent from the disk.


class ManualDocumentSorter:
    """Place each uncategorized document by an explicit rule, not by a guess."""

    def __init__(self, output_dir: Path, apply_changes: bool = False) -> None:
        """Store the corpus root and whether the pass may write.

        Args:
            output_dir: The corpus root that holds the category folders.
            apply_changes: True moves the files. False reports the plan only.
        """
        self.output_dir = output_dir  # The corpus root that holds every folder.
        self.apply_changes = apply_changes  # A dry run is the safe default.
        self.stats = SortStats()  # The counts that the caller reports.

    def decide(self, source_url: str, file_name: str) -> str:
        """Return the target folder for one document, or the unsorted folder."""
        subject = f"{source_url} {file_name}"  # One rule may match either part.
        for folder, pattern in _COMPILED:  # The first match wins, so order matters.
            if pattern.search(subject):  # This rule recognizes the document.
                return folder  # Place the document in this category folder.
        return UNSORTED  # No rule matched, so the document stays honestly unsorted.

    def run(self, database: Path) -> SortStats:
        """Sort every uncategorized document and return the counts."""
        _LOGGER.info("Sorting the uncategorized documents under %s", self.output_dir)
        rows = self._read_rows(database)  # Every uncategorized classified row.
        for source_url, local_path in rows:  # Decide and place one document.
            self._place_one(source_url, Path(local_path))  # Apply the rule.
        _LOGGER.debug("Sorted %d documents", self.stats.inspected)  # Result count.
        return self.stats  # The caller prints the summary.

    @staticmethod
    def _read_rows(database: Path) -> list[tuple[str, str]]:
        """Return the source URL and the path of every uncategorized document."""
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)  # Read only.
        try:
            found = connection.execute(
                "SELECT root_url, local_path FROM documents "
                "WHERE stage = 'classified' AND local_path IS NOT NULL "
                "AND category = 'uncategorized'"
            ).fetchall()  # Only the uncategorized bucket needs a rule decision.
        finally:
            connection.close()  # Never hold the database open during the moves.
        return [(str(row[0]), str(row[1])) for row in found]  # Plain string pairs.

    def _place_one(self, source_url: str, source: Path) -> None:
        """Move one document into its rule folder, or count it as unsorted."""
        self.stats.inspected += 1  # Count every document the pass reads.
        if not source.exists():  # A sibling row may have moved the file already.
            self.stats.missing += 1  # Count it and continue with the next row.
            return  # A missing file needs no move.
        folder = self.decide(source_url, source.name)  # The explicit rule decision.
        if folder == UNSORTED:  # The rules recognize nothing in this document.
            self.stats.unsorted += 1  # Report it rather than guess a folder.
            return  # Leave the file where it is.
        self._move(source, self.output_dir / folder)  # Place it in the rule folder.

    def _move(self, source: Path, target_dir: Path) -> None:
        """Move one file into the target folder without overwriting a file."""
        if not self.apply_changes:  # A dry run reports the plan and writes nothing.
            self.stats.moved += 1  # Count the move the real pass would make.
            return  # Never touch the disk during a dry run.
        target_dir.mkdir(parents=True, exist_ok=True)  # Ensure the target folder.
        target = self._free_name(target_dir, source)  # Never replace a real file.
        source.replace(target)  # Move the file, which is atomic on one volume.
        self.stats.moved += 1  # Count the completed move.

    @staticmethod
    def _free_name(target_dir: Path, source: Path) -> Path:
        """Return a free path in the target folder, so no file is ever replaced."""
        target = target_dir / source.name  # The preferred name keeps the original.
        index = 2  # The first duplicate takes the suffix 2.
        while target.exists():  # Another document already holds this name.
            target = target_dir / f"{source.stem}-{index}{source.suffix}"  # Try next.
            index += 1  # Keep counting until the name is free.
        return target  # A free path, so the move destroys nothing.
