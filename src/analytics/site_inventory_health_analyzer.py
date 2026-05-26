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
        offline_report = SiteInventoryHealthAnalyzer._find_sites_with_offline_infrastructure(site_inventory, site_lookup)

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
        print("! Fetching device inventory...")
        logging.info("Fetching all organization devices from inventory...")

        try:
            response = deps.mistapi.api.v1.orgs.inventory.getOrgInventory(deps.apisession, org_id, limit=1000)
            devices = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []

            ap_count = sum(1 for device in devices if device.get("type") == "ap")
            switch_count = sum(1 for device in devices if device.get("type") == "switch")
            gateway_count = sum(1 for device in devices if device.get("type") == "gateway")
            connected_count = sum(1 for device in devices if device.get("connected") is True)

            print(
                f"  Found {len(devices)} devices: {ap_count} APs, {switch_count} switches, {gateway_count} gateways ({connected_count} connected)"  # noqa: E501
            )
            logging.info("Fetched %d devices from organization inventory", len(devices))
            return devices
        except Exception as error:  # noqa: BLE001
            logging.error("Failed to fetch devices: %s", error)
            return []

    @staticmethod
    def _group_devices_by_site(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Group devices by site_id and categorize by type."""
        site_inventory: dict[str, dict[str, Any]] = {}

        for device in devices:
            site_id = device.get("site_id", "")
            if not site_id:
                continue

            if site_id not in site_inventory:
                site_inventory[site_id] = {"aps": [], "switches": [], "gateways": []}

            device_type = device.get("type", "")
            device_id = device.get("id", "")
            device_mac = device.get("mac", "")
            device_name = device.get("name", device_mac or device_id or "Unknown")
            device_model = device.get("model", "Unknown")
            device_serial = device.get("serial", "Unknown")

            connected = device.get("connected")
            if connected is True:
                status = "connected"
            elif connected is False:
                status = "disconnected"
            else:
                status = "unknown"

            device_info = {
                "id": device_id,
                "mac": device_mac,
                "name": device_name,
                "model": device_model,
                "serial": device_serial,
                "status": status,
            }

            if device_type == "ap":
                site_inventory[site_id]["aps"].append(device_info)
            elif device_type == "switch":
                site_inventory[site_id]["switches"].append(device_info)
            elif device_type == "gateway":
                site_inventory[site_id]["gateways"].append(device_info)

        return site_inventory

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
        offline_sites: list[dict[str, Any]] = []

        for site_id, inventory in site_inventory.items():
            ap_count = len(inventory["aps"])
            if ap_count == 0:
                continue

            offline_switches = [switch for switch in inventory["switches"] if switch["status"] == "disconnected"]
            offline_gateways = [gateway for gateway in inventory["gateways"] if gateway["status"] == "disconnected"]

            if offline_switches or offline_gateways:
                site_name = site_lookup.get(site_id, "Unknown Site")

                offline_device_details: list[str] = []
                for switch in offline_switches:
                    offline_device_details.append(f"Switch: {switch['name']} ({switch['model']})")
                for gateway in offline_gateways:
                    offline_device_details.append(f"Gateway: {gateway['name']} ({gateway['model']})")

                offline_sites.append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "ap_count": ap_count,
                        "total_switches": len(inventory["switches"]),
                        "offline_switches": len(offline_switches),
                        "total_gateways": len(inventory["gateways"]),
                        "offline_gateways": len(offline_gateways),
                        "offline_devices": "; ".join(offline_device_details),
                        "offline_switch_names": ", ".join([switch["name"] for switch in offline_switches]),
                        "offline_gateway_names": ", ".join([gateway["name"] for gateway in offline_gateways]),
                    }
                )

        return sorted(offline_sites, key=lambda row: row["site_name"])

    @staticmethod
    def _display_results(missing_report: list[dict[str, Any]], offline_report: list[dict[str, Any]]) -> None:
        """Display analysis results to console."""
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)

        print("\n[SITES MISSING INFRASTRUCTURE]")
        print(f"  Sites with APs but missing switch/gateway: {len(missing_report)}")
        if missing_report:
            missing_switches = sum(1 for report in missing_report if "switch" in report["missing_types"])
            missing_gateways = sum(1 for report in missing_report if "gateway" in report["missing_types"])
            print(f"    - Missing switches: {missing_switches}")
            print(f"    - Missing gateways: {missing_gateways}")

            print("\n  Sample sites (first 5):")
            for site in missing_report[:5]:
                print(f"    - {site['site_name']}: {site['ap_count']} APs, missing {site['missing_types']}")

        print("\n[SITES WITH OFFLINE INFRASTRUCTURE]")
        print(f"  Sites with APs and offline switch/gateway: {len(offline_report)}")
        if offline_report:
            total_offline_switches = sum(report["offline_switches"] for report in offline_report)
            total_offline_gateways = sum(report["offline_gateways"] for report in offline_report)
            print(f"    - Total offline switches: {total_offline_switches}")
            print(f"    - Total offline gateways: {total_offline_gateways}")

            print("\n  Sample sites (first 5):")
            for site in offline_report[:5]:
                print(
                    f"    - {site['site_name']}: {site['ap_count']} APs, offline: {site['offline_devices'][:80]}{'...' if len(site['offline_devices']) > 80 else ''}"  # noqa: E501
                )

        print("\n" + "=" * 60)

    @staticmethod
    def _export_results(
        missing_report: list[dict[str, Any]], offline_report: list[dict[str, Any]], deps: SiteInventoryHealthAnalyzerDeps
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
