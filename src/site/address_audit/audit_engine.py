"""Audit orchestrator for the address-audit feature (1003-site-address-audit).

``AddressAuditEngine`` is the single menu entry point. It loads the customer CSV,
matches each row to a Mist site (serial golden key, fuzzy fallback), enriches with
SNMP location, resolves/validates the address through the free tiers, classifies
each row into one of eleven states, renders the comparison table, and offers to save
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
from collections.abc import Callable  # Type of the collaborator factory used by _default.
from contextlib import contextmanager  # Scope the console-log suppression to one run.
from dataclasses import dataclass  # Frozen bundle for audit context (STRUCT-PARAMS fix).
from typing import Any, TypeVar  # Loose typing for Mist API records + generic collaborator default.

import mistapi  # Mist API SDK (sole Mist interface; hard dependency of MistHelper).

from src.site.address_audit.address_corrector import AddressCorrector  # Optional Mist write-back.
from src.site.address_audit.address_resolver import AddressResolver  # Tiered resolver.
from src.site.address_audit.audit_reporter import AddressAuditReporter  # CSV writer.
from src.site.address_audit.business_authority_ingester import (  # Business-authoritative CSV parser + matcher.
    BusinessAuthorityIngester,
)
from src.site.address_audit.comparison_display import ComparisonTableRenderer  # Table + prompt.
from src.site.address_audit.csv_ingester import CSVAddressIngester  # CSV parser.
from src.site.address_audit.models import (  # Shared dataclasses.
    AddressRow,
    AuditResult,
    MatchedSite,
    ResolveCandidates,
    UIGeocoderConfig,
)
from src.site.address_audit.perf import PhaseTimer  # Per-phase timing to expose slow stages.
from src.site.address_audit.site_matcher import SiteMatchingEngine  # Serial/fuzzy matcher.
from src.site.address_audit.snmp_enricher import SNMPLocationEnricher  # SNMP enrichment.
from src.site.address_audit.suite_patterns import (
    SUITE_PATTERN_CAPTURE as _SUITE_PATTERN,
)  # Shared suite detector (capturing).
from src.utils.input_utils import InputUtils  # EOF-safe operator prompts.

try:  # Optional dependency: tqdm renders the per-row progress bar.
    from tqdm import tqdm  # Progress bar for the resolve loop.
except ImportError:  # pragma: no cover -- exercised only when tqdm is absent.
    tqdm = None  # type: ignore[assignment]  # Sentinel; _progress degrades to a plain iterator.

_DATA_DIR = "data"  # Directory scanned for the customer CSV.
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
_INVALID_CHOICE: Any = object()  # WHY: Sentinel from menu parser when raw entry is neither valid index nor 'q'.
_T = TypeVar("_T")  # Generic collaborator type used by the ``_default(injected, factory)`` helper.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print/logging migration.


@dataclass(frozen=True, slots=True)
class _AuditContext:
    """Frozen bundle of per-run audit inputs shared across pipeline helpers.

    Groups the three read-only inputs (business-name prefix, Tier-3 enablement,
    business-authoritative index) that previously travelled as three positional
    arguments through ``_audit_rows``, ``_resolve_and_classify`` and
    ``_build_audit_result``; bundling them keeps every function within the
    five-parameter limit while preserving intent at each call site.
    """

    business: str  # Optional business-name prefix injected into geocoding queries (empty when skipped).
    ui_geocode: bool  # Whether Tier-3 (browser/Google) geocoding may attach for this run.
    authoritative_index: dict[str, dict[str, list[Any]]]  # Pre-indexed authoritative CSV lookup (empty when unused).


class _AddressAuditConsoleFilter(logging.Filter):
    """Console filter that drops log records emitted from the address_audit package.

    The address audit talks to the operator through ``print`` (the comparison
    table, the post-table prompts, the write-back confirmations); every
    ``logging.*`` call it makes is a diagnostic trail destined for
    ``data/script.log``. Attached to the root logger's CONSOLE handlers (and only
    for the duration of a run), this filter keeps that diagnostic noise -- e.g. the
    Nominatim "no result" warnings -- out of the terminal, where it would corrupt
    the tqdm progress bar. File handlers never receive this filter, so the full log
    trail is preserved.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Return False (drop from console) for records whose source is in address_audit."""
        path = (record.pathname or "").replace("\\", "/")  # Normalize separators for a portable check.
        return "/address_audit/" not in path  # Keep every record except this package's own logs.


class AddressAuditEngine:
    """Orchestrate the CSV address audit, render the comparison, and optionally write back."""

    def __init__(
        self,
        ingester: CSVAddressIngester | None = None,
        authority_ingester: BusinessAuthorityIngester | None = None,
        enricher: SNMPLocationEnricher | None = None,
        renderer: ComparisonTableRenderer | None = None,
        reporter: AddressAuditReporter | None = None,
    ) -> None:
        """Store collaborators (injectable for tests; sensible defaults otherwise)."""
        self._ingester = self._default(ingester, CSVAddressIngester)  # CSV parser (default or injected).
        self._authority_ingester = self._default(authority_ingester, BusinessAuthorityIngester)  # Authority parser.
        self._enricher = self._default(enricher, SNMPLocationEnricher)  # SNMP enrichment (default or injected).
        self._renderer = self._default(renderer, ComparisonTableRenderer)  # Table + prompt (default or injected).
        self._reporter = self._default(reporter, AddressAuditReporter)  # CSV report writer (default or injected).

    @staticmethod
    def _default(injected: _T | None, factory: Callable[[], _T]) -> _T:
        """Return ``injected`` when supplied, else construct a fresh ``factory()`` instance."""
        if injected is not None:  # Test/caller supplied an override -> honour it verbatim.
            return injected  # Preserve the injected collaborator without reconstructing it.
        return factory()  # No override -> build the production default lazily so tests never touch it.

    def run(self, apisession: Any, org_id: str) -> None:
        """Menu entry point: drive the full audit pipeline end-to-end.

        The Mist site address, the SNMP location variable, and the customer CSV
        are all treated as *hints* -- none is authoritative. The resolver fuses
        them into one best-guess query and prefers an external verifier
        (OpenStreetMap, plus Tier-3 browser geocoding when a debuggable browser
        is reachable) to deduce the true, shippable address. The whole run is
        wrapped so this feature's diagnostic logging goes to ``data/script.log``
        only, never the terminal (keeps the progress bar clean).
        """
        with self._console_logs_to_file_only():  # Address-audit logs -> file only; console stays clean.
            self._run_pipeline(apisession, org_id)  # Drive the actual audit pipeline.

    def _run_pipeline(self, apisession: Any, org_id: str) -> None:
        """Run the audit pipeline: select CSV, audit, render, and offer write-back."""
        ui_geocode = self._ui_geocode_enabled()  # Tier-3 web geocoding: env-gated, default auto, no CLI flag.
        logger.info("Starting site address audit (tier3_geocode=%s)", ui_geocode)  # Action-log start.
        csv_path = self._select_csv_file()  # Pick the customer CSV from data/.
        if csv_path is None:  # No CSV present -> nothing to audit.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("No CSV/TSV files found in data/. Drop your address file there and retry.")
            return  # Clean early return.
        rows, failures = self._ingester.load(csv_path)  # Parse the CSV into rows.
        if not rows:  # Every row was malformed/empty-serial.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("No valid rows parsed from %s (%s skipped).", csv_path, failures)
            return  # Nothing further to do.
        business_csv_path = self._select_business_csv_file(csv_path)  # Optional second prompt for authoritative CSV.
        ctx = _AuditContext(  # Bundle the three read-only per-run inputs into one frozen record.
            business=self._resolve_business_name(),  # Business-name prefix (env or prompt).
            ui_geocode=ui_geocode,  # Whether Tier-3 web geocoding may attach for this run.
            authoritative_index=self._load_business_authority_index(business_csv_path),  # Pre-indexed authority.
        )
        results = self._audit_rows(apisession, org_id, rows, ctx)  # Core pipeline driven by the bundled context.
        self._renderer.render(results)  # Render the comparison table.
        self._finish(results, apisession)  # Post-table save/quit prompt + optional write-back.

    @contextmanager
    def _console_logs_to_file_only(self) -> Any:
        """Suppress this feature's logging on CONSOLE handlers for the duration of a run.

        Attaches an ``_AddressAuditConsoleFilter`` to every console (stream)
        handler on the root logger, then removes it afterwards. The file handler is
        never touched, so ``data/script.log`` still captures everything -- the
        operator sees only the table, prompts, and progress bar on screen, with the
        Nominatim "no result" warnings and other diagnostics confined to the file.
        """
        handlers = self._console_handlers()  # Snapshot of the console handlers currently attached to root.
        log_filter = _AddressAuditConsoleFilter()  # Drops only address_audit records from console.
        for handler in handlers:  # Attach the filter to each console handler.
            handler.addFilter(log_filter)  # Runtime filter registration on this handler.
        try:
            yield  # Run the audit with console diagnostics suppressed.
        finally:
            for handler in handlers:  # Always detach, even when the run raises.
                handler.removeFilter(log_filter)  # Runtime filter removal to leave logging state pristine.

    @staticmethod
    def _console_handlers() -> list[logging.Handler]:
        """Return the console (non-file) ``StreamHandler`` instances on the root logger."""
        root = logging.getLogger()  # Root logger carries both file and console handlers.
        return [handler for handler in root.handlers if AddressAuditEngine._is_console_handler(handler)]

    @staticmethod
    def _is_console_handler(handler: logging.Handler) -> bool:
        """Return True for a console-bound ``StreamHandler`` (i.e. not a ``FileHandler``)."""
        if not isinstance(handler, logging.StreamHandler):  # Not a stream handler at all -> never console.
            return False  # Ignore this handler for console-filter purposes.
        return not isinstance(handler, logging.FileHandler)  # StreamHandler AND not-a-FileHandler == console.

    def _audit_rows(
        self,
        apisession: Any,
        org_id: str,
        rows: list[AddressRow],
        ctx: _AuditContext,
    ) -> list[AuditResult]:
        """Load Mist data, match/enrich/resolve every row, and classify the outcomes."""
        inventory_by_serial, sites_by_id, sites_list = self._load_mist_data(apisession, org_id)  # One read.
        matcher = SiteMatchingEngine(inventory_by_serial, sites_by_id, self._fuzzy_threshold())  # In-memory matcher.
        matched = self._match_sites(rows, matcher, sites_list)  # Serial -> fuzzy fallback per row.
        self._enrich_sites(apisession, matched)  # Fill SNMP location on matched sites.
        perf = PhaseTimer()  # One timer shared by the resolver + geocoder for this run.
        resolver = self._build_resolver(ctx.ui_geocode, perf)  # Tiered resolver (+ optional Tier 3).
        results = self._resolve_and_classify(rows, matched, resolver, ctx)  # Build results using bundled context.
        if not perf.is_empty():  # Emit the per-phase timing breakdown so slow stages are visible.
            logger.info("Address audit phase timing (slowest first):\n%s", perf.summary())  # Diagnostic summary.
        return results  # Hand the classified results back to the pipeline.

    def _select_csv_file(self) -> str | None:
        """Find CSV/TSV files in data/; auto-pick one, prompt when several, else None."""
        candidates = sorted(glob.glob(os.path.join(_DATA_DIR, "*.csv")) + glob.glob(os.path.join(_DATA_DIR, "*.tsv")))
        if not candidates:  # No files at all.
            logger.debug("No CSV/TSV files found in %s", _DATA_DIR)  # Trace the empty case.
            return None  # Signal "nothing to audit".
        if len(candidates) == 1:  # Exactly one -> auto-select.
            logger.info("Auto-selected CSV file: %s", candidates[0])  # Action-log the pick.
            return candidates[0]  # Use it without prompting.
        return self._prompt_csv_choice(candidates)  # Multiple -> ask the operator.

    def _prompt_csv_choice(self, candidates: list[str]) -> str | None:
        """Prompt the operator to choose one CSV from a numbered list; empty input aborts."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Available CSV files in data/:")  # Header for the choices.
        for index, path in enumerate(candidates, start=1):  # Enumerate options 1..N.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  [%s] %s", index, os.path.basename(path))  # Show each filename.
        while True:  # Loop until a valid selection is made or the operator/EOF aborts.
            raw = InputUtils.safe_input("Select file number: ", context="address_audit_csv_pick").strip()
            if (
                not raw
            ):  # Empty response (blank Enter or EOF sentinel from safe_input) -> abort so we cannot infinite-loop under non-interactive stdin (e.g. --test).  # noqa: E501
                logger.info("No CSV selection made (empty input); skipping address audit")  # Action-log the abort.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.info(
                    "No CSV selected. Skipping address audit."
                )  # Inform the operator (also covers non-TTY --test).
                return None  # Caller treats None as "nothing to audit".
            if raw.isdigit() and 1 <= int(raw) <= len(candidates):  # Valid in-range integer.
                return candidates[int(raw) - 1]  # Return the chosen path.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("Invalid selection. Please enter a number between 1 and %s: ", len(candidates))  # Re-prompt.

    def _select_business_csv_file(self, primary_csv_path: str) -> str | None:
        """Prompt for an optional business-authoritative CSV from data/ (second selector)."""
        candidates = sorted(glob.glob(os.path.join(_DATA_DIR, "*.csv")) + glob.glob(os.path.join(_DATA_DIR, "*.tsv")))
        if not candidates:  # No second-file candidates available.
            logger.debug("No candidate business-authoritative CSV files found in %s", _DATA_DIR)  # Trace skip.
            return None  # Continue without authority data.
        return self._prompt_business_csv_choice(candidates, primary_csv_path)  # Prompt operator from indexed list.

    def _prompt_business_csv_choice(self, candidates: list[str], primary_csv_path: str) -> str | None:
        """Prompt for a business-authoritative CSV file index, or skip with ``q``."""
        self._print_business_csv_menu(candidates, primary_csv_path)  # Show the numbered choices once.
        return self._read_business_csv_selection(candidates)  # Re-prompt loop until valid answer or explicit skip.

    @staticmethod
    def _print_business_csv_menu(candidates: list[str], primary_csv_path: str) -> None:
        """Print the numbered business-authoritative CSV menu with a primary-file marker."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "\nOptional: select business-authoritative CSV file in data/ (or q to skip):"
        )  # Second prompt header.
        for index, path in enumerate(candidates, start=1):  # Enumerate options 1..N.
            marker = " (primary file)" if path == primary_csv_path else ""  # Guard hint when selecting same file.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  [%s] %s%s", index, os.path.basename(path), marker)  # Show indexed filename choice.

    def _read_business_csv_selection(self, candidates: list[str]) -> str | None:
        """Loop reading operator input until a valid index or explicit 'q' skip is entered."""
        while True:  # Re-prompt until valid selection or explicit skip.
            raw = (
                InputUtils.safe_input(
                    "Select business file number (or q to skip): ", context="address_audit_business_csv_pick"
                )
                .strip()
                .lower()
            )  # Normalize once for downstream comparisons.
            if (
                not raw
            ):  # Empty response (blank Enter or EOF sentinel) is treated as explicit skip to avoid infinite loops under non-interactive stdin (e.g. --test).  # noqa: E501
                logger.info(
                    "Business-authoritative CSV selection skipped (empty input)"
                )  # Action-log the implicit skip.
                return None  # Proceed without authority data.
            picked = self._parse_business_csv_choice(raw, candidates)  # Interpret the raw operator entry.
            if picked is not _INVALID_CHOICE:  # Valid choice (path) or explicit skip (None) -> exit the retry loop.
                return picked  # type: ignore[no-any-return]  # Sentinel guarantees str|None here.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning(
                "Invalid selection. Enter 1-%s or q to skip.", len(candidates)
            )  # One-line validation message.

    @staticmethod
    def _parse_business_csv_choice(raw: str, candidates: list[str]) -> Any:
        """Return the picked path, ``None`` for skip, or ``_INVALID_CHOICE`` when unrecognized."""
        if raw == "q":  # Operator explicitly skips the authority dataset for this run.
            logger.info("Business-authoritative CSV selection skipped by operator")  # Action-log skip.
            return None  # Proceed without authority data.
        picked = AddressAuditEngine._business_csv_from_index(raw, candidates)  # Try to resolve raw as a menu index.
        if picked is None:  # Not a valid numeric index -> report as invalid so the loop re-prompts.
            return _INVALID_CHOICE  # Sentinel prompts the outer loop to ask again.
        logger.info("Selected business-authoritative CSV: %s", picked)  # Action-log selected file.
        return picked  # Use the selected authority file.

    @staticmethod
    def _business_csv_from_index(raw: str, candidates: list[str]) -> str | None:
        """Return the ``candidates`` entry for a valid 1..N menu index, else ``None``."""
        if not raw.isdigit():  # Non-numeric entry cannot be a menu index.
            return None  # Signal "not a valid index".
        index = int(raw)  # Parse once so the range check has a clean integer.
        if 1 <= index <= len(candidates):  # In-range menu selection -> resolve to the picked path.
            return candidates[index - 1]  # 1-based menu maps to a 0-based list index.
        return None  # Out-of-range -> caller treats as invalid.

    def _load_business_authority_index(
        self,
        business_csv_path: str | None,
    ) -> dict[str, dict[str, list[Any]]]:
        """Load + index the optional business-authoritative CSV (fail-soft to empty index)."""
        if not business_csv_path:  # No authority file selected this run.
            return {"by_name": {}, "by_full": {}, "by_no_suite": {}}  # Empty index keeps flow unchanged.
        try:
            rows = self._authority_ingester.load(business_csv_path)  # Parse authoritative rows from selected file.
            return self._authority_ingester.build_index(rows)  # Pre-index for O(1) per-row lookup.
        except Exception as exc:  # noqa: BLE001 -- authority file is additive, never run-blocking.
            logger.warning("Business-authoritative CSV load failed (%s); continuing without it", exc)  # Fail-soft log.
            return {"by_name": {}, "by_full": {}, "by_no_suite": {}}  # Degrade to empty authority index.

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
        logger.info("Loading Mist inventory and sites for org %s", org_id)  # Action-log start.
        devices = self._get_all(mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id), apisession)
        sites = self._get_all(mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000), apisession)
        inventory_by_serial = {d.get("serial", ""): d for d in devices if d.get("serial")}  # serial -> device.
        sites_by_id = {s.get("id", ""): s for s in sites if s.get("id")}  # site_id -> site.
        logger.debug("Loaded %d devices, %d sites", len(inventory_by_serial), len(sites_by_id))  # Action-log.
        return inventory_by_serial, sites_by_id, sites  # Hand back maps + raw site list (fuzzy needs it).

    @staticmethod
    def _get_all(response: Any, apisession: Any) -> list[dict[str, Any]]:
        """Fully paginate a Mist API response into a list (empty on failure)."""
        try:
            return mistapi.get_all(response=response, mist_session=apisession) or []  # Exhaust pagination.
        except Exception as exc:  # noqa: BLE001 -- a read failure must not crash the audit.
            logger.warning("Mist pagination failed: %s", exc)  # Log and degrade to empty.
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
            logger.debug("Site settings fetch failed for %s: %s", site_id, exc)  # Trace and degrade.
            record = {}  # Empty record -> enricher yields None.
        record.setdefault("id", site_id)  # Carry the id for log context.
        cache[site_id] = record  # Memoize for any repeat site_id.
        return record  # Hand back the settings record.

    def _build_resolver(self, ui_geocode: bool, perf: PhaseTimer) -> AddressResolver:
        """Construct the tiered resolver, wiring the Tier-3 UI geocoder when enabled."""
        ui_geocoder = None  # Default: Tier 3 disabled.
        if ui_geocode:  # Tier 3 permitted (env default auto) -> try to attach a browser.
            ui_geocoder = self._make_ui_geocoder(perf)  # Build and connect the browser geocoder (fail-soft).
        skip_ssl = self._skip_ssl_verify()  # Skip cert checks behind corporate SSL inspection (Zscaler).
        return AddressResolver(skip_ssl_verify=skip_ssl, ui_geocoder=ui_geocoder, perf=perf)  # Resolver + Tier 3.

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
    def _make_ui_geocoder(perf: PhaseTimer) -> Any:
        """Build and connect a ``MistUIGeocoder`` from env config; ``None`` if unavailable."""
        from src.site.address_audit.ui_geocoder import MistUIGeocoder  # Lazy: optional Playwright.

        geocoder = MistUIGeocoder(AddressAuditEngine._ui_config(), perf=perf)  # Env-driven config + shared timer.
        if not geocoder.connect():  # Establish the browser session (fail-soft).
            logger.info(  # No browser is the normal case; degrade quietly to Tier 1/2.
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
        config.min_key_delay_s = (
            AddressAuditEngine._env_float(  # Lower bound of the typing jitter (ms -> s).
                "UI_GEOCODE_MIN_KEY_DELAY_MS", config.min_key_delay_s * 1000.0
            )
            / 1000.0
        )
        config.max_key_delay_s = (
            AddressAuditEngine._env_float(  # Upper bound of the typing jitter (ms -> s).
                "UI_GEOCODE_MAX_KEY_DELAY_MS", config.max_key_delay_s * 1000.0
            )
            / 1000.0
        )
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
            logger.warning("Invalid %s=%r; using default %s", name, raw, default)  # Warn and fall back.
            return default  # Safe default.

    def _resolve_and_classify(
        self,
        rows: list[AddressRow],
        matched: list[MatchedSite],
        resolver: AddressResolver | None,
        ctx: _AuditContext,
    ) -> list[AuditResult]:
        """Resolve + classify every row, returning one ``AuditResult`` per CSV row."""
        results: list[AuditResult] = []  # Accumulator (100% row accountability).
        for row, site in self._progress(list(zip(rows, matched, strict=False)), len(rows)):  # Iterate w/ progress.
            results.append(self._build_audit_result(row, site, resolver, ctx))  # One classified result per row.
        logger.debug("Classified %d audit rows", len(results))  # Action-log completion.
        self._flag_duplicate_addresses(results)  # Cross-row safety: flag one address shared by 2+ sites.
        return results  # Hand back all results.

    @staticmethod
    def _flag_duplicate_addresses(results: list[AuditResult]) -> None:
        """Flag any final address shared by two or more distinct sites as DUPLICATE_ADDRESS.

        After correction each site should carry a unique, shippable address. When
        two *different* sites resolve to the *identical* full address (same suite,
        or both lacking one) they are indistinguishable for shipping -- a
        data-integrity problem the operator must resolve, so the row is made
        review-only and excluded from write-back. Sites that share only a base
        street but carry *different* suites are the normal strip-mall case: their
        full addresses differ, so they land in different buckets and are untouched.
        Rows already flagged CONFLICTING_HINTS keep that (more specific) reason.
        """
        buckets = AddressAuditEngine._bucket_by_address(results)  # Group every eligible row by its comparison key.
        for rows in buckets.values():  # Inspect each address bucket for a cross-site collision.
            AddressAuditEngine._apply_duplicate_flag(rows)  # Flag every row in a colliding bucket in one place.

    @staticmethod
    def _bucket_by_address(results: list[AuditResult]) -> dict[str, list[AuditResult]]:
        """Group results by their normalized comparison-key address (skipping ineligible rows)."""
        buckets: dict[str, list[AuditResult]] = {}  # Normalized full address -> rows sharing it.
        for result in results:  # Bucket every row by the address that will identify its site.
            key = AddressAuditEngine._bucket_key(result)  # "" for ineligible rows (leave them out).
            if key:  # Only bucket rows that actually have an address to compare.
                buckets.setdefault(key, []).append(result)  # Group rows by identical normalized address.
        return buckets  # Hand back the bucket map for the collision pass.

    @staticmethod
    def _bucket_key(result: AuditResult) -> str:
        """Return the collision key for a result, or ``''`` when it should be skipped."""
        if result.issue_type in ("UNMATCHED", "CONFLICTING_HINTS"):  # No trusted/unique address to compare.
            return ""  # Signal "leave this row out of the collision pass".
        final = result.suggested_address or AddressAuditEngine._mist_address_str(result)  # Post-audit address.
        return AddressAuditEngine._address_key(final)  # Normalize for an apples-to-apples comparison.

    @staticmethod
    def _apply_duplicate_flag(rows: list[AuditResult]) -> None:
        """Mark every row in ``rows`` as DUPLICATE when the bucket spans 2+ distinct sites."""
        sites = {r.matched_site.site_id for r in rows if r.matched_site.site_id}  # Distinct sites in this bucket.
        if len(sites) < 2:  # One site (or repeats of the same site) -> not a collision.
            return  # Nothing to flag.
        for result in rows:  # Two or more different sites share this exact address -> flag them all.
            AddressAuditEngine._mark_duplicate(result, len(sites))  # Rewrite the row in-place as review-only.

    @staticmethod
    def _mark_duplicate(result: AuditResult, site_count: int) -> None:
        """Rewrite a single result in-place as ``DUPLICATE_ADDRESS`` (review-only, no push)."""
        logger.info(
            "Duplicate address across %d sites (e.g. %s): not unique, flagging for review",
            site_count,
            result.matched_site.site_name,
        )  # Action-log the collision so script.log explains the flag.
        result.issue_type = "DUPLICATE_ADDRESS"  # Review-only: excluded from the correctable/push set.
        result.suggested_address = ""  # Never recommend pushing a non-unique address.
        result.source = "-"  # No trustworthy single source for a colliding address.

    @staticmethod
    def _mist_address_str(result: AuditResult) -> str:
        """Return the row's current Mist address as one comparable string (or '')."""
        addr = result.matched_site.mist_address  # Mist address payload (full string lives under 'address').
        return (addr.get("address") or "") if isinstance(addr, dict) else ""  # Street string or empty.

    @staticmethod
    def _address_key(text: str) -> str:
        """Normalize a full address into a collision key (country-stripped, lowercased, alnum-collapsed)."""
        no_country = re.sub(r",?\s*(?:USA|United States)\s*$", "", text, flags=re.IGNORECASE)  # Drop trailing country.
        alnum = re.sub(r"[^a-z0-9]+", " ", no_country.lower())  # Collapse punctuation/case to single spaces.
        return " ".join(alnum.split())  # Collapse whitespace -> a stable comparison key.

    def _build_audit_result(
        self,
        row: AddressRow,
        site: MatchedSite,
        resolver: Any,
        ctx: _AuditContext,
    ) -> AuditResult:
        """Resolve one row's address and wrap it in a classified ``AuditResult``."""
        if site.match_strategy == "unmatched":  # No site -> no resolution attempted.
            return AuditResult(address_row=row, matched_site=site, issue_type="UNMATCHED", source="-")
        candidates = self._build_candidates(row, site, ctx)  # Bundle mist+csv+authority+snmp for the resolver.
        if resolver.has_conflicting_hints(candidates):  # Hints disagree on the building with no majority.
            return self._conflicting_hints_result(row, site)  # Review-only: refuse to auto-pick among divergent hints.
        resolver_result = resolver.resolve(candidates)  # Run the tier cascade (fail-soft).
        return self._compose_audit_result(row, site, resolver_result, candidates)  # Classify + wrap the outcome.

    def _build_candidates(self, row: AddressRow, site: MatchedSite, ctx: _AuditContext) -> ResolveCandidates:
        """Assemble the resolver-input candidates (mist, csv, authority, snmp) for one row."""
        authoritative_addr = self._authority_ingester.match(row, site, ctx.authoritative_index)  # Optional auth hint.
        return ResolveCandidates(  # Bundle the inputs for the resolver.
            mist_address=site.mist_address,  # Current Mist address.
            csv_address=self._csv_to_dict(row),  # Customer CSV address.
            authoritative_address=authoritative_addr,  # Business-authoritative address when uniquely matched.
            snmp_location=site.snmp_location,  # SNMP reference (may be None).
            business_name=ctx.business,  # Optional query prefix.
            ui_geocode=ctx.ui_geocode,  # Whether Tier 3 is permitted.
        )

    @staticmethod
    def _conflicting_hints_result(row: AddressRow, site: MatchedSite) -> AuditResult:
        """Build the review-only ``CONFLICTING_HINTS`` result when the resolver refuses to pick."""
        logger.info("Conflicting address hints for site %s; flagging CONFLICTING_HINTS", site.site_name)
        return AuditResult(  # Review-only: the tool refuses to auto-pick among divergent stores.
            address_row=row,  # Original CSV row.
            matched_site=site,  # Keep the three hint columns visible for manual review.
            issue_type="CONFLICTING_HINTS",  # Never enters the correctable/push set.
            source="-",  # No single trustworthy source to credit.
            suggested_address="",  # Decline to recommend; operator compares Mist/CSV/SNMP by hand.
        )

    def _compose_audit_result(
        self,
        row: AddressRow,
        site: MatchedSite,
        resolver_result: Any,
        candidates: ResolveCandidates,
    ) -> AuditResult:
        """Classify a resolved row and wrap the outcome as an ``AuditResult``."""
        issue = self._classify(  # Classify with all available hints, including optional authority data.
            site.mist_address,  # Mist address.
            self._csv_to_dict(row),  # Customer CSV address.
            site.snmp_location,  # SNMP location.
            resolver_result,  # Resolver outcome.
            candidates.authoritative_address,  # Optional authoritative business hint.
        )
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
        authoritative_addr: dict[str, Any] | None = None,
    ) -> str:
        """Return one of the resolved classification states for a row (excludes the
        out-of-band UNMATCHED / CONFLICTING_HINTS / DUPLICATE_ADDRESS states)."""
        if not self._has_external_result(resolver_result):  # No external result -> use internal signals only.
            return self._classify_internal(mist_addr, csv_addr, snmp_loc, authoritative_addr or {})  # Internal path.
        return self._classify_external(mist_addr, resolver_result)  # External hit -> compare against Mist.

    @staticmethod
    def _has_external_result(resolver_result: Any) -> bool:
        """Return True when the resolver produced a usable canonical address."""
        if resolver_result is None:  # Whole result missing -> nothing external to classify against.
            return False  # Force the internal-only classification path.
        return resolver_result.canonical_address is not None  # A None canonical also means no external result.

    def _classify_external(self, mist_addr: dict[str, Any], resolver_result: Any) -> str:
        """Classify a row when the resolver produced an external canonical address."""
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

    def _classify_internal(
        self,
        mist_addr: dict[str, Any],
        csv_addr: dict[str, Any],
        snmp_loc: str | None,
        authoritative_addr: dict[str, Any] | None = None,
    ) -> str:
        """Classify on internal CSV/SNMP signals alone when no external result exists."""
        mist_street = mist_addr.get("address", "")  # Mist street anchor.
        candidate = self._internal_candidate(csv_addr, snmp_loc, authoritative_addr)  # Authority > SNMP > CSV order.
        if not candidate:  # No internal signal produced any candidate address.
            return "NO_RESULT"  # Internal inconclusive and nothing external resolved.
        if self._has_suite_discrepancy(mist_street, candidate):  # Internal adds a missing suite.
            return "MISSING_SUITE"  # The common strip-mall case, caught without any external call.
        return "NO_RESULT"  # Internal signal exists but adds no suite -> still inconclusive.

    @staticmethod
    def _internal_candidate(
        csv_addr: dict[str, Any],
        snmp_loc: str | None,
        authoritative_addr: dict[str, Any] | None,
    ) -> str:
        """Pick the best internal candidate street (authority > SNMP > CSV), or ``''``."""
        authority_street = (authoritative_addr or {}).get("address", "")  # Business-authoritative hint (may be blank).
        if authority_street:  # Authority wins whenever it produced an address.
            return str(authority_street)  # Coerce so mypy sees a concrete str even when the dict is Any-typed.
        if snmp_loc:  # SNMP location fallback (may still be blank/None).
            return snmp_loc  # SNMP variable already normalized to a plain string upstream.
        return str(csv_addr.get("address", ""))  # Final fallback: the primary CSV row's street.

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
        if self._house_number_mismatch(mist_street, candidate):  # Different building number -> different street.
            return False  # No further checks needed.
        if self._directionals_disagree(mist_street, candidate):  # Opposite side of the street.
            return False  # Wrong-side address must never read as a match.
        overlap = self._name_words(mist_street) & self._name_words(candidate)  # Shared street words.
        return bool(overlap)  # Same street when at least one street-name word matches.

    @staticmethod
    def _house_number_mismatch(mist_street: str, candidate: str) -> bool:
        """Return True when the Mist house number is present but absent from the candidate."""
        mist_number = AddressAuditEngine._house_number(mist_street)  # Mist street's leading house number.
        if not mist_number:  # No Mist house number to anchor on -> nothing to disagree about.
            return False  # Cannot be a mismatch when there is nothing to compare.
        return mist_number not in AddressAuditEngine._all_numbers(candidate)  # True when candidate lacks that number.

    @staticmethod
    def _directionals_disagree(mist_street: str, candidate: str) -> bool:
        """Return True when both streets carry leading directionals and they conflict (E vs W)."""
        mist_dir = AddressAuditEngine._leading_directional(mist_street)  # Directional right after Mist's number.
        cand_dir = AddressAuditEngine._leading_directional(candidate)  # Same for the candidate (city dirs ignored).
        if not (mist_dir and cand_dir):  # At least one side has no directional -> cannot disagree meaningfully.
            return False  # Absence is not conflict.
        return mist_dir != cand_dir  # Both present -> conflict when they differ.

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
        return {token for token in normalized.split() if self._is_name_token(token)}  # Keep only name-shaped tokens.

    @staticmethod
    def _is_name_token(token: str) -> bool:
        """Return True for a street-name token: alphabetic word OR alnum ordinal (``107th``)."""
        if token.isalpha() and len(token) >= 2:  # Street-name words (military, jefferson).
            return True  # Keep the plain alphabetic word.
        return AddressAuditEngine._is_alnum_ordinal(token)  # Fall through to the ordinal/alnum detector.

    @staticmethod
    def _is_alnum_ordinal(token: str) -> bool:
        """Return True when ``token`` mixes letters and digits (``107th``, ``a1a``)."""
        has_digit = any(ch.isdigit() for ch in token)  # At least one numeric character present.
        has_alpha = any(ch.isalpha() for ch in token)  # At least one alphabetic character present.
        return has_digit and has_alpha  # Both signals -> a numeric-named street token.

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
            "mist_ui": "Google (Mist UI)",  # Tier 3: Google Places autocomplete via the Mist portal address box.
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
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("No file saved. Exiting address audit.")  # Quit branch confirmation.
            return  # No write-back when nothing was saved.
        path = self._reporter.save(results)  # Write the timestamped comparison CSV.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Saved to %s", path)  # Confirm the written path.
        self._offer_write_back(results, apisession)  # Offer to push corrections to Mist.

    def _offer_write_back(self, results: list[AuditResult], apisession: Any) -> None:
        """Gate, then run, the optional per-site address write-back to Mist."""
        corrector = self._make_corrector(apisession)  # Build the write-back collaborator.
        targets = corrector.correctable(results)  # Rows with a pushable correction.
        if not targets:  # Nothing to correct.
            logger.debug("No correctable rows; skipping write-back offer")  # Trace the no-op.
            return  # Audit ends here.
        prompt = f"\nPush corrected addresses back to Mist for up to {len(targets)} site(s)? [y/N]: "
        choice = InputUtils.safe_input(prompt, context="address_audit_writeback_gate").strip().lower()
        if choice not in ("y", "yes"):  # Operator declined the whole batch.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("Skipped write-back. No Mist changes made.")  # Confirm no writes.
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
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("No correction report saved.")  # Confirm the skip.
            return  # Done.
        path = self._reporter.save_corrections(outcomes)  # Write the before/after CSV.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Saved correction report to %s", path)  # Confirm the written path.

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
        logger.info(  # Action-log the attempt (and reference args/kwargs for the deferred signature).
            "apply_corrections invoked with %d args / %d kwargs (feature disabled)", len(args), len(kwargs)
        )
        raise NotImplementedError("Address write-back is not enabled in this release.")  # Deferred.
