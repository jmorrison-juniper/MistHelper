"""Audit orchestrator for the address-audit feature (1003-site-address-audit).

``AddressAuditEngine`` is the single menu entry point. It loads the customer CSV,
matches each row to a Mist site (serial golden key, fuzzy fallback), enriches with
SNMP location, resolves/validates the address through the free tiers, classifies
each row into one of nine states, renders the comparison table, and offers to save
the results to CSV. The audit itself is read-only; afterwards the operator may
opt in to push corrected addresses back to Mist via ``AddressCorrector``, gated by
a batch confirmation and a per-site ``[y/N]`` before/after review.

The orchestration is split into small private helpers so every method stays
within the Five-Item Rule. The classification helpers (``_classify`` and its
companions) are pure and unit-testable without any live API.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import glob  # Discover candidate CSV/TSV files in data/.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # Path handling and environment access.
import re  # Address normalization / suite extraction in classification.
import sys  # Detect a non-interactive stdout to suppress the progress bar.
from typing import Any  # Loose typing for Mist API records.

import mistapi  # Mist API SDK (sole Mist interface; hard dependency of MistHelper).

from src.site.address_audit.address_corrector import AddressCorrector  # Optional Mist write-back.
from src.site.address_audit.address_resolver import AddressResolver  # Tiered resolver.
from src.site.address_audit.audit_reporter import AddressAuditReporter  # CSV writer.
from src.site.address_audit.comparison_display import ComparisonTableRenderer  # Table + prompt.
from src.site.address_audit.csv_ingester import CSVAddressIngester  # CSV parser.
from src.site.address_audit.models import (  # Shared dataclasses.
    AddressRow,
    AuditResult,
    MatchedSite,
    ResolveCandidates,
    UIGeocoderConfig,
)
from src.site.address_audit.site_matcher import SiteMatchingEngine  # Serial/fuzzy matcher.
from src.site.address_audit.snmp_enricher import SNMPLocationEnricher  # SNMP enrichment.
from src.utils.input_utils import InputUtils  # EOF-safe operator prompts.

try:  # Optional dependency: tqdm renders the per-row progress bar.
    from tqdm import tqdm  # Progress bar for the resolve loop.
except ImportError:  # pragma: no cover -- exercised only when tqdm is absent.
    tqdm = None  # type: ignore[assignment]  # Sentinel; _progress degrades to a plain iterator.

_DATA_DIR = "data"  # Directory scanned for the customer CSV.
_SUITE_PATTERN = (  # Suite token with a capture group for the unit id (state-safe).
    r"\b(?:ste|suite|unit|apt|apartment|bldg|building|space|spc|rm|room|lot)\b\.?\s*#?\s*([\w-]+)" r"|#\s*(\d[\w-]*)"
)
_DIRECTIONALS = {  # Street-name directional tokens, normalized to their abbreviation.
    "n": "N",
    "s": "S",
    "e": "E",
    "w": "W",
    "ne": "NE",
    "nw": "NW",
    "se": "SE",
    "sw": "SW",
    "north": "N",
    "south": "S",
    "east": "E",
    "west": "W",
    "northeast": "NE",
    "northwest": "NW",
    "southeast": "SE",
    "southwest": "SW",
}


class AddressAuditEngine:
    """Orchestrate the read-only CSV address audit and render the comparison."""

    def __init__(
        self,
        ingester: CSVAddressIngester | None = None,
        enricher: SNMPLocationEnricher | None = None,
        renderer: ComparisonTableRenderer | None = None,
        reporter: AddressAuditReporter | None = None,
    ) -> None:
        """Store collaborators (injectable for tests; sensible defaults otherwise)."""
        self._ingester = ingester or CSVAddressIngester()  # CSV parser.
        self._enricher = enricher or SNMPLocationEnricher()  # SNMP enrichment.
        self._renderer = renderer or ComparisonTableRenderer()  # Table + prompt.
        self._reporter = reporter or AddressAuditReporter()  # CSV report writer.

    def run(self, apisession: Any, org_id: str) -> None:
        """Menu entry point: drive the full read-only audit pipeline end-to-end.

        The Mist site address, the SNMP location variable, and the customer CSV
        are all treated as *hints* -- none is authoritative. The resolver fuses
        them into one best-guess query and prefers an external verifier
        (OpenStreetMap, plus Tier-3 browser geocoding when a debuggable browser
        is reachable) to deduce the true, shippable address.
        """
        ui_geocode = self._ui_geocode_enabled()  # Tier-3 web geocoding: env-gated, default auto, no CLI flag.
        logging.info("Starting site address audit (tier3_geocode=%s)", ui_geocode)  # Action-log start.
        csv_path = self._select_csv_file()  # Pick the customer CSV from data/.
        if csv_path is None:  # No CSV present -> nothing to audit.
            print("No CSV/TSV files found in data/. Drop your address file there and retry.")  # Inform.
            return  # Clean early return.
        rows, failures = self._ingester.load(csv_path)  # Parse the CSV into rows.
        if not rows:  # Every row was malformed/empty-serial.
            print(f"No valid rows parsed from {csv_path} ({failures} skipped).")  # Inform operator.
            return  # Nothing further to do.
        business = self._resolve_business_name()  # Business-name prefix (env or prompt).
        results = self._audit_rows(apisession, org_id, rows, business, ui_geocode)  # Core pipeline.
        self._renderer.render(results)  # Render the comparison table.
        self._finish(results, apisession)  # Post-table save/quit prompt + optional write-back.

    def _audit_rows(
        self,
        apisession: Any,
        org_id: str,
        rows: list[AddressRow],
        business: str,
        ui_geocode: bool,
    ) -> list[AuditResult]:
        """Load Mist data, match/enrich/resolve every row, and classify the outcomes."""
        inventory_by_serial, sites_by_id, sites_list = self._load_mist_data(apisession, org_id)  # One read.
        matcher = SiteMatchingEngine(inventory_by_serial, sites_by_id, self._fuzzy_threshold())  # In-memory matcher.
        matched = self._match_sites(rows, matcher, sites_list)  # Serial -> fuzzy fallback per row.
        self._enrich_sites(apisession, matched)  # Fill SNMP location on matched sites.
        resolver = self._build_resolver(ui_geocode)  # Tiered resolver (+ optional Tier 3).
        return self._resolve_and_classify(rows, matched, resolver, business, ui_geocode)  # Build results.

    def _select_csv_file(self) -> str | None:
        """Find CSV/TSV files in data/; auto-pick one, prompt when several, else None."""
        candidates = sorted(glob.glob(os.path.join(_DATA_DIR, "*.csv")) + glob.glob(os.path.join(_DATA_DIR, "*.tsv")))
        if not candidates:  # No files at all.
            logging.debug("No CSV/TSV files found in %s", _DATA_DIR)  # Trace the empty case.
            return None  # Signal "nothing to audit".
        if len(candidates) == 1:  # Exactly one -> auto-select.
            logging.info("Auto-selected CSV file: %s", candidates[0])  # Action-log the pick.
            return candidates[0]  # Use it without prompting.
        return self._prompt_csv_choice(candidates)  # Multiple -> ask the operator.

    def _prompt_csv_choice(self, candidates: list[str]) -> str:
        """Prompt the operator to choose one CSV from a numbered list."""
        print("Available CSV files in data/:")  # Header for the choices.
        for index, path in enumerate(candidates, start=1):  # Enumerate options 1..N.
            print(f"  [{index}] {os.path.basename(path)}")  # Show each filename.
        while True:  # Loop until a valid selection is made.
            raw = InputUtils.safe_input("Select file number: ", context="address_audit_csv_pick").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(candidates):  # Valid in-range integer.
                return candidates[int(raw) - 1]  # Return the chosen path.
            print(f"Invalid selection. Please enter a number between 1 and {len(candidates)}: ")  # Re-prompt.

    @staticmethod
    def _resolve_business_name() -> str:
        """Read BUSINESS_NAME from the environment, or prompt once (skippable)."""
        configured = os.environ.get("BUSINESS_NAME", "").strip()  # Preferred .env source.
        if configured:  # Already configured -> use it silently.
            return configured  # Business name from environment.
        return InputUtils.safe_input(  # Otherwise prompt once; Enter skips the prefix.
            'Enter business name for geocoding queries (e.g. "Starbucks"), or press Enter to skip: ',
            context="address_audit_business_name",
        ).strip()

    def _load_mist_data(
        self, apisession: Any, org_id: str
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
        """Read org inventory + sites once and build serial/site lookup maps."""
        logging.info("Loading Mist inventory and sites for org %s", org_id)  # Action-log start.
        devices = self._get_all(mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id), apisession)
        sites = self._get_all(mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000), apisession)
        inventory_by_serial = {d.get("serial", ""): d for d in devices if d.get("serial")}  # serial -> device.
        sites_by_id = {s.get("id", ""): s for s in sites if s.get("id")}  # site_id -> site.
        logging.debug("Loaded %d devices, %d sites", len(inventory_by_serial), len(sites_by_id))  # Action-log.
        return inventory_by_serial, sites_by_id, sites  # Hand back maps + raw site list (fuzzy needs it).

    @staticmethod
    def _get_all(response: Any, apisession: Any) -> list[dict[str, Any]]:
        """Fully paginate a Mist API response into a list (empty on failure)."""
        try:
            return mistapi.get_all(response=response, mist_session=apisession) or []  # Exhaust pagination.
        except Exception as exc:  # noqa: BLE001 -- a read failure must not crash the audit.
            logging.warning("Mist pagination failed: %s", exc)  # Log and degrade to empty.
            return []  # Return nothing so the audit continues.

    def _match_sites(
        self, rows: list[AddressRow], matcher: SiteMatchingEngine, sites_list: list[dict[str, Any]]
    ) -> list[MatchedSite]:
        """Match each row by serial; fall back to fuzzy address match on a miss."""
        matched: list[MatchedSite] = []  # Per-row match outcomes.
        for row in rows:  # Walk every parsed CSV row.
            result = matcher.match_serial(row.serial)  # Try the golden-key serial match first.
            if result.match_strategy == "unmatched":  # Serial missed -> try fuzzy address.
                result = matcher.match_fuzzy(self._csv_text(row), sites_list)  # Fuzzy fallback.
            matched.append(result)  # Record the outcome.
        return matched  # Hand back one MatchedSite per row.

    def _enrich_sites(self, apisession: Any, matched: list[MatchedSite]) -> None:
        """Populate ``snmp_location`` on each matched site (deduped, fail-soft)."""
        settings_cache: dict[str, dict[str, Any]] = {}  # site_id -> fetched settings record.
        for site in matched:  # Walk every matched site.
            if not site.site_id:  # Skip unmatched rows.
                continue  # Nothing to enrich.
            record = self._site_settings(apisession, site.site_id, settings_cache)  # Fetch (cached).
            site.snmp_location = self._enricher.enrich(record)  # Best SNMP location (or None).

    def _site_settings(self, apisession: Any, site_id: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Fetch a site's settings (vars + snmp_config), memoized per site_id."""
        if site_id in cache:  # Already fetched this run.
            return cache[site_id]  # Reuse the cached record.
        try:
            response = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)  # Site settings call.
            record = getattr(response, "data", {}) or {}  # Settings payload (vars, snmp_config).
        except Exception as exc:  # noqa: BLE001 -- enrichment is best-effort.
            logging.debug("Site settings fetch failed for %s: %s", site_id, exc)  # Trace and degrade.
            record = {}  # Empty record -> enricher yields None.
        record.setdefault("id", site_id)  # Carry the id for log context.
        cache[site_id] = record  # Memoize for any repeat site_id.
        return record  # Hand back the settings record.

    def _build_resolver(self, ui_geocode: bool) -> AddressResolver:
        """Construct the tiered resolver, wiring the Tier-3 UI geocoder when enabled."""
        ui_geocoder = None  # Default: Tier 3 disabled.
        if ui_geocode:  # Tier 3 permitted (env default auto) -> try to attach a browser.
            ui_geocoder = self._make_ui_geocoder()  # Build and connect the browser geocoder (fail-soft).
        skip_ssl = self._skip_ssl_verify()  # Skip cert checks behind corporate SSL inspection (Zscaler).
        return AddressResolver(skip_ssl_verify=skip_ssl, ui_geocoder=ui_geocoder)  # Resolver with optional Tier 3.

    @staticmethod
    def _geocode_mode() -> str:
        """Return the Tier-3 connection mode from a single env knob (no CLI flag).

        ``ADDRESS_AUDIT_GEOCODE`` accepts: ``off`` (disable Tier 3), ``auto``
        (default -- take over a debuggable browser if present, else spawn one and
        guide login), ``attach`` (take over only; operator pre-started Edge), or
        ``launch`` (Playwright launches a fresh Edge). Unknown values fall back to
        ``auto`` so a typo never disables suite discovery.
        """
        raw = os.environ.get("ADDRESS_AUDIT_GEOCODE", "auto").strip().lower()  # Single env knob; default auto.
        if raw in ("off", "0", "no", "false", "none", "disabled"):  # Any disable token.
            return "off"  # Tier 3 turned off.
        if raw in ("attach", "launch", "auto"):  # Explicit, recognized mode.
            return raw  # Honor the operator's choice.
        return "auto"  # Unknown value -> safe default keeps suite discovery on.

    @staticmethod
    def _ui_geocode_enabled() -> bool:
        """Return whether Tier-3 web geocoding may run (env-gated, default on, no CLI flag).

        Tier 3 engages automatically when a browser is reachable (taking one over
        or spawning one) and degrades silently to Tier 1/2 otherwise, so routine
        runs are never disrupted. Set ``ADDRESS_AUDIT_GEOCODE=off`` to skip it.
        """
        return AddressAuditEngine._geocode_mode() != "off"  # Enabled for every non-off mode.

    @staticmethod
    def _skip_ssl_verify() -> bool:
        """Return whether to skip TLS verification for the public Nominatim call.

        Defaults to True because the deployment environment sits behind Zscaler
        SSL inspection, whose MITM cert otherwise breaks the OpenStreetMap call.
        Set ``MIST_SKIP_SSL_VERIFY=false`` to enforce verification (non-Zscaler hosts).
        """
        raw = os.environ.get("MIST_SKIP_SSL_VERIFY", "true").strip().lower()  # Env override; default on.
        return raw not in ("false", "0", "no", "off")  # Any falsey token re-enables verification.

    @staticmethod
    def _make_ui_geocoder() -> Any:
        """Build and connect a ``MistUIGeocoder`` from env config; ``None`` if unavailable."""
        from src.site.address_audit.ui_geocoder import MistUIGeocoder  # Lazy: optional Playwright.

        geocoder = MistUIGeocoder(AddressAuditEngine._ui_config())  # Env-driven auto/attach/launch config.
        if not geocoder.connect():  # Establish the browser session (fail-soft).
            logging.info(  # No browser is the normal case; degrade quietly to Tier 1/2.
                "Tier-3 web geocoder not available; using internal + OpenStreetMap hints only. "
                "Set ADDRESS_AUDIT_GEOCODE=off to skip, or 'launch' to force a fresh Edge."
            )
            return None  # Disable Tier 3 for this run.
        geocoder.ensure_location_field_ready()  # Guide the operator to a page with the Location Search box.
        return geocoder  # Connected geocoder ready for suite-discovery lookups.

    @staticmethod
    def _ui_config() -> UIGeocoderConfig:
        """Build a ``UIGeocoderConfig`` from environment overrides (with safe defaults)."""
        config = UIGeocoderConfig()  # Start from the Zscaler-safe defaults.
        config.connect_mode = AddressAuditEngine._geocode_mode()  # off is filtered earlier; auto/attach/launch here.
        config.dashboard_url = os.environ.get("MIST_DASHBOARD_URL", config.dashboard_url).strip()  # Cloud region.
        config.per_lookup_timeout_s = AddressAuditEngine._env_float(  # Per-lookup timeout override.
            "UI_GEOCODE_TIMEOUT_SECONDS", config.per_lookup_timeout_s
        )
        config.max_lookups = int(AddressAuditEngine._env_float("UI_GEOCODE_MAX_LOOKUPS", config.max_lookups))  # Cap.
        return config  # Hand back the env-merged config.

    @staticmethod
    def _fuzzy_threshold() -> float:
        """Return the rapidfuzz score cutoff from env (default 85)."""
        return AddressAuditEngine._env_float("FUZZY_MATCH_THRESHOLD", 85.0)  # .env override or default.

    @staticmethod
    def _env_float(name: str, default: float) -> float:
        """Parse a float env var, falling back to ``default`` on absence/parse error."""
        raw = os.environ.get(name, "").strip()  # Read the raw env value.
        if not raw:  # Unset or blank -> use the default.
            return default  # Caller's default.
        try:
            return float(raw)  # Parse the configured numeric value.
        except ValueError:  # Malformed value must not crash the audit.
            logging.warning("Invalid %s=%r; using default %s", name, raw, default)  # Warn and fall back.
            return default  # Safe default.

    def _resolve_and_classify(
        self,
        rows: list[AddressRow],
        matched: list[MatchedSite],
        resolver: AddressResolver,
        business: str,
        ui_geocode: bool,
    ) -> list[AuditResult]:
        """Resolve + classify every row, returning one ``AuditResult`` per CSV row."""
        results: list[AuditResult] = []  # Accumulator (100% row accountability).
        for row, site in self._progress(list(zip(rows, matched, strict=False)), len(rows)):  # Iterate w/ progress.
            results.append(self._build_audit_result(row, site, resolver, business, ui_geocode))  # One result.
        logging.debug("Classified %d audit rows", len(results))  # Action-log completion.
        return results  # Hand back all results.

    def _build_audit_result(
        self,
        row: AddressRow,
        site: MatchedSite,
        resolver: AddressResolver,
        business: str,
        ui_geocode: bool,
    ) -> AuditResult:
        """Resolve one row's address and wrap it in a classified ``AuditResult``."""
        if site.match_strategy == "unmatched":  # No site -> no resolution attempted.
            return AuditResult(address_row=row, matched_site=site, issue_type="UNMATCHED", source="-")
        candidates = ResolveCandidates(  # Bundle the inputs for the resolver.
            mist_address=site.mist_address,  # Current Mist address.
            csv_address=self._csv_to_dict(row),  # Customer CSV address.
            snmp_location=site.snmp_location,  # SNMP reference (may be None).
            business_name=business,  # Optional query prefix.
            ui_geocode=ui_geocode,  # Whether Tier 3 is permitted.
        )
        resolver_result = resolver.resolve(candidates)  # Run the tier cascade (fail-soft).
        issue = self._classify(site.mist_address, self._csv_to_dict(row), site.snmp_location, resolver_result)
        return AuditResult(  # Compose the per-row result.
            address_row=row,  # Original CSV row.
            matched_site=site,  # Match outcome.
            resolver_result=resolver_result,  # Resolver output.
            issue_type=issue,  # Classification state.
            suggested_address=resolver_result.canonical_address or "",  # Suggestion (full).
            source=self._source_label(resolver_result),  # Display source label.
        )

    def _classify(
        self,
        mist_addr: dict[str, Any],
        csv_addr: dict[str, Any],
        snmp_loc: str | None,
        resolver_result: Any,
    ) -> str:
        """Return exactly one of the nine classification states for a resolved row."""
        if resolver_result is None or resolver_result.canonical_address is None:  # No external result.
            return self._classify_internal(mist_addr, csv_addr, snmp_loc)  # Fall back to internal signals.
        if resolver_result.ambiguous:  # Multiple plausible candidates (mall scenario).
            return "AMBIGUOUS"  # Needs manual disambiguation.
        mist_street = mist_addr.get("address", "")  # Mist street line is the stable anchor.
        canonical = resolver_result.canonical_address  # Suggested/validated address (may be prefixed/partial).
        if not self._same_street(mist_street, canonical):  # Street number/name does not line up.
            return "WRONG_STREET"  # Beyond a suite-level difference.
        if self._missing_house_number(mist_street, canonical):  # Mist street lacks the house number we found.
            return "MISSING_NUMBER"  # Incomplete Mist address -> surface, do not call it a match.
        if self._addresses_agree(mist_street, canonical):  # Same street AND same suite.
            return "ADDRESS_MATCH"  # No change needed.
        return self._classify_suite(mist_street, canonical)  # Same street: compare suites.

    @staticmethod
    def _missing_house_number(mist_street: str, candidate: str) -> bool:
        """Return True when Mist's street lacks a house number that the candidate supplies.

        Both inputs are full formatted address strings ("STREET, CITY, ST ZIP"),
        so we inspect only the leading street segment (before the first comma) and
        require a *leading* digit there. This avoids mistaking a trailing ZIP for a
        house number -- e.g. Mist ``S Federal Hwy, Fort Pierce, FL 34982`` has no
        house number even though the ZIP contains digits.
        """
        mist_lead = re.match(r"\s*\d", mist_street.split(",", 1)[0])  # Leading digit of the Mist street.
        cand_lead = re.match(r"\s*\d", candidate.split(",", 1)[0])  # Leading digit of the candidate street.
        return bool(cand_lead) and not bool(mist_lead)  # Missing only when the candidate has one and Mist does not.

    def _classify_internal(self, mist_addr: dict[str, Any], csv_addr: dict[str, Any], snmp_loc: str | None) -> str:
        """Classify on internal CSV/SNMP signals alone when no external result exists."""
        mist_street = mist_addr.get("address", "")  # Mist street anchor.
        candidate = snmp_loc or csv_addr.get("address", "")  # Best internal candidate (SNMP preferred).
        if candidate and self._has_suite_discrepancy(mist_street, candidate):  # Internal adds a missing suite.
            return "MISSING_SUITE"  # The common strip-mall case, caught without any external call.
        return "NO_RESULT"  # Internal inconclusive and nothing external resolved.

    def _classify_suite(self, mist_street: str, canonical: str) -> str:
        """Classify a same-street pair by comparing suite/unit specificity."""
        mist_suite = self._suite(mist_street)  # Mist's suite token (or "").
        cand_suite = self._suite(canonical)  # Candidate's suite token (or "").
        if cand_suite and not mist_suite:  # Candidate adds a suite Mist lacks.
            return "MISSING_SUITE"  # The common strip-mall case.
        if mist_suite and not cand_suite:  # Mist already carries a suite the candidate lacks.
            return "MIST_BETTER"  # Mist is the more specific source.
        return "CSV_BETTER"  # Both specify but differ -> candidate is the suggested correction.

    def _addresses_agree(self, mist_street: str, canonical: str) -> bool:
        """Return True when both refer to the same street AND carry the same suite."""
        same_suite = self._suite(mist_street) == self._suite(canonical)  # Compare suite tokens.
        return self._same_street(mist_street, canonical) and same_suite  # Agree only when both match.

    def _same_street(self, mist_street: str, candidate: str) -> bool:
        """Return True when the candidate covers the Mist house number and a street word.

        Robust to SNMP/geocoder strings that add a store-number prefix or drop the
        city/ZIP: anchors on the Mist house number plus at least one street-name word.
        A conflicting leading directional (Mist 'E Jefferson' vs web 'West Jefferson')
        is treated as a different street so a wrong-side address never reads as a match.
        """
        mist_number = self._house_number(mist_street)  # Mist street's house number.
        if mist_number and mist_number not in self._all_numbers(candidate):  # House number must appear.
            return False  # Different building number -> different street.
        mist_dir = self._leading_directional(mist_street)  # Directional right after the house number.
        cand_dir = self._leading_directional(candidate)  # Same for the candidate (city dirs ignored).
        if mist_dir and cand_dir and mist_dir != cand_dir:  # Opposite directionals (E vs W).
            return False  # Different side of the street -> different street.
        overlap = self._name_words(mist_street) & self._name_words(candidate)  # Shared street words.
        return bool(overlap)  # Same street when at least one street-name word matches.

    @staticmethod
    def _leading_directional(street: str) -> str:
        """Return the directional immediately after the house number, normalized, or ''.

        Only the leading directional (e.g. the ``E`` in ``1606 E Jefferson``) is
        considered, so a directional inside a later city name (``West Palm Beach``)
        never triggers a false street mismatch.
        """
        tokens = re.sub(r"[^A-Za-z0-9 ]", " ", street).split()  # Punctuation-free tokens.
        if not tokens:  # Empty street line.
            return ""  # No directional.
        index = 1 if tokens[0].isdigit() else 0  # Skip a leading house number.
        if index >= len(tokens):  # Nothing past the house number.
            return ""  # No directional.
        return _DIRECTIONALS.get(tokens[index].lower(), "")  # Normalized directional or ''.

    def _has_suite_discrepancy(self, base: str, candidate: str) -> bool:
        """Return True when ``candidate`` carries a suite the ``base`` address lacks."""
        return bool(self._suite(candidate)) and not self._suite(base)  # Candidate-only suite.

    def _name_words(self, text: str) -> set[str]:
        """Return the comparable street-name tokens (suite-stripped).

        Includes alphabetic words (``jefferson``) AND ordinal/alphanumeric street
        names (``107th``, ``a1a``) so a numeric-named street still matches when
        Google spells out ``NW``/``Avenue``; the pure-digit house number is
        excluded so two different streets at the same number never match on it.
        """
        without_suite = re.sub(_SUITE_PATTERN, " ", text.lower())  # Drop the suite token.
        normalized = self._normalize(without_suite)  # Lowercase, de-punctuate, collapse.
        words: set[str] = set()  # Accumulate comparable name tokens.
        for token in normalized.split():  # Walk every token.
            if token.isalpha() and len(token) >= 2:  # Street-name words (military, jefferson).
                words.add(token)  # Keep the word.
            elif any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token):  # Ordinals: 107th, a1a.
                words.add(token)  # Keep numeric-named streets (pure digits like the house number excluded).
        return words  # Comparable street-name token set.

    @staticmethod
    def _house_number(text: str) -> str:
        """Return the first numeric token (the house number) of a street line, or ''."""
        for token in re.sub(r"[^0-9 ]", " ", text).split():  # Walk numeric tokens left-to-right.
            return token  # The first number is the house number.
        return ""  # No numeric token present.

    @staticmethod
    def _all_numbers(text: str) -> set[str]:
        """Return every numeric token in a string (house number, store number, ZIP...)."""
        return set(re.sub(r"[^0-9 ]", " ", text).split())  # All digit runs as strings.

    @staticmethod
    def _suite(text: str) -> str:
        """Extract a normalized suite/unit identifier from an address, or ''."""
        match = re.search(_SUITE_PATTERN, text.lower())  # Find the first suite token.
        if not match:  # No suite token present.
            return ""  # Signal absence.
        return (match.group(1) or match.group(2) or "").strip()  # Unit id from whichever alt matched.

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, drop punctuation, and collapse whitespace for comparison."""
        cleaned = re.sub(r"[^a-z0-9 ]", " ", text.lower())  # Remove punctuation.
        return " ".join(cleaned.split())  # Collapse whitespace.

    @staticmethod
    def _source_label(resolver_result: Any) -> str:
        """Map a resolver source code to a human-readable Source-column label."""
        labels = {  # Source-code -> display label.
            "internal": "Internal",  # Tier 1 internal comparison.
            "nominatim": "Nominatim",  # Tier 2 OSM validation.
            "mist_ui": "Mist UI",  # Tier 3 dashboard automation.
            "cache": "Cache",  # Served from the SQLite cache.
        }
        if resolver_result is None or resolver_result.canonical_address is None:  # No suggestion.
            return "-"  # Placeholder when nothing was resolved.
        base = labels.get(resolver_result.source, "-")  # Tier label for the resolved source.
        if resolver_result.source == "internal" and getattr(resolver_result, "street_validated", False):
            return "Internal+OSM"  # Internal suite, street externally confirmed by OpenStreetMap.
        return base  # Mapped label or placeholder.

    def _finish(self, results: list[AuditResult], apisession: Any) -> None:
        """Save the report (operator's choice), then optionally write corrections back to Mist."""
        action = self._renderer.prompt_post_table(results)  # Ask save vs quit.
        if action != "save":  # Operator quit without saving.
            print("No file saved. Exiting address audit.")  # Quit branch confirmation.
            return  # No write-back when nothing was saved.
        path = self._reporter.save(results)  # Write the timestamped comparison CSV.
        print(f"Saved to {path}")  # Confirm the written path.
        self._offer_write_back(results, apisession)  # Offer to push corrections to Mist.

    def _offer_write_back(self, results: list[AuditResult], apisession: Any) -> None:
        """Gate, then run, the optional per-site address write-back to Mist."""
        corrector = self._make_corrector(apisession)  # Build the write-back collaborator.
        targets = corrector.correctable(results)  # Rows with a pushable correction.
        if not targets:  # Nothing to correct.
            logging.debug("No correctable rows; skipping write-back offer")  # Trace the no-op.
            return  # Audit ends here.
        prompt = f"\nPush corrected addresses back to Mist for up to {len(targets)} site(s)? [y/N]: "
        choice = InputUtils.safe_input(prompt, context="address_audit_writeback_gate").strip().lower()
        if choice not in ("y", "yes"):  # Operator declined the whole batch.
            print("Skipped write-back. No Mist changes made.")  # Confirm no writes.
            return  # Audit ends here.
        outcomes = corrector.review_and_apply(results)  # Per-site review + push.
        self._maybe_save_corrections(outcomes)  # Offer the before/after report.

    def _maybe_save_corrections(self, outcomes: list[Any]) -> None:
        """Offer to save a before/after report of the reviewed sites."""
        if not outcomes:  # No sites were reviewed.
            return  # Nothing to report.
        choice = (
            InputUtils.safe_input(
                "\nSave a before/after correction report to data/? [y/N]: ", context="address_audit_writeback_report"
            )
            .strip()
            .lower()
        )
        if choice not in ("y", "yes"):  # Operator declined the report.
            print("No correction report saved.")  # Confirm the skip.
            return  # Done.
        path = self._reporter.save_corrections(outcomes)  # Write the before/after CSV.
        print(f"Saved correction report to {path}")  # Confirm the written path.

    @staticmethod
    def _make_corrector(apisession: Any) -> AddressCorrector:
        """Construct the write-back collaborator (separated for test injection)."""
        return AddressCorrector(apisession)  # Real Mist-backed corrector.

    def _progress(self, items: list[Any], total: int) -> Any:
        """Wrap an iterable in a tqdm progress bar when interactive and available."""
        if tqdm is None or not sys.stdout.isatty():  # No tqdm or non-interactive stdout.
            return items  # Plain iteration (no bar).
        return tqdm(items, total=total, desc="Geocoding sites", unit="site")  # Progress bar.

    @staticmethod
    def _csv_to_dict(row: AddressRow) -> dict[str, Any]:
        """Convert a CSV ``AddressRow`` into the resolver's address-dict shape."""
        return {  # Normalized address dict.
            "address": row.address,  # Street.
            "city": row.city,  # City.
            "state": row.state,  # State.
            "zip": row.zip_code,  # ZIP.
        }

    @staticmethod
    def _csv_text(row: AddressRow) -> str:
        """Join a CSV row's address parts into a single fuzzy-match query string."""
        parts = [row.address, row.city, row.state]  # Address components for fuzzy matching.
        return " ".join(part for part in parts if part).strip()  # Skip blanks; trim.

    @staticmethod
    def _format_address(address: dict[str, Any]) -> str:
        """Join an address dict into a single comparable line."""
        parts = [  # Ordered components.
            address.get("address", ""),  # Street.
            address.get("city", ""),  # City.
            address.get("state", ""),  # State.
            str(address.get("zip", "")),  # ZIP.
        ]
        return " ".join(part for part in parts if part).strip()  # Skip blanks; trim.

    def apply_corrections(self, *args: Any, **kwargs: Any) -> None:
        """Deferred write-back surface (OQ-003); intentionally not menu-registered."""
        logging.info(  # Action-log the attempt (and reference args/kwargs for the deferred signature).
            "apply_corrections invoked with %d args / %d kwargs (feature disabled)", len(args), len(kwargs)
        )
        raise NotImplementedError("Address write-back is not enabled in this release.")  # Deferred.
