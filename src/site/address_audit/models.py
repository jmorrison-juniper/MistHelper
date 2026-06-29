"""Dataclasses for the address-audit feature (1003-site-address-audit).

Only the entities required by the Tier-3 UI geocoder ship in this first slice:
``ResolverResult`` (the common output of any resolution tier) and
``UIGeocoderConfig`` (browser-connection + bounding settings). The remaining
audit dataclasses (AddressRow, MatchedSite, AuditResult, AuditCounters) land
with the full feature implementation and MUST keep ``ResolverResult`` field
names aligned with ``specs/1003-site-address-audit/data-model.md``.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

from dataclasses import dataclass, field  # Declarative, comparable value objects.
from typing import Any  # Loose typing for the raw tier payload.


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
