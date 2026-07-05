"""Gateway export utilities extracted from MistHelper.py."""

from __future__ import annotations  # WHY: postpone hint evaluation for forward refs across helpers.

import csv  # WHY: parse cached CSV inputs during correlation flows.
import logging  # WHY: structured logging for entry/exit and errors.
import re  # WHY: regex match against WAN port-config column names.
from typing import Any  # WHY: opaque types for injected utility modules.

from src.gateway.gateway_stats_exporter import configure_gateway_stats_exporter_dependencies  # WHY: delegate wiring.
from src.gateway.overrides import (  # WHY: import walker + override wiring entry point.
    WanOverrideWalker,
    configure_gateway_override_dependencies,
)

MANAGEMENT_IP_INPUT_CSVS: tuple[str, ...] = (  # WHY: fixed set of correlation inputs for management-IP export.
    "SiteList.csv",
    "OrgGatewayTemplates.csv",
    "GatewaysWithSiteInfo.csv",
    "AllSiteGatewayConfigs.csv",
)
CONNECTED_TRUE_TOKENS: frozenset[str] = frozenset({"true", "1", "yes"})  # WHY: truthy connection-state markers.
CONNECTED_FALSE_TOKENS: frozenset[str] = frozenset({"false", "0", "no"})  # WHY: falsy connection-state markers.
STATUS_ONLINE = "Online"  # WHY: legacy connected-status label preserved verbatim.
STATUS_OFFLINE = "Offline"  # WHY: legacy disconnected-status label preserved verbatim.
STATUS_UNKNOWN = "Unknown"  # WHY: legacy fallback-status label preserved verbatim.
UNKNOWN_SITE = "Unknown Site"  # WHY: fallback display name for missing site name.
UNKNOWN_GATEWAY = "Unknown Gateway"  # WHY: fallback display name for missing gateway name.
NO_TEMPLATE_LABEL = "No Template"  # WHY: legacy label for gateways without template assignment.
MGMT_IP_MISSING_LABEL = "Not Configured"  # WHY: legacy label for missing management IP.
TEMPLATE_ID_MISSING_LABEL = "None"  # WHY: legacy label for empty template_id.
WAN_PORT_COLUMN_PATTERN = re.compile(r"(?i)port_config_ge-0/0/\d+_.*")  # WHY: cached regex for WAN column filter.
EMPTY_CELL_MARKERS: tuple[Any, ...] = (None, "", "null")  # WHY: values considered empty for port-config filter.

apisession: Any = None  # WHY: Mist API session slot populated at wiring time.
mistapi: Any = None  # WHY: mistapi SDK module slot populated at wiring time.
ConfigUtils: Any = None  # WHY: config helpers facade (org id resolver).
CacheUtils: Any = None  # WHY: CSV cache generator facade.
FilePathUtils: Any = None  # WHY: resolves CSV cache file locations.
DataExporter: Any = None  # WHY: writes report data with format selection.
DataProcessingUtils: Any = None  # WHY: flatten/normalise helpers for CSV output.
APIFetchUtils: Any = None  # WHY: paged fetch helpers for gateway configs.
APICoreFetchUtils: Any = None  # WHY: core unwrap helpers for org inventory.
OrgInventoryExporter: Any = None  # WHY: org inventory exporter facade.
OrgSiteExporter: Any = None  # WHY: org site exporter facade.
InputUtils: Any = None  # WHY: safe_input wrapper for operator prompts.
execute_with_connection_pool_management: Any = None  # WHY: pool-managed parallel runner.
ValidationUtils: Any = None  # WHY: shared input validators.
RateLimitingUtils: Any = None  # WHY: adaptive delay helpers for API pacing.
MIST_WAN_TARGET_PORTS: list[str] = []  # WHY: operator-configured WAN port list from .env.
MIST_SITE_EXCLUDE_PREFIX: str = ""  # WHY: prefix filter that removes lab/test sites.
FAST_MODE_MAX_RETRIES: int = 2  # WHY: retry cap for fast-mode API calls.
FAST_MODE_RETRY_DELAY: float = 0.5  # WHY: base delay (seconds) between retries.
_api_usage_cache: Any = None  # WHY: shared API usage cache reference.
tqdm: Any = None  # WHY: progress bar dependency reference.


def _wire_stats_exporter(deps: dict[str, Any]) -> None:  # WHY: forward stats-exporter slots only.
    """Prime the gateway stats exporter module-level slots from the shared dependency bundle."""
    configure_gateway_stats_exporter_dependencies(  # WHY: table-driven pass-through of shared deps.
        apisession_dependency=deps["apisession_dependency"],
        mistapi_dependency=deps["mistapi_dependency"],
        config_utils=deps["config_utils"],
        validation_utils=deps["validation_utils"],
        data_processing_utils=deps["data_processing_utils"],
        data_exporter=deps["data_exporter"],
        rate_limiting_utils=deps["rate_limiting_utils"],
        cache_utils=deps["cache_utils"],
        file_path_utils=deps["file_path_utils"],
        connection_pool_fn=deps["connection_pool_fn"],
        fast_mode_max_retries=deps["fast_mode_max_retries"],
        fast_mode_retry_delay=deps["fast_mode_retry_delay"],
        api_usage_cache=deps["api_usage_cache"],
        tqdm_module=deps["tqdm_module"],
        gateway_export_utils_ref=GatewayExportUtils,
    )


def _wire_override_subsystem(deps: dict[str, Any]) -> None:  # WHY: forward override-subsystem slots only.
    """Prime the WAN override analysis module-level slots from the shared dependency bundle."""
    configure_gateway_override_dependencies(  # WHY: table-driven pass-through of shared deps.
        apisession_dependency=deps["apisession_dependency"],
        mistapi_dependency=deps["mistapi_dependency"],
        cache_utils=deps["cache_utils"],
        file_path_utils=deps["file_path_utils"],
        data_exporter=deps["data_exporter"],
        org_site_exporter=deps["org_site_exporter"],
        mist_wan_target_ports=deps["mist_wan_target_ports"],
        connection_pool_fn=deps["connection_pool_fn"],
        gateway_export_utils_ref=GatewayExportUtils,
    )


def _dispatch_downstream_wiring(deps: dict[str, Any]) -> None:  # WHY: forward wiring to sibling modules once.
    """Forward the same dependency bundle to the stats exporter and override subsystem."""
    _wire_stats_exporter(deps)  # WHY: prime stats-exporter module-level slots.
    _wire_override_subsystem(deps)  # WHY: prime override-analysis module-level slots.


_KWARG_TO_MODULE_SLOT: dict[str, str] = {  # WHY: table-driven map from configure kwargs to module-level names.
    "apisession_dependency": "apisession",
    "mistapi_dependency": "mistapi",
    "config_utils": "ConfigUtils",
    "cache_utils": "CacheUtils",
    "file_path_utils": "FilePathUtils",
    "data_exporter": "DataExporter",
    "data_processing_utils": "DataProcessingUtils",
    "api_fetch_utils": "APIFetchUtils",
    "api_core_fetch_utils": "APICoreFetchUtils",
    "org_inventory_exporter": "OrgInventoryExporter",
    "org_site_exporter": "OrgSiteExporter",
    "input_utils": "InputUtils",
    "connection_pool_fn": "execute_with_connection_pool_management",
    "validation_utils": "ValidationUtils",
    "rate_limiting_utils": "RateLimitingUtils",
    "mist_wan_target_ports": "MIST_WAN_TARGET_PORTS",
    "mist_site_exclude_prefix": "MIST_SITE_EXCLUDE_PREFIX",
    "fast_mode_max_retries": "FAST_MODE_MAX_RETRIES",
    "fast_mode_retry_delay": "FAST_MODE_RETRY_DELAY",
    "api_usage_cache": "_api_usage_cache",
    "tqdm_module": "tqdm",
}


def configure_gateway_export_utils_dependencies(**deps: Any) -> None:  # WHY: variadic-kwargs collapse for 21 slots.
    """Configure runtime dependencies from MistHelper orchestration layer."""
    globals().update(  # WHY: bulk-assign module slots using the table-driven kwarg->slot map.
        {slot: deps[kwarg] for kwarg, slot in _KWARG_TO_MODULE_SLOT.items()}
    )
    _dispatch_downstream_wiring(deps)  # WHY: forward wiring to stats exporter + override subsystem.


def _classify_connected_status(connected_value: str) -> str:  # WHY: normalise raw CSV boolean cell to label.
    """Convert a raw 'connected' CSV cell into Online/Offline/Unknown."""
    normalized = str(connected_value).strip().lower()  # WHY: normalise for case-insensitive comparison.
    if normalized in CONNECTED_TRUE_TOKENS:  # WHY: truthy indicator maps to Online.
        return STATUS_ONLINE
    if normalized in CONNECTED_FALSE_TOKENS:  # WHY: falsy indicator maps to Offline.
        return STATUS_OFFLINE
    return STATUS_UNKNOWN  # WHY: preserve legacy Unknown fallback for anything else.


def _read_csv_rows(name: str) -> list[dict[str, Any]]:  # WHY: shared CSV reader by logical cache name.
    """Read a cached CSV file by logical name and return its rows."""
    path = FilePathUtils.get_csv_path(name)  # WHY: resolve logical name to concrete filesystem path.
    with open(path, encoding="utf-8") as csvfile:  # WHY: UTF-8 by convention for CSV cache.
        return list(csv.DictReader(csvfile))  # WHY: materialise rows for repeated iteration.


def _log_management_ip_row(gateway_name: str, mgmt_ip: str, status: str, template_name: str) -> None:
    """Emit per-device debug log preserving legacy formatting."""
    if mgmt_ip:  # WHY: with-IP path keeps the mgmt IP in the log line.
        logging.debug(
            "Gateway %s: Management IP %s, Status: %s (Template: %s)",
            gateway_name,
            mgmt_ip,
            status,
            template_name,
        )  # WHY: preserve legacy per-device debug log with mgmt IP.
        return
    logging.debug(  # WHY: no-IP path preserves the legacy "no management IP configured" phrase.
        "Gateway %s: No management IP configured, Status: %s (Template: %s)",
        gateway_name,
        status,
        template_name,
    )


def _resolve_template_name(template_lookup: dict, template_id: str) -> str:  # WHY: apply legacy fallback rules.
    """Return the template display name for a given id, using legacy fallback labels."""
    if not template_id:  # WHY: unassigned devices show the legacy 'No Template' label.
        return NO_TEMPLATE_LABEL
    return template_lookup.get(template_id, NO_TEMPLATE_LABEL)  # WHY: preserve legacy 'No Template' fallback.


def _build_management_ip_row(device: dict, lookups: dict[str, dict]) -> tuple[dict, str]:
    """Return (row, mgmt_ip) for a single gateway device using shared lookups."""
    gateway_name = device.get("name", UNKNOWN_GATEWAY)  # WHY: fallback preserves legacy text.
    site_id = device.get("site_id", "")  # WHY: empty string fallback for missing site_id.
    site_name = device.get("site_name", UNKNOWN_SITE)  # WHY: fallback preserves legacy text.
    mgmt_ip = lookups["mgmt_ip"].get(gateway_name, "")  # WHY: empty if no config or no mgmt overlay IP.
    status = _classify_connected_status(device.get("connected", ""))  # WHY: map raw cell to Online/Offline.
    site_info = lookups["site"].get(site_id, {})  # WHY: empty dict if site_id not present.
    template_id = site_info.get("gatewaytemplate_id", "")  # WHY: empty if no template assigned.
    template_name = _resolve_template_name(lookups["template"], template_id)  # WHY: apply legacy fallback rules.
    row = {
        "gateway_name": gateway_name,
        "management_ip": mgmt_ip if mgmt_ip else MGMT_IP_MISSING_LABEL,  # WHY: legacy string for missing IP.
        "status": status,
        "site_name": site_name,
        "gateway_template": template_name,
        "template_id": template_id if template_id else TEMPLATE_ID_MISSING_LABEL,  # WHY: legacy 'None' fallback.
    }
    _log_management_ip_row(gateway_name, mgmt_ip, status, template_name)  # WHY: emit legacy per-device log.
    return row, mgmt_ip


def _select_wan_port_columns(row_sample: dict) -> list[str]:  # WHY: extract WAN column selection out of caller.
    """Return the list of WAN-port config column names present in a sample row."""
    return [col for col in row_sample.keys() if _is_wan_port_column(col)]  # WHY: pure filter over keys.


def _project_row_to_columns(row: dict, columns: list[str]) -> dict:  # WHY: extract per-row projection helper.
    """Return a new dict containing only the requested columns from row, with empty-string fallback."""
    return {col: row.get(col, "") for col in columns}  # WHY: empty string preserves downstream shape.


def _is_wan_port_column(column_name: str) -> bool:  # WHY: pure predicate for WAN port-config columns.
    """Return True if the column name matches WAN port config but not VPN-path noise."""
    if not WAN_PORT_COLUMN_PATTERN.match(column_name):  # WHY: reject columns outside ge-0/0/N port config.
        return False
    return "_vpn_paths_" not in column_name  # WHY: exclude nested VPN-path columns from the projection.


def _row_has_port_data(row: dict, port_columns: list[str]) -> bool:  # WHY: filter rows without port-config data.
    """Return True if any port column in the row has a non-empty value."""
    return any(row.get(col) not in EMPTY_CELL_MARKERS for col in port_columns)  # WHY: skip empty rows.


def _write_empty_filtered_port_marker() -> None:  # WHY: preserve legacy empty-file fallback behaviour.
    """Write the legacy empty-marker file when no rows matched the port filter."""
    logging.warning(" No rows matched the port config filter. FilteredGatewayPortConfigs.csv will be empty.")
    filtered_csv_path = FilePathUtils.get_csv_path("FilteredGatewayPortConfigs.csv")  # WHY: resolve target path.
    logging.info("Writing empty marker file to %s", filtered_csv_path)  # WHY: log before disk write.
    with open(filtered_csv_path, "w", newline="", encoding="utf-8") as csvfile:  # WHY: newline='' per csv docs.
        csvfile.write("No matching data found.\n")  # WHY: preserve legacy empty marker content.


def _load_gateways_from_inventory_csv() -> list[dict]:  # WHY: isolate cached OrgInventory read.
    """Read the cached org inventory CSV and return only gateway rows with site+id populated."""
    inventory_path = FilePathUtils.get_csv_path("OrgInventory.csv")  # WHY: resolve inventory cache path.
    with open(inventory_path, encoding="utf-8") as csvfile:  # WHY: UTF-8 by convention for CSV cache.
        reader = csv.DictReader(csvfile)  # WHY: read as dict rows for field access.
        return [row for row in reader if row.get("type") == "gateway" and row.get("site_id") and row.get("id")]


def _load_site_name_lookup_from_csv() -> dict[str, str]:  # WHY: isolate cached SiteList read.
    """Read the cached SiteList CSV and build an id->name lookup preserving fallback text."""
    site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # WHY: resolve SiteList cache path.
    with open(site_list_path, encoding="utf-8") as csvfile:  # WHY: UTF-8 by convention for CSV cache.
        reader = csv.DictReader(csvfile)  # WHY: dict rows for id/name access.
        return {row.get("id"): row.get("name", UNKNOWN_SITE) for row in reader}  # WHY: preserve legacy fallback.


def _project_gateway_devices(  # WHY: turn raw gateway rows + site lookup into flat tuples.
    gateways: list[dict],
    site_name_lookup: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    """Project cached gateway inventory rows into (site_id, device_id, device_name, site_name) tuples."""
    return [
        (
            device.get("site_id", ""),  # WHY: empty string preserves downstream tuple shape.
            device.get("id", ""),  # WHY: empty string when device UUID missing.
            device.get("name", ""),  # WHY: empty string when device name missing.
            site_name_lookup.get(device.get("site_id", ""), UNKNOWN_SITE),  # WHY: legacy Unknown Site fallback.
        )
        for device in gateways  # WHY: single pass over cached gateway rows.
    ]


def _fetch_site_name_lookup_from_api(org_id: str) -> dict[str, str]:  # WHY: isolate mistapi paged site fetch.
    """Fetch org site list via API and build an id->name lookup."""
    site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)  # WHY: first page.
    sites = mistapi.get_all(response=site_response, mist_session=apisession)  # WHY: exhaust remaining pages.
    return {site["id"]: site.get("name", UNKNOWN_SITE) for site in sites}  # WHY: preserve legacy fallback text.


def _project_api_gateway_devices(  # WHY: isolate filter+projection for API-sourced inventory.
    devices: list[dict],
    site_name_lookup: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    """Project API inventory rows into gateway tuples, applying the same filter as the cache path."""
    return [
        (
            device.get("site_id", ""),  # WHY: empty string preserves downstream tuple shape.
            device.get("id", ""),  # WHY: empty string when device UUID missing.
            device.get("name", ""),  # WHY: empty string when device name missing.
            site_name_lookup.get(device.get("site_id", ""), UNKNOWN_SITE),  # WHY: legacy Unknown Site fallback.
        )
        for device in devices  # WHY: iterate every inventory row once.
        if device.get("type") == "gateway" and device.get("site_id") and device.get("id")  # WHY: gateway filter.
    ]


class GatewayExportUtils:  # WHY: centralised gateway export utility class extracted from MistHelper.py.
    """Centralized gateway export utilities extracted from MistHelper.py."""

    @staticmethod
    def _with_site_info() -> None:  # WHY: single-line delegate exposed for compatibility.
        """Export gateways with associated site data."""
        OrgInventoryExporter.gateways_with_site_info()  # WHY: forward to the org inventory exporter facade.

    @staticmethod
    def _load_management_ip_csv_inputs() -> tuple[list[dict], list[dict], list[dict], list[dict]] | None:
        """Load the four CSV inputs required for gateway management-IP correlation."""
        logging.info("Loading CSV inputs for gateway management IP correlation")  # WHY: log before disk reads.
        try:
            loaded = tuple(_read_csv_rows(name) for name in MANAGEMENT_IP_INPUT_CSVS)  # WHY: table-driven reads.
        except FileNotFoundError as exception:
            logging.error("Required CSV file not found: %s", exception)  # WHY: preserve legacy error log.
            print(f"! Error: Required CSV file not found: {exception}")  # WHY: preserve legacy operator message.
            return None
        sites, templates, gateway_devices, gateway_configs = loaded  # WHY: unpack into named locals.
        logging.debug(
            "Loaded sites=%d templates=%d devices=%d configs=%d",
            len(sites),
            len(templates),
            len(gateway_devices),
            len(gateway_configs),
        )  # WHY: log per-source row counts.
        return sites, templates, gateway_devices, gateway_configs

    @staticmethod
    def _build_management_ip_rows(
        gateway_devices: list[dict],
        site_lookup: dict,
        template_lookup: dict,
        mgmt_ip_lookup: dict,
    ) -> tuple[list[dict], int, int]:
        """Build per-device management-IP rows; return (rows, processed_count, with_mgmt_ip_count)."""
        lookups = {"site": site_lookup, "template": template_lookup, "mgmt_ip": mgmt_ip_lookup}  # WHY: bundle.
        results: list[dict] = []  # WHY: per-device records for export.
        with_mgmt_ip = 0  # WHY: track devices with a usable management IP.
        for device in gateway_devices:  # WHY: single pass over cached device rows.
            row, mgmt_ip = _build_management_ip_row(device, lookups)  # WHY: build row + surface mgmt IP.
            results.append(row)  # WHY: accumulate the per-device projection.
            if mgmt_ip:  # WHY: only count devices with a non-empty management IP.
                with_mgmt_ip += 1
        return results, len(results), with_mgmt_ip  # WHY: len(results) == devices processed.

    @staticmethod
    def _prime_management_ip_caches(fast: bool) -> None:  # WHY: isolate the 4 cache generation calls.
        """Ensure the 4 CSV caches consumed by management_ips are up to date."""
        print("  1. Ensuring site list with template mappings is current...")  # WHY: preserve legacy operator log.
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # WHY: refresh site cache.
        print("  2. Ensuring gateway templates are current...")  # WHY: preserve legacy operator log.
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtils.templates)
        print("  3. Ensuring gateway device data with connection status is current...")  # WHY: legacy log.
        CacheUtils.check_and_generate_csv("GatewaysWithSiteInfo.csv", OrgInventoryExporter.gateways_with_site_info)
        print("  4. Ensuring gateway configurations with management IPs are current...")  # WHY: legacy log.
        CacheUtils.check_and_generate_csv(
            "AllSiteGatewayConfigs.csv",
            lambda: GatewayExportUtils.device_configs(fast=fast),  # WHY: fast flag threaded into config generator.
        )

    @staticmethod
    def _build_management_ip_lookups(  # WHY: centralise the three lookup-map constructions.
        sites: list[dict],
        templates: list[dict],
        gateway_configs: list[dict],
    ) -> tuple[dict, dict, dict]:
        """Build (site_lookup, template_lookup, mgmt_ip_lookup) from the raw CSV inputs."""
        site_lookup = {site.get("id"): site for site in sites}  # WHY: index sites by id for O(1) lookup.
        template_lookup = {
            template.get("id"): template.get("name", "Unknown Template") for template in templates
        }  # WHY: index template id -> name for downstream projection.
        mgmt_ip_lookup = {
            config.get("name"): config.get("gateway_mgmt_overlay_ip_ip", "") for config in gateway_configs
        }  # WHY: index gateway name -> mgmt overlay IP.
        return site_lookup, template_lookup, mgmt_ip_lookup

    @staticmethod
    def _finalise_management_ip_output(results: list[dict]) -> None:  # WHY: sort + rendering isolated.
        """Sort rows and write the GatewayManagementIPs.csv export."""
        results.sort(key=lambda row: (row["gateway_template"], row["gateway_name"]))  # WHY: stable output order.
        final_results = [
            {
                "Gateway Name": row["gateway_name"],
                "Gateway Template": row["gateway_template"],
                "Management IP": row["management_ip"],
                "Online Status": row["status"],
                "Site Name": row["site_name"],
            }
            for row in results  # WHY: rename internal keys to legacy CSV column headers.
        ]
        DataExporter.write_with_format_selection(final_results, "GatewayManagementIPs.csv")  # WHY: persist.

    @staticmethod
    def _emit_management_ip_summary(gateways_processed: int, gateways_with_mgmt_ip: int) -> None:
        """Emit the completion banner + audit log preserving legacy phrasing."""
        print("! Gateway management IP export completed:")  # WHY: legacy completion banner headline.
        print(f"  - Total gateways processed: {gateways_processed}")  # WHY: legacy phrasing preserved.
        print(f"  - Gateways with management IPs: {gateways_with_mgmt_ip}")  # WHY: legacy phrasing preserved.
        print(f"  - Gateways without management IPs: {gateways_processed - gateways_with_mgmt_ip}")
        print("  - Output CSV: GatewayManagementIPs.csv")  # WHY: legacy phrasing preserved.
        logging.info(
            "Gateway management IP export completed. %d gateways processed, %d with management IPs.",
            gateways_processed,
            gateways_with_mgmt_ip,
        )  # WHY: audit log with per-count summary.

    @staticmethod
    def management_ips(fast: bool = False) -> None:
        """Export gateway management overlay IPs correlated with templates and site status."""
        logging.info("Menu #31: Starting gateway management IPs export")  # WHY: audit log for menu entry.
        print("Gateway Management IP Export:")  # WHY: user-facing banner.
        print("Collecting data from inventory, templates, and configurations...")  # WHY: legacy operator log.
        ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org id via standard pathway.
        GatewayExportUtils._prime_management_ip_caches(fast)  # WHY: ensure all 4 CSV inputs are current.
        print("  5. Processing and correlating data...")  # WHY: legacy operator log for step 5.
        loaded = GatewayExportUtils._load_management_ip_csv_inputs()  # WHY: read the four CSV inputs.
        if loaded is None:  # WHY: required CSV missing — error already printed/logged.
            return
        sites, templates, gateway_devices, gateway_configs = loaded  # WHY: unpack inputs for correlation.
        site_lookup, template_lookup, mgmt_ip_lookup = GatewayExportUtils._build_management_ip_lookups(
            sites, templates, gateway_configs
        )  # WHY: precompute lookup maps.
        results, processed, with_mgmt_ip = GatewayExportUtils._build_management_ip_rows(
            gateway_devices, site_lookup, template_lookup, mgmt_ip_lookup
        )  # WHY: correlate per-device rows.
        GatewayExportUtils._finalise_management_ip_output(results)  # WHY: sort + write CSV.
        GatewayExportUtils._emit_management_ip_summary(processed, with_mgmt_ip)  # WHY: completion banner.

    @staticmethod
    def _build_filtered_port_rows(sanitized: list) -> list:  # WHY: extract WAN-port projection from full set.
        """Return rows containing only base + WAN port columns where at least one port is non-empty."""
        base_columns = ["mac", "name"]  # WHY: preserve legacy identifier columns.
        port_columns = _select_wan_port_columns(sanitized[0])  # WHY: derive WAN column list from sample row.
        columns_to_keep = base_columns + port_columns  # WHY: build final column projection list.
        logging.debug("Built port-column projection: %d port columns", len(port_columns))  # WHY: log count.
        return [
            _project_row_to_columns(row, columns_to_keep)  # WHY: project each row via reusable helper.
            for row in sanitized  # WHY: iterate full sanitized set.
            if _row_has_port_data(row, port_columns)  # WHY: drop rows lacking any port-config data.
        ]

    @staticmethod
    def _save_filtered_port_configs(filtered_rows: list, debug: bool) -> None:
        """Write FilteredGatewayPortConfigs.csv preserving legacy empty-file fallback."""
        if not filtered_rows:  # WHY: empty projection triggers legacy empty-marker file.
            _write_empty_filtered_port_marker()  # WHY: delegate legacy fallback write.
            return
        if debug:  # WHY: only emit sample row when operator asked for debug output.
            logging.debug("Sample filtered row: %s", filtered_rows[0])
        logging.info("Saving filtered gateway port configs to FilteredGatewayPortConfigs.csv")  # WHY: pre-log.
        DataExporter.write_with_format_selection(
            filtered_rows, "FilteredGatewayPortConfigs.csv"
        )  # WHY: persist filtered set through configured exporter.
        logging.info(" Filtered gateway port configs saved to FilteredGatewayPortConfigs.csv")  # WHY: post-log.

    @staticmethod
    def device_configs(debug: bool = False, fast: bool = False) -> None:
        """Fetch and export all gateway device configuration details."""
        logging.info("Starting export of all gateway device configurations...")  # WHY: audit log for entry.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org_id via standard pathway.
        data = APIFetchUtils.gateway_device_configs(apisession, org_id, fast=fast)  # WHY: fetch configs.
        if not data:  # WHY: abort when nothing was returned by the API.
            logging.warning(" No device configs found.")
            return
        flattened = DataProcessingUtils.flatten_nested_fields(data)  # WHY: flatten nested JSON to flat cells.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # WHY: escape multiline cells for CSV.
        logging.info("Saving sanitized gateway configs to AllSiteGatewayConfigs.csv")  # WHY: pre-write log.
        DataExporter.write_with_format_selection(sanitized, "AllSiteGatewayConfigs.csv")  # WHY: persist full.
        logging.info(" Device configs saved to AllSiteGatewayConfigs.csv")  # WHY: post-write log.
        filtered_rows = GatewayExportUtils._build_filtered_port_rows(sanitized)  # WHY: build port-config subset.
        GatewayExportUtils._save_filtered_port_configs(filtered_rows, debug)  # WHY: persist filtered subset.

    @staticmethod
    def templates() -> None:
        """Export gateway templates for the selected organization."""
        print("Gateway Templates:")  # WHY: user-facing banner.
        logging.info("Exporting gateway templates for the organization...")  # WHY: audit log for entry.
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org_id via standard path.
        response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(apisession, current_org_id)
        templates = getattr(response, "data", [])  # WHY: defensive — response may lack .data attribute.
        if not templates:  # WHY: nothing to export — emit diagnostics and return.
            logging.warning("No gateway templates found for this organization.")
            print("No gateway templates found for this organization.")
            return
        templates = DataProcessingUtils.flatten_nested_fields(templates)  # WHY: flatten nested JSON to cells.
        templates = DataProcessingUtils.escape_multiline(templates)  # WHY: escape multiline cells for CSV.
        DataExporter.write_with_format_selection(templates, "OrgGatewayTemplates.csv")  # WHY: persist output.
        print(f"! {len(templates)} gateway templates exported to OrgGatewayTemplates.csv")  # WHY: banner.
        logging.info(" Gateway templates exported to OrgGatewayTemplates.csv")  # WHY: audit log for exit.

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:
        """Run the WAN override compliance report via the WanOverrideWalker orchestrator."""
        logging.info("Starting WAN override compliance report (fast=%s)", fast)  # WHY: before-action log.
        WanOverrideWalker.walk(fast=fast)  # WHY: orchestrate cache/classify/fetch/report end-to-end.
        logging.debug("WAN override compliance report finished (fast=%s)", fast)  # WHY: after-action log.

    @staticmethod
    def _get_devices_with_sites(org_id: str, fast: bool = False) -> list[tuple[str, str, str, str]]:
        """Fetch all gateway devices with site metadata for downstream gateway exports."""
        logging.info("[INFO] Fetching gateway devices with site information...")  # WHY: pre-fetch log.
        if fast:  # WHY: fast mode reads from cached CSVs to avoid API cost.
            return GatewayExportUtils._get_devices_from_cache()
        return GatewayExportUtils._get_devices_from_api(org_id)  # WHY: default path hits API endpoints.

    @staticmethod
    def _get_devices_from_cache() -> list[tuple[str, str, str, str]]:
        """Get gateway devices from cached inventory and site list CSVs."""
        try:
            CacheUtils.check_and_generate_csv("OrgInventory.csv", OrgInventoryExporter.inventory)  # WHY: refresh.
            CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # WHY: refresh site cache.
            gateways = _load_gateways_from_inventory_csv()  # WHY: load gateway rows from inventory CSV.
            site_name_lookup = _load_site_name_lookup_from_csv()  # WHY: build site id->name lookup.
            gateway_devices = _project_gateway_devices(gateways, site_name_lookup)  # WHY: shape output tuples.
            logging.info("! Fast mode: Loaded %s gateway devices from cached data", len(gateway_devices))
            return gateway_devices
        except Exception as exception:  # pylint: disable=broad-exception-caught  # WHY: fall back on any error.
            logging.warning("! Fast mode failed, falling back to API calls: %s", exception)  # WHY: log fallback.
            org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: resolve org id for API fallback path.
            return GatewayExportUtils._get_devices_from_api(org_id)  # WHY: delegate to API path.

    @staticmethod
    def _get_devices_from_api(org_id: str) -> list[tuple[str, str, str, str]]:
        """Get gateway devices from API inventory and site list endpoints."""
        logging.info("[INFO] Fetching org inventory to find gateway devices...")  # WHY: pre-fetch log.
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)  # WHY: paged org inventory fetch.
        logging.info("[INFO] Retrieved %s devices from org inventory.", len(devices))  # WHY: post-fetch log.
        site_name_lookup = _fetch_site_name_lookup_from_api(org_id)  # WHY: build site id->name lookup via API.
        gateway_devices = _project_api_gateway_devices(devices, site_name_lookup)  # WHY: filter+shape tuples.
        logging.info("[INFO] Found %s gateway devices across the organization.", len(gateway_devices))
        return gateway_devices

    @staticmethod
    def _get_site_ids_with_devices(org_id: str) -> list[str]:
        """Get site IDs that currently contain at least one gateway device."""
        logging.info("[INFO] Fetching org inventory to find sites with gateways...")  # WHY: pre-fetch log.
        devices = APICoreFetchUtils.all_inventory_with_limit(org_id)  # WHY: paged org inventory fetch.
        logging.info("[INFO] Retrieved %s devices from org inventory.", len(devices))  # WHY: post-fetch log.
        gateway_sites = {
            device["site_id"]
            for device in devices
            if device.get("type") == "gateway" and device.get("site_id") and str(device.get("site_id")).strip()
        }  # WHY: dedupe site ids for gateway-type rows only.
        logging.info("[INFO] Found %s sites with at least one gateway.", len(gateway_sites))  # WHY: post-log.
        return list(gateway_sites)  # WHY: caller expects a list rather than a set.

    @staticmethod
    def wan2_variable_migration(fast: bool = False, dry_run: bool = False) -> None:
        """Update gateway template WAN2 variable through extracted migrator."""
        from src.gateway.wan2_variable import GatewayWan2VariableMigrator, Wan2VariableDeps  # noqa: PLC0415

        deps = Wan2VariableDeps(  # WHY: build immutable dep bundle for the migrator.
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
        migrator = GatewayWan2VariableMigrator(deps)  # WHY: instantiate migrator with the bundled deps.
        migrator.execute(fast=fast, dry_run=dry_run)  # WHY: run the migration pipeline.
