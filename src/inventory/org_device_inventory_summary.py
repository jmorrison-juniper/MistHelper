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
                logging.error("searchOrgDevices switch page %d failed: %s", page_num, error, exc_info=True)
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
            logging.error("getOrgInventory gateway failed: %s", error, exc_info=True)
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
    def _fetch_all_counts(target_org_id: str, distinct: str) -> list[dict]:
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
                    logging.error("Switch %s count (VC-aware) failed: %s", distinct, error, exc_info=True)
                continue
            if device_type == "gateway":
                logging.info("Fetching gateway %s counts with HA-aware method, org=%s", distinct, target_org_id)
                try:
                    gateway_records = OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory(target_org_id)
                    type_rows = OrgDeviceInventorySummaryCore._aggregate_gateway_counts(gateway_records, distinct)
                    all_rows.extend(type_rows)
                except Exception as error:
                    logging.error("Gateway %s count (HA-aware) failed: %s", distinct, error, exc_info=True)
                continue
            try:
                response = mistapi.api.v1.orgs.devices.countOrgDevices(
                    apisession,
                    target_org_id,
                    distinct=distinct,
                    type=device_type,
                    limit=1000,
                )
                data = response.data if response and response.data else {}
                results = data.get("results", [])
                all_rows.extend(
                    {
                        "device_type": device_type,
                        distinct: item.get(distinct, "unknown"),
                        "count": item.get("count", 0),
                    }
                    for item in results
                )
            except Exception as error:
                logging.error(
                    "countOrgDevices distinct=%s type=%s failed: %s",
                    distinct,
                    device_type,
                    error,
                    exc_info=True,
                )
        all_rows.sort(key=lambda row: (row.get("device_type", ""), -int(row.get("count", 0))))
        logging.info("Total %s count rows after fetch and sort: %d", distinct, len(all_rows))
        return all_rows

    @staticmethod
    def _fetch_versions_per_model(target_org_id: str, model_rows: list[dict]) -> list[dict]:
        """Fetch version distribution per model with VC/HA-aware logic."""
        logging.info("Fetching version distribution per model, org=%s", target_org_id)
        all_rows: list[dict] = []
        has_switches = any(row.get("device_type") == "switch" for row in model_rows)
        switch_records: list[dict] = []
        if has_switches:
            try:
                switch_records = OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory(target_org_id)
            except Exception as error:
                logging.error("Switch inventory pre-fetch failed: %s", error, exc_info=True)
        has_gateways = any(row.get("device_type") == "gateway" for row in model_rows)
        gateway_records: list[dict] = []
        if has_gateways:
            try:
                gateway_records = OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory(target_org_id)
            except Exception as error:
                logging.error("Gateway inventory pre-fetch failed: %s", error, exc_info=True)
        for model_row in model_rows:
            device_type = model_row.get("device_type", "")
            model_name = model_row.get("model", "")
            if not model_name:
                continue
            if device_type == "switch":
                version_counts: dict[str, int] = {}
                for record in switch_records:
                    if record.get("model") != model_name:
                        continue
                    version = record.get("version") or "unknown"
                    num_members = int(record.get("num_members") or 1)
                    version_counts[version] = version_counts.get(version, 0) + num_members
                all_rows.extend(
                    {
                        "device_type": "switch",
                        "model": model_name,
                        "version": version,
                        "count": count,
                    }
                    for version, count in version_counts.items()
                )
                continue
            if device_type == "gateway":
                version_counts_gateway: dict[str, int] = {}
                for record in gateway_records:
                    if record.get("model") != model_name:
                        continue
                    version = record.get("version") or "unknown"
                    version_counts_gateway[version] = version_counts_gateway.get(version, 0) + 1
                all_rows.extend(
                    {
                        "device_type": "gateway",
                        "model": model_name,
                        "version": version,
                        "count": count,
                    }
                    for version, count in version_counts_gateway.items()
                )
                continue
            try:
                response = mistapi.api.v1.orgs.devices.countOrgDevices(
                    apisession,
                    target_org_id,
                    distinct="version",
                    type=device_type,
                    model=model_name,
                    limit=1000,
                )
                data = response.data if response and response.data else {}
                results = data.get("results", [])
                all_rows.extend(
                    {
                        "device_type": device_type,
                        "model": model_name,
                        "version": item.get("version", "unknown"),
                        "count": item.get("count", 0),
                    }
                    for item in results
                )
            except Exception as error:
                logging.error(
                    "countOrgDevices distinct=version type=%s model=%s failed: %s",
                    device_type,
                    model_name,
                    error,
                    exc_info=True,
                )
        all_rows.sort(key=lambda row: (row.get("device_type", ""), row.get("model", ""), -int(row.get("count", 0))))
        logging.info("Total version-per-model rows after fetch and sort: %d", len(all_rows))
        return all_rows

    @staticmethod
    def _display_pivot_and_export(rows: list[dict], filename: str) -> None:
        """Render and export combined version-per-model pivot table."""
        models = sorted({row["model"] for row in rows})
        versions = sorted({row["version"] for row in rows})
        model_type: dict[str, str] = {row["model"]: row["device_type"] for row in rows}
        pivot: dict[str, dict[str, int]] = {model: {} for model in models}
        for row in rows:
            pivot[row["model"]][row["version"]] = row.get("count", 0)

        table = PrettyTable()
        table.field_names = ["Model"] + versions + ["Total"]
        col_totals: dict[str, int] = {version: 0 for version in versions}
        export_rows: list[dict] = []

        for model in models:
            row_counts = [pivot[model].get(version, 0) for version in versions]
            row_total = sum(row_counts)
            for version, count in zip(versions, row_counts, strict=True):
                col_totals[version] += count
            table.add_row([model] + row_counts + [row_total])
            export_row: dict = {"Model": model, "Device Type": model_type.get(model, "")}
            for version in versions:
                export_row[version] = pivot[model].get(version, 0)
            export_row["Total"] = row_total
            export_rows.append(export_row)

        col_total_values = [col_totals[version] for version in versions]
        grand_total = sum(col_total_values)
        table.add_row(["TOTAL"] + col_total_values + [grand_total])

        print(f"\n{'=' * 62}")
        print("  Version Distribution per Model (All Device Types)")
        print(f"{'=' * 62}")
        print(table)

        ordered_fields = ["Model", "Device Type"] + versions + ["Total"]
        DataExporter.write_with_format_selection(
            export_rows,
            filename,
            api_function_name="orgDeviceVersionPerModel",
            fieldnames=ordered_fields,
        )

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
            {"Device Type": row["device_type"], value_col: row.get(distinct, ""), "Count": row["count"]}
            for row in rows
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
        logging.info("Starting org device inventory summary org=%s", target_org_id)
        start_time = time.time()
        safe_org = OrgDeviceInventorySummaryCore._resolve_safe_org_name(target_org_id)

        model_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(target_org_id, "model")
        OrgDeviceInventorySummaryCore._display_and_export(
            model_rows,
            "model",
            f"{safe_org}_OrgDeviceModelCounts",
            "orgDeviceModelSummary",
        )

        version_rows = OrgDeviceInventorySummaryCore._fetch_all_counts(target_org_id, "version")
        OrgDeviceInventorySummaryCore._display_and_export(
            version_rows,
            "version",
            f"{safe_org}_OrgDeviceFirmwareSummary",
            "orgDeviceFirmwareSummary",
        )

        ver_per_model = OrgDeviceInventorySummaryCore._fetch_versions_per_model(target_org_id, model_rows)
        OrgDeviceInventorySummaryCore._display_pivot_and_export(ver_per_model, f"{safe_org}_OrgDeviceVersionPerModel")

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
