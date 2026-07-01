"""Business-authoritative CSV ingestion and lookup for menu option 195.

Loads the customer-provided business authority export (for example,
``T-Builder.csv``), normalizes address records, and exposes a deterministic
lookup keyed by site name and normalized address forms. The lookup is strictly
fail-safe: only unique matches are returned, while ambiguous collisions are
ignored so no row can be auto-bound to the wrong storefront.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import csv  # Header-based CSV parsing for the business export.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # File-existence checks and basename diagnostics.
import re  # Address and key normalization.
from dataclasses import dataclass  # Typed value object for loaded business rows.

from src.site.address_audit.models import AddressRow, MatchedSite  # Existing menu-195 row/site dataclasses.
from src.site.address_audit.suite_patterns import (
    SUITE_PATTERN_CAPTURE as _SUITE_PATTERN,
)  # Shared suite detector for no-suite key normalization.


@dataclass(frozen=True)
class BusinessAuthorityRow:
    """One normalized row from the business-authoritative CSV export."""

    site_name: str  # Business display name column (header: Name).
    address: str  # Street line with optional space/suite merged in.
    city: str  # City from the authority file.
    state: str  # State/region code from the authority file.
    zip_code: str  # Postal code from the authority file.


class BusinessAuthorityIngester:
    """Load and index a business-authoritative CSV for per-row address hints."""

    def load(self, path: str) -> list[BusinessAuthorityRow]:
        """Load ``path`` and return normalized authority rows (empty on malformed body)."""
        logging.info("Loading business-authoritative CSV from %s", path)  # Action-log the selected authority file.
        if not os.path.isfile(path):  # Guard: prompt-selected path might still be missing on disk.
            logging.error("Business-authoritative CSV not found: %s", path)  # Log the hard failure clearly.
            raise FileNotFoundError(f"Business-authoritative CSV not found: {path}")  # Controlled caller-visible error.
        with open(path, encoding="utf-8-sig", newline="") as handle:  # utf-8-sig tolerates Excel/BOM exports.
            reader = csv.DictReader(handle)  # Header-aware parser for T-Builder-like exports.
            rows = [parsed for raw in reader if (parsed := self._parse_row(raw)) is not None]  # Normalize valid rows.
        logging.debug("Loaded %d authoritative rows from %s", len(rows), os.path.basename(path))  # Action-log totals.
        return rows  # Return normalized authority rows for indexing.

    def build_index(self, rows: list[BusinessAuthorityRow]) -> dict[str, dict[str, list[BusinessAuthorityRow]]]:
        """Build lookup buckets keyed by name/full-address/no-suite-address."""
        by_name: dict[str, list[BusinessAuthorityRow]] = {}  # Normalized business name -> candidate authority rows.
        by_full: dict[str, list[BusinessAuthorityRow]] = {}  # Normalized full address key -> candidate rows.
        by_no_suite: dict[str, list[BusinessAuthorityRow]] = {}  # Normalized no-suite key -> candidate rows.
        for row in rows:  # Index every authority row into all supported key spaces.
            self._add_bucket(by_name, self._norm_key(row.site_name), row)  # Name key for direct-name matches.
            self._add_bucket(
                by_full, self._address_key(row.address, row.city, row.state, row.zip_code), row
            )  # Full key.
            self._add_bucket(
                by_no_suite,
                self._address_key(
                    self._strip_suite(row.address), row.city, row.state, row.zip_code
                ),  # Suite-stripped key.
                row,
            )
        return {
            "by_name": by_name,
            "by_full": by_full,
            "by_no_suite": by_no_suite,
        }  # Single serializable lookup object.

    def match(
        self,
        row: AddressRow,
        site: MatchedSite,
        index: dict[str, dict[str, list[BusinessAuthorityRow]]],
    ) -> dict[str, str]:
        """Return one unique authoritative address dict for a row/site, or ``{}`` when ambiguous/none."""
        by_name = index.get("by_name", {})  # Name bucket map.
        by_full = index.get("by_full", {})  # Full-address bucket map.
        by_no_suite = index.get("by_no_suite", {})  # No-suite bucket map.
        site_name_hits = by_name.get(
            self._norm_key(site.site_name or ""), []
        )  # Direct match on matched Mist site name.
        if len(site_name_hits) == 1:  # Unique name match is trustworthy.
            return self._to_address_dict(site_name_hits[0])  # Promote that authority row to a resolver dict.
        csv_full = self._address_key(row.address, row.city, row.state, row.zip_code)  # Primary customer CSV full key.
        csv_hits = by_full.get(csv_full, [])  # Exact full-address matches in authority data.
        if len(csv_hits) == 1:  # Unique full-address match is trustworthy.
            return self._to_address_dict(csv_hits[0])  # Promote that authority row to a resolver dict.
        csv_no_suite = self._address_key(
            self._strip_suite(row.address), row.city, row.state, row.zip_code
        )  # Fallback key.
        csv_no_suite_hits = by_no_suite.get(
            csv_no_suite, []
        )  # Same building/city/state/zip ignoring suite tokenization.
        if len(csv_no_suite_hits) == 1:  # Unique no-suite match is trustworthy.
            return self._to_address_dict(csv_no_suite_hits[0])  # Promote that authority row to a resolver dict.
        mist = site.mist_address or {}  # Matched site's current Mist address (may be sparse/empty).
        mist_no_suite = self._address_key(  # Last deterministic fallback uses the Mist address line.
            self._strip_suite(str(mist.get("address", ""))),
            str(mist.get("city", "")),
            str(mist.get("state", "")),
            str(mist.get("zip", mist.get("zipcode", ""))),
        )
        mist_hits = by_no_suite.get(mist_no_suite, [])  # Candidate authority rows by Mist no-suite key.
        if len(mist_hits) == 1:  # Unique Mist-key match is trustworthy.
            return self._to_address_dict(mist_hits[0])  # Promote that authority row to a resolver dict.
        return {}  # No unique mapping -> fail-safe empty (never bind a row to a wrong authority record).

    def _parse_row(self, raw: dict[str, str]) -> BusinessAuthorityRow | None:
        """Normalize one authority CSV row; skip rows with no usable street/city/state/zip."""
        site_name = (raw.get("Name") or "").strip()  # Business storefront name (may be blank on some exports).
        street = (raw.get("Address") or "").strip()  # Base street line from authority export.
        space = (raw.get("Space #") or "").strip()  # Separate suite/unit column in T-Builder exports.
        city = (raw.get("City") or "").strip()  # City field.
        state = (raw.get("State") or "").strip()  # State/region field.
        zip_code = (raw.get("Zip") or "").strip()  # ZIP/postal field.
        if not street or not city or not state:  # Reject rows missing basic geocoding identity.
            return None  # Skip incomplete rows; caller keeps ingestion fail-soft.
        merged = self._merge_street_and_space(street, space)  # Build one street line with space/suite included.
        return BusinessAuthorityRow(site_name=site_name, address=merged, city=city, state=state, zip_code=zip_code)

    @staticmethod
    def _merge_street_and_space(street: str, space: str) -> str:
        """Merge Address + Space # once, avoiding duplicate suite tokens."""
        if not space:  # Nothing to merge from the dedicated suite/unit column.
            return street  # Keep the street as-is.
        if space.lower() in street.lower():  # Space value already embedded in street.
            return street  # Avoid duplicating the same suite/unit token.
        return " ".join([street, space]).strip()  # Append the authority suite token to the street.

    @staticmethod
    def _to_address_dict(row: BusinessAuthorityRow) -> dict[str, str]:
        """Convert an authority row into the resolver's standard address dict shape."""
        return {  # Common address shape reused by resolver + classifier.
            "address": row.address,  # Street line with suite/unit.
            "city": row.city,  # City.
            "state": row.state,  # State/region.
            "zip": row.zip_code,  # ZIP/postal code.
        }

    @staticmethod
    def _strip_suite(text: str) -> str:
        """Return ``text`` with the first suite/unit token removed for no-suite matching."""
        return re.sub(_SUITE_PATTERN, " ", text, flags=re.IGNORECASE).strip()  # Shared suite regex for consistency.

    @staticmethod
    def _address_key(street: str, city: str, state: str, zip_code: str) -> str:
        """Build a normalized address key for exact/equivalent matching."""
        return BusinessAuthorityIngester._norm_key(" ".join(part for part in [street, city, state, zip_code] if part))

    @staticmethod
    def _norm_key(text: str) -> str:
        """Lowercase and collapse punctuation/whitespace into a stable alnum key."""
        alnum = re.sub(r"[^a-z0-9]+", " ", text.lower())  # Keep only lowercase alnum tokens.
        return " ".join(alnum.split())  # Collapse whitespace into a deterministic key.

    @staticmethod
    def _add_bucket(
        buckets: dict[str, list[BusinessAuthorityRow]],
        key: str,
        row: BusinessAuthorityRow,
    ) -> None:
        """Append ``row`` to ``buckets[key]`` when ``key`` is non-empty."""
        if not key:  # Empty keys are non-discriminative and unsafe to index.
            return  # Skip blank bucket keys.
        buckets.setdefault(key, []).append(row)  # Append to the keyed candidate list.
