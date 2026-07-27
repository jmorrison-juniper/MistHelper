"""Security export orchestration extracted from MistHelper offender #8."""

import csv  # CSV DictReader powers the SiteList iteration for rogue exports.
import importlib  # Dynamic import shields the module from a MistHelper import cycle.
import logging  # Structured trace/warn/error logging across the export flow.
import os  # File existence and mtime probes for the fast-mode freshness check.
import time  # Wall clock for freshness math and progress duration reporting.
from collections.abc import (
    Callable,  # Typed callable signature for API fetchers.
    Iterator,  # Typed yield signature for the site iterator helper.
)
from dataclasses import dataclass  # Frozen dataclass bundles flattened-export config.
from types import SimpleNamespace  # SimpleNamespace bags all runtime dependencies.
from typing import Any  # Loose typing for heterogeneous API payloads.

from src.dataclasses.progress_event import (
    ProgressContext,
)  # Bundles progress identity for emit_progress_* (issue #470).

_OUTPUT_FILES: tuple[str, ...] = (  # Files the service produces. Also drives fast-mode freshness.
    "OrgSecurityPolicies.csv",  # Flattened org security policies dataset.
    "OrgSecIntelProfiles.csv",  # Flattened org security intelligence profiles dataset.
    "OrgRogueData.csv",  # Combined rogue APs and rogue clients dataset.
)
_ROGUE_OUTPUT: str = "OrgRogueData.csv"  # Single source of truth for the combined rogue export file name.
_SITE_LIST_CSV: str = "SiteList.csv"  # SiteList cache filename used to seed rogue iteration.
_PROGRESS_ISSUE_ID: str = "42"  # Progress identifier tying emissions to the security export operation.
_PROGRESS_STAGE: str = "security_events"  # Progress stage label surfaced to observers.
_PROGRESS_TOTAL: int = 3  # Three files (policies, intel profiles, rogue data).
_ROGUE_LOOKBACK_HOURS_PROD: int = 168  # Default rogue insights lookback window (one week).
_ROGUE_LOOKBACK_HOURS_TEST: int = 1  # Reduced rogue insights lookback window in test mode.
_ROGUE_PAGE_LIMIT: int = 1000  # Insights page size for rogue AP/client fetches.


@dataclass(frozen=True)
class _RogueKind:
    """Pairs a rogue insights endpoint with its record kind label."""

    endpoint: str  # Attribute name resolved via getattr on sites.insights.
    label: str  # "AP" or "Client" written into the tagged record's rogue_type field.


_ROGUE_KINDS: tuple[_RogueKind, ...] = (  # Table-driven dispatch across rogue types.
    _RogueKind(endpoint="listSiteRogueAPs", label="AP"),  # Rogue APs endpoint on sites.insights.
    _RogueKind(endpoint="listSiteRogueClients", label="Client"),  # Rogue clients endpoint on sites.insights.
)


def _resolve_runtime_dependencies() -> SimpleNamespace:  # Deferred import avoids MistHelper import cycles.
    """Resolve MistHelper runtime dependencies without static src imports."""
    misthelper_module = importlib.import_module("MistHelper")  # Late-bind MistHelper to sidestep circular imports.
    return SimpleNamespace(  # Bundle the pieces the service needs into a single namespace.
        ConfigUtils=misthelper_module.ConfigUtils,  # Config helpers (org id, stop signal, ...).
        PROGRESS_EMITTER=getattr(misthelper_module, "PROGRESS_EMITTER", None),  # Optional progress emitter.
        TimeUtils=misthelper_module.TimeUtils,  # Dynamic lookback helper used by rogue export.
        CacheUtils=misthelper_module.CacheUtils,  # SiteList.csv (re)generation helper.
        OrgSiteExporter=misthelper_module.OrgSiteExporter,  # Callable that refreshes the site list cache.
        DataProcessingUtils=misthelper_module.DataProcessingUtils,  # Flatten + escape helpers for CSV rows.
        DataExporter=misthelper_module.DataExporter,  # Writes rows to CSV/XLSX with format selection.
        FilePathUtils=misthelper_module.FilePathUtils,  # Resolves output CSV paths.
        mistapi=misthelper_module.mistapi,  # Mist SDK entrypoint.
        apisession=misthelper_module.apisession,  # Authenticated Mist SDK session.
        tqdm=misthelper_module.tqdm,  # Progress bar wrapper for the site iteration.
        csv_freshness_minutes=getattr(misthelper_module, "CSV_FRESHNESS_MINUTES", 60),  # Fast-mode TTL minutes.
    )


@dataclass(frozen=True)
class _FlattenedExportSpec:
    """Immutable configuration for one flattened org dataset export."""

    output_file: str  # Target CSV filename for this dataset.
    data_label: str  # Human-readable label used in stdout/logs.
    start_label: str  # Compact label logged when the fetch begins.
    fetcher: Callable[[], Any]  # Zero-arg lambda that invokes the mistapi list endpoint.
    empty_message: str  # Logged at warning level when the fetch returns zero rows.
    empty_suffix: str  # Suffix appended to the stdout summary when the dataset is empty.


class SecurityEventsService:
    """Owns organization security export flow formerly embedded in MistHelper."""

    @staticmethod
    def execute(fast: bool = False) -> None:
        """Run the organization security export workflow."""
        deps = _resolve_runtime_dependencies()  # Resolve MistHelper dependencies once for the whole run.
        if fast and SecurityEventsService._all_outputs_fresh(deps, list(_OUTPUT_FILES)):
            logging.info(
                "Fast mode cache hit: All security data CSVs are fresh; skipping fetch."
            )  # Trace short-circuit.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("* Fast mode: Using cached security data (all files fresh)")
            return  # No fetch needed. The cached CSVs are still valid.
        SecurityEventsService._run_export_workflow(deps)  # Delegate the actual export to keep this entrypoint short.

    @staticmethod
    def _run_export_workflow(deps: SimpleNamespace) -> None:
        """Execute the three security exports and emit progress bookends."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Export Organization Security Data:")
        logging.info("Starting export of organization security policies, intelligence profiles, and rogue data...")
        emitter = deps.PROGRESS_EMITTER  # Optional. None disables progress emission.
        if emitter:
            emitter.emit_progress_start(
                _PROGRESS_ISSUE_ID, _PROGRESS_STAGE, _PROGRESS_TOTAL
            )  # Announce operation start.
        op_start = time.time()  # Capture start for the completion emit duration.
        current_org_id = deps.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the target org id up front.
        for spec in SecurityEventsService._build_flattened_specs(deps, current_org_id):  # Loop over datasets.
            SecurityEventsService._export_flattened_dataset(deps, spec)  # Fetch + flatten + export one dataset.
        SecurityEventsService._export_rogue_data(deps)  # Third file: combined rogue export.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Security data export completed (3 files generated)")
        logging.info("Completed security policies, intelligence profiles, and rogue data export aggregate.")
        if emitter:
            emitter.emit_progress_complete(  # Bundle identity into a ProgressContext per issue #470.
                ProgressContext(_PROGRESS_ISSUE_ID, _PROGRESS_STAGE, _PROGRESS_TOTAL),
                _PROGRESS_TOTAL,
                False,
                time.time() - op_start,
            )

    @staticmethod
    def _all_outputs_fresh(deps: SimpleNamespace, output_files: list[str]) -> bool:
        """Return True when every expected CSV exists and is still fresh."""
        for output_file in output_files:  # Every file must pass. A single miss falsifies the check.
            try:
                path = deps.FilePathUtils.get_csv_path(output_file)  # Resolve absolute path via the util.
                if not os.path.exists(path):  # Missing file means no cache to trust.
                    return False
                age_minutes = (time.time() - os.path.getmtime(path)) / 60.0  # Convert mtime delta to minutes.
                if age_minutes >= deps.csv_freshness_minutes:  # Stale => refetch is required.
                    return False
            except Exception:  # Any filesystem error means we cannot prove freshness. Fall through to refetch.
                return False
        return True  # All files exist and are within the freshness window.

    @staticmethod
    def _build_flattened_specs(deps: SimpleNamespace, current_org_id: str) -> tuple[_FlattenedExportSpec, ...]:
        """Build the two flattened-dataset export specs (policies + secintel)."""
        return (
            _FlattenedExportSpec(  # Policies spec: describes the OrgSecurityPolicies.csv export.
                output_file="OrgSecurityPolicies.csv",
                data_label="security policies",
                start_label="secpolicies",
                fetcher=lambda: deps.mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies(
                    deps.apisession, current_org_id, limit=1000
                ),
                empty_message="No data to export for OrgSecurityPolicies.csv (zero policies returned).",
                empty_suffix="(no policies found)",
            ),
            _FlattenedExportSpec(  # Secintel spec: describes the OrgSecIntelProfiles.csv export.
                output_file="OrgSecIntelProfiles.csv",
                data_label="security intelligence profiles",
                start_label="secintel profiles",
                fetcher=lambda: deps.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles(
                    deps.apisession, current_org_id
                ),
                empty_message="No data to export for OrgSecIntelProfiles.csv (zero profiles returned).",
                empty_suffix="(no profiles found)",
            ),
        )

    @staticmethod
    def _export_flattened_dataset(deps: SimpleNamespace, spec: _FlattenedExportSpec) -> None:
        """Fetch, flatten, and export a single org dataset described by ``spec``."""
        dataset = SecurityEventsService._fetch_dataset(deps, spec)  # Isolate the try/except paging in a helper.
        if not dataset:  # Guard clause: write an empty file and note the miss for observability.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(
                "! 0 %s exported to %s %s",
                spec.data_label,
                spec.output_file,
                spec.empty_suffix,
            )
            logging.warning(spec.empty_message)  # Trace an empty result for postmortems.
            deps.DataExporter.write_with_format_selection([], spec.output_file)  # Write empty for consistency.
            return
        processed = deps.DataProcessingUtils.flatten_nested_fields(dataset)  # Flatten nested API structures.
        processed = deps.DataProcessingUtils.escape_multiline(processed)  # Escape multiline fields for CSV safety.
        deps.DataExporter.write_with_format_selection(processed, spec.output_file)  # Emit the CSV/XLSX file.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(
            "! %d %s exported to %s",
            len(processed),
            spec.data_label,
            spec.output_file,
        )
        logging.info("Exported %d %s to %s", len(processed), spec.data_label, spec.output_file)  # Trace volume.

    @staticmethod
    def _fetch_dataset(deps: SimpleNamespace, spec: _FlattenedExportSpec) -> list[dict[str, Any]]:
        """Invoke the spec's fetcher and page through results, tolerating failures."""
        try:
            logging.info("Fetching organization %s...", spec.start_label)  # Trace the fetch start.
            response = spec.fetcher()  # Zero-arg lambda invokes the specific list endpoint.
            dataset = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Page all rows.
            logging.debug("%s fetched: %d", spec.data_label.capitalize(), len(dataset))  # Trace row count.
            return dataset
        except Exception as error:  # Fetch failure is non-fatal. We still write an empty export downstream.
            logging.warning("Failed to fetch %s: %s", spec.start_label, error)  # Trace the failure cause.
            return []

    @staticmethod
    def _fetch_tagged_rogue(
        deps: SimpleNamespace,
        site_id: str,
        site_name: str,
        rogue_duration: str,
        kind: _RogueKind,
    ) -> list[dict[str, Any]]:
        """Fetch one rogue kind (AP or Client) and tag each record with site context."""
        fetcher = getattr(deps.mistapi.api.v1.sites.insights, kind.endpoint)  # Dynamic dispatch via _ROGUE_KINDS.
        response = fetcher(
            deps.apisession, site_id, duration=rogue_duration, limit=_ROGUE_PAGE_LIMIT
        )  # Insights query.
        records = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Page all rogue rows.
        for record in records:  # Tag every rogue record with owning site + kind for downstream aggregation.
            record["site_id"] = site_id  # Owning site id.
            record["site_name"] = site_name  # Owning site name.
            record["rogue_type"] = kind.label  # AP or Client kind label.
        return records  # Tagged rogue records ready to accumulate.

    @staticmethod
    def _fetch_site_rogue(
        deps: SimpleNamespace, site_id: str, site_name: str, rogue_duration: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch tagged rogue APs and rogue clients for one site. Return ([],[]) on failure."""
        try:  # Per-site failures are non-fatal for the whole export.
            aps = SecurityEventsService._fetch_tagged_rogue(
                deps, site_id, site_name, rogue_duration, _ROGUE_KINDS[0]
            )  # Rogue APs for this site.
            clients = SecurityEventsService._fetch_tagged_rogue(
                deps, site_id, site_name, rogue_duration, _ROGUE_KINDS[1]
            )  # Rogue clients for this site.
            logging.info(
                "! Fetched %d rogue APs and %d rogue clients from site: %s",
                len(aps),
                len(clients),
                site_name,
            )  # Trace per-site counts for observability.
            return aps, clients  # Tuple keeps API-compat with the previous signature.
        except Exception as error:  # Per-site API failure - warn and yield empty lists to keep the export going.
            logging.warning("! Failed to fetch rogue data from site %s: %s", site_name, error)  # Trace failure cause.
            return [], []

    @staticmethod
    def _iterate_site_rogue(
        deps: SimpleNamespace, rogue_duration: str
    ) -> Iterator[tuple[list[dict[str, Any]], list[dict[str, Any]]]]:
        """Yield (aps, clients) tuples per valid site, honoring the stop signal."""
        site_list_path = deps.FilePathUtils.get_csv_path(_SITE_LIST_CSV)  # Resolve the cached site list path.
        with open(site_list_path, encoding="utf-8") as file_handle:  # Site list is small. Read fully.
            sites = list(csv.DictReader(file_handle))  # Materialize rows so tqdm can size the bar.
        for site in deps.tqdm(sites, desc="Sites", unit="site"):  # Progress bar wraps the site loop.
            if deps.ConfigUtils.check_stop_signal():  # Honor a cooperative user cancel.
                break  # Stop iterating remaining sites.
            site_id = site.get("id")  # Site id extracted from the CSV row.
            site_name = site.get("name", "Unknown Site")  # Site name with placeholder fallback.
            if not site_id:  # Skip rows with no id (defensive against malformed cache).
                continue
            yield SecurityEventsService._fetch_site_rogue(deps, site_id, site_name, rogue_duration)  # One site batch.

    @staticmethod
    def _export_rogue_combined(deps: SimpleNamespace, all_rogue_data: list[dict[str, Any]]) -> None:
        """Flatten + export combined rogue data, or write an empty file when nothing was found."""
        if not all_rogue_data:  # Guard: no rogue devices anywhere. Still emit an empty file for consistency.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! 0 rogue devices exported to OrgRogueData.csv (no rogue devices found)")
            logging.info("No rogue devices found across all sites (OrgRogueData.csv written empty).")  # Trace empty.
            deps.DataExporter.write_with_format_selection([], _ROGUE_OUTPUT)  # Consistent empty export.
            return
        processed = deps.DataProcessingUtils.flatten_nested_fields(all_rogue_data)  # Flatten nested rogue fields.
        processed = deps.DataProcessingUtils.escape_multiline(processed)  # Escape multiline fields for CSV.
        deps.DataExporter.write_with_format_selection(processed, _ROGUE_OUTPUT)  # Write the combined rogue export.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %d rogue devices exported to OrgRogueData.csv", len(processed))
        logging.info("Exported %d rogue devices to OrgRogueData.csv", len(processed))  # Trace export volume.

    @staticmethod
    def _export_rogue_data(deps: SimpleNamespace) -> None:
        """Fetch rogue AP + client data across all sites and export combined rows."""
        lookback_hours = deps.TimeUtils.get_dynamic_lookback_hours(
            _ROGUE_LOOKBACK_HOURS_PROD, _ROGUE_LOOKBACK_HOURS_TEST
        )  # Dynamic lookback (prod default 168h, test 1h).
        rogue_duration = f"{lookback_hours}h"  # Duration string accepted by the insights endpoints.
        deps.TimeUtils.log_dynamic_lookback("rogue data fetch", lookback_hours)  # Trace chosen lookback.
        logging.info("Fetching rogue APs and clients from all sites via insights...")  # Trace workflow start.
        deps.CacheUtils.check_and_generate_csv(_SITE_LIST_CSV, deps.OrgSiteExporter.sites)  # Ensure site list exists.
        all_rogue_aps: list[dict[str, Any]] = []  # Accumulates tagged rogue APs across sites.
        all_rogue_clients: list[dict[str, Any]] = []  # Accumulates tagged rogue clients across sites.
        try:  # Guard site-list reading + iteration. Failure here aborts this export only.
            for aps, clients in SecurityEventsService._iterate_site_rogue(deps, rogue_duration):  # Per-site fan-out.
                all_rogue_aps.extend(aps)  # Accumulate rogue APs.
                all_rogue_clients.extend(clients)  # Accumulate rogue clients.
        except Exception as error:  # Failure reading/iterating the site list is fatal for this export.
            logging.error("Failed to process sites for rogue data: %s", error)  # Trace the failure.
            return  # Abort the rogue export leg without touching the other exports.
        SecurityEventsService._export_rogue_combined(deps, all_rogue_aps + all_rogue_clients)  # Emit combined file.
