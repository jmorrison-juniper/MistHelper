"""Report sites where an SSID has no enabled effective WLAN."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import mistapi

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)
from src.utils.console import echo

logger = logging.getLogger(__name__)  # WHY: keep log records tied to this module.
_HTTP_OK = 200  # WHY: a response double without a status should keep legacy success behavior.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx statuses mean the payload cannot prove emptiness.


def _response_status_code(response: Any) -> int:
    """Return the HTTP status when the SDK response exposes one."""
    status_code = getattr(response, "status_code", _HTTP_OK)  # WHY: old tests use simple response doubles.
    return status_code if isinstance(status_code, int) else _HTTP_OK  # WHY: non-int mock attributes are not statuses.


class SSIDBroadcastGapReport:
    """Find organization sites that do not broadcast a selected SSID."""

    API_NAME = "ssidBroadcastGapReport"

    @staticmethod
    def execute() -> None:
        """Prompt for an SSID, collect effective WLANs, and write the report."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
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
        failed = False  # WHY: suppress the final success count when any site query fails.
        for site in sites:  # WHY: evaluate each organization site.
            site_id = str(site.get("id", ""))  # WHY: the derived endpoint requires a site identifier.
            if not site_id:  # WHY: skip malformed site records that cannot be queried.
                logger.warning("Skipping site without an id")  # WHY: surface incomplete API data.
                continue
            response = mistapi.api.v1.sites.wlans.listSiteWlansDerived(
                apisession, site_id, resolve=True
            )  # WHY: resolve template and filter inheritance into effective WLANs.
            status_code = _response_status_code(response)  # WHY: a 5xx can carry an empty payload without raising.
            if status_code >= _HTTP_ERROR_MIN:  # WHY: a failing HTTP status cannot prove a site misses the SSID.
                logger.error(  # WHY: the operator must see the cloud status instead of a false missing-site row.
                    "The cloud returned HTTP %s for derived WLANs at site %s",
                    status_code,
                    site_id,
                )
                failed = True  # WHY: mark the report incomplete so the final count does not mislead.
                continue  # WHY: preserve the list return while avoiding a false conclusion.
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
        if failed:  # WHY: an incomplete report cannot claim a complete missing-site count.
            return missing  # WHY: preserve the list return while suppressing the false success log.
        logger.info("SSID gap report found %d sites", len(missing))  # WHY: record report size.
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
