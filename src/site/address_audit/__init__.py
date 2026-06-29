"""Site address-audit subpackage (feature 1003-site-address-audit).

This package reads a customer-provided tab-delimited CSV, matches each row to a
Mist site by device serial number, enriches with SNMP location data, and
resolves/validates the address through free tiers (internal comparison ->
Nominatim -> optional Mist-dashboard UI automation). It is READ-ONLY in v1.

Only the Tier-3 browser-automation foundation (``MistUIGeocoder``) and the
shared dataclasses ship in this first slice; the remaining classes
(CSVAddressIngester, SiteMatchingEngine, AddressResolver, AddressAuditEngine,
...) land with the full implementation per ``specs/1003-site-address-audit``.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

from src.site.address_audit.models import ResolverResult, UIGeocoderConfig  # Shared dataclasses.
from src.site.address_audit.ui_geocoder import MistUIGeocoder  # Tier-3 browser geocoder.

__all__ = [  # Public surface of the subpackage for clean imports.
    "ResolverResult",  # Result of one address-resolution attempt.
    "UIGeocoderConfig",  # Browser-connection + bounds for the UI tier.
    "MistUIGeocoder",  # Launch/takeover browser driver for the Mist address screen.
]
