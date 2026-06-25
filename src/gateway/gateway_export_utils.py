"""Gateway export utilities extracted from MistHelper.py."""

from __future__ import annotations

import csv
import logging
import re
from typing import Any

from src.gateway.gateway_stats_exporter import configure_gateway_stats_exporter_dependencies
from src.gateway.overrides import (
    WanOverrideWalker,
    configure_gateway_override_dependencies,
)

apisession: Any = None
mistapi: Any = None
ConfigUtils: Any = None
CacheUtils: Any = None
FilePathUtils: Any = None
DataExporter: Any = None
DataProcessingUtils: Any = None
APIFetchUtils: Any = None
APICoreFetchUtils: Any = None
OrgInventoryExporter: Any = None
OrgSiteExporter: Any = None
InputUtils: Any = None
execute_with_connection_pool_management: Any = None
ValidationUtils: Any = None
RateLimitingUtils: Any = None
MIST_WAN_TARGET_PORTS: list[str] = []
MIST_SITE_EXCLUDE_PREFIX: str = ""
FAST_MODE_MAX_RETRIES: int = 2
FAST_MODE_RETRY_DELAY: float = 0.5
_api_usage_cache: Any = None
tqdm: Any = None


def configure_gateway_export_utils_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    config_utils: Any,
    cache_utils: Any,
    file_path_utils: Any,
    data_exporter: Any,
    data_processing_utils: Any,
    api_fetch_utils: Any,
    api_core_fetch_utils: Any,
    org_inventory_exporter: Any,
    org_site_exporter: Any,
    input_utils: Any,
    connection_pool_fn: Any,
    validation_utils: Any,
    rate_limiting_utils: Any,
    mist_wan_target_ports: list[str],
    mist_site_exclude_prefix: str,
    fast_mode_max_retries: int,
    fast_mode_retry_delay: float,
    api_usage_cache: Any,
    tqdm_module: Any,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global mistapi
    global ConfigUtils
    global CacheUtils
    global FilePathUtils
    global DataExporter
    global DataProcessingUtils
    global APIFetchUtils
    global APICoreFetchUtils
    global OrgInventoryExporter
    global OrgSiteExporter
    global InputUtils
    global execute_with_connection_pool_management
    global ValidationUtils
    global RateLimitingUtils
    global MIST_WAN_TARGET_PORTS
    global MIST_SITE_EXCLUDE_PREFIX
    global FAST_MODE_MAX_RETRIES
    global FAST_MODE_RETRY_DELAY
    global _api_usage_cache
    global tqdm

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    ConfigUtils = config_utils
    CacheUtils = cache_utils
    FilePathUtils = file_path_utils
    DataExporter = data_exporter
    DataProcessingUtils = data_processing_utils
    APIFetchUtils = api_fetch_utils
    APICoreFetchUtils = api_core_fetch_utils
    OrgInventoryExporter = org_inventory_exporter
    OrgSiteExporter = org_site_exporter
    InputUtils = input_utils
    execute_with_connection_pool_management = connection_pool_fn
    ValidationUtils = validation_utils
    RateLimitingUtils = rate_limiting_utils
    MIST_WAN_TARGET_PORTS = mist_wan_target_ports
    MIST_SITE_EXCLUDE_PREFIX = mist_site_exclude_prefix
    FAST_MODE_MAX_RETRIES = fast_mode_max_retries
    FAST_MODE_RETRY_DELAY = fast_mode_retry_delay
    _api_usage_cache = api_usage_cache
    tqdm = tqdm_module

    configure_gateway_stats_exporter_dependencies(
        apisession_dependency=apisession_dependency,
        mistapi_dependency=mistapi_dependency,
        config_utils=config_utils,
        validation_utils=validation_utils,
        data_processing_utils=data_processing_utils,
        data_exporter=data_exporter,
        rate_limiting_utils=rate_limiting_utils,
        cache_utils=cache_utils,
        file_path_utils=file_path_utils,
        connection_pool_fn=connection_pool_fn,
        fast_mode_max_retries=fast_mode_max_retries,
        fast_mode_retry_delay=fast_mode_retry_delay,
        api_usage_cache=api_usage_cache,
        tqdm_module=tqdm_module,
        gateway_export_utils_ref=GatewayExportUtils,
    )

    configure_gateway_override_dependencies(
        apisession_dependency=apisession_dependency,
        mistapi_dependency=mistapi_dependency,
        cache_utils=cache_utils,
        file_path_utils=file_path_utils,
        data_exporter=data_exporter,
        org_site_exporter=org_site_exporter,
        mist_wan_target_ports=mist_wan_target_ports,
        connection_pool_fn=connection_pool_fn,
        gateway_export_utils_ref=GatewayExportUtils,
    )


class GatewayExportUtils:
    """Centralized gateway export utilities extracted from MistHelper.py."""

    @staticmethod
    def _with_site_info():
        """Export gateways with associated site data."""
        OrgInventoryExporter.gateways_with_site_info()

    @staticmethod
    def _load_management_ip_csv_inputs() -> tuple[list[dict], list[dict], list[dict], list[dict]] | None:
        """Load the four CSV inputs required for gateway management-IP correlation."""
        logging.info("Loading CSV inputs for gateway management IP correlation")  # Log before disk reads.
        try:
            with open(FilePathUtils.get_csv_path("SiteList.csv"), encoding="utf-8") as csvfile:
                sites = list(csv.DictReader(csvfile))  # Site list with template assignments.
            with open(FilePathUtils.get_csv_path("OrgGatewayTemplates.csv"), encoding="utf-8") as csvfile:
                templates = list(csv.DictReader(csvfile))  # Org-level gateway templates.
            with open(FilePathUtils.get_csv_path("GatewaysWithSiteInfo.csv"), encoding="utf-8") as csvfile:
                gateway_devices = list(csv.DictReader(csvfile))  # Gateway devices with site + connection state.
            with open(FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv"), encoding="utf-8") as csvfile:
                gateway_configs = list(csv.DictReader(csvfile))  # Per-device config including mgmt overlay IP.
        except FileNotFoundError as exception:
            logging.error("Required CSV file not found: %s", exception)  # Preserve legacy error log.
            print(f"! Error: Required CSV file not found: {exception}")  # Preserve legacy operator message.
            return None
        logging.debug(
            "Loaded sites=%d templates=%d devices=%d configs=%d",
            len(sites),
            len(templates),
            len(gateway_devices),
            len(gateway_configs),
        )  # Log per-source row counts.
        return sites, templates, gateway_devices, gateway_configs

    @staticmethod
    def _classify_connected_status(connected_value: str) -> str:
        """Convert a raw 'connected' CSV cell into Online/Offline/Unknown."""
        normalized = str(connected_value).strip().lower()  # Normalize for case-insensitive comparison.
        if normalized in ("true", "1", "yes"):
            return "Online"  # Truthy boolean indicators map to Online.
        if normalized in ("false", "0", "no"):
            return "Offline"  # Falsy boolean indicators map to Offline.
        return "Unknown"  # Anything else preserves legacy Unknown fallback.

    @staticmethod
    def _build_management_ip_rows(
        gateway_devices: list[dict],
        site_lookup: dict,
        template_lookup: dict,
        mgmt_ip_lookup: dict,
    ) -> tuple[list[dict], int, int]:
        """Build per-device management-IP rows; return (rows, processed_count, with_mgmt_ip_count)."""
        results: list[dict] = []  # Per-device records for export.
        gateways_processed = 0  # Total devices iterated.
        gateways_with_mgmt_ip = 0  # Devices with a non-empty management IP.
        for device in gateway_devices:
            gateway_name = device.get("name", "Unknown Gateway")  # Fallback preserves legacy text.
            site_id = device.get("site_id", "")  # Empty string fallback for missing site_id.
            site_name = device.get("site_name", "Unknown Site")  # Fallback preserves legacy text.
            mgmt_ip = mgmt_ip_lookup.get(gateway_name, "")  # Empty if no config or no mgmt overlay IP.
            status = GatewayExportUtils._classify_connected_status(device.get("connected", ""))  # Map status.
            site_info = site_lookup.get(site_id, {})  # Empty dict if site_id not present.
            template_id = site_info.get("gatewaytemplate_id", "")  # Empty if no template assigned.
            template_name = (
                template_lookup.get(template_id, "No Template") if template_id else "No Template"
            )  # Preserve legacy 'No Template' string.
            results.append(
                {
                    "gateway_name": gateway_name,
                    "management_ip": mgmt_ip if mgmt_ip else "Not Configured",  # Legacy string for missing IP.
                    "status": status,
                    "site_name": site_name,
                    "gateway_template": template_name,
                    "template_id": template_id if template_id else "None",  # Legacy 'None' string for empty.
                }
            )
            gateways_processed += 1  # Increment processed counter after row append.
            if mgmt_ip:
                gateways_with_mgmt_ip += 1  # Track devices with a usable management IP.
                logging.debug(
                    "Gateway %s: Management IP %s, Status: %s (Template: %s)",
                    gateway_name,
                    mgmt_ip,
                    status,
                    template_name,
                )  # Preserve legacy per-device debug log.
            else:
                logging.debug(
                    "Gateway %s: No management IP configured, Status: %s (Template: %s)",
                    gateway_name,
                    status,
                    template_name,
                )  # Preserve legacy per-device debug log.
        return results, gateways_processed, gateways_with_mgmt_ip

    @staticmethod
    def management_ips(fast: bool = False) -> None:  # noqa: PLR0915
        """Export gateway management overlay IPs correlated with templates and site status."""
        logging.info("Menu #31: Starting gateway management IPs export")
        print("Gateway Management IP Export:")
        print("Collecting data from inventory, templates, and configurations...")

        ConfigUtils.get_cached_or_prompted_org_id()

        print("  1. Ensuring site list with template mappings is current...")
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)

        print("  2. Ensuring gateway templates are current...")
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtils.templates)

        print("  3. Ensuring gateway device data with connection status is current...")
        CacheUtils.check_and_generate_csv("GatewaysWithSiteInfo.csv", OrgInventoryExporter.gateways_with_site_info)

        print("  4. Ensuring gateway configurations with management IPs are current...")
        CacheUtils.check_and_generate_csv(
            "AllSiteGatewayConfigs.csv",
            lambda: GatewayExportUtils.device_configs(fast=fast),
        )

        print("  5. Processing and correlating data...")

        loaded = GatewayExportUtils._load_management_ip_csv_inputs()  # Read the four CSV inputs into memory.
        if loaded is None:  # Required CSV missing - error already printed/logged.
            return
        sites, templates, gateway_devices, gateway_configs = loaded  # Unpack inputs for correlation.

        site_lookup = {site.get("id"): site for site in sites}  # Index sites by ID for O(1) lookup.
        template_lookup = {
            template.get("id"): template.get("name", "Unknown Template") for template in templates
        }  # Index template ID -> name.
        mgmt_ip_lookup = {
            config.get("name"): config.get("gateway_mgmt_overlay_ip_ip", "") for config in gateway_configs
        }  # Index gateway name -> mgmt overlay IP.

        results, gateways_processed, gateways_with_mgmt_ip = GatewayExportUtils._build_management_ip_rows(
            gateway_devices, site_lookup, template_lookup, mgmt_ip_lookup
        )  # Build per-device correlation rows.

        results.sort(key=lambda row: (row["gateway_template"], row["gateway_name"]))

        final_results = [
            {
                "Gateway Name": row["gateway_name"],
                "Gateway Template": row["gateway_template"],
                "Management IP": row["management_ip"],
                "Online Status": row["status"],
                "Site Name": row["site_name"],
            }
            for row in results
        ]

        DataExporter.write_with_format_selection(final_results, "GatewayManagementIPs.csv")

        print("! Gateway management IP export completed:")
        print(f"  - Total gateways processed: {gateways_processed}")
        print(f"  - Gateways with management IPs: {gateways_with_mgmt_ip}")
        print(f"  - Gateways without management IPs: {gateways_processed - gateways_with_mgmt_ip}")
        print("  - Output CSV: GatewayManagementIPs.csv")

        logging.info(
            "Gateway management IP export completed. %d gateways processed, %d with management IPs.",
            gateways_processed,
            gateways_with_mgmt_ip,
        )

    @staticmethod
    def _build_filtered_port_rows(sanitized: list) -> list:
        """Return rows containing only base + WAN port columns where at least one port is non-empty."""
        base_columns = ["mac", "name"]  # Preserve legacy identifier columns.
        port_columns = [
            col
            for col in sanitized[0].keys()
            if re.match(r"(?i)port_config_ge-0/0/\d+_.*", col) and "_vpn_paths_" not in col
        ]  # Match WAN port-config columns excluding VPN-path noise.
        columns_to_keep = base_columns + port_columns  # Build final column projection list.
        logging.debug("Built port-column projection: %d port columns", len(port_columns))  # Log column count.
        return [
            {col: row.get(col, "") for col in columns_to_keep}
            for row in sanitized
            if any(row.get(col) not in [None, "", "null"] for col in port_columns)
        ]  # Filter rows lacking any port-config data.

    @staticmethod
    def _save_filtered_port_configs(filtered_rows: list, debug: bool) -> None:
        """Write FilteredGatewayPortConfigs.csv preserving legacy empty-file fallback."""
        if not filtered_rows:
            logging.warning(" No rows matched the port config filter. FilteredGatewayPortConfigs.csv will be empty.")
            filtered_csv_path = FilePathUtils.get_csv_path("FilteredGatewayPortConfigs.csv")  # Resolve path.
            logging.info("Writing empty marker file to %s", filtered_csv_path)  # Log before write.
            with open(filtered_csv_path, "w", newline="", encoding="utf-8") as csvfile:
                csvfile.write("No matching data found.\n")  # Preserve legacy empty marker content.
            return  # Nothing else to persist.
        if debug:
            logging.debug("Sample filtered row: %s", filtered_rows[0])
        logging.info("Saving filtered gateway port configs to FilteredGatewayPortConfigs.csv")  # Log before save.
        DataExporter.write_with_format_selection(
            filtered_rows, "FilteredGatewayPortConfigs.csv"
        )  # Persist filtered set.
        logging.info(" Filtered gateway port configs saved to FilteredGatewayPortConfigs.csv")

    @staticmethod
    def device_configs(debug: bool = False, fast: bool = False) -> None:
        """Fetch and export all gateway device configuration details."""
        logging.info("Starting export of all gateway device configurations...")
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org_id via standard pathway.
        data = APIFetchUtils.gateway_device_configs(apisession, org_id, fast=fast)  # Fetch gateway configs.
        if not data:
            logging.warning(" No device configs found.")
            return  # Abort when no configs returned.
        flattened = DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested JSON.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # Escape multiline cells for CSV.
        logging.info("Saving sanitized gateway configs to AllSiteGatewayConfigs.csv")  # Log before save.
        DataExporter.write_with_format_selection(sanitized, "AllSiteGatewayConfigs.csv")  # Persist full configs.
        logging.info(" Device configs saved to AllSiteGatewayConfigs.csv")
        filtered_rows = GatewayExportUtils._build_filtered_port_rows(sanitized)  # Build port-config subset.
        GatewayExportUtils._save_filtered_port_configs(filtered_rows, debug)  # Persist filtered subset.

    @staticmethod
    def templates():
        """Export gateway templates for the selected organization."""
        print("Gateway Templates:")
        logging.info("Exporting gateway templates for the organization...")
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()
        response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(apisession, current_org_id)
        templates = getattr(response, "data", [])
        if not templates:
            logging.warning("No gateway templates found for this organization.")
            print("No gateway templates found for this organization.")
            return
        templates = DataProcessingUtils.flatten_nested_fields(templates)
        templates = DataProcessingUtils.escape_multiline(templates)
        DataExporter.write_with_format_selection(templates, "OrgGatewayTemplates.csv")
        print(f"! {len(templates)} gateway templates exported to OrgGatewayTemplates.csv")
        logging.info(" Gateway templates exported to OrgGatewayTemplates.csv")

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:
        """Run the WAN override compliance report via the WanOverrideWalker orchestrator."""
        logging.info("Starting WAN override compliance report (fast=%s)", fast)  # Before-action log
        WanOverrideWalker.walk(fast=fast)  # Orchestrate cache/classify/fetch/report end-to-end
        logging.debug("WAN override compliance report finished (fast=%s)", fast)  # After-action log

    @staticmethod
    def _get_devices_with_sites(org_id: str, fast: bool = False) -> list[tuple[str, str, str, str]]:
        """Fetch all gateway devices with site metadata for downstream gateway exports."""
        logging.info("[INFO] Fetching gateway devices with site information...")
        if fast:
            return GatewayExportUtils._get_devices_from_cache()
        return GatewayExportUtils._get_devices_from_api(org_id)

    @staticmethod
    def _get_devices_from_cache() -> list[tuple[str, str, str, str]]:
        """Get gateway devices from cached inventory and site list CSVs."""
        try:
            CacheUtils.check_and_generate_csv("OrgInventory.csv", OrgInventoryExporter.inventory)
            CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)

            inventory_path = FilePathUtils.get_csv_path("OrgInventory.csv")
            with open(inventory_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                gateways = [
                    row for row in reader if row.get("type") == "gateway" and row.get("site_id") and row.get("id")
                ]

            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")
            with open(site_list_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                site_name_lookup = {row.get("id"): row.get("name", "Unknown Site") for row in reader}

            gateway_devices = []
            for device in gateways:
                site_id = device.get("site_id", "")
                device_id = device.get("id", "")
                device_name = device.get("name", "")
                site_name = site_name_lookup.get(site_id, "Unknown Site")
                gateway_devices.append((site_id, device_id, device_name, site_name))

            logging.info("! Fast mode: Loaded %s gateway devices from cached data", len(gateway_devices))
            return gateway_devices

        except Exception as exception:
            logging.warning("! Fast mode failed, falling back to API calls: %s", exception)
            org_id = ConfigUtils.get_cached_or_prompted_org_id()
            return GatewayExportUtils._get_devices_from_api(org_id)

    @staticmethod
    def _get_devices_from_api(org_id: str) -> list[tuple[str, str, str, str]]:
        """Get gateway devices from API inventory and site list endpoints."""
        logging.info("[INFO] Fetching org inventory to find gateway devices...")
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)
        logging.info("[INFO] Retrieved %s devices from org inventory.", len(devices))

        site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)
        sites = mistapi.get_all(response=site_response, mist_session=apisession)
        site_name_lookup = {site["id"]: site.get("name", "Unknown Site") for site in sites}

        gateway_devices = []
        for device in devices:
            if device.get("type") == "gateway" and device.get("site_id") and device.get("id"):
                site_id = device.get("site_id", "")
                device_id = device.get("id", "")
                device_name = device.get("name", "")
                site_name = site_name_lookup.get(site_id, "Unknown Site")
                gateway_devices.append((site_id, device_id, device_name, site_name))

        logging.info("[INFO] Found %s gateway devices across the organization.", len(gateway_devices))
        return gateway_devices

    @staticmethod
    def _get_site_ids_with_devices(org_id: str) -> list[str]:
        """Get site IDs that currently contain at least one gateway device."""
        logging.info("[INFO] Fetching org inventory to find sites with gateways...")
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)
        logging.info("[INFO] Retrieved %s devices from org inventory.", len(devices))

        gateway_sites = {
            device["site_id"]
            for device in devices
            if device.get("type") == "gateway" and device.get("site_id") and str(device.get("site_id")).strip()
        }
        logging.info("[INFO] Found %s sites with at least one gateway.", len(gateway_sites))

        return list(gateway_sites)

    @staticmethod
    def wan2_variable_migration(fast: bool = False, dry_run: bool = False) -> None:
        """Update gateway template WAN2 variable through extracted migrator."""
        from src.gateway.wan2_variable import GatewayWan2VariableMigrator  # noqa: PLC0415

        migrator = GatewayWan2VariableMigrator(
            org_id=ConfigUtils.get_cached_or_prompted_org_id(),
            apisession=apisession,
            site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            generate_templates_fn=GatewayExportUtils.templates,
            generate_sites_fn=OrgSiteExporter.sites,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            save_data_fn=DataExporter.write_with_format_selection,
            input_fn=InputUtils.safe_input,
            connection_pool_fn=execute_with_connection_pool_management,
        )
        migrator.execute(fast=fast, dry_run=dry_run)
