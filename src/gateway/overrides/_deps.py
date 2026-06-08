"""Runtime dependency container for the WAN override analysis collaborators."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from typing import Any  # Generic typing for the module-level dependency holders

apisession: Any = None  # Mist API session; set by configure_gateway_override_dependencies
mistapi: Any = None  # mistapi SDK module; set by configure_gateway_override_dependencies
CacheUtils: Any = None  # CSV cache helper; set by configure_gateway_override_dependencies
FilePathUtils: Any = None  # Output path helper; set by configure_gateway_override_dependencies
DataExporter: Any = None  # Multi-backend writer; set by configure_gateway_override_dependencies
OrgSiteExporter: Any = None  # Site list exporter; set by configure_gateway_override_dependencies
MIST_WAN_TARGET_PORTS: list[str] = []  # Operator-configured WAN ports list from .env
execute_with_connection_pool_management: Any = None  # Pool-managed parallel runner
GatewayExportUtilsRef: Any = None  # Gateway export helpers ref (device_configs/templates funcs)


def configure_gateway_override_dependencies(
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
    """Configure runtime dependencies for the override analysis collaborators."""
    global apisession  # Module-level holder consumed by submodules via _deps.apisession
    global mistapi  # Module-level holder consumed by submodules via _deps.mistapi
    global CacheUtils  # Module-level holder consumed by submodules via _deps.CacheUtils
    global FilePathUtils  # Module-level holder consumed by submodules via _deps.FilePathUtils
    global DataExporter  # Module-level holder consumed by submodules via _deps.DataExporter
    global OrgSiteExporter  # Module-level holder consumed by submodules via _deps.OrgSiteExporter
    global MIST_WAN_TARGET_PORTS  # Module-level holder consumed via _deps.MIST_WAN_TARGET_PORTS
    global execute_with_connection_pool_management  # Module-level holder for pool-managed runner
    global GatewayExportUtilsRef  # Module-level holder for gateway export helpers reference

    apisession = apisession_dependency  # Real Mist session for downstream API calls
    mistapi = mistapi_dependency  # Actual mistapi SDK module
    CacheUtils = cache_utils  # CSV cache helper class
    FilePathUtils = file_path_utils  # Output path helper class
    DataExporter = data_exporter  # Multi-backend data exporter
    OrgSiteExporter = org_site_exporter  # Site list exporter helper
    MIST_WAN_TARGET_PORTS = mist_wan_target_ports  # Operator-configured target ports
    execute_with_connection_pool_management = connection_pool_fn  # Pool-managed parallel runner
    GatewayExportUtilsRef = gateway_export_utils_ref  # Gateway export helpers reference
    logging.debug("Gateway override dependencies configured")  # Confirm wiring for operator logs
