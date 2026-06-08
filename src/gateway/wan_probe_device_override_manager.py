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

    def _find_devices_with_overrides(self) -> list[dict[str, Any]]:
        """Find gateway devices with WAN port overrides. Returns list of devices."""
        print(f"\n  Scanning {len(self.template_sites)} sites for gateway devices...")  # User progress message
        all_gateways = self._scan_template_sites_for_gateways()  # Collect raw gateway entries across sites

        if not all_gateways:  # Nothing to inspect — emit user-facing diagnostics and return
            print(f"\n  No gateway devices found in the {len(self.template_sites)} sites using this template.")
            print("  Gateways must be assigned to sites before checking for port overrides.")
            logging.info("Menu #167: No gateway devices found in template sites")
            return []

        print(f"\n  Found {len(all_gateways)} gateway devices. Checking for WAN port overrides...")
        devices_with_overrides = self._collect_devices_with_overrides(all_gateways)  # Filter to overridden-only set

        if not devices_with_overrides:  # No device-level overrides — short-circuit
            print(f"\n  No WAN port overrides found on the {len(all_gateways)} gateway devices.")
            print("  All devices are using template-level WAN configuration.")
            logging.info("Menu #167: No devices with WAN port overrides found")
            return []

        total_ports = sum(len(d["overridden_wan_ports"]) for d in devices_with_overrides)  # Total port count
        print(f"\n  Found {len(devices_with_overrides)} devices with {total_ports} overridden WAN ports")
        logging.info("Found %s devices with %s overridden WAN ports", len(devices_with_overrides), total_ports)
        return devices_with_overrides

    def _scan_template_sites_for_gateways(self) -> list[dict[str, Any]]:
        """Fetch gateway devices from every template site. Returns wrapped entries."""
        all_gateways: list[dict[str, Any]] = []  # Accumulator for {device, site_id, site_name} entries
        for site_info in tqdm(self.template_sites, desc="Scanning sites", unit="site"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():  # Honour cooperative cancellation
                break
            site_id = site_info["site_id"]  # Site UUID for API call + reporting
            site_name = site_info["site_name"]  # Site name preserved for downstream report rows
            try:
                logging.info("Listing gateway devices for site %s", site_name)  # Pre-call log
                resp = mistapi.api.v1.sites.devices.listSiteDevices(  # API: enumerate gateways at this site
                    apisession, site_id, type="gateway", limit=1000
                )
                devices = resp.data if hasattr(resp, "data") else []  # Defensive: response may lack .data
                logging.debug("Site %s returned %s gateway entries", site_name, len(devices))  # Post-call log
                for device in devices:  # Iterate each gateway record
                    if isinstance(device, dict):  # Skip malformed entries silently
                        all_gateways.append({"device": device, "site_id": site_id, "site_name": site_name})
            except Exception as error:  # pylint: disable=broad-exception-caught
                logging.warning("Error scanning site %s: %s", site_name, error)  # Per-site failure
                continue
        return all_gateways

    def _collect_devices_with_overrides(self, all_gateways: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter scanned gateways to only those with overridden WAN ports."""
        devices_with_overrides: list[dict[str, Any]] = []  # Accumulator for filtered devices
        for gateway_info in all_gateways:  # Walk every scanned gateway record
            device = gateway_info["device"]  # The raw device dict from Mist
            port_config = device.get("port_config", {})  # Local port overrides keyed by port name
            if not isinstance(port_config, dict) or not port_config:  # No overrides at all — skip
                continue
            overridden_wan_ports = self._extract_overridden_wan_ports(port_config)  # Per-device override extract
            if overridden_wan_ports:  # Only retain devices that actually have WAN overrides
                devices_with_overrides.append(
                    {
                        "device_id": device.get("id", ""),  # Preserve device UUID for later update call
                        "device_name": device.get("name", "Unknown Device"),  # Friendly name for reporting
                        "site_id": gateway_info["site_id"],  # Carry forward site UUID
                        "site_name": gateway_info["site_name"],  # Carry forward site display name
                        "overridden_wan_ports": overridden_wan_ports,  # Override details for downstream update
                    }
                )
        return devices_with_overrides

    @staticmethod
    def _extract_overridden_wan_ports(port_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a list of overridden WAN port descriptors from a device's port_config."""
        overridden_wan_ports: list[dict[str, Any]] = []  # Collected WAN port override entries
        for port_name, port_settings in port_config.items():  # Inspect each port
            if not isinstance(port_settings, dict) or port_settings.get("usage") != "wan":  # WAN-only
                continue
            current_probe = port_settings.get("wan_probe_override", {})  # Existing override blob (if any)
            if not isinstance(current_probe, dict):  # Defensive: probe may be malformed
                current_probe = {}
            overridden_wan_ports.append(
                {
                    "port_name": port_name,  # Port identifier (e.g. ge-0/0/0)
                    "current_ips": current_probe.get("ips", []),  # Existing probe IPs
                    "current_profile": current_probe.get("probe_profile", ""),  # Existing probe profile
                    "port_settings": port_settings,  # Full port settings retained for context
                }
            )
        return overridden_wan_ports

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
        result = self._initial_device_result(device)  # Pre-populated result skeleton
        try:
            logging.info("Updating WAN probe overrides for device %s", result["device_name"])  # Pre-action log
            device_config = self._fetch_device_config(device, result)  # Fetch + validate device config
            if device_config is None:  # Validation failed — result already set, exit early
                return result
            ports_modified = self._apply_probe_to_ports(  # Mutate port_config in place
                device_config["port_config"], device["overridden_wan_ports"], result["device_name"]
            )
            if not ports_modified:  # Nothing matched — record SKIPPED
                result["status"] = "SKIPPED"
                result["error"] = "No matching ports found in current config"
                return result
            result["ports_updated"] = ports_modified  # Record names of mutated ports
            self._commit_device_update(device, device_config, dry_run, result)  # Push or dry-run
            logging.debug("Device %s update result: %s", result["device_name"], result["status"])  # Post-action log
        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"  # Record any unexpected failure
            result["error"] = str(error)
            logging.error("Error updating device %s: %s", result["device_name"], error)
            logging.error(traceback.format_exc())
        return result

    def _initial_device_result(self, device: dict[str, Any]) -> dict[str, Any]:  # nosec B101
        """Return a fresh result skeleton for one device update attempt."""
        assert self.selected_template is not None  # nosec B101
        return {
            "device_name": device["device_name"],  # For logging + report rendering
            "device_id": device["device_id"],
            "site_name": device["site_name"],
            "site_id": device["site_id"],
            "template_name": self.selected_template["name"],  # Template association for audit
            "ports_updated": [],  # Filled in if any ports are actually modified
            "status": "",  # SUCCESS / FAILED / SKIPPED / DRY-RUN / ERROR
            "error": "",  # Human-readable failure detail
        }

    @staticmethod
    def _fetch_device_config(device: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch device config from Mist and verify it has a usable port_config."""
        logging.debug("Fetching device config for %s", device["device_name"])  # Pre-call log
        resp = mistapi.api.v1.sites.devices.getSiteDevice(  # API: full device config
            apisession, device["site_id"], device["device_id"]
        )
        device_config = resp.data if hasattr(resp, "data") else {}  # Defensive: missing .data
        if not isinstance(device_config, dict):  # Mist returned non-dict body — unusable
            result["status"] = "SKIPPED"
            result["error"] = "Invalid device config structure"
            return None
        port_config = device_config.get("port_config", {})  # Ensure port_config dict exists
        if not isinstance(port_config, dict):  # No port_config to patch — skip
            result["status"] = "SKIPPED"
            result["error"] = "No port_config found"
            return None
        device_config["port_config"] = port_config  # Normalise back onto config for downstream mutation
        return device_config

    def _apply_probe_to_ports(
        self,
        port_config: dict[str, Any],
        overridden_wan_ports: list[dict[str, Any]],
        device_name: str,
    ) -> list[str]:
        """Patch wan_probe_override on each matching port; return modified port names."""
        ports_modified: list[str] = []  # Names of ports that were actually patched
        for wan_port in overridden_wan_ports:  # Iterate planned overrides
            port_name = wan_port["port_name"]
            if port_name not in port_config:  # Port no longer present on device — skip silently
                continue
            if not isinstance(port_config[port_name], dict):  # Defensive: replace non-dict scalar
                port_config[port_name] = {}
            port_config[port_name]["wan_probe_override"] = {  # Write new probe payload
                "ips": self.probe_ips.copy(),  # Copy so callers cannot mutate shared list
                "probe_profile": self.probe_profile,
            }
            ports_modified.append(port_name)  # Record success for this port
            logging.debug("Device %s: Updated %s probe config", device_name, port_name)
        return ports_modified

    @staticmethod
    def _commit_device_update(
        device: dict[str, Any],
        device_config: dict[str, Any],
        dry_run: bool,
        result: dict[str, Any],
    ) -> None:
        """Push the patched config back to Mist or mark as DRY-RUN."""
        device_name = device["device_name"]
        if dry_run:  # Skip the actual API write in dry-run mode
            result["status"] = "DRY-RUN"
            logging.info("DRY-RUN: Would update device %s ports: %s", device_name, result["ports_updated"])
            return
        logging.info("Updating device %s via Mist API", device_name)  # Pre-call log
        update_resp = mistapi.api.v1.sites.devices.updateSiteDevice(  # API: write back patched config
            apisession, device["site_id"], device["device_id"], body=device_config
        )
        logging.debug("Device %s update API status=%s", device_name, update_resp.status_code)  # Post-call log
        if update_resp.status_code == 200:  # Success path
            result["status"] = "SUCCESS"
            logging.info("Successfully updated device %s", device_name)
        else:  # Non-200 → mark failed with status code
            result["status"] = "FAILED"
            result["error"] = f"API returned status {update_resp.status_code}"
            logging.error("Failed to update device %s: %s", device_name, update_resp.status_code)

    def _generate_report(self, results: list[dict[str, Any]], dry_run: bool) -> None:  # nosec B101
        """Generate and display final report."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        template_name = self.selected_template["name"]  # Display name for summary

        report_data = self._build_report_rows(results)  # CSV-shaped rows per device
        output_file = "GatewayDevice_WAN_Probe_Override_Audit.csv"  # Stable audit filename
        logging.info("Saving WAN probe override audit CSV: %s", output_file)  # Pre-write log
        DataExporter.save_data_to_output(report_data, output_file)  # type: ignore[no-untyped-call]
        logging.debug("Audit CSV saved (rows=%s)", len(report_data))  # Post-write log

        total_ports = sum(len(r["ports_updated"]) for r in results)  # Aggregate ports modified
        if dry_run:  # Dry-run summary path
            self._print_dry_run_summary(results, template_name, total_ports)
        else:  # Live run summary path
            self._print_apply_summary(results, template_name, total_ports)

        print(f"\n  Report saved to: {output_file}")
        print("=" * 70)
        logging.warning(  # Audit-level summary line
            "Menu #167 DESTRUCTIVE operation complete: %s devices updated",
            sum(1 for r in results if r["status"] == "SUCCESS"),
        )

    def _build_report_rows(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert internal per-device results into CSV-shaped report rows."""
        rows: list[dict[str, Any]] = []  # Accumulator for the flattened rows
        for result in results:  # Iterate per-device outcome
            rows.append(
                {
                    "device_name": result["device_name"],  # Device display name
                    "device_id": result["device_id"],
                    "site_name": result["site_name"],
                    "site_id": result["site_id"],
                    "template_name": result["template_name"],
                    "ports_updated": ", ".join(result["ports_updated"]) if result["ports_updated"] else "",
                    "port_count": len(result["ports_updated"]),
                    "status": result["status"],
                    "error": result["error"],
                    "new_probe_ips": ", ".join(self.probe_ips),  # Configuration applied
                    "new_probe_profile": self.probe_profile,
                }
            )
        return rows

    @staticmethod
    def _print_dry_run_summary(results: list[dict[str, Any]], template_name: str, total_ports: int) -> None:
        """Print the dry-run completion banner."""
        dry_run_count = sum(1 for r in results if r["status"] == "DRY-RUN")  # Count planned updates
        print("\n  WAN Probe Device Override DRY-RUN Complete!")
        print("=" * 70)
        print("  >> DRY-RUN MODE: No actual changes were made")
        print(f"  Template: {template_name}")
        print(f"  Devices Analyzed: {len(results)}")
        print(f"  Would Update: {dry_run_count} devices")
        print(f"  WAN Ports: {total_ports}")
        print("\n  >> To apply changes, run without --dry-run flag")

    def _print_apply_summary(self, results: list[dict[str, Any]], template_name: str, total_ports: int) -> None:
        """Print the live-run completion banner with success/failure breakdown."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")  # Successful updates
        failure_count = len(results) - success_count  # Everything else counts as failed/skipped
        print("\n  WAN Probe Device Override Complete!")
        print("=" * 70)
        print(f"  Template: {template_name}")
        print(f"  Devices Updated: {success_count}")
        print(f"  Devices Failed: {failure_count}")
        print(f"  WAN Ports Configured: {total_ports}")
        if success_count > 0:  # Echo applied configuration for operator visibility
            print("\n  Configuration Applied:")
            print(f"    Probe IPs: {self.probe_ips}")
            print(f"    Probe Profile: {self.probe_profile}")
        if failure_count > 0:  # Direct operator to audit CSV for details
            print(f"\n  !? {failure_count} devices failed - check audit report")
