"""Gateway override analyzer façade — delegates to src/gateway/overrides/ collaborators."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from typing import Any  # Generic typing for the module-level dependency holders

apisession: Any = None  # Mist API session; set by configure_gateway_override_analyzer_dependencies
mistapi: Any = None  # mistapi SDK module; set by configure_gateway_override_analyzer_dependencies
CacheUtils: Any = None  # CSV cache helper; set by configure_gateway_override_analyzer_dependencies
FilePathUtils: Any = None  # Output path helper; set by configure_gateway_override_analyzer_dependencies
DataExporter: Any = None  # Multi-backend writer; set by configure_gateway_override_analyzer_dependencies
OrgSiteExporter: Any = None  # Site list exporter; set by configure_gateway_override_analyzer_dependencies
MIST_WAN_TARGET_PORTS: list[str] = []  # Operator-configured WAN ports list from .env
execute_with_connection_pool_management: Any = None  # Pool-managed parallel runner; set by configure_*
GatewayExportUtilsRef: Any = None  # Gateway export helpers ref; set by configure_*


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
    global apisession  # Module-level holder consumed by the overrides submodule via _deps.apisession
    global mistapi  # Module-level holder consumed by the overrides submodule via _deps.mistapi
    global CacheUtils  # Module-level holder consumed by the overrides submodule via _deps.CacheUtils
    global FilePathUtils  # Module-level holder consumed by the overrides submodule via _deps.FilePathUtils
    global DataExporter  # Module-level holder consumed by the overrides submodule via _deps.DataExporter
    global OrgSiteExporter  # Module-level holder consumed by the overrides submodule via _deps.OrgSiteExporter
    global MIST_WAN_TARGET_PORTS  # Module-level holder consumed via _deps.MIST_WAN_TARGET_PORTS
    global execute_with_connection_pool_management  # Module-level holder consumed via _deps.execute_*
    global GatewayExportUtilsRef  # Module-level holder consumed via _deps.GatewayExportUtilsRef

    apisession = apisession_dependency  # Replace placeholder with real Mist session for downstream API calls
    mistapi = mistapi_dependency  # Replace placeholder with the actual mistapi SDK module
    CacheUtils = cache_utils  # Replace placeholder with the project's CSV cache helper class
    FilePathUtils = file_path_utils  # Replace placeholder with the project's path helper class
    DataExporter = data_exporter  # Replace placeholder with the multi-backend data exporter
    OrgSiteExporter = org_site_exporter  # Replace placeholder with the site list exporter helper
    MIST_WAN_TARGET_PORTS = mist_wan_target_ports  # Replace placeholder with operator's configured port list
    execute_with_connection_pool_management = connection_pool_fn  # Pool-managed parallel runner from orchestrator
    GatewayExportUtilsRef = gateway_export_utils_ref  # Gateway export helpers (device_configs/templates funcs)
    logging.debug("GatewayOverrideAnalyzer dependencies configured")  # Confirm wiring for operator-visible logs


class GatewayOverrideAnalyzer:
    """Façade — delegates to the WanOverrideWalker collaborator in src/gateway/overrides/."""

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:
        """Generate report of gateways with template-overridden WAN ports (façade)."""
        from .overrides import WanOverrideWalker  # Lazy import avoids any circular dependency at module load

        WanOverrideWalker.walk(fast=fast)  # Hand off the full pipeline to the extracted orchestrator
