"""Virtual chassis to virtual MAC conversion operations.

Extracted from MistHelper.py (Issue #213). Provides functionality to convert
virtual chassis switches to virtual MAC addressing, check conversion status,
and perform bulk conversions via CSV site lists.

Menu operations: 92 (single convert), 93 (bulk by site list), 94 (status check).
"""

from __future__ import annotations  # WHY: enable PEP-563 string annotations for cheap forward refs.

import csv  # WHY: CSV IO for inventory / site-list / VCConvert files.
import logging  # WHY: structured operator logging for observability of destructive operations.
import os  # WHY: portable filesystem path checks (existence of cache CSVs).
from collections.abc import Callable  # WHY: precise callable typing without runtime penalty.
from dataclasses import dataclass  # WHY: frozen dataclasses collapse parameter groups (STRUCT-PARAMS).
from typing import Any  # WHY: mistapi session and response payloads are dynamically shaped.

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SafeInputFn = Callable[..., str]  # WHY: alias for the injected safe_input helper (context-aware EOF).
SelectSiteFn = Callable[[], str | None]  # WHY: alias for site prompt returning selected site_id.
GetCsvPathFn = Callable[[str], str]  # WHY: resolves a filename to an absolute cache path.
CreateCsvTemplateFn = Callable[[str], str]  # WHY: writes an empty template CSV, returns the path.
CheckAndGenerateCsvFn = Callable[[str, Any], bool]  # WHY: ensures a cached CSV exists, returns success.
FlattenFieldsFn = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]  # WHY: flattens nested dicts.
EscapeMultilineFn = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]  # WHY: sanitizes multiline text.
SaveDataFn = Callable[[list[dict[str, Any]], str], bool]  # WHY: exporter, returns success bool.

# Converted prefix for virtual MAC
_CONVERTED_PREFIX = "020003"  # WHY: Juniper virtual-MAC OUI marker used to detect a converted switch.


@dataclass(frozen=True)
class VCIODeps:
    """Immutable bundle of CSV cache / inventory dependencies for VC operations."""

    get_csv_path_fn: GetCsvPathFn  # WHY: resolve filenames to data-dir paths.
    check_and_generate_csv_fn: CheckAndGenerateCsvFn  # WHY: ensures a fresh cached CSV exists.
    inventory_generator: Any  # WHY: callable that regenerates OrgInventory.csv on demand.
    sites_generator: Any  # WHY: callable that regenerates SiteList.csv on demand.
    create_csv_template_fn: CreateCsvTemplateFn | None = None  # WHY: optional template writer for VCConvert.


@dataclass(frozen=True)
class VCExportDeps:
    """Immutable bundle of export helpers used when persisting status results."""

    flatten_fields_fn: FlattenFieldsFn  # WHY: flatten nested inventory rows before writing.
    escape_multiline_fn: EscapeMultilineFn  # WHY: escape newlines / quotes to keep CSV valid.
    save_data_fn: SaveDataFn  # WHY: physical writer that persists the final CSV to disk.


@dataclass(frozen=True)
class _ConvertTarget:
    """Bundle of fields identifying one switch targeted by a conversion call."""

    selected: dict[str, Any]  # WHY: full inventory row for the switch (for display + confirm).
    site_id: str  # WHY: mistapi convert endpoint requires site_id.
    site_name: str  # WHY: operator-visible label for confirmations / logs.
    device_id: str  # WHY: mistapi convert endpoint requires device_id.


class VirtualChassisManager:
    """Manage virtual chassis to virtual MAC conversion operations.

    All methods are static. External dependencies are injected via the
    ``VCIODeps`` / ``VCExportDeps`` dataclasses and function callables so the
    module can be tested and run independently of MistHelper globals.
    """

    # ------------------------------------------------------------------
    # Public entry-points (menus 92, 93, 94)
    # ------------------------------------------------------------------

    @staticmethod
    def convert_single(
        *,
        apisession: Any,
        io_deps: VCIODeps,
        safe_input_fn: SafeInputFn,
        select_site_fn: SelectSiteFn,
        dry_run: bool = False,
    ) -> None:
        """Interactively convert a single VC switch to virtual MAC (Menu 92)."""
        VirtualChassisManager._print_intro(dry_run)  # WHY: banner + optional dry-run notice.
        site = VirtualChassisManager._resolve_site(apisession, select_site_fn)  # WHY: gate on selection.
        if site is None:  # WHY: user cancelled or no site returned; nothing to convert.
            return  # WHY: exit silently without touching API state.
        site_id, site_name = site  # WHY: unpack for readable downstream calls.
        selected = VirtualChassisManager._pick_switch(site_id, site_name, io_deps, safe_input_fn)  # WHY.
        if selected is None:  # WHY: no switch chosen or none available.
            return  # WHY: nothing to convert, exit cleanly.
        device_id = VirtualChassisManager._validate_switch(selected, safe_input_fn)  # WHY: preflight.
        if device_id is None:  # WHY: preflight or id check failed.
            return  # WHY: already logged; nothing to do.
        target = _ConvertTarget(  # WHY: bundle to keep _convert_or_dry_run under param limit.
            selected=selected, site_id=site_id, site_name=site_name, device_id=device_id
        )
        VirtualChassisManager._convert_or_dry_run(apisession, target, dry_run, safe_input_fn)  # WHY: exec.

    @staticmethod
    def convert_by_site_list(
        *,
        apisession: Any,
        io_deps: VCIODeps,
        safe_input_fn: SafeInputFn,
    ) -> None:
        """Bulk convert VC switches from sites in VCConvert.CSV (Menu 93)."""
        logging.info("Starting bulk VC to virtual MAC conversion by site list...")  # WHY: audit start.
        target_ids, site_name_to_id = VirtualChassisManager._prepare_bulk_targets(  # WHY: resolve sites.
            io_deps, safe_input_fn
        )
        if not target_ids:  # WHY: nothing to convert if there are no resolvable sites.
            return  # WHY: early exit; user-facing messaging already emitted.
        switches = VirtualChassisManager._load_switches_for_sites(  # WHY: load VC switches for the sites.
            target_ids, site_name_to_id, io_deps.get_csv_path_fn
        )
        if not switches:  # WHY: nothing to convert.
            print(" No virtual chassis switches found in the specified sites.")  # WHY: operator note.
            logging.warning("No virtual chassis switches found in target sites.")  # WHY: audit.
            return  # WHY: exit cleanly.
        VirtualChassisManager._display_switches_for_conversion(switches)  # WHY: show what will convert.
        if not VirtualChassisManager._confirm_bulk(safe_input_fn):  # WHY: destructive-op double-check.
            return  # WHY: cancelled; already printed.
        VirtualChassisManager._execute_bulk_conversion(apisession, switches)  # WHY: perform conversion.

    @staticmethod
    def check_status(
        *,
        io_deps: VCIODeps,
        export_deps: VCExportDeps,
    ) -> None:
        """Check conversion status of all VC switches in the org (Menu 94)."""
        VirtualChassisManager._print_status_banner()  # WHY: header + explanation of prefix.
        logging.info("Starting virtual chassis conversion status check...")  # WHY: audit entry.
        io_deps.check_and_generate_csv_fn("OrgInventory.csv", io_deps.inventory_generator)  # WHY: refresh.
        vc_switches = VirtualChassisManager._load_vc_switches(io_deps.get_csv_path_fn)  # WHY: load subset.
        if not vc_switches:  # WHY: no VC switches to classify.
            VirtualChassisManager._print_no_vc_switches()  # WHY: consistent operator messaging.
            return  # WHY: nothing to analyze or export.
        converted, not_converted = VirtualChassisManager._classify_status(  # WHY: enrich + partition.
            vc_switches, io_deps
        )
        VirtualChassisManager._display_status_summary(converted, not_converted)  # WHY: totals + samples.
        VirtualChassisManager._export_status_results(  # WHY: persist merged results to CSV.
            converted + not_converted,
            export_deps.flatten_fields_fn,
            export_deps.escape_multiline_fn,
            export_deps.save_data_fn,
            io_deps.get_csv_path_fn,
        )
        VirtualChassisManager._print_status_usage_notes()  # WHY: closing usage guidance.

    # ------------------------------------------------------------------
    # convert_single helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_intro(dry_run: bool) -> None:
        """Print the convert-single banner and optional dry-run notice."""
        mode_label = "[DRY RUN] " if dry_run else ""  # WHY: prefix banner in dry-run mode.
        print(f"\n  {mode_label}DESTRUCTIVE: Virtual Chassis to Virtual MAC Conversion")  # WHY: banner.
        print("=" * 60)  # WHY: visual separator.
        if dry_run:  # WHY: extra explanation when dry-run is active.
            print("  DRY RUN MODE: No changes will be made. Showing what would happen.")  # WHY: notice.

    @staticmethod
    def _resolve_site(apisession: Any, select_site_fn: SelectSiteFn) -> tuple[str, str] | None:
        """Prompt for a site and return (site_id, site_name) or None if cancelled."""
        site_id = select_site_fn()  # WHY: interactive site chooser.
        if not site_id:  # WHY: operator cancelled selection.
            print(" No site selected.")  # WHY: visible feedback.
            return None  # WHY: signal to caller that we should exit.
        site_name = VirtualChassisManager._get_site_name(apisession, site_id)  # WHY: friendly name.
        print(f"\n  Selected Site: {site_name} ({site_id})")  # WHY: confirmation echo.
        return site_id, site_name  # WHY: tuple keeps caller simple.

    @staticmethod
    def _pick_switch(
        site_id: str,
        site_name: str,
        io_deps: VCIODeps,
        safe_input_fn: SafeInputFn,
    ) -> dict[str, Any] | None:
        """Load switches at site and let the operator pick one to convert."""
        switches = VirtualChassisManager._load_site_switches(  # WHY: get eligible switches.
            site_id,
            io_deps.get_csv_path_fn,
            io_deps.check_and_generate_csv_fn,
            io_deps.inventory_generator,
        )
        if not switches:  # WHY: no eligible switches at this site.
            print(f"! No virtual chassis switches found at site '{site_name}'.")  # WHY: operator note.
            print(" Virtual chassis switches must have a device ID assigned.")  # WHY: eligibility hint.
            logging.warning("No virtual chassis switches found at site %s.", site_id)  # WHY: audit.
            return None  # WHY: nothing to pick.
        return VirtualChassisManager._prompt_switch_selection(switches, site_name, safe_input_fn)

    @staticmethod
    def _convert_or_dry_run(
        apisession: Any,
        target: _ConvertTarget,
        dry_run: bool,
        safe_input_fn: SafeInputFn,
    ) -> None:
        """Branch to dry-run print or execute the destructive conversion."""
        if dry_run:  # WHY: simulate without hitting the API.
            VirtualChassisManager._print_dry_run(  # WHY: preview only.
                target.selected, target.site_name, target.device_id, target.site_id
            )
            return  # WHY: dry-run never executes the real API call.
        if not VirtualChassisManager._confirm_conversion(  # WHY: final destructive-op confirmation.
            target.selected, target.site_name, target.device_id, safe_input_fn
        ):
            print(" Operation cancelled.")  # WHY: visible cancellation.
            return  # WHY: skip execution when operator did not type CONVERT.
        VirtualChassisManager._execute_conversion(  # WHY: fire the mistapi call.
            apisession, target.site_id, target.device_id, target.selected.get("name", ""), target.site_name
        )

    @staticmethod
    def _validate_switch(
        selected: dict[str, Any],
        safe_input_fn: SafeInputFn,
    ) -> str | None:
        """Return device_id when switch passes id + preflight checks, else None."""
        device_id = selected.get("id")  # WHY: mistapi requires an id to convert.
        if not device_id:  # WHY: defensive guard against malformed inventory rows.
            print(" Missing device_id for selected switch.")  # WHY: surface operator-visible error.
            logging.warning("Missing device_id for selected switch.")  # WHY: audit trail.
            return None  # WHY: caller aborts on None.
        if not VirtualChassisManager._preflight_check(selected, safe_input_fn):  # WHY: eligibility.
            return None  # WHY: preflight failed or operator declined.
        return str(device_id)  # WHY: valid target device id; coerce dict[Any] value to str.

    # ------------------------------------------------------------------
    # convert_by_site_list helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_bulk_targets(
        io_deps: VCIODeps,
        safe_input_fn: SafeInputFn,
    ) -> tuple[list[str], dict[str, str]]:
        """Load site names, refresh caches, resolve to (target_ids, name_to_id)."""
        template_fn = io_deps.create_csv_template_fn or (lambda _n: "")  # WHY: safe fallback.
        site_names = VirtualChassisManager._load_site_names_from_csv(  # WHY: user-provided target list.
            io_deps.get_csv_path_fn, template_fn, safe_input_fn
        )
        if not site_names:  # WHY: empty VCConvert.CSV means nothing to do.
            return [], {}  # WHY: caller uses truthiness to bail out.
        print(f"! Loaded {len(site_names)} site names from VCConvert.CSV:")  # WHY: echo count.
        for idx, name in enumerate(site_names):  # WHY: enumerate loaded targets for the operator.
            print(f"  [{idx + 1}] {name}")  # WHY: 1-indexed for humans.
        io_deps.check_and_generate_csv_fn("OrgInventory.csv", io_deps.inventory_generator)  # WHY: refresh.
        io_deps.check_and_generate_csv_fn("SiteList.csv", io_deps.sites_generator)  # WHY: refresh mapping.
        site_name_to_id = VirtualChassisManager._load_site_name_mapping(io_deps.get_csv_path_fn)  # WHY.
        if not site_name_to_id:  # WHY: cannot resolve names without mapping.
            return [], {}  # WHY: caller uses truthiness to bail out.
        target_ids, missing = VirtualChassisManager._resolve_site_ids(site_names, site_name_to_id)  # WHY.
        VirtualChassisManager._report_missing_sites(missing, target_ids)  # WHY: user-facing feedback.
        return target_ids, site_name_to_id  # WHY: caller decides next step.

    @staticmethod
    def _report_missing_sites(missing: list[str], target_ids: list[str]) -> None:
        """Emit warnings/errors for sites that could not be resolved."""
        if missing:  # WHY: only print warning when there are unresolved names.
            print("! Warning: The following sites were not found in the organization:")  # WHY: warn.
            for site in missing:  # WHY: enumerate the unresolved names for operator triage.
                print(f"   - {site}")  # WHY: indented for readability.
        if not target_ids:  # WHY: no valid targets == fatal for bulk.
            print(" No valid sites found. Exiting.")  # WHY: clear operator feedback.
            logging.error("No valid sites found for VC conversion.")  # WHY: audit failure.

    @staticmethod
    def _confirm_bulk(safe_input_fn: SafeInputFn) -> bool:
        """Ask the operator to type CONVERT to proceed with a bulk conversion."""
        confirm = safe_input_fn(  # WHY: hard confirmation for destructive bulk operation.
            "\nType 'CONVERT' to proceed with bulk conversion or anything else to cancel: ",
            context="vc_bulk_conversion",
        )
        if confirm != "CONVERT":  # WHY: only literal CONVERT proceeds.
            print(" Conversion cancelled by user.")  # WHY: visible cancellation.
            logging.info("Virtual chassis conversion cancelled by user.")  # WHY: audit cancellation.
            return False  # WHY: caller bails out.
        return True  # WHY: proceed with bulk execution.

    # ------------------------------------------------------------------
    # check_status helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_status_banner() -> None:
        """Print the check-status banner and explanation of prefix semantics."""
        print("\n  Virtual Chassis to Virtual MAC Conversion Status Check")  # WHY: banner.
        print("=" * 70)  # WHY: visual separator.
        print(" Checking all switches for virtual chassis conversion status...")  # WHY: progress.
        print(f" Converted switches have vc_mac starting with '{_CONVERTED_PREFIX}'")  # WHY: legend.

    @staticmethod
    def _print_no_vc_switches() -> None:
        """Emit operator-visible message when no VC switches are found."""
        print(" No switches with vc_mac found in the organization.")  # WHY: primary message.
        print(" Only virtual chassis switches have vc_mac assigned.")  # WHY: educational hint.
        logging.warning("No switches with vc_mac found.")  # WHY: audit warning.

    @staticmethod
    def _classify_status(
        vc_switches: list[dict[str, Any]],
        io_deps: VCIODeps,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Enrich switches with site names and split into converted / not_converted."""
        site_id_to_name = VirtualChassisManager._load_site_id_mapping(  # WHY: reverse mapping for names.
            io_deps.get_csv_path_fn, io_deps.check_and_generate_csv_fn, io_deps.sites_generator
        )
        return VirtualChassisManager._analyze_conversion_status(vc_switches, site_id_to_name)  # WHY: split.

    @staticmethod
    def _print_status_usage_notes() -> None:
        """Print the closing usage-notes block for the status report."""
        print("\n  Usage Notes:")  # WHY: guidance header.
        print("   !? Use option 92 to convert individual switches")  # WHY: cross-reference menu 92.
        print("   !? Use option 93 for bulk conversion by site list")  # WHY: cross-reference menu 93.
        print(  # WHY: eligibility hint for uncoverted switches.
            f"   !? Virtual chassis switches without '{_CONVERTED_PREFIX}' vc_mac prefix can be converted"
        )

    # ------------------------------------------------------------------
    # API helpers (require apisession)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_site_name(apisession: Any, site_id: str) -> str:
        """Fetch site name from API, falling back to a placeholder on failure."""
        import mistapi  # WHY: lazy import keeps module light for unit tests.

        try:
            response = mistapi.api.v1.sites.getSite(apisession, site_id)  # WHY: mistapi call.
            if response.data:  # WHY: guard against empty response body.
                return str(response.data.get("name", site_id))  # WHY: prefer name, fallback to id.
        except Exception as exc:  # WHY: any network / auth failure is non-fatal for display.
            logging.warning("Could not fetch site name for %s: %s", site_id, exc)  # WHY: audit warn.
        return "Unknown Site"  # WHY: safe placeholder.

    @staticmethod
    def _execute_conversion(
        apisession: Any,
        site_id: str,
        device_id: str,
        switch_name: str,
        site_name: str,
    ) -> None:
        """Execute API call to convert one switch to virtual MAC."""
        import mistapi  # WHY: lazy import; module is import-free without a session.

        print(  # WHY: pre-call progress message.
            f"! Converting switch '{switch_name}' (device_id: {device_id}) at site '{site_name}' to virtual MAC..."
        )
        try:
            response = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(  # WHY: real call.
                apisession, site_id, device_id
            )
            VirtualChassisManager._handle_conversion_response(  # WHY: process API response.
                response, device_id, site_id, site_name, switch_name
            )
        except Exception as exc:  # WHY: mistapi errors are surfaced but non-fatal.
            print(f"! Failed to convert to virtual MAC: {exc}")  # WHY: operator-visible error.
            logging.error("Failed to convert to virtual MAC: %s", exc)  # WHY: audit failure.

    @staticmethod
    def _handle_conversion_response(
        response: Any,
        device_id: str,
        site_id: str,
        site_name: str,
        switch_name: str,
    ) -> None:
        """Process API response from a conversion call, printing status."""
        if VirtualChassisManager._log_http_error(response, switch_name, site_name):  # WHY: HTTP-level.
            return  # WHY: HTTP error already reported.
        if VirtualChassisManager._log_detail_error(response, switch_name, site_name):  # WHY: body-level.
            return  # WHY: body-level failure already reported.
        VirtualChassisManager._print_conversion_success(response, device_id, site_id)  # WHY: success.

    @staticmethod
    def _log_http_error(response: Any, switch_name: str, site_name: str) -> bool:
        """Print + log an HTTP >= 400 error; return True when handled."""
        if hasattr(response, "status_code") and response.status_code >= 400:  # WHY: HTTP error path.
            data = getattr(response, "data", "")  # WHY: include payload for context.
            print(f"! Conversion failed (HTTP {response.status_code}): {data}")  # WHY: operator.
            logging.error(  # WHY: audit the failure with structured fields.
                "Conversion failed for %s at %s. HTTP %s",
                switch_name,
                site_name,
                response.status_code,
            )
            return True  # WHY: caller should stop processing.
        return False  # WHY: no HTTP error; caller continues checking body.

    @staticmethod
    def _log_detail_error(response: Any, switch_name: str, site_name: str) -> bool:
        """Print + log a body-level detail error; return True when handled."""
        resp_data = getattr(response, "data", None)  # WHY: normalize access to payload.
        if isinstance(resp_data, dict) and "detail" in resp_data:  # WHY: mistapi body error shape.
            print(f"! Conversion failed: {resp_data['detail']}")  # WHY: operator feedback.
            logging.error(  # WHY: audit with the returned detail message.
                "Conversion failed for %s at %s. Detail: %s",
                switch_name,
                site_name,
                resp_data["detail"],
            )
            return True  # WHY: caller should stop processing.
        return False  # WHY: no body-level error detected.

    @staticmethod
    def _print_conversion_success(response: Any, device_id: str, site_id: str) -> None:
        """Print success message and rollback guidance after a conversion trigger."""
        print(" Conversion to virtual MAC triggered successfully!")  # WHY: primary success msg.
        print(" Check the device status in the Mist UI to monitor progress.")  # WHY: next step.
        print("\n  Rollback Guidance:")  # WHY: rollback header.
        print("   If the conversion causes issues, contact Juniper TAC.")  # WHY: escalation path.
        print("   The device may need a factory reset and re-adoption to revert.")  # WHY: recovery note.
        print("   Use Menu 94 to verify conversion status after the device reboots.")  # WHY: verification.
        logging.info(  # WHY: audit successful trigger with correlation ids.
            "Conversion triggered for device %s at site %s. Response: %s",
            device_id,
            site_id,
            getattr(response, "data", ""),
        )

    @staticmethod
    def _execute_bulk_conversion(apisession: Any, switches: list[dict[str, Any]]) -> None:
        """Execute conversion for multiple switches sequentially."""
        print(f"\n  Starting conversion of {len(switches)} switches...")  # WHY: batch banner.
        successful = 0  # WHY: counter for summary.
        failed = 0  # WHY: counter for summary.
        for idx, switch in enumerate(switches):  # WHY: iterate one at a time to isolate errors.
            if VirtualChassisManager._convert_one_from_bulk(apisession, switch, idx, len(switches)):
                successful += 1  # WHY: success bookkeeping.
            else:
                failed += 1  # WHY: failure bookkeeping.
        VirtualChassisManager._print_bulk_summary(successful, failed, len(switches))  # WHY: final report.

    @staticmethod
    def _convert_one_from_bulk(
        apisession: Any,
        switch: dict[str, Any],
        idx: int,
        total: int,
    ) -> bool:
        """Convert one switch inside the bulk loop; return True on success."""
        switch_name = switch.get("name", "")  # WHY: user-visible identifier for progress banner.
        site_name = switch.get("site_name", "")  # WHY: user-visible identifier for progress banner.
        print(f"\n[{idx + 1}/{total}] Converting '{switch_name}' at site '{site_name}'...")  # WHY: progress.
        return VirtualChassisManager._call_convert_api(apisession, switch)  # WHY: delegated API call.

    @staticmethod
    def _call_convert_api(apisession: Any, switch: dict[str, Any]) -> bool:
        """Call mistapi convert endpoint; return True on success, False on error."""
        import mistapi  # WHY: lazy import keeps module light for unit tests.

        site_id = switch.get("site_id", "")  # WHY: mistapi endpoint requires site_id.
        device_id = switch.get("id", "")  # WHY: mistapi endpoint requires device_id.
        switch_name = switch.get("name", "")  # WHY: used in audit logs and operator output.
        site_name = switch.get("site_name", "")  # WHY: used in audit logs and operator output.
        try:
            response = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(  # WHY: call.
                apisession, site_id, device_id
            )
            if VirtualChassisManager._is_conversion_error(response):  # WHY: HTTP or body error.
                return False  # WHY: caller counts failure.
            print("! Conversion triggered successfully.")  # WHY: success message.
            logging.info("Conversion triggered for %s at %s.", switch_name, site_name)  # WHY: audit.
            return True  # WHY: caller counts success.
        except Exception as exc:  # WHY: guard against network/mistapi exceptions.
            print(f"! Exception during conversion: {exc}")  # WHY: operator-visible.
            logging.error(  # WHY: audit exception with structured fields.
                "Exception during conversion of %s at %s: %s", switch_name, site_name, exc
            )
            return False  # WHY: caller counts failure.

    # ------------------------------------------------------------------
    # CSV / file helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_site_switches(
        site_id: str,
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        inventory_generator: Any,
    ) -> list[dict[str, Any]]:
        """Load switches at a specific site from cached inventory."""
        check_and_generate_csv_fn("OrgInventory.csv", inventory_generator)  # WHY: refresh cache.
        path = get_csv_path_fn("OrgInventory.csv")  # WHY: resolve cache path.
        with open(path, encoding="utf-8") as csvfile:  # WHY: read the freshly-cached inventory.
            reader = list(csv.DictReader(csvfile))  # WHY: materialize rows for filtering.
            return [  # WHY: return switches at this site with a real device id.
                row
                for row in reader
                if (row.get("type") == "switch" and row.get("id", "").strip() and row.get("site_id") == site_id)
            ]

    @staticmethod
    def _load_site_names_from_csv(
        get_csv_path_fn: GetCsvPathFn,
        create_csv_template_fn: CreateCsvTemplateFn,
        safe_input_fn: SafeInputFn,
    ) -> list[str]:
        """Load site names from VCConvert.CSV, prompting to create it if missing."""
        csv_path = get_csv_path_fn("VCConvert.CSV")  # WHY: resolve the target VCConvert path.
        if not os.path.exists(csv_path):  # WHY: prompt on missing file.
            VirtualChassisManager._handle_missing_csv(csv_path, create_csv_template_fn, safe_input_fn)
            return []  # WHY: nothing loaded when file does not exist.
        return VirtualChassisManager._read_vc_site_names(csv_path)  # WHY: pure read helper.

    @staticmethod
    def _read_vc_site_names(csv_path: str) -> list[str]:
        """Read non-blank site names from a VCConvert.CSV, tolerating read errors."""
        try:
            site_names: list[str] = []  # WHY: accumulator for non-empty first-column values.
            with open(csv_path, encoding="utf-8") as csvfile:  # WHY: open for reading.
                for row in csv.reader(csvfile):  # WHY: iterate rows one-by-one.
                    if row and row[0].strip():  # WHY: skip blank rows / blank first cells.
                        site_names.append(row[0].strip())  # WHY: keep normalized names.
            return site_names  # WHY: return the accumulated list.
        except Exception as exc:  # WHY: file permission / decode errors are non-fatal.
            print(f"! Error reading VCConvert.CSV: {exc}")  # WHY: operator feedback.
            logging.error("Error reading VCConvert.CSV: %s", exc)  # WHY: audit failure.
            return []  # WHY: safe fallback.

    @staticmethod
    def _handle_missing_csv(
        csv_path: str,
        create_csv_template_fn: CreateCsvTemplateFn,
        safe_input_fn: SafeInputFn,
    ) -> None:
        """Prompt user when VCConvert.CSV is not found and optionally create a template."""
        print("! File 'VCConvert.CSV' not found.")  # WHY: primary error message.
        print(f"   Please create this file at: {csv_path}")  # WHY: show target path.
        print("   This file should contain site names (one per line, no header).")  # WHY: hint.
        answer = VirtualChassisManager._prompt_yes_no(safe_input_fn)  # WHY: extract prompt for length.
        if answer in ("y", "yes"):  # WHY: accept y / yes as affirmative.
            VirtualChassisManager._create_vc_template(create_csv_template_fn)  # WHY: attempt write.
        logging.error("VCConvert.CSV file not found.")  # WHY: audit the missing-file case.

    @staticmethod
    def _prompt_yes_no(safe_input_fn: SafeInputFn) -> str:
        """Prompt the operator to create an empty VCConvert template; return normalized answer."""
        return (  # WHY: normalize input to lower-case stripped string for comparison.
            safe_input_fn(
                "   Would you like to create an empty file to get started? (y/n): ",
                context="vc_csv_create",
            )
            .strip()
            .lower()
        )

    @staticmethod
    def _create_vc_template(create_csv_template_fn: CreateCsvTemplateFn) -> None:
        """Attempt to create the VCConvert.CSV template, reporting result to operator."""
        try:
            path = create_csv_template_fn("VCConvert.CSV")  # WHY: writes empty template.
            print(f"! Empty file created at: {path}")  # WHY: confirm success.
            print("   Please edit the file to add your site names and run the script again.")  # WHY: hint.
        except Exception as exc:  # WHY: file write may fail due to permissions.
            print(f"! Failed to create file: {exc}")  # WHY: operator-visible error.

    @staticmethod
    def _load_site_name_mapping(
        get_csv_path_fn: GetCsvPathFn,
    ) -> dict[str, str]:
        """Load site name-to-ID mapping from cached SiteList.csv."""
        try:
            path = get_csv_path_fn("SiteList.csv")  # WHY: resolve mapping cache path.
            with open(path, encoding="utf-8") as csvfile:  # WHY: read the mapping.
                reader = csv.DictReader(csvfile)  # WHY: parse header row for name/id columns.
                return {row.get("name", ""): row.get("id", "") for row in reader}  # WHY: build dict.
        except Exception as exc:  # WHY: missing cache or decode error is non-fatal.
            print(f"! Error reading SiteList.csv: {exc}")  # WHY: operator feedback.
            logging.error("Error reading SiteList.csv: %s", exc)  # WHY: audit failure.
            return {}  # WHY: safe fallback.

    @staticmethod
    def _load_switches_for_sites(
        target_site_ids: list[str],
        site_name_to_id: dict[str, str],
        get_csv_path_fn: GetCsvPathFn,
    ) -> list[dict[str, Any]]:
        """Load switches from inventory for specific sites, enriched with site names."""
        try:
            path = get_csv_path_fn("OrgInventory.csv")  # WHY: resolve inventory cache path.
            switches: list[dict[str, Any]] = []  # WHY: accumulator for matching switches.
            with open(path, encoding="utf-8") as csvfile:  # WHY: read inventory.
                for row in csv.DictReader(csvfile):  # WHY: iterate rows.
                    if not VirtualChassisManager._is_target_switch(row, target_site_ids):  # WHY: filter.
                        continue  # WHY: skip non-matching rows.
                    site_name = VirtualChassisManager._reverse_lookup(  # WHY: enrich with site name.
                        row.get("site_id", ""), site_name_to_id
                    )
                    row["site_name"] = site_name  # WHY: annotate row for display.
                    switches.append(row)  # WHY: collect the matching switch.
            return switches  # WHY: return the accumulated list.
        except Exception as exc:  # WHY: missing cache is non-fatal.
            print(f"! Error reading OrgInventory.csv: {exc}")  # WHY: operator feedback.
            logging.error("Error reading OrgInventory.csv: %s", exc)  # WHY: audit failure.
            return []  # WHY: safe fallback.

    @staticmethod
    def _load_vc_switches(
        get_csv_path_fn: GetCsvPathFn,
    ) -> list[dict[str, Any]]:
        """Load all switches with vc_mac from inventory."""
        try:
            path = get_csv_path_fn("OrgInventory.csv")  # WHY: resolve inventory path.
            switches: list[dict[str, Any]] = []  # WHY: accumulator.
            with open(path, encoding="utf-8") as csvfile:  # WHY: read inventory.
                for row in csv.DictReader(csvfile):  # WHY: iterate rows.
                    if row.get("type") == "switch" and row.get("vc_mac", "").strip():  # WHY: filter.
                        switches.append(row)  # WHY: keep only VC-eligible switches.
            return switches  # WHY: return the collected VC switches.
        except Exception as exc:  # WHY: missing cache is non-fatal.
            print(f"! Error reading OrgInventory.csv: {exc}")  # WHY: operator feedback.
            logging.error("Error reading OrgInventory.csv: %s", exc)  # WHY: audit failure.
            return []  # WHY: safe fallback.

    @staticmethod
    def _load_site_id_mapping(
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        sites_generator: Any,
    ) -> dict[str, str]:
        """Load site ID-to-name mapping from cached CSV."""
        try:
            check_and_generate_csv_fn("SiteList.csv", sites_generator)  # WHY: ensure cache is fresh.
            path = get_csv_path_fn("SiteList.csv")  # WHY: resolve cache path.
            with open(path, encoding="utf-8") as csvfile:  # WHY: read mapping.
                reader = csv.DictReader(csvfile)  # WHY: header-based read.
                return {row.get("id", ""): row.get("name", "Unknown Site") for row in reader}  # WHY: map.
        except Exception as exc:  # WHY: missing cache or decode error is non-fatal.
            logging.warning("Could not load site names: %s", exc)  # WHY: audit warn.
            return {}  # WHY: safe fallback.

    # ------------------------------------------------------------------
    # User-interaction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prompt_switch_selection(
        switches: list[dict[str, Any]],
        site_name: str,
        safe_input_fn: SafeInputFn,
    ) -> dict[str, Any] | None:
        """Display switches and prompt user for selection by index or name."""
        index_map, name_map = VirtualChassisManager._render_switch_options(switches, site_name)  # WHY.
        user_input = safe_input_fn(  # WHY: capture operator input for selection.
            f"\nEnter the index or switch name to convert to virtual MAC [0-{len(switches) - 1}]: ",
            context="vc_switch_selection",
        ).strip()  # WHY: strip whitespace for tolerant matching.
        if user_input.isdigit():  # WHY: numeric input is an index into the list.
            return index_map.get(int(user_input))  # WHY: return switch or None if out of range.
        return name_map.get(user_input)  # WHY: fallback to name lookup.

    @staticmethod
    def _render_switch_options(
        switches: list[dict[str, Any]],
        site_name: str,
    ) -> tuple[dict[int, dict[str, Any]], dict[str, dict[str, Any]]]:
        """Print each switch line and return index / name maps for selection."""
        print(f"\n  Available Virtual Chassis Switches at '{site_name}':")  # WHY: header.
        print("-" * 80)  # WHY: visual separator.
        index_map: dict[int, dict[str, Any]] = {}  # WHY: map integer index to switch.
        name_map: dict[str, dict[str, Any]] = {}  # WHY: map switch name to switch.
        for idx, switch in enumerate(switches):  # WHY: enumerate to give a numeric selector.
            print(  # WHY: single readable row per switch.
                f"[{idx}] {switch.get('name', ''):20} "
                f"MAC: {switch.get('mac', ''):17} "
                f"Model: {switch.get('model', ''):10} "
                f"Serial: {switch.get('serial', ''):15} "
                f"ID: {switch.get('id', '')}"
            )
            index_map[idx] = switch  # WHY: record positional index.
            name_map[switch.get("name", "")] = switch  # WHY: record by name.
        return index_map, name_map  # WHY: caller uses both maps for tolerant selection.

    @staticmethod
    def _preflight_check(switch: dict[str, Any], safe_input_fn: SafeInputFn) -> bool:
        """Validate switch is eligible for VC-to-virtual-MAC conversion."""
        device_type = switch.get("type", "")  # WHY: mistapi requires type == switch.
        if device_type != "switch":  # WHY: reject anything else.
            print(f"! Preflight FAILED: Device type is '{device_type}', expected 'switch'.")  # WHY: msg.
            logging.error("Preflight: wrong device type '%s' for VC conversion", device_type)  # WHY: audit.
            return False  # WHY: fail preflight.
        device_id = switch.get("id", "").strip()  # WHY: id is required for API call.
        if not device_id:  # WHY: no id == cannot convert.
            print("! Preflight FAILED: Device has no assigned device ID.")  # WHY: operator note.
            logging.error("Preflight: missing device_id for VC conversion")  # WHY: audit.
            return False  # WHY: fail preflight.
        if not VirtualChassisManager._check_already_converted(switch, safe_input_fn):  # WHY: subhelper.
            return False  # WHY: operator declined to re-convert.
        logging.info(  # WHY: audit successful preflight.
            "Preflight passed for switch '%s' (id=%s)", switch.get("name", ""), device_id
        )
        return True  # WHY: eligible for conversion.

    @staticmethod
    def _check_already_converted(
        switch: dict[str, Any],
        safe_input_fn: SafeInputFn,
    ) -> bool:
        """Return True unless switch is already converted and operator declines to proceed."""
        vc_mac = switch.get("vc_mac", "").strip()  # WHY: read current vc_mac for prefix check.
        if not (vc_mac and vc_mac.startswith(_CONVERTED_PREFIX)):  # WHY: not already converted.
            return True  # WHY: nothing to warn about.
        print(f"! Preflight WARNING: Switch '{switch.get('name', '')}' appears already converted.")  # WHY.
        print(f"   vc_mac '{vc_mac}' starts with '{_CONVERTED_PREFIX}' (virtual MAC prefix).")  # WHY: msg.
        proceed = (  # WHY: prompt operator whether to continue despite the warning.
            safe_input_fn("   Continue anyway? (y/n): ", context="vc_preflight_already_converted").strip().lower()
        )
        return proceed in ("y", "yes")  # WHY: True only when operator affirms.

    @staticmethod
    def _confirm_conversion(
        switch: dict[str, Any],
        site_name: str,
        device_id: str,
        safe_input_fn: SafeInputFn,
    ) -> bool:
        """Display warning and get confirmation for destructive operation."""
        print("\n   DESTRUCTIVE OPERATION WARNING ")  # WHY: highlight destructive nature.
        print(f"You are about to convert switch '{switch.get('name', '')}' to virtual MAC.")  # WHY: msg.
        print(f"Site: {site_name}")  # WHY: echo site.
        print(f"Device ID: {device_id}")  # WHY: echo device id.
        print(f"MAC: {switch.get('mac', '')}")  # WHY: echo mac.
        print("This operation cannot be undone!")  # WHY: final warning line.
        confirm = safe_input_fn(  # WHY: require literal CONVERT to proceed.
            "\nType 'CONVERT' to proceed or anything else to cancel: ",
            "",
            True,
            "virtual MAC conversion confirmation",
        )
        return confirm == "CONVERT"  # WHY: only exact match confirms.

    # ------------------------------------------------------------------
    # Pure logic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_site_ids(site_names: list[str], site_name_to_id: dict[str, str]) -> tuple[list[str], list[str]]:
        """Resolve site names to IDs, returning valid IDs and missing names."""
        target_ids: list[str] = []  # WHY: accumulator for resolved ids.
        missing: list[str] = []  # WHY: accumulator for unresolved names.
        for name in site_names:  # WHY: process each requested site name.
            site_id = site_name_to_id.get(name)  # WHY: attempt mapping lookup.
            if site_id:  # WHY: only accept truthy site ids.
                target_ids.append(site_id)  # WHY: record resolved id.
            else:
                missing.append(name)  # WHY: record miss for later warning.
        return target_ids, missing  # WHY: caller uses both lists.

    @staticmethod
    def _analyze_conversion_status(
        switches: list[dict[str, Any]], site_id_to_name: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Classify switches as converted or not based on vc_mac prefix."""
        converted: list[dict[str, Any]] = []  # WHY: accumulator for converted switches.
        not_converted: list[dict[str, Any]] = []  # WHY: accumulator for un-converted switches.
        for switch in switches:  # WHY: classify each switch.
            enhanced = VirtualChassisManager._enrich_status_row(switch, site_id_to_name)  # WHY: annotate.
            if enhanced["conversion_status"] == "CONVERTED":  # WHY: partition after enrichment.
                converted.append(enhanced)  # WHY: converted bucket.
            else:
                not_converted.append(enhanced)  # WHY: not-converted bucket.
        return converted, not_converted  # WHY: return both partitions.

    @staticmethod
    def _enrich_status_row(
        switch: dict[str, Any],
        site_id_to_name: dict[str, str],
    ) -> dict[str, Any]:
        """Copy a switch row and annotate with site_name + conversion_status/notes."""
        vc_mac = switch.get("vc_mac", "")  # WHY: read existing vc_mac for classification.
        site_id = switch.get("site_id", "")  # WHY: read site_id for name mapping.
        enhanced = switch.copy()  # WHY: never mutate the caller's dict.
        enhanced["site_name"] = site_id_to_name.get(site_id, "Unknown Site")  # WHY: enrich for display.
        if vc_mac.startswith(_CONVERTED_PREFIX):  # WHY: prefix decides classification.
            enhanced["conversion_status"] = "CONVERTED"  # WHY: mark as converted.
            enhanced["conversion_notes"] = f"vc_mac starts with {_CONVERTED_PREFIX} - converted to virtual MAC"
        else:
            enhanced["conversion_status"] = "NOT_CONVERTED"  # WHY: mark as not converted.
            enhanced["conversion_notes"] = f"vc_mac starts with {vc_mac[:6]} - not converted to virtual MAC"
        return enhanced  # WHY: caller partitions using conversion_status.

    @staticmethod
    def _is_target_switch(row: dict[str, Any], target_site_ids: list[str]) -> bool:
        """Check if an inventory row is a switch in one of the target sites."""
        return (  # WHY: single-expression predicate keeps CC low.
            row.get("type") == "switch"
            and row.get("site_id", "") in target_site_ids
            and bool(row.get("id", "").strip())
        )

    @staticmethod
    def _reverse_lookup(site_id: str, name_to_id: dict[str, str]) -> str:
        """Find the site name for a given site_id from a name->id map."""
        return next(  # WHY: first matching key or fallback string.
            (name for name, sid in name_to_id.items() if sid == site_id),
            "Unknown Site",
        )

    @staticmethod
    def _is_conversion_error(response: Any) -> bool:
        """Return True if the response indicates a conversion failure."""
        if hasattr(response, "status_code") and response.status_code >= 400:  # WHY: HTTP failure path.
            data = getattr(response, "data", "")  # WHY: include payload for context.
            print(f"! Conversion failed (HTTP {response.status_code}): {data}")  # WHY: operator.
            logging.error("Conversion failed. HTTP %s", response.status_code)  # WHY: audit.
            return True  # WHY: caller treats as failure.
        resp_data = getattr(response, "data", None)  # WHY: check body-level detail error.
        if isinstance(resp_data, dict) and "detail" in resp_data:  # WHY: mistapi body error shape.
            print(f"! Conversion failed: {resp_data['detail']}")  # WHY: operator.
            logging.error("Conversion failed. Detail: %s", resp_data["detail"])  # WHY: audit.
            return True  # WHY: caller treats as failure.
        return False  # WHY: no error detected.

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_dry_run(selected: dict[str, Any], site_name: str, device_id: str, site_id: str) -> None:
        """Print dry-run output for a single conversion."""
        print(f"\n  [DRY RUN] Would convert switch '{selected.get('name', '')}' at site '{site_name}'")  # WHY.
        print(f"  [DRY RUN] Device ID: {device_id}")  # WHY: echo device id.
        print(f"  [DRY RUN] MAC: {selected.get('mac', '')}")  # WHY: echo mac.
        print("  [DRY RUN] No API call made. Use without --dry-run to execute.")  # WHY: closing note.
        logging.info("DRY RUN: Would convert %s at site %s", device_id, site_id)  # WHY: audit.

    @staticmethod
    def _display_switches_for_conversion(
        switches: list[dict[str, Any]],
    ) -> None:
        """Display switches that will be converted."""
        print(f"\n  Found {len(switches)} virtual chassis switches to convert:")  # WHY: banner.
        print("=" * 100)  # WHY: visual separator.
        for idx, switch in enumerate(switches):  # WHY: enumerate for numeric labels.
            print(  # WHY: single-row summary per switch.
                f"[{idx + 1:2}] "
                f"Site: {switch.get('site_name', ''):25} | "
                f"Name: {switch.get('name', ''):20} | "
                f"MAC: {switch.get('mac', ''):17} | "
                f"Model: {switch.get('model', ''):12} | "
                f"Serial: {switch.get('serial', '')}"
            )
        print(f"\n  This will convert {len(switches)} virtual chassis switches to virtual MAC.")  # WHY: msg.
        print(" This operation cannot be undone easily.")  # WHY: final warning.

    @staticmethod
    def _display_status_summary(
        converted: list[dict[str, Any]],
        not_converted: list[dict[str, Any]],
    ) -> None:
        """Display conversion status summary with counts and per-bucket samples."""
        total = len(converted) + len(not_converted)  # WHY: total for headline.
        print("\n  Virtual Chassis Conversion Status Summary:")  # WHY: header.
        print(f"   Total virtual chassis switches: {total}")  # WHY: totals line.
        print(f"   Converted to virtual MAC: {len(converted)}")  # WHY: converted count.
        print(f"   Not converted: {len(not_converted)}")  # WHY: not-converted count.
        VirtualChassisManager._print_status_list(  # WHY: sample of converted rows.
            converted, "Converted", f"vc_mac starts with '{_CONVERTED_PREFIX}'"
        )
        VirtualChassisManager._print_status_list(  # WHY: sample of not-converted rows.
            not_converted, "Not Converted", f"vc_mac does NOT start with '{_CONVERTED_PREFIX}'"
        )

    @staticmethod
    def _print_status_list(switches: list[dict[str, Any]], label: str, description: str) -> None:
        """Print up to 10 switches from a status list."""
        if not switches:  # WHY: avoid printing an empty section header.
            return  # WHY: nothing to display.
        print(f"\n {label} Switches ({description}):")  # WHY: section header.
        for switch in switches[:10]:  # WHY: cap output to first 10 for readability.
            vc_mac_display = switch.get("vc_mac", "")[:8]  # WHY: truncate for compact display.
            print(  # WHY: compact per-switch line.
                f"   !? {switch.get('name', 'Unnamed'):20} | "
                f"Site: {switch.get('site_name', ''):25} | "
                f"vc_mac: {vc_mac_display}..."
            )
        if len(switches) > 10:  # WHY: hint that more rows exist.
            print(f"   ... and {len(switches) - 10} more")  # WHY: tell operator the tail count.

    @staticmethod
    def _print_bulk_summary(successful: int, failed: int, total: int) -> None:
        """Print summary after bulk conversion."""
        print("\n  Conversion Summary:")  # WHY: header.
        print(f"   Successful conversions: {successful}")  # WHY: success count.
        print(f"   Failed conversions: {failed}")  # WHY: failure count.
        print(f"   Total switches processed: {total}")  # WHY: totals line.
        if successful > 0:  # WHY: only nudge when at least one succeeded.
            print("\n  Note: Successful conversions may take a few minutes to complete.")  # WHY: hint.
            print("   Monitor the devices in the Mist portal to confirm the conversion status.")  # WHY: hint.
        logging.info(  # WHY: audit final totals with structured fields.
            "Bulk VC conversion completed: %d successful, %d failed", successful, failed
        )

    @staticmethod
    def _export_status_results(
        all_switches: list[dict[str, Any]],
        flatten_fields_fn: FlattenFieldsFn,
        escape_multiline_fn: EscapeMultilineFn,
        save_data_fn: SaveDataFn,
        get_csv_path_fn: GetCsvPathFn,
    ) -> None:
        """Export conversion status results to CSV."""
        try:
            flattened = flatten_fields_fn(all_switches)  # WHY: flatten nested inventory fields first.
            sanitized = escape_multiline_fn(flattened)  # WHY: escape multiline strings before write.
            filename = "VirtualChassisConversionStatus.csv"  # WHY: fixed export filename.
            save_data_fn(sanitized, filename)  # WHY: physical write to disk.
            print(f"\n  Results exported to: {filename}")  # WHY: confirm success.
            print(f"   Location: {get_csv_path_fn(filename)}")  # WHY: show absolute path.
            logging.info("Virtual chassis conversion status exported to %s", filename)  # WHY: audit.
        except Exception as exc:  # WHY: any transformer / writer error is non-fatal.
            print(f"! Error exporting results: {exc}")  # WHY: operator-visible error.
            logging.error("Error exporting conversion status results: %s", exc)  # WHY: audit failure.
