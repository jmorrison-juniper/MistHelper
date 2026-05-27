"""WAN probe device override manager extracted from MistHelper menu 167 flow."""

from __future__ import annotations

import csv
import logging
import os
import traceback
from typing import Any

from tqdm import tqdm

apisession: Any = None
ConfigUtils: Any = None
CacheUtils: Any = None
OrgSiteExporter: Any = None
GatewayExportUtils: Any = None
FilePathUtils: Any = None
InputUtils: Any = None
DataExporter: Any = None
mistapi: Any = None
MIST_SITE_EXCLUDE_PREFIX = ""


def configure_wan_probe_device_override_dependencies(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    *,
    apisession_dependency: Any,
    config_utils: Any,
    cache_utils: Any,
    org_site_exporter: Any,
    gateway_export_utils: Any,
    file_path_utils: Any,
    input_utils: Any,
    data_exporter: Any,
    mistapi_dependency: Any,
    site_exclude_prefix: str,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global ConfigUtils
    global CacheUtils
    global OrgSiteExporter
    global GatewayExportUtils
    global FilePathUtils
    global InputUtils
    global DataExporter
    global mistapi
    global MIST_SITE_EXCLUDE_PREFIX

    apisession = apisession_dependency
    ConfigUtils = config_utils
    CacheUtils = cache_utils
    OrgSiteExporter = org_site_exporter
    GatewayExportUtils = gateway_export_utils
    FilePathUtils = file_path_utils
    InputUtils = input_utils
    DataExporter = data_exporter
    mistapi = mistapi_dependency
    MIST_SITE_EXCLUDE_PREFIX = site_exclude_prefix


class WANProbeDeviceOverrideManager:
    """
    Manages WAN probe configuration for device-level port overrides.

    Menu #167: Configure WAN probe override settings on gateway devices that
    have device-level port overrides. This complements Menu #166 (template-level)
    by targeting ONLY ports that have been overridden from their template.

    Workflow:
        1. User selects a gateway template
        2. Find all sites using that template
        3. Find all gateway devices in those sites
        4. Identify devices with port-level WAN overrides
        5. Apply ICMP probe configuration to ONLY overridden WAN ports

    Default Configuration:
        - probe IPs: ["192.151.29.254", "18.154.184.32"] (override via MIST_WAN_PROBE_IPS)
        - probe_profile: "lte" (override via MIST_WAN_PROBE_PROFILE)
    """

    DEFAULT_PROBE_IPS = [
        ip.strip() for ip in os.getenv("MIST_WAN_PROBE_IPS", "192.151.29.254,18.154.184.32").split(",") if ip.strip()
    ]
    DEFAULT_PROBE_PROFILE = os.getenv("MIST_WAN_PROBE_PROFILE", "lte")

    def __init__(self):  # type: ignore[no-untyped-def]
        """Initialize the WAN Probe Device Override Manager."""
        self.org_id: str | None = None
        self.templates: list[dict[str, Any]] = []
        self.sites: list[dict[str, Any]] = []
        self.probe_ips = self.DEFAULT_PROBE_IPS.copy()
        self.probe_profile = self.DEFAULT_PROBE_PROFILE
        self.selected_template: dict[str, Any] | None = None
        self.template_sites: list[dict[str, Any]] = []

    @classmethod
    def configure(cls, dry_run: bool = False) -> None:
        """
        Menu #167: Configure WAN Probe Override on Device Port Overrides (DESTRUCTIVE)

        Updates wan_probe_override settings for WAN ports that have device-level
        overrides from their gateway template.

        Args:
            dry_run: If True, show what would change without making modifications
        """
        manager = cls()
        manager._execute(dry_run)

    def _execute(self, dry_run: bool) -> None:
        """Main execution flow for device-level WAN probe configuration."""
        self._display_header(dry_run)

        if not self._initialize():
            return

        if not self._load_data():
            return

        if not self._select_template():
            return

        if not self._find_template_sites():
            return

        devices_with_overrides = self._find_devices_with_overrides()
        if not devices_with_overrides:
            return

        self._show_preview(devices_with_overrides, dry_run)

        if not dry_run:
            if not self._confirm_operation(len(devices_with_overrides)):
                return

        results = self._apply_changes(devices_with_overrides, dry_run)
        self._generate_report(results, dry_run)

    def _display_header(self, dry_run: bool) -> None:
        """Display operation header with configuration details."""
        print("\n  DESTRUCTIVE: Configure WAN Probe on Device Port Overrides")
        print("=" * 70)
        if dry_run:
            print("  >> DRY-RUN MODE: No changes will be made to devices")
            print("  >> This will show what WOULD be changed without modifying anything")
        else:
            print("  !? WARNING: This operation modifies gateway device configurations")
            print("  !? Only device-level overridden WAN ports will be modified")
        print("=" * 70)
        print("\n  Probe Configuration:")
        print(f"    Probe IPs: {self.probe_ips}")
        print(f"    Probe Profile: {self.probe_profile}")
        print("=" * 70)
        logging.warning("Menu #167 DESTRUCTIVE: Configure WAN Probe on Device Port Overrides started")

    def _initialize(self) -> bool:
        """Initialize org_id. Returns True on success."""
        self.org_id = ConfigUtils.get_cached_or_prompted_org_id()
        if not self.org_id:
            print(" Failed to get organization ID.")
            logging.error("Menu #167: Could not obtain org_id")
            return False
        return True

    def _load_data(self) -> bool:
        """Load gateway templates and site data. Returns True on success."""
        print("\n  Loading gateway template and site data...")
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtils.templates)
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)

        templates_path = FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")
        with open(templates_path, encoding="utf-8") as file_handle:
            self.templates = list(csv.DictReader(file_handle))

        if not self.templates:
            print(" No gateway templates found.")
            logging.warning("Menu #167: No gateway templates available")
            return False

        sites_path = FilePathUtils.get_csv_path("SiteList.csv")
        with open(sites_path, encoding="utf-8") as file_handle:
            self.sites = list(csv.DictReader(file_handle))

        logging.info("Loaded %s gateway templates and %s sites", len(self.templates), len(self.sites))
        return True

    def _select_template(self) -> bool:
        """Display templates and get user selection. Returns True if selected."""
        templates_sorted = sorted(self.templates, key=lambda t: t.get("name", "").lower())

        template_site_counts: dict[str, int] = {}
        for site in self.sites:
            if MIST_SITE_EXCLUDE_PREFIX and site.get("name", "").startswith(MIST_SITE_EXCLUDE_PREFIX):
                continue
            template_id = site.get("gatewaytemplate_id", "").strip()
            if template_id:
                template_site_counts[template_id] = template_site_counts.get(template_id, 0) + 1

        print(f"\n  Available Gateway Templates ({len(templates_sorted)}):")
        template_list = []
        for idx, template in enumerate(templates_sorted, start=1):
            template_id = template.get("id", "")
            template_name = template.get("name", "Unnamed Template")
            site_count = template_site_counts.get(template_id, 0)
            template_list.append({"id": template_id, "name": template_name, "site_count": site_count})
            print(f"   [{idx}] {template_name} ({site_count} sites)")

        print("\n  Template Selection:")
        print("   Enter a template number to select")
        print("   Or 'cancel' to abort")

        selection = (
            InputUtils.safe_input(
                "\n  Selection: ",
                context="wan_probe_device_template_selection",
            )
            .strip()
            .lower()
        )

        if selection == "cancel":
            print(" Operation cancelled.")
            logging.info("Menu #167 cancelled by user at template selection")
            return False

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(template_list):  # nosec B101
                self.selected_template = template_list[idx]
                assert self.selected_template is not None  # nosec B101
                template_name = self.selected_template["name"]
                print(f"\n  Selected template: {template_name}")
                logging.info("Menu #167: Selected template %s", template_name)
                return True

            print(" Invalid selection.")
            return False
        except ValueError:
            print(f" Invalid selection: {selection}")
            logging.error("Menu #167: Invalid template selection: %s", selection)
            return False

    def _find_template_sites(self) -> bool:  # nosec B101
        """Find all sites using the selected template. Returns True if found."""
        assert self.selected_template is not None, "Template must be selected before finding sites"  # nosec B101
        template_id = self.selected_template["id"]
        template_name = self.selected_template["name"]

        self.template_sites = []
        for site in self.sites:
            if MIST_SITE_EXCLUDE_PREFIX and site.get("name", "").startswith(MIST_SITE_EXCLUDE_PREFIX):
                continue
            if site.get("gatewaytemplate_id", "").strip() == template_id:
                self.template_sites.append(
                    {"site_id": site.get("id", ""), "site_name": site.get("name", "Unknown Site")}
                )

        if not self.template_sites:
            print(f"\n  No sites found using template '{template_name}'.")
            logging.warning("Menu #167: No sites using template %s", template_name)
            return False

        print(f"\n  Found {len(self.template_sites)} sites using template '{template_name}'")
        logging.info("Found %s sites using template %s", len(self.template_sites), template_name)
        return True

    def _find_devices_with_overrides(self) -> list[dict[str, Any]]:  # noqa: C901, PLR0912
        """Find gateway devices with WAN port overrides. Returns list of devices."""
        print(f"\n  Scanning {len(self.template_sites)} sites for gateway devices...")

        all_gateways = []
        for site_info in tqdm(self.template_sites, desc="Scanning sites", unit="site"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():
                break
            site_id = site_info["site_id"]
            site_name = site_info["site_name"]

            try:
                resp = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="gateway", limit=1000)
                devices = resp.data if hasattr(resp, "data") else []

                for device in devices:
                    if isinstance(device, dict):
                        all_gateways.append({"device": device, "site_id": site_id, "site_name": site_name})
            except Exception as error:  # pylint: disable=broad-exception-caught
                logging.warning("Error scanning site %s: %s", site_name, error)
                continue

        if not all_gateways:
            print(f"\n  No gateway devices found in the {len(self.template_sites)} sites using this template.")
            print("  Gateways must be assigned to sites before checking for port overrides.")
            logging.info("Menu #167: No gateway devices found in template sites")
            return []

        print(f"\n  Found {len(all_gateways)} gateway devices. Checking for WAN port overrides...")

        devices_with_overrides = []
        for gateway_info in all_gateways:
            device = gateway_info["device"]
            site_id = gateway_info["site_id"]
            site_name = gateway_info["site_name"]

            device_id = device.get("id", "")
            device_name = device.get("name", "Unknown Device")
            port_config = device.get("port_config", {})

            if not isinstance(port_config, dict) or not port_config:
                continue

            overridden_wan_ports = []
            for port_name, port_settings in port_config.items():
                if not isinstance(port_settings, dict):
                    continue

                if port_settings.get("usage") != "wan":
                    continue

                current_probe = port_settings.get("wan_probe_override", {})
                current_ips = current_probe.get("ips", []) if isinstance(current_probe, dict) else []
                current_profile = current_probe.get("probe_profile", "") if isinstance(current_probe, dict) else ""

                overridden_wan_ports.append(
                    {
                        "port_name": port_name,
                        "current_ips": current_ips,
                        "current_profile": current_profile,
                        "port_settings": port_settings,
                    }
                )

            if overridden_wan_ports:
                devices_with_overrides.append(
                    {
                        "device_id": device_id,
                        "device_name": device_name,
                        "site_id": site_id,
                        "site_name": site_name,
                        "overridden_wan_ports": overridden_wan_ports,
                    }
                )

        if not devices_with_overrides:
            print(f"\n  No WAN port overrides found on the {len(all_gateways)} gateway devices.")
            print("  All devices are using template-level WAN configuration.")
            logging.info("Menu #167: No devices with WAN port overrides found")
            return []

        total_ports = sum(len(d["overridden_wan_ports"]) for d in devices_with_overrides)
        print(f"\n  Found {len(devices_with_overrides)} devices with {total_ports} overridden WAN ports")
        logging.info("Found %s devices with %s overridden WAN ports", len(devices_with_overrides), total_ports)
        return devices_with_overrides

    def _show_preview(self, devices_with_overrides: list[dict[str, Any]], dry_run: bool) -> None:  # nosec B101
        """Display preview of changes to be made."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        total_ports = sum(len(d["overridden_wan_ports"]) for d in devices_with_overrides)

        print("\n  Preview of Changes:")
        print(f"  Template: {self.selected_template['name']}")
        print(f"  Devices: {len(devices_with_overrides)}")
        print(f"  Overridden WAN Ports: {total_ports}")

        preview_count = min(5, len(devices_with_overrides))
        print(f"\n  Sample devices (showing {preview_count} of {len(devices_with_overrides)}):")

        for device in devices_with_overrides[:preview_count]:
            print(f"\n   Device: {device['device_name']} ({device['site_name']})")
            for wan_port in device["overridden_wan_ports"]:
                port = wan_port["port_name"]
                current_ips = wan_port["current_ips"] or ["(none)"]
                current_profile = wan_port["current_profile"] or "(none)"
                print(f"     {port}:")
                print(f"       Current: ips={current_ips}, profile={current_profile}")
                print(f"       New:     ips={self.probe_ips}, profile={self.probe_profile}")

        if len(devices_with_overrides) > preview_count:
            print(f"\n   ... and {len(devices_with_overrides) - preview_count} more devices")

    def _confirm_operation(self, device_count: int) -> bool:
        """Prompt for confirmation. Returns True if confirmed."""
        print(f"\n  {'=' * 70}")
        print(f"  !? CRITICAL: This will modify {device_count} gateway devices")
        print("  !? Type 'APPLY' (all caps) to proceed or anything else to cancel")
        print(f"  {'=' * 70}")

        confirmation = InputUtils.safe_input(
            "\n  Confirmation: ",
            context="wan_probe_device_apply_confirmation",
        ).strip()
        if confirmation != "APPLY":
            print(" Operation cancelled.")
            logging.info("Menu #167 cancelled by user at final confirmation")
            return False
        return True

    def _apply_changes(self, devices_with_overrides: list[dict[str, Any]], dry_run: bool) -> list[dict[str, Any]]:
        """Apply probe configuration changes to devices. Returns results."""
        print("\n  Applying WAN probe configuration to device overrides...")
        results = []

        for device in tqdm(devices_with_overrides, desc="Updating devices", unit="device"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():
                break
            result = self._update_single_device(device, dry_run)
            results.append(result)

        return results

    def _update_single_device(self, device: dict[str, Any], dry_run: bool) -> dict[str, Any]:  # nosec B101
        """Update a single device's overridden WAN port probe configuration."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        device_id = device["device_id"]
        device_name = device["device_name"]
        site_id = device["site_id"]
        site_name = device["site_name"]

        result = {
            "device_name": device_name,
            "device_id": device_id,
            "site_name": site_name,
            "site_id": site_id,
            "template_name": self.selected_template["name"],
            "ports_updated": [],
            "status": "",
            "error": "",
        }

        try:
            logging.debug("Fetching device config for %s", device_name)
            resp = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
            device_config = resp.data if hasattr(resp, "data") else {}

            if not isinstance(device_config, dict):
                result["status"] = "SKIPPED"
                result["error"] = "Invalid device config structure"
                return result

            port_config = device_config.get("port_config", {})
            if not isinstance(port_config, dict):
                result["status"] = "SKIPPED"
                result["error"] = "No port_config found"
                return result

            ports_modified = []
            for wan_port in device["overridden_wan_ports"]:
                port_name = wan_port["port_name"]

                if port_name in port_config:
                    if not isinstance(port_config[port_name], dict):
                        port_config[port_name] = {}

                    port_config[port_name]["wan_probe_override"] = {
                        "ips": self.probe_ips.copy(),
                        "probe_profile": self.probe_profile,
                    }
                    ports_modified.append(port_name)
                    logging.debug("Device %s: Updated %s probe config", device_name, port_name)

            if ports_modified:
                device_config["port_config"] = port_config
                result["ports_updated"] = ports_modified

                if dry_run:
                    result["status"] = "DRY-RUN"
                    logging.info("DRY-RUN: Would update device %s ports: %s", device_name, ports_modified)
                else:
                    logging.debug("Updating device %s via API", device_name)
                    update_resp = mistapi.api.v1.sites.devices.updateSiteDevice(
                        apisession, site_id, device_id, body=device_config
                    )

                    if update_resp.status_code == 200:
                        result["status"] = "SUCCESS"
                        logging.info("Successfully updated device %s", device_name)
                    else:
                        result["status"] = "FAILED"
                        result["error"] = f"API returned status {update_resp.status_code}"
                        logging.error("Failed to update device %s: %s", device_name, update_resp.status_code)
            else:
                result["status"] = "SKIPPED"
                result["error"] = "No matching ports found in current config"

        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"
            result["error"] = str(error)
            logging.error("Error updating device %s: %s", device_name, error)
            logging.error(traceback.format_exc())

        return result

    def _generate_report(self, results: list[dict[str, Any]], dry_run: bool) -> None:  # nosec B101
        """Generate and display final report."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        template_name = self.selected_template["name"]

        report_data = []
        for result in results:
            report_data.append(
                {
                    "device_name": result["device_name"],
                    "device_id": result["device_id"],
                    "site_name": result["site_name"],
                    "site_id": result["site_id"],
                    "template_name": result["template_name"],
                    "ports_updated": ", ".join(result["ports_updated"]) if result["ports_updated"] else "",
                    "port_count": len(result["ports_updated"]),
                    "status": result["status"],
                    "error": result["error"],
                    "new_probe_ips": ", ".join(self.probe_ips),
                    "new_probe_profile": self.probe_profile,
                }
            )

        output_file = "GatewayDevice_WAN_Probe_Override_Audit.csv"
        DataExporter.save_data_to_output(report_data, output_file)  # type: ignore[no-untyped-call]

        total_ports = sum(len(r["ports_updated"]) for r in results)

        if dry_run:
            dry_run_count = sum(1 for r in results if r["status"] == "DRY-RUN")
            print("\n  WAN Probe Device Override DRY-RUN Complete!")
            print("=" * 70)
            print("  >> DRY-RUN MODE: No actual changes were made")
            print(f"  Template: {template_name}")
            print(f"  Devices Analyzed: {len(results)}")
            print(f"  Would Update: {dry_run_count} devices")
            print(f"  WAN Ports: {total_ports}")
            print("\n  >> To apply changes, run without --dry-run flag")
        else:
            success_count = sum(1 for r in results if r["status"] == "SUCCESS")
            failure_count = len(results) - success_count

            print("\n  WAN Probe Device Override Complete!")
            print("=" * 70)
            print(f"  Template: {template_name}")
            print(f"  Devices Updated: {success_count}")
            print(f"  Devices Failed: {failure_count}")
            print(f"  WAN Ports Configured: {total_ports}")

            if success_count > 0:
                print("\n  Configuration Applied:")
                print(f"    Probe IPs: {self.probe_ips}")
                print(f"    Probe Profile: {self.probe_profile}")

            if failure_count > 0:
                print(f"\n  !? {failure_count} devices failed - check audit report")

        print(f"\n  Report saved to: {output_file}")
        print("=" * 70)

        logging.warning(
            "Menu #167 DESTRUCTIVE operation complete: %s devices updated",
            sum(1 for r in results if r["status"] == "SUCCESS"),
        )
