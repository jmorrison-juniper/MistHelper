"""Site matching for the address-audit feature (1003-site-address-audit).

Resolves each customer CSV row to a Mist site. The device **serial number** is
the golden key: serial -> Mist device inventory -> ``site_id`` -> site record
(exact, high-confidence). When a serial is not found, an optional rapidfuzz
address fuzzy-match (>=85% by default) is the fallback. Anything that misses
both is reported as ``unmatched`` so every row stays accountable.

The engine operates on in-memory maps (built by the orchestrator from a single
``mistapi`` inventory + sites read) so it is fast and unit-testable without a
live API. ``rapidfuzz`` is an optional dependency: when absent, fuzzy matching
is skipped after one startup warning and rows simply fall through to
``unmatched``.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
from typing import Any  # Loose typing for Mist device/site record dicts.

from src.site.address_audit.models import MatchedSite  # Match-outcome dataclass.

try:  # Optional dependency: rapidfuzz powers the fuzzy fallback.
    from rapidfuzz import fuzz, process  # Fast fuzzy string matching.
except ImportError:  # pragma: no cover -- exercised only when rapidfuzz is absent.
    fuzz = None  # type: ignore[assignment]  # Sentinel; match_fuzzy degrades to unmatched.
    process = None  # type: ignore[assignment]  # Sentinel for the extractOne helper.

_DEFAULT_FUZZY_THRESHOLD = 85.0  # rapidfuzz score cutoff (overridable via .env FUZZY_MATCH_THRESHOLD).


class SiteMatchingEngine:
    """Match CSV serials/addresses to Mist sites using preloaded inventory maps."""

    def __init__(
        self,
        inventory_by_serial: dict[str, dict[str, Any]],
        sites_by_id: dict[str, dict[str, Any]],
        fuzzy_threshold: float = _DEFAULT_FUZZY_THRESHOLD,
    ) -> None:
        """Store preloaded lookup maps and warn once if rapidfuzz is unavailable."""
        self._inventory_by_serial = inventory_by_serial  # serial -> device record (has site_id).
        self._sites_by_id = sites_by_id  # site_id -> site record (has address/name/vars).
        self._fuzzy_threshold = fuzzy_threshold  # rapidfuzz cutoff for the fallback.
        if process is None:  # rapidfuzz missing -> fuzzy fallback disabled.
            logging.warning("rapidfuzz not installed; address fuzzy fallback disabled")  # One-time warning.

    def match_serial(self, serial: str) -> MatchedSite:
        """Resolve a device serial to its Mist site (high-confidence golden key)."""
        logging.info("Matching serial %s against device inventory", serial)  # Action-log start.
        device = self._inventory_by_serial.get(serial)  # Exact serial lookup in inventory.
        if device is None:  # Serial not present in inventory at all.
            logging.debug("Serial %s not found in inventory", serial)  # Trace the miss.
            return MatchedSite(match_strategy="unmatched")  # Caller may try fuzzy next.
        site_id = device.get("site_id")  # Device's assigned site (may be null/unassigned).
        if not site_id:  # Device exists but is not assigned to a site.
            logging.debug("Serial %s found but device is unassigned", serial)  # Trace unassigned device.
            return MatchedSite(match_strategy="unmatched")  # Reason: device unassigned.
        return self._build_matched_site(site_id, strategy="serial", confidence=1.0)  # Exact match.

    def match_fuzzy(self, address: str, sites: list[dict[str, Any]]) -> MatchedSite:
        """Fall back to a rapidfuzz address match across the provided sites."""
        logging.info("Attempting fuzzy address match for: %s", address)  # Action-log start.
        if process is None or fuzz is None or not address:  # No rapidfuzz or no address to match.
            logging.debug("Fuzzy match skipped (rapidfuzz unavailable or empty address)")  # Trace skip.
            return MatchedSite(match_strategy="unmatched")  # Degrade to unmatched.
        choices = self._build_choice_map(sites)  # site_id -> normalized "address city state".
        best = process.extractOne(  # Find the single best candidate above the cutoff.
            address.lower(),  # Normalize the query for comparison.
            choices,  # Mapping of site_id -> comparable address string.
            scorer=fuzz.WRatio,  # Weighted ratio handles partial/word-order differences.
            score_cutoff=self._fuzzy_threshold,  # Reject anything below the threshold.
        )
        if best is None:  # No candidate cleared the cutoff.
            logging.debug("No fuzzy match >= %.0f for: %s", self._fuzzy_threshold, address)  # Trace miss.
            return MatchedSite(match_strategy="unmatched")  # Below threshold -> unmatched.
        _matched_text, score, site_id = best  # extractOne returns (value, score, key).
        return self._build_matched_site(site_id, strategy="fuzzy", confidence=score / 100.0)  # Scaled.

    def _build_choice_map(self, sites: list[dict[str, Any]]) -> dict[str, str]:
        """Build a site_id -> normalized 'address city state' map for fuzzy scoring."""
        choices: dict[str, str] = {}  # Accumulator keyed by site_id.
        for site in sites:  # Walk every candidate site.
            site_id = site.get("id")  # Site UUID is the map key.
            if not site_id:  # Skip malformed site records with no id.
                continue  # Nothing to key on.
            parts = [site.get("address", ""), site.get("city", ""), site.get("state", "")]  # Address parts.
            choices[site_id] = " ".join(p for p in parts if p).lower().strip()  # Normalized comparable text.
        return choices  # Hand back the comparison map.

    def _build_matched_site(self, site_id: str, strategy: str, confidence: float) -> MatchedSite:
        """Assemble a ``MatchedSite`` from a resolved site_id and match metadata."""
        site = self._sites_by_id.get(site_id, {})  # Look up the full site record.
        logging.debug("Matched site %s via %s (confidence=%.2f)", site_id, strategy, confidence)  # Trace.
        return MatchedSite(  # Build the populated match result.
            site_id=site_id,  # Resolved Mist site UUID.
            site_name=site.get("name"),  # Human-readable site name.
            mist_address=self._extract_mist_address(site),  # Current Mist address dict.
            match_strategy=strategy,  # serial | fuzzy.
            match_confidence=confidence,  # 1.0 serial. Score/100 fuzzy.
        )

    @staticmethod
    def _extract_mist_address(site: dict[str, Any]) -> dict[str, Any]:
        """Pull the standard address sub-fields from a Mist site record."""
        return {  # Normalized address dict used by the resolver and renderer.
            "address": site.get("address", ""),  # Street address.
            "city": site.get("city", ""),  # City.
            "state": site.get("state", ""),  # State code.
            "zip": site.get("zipcode", site.get("zip", "")),  # ZIP (Mist uses 'zipcode').
        }
