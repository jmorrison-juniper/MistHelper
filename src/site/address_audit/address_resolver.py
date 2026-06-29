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
from src.utils.address_utils import AddressValidationConfig, NominatimValidator  # Reused Tier-2 validator.

_DB_RELATIVE_PATH = os.path.join("data", "mist_data.db")  # Constitution-fixed cache location.
_NOMINATIM_MIN_INTERVAL = 1.1  # Seconds between Nominatim calls (>=1 req/sec ToS).
_SUITE_PATTERN = r"\b(?:ste|suite|unit|apt|bldg|building)\.?\s+#?\s*[\w-]+"  # Suite/unit markers (state-safe).


class AddressResolver:
    """Resolve a site's best canonical address across internal, Nominatim, and UI tiers."""

    def __init__(
        self,
        db_path: str | None = None,
        skip_ssl_verify: bool = False,
        ui_geocoder: Any = None,
    ) -> None:
        """Store cache path, build the reused Nominatim config, and init counters."""
        self._db_path = db_path or _DB_RELATIVE_PATH  # Cache DB path (injectable for tests).
        self._nominatim_config = AddressValidationConfig(skip_ssl_verify=skip_ssl_verify)  # Reused validator cfg.
        self._ui_geocoder = ui_geocoder  # Optional MistUIGeocoder (Tier 3); None disables it.
        self.cache_hits = 0  # Count of cache hits this run (feeds AuditCounters).
        self.external_calls = 0  # Count of Nominatim/UI calls actually made.
        self._last_nominatim_ts = 0.0  # Timestamp of the last Nominatim call for rate limiting.

    def resolve(self, candidates: ResolveCandidates) -> ResolverResult:
        """Resolve one site's address: cache -> Tier 1 -> Tier 2 -> optional Tier 3."""
        query = self._build_query(candidates)  # Construct the human-readable query string.
        key = self._build_query_key(query)  # Normalize it into a cache key.
        logging.info("Resolving address (key=%s)", key)  # Action-log the resolve start.
        cached = self._from_cache(key)  # Cache read before any external call.
        if cached is not None:  # Cache hit -> zero external calls.
            return cached  # Return the cached result verbatim.
        result = self._resolve_uncached(candidates, query)  # Run the tier cascade.
        self._to_cache(key, result)  # Persist the outcome (including negatives).
        logging.debug("Resolved key=%s via source=%s", key, result.source)  # Action-log the outcome.
        return result  # Hand the result back to the engine.

    def _resolve_uncached(self, candidates: ResolveCandidates, query: str) -> ResolverResult:
        """Run Tier 1 -> Tier 2 -> Tier 3 with a fail-soft envelope (FR-013)."""
        try:
            internal = self._compare_internal(candidates)  # Tier 1: no network.
            if internal is not None:  # Internal signal already answers the question.
                internal.query = query  # Stamp the query for cache consistency.
                return internal  # Return the internal suggestion.
            nominatim = self._validate_nominatim(candidates, query)  # Tier 2: free OSM validation.
            if nominatim is not None:  # Nominatim produced a usable result.
                return nominatim  # Return the validated address.
            ui_result = self._maybe_ui(candidates, query)  # Tier 3: optional, flagged.
            if ui_result is not None:  # UI tier captured a suggestion.
                return ui_result  # Return the UI-sourced address.
            return ResolverResult(query=query, canonical_address=None, source="internal", confidence=0.0)
        except Exception as exc:  # noqa: BLE001 -- one row must never abort the audit.
            logging.warning("Resolve failed for key derived from '%s': %s", query, exc)  # Log and continue.
            return ResolverResult(query=query, canonical_address=None, source="internal", confidence=0.0)

    def _compare_internal(self, candidates: ResolveCandidates) -> ResolverResult | None:
        """Tier 1: suggest a CSV/SNMP candidate that adds a suite the Mist address lacks."""
        mist_text = self._format_address(candidates.mist_address)  # Current Mist address as text.
        candidate_text = candidates.snmp_location or self._format_address(candidates.csv_address)  # Best internal.
        if not candidate_text:  # Nothing internal to compare against.
            return None  # Defer to Tier 2.
        if self._adds_suite(mist_text, candidate_text):  # Candidate carries a suite Mist is missing.
            logging.debug("Tier 1 internal suggestion: %s", candidate_text)  # Trace the internal hit.
            return ResolverResult(query="", canonical_address=candidate_text, source="internal", confidence=0.7)
        return None  # No clear internal discrepancy -> let Tier 2 validate.

    def _validate_nominatim(self, candidates: ResolveCandidates, query: str) -> ResolverResult | None:
        """Tier 2: validate the base street via the reused ``NominatimValidator``."""
        self._respect_rate_limit()  # Enforce <=1 req/sec before calling out.
        self.external_calls += 1  # Count this external call for the run summary.
        validator = NominatimValidator(self._nominatim_config)  # Build the reused validator.
        outcome = validator.validate(candidates.mist_address, candidates.csv_address)  # Geocode both addresses.
        comparison = outcome.get("comparison_validation", {})  # The CSV-side geocode result.
        if not comparison.get("valid"):  # Nominatim could not validate the candidate street.
            logging.debug("Nominatim returned no valid comparison result")  # Trace the miss.
            return None  # Defer to Tier 3 / NO_RESULT.
        confidence = float(comparison.get("confidence", 0.0))  # OSM importance-derived confidence.
        canonical = comparison.get("display_name") or self._format_address(candidates.csv_address)  # Canonical.
        return ResolverResult(  # Build the Tier-2 result.
            query=query,  # Echo the query for caching.
            canonical_address=canonical,  # OSM-canonicalized address.
            source="nominatim",  # Originating tier.
            confidence=confidence,  # Validation confidence.
            ambiguous=confidence < 0.4,  # Low confidence flags a possible mall/ambiguous case.
            raw_response=outcome,  # Full validator payload for audit/debug.
        )

    def _maybe_ui(self, candidates: ResolveCandidates, query: str) -> ResolverResult | None:
        """Tier 3: delegate to the optional ``MistUIGeocoder`` when permitted."""
        if not candidates.ui_geocode or self._ui_geocoder is None:  # Tier 3 disabled for this row/run.
            return None  # Skip the UI tier.
        logging.info("Delegating to Tier 3 UI geocoder")  # Action-log the delegation.
        self.external_calls += 1  # Count the UI lookup as an external call.
        result = self._ui_geocoder.geocode_via_ui(query)  # Drive the dashboard autocomplete (fail-soft).
        if result is not None:  # Stamp the query so caching stays consistent.
            result.query = query  # Align the result's query with the cache key source.
        return result  # May be None (fail-soft) -> caller yields NO_RESULT.

    def _respect_rate_limit(self) -> None:
        """Sleep as needed so consecutive Nominatim calls stay within ToS."""
        elapsed = time.monotonic() - self._last_nominatim_ts  # Time since the previous call.
        if elapsed < _NOMINATIM_MIN_INTERVAL:  # Too soon since the last request.
            time.sleep(_NOMINATIM_MIN_INTERVAL - elapsed)  # Pause to respect <=1 req/sec.
        self._last_nominatim_ts = time.monotonic()  # Record this call's timestamp.

    def _build_query(self, candidates: ResolveCandidates) -> str:
        """Build the query string: best internal candidate, optionally business-prefixed."""
        best = (  # First non-empty of SNMP -> CSV -> Mist, in priority order.
            candidates.snmp_location
            or self._format_address(candidates.csv_address)
            or self._format_address(candidates.mist_address)
        )
        if candidates.business_name:  # Prepend the business name when configured.
            return f"{candidates.business_name} {best}".strip()  # Business-qualified query.
        return best.strip()  # Raw-address query (private/internal addresses).

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
    def _adds_suite(base: str, candidate: str) -> bool:
        """Return True when ``candidate`` contains a suite/unit marker ``base`` lacks."""
        candidate_has = re.search(_SUITE_PATTERN, candidate.lower()) is not None  # Candidate carries a suite.
        base_has = re.search(_SUITE_PATTERN, base.lower()) is not None  # Base already has a suite.
        return candidate_has and not base_has  # Discrepancy only when candidate adds one.

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
        try:
            self._ensure_db_dir()  # Make sure the data/ directory exists.
            with sqlite3.connect(self._db_path) as conn:  # Open (creates the DB file if absent).
                self._ensure_cache_table(conn)  # Ensure the table exists before querying.
                row = conn.execute(  # Look up the normalized key.
                    "SELECT canonical_addr, source, confidence, raw_json FROM geocoding_cache WHERE query_key = ?",
                    (key,),
                ).fetchone()
        except sqlite3.Error as exc:  # Cache problems must never break the audit.
            logging.debug("Cache read error (ignored): %s", exc)  # Trace and treat as a miss.
            return None  # Fall through to live resolution.
        if row is None:  # No cached entry for this key.
            return None  # Caller resolves live.
        self.cache_hits += 1  # Count the hit for the run summary.
        logging.debug("cache hit for %s", key)  # Action-log the hit.
        return ResolverResult(  # Reconstruct the result from the cached row.
            query=key,  # Use the key as the query echo.
            canonical_address=row[0],  # Cached canonical address (may be None => NO_RESULT).
            source="cache",  # Mark the source as the cache.
            confidence=float(row[2] or 0.0),  # Cached confidence.
            raw_response=self._loads_json(row[3]),  # Restore the raw payload.
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
                        json.dumps(result.raw_response),
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
