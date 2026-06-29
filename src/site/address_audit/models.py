"""Dataclasses for the address-audit feature (1003-site-address-audit).

Defines every value object the audit pipeline exchanges: ``AddressRow`` (one
parsed CSV row), ``MatchedSite`` (a row resolved to a Mist site + SNMP),
``ResolverResult`` (output of any resolution tier), ``AuditResult`` (the per-row
record that drives both the table and the saved CSV), ``AuditCounters`` (run
summary), and the ``ResolveCandidates`` config object plus ``UIGeocoderConfig``
(browser-connection + bounding settings for the Tier-3 UI geocoder).

Field names and ``source`` values match ``specs/1003-site-address-audit/
data-model.md`` so the resolver can cache/persist results without divergence.
Dataclasses hold no behavior beyond trivial defaults (logic lives in the owning
classes).
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

from dataclasses import dataclass, field  # Declarative, comparable value objects.
from typing import Any  # Loose typing for the raw tier payload.


@dataclass
class AddressRow:
    """One parsed, sanitized CSV row (tab-delimited, header-less customer file)."""

    serial: str  # Col 0: Juniper device serial (numeric string); required, non-empty.
    model: str  # Col 1: device model (e.g. SSR130); display only.
    address: str  # Col 2: street address; sanitized (newlines removed, ws collapsed).
    city: str  # Col 3: city name.
    state: str  # Col 4: 2-letter state code.
    zip_code: str  # Col 5: 5-digit ZIP.


@dataclass
class MatchedSite:
    """A CSV row resolved (or not) to a Mist site, optionally SNMP-enriched."""

    site_id: str | None = None  # Mist site UUID; None when unmatched.
    site_name: str | None = None  # Display name; None when unmatched.
    mist_address: dict[str, Any] = field(default_factory=dict)  # {address,city,state,zip} from the site.
    snmp_location: str | None = None  # Filled by SNMPLocationEnricher; None/(none) when absent.
    match_strategy: str = "unmatched"  # One of: serial | fuzzy | unmatched.
    match_confidence: float = 0.0  # 1.0 serial; rapidfuzz score/100 fuzzy; 0.0 unmatched.


@dataclass
class ResolverResult:
    """Output of a single address-resolution attempt (any tier).

    Field names and ``source`` values match the data-model contract so the
    full ``AddressResolver`` can persist/cache results without divergence.
    """

    query: str  # The query string sent to the resolution tier.
    canonical_address: str | None = None  # Resolved address; ``None`` => NO_RESULT.
    source: str = "mist_ui"  # One of: internal | nominatim | mist_ui | cache.
    confidence: float = 0.0  # Heuristic 0.0-1.0 confidence in the result.
    raw_response: dict[str, Any] = field(default_factory=dict)  # Raw tier payload (cached as raw_json).
    ambiguous: bool = False  # True when multiple plausible results (mall) -> drives AMBIGUOUS.


@dataclass
class AuditResult:
    """Per-row result driving BOTH the terminal table and the saved CSV."""

    address_row: AddressRow  # Original CSV input row.
    matched_site: MatchedSite  # Match outcome (+ SNMP enrichment).
    resolver_result: ResolverResult | None = None  # None for UNMATCHED rows (no resolution attempted).
    issue_type: str = "UNMATCHED"  # Exactly one of the eight classification states.
    suggested_address: str = ""  # Best correction to display (full value; truncated only in terminal).
    source: str = "-"  # Display label for the Source column (Internal/Nominatim/Mist UI/Cache/-).


@dataclass
class AuditCounters:
    """Lightweight run-summary counters (fresh per run; not persisted)."""

    total_rows: int = 0  # CSV rows emitted by the ingester.
    parse_failures: int = 0  # Rows skipped (empty/non-numeric serial).
    by_state: dict[str, int] = field(default_factory=dict)  # Count per classification state.
    cache_hits: int = 0  # Resolver cache hits (DEBUG-visible).
    external_calls: int = 0  # Nominatim + UI calls actually made.


@dataclass
class ResolveCandidates:
    """Single config object passed to ``AddressResolver.resolve`` (<=5-param rule)."""

    mist_address: dict[str, Any] = field(default_factory=dict)  # Current Mist site address dict.
    csv_address: dict[str, Any] = field(default_factory=dict)  # Customer CSV address dict.
    snmp_location: str | None = None  # SNMP location string (extra reference), if any.
    business_name: str = ""  # Optional business-name prefix for queries.
    ui_geocode: bool = False  # Whether Tier-3 UI geocoding is permitted for this row.


@dataclass
class UIGeocoderConfig:
    """Browser-connection and bounding settings for ``MistUIGeocoder``.

    Defaults reflect a Zscaler-restricted Windows host: Playwright cannot
    download its own Chromium, so we drive the system-installed Edge channel
    or take over an already-authenticated browser over CDP.
    """

    connect_mode: str = "attach"  # "attach" (CDP takeover) or "launch" (fresh Edge + interactive login).
    cdp_endpoint: str = "http://localhost:9222"  # DevTools endpoint of the operator's debuggable browser.
    browser_channel: str = "msedge"  # System browser channel; avoids the Zscaler-blocked Chromium CDN.
    dashboard_url: str = "https://manage.mist.com/"  # Regional Mist cloud login/landing URL (override per cloud).
    headless: bool = False  # Must be visible so the operator can log in / observe the takeover.
    per_lookup_timeout_s: float = 20.0  # Hard per-lookup ceiling (UI_GEOCODE_TIMEOUT_SECONDS).
    max_lookups: int = 50  # Per-run cap on Tier-3 lookups (UI_GEOCODE_MAX_LOOKUPS).
    politeness_delay_s: float = 1.0  # >=1 req/sec politeness toward Google Places.
