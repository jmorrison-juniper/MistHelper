"""Site inventory health analyzer extracted from MistHelper.py."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SiteInventoryHealthAnalyzerDeps:
    """Dependency container for SiteInventoryHealthAnalyzer execution."""

    apisession: Any
    mistapi: Any
    get_org_id_fn: Any
    all_sites_fn: Any
    save_data_fn: Any


class SiteInventoryHealthAnalyzer:
    """Analyzes site inventory health to identify gaps and offline devices."""

    @staticmethod
    def analyze(deps: SiteInventoryHealthAnalyzerDeps) -> None:
        """Main entry point for site inventory health analysis."""
        print("Site Inventory Health Analyzer:")
        print("=" * 60)
        logging.info("Starting site inventory health analysis...")

        current_org_id = deps.get_org_id_fn()
        if not current_org_id:
            print("! No organization selected. Exiting.")
            return

        sites_data = SiteInventoryHealthAnalyzer._fetch_sites(current_org_id, deps)
        devices_data = SiteInventoryHealthAnalyzer._fetch_devices(current_org_id, deps)

        if not sites_data or not devices_data:
            print("! Failed to fetch required data. Please verify API access.")
            return

        site_lookup = {site.get("id"): site.get("name", "Unnamed Site") for site in sites_data}
        site_inventory = SiteInventoryHealthAnalyzer._group_devices_by_site(devices_data)

        missing_report = SiteInventoryHealthAnalyzer._find_sites_missing_infrastructure(site_inventory, site_lookup)
        offline_report = SiteInventoryHealthAnalyzer._find_sites_with_offline_infrastructure(
            site_inventory, site_lookup
        )

        SiteInventoryHealthAnalyzer._display_results(missing_report, offline_report)
        SiteInventoryHealthAnalyzer._export_results(missing_report, offline_report, deps)

        logging.info("Site inventory health analysis complete.")

    @staticmethod
    def _fetch_sites(org_id: str, deps: SiteInventoryHealthAnalyzerDeps) -> list[dict[str, Any]]:
        """Fetch all sites in the organization."""
        print("! Fetching sites...")
        logging.info("Fetching all organization sites...")

        try:
            sites = deps.all_sites_fn(org_id)
            print(f"  Found {len(sites)} sites")
            return sites
        except Exception as error:  # noqa: BLE001
            logging.error("Failed to fetch sites: %s", error)
            return []

    @staticmethod
    def _fetch_devices(org_id: str, deps: SiteInventoryHealthAnalyzerDeps) -> list[dict[str, Any]]:
        """Fetch all devices (inventory) in the organization."""
        print("! Fetching device inventory...")  # User progress message
        logging.info("Fetching all organization devices from inventory...")  # Pre-action log
        try:
            response = deps.mistapi.api.v1.orgs.inventory.getOrgInventory(  # API: first page of inventory
                deps.apisession, org_id, limit=1000
            )
            devices = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Paginate fully
            logging.debug("Fetched %d devices from organization inventory", len(devices))  # Post-action log
            SiteInventoryHealthAnalyzer._print_device_summary(devices)  # Print AP/switch/gateway/connected breakdown
            return devices
        except Exception as error:  # noqa: BLE001 - Mist SDK raises bare Exception subclasses
            logging.error("Failed to fetch devices: %s", error)
            return []

    @staticmethod
    def _print_device_summary(devices: list[dict[str, Any]]) -> None:
        """Print a one-line summary of device counts by type plus connected total."""
        counts = {"ap": 0, "switch": 0, "gateway": 0, "connected": 0}  # Accumulator for tally below
        for device in devices:  # Single pass over the device list
            device_type = device.get("type")  # Categorise by mistapi type field
            if device_type in counts:  # Bump per-type counter when known
                counts[device_type] += 1
            if device.get("connected") is True:  # Connected counter is independent of type
                counts["connected"] += 1
        print(  # noqa: E501
            f"  Found {len(devices)} devices: {counts['ap']} APs, {counts['switch']} switches, "
            f"{counts['gateway']} gateways ({counts['connected']} connected)"
        )

    @staticmethod
    def _group_devices_by_site(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Group devices by site_id and categorize by type."""
        # Maps from raw mistapi device.type -> our per-site bucket key
        type_to_bucket = {"ap": "aps", "switch": "switches", "gateway": "gateways"}
        site_inventory: dict[str, dict[str, Any]] = {}  # site_id -> {aps:[], switches:[], gateways:[]}
        for device in devices:  # Walk every device record once
            site_id = device.get("site_id", "")  # Devices without site_id are unassigned — skip
            if not site_id:
                continue
            bucket_key = type_to_bucket.get(device.get("type", ""))  # Type → bucket name
            if bucket_key is None:  # Unknown / unsupported device type — skip
                continue
            buckets = site_inventory.setdefault(  # Lazily create the per-site bucket dict
                site_id, {"aps": [], "switches": [], "gateways": []}
            )
            buckets[bucket_key].append(SiteInventoryHealthAnalyzer._build_device_info(device))  # Append shape
        return site_inventory

    @staticmethod
    def _build_device_info(device: dict[str, Any]) -> dict[str, Any]:
        """Project a raw device record into our internal info dict (name/model/status)."""
        device_id = device.get("id", "")  # Mist device UUID
        device_mac = device.get("mac", "")  # MAC address (fallback name source)
        return {
            "id": device_id,
            "mac": device_mac,
            "name": device.get("name", device_mac or device_id or "Unknown"),  # Best-available name
            "model": device.get("model", "Unknown"),
            "serial": device.get("serial", "Unknown"),
            "status": SiteInventoryHealthAnalyzer._derive_status(device.get("connected")),  # 3-state
        }

    @staticmethod
    def _derive_status(connected: Any) -> str:
        """Translate the raw ``connected`` flag into a 3-state status string."""
        if connected is True:  # Explicit boolean True → connected
            return "connected"
        if connected is False:  # Explicit boolean False → disconnected
            return "disconnected"
        return "unknown"  # None / missing → unknown

    @staticmethod
    def _find_sites_missing_infrastructure(
        site_inventory: dict[str, dict[str, Any]], site_lookup: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Find sites that have APs but are missing switches or gateways."""
        missing_sites: list[dict[str, Any]] = []

        for site_id, inventory in site_inventory.items():
            ap_count = len(inventory["aps"])
            switch_count = len(inventory["switches"])
            gateway_count = len(inventory["gateways"])

            if ap_count == 0:
                continue

            missing_switch = switch_count == 0
            missing_gateway = gateway_count == 0

            if missing_switch or missing_gateway:
                site_name = site_lookup.get(site_id, "Unknown Site")
                missing_types: list[str] = []
                if missing_switch:
                    missing_types.append("switch")
                if missing_gateway:
                    missing_types.append("gateway")

                missing_sites.append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "ap_count": ap_count,
                        "switch_count": switch_count,
                        "gateway_count": gateway_count,
                        "missing_types": ", ".join(missing_types),
                        "ap_names": ", ".join([ap["name"] for ap in inventory["aps"][:5]])
                        + ("..." if ap_count > 5 else ""),
                    }
                )

        return sorted(missing_sites, key=lambda row: row["site_name"])

    @staticmethod
    def _find_sites_with_offline_infrastructure(
        site_inventory: dict[str, dict[str, Any]], site_lookup: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Find sites with APs where switch or gateway is offline."""
        offline_sites: list[dict[str, Any]] = []  # Accumulator for matching site reports
        for site_id, inventory in site_inventory.items():  # One pass over every site
            entry = SiteInventoryHealthAnalyzer._build_offline_entry(site_id, site_lookup, inventory)
            if entry is not None:  # Append only when this site actually qualifies
                offline_sites.append(entry)
        return sorted(offline_sites, key=lambda row: row["site_name"])  # Stable display order

    @staticmethod
    def _build_offline_entry(
        site_id: str, site_lookup: dict[str, str], inventory: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Build a per-site offline-infrastructure report row, or None when not applicable."""
        ap_count = len(inventory["aps"])  # APs are the trigger for considering this site
        if ap_count == 0:  # Site has no APs → not interesting for this report
            return None
        offline_switches = SiteInventoryHealthAnalyzer._filter_disconnected(inventory["switches"])  # Bad switches
        offline_gateways = SiteInventoryHealthAnalyzer._filter_disconnected(inventory["gateways"])  # Bad GWs
        if not offline_switches and not offline_gateways:  # Everything online → nothing to report
            return None
        offline_device_details = SiteInventoryHealthAnalyzer._format_offline_details(  # Pretty labels
            offline_switches, offline_gateways
        )
        return {
            "site_id": site_id,
            "site_name": site_lookup.get(site_id, "Unknown Site"),  # Friendly name fallback
            "ap_count": ap_count,
            "total_switches": len(inventory["switches"]),
            "offline_switches": len(offline_switches),
            "total_gateways": len(inventory["gateways"]),
            "offline_gateways": len(offline_gateways),
            "offline_devices": "; ".join(offline_device_details),  # Semi-colon joined list for CSV
            "offline_switch_names": ", ".join(s["name"] for s in offline_switches),
            "offline_gateway_names": ", ".join(g["name"] for g in offline_gateways),
        }

    @staticmethod
    def _filter_disconnected(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return the subset of devices whose status is ``disconnected``."""
        return [device for device in devices if device["status"] == "disconnected"]

    @staticmethod
    def _format_offline_details(
        offline_switches: list[dict[str, Any]], offline_gateways: list[dict[str, Any]]
    ) -> list[str]:
        """Format ``Switch: name (model)`` / ``Gateway: name (model)`` labels for the report."""
        switch_labels = [f"Switch: {s['name']} ({s['model']})" for s in offline_switches]
        gateway_labels = [f"Gateway: {g['name']} ({g['model']})" for g in offline_gateways]
        return switch_labels + gateway_labels

    @staticmethod
    def _display_results(missing_report: list[dict[str, Any]], offline_report: list[dict[str, Any]]) -> None:
        """Display analysis results to console."""
        print("\n" + "=" * 60)  # Banner separator
        print("ANALYSIS RESULTS")
        print("=" * 60)
        SiteInventoryHealthAnalyzer._display_missing_section(missing_report)  # Missing-infrastructure block
        SiteInventoryHealthAnalyzer._display_offline_section(offline_report)  # Offline-infrastructure block
        print("\n" + "=" * 60)  # Trailing separator

    @staticmethod
    def _display_missing_section(missing_report: list[dict[str, Any]]) -> None:
        """Console block for sites missing switch/gateway infrastructure."""
        print("\n[SITES MISSING INFRASTRUCTURE]")
        print(f"  Sites with APs but missing switch/gateway: {len(missing_report)}")
        if not missing_report:  # Nothing more to render when the report is empty
            return
        missing_switches = sum(1 for report in missing_report if "switch" in report["missing_types"])
        missing_gateways = sum(1 for report in missing_report if "gateway" in report["missing_types"])
        print(f"    - Missing switches: {missing_switches}")
        print(f"    - Missing gateways: {missing_gateways}")
        print("\n  Sample sites (first 5):")
        for site in missing_report[:5]:  # Bounded preview
            print(f"    - {site['site_name']}: {site['ap_count']} APs, missing {site['missing_types']}")

    @staticmethod
    def _display_offline_section(offline_report: list[dict[str, Any]]) -> None:
        """Console block for sites with offline switch/gateway infrastructure."""
        print("\n[SITES WITH OFFLINE INFRASTRUCTURE]")
        print(f"  Sites with APs and offline switch/gateway: {len(offline_report)}")
        if not offline_report:  # Nothing more to render when the report is empty
            return
        total_offline_switches = sum(report["offline_switches"] for report in offline_report)
        total_offline_gateways = sum(report["offline_gateways"] for report in offline_report)
        print(f"    - Total offline switches: {total_offline_switches}")
        print(f"    - Total offline gateways: {total_offline_gateways}")
        print("\n  Sample sites (first 5):")
        for site in offline_report[:5]:  # Bounded preview
            devices_label = site["offline_devices"]
            suffix = "..." if len(devices_label) > 80 else ""  # Truncate long detail strings
            print(f"    - {site['site_name']}: {site['ap_count']} APs, offline: {devices_label[:80]}{suffix}")

    @staticmethod
    def _export_results(
        missing_report: list[dict[str, Any]],
        offline_report: list[dict[str, Any]],
        deps: SiteInventoryHealthAnalyzerDeps,
    ) -> None:
        """Export analysis results to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if missing_report:
            missing_filename = f"SitesMissingInfrastructure_{timestamp}.csv"
            deps.save_data_fn(
                missing_report,
                missing_filename,
                api_function_name="sitesMissingInfrastructure",
            )
            print(f"! Missing infrastructure report exported to {missing_filename}")
            logging.info("Exported %d sites to %s", len(missing_report), missing_filename)
        else:
            print("! No sites found with missing infrastructure (all sites with APs have switches and gateways)")

        if offline_report:
            offline_filename = f"SitesWithOfflineInfrastructure_{timestamp}.csv"
            deps.save_data_fn(
                offline_report,
                offline_filename,
                api_function_name="sitesWithOfflineInfrastructure",
            )
            print(f"! Offline infrastructure report exported to {offline_filename}")
            logging.info("Exported %d sites to %s", len(offline_report), offline_filename)
        else:
            print("! No sites found with offline infrastructure (all switches and gateways are online)")
