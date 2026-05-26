"""WAN2 migration manager extracted from MistHelper menu 149 flow."""

from __future__ import annotations

import csv
import json
import logging
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


def configure_wan2_migration_dependencies(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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


class WAN2MigrationManager:
    """
    Manages WAN2 interface variable migration for gateway templates and sites.

    Consolidates Menu Options 103 and 104:
    - set_site_variable(): Set wan2_interface site variable across sites (Menu 103)
    - update_templates(): Migrate gateway templates to use {{wan2_interface}} variable (Menu 104)

    Both operations support bidirectional migration (apply/revert) and preserve device-level
    static IP overrides by properly handling port_config keys.
    """

    def __init__(self):  # type: ignore[no-untyped-def]
        """Initialize the WAN2 migration manager."""
        self.org_id = ConfigUtils.get_cached_or_prompted_org_id()
        self.sites = []
        self.gateway_configs = []
        self.template_data = []
        self.site_to_template_id = {}
        self.template_port_configs = {}
        self.site_overrides_map = {}

    def set_site_variable(self):  # type: ignore[no-untyped-def]
        """
        Menu #149: Set WAN2 Interface Site Variable.

        Creates and sets the {{wan2_interface}} site variable to 'ge-0/0/1' across selected sites.
        Reports sites with WAN2 port overrides requiring manual review.
        """
        self._display_site_variable_header()  # type: ignore[no-untyped-call]

        if not self._load_required_data():
            return

        sites_to_configure = self._get_site_selection()
        if not sites_to_configure:
            return

        sites_to_configure = self._filter_excluded_sites(sites_to_configure)
        if not sites_to_configure:
            return

        if not self._confirm_site_variable_operation(len(sites_to_configure)):
            return

        self._build_override_detection_map()  # type: ignore[no-untyped-call]
        results = self._process_sites_for_variable(sites_to_configure)
        self._generate_site_variable_report(results)

    def _display_site_variable_header(self):  # type: ignore[no-untyped-def]
        """Display operation header for Menu #149."""
        print("\n  Set WAN2 Interface Site Variable")
        print("=" * 70)
        print("  This operation will set the 'wan2_interface' site variable to 'ge-0/0/1'")
        print("  across selected sites, preparing them for template-based WAN migration.")
        print("=" * 70)
        logging.info("Menu #149: Set WAN2 Interface Site Variable operation started")

    def _load_required_data(self) -> bool:
        """Load site and gateway configuration data. Returns True on success."""
        print("\n  Preparing site and gateway configuration data...")
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)
        CacheUtils.check_and_generate_csv("AllSiteGatewayConfigs.csv", GatewayExportUtils.device_configs)
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtils.templates)

        site_list_path = FilePathUtils.get_csv_path("SiteList.csv")
        with open(site_list_path, encoding="utf-8") as file_handle:
            self.sites = list(csv.DictReader(file_handle))

        if not self.sites:
            print(" No sites found in organization.")
            logging.warning("No sites available for WAN2 variable assignment")
            return False

        return True

    def _get_site_selection(self) -> list[dict[str, Any]]:
        """Prompt user for site selection. Returns selected sites or empty list."""
        logging.info(
            "Entering WAN2MigrationManager._get_site_selection: %s sites available",
            len(self.sites),
        )
        print(f"\n  Found {len(self.sites)} sites in organization")
        print("  Site Selection:")
        print("   1. Select individual sites")
        print("   2. All sites in organization")
        print("   3. Cancel")

        selection_choice = InputUtils.safe_input(
            "\n  Choose selection method (1-3): ",
            context="wan2_site_selection_method",
        ).strip()

        if selection_choice == "1":
            result = self._select_individual_sites()
            logging.info(
                "Exiting WAN2MigrationManager._get_site_selection: individual selection returned %s sites",
                len(result),
            )
            return result
        if selection_choice == "2":
            all_sites = self.sites.copy()
            logging.info(
                "Exiting WAN2MigrationManager._get_site_selection: all-sites selection returned %s sites",
                len(all_sites),
            )
            return all_sites

        print(" Operation cancelled.")
        logging.info("Menu #149 cancelled by user")
        logging.info(
            "Exiting WAN2MigrationManager._get_site_selection: cancelled by user"
        )
        return []

    def _select_individual_sites(self) -> list[dict[str, Any]]:
        """Display site list and get individual selections."""
        print("\n  Available Sites:")
        for index, site in enumerate(self.sites, start=1):
            site_name = site.get("name", "Unnamed Site")
            site_id = site.get("id", "")
            print(f"   [{index}] {site_name} ({site_id})")

        print("\n  Enter site numbers to configure (comma-separated, e.g., 1,3,5):")
        site_indices_input = InputUtils.safe_input("  Site numbers: ", context="wan2_site_index_selection").strip()

        try:
            selected_indices = [int(idx.strip()) - 1 for idx in site_indices_input.split(",")]
            return [self.sites[idx] for idx in selected_indices if 0 <= idx < len(self.sites)]
        except (ValueError, IndexError) as error:
            print(f" Invalid site selection: {error}")
            logging.error("Invalid site selection in Menu #149: %s", error)
            return []

    def _filter_excluded_sites(self, sites_to_configure: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out excluded sites from configuration list based on MIST_SITE_EXCLUDE_PREFIX."""
        if not MIST_SITE_EXCLUDE_PREFIX:
            return sites_to_configure

        original_count = len(sites_to_configure)
        filtered_sites = [
            site for site in sites_to_configure if not site.get("name", "").startswith(MIST_SITE_EXCLUDE_PREFIX)
        ]
        filtered_count = original_count - len(filtered_sites)

        if filtered_count > 0:
            print(f"\n  !? SECURITY: Excluded {filtered_count} '{MIST_SITE_EXCLUDE_PREFIX}*' sites from configuration")
            logging.info(
                "Menu #149: Excluded %s sites matching prefix '%s' from WAN2 variable operation",
                filtered_count,
                MIST_SITE_EXCLUDE_PREFIX,
            )

        if not filtered_sites:
            print(f" No sites remaining after filtering '{MIST_SITE_EXCLUDE_PREFIX}*' sites.")
            logging.warning(
                "Menu #149: All selected sites matched exclude prefix '%s' - operation cancelled",
                MIST_SITE_EXCLUDE_PREFIX,
            )

        return filtered_sites

    def _confirm_site_variable_operation(self, site_count: int) -> bool:
        """Confirm the site variable operation with user."""
        logging.info(
            "Entering WAN2MigrationManager._confirm_site_variable_operation: %s sites pending",
            site_count,
        )
        print(f"\n  Will configure {site_count} sites with wan2_interface variable.")
        confirm = (
            InputUtils.safe_input(
                "\n  Proceed with setting site variables? (yes/no): ",
                context="wan2_site_variable_confirm",
            )
            .strip()
            .lower()
        )

        if confirm not in ["yes", "y"]:
            print(" Operation cancelled.")
            logging.info("Menu #149 cancelled by user at confirmation prompt")
            logging.info(
                "Exiting WAN2MigrationManager._confirm_site_variable_operation: result=cancelled"
            )
            return False
        logging.info(
            "Exiting WAN2MigrationManager._confirm_site_variable_operation: result=confirmed for %s sites",
            site_count,
        )
        return True

    def _build_override_detection_map(self):  # type: ignore[no-untyped-def]
        """Build map of sites with WAN2 port overrides for analysis."""
        self._load_gateway_configs()  # type: ignore[no-untyped-call]
        self._load_template_configs()  # type: ignore[no-untyped-call]
        self._build_site_to_template_mapping()  # type: ignore[no-untyped-call]
        self._extract_template_port_configs()  # type: ignore[no-untyped-call]
        self._detect_device_overrides()  # type: ignore[no-untyped-call]

    def _load_gateway_configs(self):  # type: ignore[no-untyped-def]
        """Load gateway device configurations from CSV."""
        gateway_configs_path = FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv")
        with open(gateway_configs_path, encoding="utf-8") as file_handle:
            self.gateway_configs = list(csv.DictReader(file_handle))

    def _load_template_configs(self):  # type: ignore[no-untyped-def]
        """Load gateway template configurations from CSV."""
        template_configs_path = FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")
        with open(template_configs_path, encoding="utf-8") as file_handle:
            self.template_data = list(csv.DictReader(file_handle))

    def _build_site_to_template_mapping(self):  # type: ignore[no-untyped-def]
        """Build mapping from site_id to gateway template_id."""
        for site in self.sites:
            site_id = site.get("id", "").strip()
            template_id = site.get("gatewaytemplate_id", "").strip()
            if site_id and template_id:
                self.site_to_template_id[site_id] = template_id
        logging.info("Mapped %s sites to gateway templates", len(self.site_to_template_id))

    def _extract_template_port_configs(self):  # type: ignore[no-untyped-def]
        """Extract IP configuration type from templates for ge-0/0/1 port."""
        for template_row in self.template_data:
            template_id = template_row.get("id", "").strip()
            if not template_id:
                continue

            ip_config = self._parse_template_ip_config(template_row)
            self.template_port_configs[template_id] = ip_config

        logging.info("Loaded port IP configs for %s templates", len(self.template_port_configs))

    def _parse_template_ip_config(self, template_row: dict[str, Any]) -> dict[str, str]:
        """Parse IP configuration from template row."""
        ip_config_raw = template_row.get("port_config_ge-0/0/1_ip_config", "").strip()
        result = {"ip_type": "not_configured", "ip": "", "netmask": "", "gateway": ""}

        if not ip_config_raw:
            return result

        try:
            ip_config_data = json.loads(ip_config_raw)
            result["ip_type"] = ip_config_data.get("type", "").lower() or "not_configured"
            if result["ip_type"] == "static":
                result["ip"] = ip_config_data.get("ip", "")
                result["netmask"] = ip_config_data.get("netmask", "")
                result["gateway"] = ip_config_data.get("gateway", "")
        except json.JSONDecodeError as error:
            logging.warning("Failed to parse template IP config: %s", error)
            result["ip_type"] = "parse_error"

        return result

    def _detect_device_overrides(self):  # type: ignore[no-untyped-def]
        """Detect devices with WAN2 port overrides and classify severity."""
        for config_row in self.gateway_configs:
            site_id = config_row.get("site_id", "").strip()
            device_name = config_row.get("name", "").strip()

            override_info = self._analyze_device_override(config_row, site_id)
            if override_info:
                if site_id not in self.site_overrides_map:
                    self.site_overrides_map[site_id] = []
                self.site_overrides_map[site_id].append({"device_name": device_name, **override_info})

    def _analyze_device_override(self, config_row: dict[str, Any], site_id: str) -> dict[str, Any] | None:
        """Analyze a device config for WAN2 port overrides. Returns override info or None."""
        wan2_fields = self._get_wan2_override_fields(config_row)
        has_override = self._check_has_meaningful_override(config_row, wan2_fields)

        if not has_override:
            return None

        device_ip_info = self._extract_device_ip_config(config_row)
        template_ip_type = self._get_template_ip_type_for_site(site_id, device_ip_info.get("port_identifier", ""))
        severity = self._classify_override_severity(template_ip_type, device_ip_info.get("ip_type", ""))

        return {
            "port_identifier": device_ip_info.get("port_identifier", "ge-0/0/1"),
            "template_ip_type": template_ip_type.upper(),
            "device_ip_type": device_ip_info.get("ip_type", "").upper() or "NOT_CONFIGURED",
            "device_static_ip": device_ip_info.get("ip", ""),
            "device_netmask": device_ip_info.get("netmask", ""),
            "device_gateway": device_ip_info.get("gateway", ""),
            "override_severity": severity,
            "ip_type_conflict": severity in ["CRITICAL", "WARNING"],
        }

    def _get_wan2_override_fields(self, config_row: dict[str, Any]) -> list[str]:
        """Get list of WAN2-related port_config fields from config row."""
        return [
            col
            for col in config_row
            if col.startswith("port_config_ge-0/0/1_")
            or col.startswith("port_config_ge-0/0/1.")
            or col.startswith("port_config_{{wan2_interface}}_")
            or col.startswith("port_config_{{wan2_interface}}.")
        ]

    def _check_has_meaningful_override(self, config_row: dict[str, Any], fields: list[str]) -> bool:
        """Check if config row has meaningful WAN2 overrides (excluding VPN paths)."""
        return any(
            config_row.get(field, "").strip().lower() not in ["", "null", "none"]
            for field in fields
            if "_vpn_paths_" not in field
        )

    def _extract_device_ip_config(self, config_row: dict[str, Any]) -> dict[str, str]:
        """Extract IP configuration from device config row."""
        subinterface_configs = self._find_subinterface_ip_configs(config_row)
        if subinterface_configs:
            return subinterface_configs[0]

        return self._extract_base_port_ip_config(config_row)

    def _find_subinterface_ip_configs(self, config_row: dict[str, Any]) -> list[dict[str, str]]:
        """Find and parse subinterface IP configurations."""
        configs = []
        for col in config_row:
            if not (
                (col.startswith("port_config_ge-0/0/1.") or col.startswith("port_config_{{wan2_interface}}."))
                and col.endswith("_ip_config_type")
            ):
                continue

            subif_ip_type = config_row.get(col, "").strip().lower()
            if not subif_ip_type:
                continue

            subif_name = col.replace("port_config_", "").replace("_ip_config_type", "")
            ip_col_base = f"port_config_{subif_name}_ip_config"

            configs.append(
                {
                    "port_identifier": subif_name,
                    "ip_type": subif_ip_type,
                    "ip": config_row.get(f"{ip_col_base}_ip", "").strip(),
                    "netmask": config_row.get(f"{ip_col_base}_netmask", "").strip(),
                    "gateway": config_row.get(f"{ip_col_base}_gateway", "").strip(),
                }
            )

        return configs

    def _extract_base_port_ip_config(self, config_row: dict[str, Any]) -> dict[str, str]:
        """Extract base port (ge-0/0/1) IP configuration from device config."""
        result = {"port_identifier": "ge-0/0/1", "ip_type": "", "ip": "", "netmask": "", "gateway": ""}
        ip_config_raw = config_row.get("port_config_ge-0/0/1_ip_config", "").strip()

        if not ip_config_raw:
            return result

        try:
            ip_data = json.loads(ip_config_raw)
            result["ip_type"] = ip_data.get("type", "").lower()
            if result["ip_type"] == "static":
                result["ip"] = ip_data.get("ip", "")
                result["netmask"] = ip_data.get("netmask", "")
                result["gateway"] = ip_data.get("gateway", "")
        except json.JSONDecodeError:
            result["ip_type"] = "parse_error"

        return result

    def _get_template_ip_type_for_site(self, site_id: str, port_identifier: str) -> str:
        """Get the template IP type for a site, checking subinterface if needed."""
        template_id = self.site_to_template_id.get(site_id, "")
        template_config = self.template_port_configs.get(template_id, {})
        template_ip_type = template_config.get("ip_type", "unknown")

        if "." in port_identifier:
            for template_row in self.template_data:
                if template_row.get("id", "").strip() == template_id:
                    subif_col = f"port_config_{port_identifier}_ip_config_type"
                    subif_type = template_row.get(subif_col, "").strip().lower()
                    if subif_type:
                        return subif_type  # type: ignore[no-any-return]
                    break

        return template_ip_type  # type: ignore[no-any-return]

    def _classify_override_severity(self, template_ip_type: str, device_ip_type: str) -> str:
        """Classify override severity based on IP type mismatch."""
        if template_ip_type == "dhcp" and device_ip_type == "static":
            return "CRITICAL"
        if template_ip_type == "static" and device_ip_type == "dhcp":
            return "WARNING"
        if template_ip_type == device_ip_type and device_ip_type in ["dhcp", "static"]:
            return "INFO"
        return "UNKNOWN"

    def _process_sites_for_variable(self, sites_to_configure: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process each site to set the wan2_interface variable."""
        results = []
        print("\n  Processing sites...")

        for site in tqdm(sites_to_configure, desc="Configuring sites", unit="site"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():
                break
            result = self._set_variable_for_site(site)
            results.append(result)

        return results

    def _set_variable_for_site(self, site: dict[str, Any]) -> dict[str, Any]:
        """Set wan2_interface variable for a single site."""
        site_id = site.get("id", "")
        site_name = site.get("name", "Unnamed Site")

        result = self._initialize_site_result(site_id, site_name)
        self._add_override_info_to_result(result, site_id)

        try:
            self._update_site_settings(site_id, site_name, result)
        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"
            result["error"] = str(error)
            logging.error("Error setting variable for site %s: %s", site_name, error)
            logging.error(traceback.format_exc())

        return result

    def _initialize_site_result(self, site_id: str, site_name: str) -> dict[str, Any]:
        """Initialize result dictionary for a site."""
        return {
            "site_id": site_id,
            "site_name": site_name,
            "variable_set": False,
            "has_overrides": False,
            "override_devices": [],
            "critical_override_count": 0,
            "warning_override_count": 0,
            "info_override_count": 0,
            "total_override_count": 0,
            "status": "",
            "error": "",
        }

    def _add_override_info_to_result(self, result: dict[str, Any], site_id: str):  # type: ignore[no-untyped-def]
        """Add override detection info to result dictionary."""
        if site_id not in self.site_overrides_map:
            return

        result["has_overrides"] = True
        override_details = self.site_overrides_map[site_id]
        result["override_devices"] = [d["device_name"] for d in override_details]

        critical = [d for d in override_details if d["override_severity"] == "CRITICAL"]
        warning = [d for d in override_details if d["override_severity"] == "WARNING"]
        info = [d for d in override_details if d["override_severity"] == "INFO"]

        result["critical_override_count"] = len(critical)
        result["warning_override_count"] = len(warning)
        result["info_override_count"] = len(info)
        result["total_override_count"] = len(override_details)
        result["override_details"] = self._format_override_details(override_details)

    def _format_override_details(self, override_details: list[dict[str, Any]]) -> str:
        """Format override details for CSV export."""
        summaries = []
        for detail in override_details:
            device = detail["device_name"]
            port = detail.get("port_identifier", "ge-0/0/1")
            severity = detail["override_severity"]
            template_ip = detail["template_ip_type"]
            device_ip = detail["device_ip_type"]
            static_ip = detail["device_static_ip"]
            netmask = detail["device_netmask"]

            if static_ip and netmask:
                summary = f"{device}@{port}({severity}:{template_ip}->{device_ip}:{static_ip}{netmask})"
            elif static_ip:
                summary = f"{device}@{port}({severity}:{template_ip}->{device_ip}:{static_ip})"
            else:
                summary = f"{device}@{port}({severity}:{template_ip}->{device_ip})"
            summaries.append(summary)

        return "; ".join(summaries)

    def _update_site_settings(self, site_id: str, site_name: str, result: dict[str, Any]):  # type: ignore[no-untyped-def]
        """Update site settings with wan2_interface variable."""
        logging.debug("Fetching current settings for site %s (%s)", site_name, site_id)
        settings_resp = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)
        current_settings = settings_resp.data if hasattr(settings_resp, "data") else {}

        if not isinstance(current_settings, dict):
            current_settings = {}

        site_vars = current_settings.get("vars", {})
        if not isinstance(site_vars, dict):
            site_vars = {}

        site_vars["wan2_interface"] = "ge-0/0/1"
        current_settings["vars"] = site_vars

        logging.debug("Updating site settings for %s with wan2_interface variable", site_name)
        update_resp = mistapi.api.v1.sites.setting.updateSiteSettings(apisession, site_id, body=current_settings)

        if update_resp.status_code == 200:
            result["variable_set"] = True
            result["status"] = "SUCCESS"
            logging.info("Successfully set wan2_interface variable for site %s", site_name)
        else:
            result["status"] = "FAILED"
            result["error"] = f"API returned status {update_resp.status_code}"
            logging.error("Failed to set variable for site %s: status %s", site_name, update_resp.status_code)

    def _generate_site_variable_report(self, results: list[dict[str, Any]]):  # type: ignore[no-untyped-def]
        """Generate and save the site variable report."""
        report_data = self._build_report_data(results)
        output_file = "WAN2_SiteVariable_Report.csv"
        DataExporter.save_data_to_output(report_data, output_file)  # type: ignore[no-untyped-call]

        self._print_site_variable_summary(results, output_file)

    def _build_report_data(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build report data from results."""
        report_data = []
        for result in results:
            requires_review = (
                "CRITICAL"
                if result.get("critical_override_count", 0) > 0
                else (
                    "WARNING"
                    if result.get("warning_override_count", 0) > 0
                    else ("INFO" if result.get("info_override_count", 0) > 0 else "No")
                )
            )

            report_data.append(
                {
                    "site_name": result["site_name"],
                    "site_id": result["site_id"],
                    "wan2_variable_set": "Yes" if result["variable_set"] else "No",
                    "status": result["status"],
                    "has_wan2_overrides": "Yes" if result["has_overrides"] else "No",
                    "total_override_count": result.get("total_override_count", 0),
                    "critical_override_count": result.get("critical_override_count", 0),
                    "warning_override_count": result.get("warning_override_count", 0),
                    "info_override_count": result.get("info_override_count", 0),
                    "override_devices": ", ".join(result["override_devices"]) if result["override_devices"] else "",
                    "override_details": result.get("override_details", ""),
                    "requires_manual_review": requires_review,
                    "error": result["error"],
                }
            )
        return report_data

    def _print_site_variable_summary(self, results: list[dict[str, Any]], output_file: str):  # type: ignore[no-untyped-def]
        """Print summary of site variable operation."""
        success_count = sum(1 for r in results if r["variable_set"])
        override_count = sum(1 for r in results if r["has_overrides"])
        critical_sites = sum(1 for r in results if r.get("critical_override_count", 0) > 0)
        warning_sites = sum(1 for r in results if r.get("warning_override_count", 0) > 0)
        info_sites = sum(
            1
            for r in results
            if r.get("has_overrides")
            and r.get("critical_override_count", 0) == 0
            and r.get("warning_override_count", 0) == 0
        )

        print("\n  Configuration Complete!")
        print("=" * 70)
        print(f"  Sites Processed: {len(results)}")
        print(f"  Variables Set: {success_count}")
        print(f"  Sites with WAN2 Overrides: {override_count}")
        print(f"    -> CRITICAL (DHCP->Static IP conflicts): {critical_sites}")
        print(f"    -> WARNING (Static->DHCP conflicts): {warning_sites}")
        print(f"    -> INFO (Same IP type, other overrides): {info_sites}")
        print(f"\n  Report saved to: {output_file}")
        print("=" * 70)

        self._print_severity_warnings(critical_sites, warning_sites, info_sites)

        logging.info("Menu #149 complete: %s/%s sites configured", success_count, len(results))
        logging.info("Override breakdown - CRITICAL: %s, WARNING: %s, INFO: %s", critical_sites, warning_sites, info_sites)

    def _print_severity_warnings(self, critical_sites: int, warning_sites: int, info_sites: int):  # type: ignore[no-untyped-def]
        """Print severity-specific warnings."""
        if critical_sites > 0:
            print(f"\n  !? CRITICAL ATTENTION: {critical_sites} sites have DHCP->Static IP conflicts")
            print("  Template specifies DHCP but devices use locally unique static IPs")
            print("  These MUST be manually reviewed before template migration (Menu #163)")
            print("  Static IPs will be lost if template DHCP is applied without device overrides")
            print("  Check 'override_details' column for device names and static IP addresses")

        if warning_sites > 0:
            print(f"\n  ! WARNING: {warning_sites} sites have Static->DHCP conflicts")
            print("  Template specifies Static IP but devices configured for DHCP")
            print("  Review recommended before template migration")

        if info_sites > 0:
            print(f"\n  INFO: {info_sites} sites have same-IP-type overrides (likely safe)")
            print("  Template and device use same IP configuration type (both DHCP or both Static)")
            print("  Overrides may be for description, usage, or other non-critical fields")
