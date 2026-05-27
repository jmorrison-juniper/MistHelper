"""Gateway export utilities extracted from MistHelper.py."""

from __future__ import annotations

import csv
import logging
import re
from typing import Any

from src.gateway.gateway_override_analyzer import (
    GatewayOverrideAnalyzer,
    configure_gateway_override_analyzer_dependencies,
)
from src.gateway.gateway_stats_exporter import configure_gateway_stats_exporter_dependencies

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

    configure_gateway_override_analyzer_dependencies(
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

        try:
            with open(FilePathUtils.get_csv_path("SiteList.csv"), encoding="utf-8") as csvfile:
                sites = list(csv.DictReader(csvfile))
            with open(FilePathUtils.get_csv_path("OrgGatewayTemplates.csv"), encoding="utf-8") as csvfile:
                templates = list(csv.DictReader(csvfile))
            with open(FilePathUtils.get_csv_path("GatewaysWithSiteInfo.csv"), encoding="utf-8") as csvfile:
                gateway_devices = list(csv.DictReader(csvfile))
            with open(FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv"), encoding="utf-8") as csvfile:
                gateway_configs = list(csv.DictReader(csvfile))
        except FileNotFoundError as exception:
            logging.error(f"Required CSV file not found: {exception}")
            print(f"! Error: Required CSV file not found: {exception}")
            return

        site_lookup = {site.get("id"): site for site in sites}
        template_lookup = {template.get("id"): template.get("name", "Unknown Template") for template in templates}
        mgmt_ip_lookup = {
            config.get("name"): config.get("gateway_mgmt_overlay_ip_ip", "") for config in gateway_configs
        }

        results = []
        gateways_processed = 0
        gateways_with_mgmt_ip = 0

        for device in gateway_devices:
            gateway_name = device.get("name", "Unknown Gateway")
            site_id = device.get("site_id", "")
            site_name = device.get("site_name", "Unknown Site")
            connected_status = device.get("connected", "")
            mgmt_ip = mgmt_ip_lookup.get(gateway_name, "")
            connected_val = str(connected_status).strip().lower()

            if connected_val in ["true", "1", "yes"]:
                status = "Online"
            elif connected_val in ["false", "0", "no"]:
                status = "Offline"
            else:
                status = "Unknown"

            site_info = site_lookup.get(site_id, {})
            template_id = site_info.get("gatewaytemplate_id", "")
            template_name = template_lookup.get(template_id, "No Template") if template_id else "No Template"

            result_row = {
                "gateway_name": gateway_name,
                "management_ip": mgmt_ip if mgmt_ip else "Not Configured",
                "status": status,
                "site_name": site_name,
                "gateway_template": template_name,
                "template_id": template_id if template_id else "None",
            }

            results.append(result_row)
            gateways_processed += 1

            if mgmt_ip:
                gateways_with_mgmt_ip += 1
                logging.debug(
                    f"Gateway {gateway_name}: Management IP {mgmt_ip}, Status: {status} (Template: {template_name})"
                )
            else:
                logging.debug(
                    f"Gateway {gateway_name}: No management IP configured, Status: {status} (Template: {template_name})"
                )

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

        DataExporter.save_data_to_output(final_results, "GatewayManagementIPs.csv")

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
    def device_configs(debug: bool = False, fast: bool = False) -> None:
        """Fetch and export all gateway device configuration details."""
        logging.info("Starting export of all gateway device configurations...")
        org_id = ConfigUtils.get_cached_or_prompted_org_id()
        data = APIFetchUtils.gateway_device_configs(apisession, org_id, fast=fast)
        if not data:
            logging.warning(" No device configs found.")
            return

        flattened = DataProcessingUtils.flatten_nested_fields(data)
        sanitized = DataProcessingUtils.escape_multiline(flattened)
        DataExporter.save_data_to_output(sanitized, "AllSiteGatewayConfigs.csv")
        logging.info(" Device configs saved to AllSiteGatewayConfigs.csv")

        base_columns = ["mac", "name"]
        port_columns = [
            col
            for col in sanitized[0].keys()
            if re.match(r"(?i)port_config_ge-0/0/\d+_.*", col) and "_vpn_paths_" not in col
        ]
        columns_to_keep = base_columns + port_columns

        filtered_rows = [
            {col: row.get(col, "") for col in columns_to_keep}
            for row in sanitized
            if any(row.get(col) not in [None, "", "null"] for col in port_columns)
        ]

        if not filtered_rows:
            logging.warning(" No rows matched the port config filter. FilteredGatewayPortConfigs.csv will be empty.")
            filtered_csv_path = FilePathUtils.get_csv_path("FilteredGatewayPortConfigs.csv")
            with open(filtered_csv_path, "w", newline="", encoding="utf-8") as csvfile:
                csvfile.write("No matching data found.\n")
        else:
            if debug:
                logging.debug(f"Sample filtered row: {filtered_rows[0]}")
            DataExporter.save_data_to_output(filtered_rows, "FilteredGatewayPortConfigs.csv")
            logging.info(" Filtered gateway port configs saved to FilteredGatewayPortConfigs.csv")

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
        DataExporter.save_data_to_output(templates, "OrgGatewayTemplates.csv")
        print(f"! {len(templates)} gateway templates exported to OrgGatewayTemplates.csv")
        logging.info(" Gateway templates exported to OrgGatewayTemplates.csv")

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:
        """Delegated gateway override analysis entrypoint."""
        GatewayOverrideAnalyzer.with_wan_overrides(fast=fast)

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

            logging.info(f"! Fast mode: Loaded {len(gateway_devices)} gateway devices from cached data")
            return gateway_devices

        except Exception as exception:
            logging.warning(f"! Fast mode failed, falling back to API calls: {exception}")
            org_id = ConfigUtils.get_cached_or_prompted_org_id()
            return GatewayExportUtils._get_devices_from_api(org_id)

    @staticmethod
    def _get_devices_from_api(org_id: str) -> list[tuple[str, str, str, str]]:
        """Get gateway devices from API inventory and site list endpoints."""
        logging.info("[INFO] Fetching org inventory to find gateway devices...")
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)
        logging.info(f"[INFO] Retrieved {len(devices)} devices from org inventory.")

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

        logging.info(f"[INFO] Found {len(gateway_devices)} gateway devices across the organization.")
        return gateway_devices

    @staticmethod
    def _get_site_ids_with_devices(org_id: str) -> list[str]:
        """Get site IDs that currently contain at least one gateway device."""
        logging.info("[INFO] Fetching org inventory to find sites with gateways...")
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)
        logging.info(f"[INFO] Retrieved {len(devices)} devices from org inventory.")

        gateway_sites = {
            device["site_id"]
            for device in devices
            if device.get("type") == "gateway" and device.get("site_id") and str(device.get("site_id")).strip()
        }
        logging.info(f"[INFO] Found {len(gateway_sites)} sites with at least one gateway.")

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
            save_data_fn=DataExporter.save_data_to_output,
            input_fn=InputUtils.safe_input,
            connection_pool_fn=execute_with_connection_pool_management,
        )
        migrator.execute(fast=fast, dry_run=dry_run)
