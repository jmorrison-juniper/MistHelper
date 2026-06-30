"""Site address-audit subpackage (feature 1003-site-address-audit).

Reads a customer-provided tab-delimited CSV, matches each row to a Mist site by
device serial number, enriches with SNMP location data, and resolves/validates
the address through free tiers (internal comparison -> Nominatim -> optional
Mist-dashboard UI automation). READ-ONLY in v1: no Mist site record is written.

``AddressAuditEngine`` is the menu entry point; the remaining classes are its
collaborators. ``AddressCorrector`` is an inert, unregistered write-back stub.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

from src.site.address_audit.address_corrector import AddressCorrector  # Deferred write-back stub.
from src.site.address_audit.address_resolver import AddressResolver  # Tiered resolver.
from src.site.address_audit.audit_engine import AddressAuditEngine  # Orchestrator + menu entry.
from src.site.address_audit.audit_reporter import AddressAuditReporter  # CSV report writer.
from src.site.address_audit.comparison_display import ComparisonTableRenderer  # Table + prompt.
from src.site.address_audit.csv_ingester import CSVAddressIngester  # CSV parser.
from src.site.address_audit.models import (  # Shared dataclasses.
    AddressRow,
    AuditCounters,
    AuditResult,
    MatchedSite,
    ResolveCandidates,
    ResolverResult,
    UIGeocoderConfig,
)
from src.site.address_audit.site_matcher import SiteMatchingEngine  # Serial/fuzzy matcher.
from src.site.address_audit.snmp_enricher import SNMPLocationEnricher  # SNMP enrichment.
from src.site.address_audit.ui_geocoder import MistUIGeocoder  # Tier-3 browser geocoder.

__all__ = [  # Public surface of the subpackage for clean imports.
    "AddressAuditEngine",  # Menu entry point.
    "AddressCorrector",  # Deferred write-back stub.
    "AddressResolver",  # Tiered address resolver.
    "AddressAuditReporter",  # CSV report writer.
    "ComparisonTableRenderer",  # Comparison table + post-table prompt.
    "CSVAddressIngester",  # Tab-delimited CSV parser.
    "SiteMatchingEngine",  # Serial/fuzzy site matcher.
    "SNMPLocationEnricher",  # SNMP location enrichment.
    "MistUIGeocoder",  # Launch/takeover browser driver.
    "AddressRow",  # Parsed CSV row.
    "MatchedSite",  # Matched-site record.
    "ResolverResult",  # Resolution result.
    "AuditResult",  # Per-row audit record.
    "AuditCounters",  # Run summary counters.
    "ResolveCandidates",  # Resolver input config.
    "UIGeocoderConfig",  # UI-geocoder config.
]
