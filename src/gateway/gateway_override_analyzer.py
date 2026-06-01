"""Gateway override analyzer extracted from MistHelper.py."""

from __future__ import annotations

import csv
import logging
from typing import Any

apisession: Any = None
mistapi: Any = None
CacheUtils: Any = None
FilePathUtils: Any = None
DataExporter: Any = None
OrgSiteExporter: Any = None
MIST_WAN_TARGET_PORTS: list[str] = []
execute_with_connection_pool_management: Any = None
GatewayExportUtilsRef: Any = None


def configure_gateway_override_analyzer_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    cache_utils: Any,
    file_path_utils: Any,
    data_exporter: Any,
    org_site_exporter: Any,
    mist_wan_target_ports: list[str],
    connection_pool_fn: Any,
    gateway_export_utils_ref: Any,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global mistapi
    global CacheUtils
    global FilePathUtils
    global DataExporter
    global OrgSiteExporter
    global MIST_WAN_TARGET_PORTS
    global execute_with_connection_pool_management
    global GatewayExportUtilsRef

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    CacheUtils = cache_utils
    FilePathUtils = file_path_utils
    DataExporter = data_exporter
    OrgSiteExporter = org_site_exporter
    MIST_WAN_TARGET_PORTS = mist_wan_target_ports
    execute_with_connection_pool_management = connection_pool_fn
    GatewayExportUtilsRef = gateway_export_utils_ref


class GatewayOverrideAnalyzer:
    """Extracted gateway override analysis implementation."""

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:  # noqa: C901, PLR0912, PLR0915
        """Generate report of gateways with template-overridden WAN ports."""
        print("Gateway Ports Overridden from Template (Compliance Outliers):")
        logging.info(" Identifying gateway ports with template overrides (outliers for compliance correction)...")

        target_ports = MIST_WAN_TARGET_PORTS
        if not target_ports:
            print(" MIST_WAN_TARGET_PORTS not configured in .env - skipping port override analysis")
            logging.warning("MIST_WAN_TARGET_PORTS environment variable not set")
            return

        CacheUtils.check_and_generate_csv(
            "AllSiteGatewayConfigs.csv",
            lambda: GatewayExportUtilsRef.device_configs(fast=fast),
        )
        CacheUtils.check_and_generate_csv("SiteList_ListAPI.csv", OrgSiteExporter.sites_list_api)
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtilsRef.templates)

        with open(FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv"), encoding="utf-8") as csvfile:
            configs = list(csv.DictReader(csvfile))
        with open(FilePathUtils.get_csv_path("SiteList_ListAPI.csv"), encoding="utf-8") as csvfile:
            sites = list(csv.DictReader(csvfile))
        with open(FilePathUtils.get_csv_path("OrgGatewayTemplates.csv"), encoding="utf-8") as csvfile:
            templates = list(csv.DictReader(csvfile))

        site_lookup = {site.get("id"): site.get("name", "Unknown Site") for site in sites}
        site_to_template_id = {site.get("id"): site.get("gatewaytemplate_id", "") for site in sites}
        template_lookup = {template.get("id"): template.get("name", "Unknown Template") for template in templates}

        overridden_port_info = []

        logging.info(" First pass: Identifying devices with port overrides...")
        devices_with_overrides = {}

        for row in configs:
            device_name = row.get("name", "").strip()
            site_id = row.get("site_id", "").strip()
            device_id = row.get("id", "").strip()
            site_name = site_lookup.get(site_id, "Unknown Site")
            template_id = site_to_template_id.get(site_id, "")
            template_name = template_lookup.get(template_id, "No Template") if template_id else "No Template"

            if not device_name or not site_id or not device_id:
                continue

            device_overridden_ports = []
            for port_name in target_ports:
                port_config_fields = [
                    col
                    for col in row
                    if col.startswith(f"port_config_{port_name}_") or col.startswith(f"port_config_{port_name}.")
                ]

                override_fields = []
                for field_name in port_config_fields:
                    value = row.get(field_name, "").strip().lower()
                    if value not in ["", "null", "none"] and "_vpn_paths_" not in field_name:
                        override_fields.append(f"{field_name}={value}")

                if len(override_fields) > 0:
                    device_overridden_ports.append(port_name)

            if device_overridden_ports:
                devices_with_overrides[device_id] = {
                    "device_name": device_name,
                    "site_id": site_id,
                    "site_name": site_name,
                    "template_id": template_id,
                    "template_name": template_name,
                    "row_data": row,
                    "overridden_ports": device_overridden_ports,
                }

        logging.info(
            "! Found %d devices with port overrides out of %d total gateway devices",
            len(devices_with_overrides),
            len(configs),
        )

        if not devices_with_overrides:
            logging.info(" No template overrides found - all gateways are compliant with their assigned templates!")
            output_file = "GatewayOverriddenPorts.csv"
            fieldnames = [
                "gateway_device_name",
                "site_name",
                "template_name",
                "port_name",
                "recommended_variable",
                "port_description",
                "port_status",
                "port_admin_status",
                "port_gateway_ip",
                "port_ip_address",
                "port_netmask",
                "port_config_type",
                "port_usage",
                "overridden_from_template",
                "device_id",
                "site_id",
                "template_id",
            ]
            output_path = FilePathUtils.get_csv_path(output_file)
            with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            print(f"! Gateway override report written to {output_file}")
            print(" No template overrides found - all gateways are compliant with their assigned templates!")
            return

        logging.info(
            "! Second pass: Fetching device configs and stats for %d devices with overrides...",
            len(devices_with_overrides),
        )

        if fast and len(devices_with_overrides) > 5:
            logging.info(" Using fast mode with connection pool management for device data fetching...")

            def fetch_device_data(device_info, connection_semaphore):
                device_id_inner = device_info[0]
                device_data = device_info[1]
                device_name_inner = device_data["device_name"]
                site_id_inner = device_data["site_id"]

                with connection_semaphore:
                    port_configs = {}
                    interface_stats = {}

                    try:
                        resp = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id_inner, device_id_inner)
                        device_config_data = getattr(resp, "data", {})
                        port_configs = device_config_data.get("port_config", {})
                    except Exception as exception:
                        logging.warning(
                            "[WARN] Could not fetch device config for %s (%s): %s",
                            device_name_inner,
                            device_id_inner,
                            exception,
                        )
                        port_configs = {}

                    try:
                        stats_resp = mistapi.api.v1.sites.stats.getSiteDeviceStats(
                            apisession, site_id_inner, device_id_inner
                        )
                        stats_data = getattr(stats_resp, "data", {})
                        interface_stats = stats_data.get("if_stat", {})
                    except Exception as exception:
                        if "403" in str(exception) or "Forbidden" in str(exception):
                            logging.warning(
                                "[WARN] Insufficient permissions to fetch device stats for %s (%s): 403 Forbidden",
                                device_name_inner,
                                device_id_inner,
                            )
                        else:
                            logging.warning(
                                "[WARN] Could not fetch device stats for %s (%s): %s",
                                device_name_inner,
                                device_id_inner,
                                exception,
                            )
                        interface_stats = {}

                    return (device_id_inner, port_configs, interface_stats)

            work_items = list(devices_with_overrides.items())
            successful_results, failed_devices = execute_with_connection_pool_management(
                work_items=work_items,
                worker_function=fetch_device_data,
                batch_description="override devices",
                retry_function=None,
            )

            device_data_cache = {}
            for device_id_result, port_configs, interface_stats in successful_results:
                device_data_cache[device_id_result] = (port_configs, interface_stats)

            for failed_item in failed_devices:
                device_id_failed = failed_item[0]
                device_data_cache[device_id_failed] = ({}, {})

            logging.info(
                "! Fast mode: Fetched data for %d/%d devices with connection pool protection",
                len(successful_results),
                len(work_items),
            )

        else:
            device_data_cache = {}
            for device_id, device_info in devices_with_overrides.items():
                device_name = device_info["device_name"]
                site_id = device_info["site_id"]

                try:
                    resp = mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)
                    device_data = getattr(resp, "data", {})
                    port_configs = device_data.get("port_config", {})
                except Exception as exception:
                    logging.warning(
                        f"[WARN] Could not fetch device config for {device_name} ({device_id}): {exception}"
                    )
                    port_configs = {}

                try:
                    stats_resp = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, site_id, device_id)
                    stats_data = getattr(stats_resp, "data", {})
                    interface_stats = stats_data.get("if_stat", {})
                except Exception as exception:
                    if "403" in str(exception) or "Forbidden" in str(exception):
                        logging.warning(
                            "[WARN] Insufficient permissions to fetch device stats for %s (%s): 403 Forbidden",
                            device_name,
                            device_id,
                        )
                    else:
                        logging.warning(
                            f"[WARN] Could not fetch device stats for {device_name} ({device_id}): {exception}"
                        )
                    interface_stats = {}

                device_data_cache[device_id] = (port_configs, interface_stats)

        logging.info(" Third pass: Processing overridden ports with live data...")
        for device_id, device_info in devices_with_overrides.items():
            device_name = device_info["device_name"]
            site_id = device_info["site_id"]
            site_name = device_info["site_name"]
            template_id = device_info["template_id"]
            template_name = device_info["template_name"]
            row = device_info["row_data"]
            overridden_ports = device_info["overridden_ports"]

            port_configs, interface_stats = device_data_cache.get(device_id, ({}, {}))

            for port_name in overridden_ports:
                port_config = port_configs.get(port_name, {})
                interface_stat = interface_stats.get(port_name, {})

                ip_config = port_config.get("ip_config", {})
                usage = port_config.get("usage", "")
                description = port_config.get("description", "")
                disabled = port_config.get("disabled", False)

                port_ip = ip_config.get("ip", "")
                netmask = ip_config.get("netmask", "")
                gateway_ip = ip_config.get("gateway", "")
                config_type = ip_config.get("type", "")

                if config_type == "dhcp":
                    config_type_display = "DHCP"
                elif config_type == "static":
                    config_type_display = "STATIC"
                else:
                    config_type_display = config_type.upper() if config_type else "UNKNOWN"

                port_status = "down"
                if interface_stat and interface_stat.get("up", False):
                    port_status = "up"

                admin_status = "disabled" if disabled else "enabled"

                port_entry = {
                    "gateway_device_name": device_name,
                    "site_name": site_name,
                    "template_name": template_name,
                    "port_name": port_name,
                    "port_description": description,
                    "port_status": port_status,
                    "port_admin_status": admin_status,
                    "port_gateway_ip": gateway_ip,
                    "port_ip_address": port_ip,
                    "port_netmask": netmask,
                    "port_config_type": config_type_display,
                    "port_usage": usage,
                    "overridden_from_template": "Yes",
                    "device_id": device_id,
                    "site_id": site_id,
                    "template_id": template_id,
                }
                overridden_port_info.append(port_entry)

        output_file = "GatewayOverriddenPorts.csv"
        DataExporter.save_data_to_output(overridden_port_info, output_file)

        total_gateways_processed = len(configs)
        devices_with_overrides_count = len(devices_with_overrides) if "devices_with_overrides" in locals() else 0
        if overridden_port_info:
            gateways_with_overrides = len(set(entry["device_id"] for entry in overridden_port_info))
        else:
            gateways_with_overrides = 0
        total_overridden_ports = len(overridden_port_info)

        logging.info(
            "! Gateway override report written to %s with %d overridden ports from %d gateway devices.",
            output_file,
            total_overridden_ports,
            gateways_with_overrides,
        )
        logging.info(
            "! API Optimization: Made device config/stats calls for only %d devices instead of all %d devices",
            devices_with_overrides_count,
            total_gateways_processed,
        )
        print(f"! Gateway override report written to {output_file}")
        print(
            f"! Found {total_overridden_ports} overridden ports across"
            f" {gateways_with_overrides} of {total_gateways_processed} gateway devices"
        )
        # Calculate saved API calls for readability
        saved_calls = total_gateways_processed - devices_with_overrides_count
        print(
            f"! API Optimization: Only fetched live data for {devices_with_overrides_count}"
            f" devices with overrides (saved {saved_calls} unnecessary API calls)"
        )
        print(f"! Target ports analyzed: {', '.join(target_ports)}")
        print("! These are outliers that may need correction to match template configuration")

        if total_overridden_ports == 0:
            print(" No template overrides found - all gateways are compliant with their assigned templates!")
