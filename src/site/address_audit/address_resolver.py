"""Tiered address resolver for the address-audit feature (1003-site-address-audit).

Resolves the best canonical address for one site WITHOUT any paid or non-existent
API. Order of resolution:

  * Tier 1 (internal, no network): compare the Mist address against the CSV
    address and the SNMP location; when an internal candidate clearly carries a
    suite/unit the Mist address lacks, that candidate is the suggestion.
  * Tier 2 (Nominatim, free, <=1 req/sec): reuse the existing
    ``NominatimValidator`` to validate the base street and produce a canonical
    OSM address.
  * Tier 3 (optional, flagged): delegate to ``MistUIGeocoder`` only when the row
    permits UI geocoding (mall/ambiguous cases).

A SQLite ``geocoding_cache`` table in ``data/mist_data.db`` is read before any
Tier 2/3 call and upserted after, so reruns make zero external calls for
unchanged addresses. Any failure degrades to ``ResolverResult(canonical_address
=None)`` (the row classifies ``NO_RESULT``) -- the audit is never aborted.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import json  # Serialize raw tier payloads into the cache.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # DB path construction and directory creation.
import re  # Suite/unit marker detection in Tier-1 comparison.
import sqlite3  # Local cache store.
import time  # Enforce the Nominatim rate limit between calls.
from datetime import UTC, datetime  # ISO-8601 UTC cache timestamps.
from typing import Any  # Loose typing for address dicts and the UI geocoder handle.

from src.site.address_audit.models import ResolveCandidates, ResolverResult  # Resolver I/O dataclasses.
from src.site.address_audit.perf import PhaseTimer  # Per-phase timing to expose slow tiers.
from src.site.address_audit.suite_patterns import SUITE_PATTERN as _SUITE_PATTERN  # Shared suite/unit detector.
from src.utils.address_utils import AddressValidationConfig, NominatimValidator  # Reused Tier-2 validator.

_DB_RELATIVE_PATH = os.path.join("data", "mist_data.db")  # Constitution-fixed cache location.
_NOMINATIM_MIN_INTERVAL = 1.1  # Seconds between Nominatim calls (>=1 req/sec ToS).


class AddressResolver:
    """Resolve a site's best canonical address across internal, Nominatim, and UI tiers."""

    def __init__(
        self,
        db_path: str | None = None,
        skip_ssl_verify: bool = False,
        ui_geocoder: Any = None,
        perf: PhaseTimer | None = None,
    ) -> None:
        """Store cache path, build the reused Nominatim config, and init counters."""
        self._db_path = db_path or _DB_RELATIVE_PATH  # Cache DB path (injectable for tests).
        self._nominatim_config = AddressValidationConfig(skip_ssl_verify=skip_ssl_verify)  # Reused validator cfg.
        self._ui_geocoder = ui_geocoder  # Optional MistUIGeocoder (Tier 3); None disables it.
        self._perf = perf or PhaseTimer()  # Timing sink (own no-op timer when the caller passes none).
        self.cache_hits = 0  # Count of cache hits this run (feeds AuditCounters).
        self.external_calls = 0  # Count of Nominatim/UI calls actually made.
        self._last_nominatim_ts = 0.0  # Timestamp of the last Nominatim call for rate limiting.

    def resolve(self, candidates: ResolveCandidates) -> ResolverResult:
        """Resolve one site's address: cache -> Tier 1 -> Tier 2 -> optional Tier 3."""
        query = self._build_query(candidates)  # Construct the human-readable query string.
        key = self._build_query_key(query)  # Normalize it into a cache key.
        logging.info("Resolving address (key=%s)", key)  # Action-log the resolve start.
        with self._perf.phase("cache_read"):  # Time the SQLite cache lookup.
            cached = self._from_cache(key)  # Cache read before any external call.
        if cached is not None:  # Cache hit -> zero external calls.
            return cached  # Return the cached result verbatim.
        result = self._resolve_uncached(candidates, query)  # Run the tier cascade.
        self._to_cache(key, result)  # Persist the outcome (including negatives).
        logging.debug("Resolved key=%s via source=%s", key, result.source)  # Action-log the outcome.
        return result  # Hand the result back to the engine.

    def _resolve_uncached(self, candidates: ResolveCandidates, query: str) -> ResolverResult:
        """Run Tier 1 (internal) + Tier 2 (OSM) + optional Tier 3 (web authority), fail-soft."""
        try:
            with self._perf.phase("tier1_internal"):  # Time the no-network internal comparison.
                internal = self._compare_internal(candidates)  # Tier 1: internal suite candidate (no network).
            with self._perf.phase("tier2_nominatim"):  # Time OSM validation incl. its rate-limit sleep.
                osm = self._validate_nominatim(candidates, query)  # Tier 2: OpenStreetMap street validation.
            with self._perf.phase("tier3_ui"):  # Time the browser tier incl. typing/read/politeness.
                ui = self._maybe_ui(candidates, query)  # Tier 3: Google-via-Mist authority (gated; fail-soft).
            return self._combine(internal, osm, ui, candidates, query)  # Merge the tiers into one result.
        except Exception as exc:  # noqa: BLE001 -- one row must never abort the audit.
            logging.warning("Resolve failed for key derived from '%s': %s", query, exc)  # Log and continue.
            return ResolverResult(query=query, canonical_address=None, source="internal", confidence=0.0)

    def _combine(
        self,
        internal: ResolverResult | None,
        osm: ResolverResult | None,
        ui: ResolverResult | None,
        candidates: ResolveCandidates,
        query: str,
    ) -> ResolverResult:  # WHY: fan-in point where the three tiers collapse to one authoritative answer.
        """Merge results with the web (Tier 3) as the authority for the true suite.

        Priority: a confident Tier-3 (Google-via-Mist) suggestion WINS because it is
        the only source that knows the real suite; otherwise the internal suite
        candidate (street cross-checked by OSM); otherwise OSM's validated street;
        otherwise NO_RESULT. Tier 3 only overrides when it actually returned an
        address, so a missing/failed browser never makes results worse.
        """
        winner = self._pick_tier_winner(ui, internal, osm)  # WHY: encapsulate priority order in a pure helper.
        if winner is None:  # WHY: no tier produced an address -> NO_RESULT sentinel.
            return ResolverResult(query=query, canonical_address=None, source="internal", confidence=0.0)
        winner.query = query  # WHY: stamp the query so the cache key round-trips consistently.
        winner.street_validated = self._resolve_validated(winner, ui, osm)  # WHY: preserve OSM cross-check semantics.
        return winner  # WHY: single return keeps the merge trivial and free of tier-specific branches.

    @staticmethod
    def _pick_tier_winner(
        ui: ResolverResult | None,
        internal: ResolverResult | None,
        osm: ResolverResult | None,
    ) -> ResolverResult | None:  # WHY: isolate the tier-priority table from the finalization logic.
        """Return the highest-priority non-empty tier result, or None when all tiers are empty."""
        if ui is not None and ui.canonical_address:  # WHY: Tier 3 only wins with a real (suite-bearing) address.
            return ui  # WHY: web authority is the only source that knows the true suite.
        if internal is not None:  # WHY: internal suite hint beats a bare OSM street when both exist.
            return internal  # WHY: suite-bearing suggestion wins over a mere street validation.
        return osm  # WHY: OSM (or None) is the last-chance answer.

    @staticmethod
    def _resolve_validated(
        winner: ResolverResult,
        ui: ResolverResult | None,
        osm: ResolverResult | None,
    ) -> bool:  # WHY: tier identity dictates how the street-validated flag is derived.
        """Return the street_validated flag for the winning tier, respecting OSM cross-check."""
        osm_present = osm is not None  # WHY: cache the presence check so both branches read cleanly.
        if winner is ui:  # WHY: Tier 3 may already carry its own validated flag; OR with OSM cross-check.
            return winner.street_validated or osm_present  # WHY: never demote an already-validated UI answer.
        if winner is osm:  # WHY: OSM itself is the external validator when it wins.
            return True  # WHY: OSM's presence *is* the confirmation.
        return osm_present  # WHY: internal winner only trusts OSM's separate confirmation.

    def _compare_internal(self, candidates: ResolveCandidates) -> ResolverResult | None:
        """Tier 1: build a clean Mist-base + suite suggestion when Mist is missing a suite.

        The suite is taken preferentially from the business-authoritative CSV,
        then the customer CSV, then the SNMP location. The suggestion is rebuilt
        from Mist's own clean street/city/state/zip so store-number prefixes and
        stale ZIPs never leak into the output.
        """
        mist_street = candidates.mist_address.get("address", "")  # Mist street line (the clean base).
        if re.search(_SUITE_PATTERN, mist_street, flags=re.IGNORECASE):  # Mist already carries a suite.
            return None  # No discrepancy to surface; defer to Tier 2.
        suite = self._pick_internal_suite(candidates)  # WHY: fold the authority/CSV/SNMP fallback chain into a helper.
        if not suite:  # Neither internal source supplies a suite Mist lacks.
            return None  # Nothing to add; defer to Tier 2.
        clean = self._build_clean_suggestion(candidates.mist_address, suite)  # Mist base + suite, no pollution.
        logging.debug("Tier 1 internal suggestion (suite=%s): %s", suite, clean)  # Trace the internal hit.
        return ResolverResult(query="", canonical_address=clean, source="internal", confidence=0.7)

    def _pick_internal_suite(self, candidates: ResolveCandidates) -> str:  # WHY: keep suite fallback out of Tier 1.
        """Return the first available suite token: authority > CSV > SNMP; empty string when none."""
        for source in (candidates.authoritative_address, candidates.csv_address):  # WHY: authority-first preference.
            suite = self._extract_suite(source.get("address", ""))  # WHY: normalized suite token or empty.
            if suite:  # WHY: first non-empty match wins.
                return suite  # WHY: authority beats CSV beats SNMP by iteration order.
        return self._extract_suite(candidates.snmp_location or "")  # WHY: SNMP is the last-resort fallback.

    @staticmethod
    def _extract_suite(text: str) -> str:
        """Return the normalized suite/unit token from an address string, or ''."""
        match = re.search(_SUITE_PATTERN, text, flags=re.IGNORECASE)  # First suite token in the string.
        if not match:  # No suite present.
            return ""  # Signal absence.
        return " ".join(match.group(0).split()).strip()  # Collapse whitespace in the matched token.

    def _build_clean_suggestion(self, mist_address: dict[str, Any], suite: str) -> str:
        """Compose a clean suggested address from Mist's own fields plus the suite."""
        base = mist_address.get("address", "").strip()  # Mist's street line.
        base = re.sub(_SUITE_PATTERN, "", base, flags=re.IGNORECASE).strip().rstrip(",").strip()  # De-dupe suite.
        street = f"{base} {suite}".strip() if suite else base  # Append the discovered suite.
        locality = self._build_locality(mist_address)  # WHY: pull "STATE ZIP" join into a helper to cap CC.
        parts = [street, mist_address.get("city", ""), locality]  # Ordered output components.
        return ", ".join(part for part in parts if part).strip()  # Clean "street, city, ST ZIP".

    @staticmethod
    def _build_locality(mist_address: dict[str, Any]) -> str:  # WHY: isolate the state/zip join so CC stays under 5.
        """Return a "STATE ZIP" pair built from Mist fields; empty string when both are absent."""
        zip_value = mist_address.get("zip") or mist_address.get("zipcode", "")  # WHY: either zip key may be populated.
        tokens = (mist_address.get("state", ""), str(zip_value))  # WHY: state first, ZIP second per US postal order.
        return " ".join(token for token in tokens if token).strip()  # WHY: filter empties so lone components stand.

    def _validate_nominatim(self, candidates: ResolveCandidates, query: str) -> ResolverResult | None:
        """Tier 2: validate the base street via the reused ``NominatimValidator``."""
        self._respect_rate_limit()  # Enforce <=1 req/sec before calling out.
        self.external_calls += 1  # Count this external call for the run summary.
        mist_street = self._strip_suite_from_dict(candidates.mist_address)  # OSM has no suites -> validate street.
        csv_street = self._strip_suite_from_dict(candidates.csv_address)  # Strip suite so the street can match.
        logging.info("Validating street via OpenStreetMap/Nominatim: %s", csv_street.get("address", query))
        validator = NominatimValidator(self._nominatim_config)  # Build the reused validator.
        outcome = validator.validate(mist_street, csv_street)  # Geocode both suite-stripped streets.
        comparison = outcome.get("comparison_validation", {})  # The CSV-side geocode result.
        if not comparison.get("valid"):  # Nominatim could not validate the candidate street.
            self._log_nominatim_miss(csv_street, mist_street, query)  # WHY: keep miss-log path off the hot return.
            return None  # Defer to Tier 3 / NO_RESULT.
        confidence = float(comparison.get("confidence", 0.0))  # OSM importance-derived confidence.
        canonical = self._nominatim_canonical(candidates, comparison)  # Clean street line (not raw display_name).
        logging.info("Nominatim validated street: %s (confidence=%.2f)", canonical, confidence)  # Visible hit.
        return ResolverResult(  # Build the Tier-2 result.
            query=query,  # Echo the query for caching.
            canonical_address=canonical,  # OSM-canonicalized address.
            source="nominatim",  # Originating tier.
            confidence=confidence,  # Validation confidence.
            ambiguous=confidence < 0.4,  # Low confidence flags a possible mall/ambiguous case.
            raw_response=outcome,  # Full validator payload for audit/debug.
        )

    @staticmethod
    def _log_nominatim_miss(
        csv_street: dict[str, Any],
        mist_street: dict[str, Any],
        query: str,
    ) -> None:  # WHY: single-purpose helper keeps _validate_nominatim under the 25-line cap.
        """Emit the "no result" warning with the actual street that was geocoded."""
        street_for_log = csv_street.get("address") or mist_street.get("address") or query  # WHY: prefer the CSV try.
        logging.warning(  # WHY: show the real street, not the business+suite query string.
            "Nominatim returned no result for street '%s' (check network/SSL)", street_for_log
        )

    def _nominatim_canonical(self, candidates: ResolveCandidates, comparison: dict[str, Any]) -> str:
        """Return a clean suggestion for an OSM-validated row from Mist's own address.

        OpenStreetMap validates only the *street*; its ``display_name`` is verbose
        and noisy (``Business, 1200, Northwest 87th Avenue, Doral, Miami-Dade
        County, Florida, 33172, United States``). Since OSM merely confirms the
        street is real, the cleanest, most useful suggestion is Mist's own
        already-formatted address string with the trailing country dropped --
        consistent with the Tier-1/Tier-3 outputs and never losing an existing
        suite. Falls back to the raw display_name only if Mist has no usable address.
        """
        mist_address = (candidates.mist_address.get("address") or "").strip()  # Mist's full address string.
        if mist_address:  # Mist has a usable address line.
            return re.sub(r",?\s*(?:USA|United States)\s*$", "", mist_address, flags=re.IGNORECASE).strip()
        return comparison.get("display_name") or self._format_address(candidates.csv_address)  # Last resort.

    def _maybe_ui(self, candidates: ResolveCandidates, query: str) -> ResolverResult | None:
        """Tier 3: consult the Google-via-Mist authority to find or adjudicate the suite.

        Runs when UI geocoding is permitted AND either the Mist street lacks a
        suite (discover the true unit for shipping) or the CSV claims a different
        unit than Mist (adjudicate the conflict). Rows where Mist already carries a
        suite that matches the CSV skip the (slow) browser lookup. Fail-soft to
        ``None``.
        """
        if not candidates.ui_geocode or self._ui_geocoder is None:  # Tier 3 disabled for this row/run.
            return None  # Skip the UI tier.
        if not self._should_consult_ui(candidates):  # Mist suite present and consistent with the CSV.
            logging.debug("Mist suite present and matches CSV; skipping Tier-3 lookup")  # Nothing to discover.
            return None  # Save a browser lookup.
        logging.info("Delegating to Tier 3 (Google-via-Mist) to deduce the suite")  # Action-log delegation.
        result = self._ui_lookup_with_fallback(candidates, query)  # Business query, then plain on a miss.
        if result is not None:  # Stamp the query so caching stays consistent.
            result.query = query  # Align the result's query with the cache key source.
        return result  # May be None / empty (fail-soft) -> caller falls back to Tier 1/2.

    def _ui_lookup_with_fallback(self, candidates: ResolveCandidates, query: str) -> ResolverResult | None:
        """Geocode the business-prefixed query; if it yields nothing, retry the plain address.

        A business-name prefix (``T-Mobile <addr>``) helps Google return the exact
        store unit, but when no store sits at that number Google returns unrelated
        stores and the stale-guard rejects them all. Retrying the plain address
        then resolves the street itself (for example ``2315 S Federal Hwy``).
        """
        self.external_calls += 1  # Count the primary UI lookup.
        result = self._ui_geocoder.geocode_via_ui(query)  # Business-prefixed query first.
        if self._has_address(result) or not candidates.business_name:  # Got an answer, or nothing to strip.
            return result  # Use the primary result as-is.
        plain = self._consensus_address(candidates)  # The same address without the business prefix.
        if not plain:  # No usable plain query to retry with.
            return result  # Keep the (empty) primary result.
        logging.info("Tier 3 retrying without business prefix: %s", plain)  # Action-log the fallback.
        self.external_calls += 1  # Count the fallback lookup.
        return self._ui_geocoder.geocode_via_ui(plain)  # Plain-address retry (fail-soft).

    @staticmethod
    def _has_address(result: ResolverResult | None) -> bool:
        """Return True when a resolver result actually carries a canonical address."""
        return result is not None and bool(result.canonical_address)  # Non-empty suggestion present.

    def _should_consult_ui(self, candidates: ResolveCandidates) -> bool:
        """Run Tier 3 when Mist lacks a suite, or when the CSV claims a different one.

        The goal is the true shippable unit. Tier 3 runs when Mist has no suite
        (discover it) or when the business-authoritative/CSV unit disagrees with
        Mist's (adjudicate the conflict via the web). It is skipped only when Mist
        already carries the same unit, sparing a browser lookup.
        """
        mist_unit = self._suite_unit(candidates.mist_address.get("address", ""))  # Mist's unit id (or '').
        if not mist_unit:  # Mist has no suite at all.
            return True  # Discover the missing suite.
        return self._has_unit_conflict(candidates, mist_unit)  # WHY: table-drive the authority/CSV conflict scan.

    def _has_unit_conflict(self, candidates: ResolveCandidates, mist_unit: str) -> bool:
        """Return True when authority or CSV claim a suite different from Mist's."""
        sources = (  # WHY: (log-label, address-dict) pairs preserve the authority-then-CSV precedence.
            ("business-authority", candidates.authoritative_address),
            ("CSV", candidates.csv_address),
        )
        for label, address in sources:  # WHY: iterate in priority order so the first conflict wins.
            other_unit = self._suite_unit(address.get("address", ""))  # WHY: normalize both sides to bare unit ids.
            if other_unit and other_unit != mist_unit:  # WHY: only a *different* non-empty unit is a conflict.
                logging.info(  # WHY: log the specific source so operators can audit the adjudication trigger.
                    "Mist unit %r conflicts with %s unit %r; adjudicating via Tier 3",
                    mist_unit,
                    label,
                    other_unit,
                )
                return True  # WHY: resolve the conflict against the web.
        return False  # Mist already specific and consistent with the CSV.

    @staticmethod
    def _suite_unit(street: str) -> str:
        """Extract the bare unit identifier from a street's suite token (for example 'h200', '204', '')."""
        token = AddressResolver._extract_suite(street)  # for example 'Suite H200', '#204', 'Space P239'.
        if not token:  # No suite token present.
            return ""  # No unit.
        parts = token.split()  # Split the keyword from the identifier.
        return parts[-1].lstrip("#").lower() if parts else token.lower()  # Trailing unit id, '#' stripped.

    def _respect_rate_limit(self) -> None:
        """Sleep as needed so consecutive Nominatim calls stay within ToS."""
        elapsed = time.monotonic() - self._last_nominatim_ts  # Time since the previous call.
        if elapsed < _NOMINATIM_MIN_INTERVAL:  # Too soon since the last request.
            time.sleep(_NOMINATIM_MIN_INTERVAL - elapsed)  # Pause to respect <=1 req/sec.
        self._last_nominatim_ts = time.monotonic()  # Record this call's timestamp.

    def _build_query(self, candidates: ResolveCandidates) -> str:
        """Build the geocoding query from the consensus hint, optionally business-prefixed."""
        address = self._consensus_address(candidates)  # Best hint by house-number agreement.
        if candidates.business_name:  # Prepend the business name (retail store disambiguation).
            return f"{candidates.business_name} {address}".strip()  # Business-qualified query.
        return address.strip()  # Raw-address query (private/internal addresses).

    def _consensus_address(self, candidates: ResolveCandidates) -> str:
        """Pick the hint whose house number the most sources agree on (suite-preferring).

        The Mist address, SNMP location, customer CSV, and optional business
        authority CSV are all hints, and any single one can be wrong. Voting on
        house number means one bad hint cannot hijack the geocoding query; the
        agreed-upon, cleanest, suite-bearing source wins.
        """
        hints = self._gather_hints(candidates)  # [(label, text, house_no, has_suite), ...].
        if not hints:  # No usable hint at all.
            return ""  # Empty query -> NO_RESULT.
        winner = self._majority_house_number(hints)  # House number with the most votes.
        group = [hint for hint in hints if hint[2] == winner] or hints  # Sources matching the winner.
        return self._prefer_hint(group)[1]  # Suite-bearing first, then CSV > Mist > SNMP.

    def has_conflicting_hints(self, candidates: ResolveCandidates) -> bool:
        """Return True when the hints disagree on the house number with no majority.

        The Mist address, customer CSV, SNMP location, and optional business
        authority are independent hints. A split with a clear leader is still
        accepted, but when top votes tie there is no majority to break the tie.
        Such rows are surfaced for manual review instead of auto-corrected.
        """
        hints = self._gather_hints(candidates)  # [(label, text, house_no, has_suite), ...].
        numbers = [house for _, _, house, _ in hints if house]  # Non-empty leading house numbers only.
        distinct = set(numbers)  # Unique house numbers across the hints.
        if len(distinct) < 2:  # Zero or one distinct number -> consensus or a single source.
            return False  # Nothing for the sources to disagree about.
        if not self._has_tied_leaders(numbers, distinct):  # WHY: single leader = majority-wins, no conflict.
            return False  # Clear leader breaks the tie -> not a conflict.
        logging.info("Conflicting hint house numbers %s; no majority to trust", sorted(distinct))  # Explain the flag.
        return True  # True only when the sources actively disagree with no winner.

    @staticmethod
    def _has_tied_leaders(numbers: list[str], distinct: set[str]) -> bool:  # WHY: extract vote-count math.
        """Return True when at least two distinct house numbers share the top vote count."""
        counts = {number: numbers.count(number) for number in distinct}  # WHY: one pass per distinct number.
        top = max(counts.values())  # WHY: highest vote count is the leader threshold.
        leaders = sum(1 for votes in counts.values() if votes == top)  # WHY: count how many share the lead.
        return leaders > 1  # WHY: two or more leaders => tied => no majority.

    def _gather_hints(self, candidates: ResolveCandidates) -> list[tuple[str, str, str, bool]]:
        """Normalize each hint into (label, text, house_number, has_suite); drop empties."""
        raw = [  # Source label -> raw text (authority/CSV first so ties prefer customer-provided business data).
            ("authority", self._format_address(candidates.authoritative_address)),
            ("csv", self._format_address(candidates.csv_address)),
            ("mist", self._format_address(candidates.mist_address)),
            ("snmp", candidates.snmp_location or ""),
        ]
        hints: list[tuple[str, str, str, bool]] = []  # Accumulate usable hints.
        for label, text in raw:  # Walk each candidate source.
            norm = self._normalize_glue(text)  # Repair directional glue (SFederal -> S Federal).
            if norm:  # Skip empty sources.
                has_suite = bool(re.search(_SUITE_PATTERN, norm, flags=re.IGNORECASE))  # Suite present?
                hints.append((label, norm, self._leading_house_number(norm), has_suite))  # Record it.
        return hints  # One tuple per non-empty source.

    @staticmethod
    def _normalize_glue(text: str) -> str:
        """Repair common SNMP glue: split a directional/US prefix fused to a street name."""
        spaced = re.sub(r"\b(US|NE|NW|SE|SW|N|S|E|W)([A-Z][a-z])", r"\1 \2", text)  # NMilitary -> N Military.
        no_space_comma = re.sub(r"\s+,", ",", spaced)  # Drop any space before a comma.
        return re.sub(r"\s{2,}", " ", no_space_comma).strip()  # Collapse repeated whitespace.

    @staticmethod
    def _leading_house_number(text: str) -> str:
        """Return the leading 1-6 digit run (the house number), or '' when none leads.

        Anchored at the start so a trailing ZIP is never mistaken for a house
        number (for example ``S Federal Hwy ... 34982`` has no house number).
        """
        match = re.match(r"\s*(\d{1,6})\b", text)  # House numbers lead the street line.
        return match.group(1) if match else ""  # Leading digits or empty.

    @staticmethod
    def _majority_house_number(hints: list[tuple[str, str, str, bool]]) -> str:
        """Return the house number shared by the most sources (CSV wins ties via insertion order)."""
        counts: dict[str, int] = {}  # House number -> vote count.
        for _, _, number, _ in hints:  # Tally every non-empty house number.
            if number:  # Ignore sources without a leading house number.
                counts[number] = counts.get(number, 0) + 1  # One vote.
        if not counts:  # No house numbers anywhere.
            return ""  # No consensus possible.
        return max(counts, key=lambda key: counts[key])  # Most-voted (first-inserted on ties = CSV).

    @staticmethod
    def _prefer_hint(group: list[tuple[str, str, str, bool]]) -> tuple[str, str, str, bool]:
        """Pick the best hint in a group: suite-bearing first, then Authority > CSV > Mist > SNMP."""
        rank = {"authority": 0, "csv": 1, "mist": 2, "snmp": 3}  # Source preference for ties.
        return sorted(group, key=lambda hint: (not hint[3], rank.get(hint[0], 9)))[0]  # Suite, then source.

    @staticmethod
    def _build_query_key(query: str) -> str:
        """Normalize a query into a cache key (lowercase + collapsed whitespace)."""
        return " ".join(query.lower().split())  # Lowercase and collapse all whitespace runs.

    @staticmethod
    def _format_address(address: dict[str, Any]) -> str:
        """Join an address dict into a single comparable 'street city state zip' string."""
        parts = [  # Ordered address components.
            address.get("address", ""),  # Street.
            address.get("city", ""),  # City.
            address.get("state", ""),  # State code.
            str(address.get("zip", address.get("zipcode", ""))),  # ZIP (either key).
        ]
        return " ".join(part for part in parts if part).strip()  # Skip blanks; trim.

    @staticmethod
    def _strip_suite_from_dict(address: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of an address dict with any suite/unit token removed from the street.

        OpenStreetMap does not carry US retail suite numbers, so the suite is
        stripped before geocoding to let the base street match.
        """
        cleaned = dict(address)  # Shallow copy so the caller's dict is untouched.
        street = cleaned.get("address", "")  # Original street line (may carry a suite).
        without_suite = re.sub(_SUITE_PATTERN, "", street, flags=re.IGNORECASE)  # Drop the suite token.
        cleaned["address"] = re.sub(r"[,\s]+$", "", without_suite).strip()  # Trim trailing comma/space.
        return cleaned  # Suite-free address dict for OSM geocoding.

    def _ensure_db_dir(self) -> None:
        """Create the cache DB's parent directory if it does not yet exist."""
        parent = os.path.dirname(os.path.abspath(self._db_path))  # Absolute parent directory.
        os.makedirs(parent, exist_ok=True)  # Idempotent directory creation.

    @staticmethod
    def _ensure_cache_table(conn: sqlite3.Connection) -> None:
        """Create the additive ``geocoding_cache`` table if absent (idempotent)."""
        conn.execute(  # CREATE IF NOT EXISTS keeps reruns and existing DBs safe.
            "CREATE TABLE IF NOT EXISTS geocoding_cache ("
            "query_key TEXT PRIMARY KEY, canonical_addr TEXT, source TEXT, "
            "confidence REAL, raw_json TEXT, cached_at TEXT)"
        )

    def _from_cache(self, key: str) -> ResolverResult | None:
        """Return a cached ``ResolverResult`` for ``key``, or ``None`` on miss/error."""
        row = self._fetch_cached_row(key)  # WHY: isolate the SQLite path so this stays a plain flow.
        if row is None:  # No cached entry for this key (or read failed).
            return None  # Caller resolves live.
        self.cache_hits += 1  # Count the hit for the run summary.
        logging.debug("cache hit for %s", key)  # Action-log the hit.
        return self._row_to_result(row, key)  # WHY: hydration is a pure transform of tuple -> dataclass.

    def _fetch_cached_row(self, key: str) -> tuple[Any, Any, Any, Any] | None:  # WHY: split I/O from mapping.
        """Return the raw SQLite row for ``key``, or None on miss / error (fail-soft)."""
        try:
            self._ensure_db_dir()  # Make sure the data/ directory exists.
            with sqlite3.connect(self._db_path) as conn:  # Open (creates the DB file if absent).
                self._ensure_cache_table(conn)  # Ensure the table exists before querying.
                return conn.execute(  # WHY: single-row lookup by normalized cache key.
                    "SELECT canonical_addr, source, confidence, raw_json FROM geocoding_cache WHERE query_key = ?",
                    (key,),
                ).fetchone()
        except sqlite3.Error as exc:  # Cache problems must never break the audit.
            logging.debug("Cache read error (ignored): %s", exc)  # Trace and treat as a miss.
            return None  # Fall through to live resolution.

    def _row_to_result(self, row: tuple[Any, Any, Any, Any], key: str) -> ResolverResult:  # WHY: pure hydration.
        """Reconstruct a ``ResolverResult`` from a cached SQLite row."""
        raw = self._loads_json(row[3])  # Restore the raw payload (carries street-validation flag).
        return ResolverResult(  # Reconstruct the result from the cached row.
            query=key,  # Use the key as the query echo.
            canonical_address=row[0],  # Cached canonical address (may be None => NO_RESULT).
            source="cache",  # Mark the source as the cache.
            confidence=float(row[2] or 0.0),  # Cached confidence.
            raw_response=raw,  # Restore the raw payload.
            street_validated=bool(raw.get("_street_validated", False)),  # Restore OSM confirmation flag.
        )

    def _to_cache(self, key: str, result: ResolverResult) -> None:
        """Upsert a resolved result into the cache (negatives included)."""
        try:
            self._ensure_db_dir()  # Ensure the data/ directory exists.
            with sqlite3.connect(self._db_path) as conn:  # Open the cache DB.
                self._ensure_cache_table(conn)  # Ensure the table exists before writing.
                conn.execute(  # INSERT OR REPLACE avoids duplicate-key errors on rerun.
                    "INSERT OR REPLACE INTO geocoding_cache "
                    "(query_key, canonical_addr, source, confidence, raw_json, cached_at) VALUES (?,?,?,?,?,?)",
                    (
                        key,
                        result.canonical_address,
                        result.source,
                        result.confidence,
                        json.dumps({**result.raw_response, "_street_validated": result.street_validated}),
                        datetime.now(UTC).isoformat(),
                    ),
                )
        except sqlite3.Error as exc:  # A cache-write failure is non-fatal.
            logging.debug("Cache write error (ignored): %s", exc)  # Trace and continue.

    @staticmethod
    def _loads_json(raw: str | None) -> dict[str, Any]:
        """Safely parse a cached JSON payload into a dict, defaulting to empty."""
        if not raw:  # Null/empty payloads become an empty dict.
            return {}  # Nothing to parse.
        try:
            parsed = json.loads(raw)  # Attempt to decode the stored JSON.
        except (ValueError, TypeError):  # Corrupt payloads must not crash the run.
            return {}  # Degrade gracefully.
        return parsed if isinstance(parsed, dict) else {}  # Only dict payloads are expected.
