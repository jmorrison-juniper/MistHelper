"""Select which Juniper documents to keep from the inventory.

The corpus holds many release notes for the same software line. This selector
keeps the newest release note in each train and keeps every other document. A
train is one product family and one version line.

The selector reads the product family from the document name, not from a fixed
path segment. The name is the reliable source for two reasons. Junos OS and
Junos OS Evolved share the path segment ``junos`` yet form different products.
A PDF tree can also place a locale segment where the product segment would
otherwise sit.

By default a train covers a major version and a minor version. So 23.1, 23.2,
23.3, and 23.4 each keep their own newest note. This default keeps more history
and cannot silently lose a release the operator wanted. The
``collapse_to_major`` option collapses a train to the major version only, so
major 23 keeps one note.

An X-build, such as 23.4X100, is a special branch, not a successor to the
mainstream 23.4 line. The selector gives each X-build its own train. So an
X-build never evicts a mainstream R note, and the newest D revision wins inside
the X-build train.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Log the selection outcome for observability.
import re  # Parse the product family and the version from a release-note name.
from dataclasses import dataclass  # Build the small, hashable train key.
from typing import NamedTuple  # Build the ordered, hashable version value.

from src.juniper_docs.models import InventoryRecord  # Inventory record for the corpus filter.

RELEASE_NOTE_MARKERS = ("release-note", "relnote", "release_notes")  # Slug hints.
DROP_REASON = "superseded-by-newer-train-member"  # Reason recorded for a dropped note.
_LOCALE_TOKENS = ("us", "en", "en_us")  # Locale segments the path fallback skips.

_VERSION_PATTERN = re.compile(
    r"(\d{1,2})[._-](\d{1,2})"  # Major and minor, such as 23.4.
    r"(?:[._-](\d+))?"  # Optional dotted third number, such as .1 in 3.2.1.
    r"(?:[xX](\d+))?"  # Optional X special build, such as X100.
    r"(?:[-._]?[rR](\d+))?"  # Optional R revision, such as R2, after an optional dash.
    r"(?:[-._]?[dD](\d+))?"  # Optional D revision, such as -D40, after an optional dash.
)  # One pattern parses both the Junos form and the dotted product form.
_MARKER_PATTERN = re.compile(r"release[-_]notes?|relnotes?", re.IGNORECASE)  # Note marker.
_EXTENSION_PATTERN = re.compile(r"\.(?:pdf|html?|xml|js)$", re.IGNORECASE)  # File suffix.
_SEPARATOR_PATTERN = re.compile(r"[-_. ]+")  # A run of separators between name words.

_LOGGER = logging.getLogger(__name__)  # Module logger for the selection.


class ReleaseVersion(NamedTuple):
    """One parsed release version, ordered from most to least significant."""

    major: int  # Major version, such as 23 in 23.4R2.
    minor: int  # Minor version, such as 4 in 23.4R2.
    patch: int  # Dotted third number for a product version, such as 1 in 3.2.1.
    x_build: int  # The X special-branch build, such as 100 in 23.4X100.
    r_rev: int  # The R maintenance revision, such as 2 in 23.4R2.
    d_rev: int  # The D revision, such as 40 in 23.4X100-D40.


@dataclass(frozen=True)
class ReleaseNoteKey:
    """Identify the train that one release note belongs to."""

    product: str  # Product family, such as junos or junos-evo.
    major: int  # Major version, such as 23 in 23.4R1.
    minor: int  # Minor version, such as 4 in 23.4R1, or 0 when the train collapses.
    x_build: int  # The X-build number, such as 100 in 23.4X100, or 0 for mainstream.


class ReleaseNoteSelector:
    """Keep only the newest release note in each product and version train.

    The train key names the product family, the major version, the minor
    version, and the X-build number. The minor version drops to 0 when
    ``collapse_to_major`` is True. The X-build number keeps a special branch in
    its own train, so an X-build never evicts a mainstream R note.
    """

    def __init__(self, collapse_to_major: bool = False) -> None:
        """Store whether one train covers a major version only."""
        self.collapse_to_major = collapse_to_major  # Select the train granularity.

    def is_release_note(self, root: str) -> bool:
        """Return True when one document root names a release note."""
        lowered = root.lower()  # Compare in one case only.
        return any(marker in lowered for marker in RELEASE_NOTE_MARKERS)  # Any hint.

    def read_product(self, root: str) -> str:
        """Return the product family for one release-note root.

        The method reads the family from the document name first. It removes the
        file extension, the release-note marker, and the version span, then it
        keeps the words that remain. This name-first rule keeps Junos OS apart
        from Junos OS Evolved and keeps a locale segment out of the family.
        """
        tail = root.rsplit("/", 1)[-1].lower()  # The document name in one case.
        without_extension = _EXTENSION_PATTERN.sub(" ", tail)  # Drop a known file suffix.
        without_marker = _MARKER_PATTERN.sub(" ", without_extension)  # Drop the note marker.
        without_version = _VERSION_PATTERN.sub(" ", without_marker)  # Drop the version span.
        token = _SEPARATOR_PATTERN.sub("-", without_version).strip("-")  # Join the words.
        if token:  # The name carries a product family.
            return token  # Use the name-derived family.
        parts = root.split("/")  # No family in the name, so read it from the path.
        return (parts[1] if len(parts) > 1 else parts[0]).lower()  # The family segment.

    def read_version(self, root: str) -> ReleaseVersion | None:
        """Return the parsed version for one release-note root, or None."""
        tail = root.rsplit("/", 1)[-1]  # The document name holds the version.
        match = _VERSION_PATTERN.search(tail)  # Match a Junos or a product version.
        if match is None:  # The name carries no comparable version.
            return None  # An unversioned note has no train.
        numbers = [int(group) if group else 0 for group in match.groups()]  # Fill each blank.
        return ReleaseVersion(*numbers)  # Order: major, minor, patch, x, r, d.

    def build_key(self, root: str) -> ReleaseNoteKey | None:
        """Return the train key for one release-note root, or None.

        The X-build number stays in the key, so a special branch such as
        23.4X100 forms its own train and never evicts a mainstream R note.
        """
        version = self.read_version(root)  # Parse the version from the name.
        if version is None:  # An unversioned note has no train.
            return None  # The caller keeps an unversioned note.
        minor = 0 if self.collapse_to_major else version.minor  # Collapse the minor when asked.
        product = self.read_product(root)  # The product family from the name or path.
        return ReleaseNoteKey(product, version.major, minor, version.x_build)  # The train key.

    def select(self, roots: list[str]) -> tuple[list[str], list[str]]:
        """Return the kept roots and the dropped release-note roots."""
        _LOGGER.info("Selecting release notes across %d roots", len(roots))  # Log intent.
        newest: dict[ReleaseNoteKey, tuple[ReleaseVersion, str]] = {}  # Train winners.
        unversioned: list[str] = []  # Release notes with no parsable version.
        kept: list[str] = []  # Every document that is not a release note.
        for root in roots:  # Classify each document root in turn.
            self._sort_root(root, newest, unversioned, kept)  # Route the root.
        selected, dropped = self._partition(roots, newest, unversioned, kept)  # Split.
        _LOGGER.debug("Kept %d roots, dropped %d release notes", len(selected), len(dropped))
        return selected, dropped  # Return the kept roots and the dropped roots.

    def _sort_root(
        self,
        root: str,
        newest: dict[ReleaseNoteKey, tuple[ReleaseVersion, str]],
        unversioned: list[str],
        kept: list[str],
    ) -> None:
        """Route one root to the kept, the unversioned, or the newest map."""
        if not self.is_release_note(root):  # A normal document is always kept.
            kept.append(root)  # Keep every non-release-note document.
            return  # Nothing more to do for a normal document.
        key = self.build_key(root)  # Identify the train of the release note.
        version = self.read_version(root)  # Parse the version for the comparison.
        if key is None or version is None:  # An unversioned note has no sibling.
            unversioned.append(root)  # Keep the note with no comparable version.
            return  # Nothing more to compare for an unversioned note.
        current = newest.get(key)  # Best candidate seen so far for the train.
        if current is None or version > current[0]:  # This candidate is newer.
            newest[key] = (version, root)  # Record the new train winner.

    @staticmethod
    def _partition(
        roots: list[str],
        newest: dict[ReleaseNoteKey, tuple[ReleaseVersion, str]],
        unversioned: list[str],
        kept: list[str],
    ) -> tuple[list[str], list[str]]:
        """Return the sorted kept roots and the sorted dropped roots."""
        winners = [root for _, root in newest.values()]  # Newest of each train.
        selected = kept + unversioned + winners  # Everything the run will download.
        selected_set = set(selected)  # Fast membership test for the drop pass.
        dropped = [root for root in roots if root not in selected_set]  # Lost siblings.
        return sorted(selected_set), sorted(dropped)  # Sorted kept and dropped roots.


class CorpusReleaseNoteSelector(ReleaseNoteSelector):
    """Filter inventory records, keeping the newest release note per train."""

    def filter_records(self, records: list[InventoryRecord]) -> tuple[list[InventoryRecord], list[tuple[str, str]]]:
        """Return the kept records and the dropped root URL and reason pairs."""
        _LOGGER.info("Filtering %d records for superseded release notes", len(records))
        by_slug = {record.root_slug: record for record in records}  # Slug to record map.
        kept_slugs, dropped_slugs = self.select(list(by_slug))  # Reuse the base logic.
        kept = [by_slug[slug] for slug in kept_slugs if slug in by_slug]  # Kept records.
        dropped = [
            (by_slug[slug].source_url, DROP_REASON) for slug in dropped_slugs if slug in by_slug
        ]  # Each dropped root URL with the recorded reason.
        _LOGGER.debug("Kept %d records, dropped %d release notes", len(kept), len(dropped))
        return kept, dropped  # The runner records each dropped root in the store.
