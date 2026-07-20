"""Org device inventory summary core extracted from MistHelper.py."""  # WHY: module summary anchor for tooling

from __future__ import annotations  # WHY: PEP 563 keeps annotations lazy for module load speed

import logging  # WHY: structured diagnostics for long-running inventory fetch loops
import os  # WHY: env fallback for org name when API lookup fails
import time  # WHY: wall-clock elapsed reporting for the full org summary run
from collections.abc import Callable  # WHY: PEP 585 canonical location for Callable
from typing import Any  # WHY: apisession / mistapi / DataExporter typed as Any due to injection

from prettytable import PrettyTable  # WHY: console rendering for the operator-facing summary tables

apisession: Any = None  # WHY: mistapi session injected by configure_* to keep the module import-safe
mistapi: Any = None  # WHY: mistapi module injected lazily; direct import would create cycles at load
DataExporter: Any = None  # WHY: exporter injected so tests can substitute a mock without touching disk
org_id: str = ""  # WHY: selected org for execute(); empty string means "no org chosen yet"

_SEPARATOR_WIDTH: int = 62  # WHY: fixed banner width keeps CLI output aligned across reports
_INVENTORY_PAGE_SIZE: int = 1000  # WHY: large page size minimizes round-trips for big inventories
_UNKNOWN: str = "unknown"  # WHY: shared fallback label so bucketing stays consistent across helpers
_UNASSIGNED: str = "unassigned"  # WHY: dedicated bucket keeps stock visible next to assigned firmware


def configure_org_device_inventory_summary_dependencies(  # WHY: dependency-injection seam for orchestrator + tests
    *,
    apisession_dependency: Any,  # WHY: authenticated mistapi session
    mistapi_dependency: Any,  # WHY: mistapi package handle for endpoint calls
    data_exporter: Any,  # WHY: exporter class writing CSV/JSON output
    org_id_value: str,  # WHY: default org used when execute() is called without args
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession  # WHY: mutate module-level session so class helpers can reach it
    global mistapi  # WHY: mutate module-level mistapi handle for later endpoint access
    global DataExporter  # WHY: mutate module-level exporter so exports use the injected implementation
    global org_id  # WHY: retain selected org across subsequent execute() calls

    apisession = apisession_dependency  # WHY: store injected session on the module
    mistapi = mistapi_dependency  # WHY: store injected mistapi module
    DataExporter = data_exporter  # WHY: store injected exporter class
    org_id = org_id_value or ""  # WHY: normalize None to empty string so execute() gate stays simple


class OrgDeviceInventorySummaryCore:  # WHY: single-org inventory summarization pipeline
    """Core inventory summary logic for a single organization."""

    _DEVICE_TYPES: tuple[str, ...] = ("ap", "switch", "gateway")  # WHY: canonical ordering for output rows

    @staticmethod
    def _search_switch_page(target_org_id: str, next_url: str | None) -> dict | None:  # WHY: single-page fetch helper
        """Return one page of switch inventory results or ``None`` when the API errors."""
        try:  # WHY: mistapi raises on transport errors; caller treats None as stop-signal
            response = (  # WHY: continuation URL preserves cursor across pages when present
                apisession.mist_get(next_url)  # WHY: mist_get follows the next-page URL verbatim
                if next_url  # WHY: first page has no continuation, so fall through to primary search
                else mistapi.api.v1.orgs.devices.searchOrgDevices(  # WHY: primary listing endpoint
                    apisession, target_org_id, type="switch", limit=_INVENTORY_PAGE_SIZE
                )
            )
        except Exception as error:  # WHY: any transport failure stops pagination without aborting the run
            logging.exception("searchOrgDevices switch page failed: %s", error)  # WHY: keep traceback for ops
            return None  # WHY: sentinel telling the loop to break gracefully
        page_data = getattr(response, "data", None) if response else None  # WHY: defensive against empty response
        return page_data if isinstance(page_data, dict) else None  # WHY: only dict payloads are usable

    @staticmethod
    def _fetch_switch_physical_inventory(target_org_id: str) -> list[dict]:  # WHY: paginated switch listing
        """Fetch switch inventory records with full pagination."""
        logging.info("Fetching switch physical inventory via searchOrgDevices, org=%s", target_org_id)  # WHY: op trace
        all_records: list[dict] = []  # WHY: accumulator across pages
        next_url: str | None = None  # WHY: cursor for the next page; None means "first request"
        page_num: int = 0  # WHY: counter for log context
        while True:  # WHY: exit conditions live inside via guard clauses to keep complexity flat
            page_num += 1  # WHY: increment before fetch so logs show the page being requested
            page_data = OrgDeviceInventorySummaryCore._search_switch_page(target_org_id, next_url)  # WHY: single page
            if page_data is None:  # WHY: helper returns None on failure or non-dict payload
                break  # WHY: stop pagination on failure without losing already-collected records
            results: list[dict] = page_data.get("results", [])  # WHY: switch records live under "results"
            if not results:  # WHY: empty page means we walked past the last record
                break  # WHY: nothing more to accumulate
            all_records.extend(results)  # WHY: fold this page into the accumulator
            next_url = page_data.get("next")  # WHY: continuation URL for the next iteration
            if not next_url:  # WHY: API omits "next" once the final page is served
                break  # WHY: final page reached; stop looping
        logging.info(  # WHY: summarize outcome once at the end so logs stay quiet during success
            "Switch physical inventory complete: %d logical devices org=%s", len(all_records), target_org_id
        )
        return all_records  # WHY: caller aggregates counts from these raw records

    @staticmethod
    def _aggregate_switch_counts(switch_records: list[dict], distinct: str) -> list[dict]:  # WHY: VC-aware sum
        """Aggregate switch counts by model/version using num_members for VC accuracy."""
        logging.info(  # WHY: op trace preserves visibility for large orgs
            "Aggregating switch physical counts by %s from %d records", distinct, len(switch_records)
        )
        counts: dict[str, int] = {}  # WHY: bucket -> running total
        for record in switch_records:  # WHY: walk every switch exactly once
            value = record.get(distinct) or _UNKNOWN  # WHY: fall back so missing labels don't crash the row build
            num_members = int(record.get("num_members") or 1)  # WHY: VC stacks count as members, not one chassis
            counts[value] = counts.get(value, 0) + num_members  # WHY: sum VC-accurate physical count
        rows = [  # WHY: materialize the accumulator into row dicts for downstream merge
            {"device_type": "switch", distinct: value, "count": count} for value, count in counts.items()
        ]
        rows.sort(key=lambda row: -int(row.get("count", 0)))  # WHY: largest buckets first for readability
        logging.debug("Switch %s aggregation: %d distinct values", distinct, len(rows))  # WHY: outcome trace
        return rows  # WHY: caller may merge with unassigned rows before rendering

    @staticmethod
    def _fetch_gateway_physical_inventory(target_org_id: str) -> list[dict]:  # WHY: HA-aware gateway listing
        """Fetch gateway inventory records with vc=True to include HA members."""
        logging.info("Fetching gateway physical inventory via getOrgInventory, org=%s", target_org_id)  # WHY: op trace
        try:  # WHY: inventory fetch errors must not abort the larger summary run
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: getOrgInventory yields per-node records
                apisession, target_org_id, type="gateway", vc=True, limit=_INVENTORY_PAGE_SIZE
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)  # WHY: auto-paginate
        except Exception as error:  # WHY: degrade gracefully rather than crash the parent report
            logging.exception("getOrgInventory gateway failed: %s", error)  # WHY: traceback for ops
            all_records = []  # WHY: empty list keeps callers happy
        logging.info(  # WHY: summarize outcome once so logs stay quiet during success
            "Gateway physical inventory complete: %d physical devices org=%s", len(all_records), target_org_id
        )
        return all_records  # WHY: caller aggregates counts from these records

    @staticmethod
    def _aggregate_gateway_counts(gateway_records: list[dict], distinct: str) -> list[dict]:  # WHY: per-record sum
        """Aggregate gateway counts by model/version using one record per physical gateway."""
        logging.info(  # WHY: op trace mirrors switch aggregation for parity
            "Aggregating gateway physical counts by %s from %d records", distinct, len(gateway_records)
        )
        counts: dict[str, int] = {}  # WHY: bucket -> physical gateway count
        for record in gateway_records:  # WHY: walk each HA member exactly once
            value = record.get(distinct) or _UNKNOWN  # WHY: fall back so missing labels don't crash the row build
            counts[value] = counts.get(value, 0) + 1  # WHY: one record == one physical gateway
        rows = [  # WHY: materialize the accumulator into row dicts for downstream merge
            {"device_type": "gateway", distinct: value, "count": count} for value, count in counts.items()
        ]
        rows.sort(key=lambda row: -int(row.get("count", 0)))  # WHY: largest buckets first for readability
        logging.debug("Gateway %s aggregation: %d distinct values", distinct, len(rows))  # WHY: outcome trace
        return rows  # WHY: caller may merge with unassigned rows before rendering

    @staticmethod
    def _fetch_ap_inventory(target_org_id: str) -> list[dict]:  # WHY: portal "Claim APs" data source
        """Fetch all claimed APs (assigned + unassigned) from the org inventory."""
        logging.info("Fetching all AP inventory via getOrgInventory, org=%s", target_org_id)  # WHY: op trace
        try:  # WHY: inventory fetch errors must not abort the larger summary run
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: same data as portal claim screen
                apisession, target_org_id, type="ap", limit=_INVENTORY_PAGE_SIZE
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)  # WHY: auto-paginate
        except Exception as error:  # WHY: graceful degradation keeps other reports running
            logging.exception("getOrgInventory AP fetch failed: %s", error)  # WHY: traceback for ops
            all_records = []  # WHY: empty result surfaces no AP rows rather than crashing
        logging.debug("AP inventory fetched: %d records org=%s", len(all_records), target_org_id)  # WHY: outcome
        return all_records  # WHY: caller aggregates by version/model

    @staticmethod
    def _ap_inventory_bucket(record: dict, distinct: str) -> str:  # WHY: 3-way version rule kept in one place
        """Return the model or version bucket label for a single AP inventory record."""
        if distinct == "model":  # WHY: model report always uses the real model regardless of assignment
            return record.get("model") or _UNKNOWN  # WHY: fall back only when the model is missing
        if not record.get("site_id"):  # WHY: version report treats unassigned stock as its own bucket
            return _UNASSIGNED  # WHY: dedicated column so operators can see stock at a glance
        return record.get("version") or _UNKNOWN  # WHY: assigned APs report firmware or "unknown" if never-connected

    @staticmethod
    def _aggregate_ap_counts(ap_records: list[dict], distinct: str) -> list[dict]:  # WHY: full-inventory AP sum
        """Aggregate AP counts from full inventory so claimed-but-never-connected APs are not lost."""
        logging.info("Aggregating %d AP inventory records by %s", len(ap_records), distinct)  # WHY: op trace
        counts: dict[str, int] = {}  # WHY: bucket label -> running count
        for record in ap_records:  # WHY: walk every claimed AP exactly once
            value = OrgDeviceInventorySummaryCore._ap_inventory_bucket(record, distinct)  # WHY: 3-way version rule
            counts[value] = counts.get(value, 0) + 1  # WHY: one inventory record == one physical AP
        rows = [  # WHY: materialize the accumulator into row dicts for downstream merge
            {"device_type": "ap", distinct: value, "count": count} for value, count in counts.items()
        ]
        rows.sort(key=lambda row: -int(row.get("count", 0)))  # WHY: largest buckets first for readability
        logging.debug("AP %s aggregation produced %d buckets", distinct, len(rows))  # WHY: outcome trace
        return rows  # WHY: caller may merge with unassigned rows before rendering

    @staticmethod
    def _fetch_unassigned_inventory(target_org_id: str) -> list[dict]:  # WHY: unassigned switches only
        """Fetch switch inventory that is claimed but not assigned to any site."""
        logging.info("Fetching unassigned switch inventory via getOrgInventory, org=%s", target_org_id)  # WHY: trace
        try:  # WHY: supplemental fetch errors must not break the primary report
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: inventory API returns claimed stock
                apisession, target_org_id, type="switch", limit=_INVENTORY_PAGE_SIZE
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)  # WHY: auto-paginate
        except Exception as error:  # WHY: degrade gracefully so callers simply see no unassigned rows
            logging.exception("getOrgInventory unassigned switch failed: %s", error)  # WHY: traceback for ops
            all_records = []  # WHY: empty on error keeps downstream filters valid
        unassigned = [record for record in all_records if not record.get("site_id")]  # WHY: no site_id => stock
        logging.debug(  # WHY: filter selectivity trace for post-mortem sizing
            "Unassigned switch inventory: %d of %d records have no site_id", len(unassigned), len(all_records)
        )
        return unassigned  # WHY: caller aggregates by version/model

    @staticmethod
    def _unassigned_bucket_value(record: dict, distinct: str) -> str:  # WHY: keep aggregator complexity under budget
        """Return the model or version bucket value for a single unassigned record."""
        if distinct == "version":  # WHY: version report collapses all unassigned stock into one column
            return _UNASSIGNED  # WHY: distinct from "unknown" (assigned but never reported firmware)
        return record.get(distinct) or _UNKNOWN  # WHY: model report preserves real model so totals merge

    @staticmethod
    def _aggregate_unassigned_counts(unassigned_records: list[dict], distinct: str) -> list[dict]:  # WHY: stock rollup
        """Aggregate unassigned device counts; firmware rows bucket under an 'unassigned' label."""
        logging.info("Aggregating %d unassigned records by %s", len(unassigned_records), distinct)  # WHY: op trace
        counts: dict[tuple[str, str], int] = {}  # WHY: key on (device_type, bucket) to keep types separate
        for record in unassigned_records:  # WHY: walk each unassigned inventory record once
            device_type = record.get("type") or _UNKNOWN  # WHY: inventory record carries its own ap/switch type
            value = OrgDeviceInventorySummaryCore._unassigned_bucket_value(record, distinct)  # WHY: reuse rule
            counts[(device_type, value)] = counts.get((device_type, value), 0) + 1  # WHY: one record == one device
        rows = [  # WHY: materialize accumulator into standard row dicts consumed by _merge_counts
            {"device_type": device_type, distinct: value, "count": count}
            for (device_type, value), count in counts.items()
        ]
        logging.debug("Unassigned %s aggregation produced %d rows", distinct, len(rows))  # WHY: outcome trace
        return rows  # WHY: caller merges with assigned rows before rendering

    @staticmethod
    def _merge_counts(base_rows: list[dict], extra_rows: list[dict], distinct: str) -> list[dict]:  # WHY: sum overlaps
        """Merge supplemental rows into base rows, summing counts by (device_type, value)."""
        logging.info(  # WHY: op trace with input sizes eases regressions triage
            "Merging %d base and %d supplemental %s rows", len(base_rows), len(extra_rows), distinct
        )
        combined: dict[tuple[str, str], int] = {}  # WHY: running total per (device_type, value)
        order: list[tuple[str, str]] = []  # WHY: preserve first-seen order for deterministic output
        for row in [*base_rows, *extra_rows]:  # WHY: assigned rows first so their order wins on ties
            key = (row.get("device_type", ""), row.get(distinct, ""))  # WHY: same grouping key both reports use
            if key not in combined:  # WHY: first sighting seeds the bucket
                combined[key] = 0  # WHY: initialize the accumulator entry
                order.append(key)  # WHY: remember insertion order for stable output
            combined[key] += int(row.get("count", 0) or 0)  # WHY: accumulate this row's count
        merged = [  # WHY: rebuild rows from the merged totals in first-seen order
            {"device_type": device_type, distinct: value, "count": combined[(device_type, value)]}
            for (device_type, value) in order
        ]
        logging.debug("Merge produced %d combined %s rows", len(merged), distinct)  # WHY: outcome trace
        return merged  # WHY: caller sorts before rendering

    @staticmethod
    def _fetch_switch_type_rows(target_org_id: str, distinct: str, _ap_records: list[dict] | None) -> list[dict]:
        """Return switch rows using the VC-aware fetch + aggregate pipeline."""  # WHY: dispatch handler for "switch"
        logging.info("Fetching switch %s counts with VC-aware method, org=%s", distinct, target_org_id)  # WHY: trace
        try:  # WHY: never abort the combined report on one type's failure
            records = OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory(target_org_id)  # WHY: paginate
            return OrgDeviceInventorySummaryCore._aggregate_switch_counts(records, distinct)  # WHY: VC-accurate sum
        except Exception as error:  # WHY: swallow so other types still contribute rows
            logging.exception("Switch %s count (VC-aware) failed: %s", distinct, error)  # WHY: traceback for ops
            return []  # WHY: empty rows so downstream merge/sort still work

    @staticmethod
    def _fetch_gateway_type_rows(target_org_id: str, distinct: str, _ap_records: list[dict] | None) -> list[dict]:
        """Return gateway rows using the HA-aware fetch + aggregate pipeline."""  # WHY: dispatch handler for "gateway"
        logging.info("Fetching gateway %s counts with HA-aware method, org=%s", distinct, target_org_id)  # WHY: trace
        try:  # WHY: never abort the combined report on one type's failure
            records = OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory(target_org_id)  # WHY: HA members
            return OrgDeviceInventorySummaryCore._aggregate_gateway_counts(records, distinct)  # WHY: per-record sum
        except Exception as error:  # WHY: swallow so other types still contribute rows
            logging.exception("Gateway %s count (HA-aware) failed: %s", distinct, error)  # WHY: traceback for ops
            return []  # WHY: empty rows so downstream merge/sort still work

    @staticmethod
    def _fetch_ap_type_rows(target_org_id: str, distinct: str, ap_records: list[dict] | None) -> list[dict]:
        """Return AP rows using full inventory so claimed-but-never-connected APs are counted."""  # WHY: AP handler
        try:  # WHY: AP counting must never abort the combined report
            resolved = (  # WHY: direct/test callers may omit the shared fetch; pull it ourselves
                ap_records
                if ap_records is not None
                else OrgDeviceInventorySummaryCore._fetch_ap_inventory(target_org_id)
            )
            return OrgDeviceInventorySummaryCore._aggregate_ap_counts(resolved, distinct)  # WHY: 3-way version rule
        except Exception as error:  # WHY: swallow so other types still contribute rows
            logging.exception("AP %s count from inventory failed: %s", distinct, error)  # WHY: traceback for ops
            return []  # WHY: empty rows so downstream merge/sort still work

    _TYPE_HANDLERS: dict[str, Callable[[str, str, list[dict] | None], list[dict]]] = {}  # WHY: filled below

    @staticmethod
    def _fetch_all_counts(  # WHY: dispatch across device types and merge with unassigned stock
        target_org_id: str,
        distinct: str,
        unassigned_records: list[dict] | None = None,
        ap_records: list[dict] | None = None,
    ) -> list[dict]:
        """Fetch grouped counts for AP/switch/gateway by model or version."""
        logging.info("Fetching device %s counts for all types, org=%s", distinct, target_org_id)  # WHY: op trace
        all_rows: list[dict] = []  # WHY: accumulate rows across every device type
        for device_type in OrgDeviceInventorySummaryCore._DEVICE_TYPES:  # WHY: canonical ordering
            handler = OrgDeviceInventorySummaryCore._TYPE_HANDLERS[device_type]  # WHY: table-driven avoids branching
            all_rows.extend(handler(target_org_id, distinct, ap_records))  # WHY: handler returns [] on failure
        all_rows = OrgDeviceInventorySummaryCore._with_unassigned(  # WHY: fold unassigned stock into totals
            all_rows, target_org_id, distinct, unassigned_records
        )
        all_rows.sort(key=lambda row: (row.get("device_type", ""), -int(row.get("count", 0))))  # WHY: stable output
        logging.info("Total %s count rows after fetch and sort: %d", distinct, len(all_rows))  # WHY: outcome trace
        return all_rows  # WHY: caller renders and exports

    @staticmethod
    def _with_unassigned(  # WHY: kept separate so _fetch_all_counts stays within complexity budget
        all_rows: list[dict], target_org_id: str, distinct: str, unassigned_records: list[dict] | None
    ) -> list[dict]:
        """Merge unassigned AP/switch stock into assigned counts so totals are not understated."""
        resolved = (  # WHY: direct/test callers may omit the shared fetch; pull it ourselves
            unassigned_records
            if unassigned_records is not None
            else OrgDeviceInventorySummaryCore._fetch_unassigned_inventory(target_org_id)
        )
        try:  # WHY: supplemental counting must never break the primary report
            unassigned_rows = OrgDeviceInventorySummaryCore._aggregate_unassigned_counts(resolved, distinct)
            return OrgDeviceInventorySummaryCore._merge_counts(all_rows, unassigned_rows, distinct)  # WHY: sum overlap
        except Exception as error:  # WHY: fall back to assigned-only rows on any aggregation/merge failure
            logging.exception("Unassigned %s supplemental count failed: %s", distinct, error)  # WHY: traceback for ops
            return all_rows  # WHY: degrade gracefully to the assigned-only counts

    @staticmethod
    def _print_summary_banner(distinct: str, table: PrettyTable) -> None:  # WHY: keep display method concise
        """Print the labelled banner and table for one summary."""
        separator = "=" * _SEPARATOR_WIDTH  # WHY: reuse the constant width for both borders
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("\n%s", separator)  # WHY: leading blank line separates from preceding output
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("  %s Distribution Summary", distinct.capitalize())  # WHY: operator label matches column
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info(separator)  # WHY: trailing border closes the banner block
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("%s", table)  # WHY: rendered PrettyTable follows the banner

    @staticmethod
    def _display_and_export(rows: list[dict], distinct: str, filename: str, api_func: str) -> None:  # WHY: I/O leaf
        """Render and export summary table for model/version counts."""
        value_col = distinct.capitalize()  # WHY: header casing matches CLI banner
        table = PrettyTable()  # WHY: pretty console output for interactive users
        table.field_names = ["Device Type", value_col, "Count"]  # WHY: fixed columns for both reports
        for row in rows:  # WHY: emit one row per (device_type, bucket)
            table.add_row([row.get("device_type", ""), row.get(distinct, ""), row.get("count", 0)])  # WHY: defensive
        OrgDeviceInventorySummaryCore._print_summary_banner(distinct, table)  # WHY: shared banner formatter
        export_rows = [  # WHY: exporter expects human-readable column names
            {"Device Type": row["device_type"], value_col: row.get(distinct, ""), "Count": row["count"]} for row in rows
        ]
        DataExporter.write_with_format_selection(export_rows, filename, api_function_name=api_func)  # WHY: persist

    @staticmethod
    def _lookup_org_name_from_api(
        target_org_id: str,
    ) -> str | None:  # WHY: complexity budget for _resolve_safe_org_name
        """Return the API-reported org name, or ``None`` on failure or missing name."""
        try:  # WHY: API failures fall back to env / org id at higher level
            org_response = mistapi.api.v1.orgs.orgs.getOrg(apisession, target_org_id)  # WHY: authoritative name source
        except Exception as error:  # WHY: never break the summary run on a naming lookup
            logging.warning("Could not resolve org name from API: %s", error)  # WHY: warn-only; recovery follows
            return None  # WHY: signal caller to try env / id fallbacks
        return getattr(org_response, "data", {}).get("name")  # WHY: response may be dict-like or missing name key

    @staticmethod
    def _sanitize_name(raw_name: str) -> str:  # WHY: keep filesystem paths safe on every platform
        """Replace non-alphanumeric characters with underscores for safe filenames."""
        return "".join(  # WHY: character-by-character filter avoids regex import
            char if char.isalnum() or char in "-_" else "_" for char in raw_name  # WHY: preserve hyphen/underscore
        )

    @staticmethod
    def _resolve_safe_org_name(target_org_id: str) -> str:  # WHY: filesystem-safe output prefix
        """Resolve a filesystem-safe organization name for output prefixes."""
        raw_name = (  # WHY: prefer API name, then env override, then raw org id
            OrgDeviceInventorySummaryCore._lookup_org_name_from_api(target_org_id)
            or os.getenv("END_CUSTOMER_NAME")
            or target_org_id
        )
        return OrgDeviceInventorySummaryCore._sanitize_name(raw_name)  # WHY: one place normalizes characters

    @staticmethod
    def _run_model_report(
        target_org_id: str, safe_org: str, unassigned_records: list[dict], ap_records: list[dict]
    ) -> list[dict]:  # WHY: keep run_for_org within length budget
        """Compute, render and export the per-model report; return the rows for reuse."""
        model_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(  # WHY: shared fetches reuse across reports
            target_org_id, "model", unassigned_records, ap_records
        )
        OrgDeviceInventorySummaryCore._display_and_export(  # WHY: side-effectful render + write
            model_rows, "model", f"{safe_org}_OrgDeviceModelCounts", "orgDeviceModelSummary"
        )
        return model_rows  # WHY: pivot report needs these rows too

    @staticmethod
    def _run_version_report(
        target_org_id: str, safe_org: str, unassigned_records: list[dict], ap_records: list[dict]
    ) -> list[dict]:  # WHY: mirror of _run_model_report
        """Compute, render and export the per-version report; return the rows."""
        version_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(  # WHY: shared fetches reuse across reports
            target_org_id, "version", unassigned_records, ap_records
        )
        OrgDeviceInventorySummaryCore._display_and_export(  # WHY: side-effectful render + write
            version_rows, "version", f"{safe_org}_OrgDeviceFirmwareSummary", "orgDeviceFirmwareSummary"
        )
        return version_rows  # WHY: caller returns tuple to preserve public API

    @staticmethod
    def _run_pivot_report(
        target_org_id: str,
        safe_org: str,
        model_rows: list[dict],
        unassigned_records: list[dict],
        ap_records: list[dict],
    ) -> list[dict]:  # WHY: collaborator
        """Compute the per-model version pivot; delegate render to PivotRenderer."""
        from src.inventory.inventory_summary.pivot_renderer import PivotRenderer  # WHY: lazy import breaks cycle
        from src.inventory.inventory_summary.version_per_model_fetcher import (
            VersionPerModelFetcher,  # WHY: collaborator owns per-type version expansion
        )

        ver_per_model = VersionPerModelFetcher.fetch(  # WHY: expand model rows into (model, version, count)
            target_org_id, model_rows, unassigned_records, ap_records
        )
        PivotRenderer.render(ver_per_model, f"{safe_org}_OrgDeviceVersionPerModel")  # WHY: pivot + table + export
        return ver_per_model  # WHY: returned to caller for its public tuple

    @staticmethod
    def run_for_org(target_org_id: str) -> tuple[list[dict], list[dict], list[dict], str]:  # WHY: pipeline entry
        """Run all inventory summaries for one organization and export results."""
        logging.info("Starting org device inventory summary org=%s", target_org_id)  # WHY: op trace
        start_time = time.time()  # WHY: elapsed reporting for operator feedback
        safe_org = OrgDeviceInventorySummaryCore._resolve_safe_org_name(target_org_id)  # WHY: file-safe prefix
        unassigned_records = OrgDeviceInventorySummaryCore._fetch_unassigned_inventory(target_org_id)  # WHY: reuse
        ap_records = OrgDeviceInventorySummaryCore._fetch_ap_inventory(target_org_id)  # WHY: reuse across reports
        model_rows = OrgDeviceInventorySummaryCore._run_model_report(  # WHY: per-model report + shared rows
            target_org_id, safe_org, unassigned_records, ap_records
        )
        version_rows = OrgDeviceInventorySummaryCore._run_version_report(  # WHY: per-version report
            target_org_id, safe_org, unassigned_records, ap_records
        )
        ver_per_model = OrgDeviceInventorySummaryCore._run_pivot_report(  # WHY: pivot uses model_rows
            target_org_id, safe_org, model_rows, unassigned_records, ap_records
        )
        elapsed = time.time() - start_time  # WHY: total wall-clock cost of the summary
        logging.info(  # WHY: log outcome so ops can tune inventory volume
            "Org device inventory summary for %s completed in %.1f seconds", target_org_id, elapsed
        )
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("\nSummary for %s completed in %.1f seconds", safe_org, elapsed)  # operator feedback
        return model_rows, version_rows, ver_per_model, safe_org  # WHY: public tuple preserved for callers

    @staticmethod
    def execute() -> None:  # WHY: menu-level entry point requires configured org
        """Run inventory summaries for the currently selected org."""
        if not org_id:  # WHY: guard clause reports the misconfiguration instead of crashing
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logging.info("X No organization selected")  # WHY: user-visible error mirrors the rest of the CLI
            logging.error("OrgDeviceInventorySummaryCore.execute called with empty org_id")  # WHY: audit trail
            return  # WHY: early return keeps the happy path un-indented
        OrgDeviceInventorySummaryCore.run_for_org(org_id)  # WHY: delegate to the parameterized pipeline


OrgDeviceInventorySummaryCore._TYPE_HANDLERS = {  # WHY: initialized after class body so handler refs resolve
    "switch": OrgDeviceInventorySummaryCore._fetch_switch_type_rows,  # WHY: VC-aware switch path
    "gateway": OrgDeviceInventorySummaryCore._fetch_gateway_type_rows,  # WHY: HA-aware gateway path
    "ap": OrgDeviceInventorySummaryCore._fetch_ap_type_rows,  # WHY: full-inventory AP path
}
