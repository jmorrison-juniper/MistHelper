"""SiteDeviceExporter -- site-level device inventory + stats + port + VC exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 34).
Backs menu options 60 (site devices), 61 (site device stats), 62 (site port stats),
and site device virtual-chassis exports. Direct imports cover stdlib + installed
packages (mistapi, prettytable). Live-global reads (``apisession``,
``DataProcessingUtils``, ``DataExporter``, ``PromptUtils``, ``ConfigUtils``,
``APICoreFetchUtils``, ``SiteExportUtils``, ``PROGRESS_EMITTER``,
``ProgressContext``) are resolved via lazy ``mh = importlib.import_module("MistHelper")``
inside each helper. Callers continue to reach the class through the
``MistHelper.SiteDeviceExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for device-export lifecycle events.
import time  # WHY: measure op_start for port-stats progress reporting.
from typing import Any  # WHY: mistapi response payloads + inventory rows are duck-typed here.

import mistapi  # WHY: direct calls to sites.devices + sites.stats endpoints + get_all pager.
from prettytable import PrettyTable  # WHY: debug-log a formatted inventory table.


class SiteDeviceExporter:
    """Site Device Data Exporter.

    Handles site-level device inventory, stats, port stats, and VC exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def device_inventory(
        site_id: str, device_type: str = "all", csv_filename: str = "SiteInventory.csv"
    ) -> None:  # Export site device inventory.
        """Fetch, export, and display a site's device inventory (CSV + debug table).

        SECURITY: always fetches type=all then filters locally, avoiding Mist's APs-only default.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + DataProcessingUtils/DataExporter.
        logging.info("Fetching device inventory for site_id=%s, device_type=%s", site_id, device_type)  # Log the fetch.
        rawdata = mistapi.api.v1.sites.devices.listSiteDevices(
            mh.apisession, site_id, type="all"
        ).data  # All device types
        if not rawdata:  # No devices.
            print("No devices found for the selected site.")  # Tell the user.
            logging.warning("No devices found for site_id=%s", site_id)  # Warn none found.
            return  # Abort.
        if device_type != "all":  # Type filter requested.
            rawdata = SiteDeviceExporter._filter_devices_by_type(rawdata, device_type, site_id)  # Keep matching types
            if rawdata is None:  # No devices remained after filtering (already logged/printed).
                return  # Abort.
        inventory = sorted(rawdata, key=lambda x: x.get("model", ""))  # Sort by model for easier viewing.
        inventory = mh.DataProcessingUtils.flatten_nested_fields(inventory)  # Flatten nested fields.
        inventory = mh.DataProcessingUtils.escape_multiline(inventory)
        fields = mh.DataProcessingUtils.get_unique_keys(inventory)
        mh.DataExporter.write_with_format_selection(inventory, csv_filename)
        logging.info("Device inventory written to %s (%s rows)", csv_filename, len(inventory))  # Log the write.
        SiteDeviceExporter._display_inventory_table(inventory, fields)  # Debug-log a PrettyTable of the inventory.

    @staticmethod
    def _filter_devices_by_type(
        rawdata: list[dict[str, Any]], device_type: str, site_id: str
    ) -> list[dict[str, Any]] | None:
        """Keep only devices whose type is in the comma-separated device_type; return None when none remain."""
        requested_types = [dtype.strip() for dtype in device_type.split(",")]  # Parse requested types.
        filtered = [d for d in rawdata if d.get("type", "").lower() in requested_types]  # Keep matching devices.
        if not filtered:  # None after filter.
            print(f"No devices of type '{device_type}' found at the selected site.")  # Tell the user.
            logging.warning("No devices of type '%s' found for site_id: %s", device_type, site_id)  # Warn none.
            return None  # Signal the caller to abort.
        return filtered  # Devices matching the requested type(s).

    @staticmethod
    def _display_inventory_table(inventory: list[dict[str, Any]], fields: list[str]) -> None:  # Debug-log a table
        """Build a PrettyTable of the inventory (sorted by model when present) and debug-log it."""
        table = PrettyTable()  # Build the table.
        table.field_names = fields  # Set columns.
        if "model" in fields:  # Model column present.
            try:
                table.sortby = "model"  # Sort by model.
            except Exception as error:  # Sort failed.
                logging.warning("! Could not sort table by 'model': %s", error)  # Warn sort failure.
        for item in inventory:  # Add each row.
            table.add_row([item.get(field, "") for field in fields])  # Build and add the row.
        logging.debug("\n%s", table.get_string())  # Log the table.

    @staticmethod
    def _persist_site_device_stats(rawdata: list[dict[str, Any]], site_name: str) -> None:
        """Flatten + write device-stats rows to a per-site CSV, or tell the user when empty."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if not rawdata:  # No data -- tell the user and return.
            print("! No device statistics found for this site")  # User notice.
            return  # Done.
        flattened_data = mh.DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        sanitized_data = mh.DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe.
        filename = f"SiteDeviceStats_{site_name.replace(' ', '_')}.csv"  # Build per-site CSV name.
        mh.DataExporter.write_with_format_selection(sanitized_data, filename)  # Persist.
        print(f"! {len(rawdata)} device stats exported to {filename}")  # User notice with count.

    @staticmethod
    def _resolve_site_for_stats(export_label: str = "data") -> tuple[str, str] | None:
        """Prompt for a site + org, then return the chosen ``(site_id, site_name)`` or ``None`` to abort."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils + ConfigUtils + APICoreFetchUtils.
        site_id = mh.PromptUtils.select_site()  # Prompt the operator to choose a site
        if not site_id:  # Operator skipped or no sites available
            logging.error("No site selected. Exiting.")
            return None
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org context
        if not current_org_id:  # Org not resolvable -> cannot list sites
            logging.error("No org_id available. Exiting.")
            return None
        sites = mh.APICoreFetchUtils.all_sites_with_limit(current_org_id)  # Look up sites for friendly-name resolution
        site_name = next(
            (site["name"] for site in sites if site["id"] == site_id), site_id
        )  # Friendly name or id fallback
        logging.info("Exporting %s for site: %s", export_label, site_name)  # Trace which site is being exported
        return site_id, site_name

    @staticmethod
    def device_stats() -> None:  # Export site device stats.
        """Export device statistics for a site to SiteDeviceStats.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        print("Site Device Statistics:")  # Header
        logging.info("Starting export of site device statistics...")  # Trace start
        resolved = SiteDeviceExporter._resolve_site_for_stats("device statistics")  # Prompt + org/site resolution
        if resolved is None:  # Abort signaled by resolver
            return
        site_id, site_name = resolved  # Unpack resolved identifiers
        try:
            response = mistapi.api.v1.sites.stats.listSiteDevicesStats(mh.apisession, site_id, type="all", limit=1000)
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows
            SiteDeviceExporter._persist_site_device_stats(rawdata, site_name)  # Persist or tell user empty
        except Exception as e:  # Fetch failed
            logging.error("Error fetching device stats for site %s: %s", site_name, e)  # Log the error
            print(f"! Error fetching device statistics: {e}")  # Tell the user

    @staticmethod
    def port_stats() -> None:  # Export site port stats.
        """Export port statistics for a site to SitePortStats.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of PROGRESS_EMITTER + ProgressContext + SiteExport.
        emitter = mh.PROGRESS_EMITTER  # Progress emitter.
        if emitter:  # Emitter present.
            emitter.emit_progress_start("29", "port_stats", 1)  # Signal progress start.
        op_start = time.time()  # Start the timer.
        mh.SiteExportUtils._export_data(
            api_call=mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts, data_type="port stats", sort_key="mac"
        )
        if emitter:  # Emitter present.
            emitter.emit_progress_complete(mh.ProgressContext("29", "port_stats", 1), 1, False, time.time() - op_start)

    @staticmethod
    def device_virtual_chassis() -> None:  # Export device virtual chassis.
        """Export virtual chassis data for a site to SiteDeviceVirtualChassis.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils.
        print("Export Virtual Chassis Information:")  # Header.
        logging.info("Starting export of site device virtual chassis information...")  # Log start.
        site_id = mh.PromptUtils.select_site()  # Select a site.
        if not site_id:  # No site.
            logging.error("No site selected. Exiting.")  # Log the error.
            return  # Abort.
        # Issue #431: inlined PromptUtils.select_device -> canonical select_device_id_from_inventory.
        device_id = mh.PromptUtils.select_device_id_from_inventory(site_id, device_type="switch")  # Select a switch.
        if not device_id:  # No switch.
            logging.error("No switch device selected. Exiting.")  # Log the error.
            return  # Abort.
        device_name = SiteDeviceExporter._resolve_device_name(site_id, device_id)  # Friendly name (falls back to id).
        logging.info("Exporting virtual chassis information for device: %s", device_name)  # Log the export.
        SiteDeviceExporter._export_vc_for_device(site_id, device_id, device_name)  # Fetch + write + summarize VC data.

    @staticmethod
    def _resolve_device_name(site_id: str, device_id: str) -> str:  # Resolve a device's friendly name
        """Return the device's name from the site device list, falling back to its id when not found."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        response = mistapi.api.v1.sites.devices.listSiteDevices(
            mh.apisession, site_id, type="all"
        )  # List site devices.
        devices = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
        return next(
            (dev["name"] for dev in devices if dev["id"] == device_id), device_id
        )  # type: ignore[no-any-return]  # Name, else the id.

    @staticmethod
    def _export_vc_for_device(site_id: str, device_id: str, device_name: str) -> None:  # Fetch + write VC data
        """Fetch the device's virtual chassis, write it to a CSV, and print a short summary (non-fatal on error)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + DataProcessingUtils/DataExporter.
        try:
            response = mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(
                mh.apisession, site_id, device_id
            )  # Fetch
            if not response.data:  # No VC payload.
                logging.warning("! No virtual chassis data returned for device %s", device_name)  # Warn no VC data.
                print(f"! No virtual chassis data found for device {device_name}")  # Tell the user.
                return  # Nothing to export.
            vc_data = [response.data] if isinstance(response.data, dict) else response.data  # Normalize to a list.
            flattened = mh.DataProcessingUtils.flatten_nested_fields(vc_data)  # Flatten nested fields.
            sanitized = mh.DataProcessingUtils.escape_multiline(flattened)
            filename = f"VirtualChassis_{device_name.replace(' ', '_')}.csv"  # Build the CSV name.
            mh.DataExporter.write_with_format_selection(sanitized, filename)
            logging.info("! Virtual chassis information exported to %s", filename)  # Log the export.
            SiteDeviceExporter._print_vc_summary(sanitized, device_name, filename)  # Print a short operator summary.
        except Exception as e:  # Export failed.
            logging.error("! Failed to export virtual chassis information: %s", e)  # Log the error.
            print(f"! Failed to export virtual chassis information: {e}")  # Tell the user.

    @staticmethod
    def _print_vc_summary(sanitized: list[dict[str, Any]], device_name: str, filename: str) -> None:
        """Print a short VC summary (record count, optional members/preprovisioned fields, output path)."""
        if not sanitized:  # No records to summarize.
            return  # Nothing to print.
        print(f"\n!! Virtual Chassis Summary for {device_name}:")  # Header.
        print(f"   * Records exported: {len(sanitized)}")  # Show the count.
        if "members" in sanitized[0]:  # Members present.
            print(f"   * VC members: {sanitized[0].get('members', 'N/A')}")  # Show members.
        if "preprovisioned" in sanitized[0]:  # Preprovisioned present.
            print(f"   * Preprovisioned: {sanitized[0].get('preprovisioned', 'N/A')}")  # Show preprovisioned flag.
        print(f"   * Data saved to: {filename}")  # Show the path.

    @staticmethod
    def _persist_site_devices(rawdata: list[dict[str, Any]], site_name: str) -> None:
        """Flatten + persist site-devices rows to a per-site CSV (or tell the user when empty)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if not rawdata:  # No devices -- tell the user and return.
            print("! No devices found for this site")  # User notice.
            return  # Done.
        flattened_data = mh.DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        sanitized_data = mh.DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe.
        filename = f"SiteDevices_{site_name.replace(' ', '_')}.csv"  # Per-site CSV name.
        mh.DataExporter.write_with_format_selection(sanitized_data, filename)  # Persist.
        print(f"! {len(rawdata)} devices exported to {filename}")  # User notice with count.

    @staticmethod
    def devices() -> None:  # Export site device list.
        """Export device data for a site to SiteDevices.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        print("Site Device List:")  # Header
        logging.info("Starting export of site device list...")  # Trace start
        resolved = SiteDeviceExporter._resolve_site_for_stats("device list")  # Prompt + org/site resolution
        if resolved is None:  # Abort signaled by resolver
            return
        site_id, site_name = resolved  # Unpack resolved identifiers
        try:
            response = mistapi.api.v1.sites.devices.listSiteDevices(mh.apisession, site_id, type="all")
            rawdata = getattr(response, "data", [])  # Unwrap data; default empty
            SiteDeviceExporter._persist_site_devices(rawdata, site_name)  # Persist or tell user empty
        except Exception as e:  # Fetch failed
            logging.error("Error fetching devices for site %s: %s", site_name, e)  # Log the error
            print(f"! Error fetching device data: {e}")  # Tell the user
