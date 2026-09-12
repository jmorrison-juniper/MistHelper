"""Report sites where an SSID has no enabled effective WLAN."""

from __future__ import annotations

import importlib
import logging
from datetime import UTC, datetime
from typing import Any

import mistapi

from src.utils.console import echo


class SSIDBroadcastGapReport:
    """Find organization sites that do not broadcast a selected SSID."""

    API_NAME = "ssidBroadcastGapReport"

    @staticmethod
    def execute() -> None:
        """Prompt for an SSID, collect effective WLANs, and write the report."""
        mh = importlib.import_module("MistHelper")  # WHY: resolve live session and shared utilities after startup.
        ssid = mh.InputUtils.safe_input("  Enter the SSID: ", context="ssid_broadcast_gap_report").strip()
        if not ssid:  # WHY: an empty SSID cannot identify a WLAN.
            echo("  The SSID cannot be empty.")
            return
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: use the selected organization.
        sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)  # WHY: include every organization site.
        missing = SSIDBroadcastGapReport._find_missing_sites(
            mh.apisession, sites, ssid
        )  # WHY: inspect effective WLANs.
        SSIDBroadcastGapReport._display(missing, ssid)  # WHY: show the complete result without truncation.
        SSIDBroadcastGapReport._write_outputs(missing, ssid, mh)  # WHY: create the CSV and optional SQLite copy.

    @staticmethod
    def _find_missing_sites(apisession: Any, sites: list[dict[str, Any]], ssid: str) -> list[dict[str, Any]]:
        """Return sites without an enabled WLAN that exactly matches the SSID."""
        missing: list[dict[str, Any]] = []  # WHY: collect report rows in site order.
        for site in sites:  # WHY: evaluate each organization site.
            site_id = str(site.get("id", ""))  # WHY: the derived endpoint requires a site identifier.
            if not site_id:  # WHY: skip malformed site records that cannot be queried.
                logging.warning("Skipping site without an id")  # WHY: surface incomplete API data.
                continue
            response = mistapi.api.v1.sites.wlans.listSiteWlansDerived(
                apisession, site_id, resolve=True
            )  # WHY: resolve template and filter inheritance into effective WLANs.
            wlans = getattr(response, "data", response)  # WHY: support SDK response objects and test lists.
            if not SSIDBroadcastGapReport._has_enabled_ssid(wlans, ssid):  # WHY: report only absent broadcasts.
                missing.append(
                    {
                        "id": f"{site_id}:{ssid}",
                        "site_id": site_id,
                        "site_name": str(site.get("name", "")),
                        "ssid": ssid,
                    }
                )  # WHY: retain a stable row key and operator-readable fields.
        logging.info("SSID gap report found %d sites", len(missing))  # WHY: record report size.
        return missing

    @staticmethod
    def _has_enabled_ssid(wlans: Any, ssid: str) -> bool:
        """Return true when an effective WLAN matches the SSID and remains enabled."""
        for wlan in wlans or []:  # WHY: tolerate an empty derived WLAN response.
            if wlan.get("ssid") == ssid and wlan.get("enabled", True) is not False:  # WHY: SSIDs are case-sensitive.
                return True
        return False

    @staticmethod
    def _display(rows: list[dict[str, Any]], ssid: str) -> None:
        """Display every site in the report."""
        echo("\n--- Sites without enabled SSID broadcast: %s ---", ssid)
        if not rows:  # WHY: distinguish a complete organization from an empty result.
            echo("  No sites match the report.")
            return
        for row in rows:  # WHY: print one complete site name per line without table truncation.
            echo("  %s (%s)", row["site_name"], row["site_id"])

    @staticmethod
    def _write_outputs(rows: list[dict[str, Any]], ssid: str, mh: Any) -> None:
        """Write CSV output and write SQLite output when the process runs in a container."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")  # WHY: make each report file unique.
        filename = f"ssid_broadcast_gaps_{timestamp}.csv"  # WHY: identify the report and its creation time.
        mh.DataExporter.write_with_format_selection(rows, filename, api_function_name=SSIDBroadcastGapReport.API_NAME)
        if mh.EnvironmentUtils.is_running_in_container():  # WHY: local SQLite is required for container runs.
            from src.dataclasses.export_backend_options import ExportBackendOptions

            mh.DataExporter.write_with_format_selection(
                rows,
                filename,
                api_function_name=SSIDBroadcastGapReport.API_NAME,
                backend_options=ExportBackendOptions(format_override="sqlite"),
            )  # WHY: persist the same rows in the local database.
        echo("  Report written to data/%s", filename)
