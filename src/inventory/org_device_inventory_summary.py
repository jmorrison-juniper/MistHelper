"""Org device inventory summary core extracted from MistHelper.py."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from prettytable import PrettyTable

apisession: Any = None
mistapi: Any = None
DataExporter: Any = None
org_id: str = ""


def configure_org_device_inventory_summary_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    data_exporter: Any,
    org_id_value: str,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global mistapi
    global DataExporter
    global org_id

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    DataExporter = data_exporter
    org_id = org_id_value or ""


class OrgDeviceInventorySummaryCore:
    """Core inventory summary logic for a single organization."""

    _DEVICE_TYPES: tuple[str, ...] = ("ap", "switch", "gateway")

    @staticmethod
    def _fetch_switch_physical_inventory(target_org_id: str) -> list[dict]:
        """Fetch switch inventory records with full pagination."""
        logging.info("Fetching switch physical inventory via searchOrgDevices, org=%s", target_org_id)
        all_records: list[dict] = []
        next_url: str | None = None
        page_num: int = 0
        while True:
            page_num += 1
            logging.info("Fetching switch inventory page %d org=%s", page_num, target_org_id)
            try:
                if next_url:
                    response = apisession.mist_get(next_url)
                else:
                    response = mistapi.api.v1.orgs.devices.searchOrgDevices(
                        apisession,
                        target_org_id,
                        type="switch",
                        limit=1000,
                    )
            except Exception as error:
                logging.exception("searchOrgDevices switch page %d failed: %s", page_num, error)
                break
            page_data = getattr(response, "data", None) if response else None
            if not page_data or not isinstance(page_data, dict):
                logging.debug("No dict data on switch inventory page %d - stopping", page_num)
                break
            results: list[dict] = page_data.get("results", [])
            if not results:
                logging.debug("Empty results on switch inventory page %d - done", page_num)
                break
            all_records.extend(results)
            logging.debug(
                "Switch inventory page %d: %d records, total so far: %d / %d",
                page_num,
                len(results),
                len(all_records),
                page_data.get("total", "?"),
            )
            next_url = page_data.get("next")
            if not next_url:
                break
        logging.info("Switch physical inventory complete: %d logical devices org=%s", len(all_records), target_org_id)
        return all_records

    @staticmethod
    def _aggregate_switch_counts(switch_records: list[dict], distinct: str) -> list[dict]:
        """Aggregate switch counts by model/version using num_members for VC accuracy."""
        logging.info("Aggregating switch physical counts by %s from %d records", distinct, len(switch_records))
        counts: dict[str, int] = {}
        for record in switch_records:
            value = record.get(distinct) or "unknown"
            num_members = int(record.get("num_members") or 1)
            counts[value] = counts.get(value, 0) + num_members
        rows = [{"device_type": "switch", distinct: value, "count": count} for value, count in counts.items()]
        rows.sort(key=lambda row: -int(row.get("count", 0)))
        logging.debug("Switch %s aggregation: %d distinct values", distinct, len(rows))
        return rows

    @staticmethod
    def _fetch_gateway_physical_inventory(target_org_id: str) -> list[dict]:
        """Fetch gateway inventory records with vc=True to include HA members."""
        logging.info("Fetching gateway physical inventory via getOrgInventory, org=%s", target_org_id)
        try:
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(
                apisession,
                target_org_id,
                type="gateway",
                vc=True,
                limit=1000,
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)
        except Exception as error:
            logging.exception("getOrgInventory gateway failed: %s", error)
            all_records = []
        logging.info("Gateway physical inventory complete: %d physical devices org=%s", len(all_records), target_org_id)
        return all_records

    @staticmethod
    def _aggregate_gateway_counts(gateway_records: list[dict], distinct: str) -> list[dict]:
        """Aggregate gateway counts by model/version using one record per physical gateway."""
        logging.info("Aggregating gateway physical counts by %s from %d records", distinct, len(gateway_records))
        counts: dict[str, int] = {}
        for record in gateway_records:
            value = record.get(distinct) or "unknown"
            counts[value] = counts.get(value, 0) + 1
        rows = [{"device_type": "gateway", distinct: value, "count": count} for value, count in counts.items()]
        rows.sort(key=lambda row: -int(row.get("count", 0)))
        logging.debug("Gateway %s aggregation: %d distinct values", distinct, len(rows))
        return rows

    @staticmethod
    def _fetch_ap_inventory(target_org_id: str) -> list[dict]:
        """Fetch all claimed APs (assigned + unassigned) from the org inventory."""
        # getOrgInventory is the same data source as the portal "Claim APs" screen, so it returns
        # assigned, unassigned, connected and never-connected APs in one consistent list. Counting
        # APs from here (instead of countOrgDevices) is what keeps claimed-but-never-connected APs
        # from being dropped, because countOrgDevices only returns version-keyed buckets.
        logging.info("Fetching all AP inventory via getOrgInventory, org=%s", target_org_id)
        try:
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # Portal "Claim APs" data source
                apisession,
                target_org_id,
                type="ap",  # APs only; switch and gateway keep their existing counting paths
                limit=1000,  # Large page size minimizes round trips for big inventories
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)  # Auto-paginate
        except Exception as error:  # Inventory fetch errors must not abort the larger summary run
            logging.exception("getOrgInventory AP fetch failed: %s", error)  # Traceback for ops
            all_records = []  # Degrade gracefully so callers simply see no AP rows
        logging.debug("AP inventory fetched: %d records org=%s", len(all_records), target_org_id)  # Record size
        return all_records

    @staticmethod
    def _ap_inventory_bucket(record: dict, distinct: str) -> str:
        """Return the model or version bucket label for a single AP inventory record."""
        # Three-way version rule keeps the three real-world AP states visibly distinct:
        #   unassigned (no site_id), assigned-with-firmware (real version), and assigned-but-
        #   never-connected (no version yet -> "unknown").
        if distinct == "model":  # Model report: count every AP under its real model
            return record.get("model") or "unknown"  # Fall back only when the model is missing
        if not record.get("site_id"):  # Version report: claimed but not assigned to any site
            return "unassigned"  # Dedicated column so operators can see stock at a glance
        return record.get("version") or "unknown"  # Assigned: real firmware, or "unknown" if never connected

    @staticmethod
    def _aggregate_ap_counts(ap_records: list[dict], distinct: str) -> list[dict]:
        """Aggregate AP counts from full inventory so claimed-but-never-connected APs are not lost."""
        # Replaces the old countOrgDevices(distinct="version") path, which silently dropped APs that
        # have never connected and therefore report no firmware version.
        logging.info("Aggregating %d AP inventory records by %s", len(ap_records), distinct)
        counts: dict[str, int] = {}  # bucket label -> running count
        for record in ap_records:  # Walk every claimed AP exactly once
            value = OrgDeviceInventorySummaryCore._ap_inventory_bucket(record, distinct)  # 3-way version / real model
            counts[value] = counts.get(value, 0) + 1  # One inventory record == one physical AP
        rows = [{"device_type": "ap", distinct: value, "count": count} for value, count in counts.items()]
        rows.sort(key=lambda row: -int(row.get("count", 0)))  # Largest buckets first for readability
        logging.debug("AP %s aggregation produced %d buckets", distinct, len(rows))  # Record outcome
        return rows

    @staticmethod
    def _fetch_unassigned_inventory(target_org_id: str) -> list[dict]:
        """Fetch switch inventory that is claimed but not assigned to any site."""
        # Unassigned switches are invisible to searchOrgDevices (assigned-only), so pull the full
        # switch inventory and keep only records that lack a site_id. APs are intentionally excluded
        # here because they are now counted in full from getOrgInventory via _aggregate_ap_counts;
        # including them here too would double-count every unassigned AP.
        logging.info("Fetching unassigned switch inventory via getOrgInventory, org=%s", target_org_id)
        try:
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(  # Inventory API returns claimed stock
                apisession,
                target_org_id,
                type="switch",  # Switch only: APs via _aggregate_ap_counts, gateways via getOrgInventory already
                limit=1000,  # Large page size minimizes round trips for big inventories
            )
            all_records: list[dict] = mistapi.get_all(response=response, mist_session=apisession)  # Auto-paginate
        except Exception as error:  # Inventory fetch errors must not abort the larger summary run
            logging.exception("getOrgInventory unassigned switch failed: %s", error)  # Traceback for ops
            all_records = []  # Degrade gracefully so callers simply see no unassigned rows
        unassigned = [record for record in all_records if not record.get("site_id")]  # site_id empty/None => unassigned
        logging.debug(
            "Unassigned switch inventory: %d of %d records have no site_id",  # Show filter selectivity
            len(unassigned),
            len(all_records),
        )
        return unassigned

    @staticmethod
    def _aggregate_unassigned_counts(unassigned_records: list[dict], distinct: str) -> list[dict]:
        """Aggregate unassigned device counts; firmware rows bucket under an 'unassigned' label."""
        # For the version report we surface unassigned stock as its own bucket (distinct from
        # "unknown", which means an assigned device that never reported firmware). For the model
        # report we keep the real model so per-model totals stay accurate.
        logging.info("Aggregating %d unassigned records by %s", len(unassigned_records), distinct)
        counts: dict[tuple[str, str], int] = {}  # Key on (device_type, bucket) to keep types separate
        for record in unassigned_records:  # Walk each unassigned inventory record once
            device_type = record.get("type") or "unknown"  # Inventory record carries its own ap/switch type
            if distinct == "version":  # Firmware report: collapse all unassigned stock into one column
                value = "unassigned"  # New column the operator can see at a glance
            else:  # Model report: preserve real model so totals merge correctly with assigned counts
                value = record.get(distinct) or "unknown"  # Fall back to "unknown" only if model missing
            key = (device_type, value)  # Compose the grouping key
            counts[key] = counts.get(key, 0) + 1  # Each unassigned record is one physical device (no VC in stock)
        rows = [  # Materialize accumulator into standard row dicts
            {"device_type": device_type, distinct: value, "count": count}
            for (device_type, value), count in counts.items()
        ]
        logging.debug("Unassigned %s aggregation produced %d rows", distinct, len(rows))  # Record outcome
        return rows

    @staticmethod
    def _merge_counts(base_rows: list[dict], extra_rows: list[dict], distinct: str) -> list[dict]:
        """Merge supplemental rows into base rows, summing counts by (device_type, value)."""
        # Used to fold unassigned counts into the assigned-device rows so a model present in both
        # assigned and unassigned states reports one combined total instead of duplicate rows.
        logging.info("Merging %d base and %d supplemental %s rows", len(base_rows), len(extra_rows), distinct)
        combined: dict[tuple[str, str], int] = {}  # Running total per (device_type, value)
        order: list[tuple[str, str]] = []  # Preserve first-seen order for deterministic output
        for row in [*base_rows, *extra_rows]:  # Iterate assigned rows first, then unassigned supplements
            key = (row.get("device_type", ""), row.get(distinct, ""))  # Same grouping key both reports use
            if key not in combined:  # First time we see this key
                combined[key] = 0  # Initialize the bucket
                order.append(key)  # Remember insertion order
            combined[key] += int(row.get("count", 0) or 0)  # Accumulate this row's count
        merged = [  # Rebuild rows from the merged totals in first-seen order
            {"device_type": device_type, distinct: value, "count": combined[(device_type, value)]}
            for (device_type, value) in order
        ]
        logging.debug("Merge produced %d combined %s rows", len(merged), distinct)  # Record outcome
        return merged

    @staticmethod
    def _fetch_all_counts(
        target_org_id: str,
        distinct: str,
        unassigned_records: list[dict] | None = None,
        ap_records: list[dict] | None = None,
    ) -> list[dict]:
        """Fetch grouped counts for AP/switch/gateway by model or version."""
        logging.info("Fetching device %s counts for all types, org=%s", distinct, target_org_id)
        all_rows: list[dict] = []
        for device_type in OrgDeviceInventorySummaryCore._DEVICE_TYPES:
            if device_type == "switch":
                logging.info("Fetching switch %s counts with VC-aware method, org=%s", distinct, target_org_id)
                try:
                    switch_records = OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory(target_org_id)
                    type_rows = OrgDeviceInventorySummaryCore._aggregate_switch_counts(switch_records, distinct)
                    all_rows.extend(type_rows)
                except Exception as error:
                    logging.exception("Switch %s count (VC-aware) failed: %s", distinct, error)
                continue
            if device_type == "gateway":
                logging.info("Fetching gateway %s counts with HA-aware method, org=%s", distinct, target_org_id)
                try:
                    gateway_records = OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory(target_org_id)
                    type_rows = OrgDeviceInventorySummaryCore._aggregate_gateway_counts(gateway_records, distinct)
                    all_rows.extend(type_rows)
                except Exception as error:
                    logging.exception("Gateway %s count (HA-aware) failed: %s", distinct, error)
                continue
            # APs are counted from the full org inventory (the portal "Claim APs" source) so that
            # claimed-but-never-connected APs -- which countOrgDevices(distinct="version") drops --
            # are included. This is the AP branch of the device-type loop.
            try:
                if ap_records is None:  # Direct/test callers may omit the shared fetch; pull it ourselves
                    ap_records = OrgDeviceInventorySummaryCore._fetch_ap_inventory(target_org_id)
                all_rows.extend(OrgDeviceInventorySummaryCore._aggregate_ap_counts(ap_records, distinct))
            except Exception as error:  # AP counting must never abort the combined report
                logging.exception("AP %s count from inventory failed: %s", distinct, error)
        all_rows = OrgDeviceInventorySummaryCore._with_unassigned(all_rows, target_org_id, distinct, unassigned_records)
        all_rows.sort(key=lambda row: (row.get("device_type", ""), -int(row.get("count", 0))))
        logging.info("Total %s count rows after fetch and sort: %d", distinct, len(all_rows))
        return all_rows

    @staticmethod
    def _with_unassigned(
        all_rows: list[dict], target_org_id: str, distinct: str, unassigned_records: list[dict] | None
    ) -> list[dict]:
        """Merge unassigned AP/switch stock into assigned counts so totals are not understated."""
        # Kept as its own method so the primary counting loop stays within the complexity budget.
        if unassigned_records is None:  # Direct/test callers may omit the shared fetch; pull it ourselves
            unassigned_records = OrgDeviceInventorySummaryCore._fetch_unassigned_inventory(target_org_id)
        try:  # Supplemental counting must never break the primary report
            unassigned_rows = OrgDeviceInventorySummaryCore._aggregate_unassigned_counts(unassigned_records, distinct)
            merged = OrgDeviceInventorySummaryCore._merge_counts(all_rows, unassigned_rows, distinct)
            return merged  # Combined assigned + unassigned rows
        except Exception as error:  # Fall back to assigned-only rows on any aggregation/merge failure
            logging.exception("Unassigned %s supplemental count failed: %s", distinct, error)
            return all_rows  # Degrade gracefully to the assigned-only counts

    @staticmethod
    def _display_and_export(rows: list[dict], distinct: str, filename: str, api_func: str) -> None:
        """Render and export summary table for model/version counts."""
        value_col = distinct.capitalize()
        table = PrettyTable()
        table.field_names = ["Device Type", value_col, "Count"]
        for row in rows:
            table.add_row([row.get("device_type", ""), row.get(distinct, ""), row.get("count", 0)])

        print(f"\n{'=' * 62}")
        print(f"  {distinct.capitalize()} Distribution Summary")
        print(f"{'=' * 62}")
        print(table)

        export_rows = [
            {"Device Type": row["device_type"], value_col: row.get(distinct, ""), "Count": row["count"]} for row in rows
        ]
        DataExporter.write_with_format_selection(
            export_rows,
            filename,
            api_function_name=api_func,
        )

    @staticmethod
    def _resolve_safe_org_name(target_org_id: str) -> str:
        """Resolve a filesystem-safe organization name for output prefixes."""
        raw_name: str | None = None
        try:
            org_response = mistapi.api.v1.orgs.orgs.getOrg(apisession, target_org_id)
            raw_name = getattr(org_response, "data", {}).get("name")
        except Exception as error:
            logging.warning("Could not resolve org name from API: %s", error)
        if not raw_name:
            raw_name = os.getenv("END_CUSTOMER_NAME")
        if not raw_name:
            raw_name = target_org_id
        safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in raw_name)
        return safe_name

    @staticmethod
    def run_for_org(target_org_id: str) -> tuple[list[dict], list[dict], list[dict], str]:
        """Run all inventory summaries for one organization and export results."""
        # Lazy imports avoid the circular dependency: collaborators import this module's globals at call time
        from src.inventory.inventory_summary.pivot_renderer import (
            PivotRenderer,
        )  # Local import keeps module load order clean
        from src.inventory.inventory_summary.version_per_model_fetcher import (
            VersionPerModelFetcher,
        )  # Local import keeps module load order clean

        logging.info("Starting org device inventory summary org=%s", target_org_id)
        start_time = time.time()
        safe_org = OrgDeviceInventorySummaryCore._resolve_safe_org_name(target_org_id)

        # Fetch shared inventory once and reuse across every report below so the getOrgInventory
        # calls are not repeated per report. unassigned_records covers unassigned switches; ap_records
        # covers ALL APs (assigned + unassigned) since APs are counted entirely from inventory.
        unassigned_records = OrgDeviceInventorySummaryCore._fetch_unassigned_inventory(target_org_id)
        ap_records = OrgDeviceInventorySummaryCore._fetch_ap_inventory(target_org_id)

        model_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(
            target_org_id, "model", unassigned_records, ap_records
        )
        OrgDeviceInventorySummaryCore._display_and_export(
            model_rows,
            "model",
            f"{safe_org}_OrgDeviceModelCounts",
            "orgDeviceModelSummary",
        )

        version_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(
            target_org_id, "version", unassigned_records, ap_records
        )
        OrgDeviceInventorySummaryCore._display_and_export(
            version_rows,
            "version",
            f"{safe_org}_OrgDeviceFirmwareSummary",
            "orgDeviceFirmwareSummary",
        )

        ver_per_model = VersionPerModelFetcher.fetch(
            target_org_id, model_rows, unassigned_records, ap_records
        )  # Decomposed: per-type version expansion lives in collaborator
        PivotRenderer.render(
            ver_per_model, f"{safe_org}_OrgDeviceVersionPerModel"
        )  # Decomposed: pivot + table + export now in collaborator

        elapsed = time.time() - start_time
        logging.info("Org device inventory summary for %s completed in %.1f seconds", target_org_id, elapsed)
        print(f"\nSummary for {safe_org} completed in {elapsed:.1f} seconds")
        return model_rows, version_rows, ver_per_model, safe_org

    @staticmethod
    def execute() -> None:
        """Run inventory summaries for the currently selected org."""
        if not org_id:
            print("X No organization selected")
            logging.error("OrgDeviceInventorySummaryCore.execute called with empty org_id")
            return
        OrgDeviceInventorySummaryCore.run_for_org(org_id)
