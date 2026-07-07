"""Runtime dependency container for the WAN override analysis collaborators."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from dataclasses import dataclass  # WHY: frozen slotted bundle shrinks wiring signature to one param.
from typing import Any, Final  # Typing helpers for module-level dependency holders

_LOG_CONFIGURED: Final[str] = "Gateway override dependencies configured"  # WHY: single-source log template.

apisession: Any = None  # Mist API session; set by configure_gateway_override_dependencies
mistapi: Any = None  # mistapi SDK module; set by configure_gateway_override_dependencies
CacheUtils: Any = None  # CSV cache helper; set by configure_gateway_override_dependencies
FilePathUtils: Any = None  # Output path helper; set by configure_gateway_override_dependencies
DataExporter: Any = None  # Multi-backend writer; set by configure_gateway_override_dependencies
OrgSiteExporter: Any = None  # Site list exporter; set by configure_gateway_override_dependencies
MIST_WAN_TARGET_PORTS: list[str] = []  # Operator-configured WAN ports list from .env
# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute.
# See specs/1012-misthelper-refactor-hot-functions/spec.md.
execute_fn: Any = (
    None  # Pool-managed parallel runner (1012 SC-003; renamed from execute_with_connection_pool_management)
)
GatewayExportUtilsRef: Any = None  # Gateway export helpers ref (device_configs/templates funcs)


@dataclass(frozen=True, slots=True)  # WHY: immutable bundle collapses 9 wiring args (STRUCT-PARAMS).
class GatewayOverrideDependencies:
    """Immutable bundle carrying WAN override analysis dependencies into configure()."""

    apisession_dependency: Any  # Live Mist API session used by downstream override modules
    mistapi_dependency: Any  # mistapi SDK reference required for API calls
    cache_utils: Any  # CSV cache helper class exposing check_and_generate_csv
    file_path_utils: Any  # FilePathUtils class exposing get_csv_path
    data_exporter: Any  # DataExporter class exposing write_with_format_selection
    org_site_exporter: Any  # OrgSiteExporter class exposing sites_list_api
    mist_wan_target_ports: list[str]  # Operator-configured WAN target ports list from .env
    execute_fn: Any  # ConnectionPoolExecutor.execute callable (1012 SC-003; renamed from connection_pool_fn)
    gateway_export_utils_ref: Any  # GatewayExportUtils reference (device_configs / templates)


def configure_gateway_override_dependencies(deps: GatewayOverrideDependencies) -> None:
    """Configure runtime dependencies for the override analysis collaborators."""
    global apisession, mistapi, CacheUtils, FilePathUtils, DataExporter  # WHY: module-level DI slots.
    global OrgSiteExporter, MIST_WAN_TARGET_PORTS  # WHY: module-level DI slots.
    global execute_fn, GatewayExportUtilsRef  # WHY: module-level DI slots.
    apisession = deps.apisession_dependency  # Real Mist session for downstream API calls
    mistapi = deps.mistapi_dependency  # Actual mistapi SDK module
    CacheUtils = deps.cache_utils  # CSV cache helper class
    FilePathUtils = deps.file_path_utils  # Output path helper class
    DataExporter = deps.data_exporter  # Multi-backend data exporter
    OrgSiteExporter = deps.org_site_exporter  # Site list exporter helper
    MIST_WAN_TARGET_PORTS = deps.mist_wan_target_ports  # Operator-configured target ports
    execute_fn = deps.execute_fn  # Pool-managed parallel runner (renamed from connection_pool_fn per 1012 SC-003)
    GatewayExportUtilsRef = deps.gateway_export_utils_ref  # Gateway export helpers reference
    logging.debug(_LOG_CONFIGURED)  # Confirm wiring for operator logs
