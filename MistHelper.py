#!/usr/bin/env python3
"""
MistHelper - Comprehensive Juniper Mist API Data Export Tool
A powerful utility for extracting and analyzing data from Juniper Mist cloud environments.
"""

# ============================================================================
# PYTHON VERSION CHECK - MUST BE FIRST (before any other imports)
# ============================================================================
import sys

# Enforce Python 3.13+ requirement
MINIMUM_PYTHON_VERSION = (3, 13)  # Define minimum required Python version tuple for compatibility checks
if sys.version_info < MINIMUM_PYTHON_VERSION:  # Exit early if Python is too old to prevent cryptic errors later
    # Format current Python version for display
    version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    required_str = (
        f"{MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]}"  # Format minimum required version for display
    )
    warning_msg = (  # Build user-friendly error message with actionable guidance
        f"WARNING: Python {version_str} detected. MistHelper requires Python {required_str} or newer.\n"
        f"Some features may not work correctly. Please upgrade Python to {required_str}+.\n"
        f"Download from: https://www.python.org/downloads/"
    )
    print(f"\n{'=' * 70}", file=sys.stderr)  # Print separator line to stderr (visible even if stdout redirected)
    print(warning_msg, file=sys.stderr)  # Print version warning to stderr for visibility during startup
    print(f"{'=' * 70}\n", file=sys.stderr)  # Print closing separator to stderr
    # Log will be configured later, but we can't use logging yet
    # The warning is printed to stderr so it's visible regardless

# ============================================================================
# GLOBAL DEPENDENCY MANAGEMENT AND IMPORT SYSTEM
# ============================================================================
import warnings  # Import warnings module to suppress harmless SyntaxWarnings from third-party libraries

warnings.filterwarnings(
    "ignore", message="invalid escape sequence", category=SyntaxWarning
)  # Suppress false SyntaxWarnings about escape sequences in regex patterns from mistapi library

import argparse  # Import argparse for command-line argument parsing (--menu, --test, --fast flags)
import logging  # Import logging for structured logging to script.log and console
import os  # Import os for file path operations, environment variables, and data/ directory setup
import re  # Import re for regex pattern matching in data parsing (SSIDs, descriptions, etc.)
import subprocess  # nosec B404  # Import subprocess for executing external commands (SSH, JSON parsing) with security review
import time  # Import time for rate limiting, delays, and performance monitoring
import traceback  # Import traceback for detailed exception context in error logs
from datetime import datetime  # Import datetime for timestamping logs and events
from typing import TYPE_CHECKING, Any  # Import type hints for static analysis without runtime overhead

# Type stubs for dynamically imported modules
# These allow type checking while the actual imports happen at runtime via GlobalImportManager
# Pylance uses these unconditionally; runtime try/except blocks below handle actual loading.
if TYPE_CHECKING:  # These imports only used by static type checkers (Pylance, mypy), not at runtime
    from collections.abc import Callable  # Callable protocol for typed optional-import fallbacks
    from types import ModuleType  # ModuleType annotation for optional-module fallback typing

    import requests  # Type stub for requests (HTTP library used by mistapi)
    from prettytable import PrettyTable  # Type stub for prettytable (ASCII table formatting)

    import websocket  # Type stub for websocket (WebSocket client for device diagnostics)

# ============================================================================
# POLYGLOT DATABASE LAYER (OPTIONAL)
# ============================================================================
# Conditional import for ArangoDB + Redis TimeSeries backends.
# Falls back gracefully in standalone mode (no python-arango/redis installed).
try:  # Attempt to import polyglot database layer for ArangoDB/Redis export backends
    from src.db import DatabaseConfig as _DatabaseConfigImpl
    from src.db import configure_db_logging as _configure_db_logging_impl
    from src.db.router import DatabaseRouter as _DatabaseRouterImpl

    DatabaseConfig: type[_DatabaseConfigImpl] | None = _DatabaseConfigImpl  # Class reference for DB config construction
    configure_db_logging: "Callable[[], None] | None" = _configure_db_logging_impl  # Logging setup callable
    DatabaseRouter: type[_DatabaseRouterImpl] | None = _DatabaseRouterImpl  # Class reference for DB router construction
    DB_LAYER_AVAILABLE = True  # Set flag indicating database backends are available for export operations
except ImportError:  # If database dependencies (python-arango, redis) not installed, gracefully disable
    DatabaseConfig = None  # None lets runtime guards detect DB-layer absence
    configure_db_logging = None  # None lets runtime guards detect DB-layer absence
    DatabaseRouter = None  # None lets runtime guards detect DB-layer absence
    DB_LAYER_AVAILABLE = False  # Set flag to disable database output formats (CSV/SQLite only)

# Explicit public API surface (issue #895).
# Every name below is re-exported from a src.* submodule for external
# consumers. Adding a name here MUST accompany a corresponding update to
# specs/1016-misthelper-suppression-cleanup/contracts/public_api_snapshot.txt.
__all__ = [
    "APICoreFetchUtils",
    "APIDataFetcher",
    "APIFetchUtils",
    "APITenantFetchUtils",
    "API_REQUEST_MAX_RETRIES",
    "API_REQUEST_RETRY_DELAY",
    "API_REQUEST_TIMEOUT",
    "ARPCommandManager",
    "AUTO_UPGRADE_DEPENDENCIES",
    "AUTO_UPGRADE_UV",
    "AddressAuditEngine",
    "AnomalyMetricsDiscovery",
    "Any",
    "ArpDeviceExecutor",
    "AuditAnalysisOps",
    "BulkRadiusWLANConfigManager",
    "CLIShellManager",
    "CSV_FRESHNESS_MINUTES",
    "CacheUtils",
    "ConfigUtils",
    "ConnectionPoolExecutor",
    "ConstDefinitionsExporter",
    "DATABASE_PATH",
    "DB_LAYER_AVAILABLE",
    "DEFAULT_API_PAGE_LIMIT",
    "DOTENV_AVAILABLE",
    "DataCollectionManager",
    "DataDirectoryChecker",
    "DataExporter",
    "DataProcessingUtils",
    "DatabaseConfig",
    "DatabaseRouter",
    "DatabaseSchemaUtils",
    "DependencyCheckOrchestrator",
    "DeviceConfigTemplateClonerManager",
    "DeviceDataFetcher",
    "DeviceEvents52wExporter",
    "DeviceMetricOperation",
    "DeviceRebootManager",
    "DeviceUtils",
    "DisplayUtils",
    "E911BSSIDReportGenerator",
    "EndpointConfig",
    "EnhancedSSHRunner",
    "EnvironmentUtils",
    "ExtractedMarvisTroubleshootUtils",
    "ExtractedSiteAnalyticsConfigurator",
    "ExtractedSiteInventoryHealthAnalyzer",
    "FAST_MODE_ENABLED",
    "FAST_MODE_FALLBACK_THREADS",
    "FAST_MODE_MAX_RETRIES",
    "FAST_MODE_RETRY_DELAY",
    "FAST_MODE_RETRY_MAX_RETRIES",
    "FAST_MODE_RETRY_THREADS",
    "FastModeBackoffMultiplier",
    "FastModeSequentialMaxRetries",
    "FilePathUtils",
    "FilterOperatorEngine",
    "FirmwareManager",
    "FirmwareManagerConfig",
    "GatewayExportUtils",
    "GatewayHaExporter",
    "GatewayStatsExporter",
    "GatewayTemplateConfigManager",
    "GatewayTestExporter",
    "GlobalImportManager",
    "GlobalWiredClientReportGenerator",
    "IS_TEST_MODE",
    "InputUtils",
    "InsightMetricsUtils",
    "InteractiveDisplayUtils",
    "InteractiveTestRunner",
    "InventoryCSVComparator",
    "IsDebugMode",
    "KeyboardListener",
    "LAST_SELECTED_SITE_ID",
    "LicenseExportUtils",
    "LogSanitizer",
    "LoginOrchestrator",
    "MINIMUM_PYTHON_VERSION",
    "MIST_SITE_EXCLUDE_PREFIX",
    "MSPInventoryExporter",
    "MacTableCommand",
    "MainEntrypoint",
    "MapsManagerLauncher",
    "MarvisDataUtilsFactory",
    "MarvisTroubleshootDeps",
    "MistSessionInitializer",
    "MistSessionInteractiveInitializer",
    "MistWanTargetPorts",
    "MspOrgSelector",
    "OUTPUT_FORMAT",
    "OfflineDeviceReporter",
    "OperationRegistry",
    "OrgAdminExporter",
    "OrgAlarmEventExporter",
    "OrgClientSecurityExporter",
    "OrgConfigExporter",
    "OrgConfigMigrationManager",
    "OrgDataCollector",
    "OrgDeviceInventorySummary",
    "OrgDeviceStatsExporter",
    "OrgExportUtils",
    "OrgInventoryExporter",
    "OrgSiteExporter",
    "OrgTemplateExporter",
    "OrgTicketManager",
    "PROGRESS_EMITTER",
    "PackageImportMapManager",
    "PackageInstaller",
    "PacketCaptureManager",
    "PingDeviceExecutor",
    "PrettyTable",
    "ProgressContext",
    "PromptClientUtils",
    "PromptUtils",
    "RateLimitingUtils",
    "RejectPolicy",
    "RoutingDeps",
    "RoutingUtils",
    "RunInteractiveTestManager",
    "SFPTransceiverDataProcessor",
    "SQLiteDatabaseWriter",
    "SSHClient",
    "SSHRunnerManager",
    "SSHRunnerManagerDeps",
    "SelfExportUtils",
    "SequenceMatcher",
    "ServicePingLauncher",
    "SiteAnalyticsConfiguratorDeps",
    "SiteAnomalyExporter",
    "SiteAutoUpgradeConfigurator",
    "SiteClientExporter",
    "SiteConfigExporter",
    "SiteConfigManager",
    "SiteDeviceExporter",
    "SiteExportUtils",
    "SiteInventoryHealthAnalyzerDeps",
    "SiteMetricOperation",
    "SitesByAPModelExporter",
    "SwitchToInteractiveLoginManager",
    "SystematicTestOption",
    "TUILauncher",
    "TYPE_CHECKING",
    "TelemetryEmitter",
    "TimeUtils",
    "TroubleshootUtils",
    "UPGRADE_CHECK_TIMEOUT",
    "UTC",
    "ValidationUtils",
    "VirtualChassisManager",
    "WAN2MigrationLauncher",
    "WANProbeConfigManager",
    "WANProbeDeviceOverrideManager",
    "WLANRadiusTimerManager",
    "WanHubGroupNumberManager",
    "WanVpnBuilder",
    "WebSocketCmdDeps",
    "WebSocketManager",
    "WebSocketStreamTarget",
    "WiredClientManufacturerReportGenerator",
    "apisession",
    "argparse",
    "concurrent",
    "config",
    "configure_db_logging",
    "configure_gateway_export_utils_dependencies",
    "datetime",
    "detect_msp_privileges",
    "fuzz",
    "import_manager",
    "inspect",
    "load_dotenv",
    "logging",
    "menu_actions",
    "mistapi",
    "msp_privileges",
    "normalize_address_record",
    "np",
    "org_id",
    "os",
    "paramiko",
    "pyte",
    "re",
    "requests",
    "selected_msp",
    "subprocess",
    "sys",
    "threading",
    "time",
    "timezone",
    "tqdm",
    "traceback",
    "tuning_data_file",
    "urllib3",
    "warnings",
    "websocket",
]

from src.analytics.data_collection_manager import (
    DataCollectionManager,  # Cat B (1013 SC-001 position 25) -- re-export for MistHelper.DataCollectionManager callers
)
from src.analytics.insight_metrics_utils import (
    InsightMetricsUtils,
)  # Cat E canonical (1014 P11) -- re-export for MistHelper.InsightMetricsUtils callers
from src.analytics.site_analytics_configurator import (  # Import site analytics configuration tools
    SiteAnalyticsConfigurator as ExtractedSiteAnalyticsConfigurator,  # Rename to avoid naming conflicts
)
from src.analytics.site_analytics_configurator import SiteAnalyticsConfiguratorDeps  # Import dependency injection class
from src.analytics.site_inventory_health_analyzer import (  # Import site inventory health analysis tools
    SiteInventoryHealthAnalyzer as ExtractedSiteInventoryHealthAnalyzer,  # Rename to avoid naming conflicts
)
from src.analytics.site_inventory_health_analyzer import (
    SiteInventoryHealthAnalyzerDeps,
)  # Import dependency injection class
from src.analytics.telemetry_emitter import (
    TelemetryEmitter,  # Cat B (1013 SC-001 position 9) -- re-export for callers at 18629/18632/18711/19062
)
from src.api.api_core_fetch_utils import (
    APICoreFetchUtils,
)  # Cat E canonical (1014 P10) -- re-export for MistHelper.APICoreFetchUtils callers
from src.api.api_data_fetcher import (
    APIDataFetcher,  # Cat B (1013 SC-001 position 21) -- re-export for MistHelper.APIDataFetcher callers
)
from src.api.api_fetch_utils import (
    APIFetchUtils,
)  # Cat E canonical (1014 P8) -- re-export for MistHelper.APIFetchUtils callers
from src.audit.audit_analysis_ops import (
    AuditAnalysisOps,  # Cat B (1013 SC-001 position 12) -- re-export for menu_actions #25/#174 dispatch
)
from src.auth.interactive import (
    LoginOrchestrator,  # Re-exported so extracted refactors can resolve it via MistHelper (SC-023)
    MspOrgSelector,
)  # Duplicate import (re-stated with comment below); kept to preserve module load behavior
from src.bootstrap.dependency_check import (
    DependencyCheckOrchestrator,
)  # Duplicate import; harmless re-import of dependency check orchestrator
from src.bootstrap.package_installer import (
    PackageInstaller,
)  # Duplicate import; harmless re-import of package installer
from src.cache.cache_utils import (
    CacheUtils,
)  # Cat E canonical (1014 P14) -- re-export for MistHelper.CacheUtils callers
from src.capture.packet_capture import (
    PacketCaptureManager,
)  # Import packet capture manager directly under its canonical name (issue #431: alias removed)
from src.config.config_utils import (
    ConfigUtils,  # Cat E canonical (1015 T-12) -- re-export for MistHelper.ConfigUtils callers
)

# BatchWorkerConfig import removed: pool machinery moved to ConnectionPoolExecutor (1012 SC-003)
from src.dataclasses.endpoint_config import (
    EndpointConfig,  # Cat B (1013 SC-001 position 16) -- re-export for MistHelper.EndpointConfig callers
)
from src.dataclasses.progress_event import (
    ProgressContext,  # test access + mh.ProgressContext usage from extracted modules
)
from src.dataclasses.systematic_test_option import (
    SystematicTestOption,
)  # Issue #470: groups menu-option identity to keep _systematic_test_run_option within the 5-Item Rule.
from src.dataclasses.websocket_stream_target import (
    WebSocketStreamTarget,  # Re-export after ARPCommandManager extraction (1013 SC-001 position 42)
)
from src.db.database_schema_utils import (
    DatabaseSchemaUtils,  # Cat B (1013 SC-001 position 38) -- re-export for MistHelper.DatabaseSchemaUtils callers
)
from src.device.arp_command_manager import (
    ARPCommandManager,  # Cat B (1013 SC-001 position 42) -- re-export for MistHelper.ARPCommandManager callers
)
from src.device.device_reboot_manager import (
    DeviceRebootManager,  # Cat B (1013 SC-001 position 41) -- re-export for MistHelper.DeviceRebootManager callers
)
from src.device.device_utils import (
    DeviceUtils,  # Cat B (1013 SC-001 position 6) -- re-export for dynamic _mh.DeviceUtils lookup
)
from src.device.virtual_chassis import (  # Cat E canonical (1015 T-11) -- fold-in of stub facade
    VirtualChassisDependencies as _VirtualChassisDependencies,
)
from src.device.virtual_chassis import (
    VirtualChassisManager,
)
from src.device.virtual_chassis import (
    configure_virtual_chassis_dependencies as _configure_virtual_chassis_dependencies,
)
from src.export.const_definitions_exporter import (
    ConstDefinitionsExporter,  # Cat B (1013 SC-001 position 17) -- re-export
)
from src.export.device_events_52w_exporter import (
    DeviceEvents52wExporter,  # Re-export preserved after OrgAlarmEventExporter extraction (1013 SC-001 position 18)
)
from src.export.gateway_test_exporter import (
    GatewayTestExporter,  # Cat B (1013 SC-001 position 37) -- re-export for MistHelper.GatewayTestExporter callers
)
from src.export.license_export_utils import (
    LicenseExportUtils,  # Cat B (1013 SC-001 position 24) -- re-export for MistHelper.LicenseExportUtils callers
)
from src.export.msp_inventory_exporter import (
    MSPInventoryExporter,  # Cat B (1013 SC-001 position 8) -- re-export for menu tuple + static call rewire
)
from src.export.org_admin_exporter import (
    OrgAdminExporter,  # Cat B (1013 SC-001 position 20) -- re-export for MistHelper.OrgAdminExporter callers
)
from src.export.org_alarm_event_exporter import (
    OrgAlarmEventExporter,  # Cat B (1013 SC-001 position 18) -- re-export for MistHelper.OrgAlarmEventExporter callers
)
from src.export.org_client_security_exporter import (
    OrgClientSecurityExporter,  # Cat B (1013 SC-001 position 32) -- re-export
)
from src.export.org_config_exporter import (
    OrgConfigExporter,  # Cat B (1013 SC-001 position 31) -- re-export for MistHelper.OrgConfigExporter callers
)
from src.export.org_device_stats_exporter import (
    OrgDeviceStatsExporter,  # Cat B (1013 SC-001 position 45) -- re-export
)
from src.export.org_export_utils import (
    OrgExportUtils,  # Cat B (1013 SC-001 position 47) -- re-export for MistHelper.OrgExportUtils callers
)
from src.export.org_inventory_exporter import (
    OrgInventoryExporter,  # Cat E canonical (1015 T-06) -- re-export for MistHelper.OrgInventoryExporter callers
)
from src.export.org_site_exporter import (
    OrgSiteExporter,  # Cat E canonical (1014 P9) -- re-export for MistHelper.OrgSiteExporter callers
)
from src.export.org_template_exporter import (
    OrgTemplateExporter,  # Cat B (1013 SC-001 position 22) -- re-export for MistHelper.OrgTemplateExporter callers
)
from src.export.self_export_utils import (
    SelfExportUtils,  # Cat B (1013 SC-001 position 7) -- re-export for menu tuple at MistHelper:18167
)
from src.export.site_anomaly_exporter import (
    SiteAnomalyExporter,  # Cat B (1013 SC-001 position 43) -- re-export for MistHelper.SiteAnomalyExporter callers
)
from src.export.site_client_exporter import (
    SiteClientExporter,  # Cat B (1013 SC-001 position 14) -- re-export for MistHelper.SiteClientExporter callers
)
from src.export.site_config_exporter import (
    SiteConfigExporter,  # Cat B (1013 SC-001 position 19) -- re-export for MistHelper.SiteConfigExporter callers
)
from src.export.site_device_exporter import (
    SiteDeviceExporter,  # Cat B (1013 SC-001 position 34) -- re-export for MistHelper.SiteDeviceExporter callers
)
from src.export.site_export_utils import (  # Cat A canonical (1014 P16)
    SiteExportUtils,
)
from src.export.site_insights.device_metric_operation import (
    DeviceMetricOperation,
)  # Decomposed Menu 76 entry point
from src.export.site_insights.site_metric_operation import (
    SiteMetricOperation,
)  # Decomposed Menu 74 entry point
from src.export.sites_by_ap_model_exporter import (
    SitesByAPModelExporter,  # Cat B (1013 SC-001 position 28) -- re-export
)
from src.firmware.firmware_manager import (  # Cat A canonical (1013 SC-002)
    FirmwareManager,
    FirmwareManagerConfig,
)
from src.firmware.org_ap_upgrader import (  # Cat A canonical (1014 P7)
    OrgLevelAPFirmwareUpgrader as _OrgLevelAPFirmwareUpgrader,
)
from src.firmware.site_auto_upgrade import (  # Cat A canonical (1014 P2)
    SiteAutoUpgradeConfigurator,
)
from src.gateway.gateway_export_utils import (  # Cat A canonical (1014 SC-001 position 13)
    GatewayExportUtils,  # re-export for MistHelper.GatewayExportUtils callers
    configure_gateway_export_utils_dependencies,
)
from src.gateway.gateway_ha_exporter import (
    GatewayHaExporter,  # Cat B (1013 SC-001 position 23) -- re-export for MistHelper.GatewayHaExporter callers
)
from src.gateway.gateway_stats_exporter import (
    GatewayStatsExporter,  # Cat A (1014 SC-001 position 12) -- re-export for MistHelper.GatewayStatsExporter callers
)
from src.gateway.template_config import GatewayTemplateConfigManager  # Cat A canonical (1013 SC-001)
from src.input.prompt_client_utils import (
    PromptClientUtils,  # Cat B (1013 SC-001 position 35) -- re-export for MistHelper.PromptClientUtils callers
)
from src.inventory.org_device_inventory_summary_facade import (
    OrgDeviceInventorySummary,  # Cat B (1013 SC-001 position 29) -- re-export
)
from src.network.routing_utils import (  # Cat A canonical (1014 P4)
    RoutingDeps,
    RoutingUtils,
)
from src.org.org_config_migration_manager import OrgConfigMigrationManager  # Cat B (1013 SC-001 position 5)
from src.org.org_ticket_manager import (
    OrgTicketManager,  # Cat B (1013 SC-001 position 46) -- re-export for MistHelper.OrgTicketManager callers
)
from src.org_data_collector import OrgDataCollector  # Import org-level data collection orchestrator
from src.refactors.anomaly_metrics_discovery import (
    AnomalyMetricsDiscovery,  # Cat B (1013 SC-001 pos 43) -- lazy access via mh.AnomalyMetricsDiscovery
)
from src.refactors.connection_pool_executor import ConnectionPoolExecutor  # Extracted pool executor (1012 SC-003)
from src.refactors.data_directory_checker import DataDirectoryChecker  # Early data-dir writable check (SC-005)
from src.refactors.device_config_template_cloner_manager import (
    DeviceConfigTemplateClonerManager,  # Extracted device config template cloner (SC-020)
)
from src.refactors.device_data_fetcher import (
    DeviceDataFetcher,  # Extracted device fetcher (SC-017); lazy re-export for interactive_display_utils
)
from src.refactors.fast_mode_backoff_multiplier import (
    FastModeBackoffMultiplier,  # Extracted backoff multiplier (SC-028); lazy re-export for org_device_stats_exporter
)

# FastModeDevicesPerThread import removed: only referenced from within ConnectionPoolExecutor (1012 SC-003)
from src.refactors.fast_mode_sequential_max_retries import (
    FastModeSequentialMaxRetries,  # Cat E (1014 P8) -- re-export for lazy access in api_fetch_utils.py
)
from src.refactors.initialize_mist_session import (
    MistSessionInitializer,  # Extracted token-based session initializer (SC-024)
)
from src.refactors.initialize_mist_session_interactive import (
    MistSessionInteractiveInitializer,  # Extracted interactive login initializer (SC-023)
)
from src.refactors.inventory_csvcomparator import (
    InventoryCSVComparator,  # Extracted inventory CSV comparator adapter (SC-018)
)
from src.refactors.is_debug_mode import IsDebugMode  # Extracted debug-mode predicate (SC-002)
from src.refactors.keyboard_listener import (
    KeyboardListener,  # Re-exported for src.ssh.cli_shell_manager.CLIShellManager lazy `mh.KeyboardListener` access
)
from src.refactors.main_entrypoint import MainEntrypoint  # Extracted CLI main entrypoint (SC-026)
from src.refactors.maps_manager_launcher import MapsManagerLauncher  # Extracted Maps Manager launcher (SC-006)
from src.refactors.marvis_data_utils import (
    MarvisDataUtilsFactory,  # Cat B (1013 SC-001 position 39) -- re-export for lazy access in troubleshoot_utils.py
)
from src.refactors.mist_wan_target_ports import (
    MistWanTargetPorts,  # Extracted operator-configured WAN target-ports list (SC-032)
)
from src.refactors.msp_privilege_detection import (
    detect_msp_privileges,  # Extracted MSP privilege detector (1015 T-05, Cat E)
)
from src.refactors.package_import_map import (
    PackageImportMapManager,  # Extracted pip-name -> import-name mapping (SC-025)
)
from src.refactors.run_interactive_test import (
    RunInteractiveTestManager,  # Extracted interactive-test manager (SC-011)
)
from src.refactors.service_ping_launcher import ServicePingLauncher  # Extracted Service Ping launcher (SC-008)
from src.refactors.sqlite_database_writer import (
    SQLiteDatabaseWriter,  # Extracted SQLite writer (SC-003) -- re-export for MistHelper.SQLiteDatabaseWriter callers
)
from src.refactors.switch_to_interactive_login import (
    SwitchToInteractiveLoginManager,  # Extracted switch-to-interactive-login manager (SC-010)
)
from src.refactors.tui_launcher import TUILauncher  # Extracted TUI launcher (SC-004)
from src.refactors.wan2_migration_launcher import WAN2MigrationLauncher  # Extracted WAN2 migration launcher (SC-009)
from src.refactors.wan_probe_device_override_manager import (
    WANProbeDeviceOverrideManager,  # Extracted WAN probe device override manager (SC-021)
)
from src.refactors.wanprobe_config_manager import (
    WANProbeConfigManager,  # Extracted WAN probe config manager (SC-015)
)
from src.refactors.wlanradius_timer_manager import (
    WLANRadiusTimerManager,  # Extracted WLAN RADIUS timer manager (SC-014)
)
from src.reports.e911_bssid import (
    E911BSSIDReportGenerator,  # Module-level for tests + lazy-import re-export for src.export.org_export_utils
)
from src.reports.global_wired_client_report_generator import (
    GlobalWiredClientReportGenerator,  # Cat B (1013 SC-001 position 36) -- re-export
)
from src.reports.offline_device_reporter import (
    OfflineDeviceReporter,  # Cat B (1013 SC-001 position 44) -- re-export for MistHelper.OfflineDeviceReporter callers
)
from src.reports.sfp_transceiver_data_processor import (
    SFPTransceiverDataProcessor,  # Cat B (1013 SC-001 position 27) -- re-export
)
from src.reports.wired_client_manufacturer_report_generator import (
    WiredClientManufacturerReportGenerator,  # Cat B (1013 SC-001 position 26) -- re-export
)
from src.site.address_audit import AddressAuditEngine  # Menu 195: read-only CSV site-address audit
from src.site.bulk_radius_wlan_config_manager import (
    BulkRadiusWLANConfigManager,  # Cat B (1013 SC-001 position 15) -- re-export
)
from src.site.site_config_manager import (  # Cat A canonical (1013 SC-003)
    SiteConfigDependencies as _SiteConfigDependencies,
)
from src.site.site_config_manager import (
    SiteConfigManager,
)
from src.site.site_config_manager import (
    configure_site_config_manager_dependencies as _configure_site_config_dependencies,
)
from src.ssh.cli_shell_manager import CLIShellManager
from src.ssh.ssh_runner import EnhancedSSHRunner  # Import SSH command execution and result parsing
from src.ssh.ssh_runner_manager import SSHRunnerManager, SSHRunnerManagerDeps  # Cat A canonical (1014 P15)
from src.time.time_utils import TimeUtils  # Cat E canonical (1014 P6)
from src.troubleshooting.interactive_test_runner import (
    InteractiveTestRunner,
)  # Import interactive diagnostic test runner
from src.troubleshooting.marvis_troubleshoot_utils import (
    MarvisTroubleshootDeps,  # Cat B (1013 SC-001 position 39) -- re-export for lazy access in troubleshoot_utils.py
)
from src.troubleshooting.marvis_troubleshoot_utils import (
    MarvisTroubleshootUtils as ExtractedMarvisTroubleshootUtils,  # Cat B (1013 SC-001 position 39) -- re-export
)
from src.troubleshooting.troubleshoot_utils import (
    TroubleshootUtils,  # Cat B (1013 SC-001 position 39) -- re-export for MistHelper.TroubleshootUtils callers
)
from src.ui.display_utils import (
    DisplayUtils,  # Cat B (1013 SC-001 position 11) -- re-export for lazy _MH.DisplayUtils callers
)
from src.ui.interactive_display_utils import (
    InteractiveDisplayUtils,  # Cat B (1013 SC-001 position 10) -- re-export for callers at 17392/17393/17394/17395
)
from src.utils.environment_utils import (
    EnvironmentUtils,  # Cat B (1013 SC-001 position 33) -- re-export for MistHelper.EnvironmentUtils callers
)
from src.utils.file_path_utils import (
    FilePathUtils,  # Cat E canonical (1015 T-13) -- re-export for MistHelper.FilePathUtils callers
)
from src.utils.filter_operator_engine import (
    FilterOperatorEngine,  # Cat B (1013 SC-001 position 40) -- re-export for MistHelper.FilterOperatorEngine callers
)
from src.utils.operation_registry import (
    OperationRegistry,  # Cat B (1013 SC-001 position 13) -- re-export for menu safety classification
)
from src.validation.validation_utils import ValidationUtils  # Cat E canonical (1014 P5)
from src.wan_hub_group_manager import WanHubGroupNumberManager  # Import WAN hub group number manager for hub routing
from src.wan_vpn_builder import WanVpnBuilder  # Import WAN VPN configuration builder
from src.websocket.commands import MacTableCommand  # Import WebSocket show-MAC-table command handler
from src.websocket.context import WebSocketCmdDeps  # Import WebSocket command dependency injection class
from src.websocket.diagnostics import (
    ArpDeviceExecutor,
    PingDeviceExecutor,
)  # WebSocket network diagnostic command executors
from src.websocket.manager import WebSocketManager  # Import WebSocket connection manager for long-running diagnostics

# ============================================================================
# EARLY LOGGING SETUP
# ============================================================================
# Configure logging IMMEDIATELY after imports to prevent Python from creating
# a default handler that writes script.log to the root directory.
# This configuration will be enhanced later by GlobalImportManager._setup_logging()
# with additional handlers and formatting, but this ensures all early logging
# calls go to the correct location.
_early_log_dir = "data"  # Define data directory for logs (same as runtime output directory)
os.makedirs(_early_log_dir, exist_ok=True)  # Create data/ directory if it doesn't exist (no error if already present)
_early_log_path = os.path.join(
    _early_log_dir, "script.log"
)  # Define full path to script.log using os.path.join for cross-platform compatibility


# ============================================================================
# DATA DIRECTORY PERMISSION CHECKER
# ============================================================================
# Critical for container deployments - runs as non-root 'misthelper' user


# Run data directory check immediately (NO WRAPPER - direct class instantiation)
DataDirectoryChecker(
    _early_log_dir
).check()  # Instantiate checker and validate data/ directory write permissions (exits if not writable)

# Get log levels from environment (same as GlobalImportManager._setup_logging)
_early_console_level = int(
    os.environ.get("CONSOLE_LOG_LEVEL", logging.INFO)
)  # Read console log level from env (default: INFO=20)
_early_file_level = int(
    os.environ.get("LOGGING_LOG_LEVEL", logging.INFO)
)  # Read file log level from env (default: INFO=20)

# Make stdout/stderr resilient to non-cp1252 characters in real data (e.g. the Hawaiian
# 'okina in addresses like "Maka'ala Street"). Without this, printing the comparison table
# or logging such strings raises UnicodeEncodeError under the default Windows console codec.
for _std_stream in (sys.stdout, sys.stderr):  # Harden both standard streams (best-effort).
    _reconfigure = getattr(_std_stream, "reconfigure", None)  # TextIOWrapper has this; plain TextIO does not.
    if callable(_reconfigure):  # Only proceed when the stream supports reconfiguration.
        try:
            _reconfigure(encoding="utf-8", errors="backslashreplace")  # UTF-8 + never-crash fallback
        except ValueError:  # Stream already closed or codec rejected -> skip safely
            pass  # Degradation is acceptable: worst case is the original behavior, no new failure introduced

# Create handlers with appropriate levels
_early_console_handler = logging.StreamHandler()  # Create handler for console output (stdout/stderr)
_early_console_handler.setLevel(
    _early_console_level
)  # Set console handler to respect CONSOLE_LOG_LEVEL environment variable
_early_file_handler = logging.FileHandler(
    _early_log_path, encoding="utf-8"
)  # script.log file output; UTF-8 so non-cp1252 chars (e.g. Hawaiian 'okina) never crash logging
_early_file_handler.setLevel(_early_file_level)  # Set file handler to respect LOGGING_LOG_LEVEL environment variable

logging.basicConfig(  # Configure root logger with handlers and format
    level=logging.DEBUG,  # Root logger captures all levels; handlers filter based on their individual levels
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define log message format with timestamp, level, and message
    handlers=[_early_file_handler, _early_console_handler],  # Register both file and console handlers
    force=True,  # Force reconfiguration even if logging was already configured (needed for module init)
)

# Attach LogSanitizer to redact sensitive fields (API tokens, passwords, MACs) from logs
try:  # Attempt to import LogSanitizer from mistapi library
    from mistapi.__logger import LogSanitizer  # Import mistapi log sanitizer (redacts secrets from output)

    logging.getLogger().addFilter(LogSanitizer())  # Register sanitizer filter on root logger to redact all log records
except ImportError:  # If LogSanitizer not available, skip (mistapi pre-0.59.3 doesn't have it)
    pass  # mistapi pre-0.59.3 does not have LogSanitizer; safe to skip

# Log Python version warning if below minimum requirement
if sys.version_info < MINIMUM_PYTHON_VERSION:  # Check if Python is below minimum version
    version_str = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"  # Format current Python version
    )
    required_str = f"{MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]}"  # Format minimum required version
    logging.warning(  # Log warning (will be written to script.log after handler setup)
        "Python %s detected. MistHelper requires Python %s+. Some features may not work correctly.",
        version_str,
        required_str,
    )


# Debug mode detection helper
# NOTE: is_debug_mode extracted to IsDebugMode.check. See specs/1012-misthelper-refactor-hot-functions/spec.md.


# ============================================================================
# CONFIGURATION DATACLASSES (5-Item Rule Compliance)
# ============================================================================
# These dataclasses group related parameters to comply with the 5-parameter limit
# per function. Each dataclass encapsulates configuration for a specific domain.


# NOTE: SSHConnectionConfig removed (1014 P3) - was a dead duplicate of src/ssh/ssh_runner.py:155;
#       nothing in MistHelper.py imported the local copy, and all src/ssh/*.py callers
#       already imported from src.ssh.ssh_runner. Import from src.ssh.ssh_runner instead.
# NOTE: SSHExecutionConfig removed (1014 P1) - was a dead duplicate of src/ssh/ssh_runner.py:167;
#       nothing in MistHelper.py imported the local copy, and all src/ssh/batch/*.py callers
#       already imported from src.ssh.ssh_runner. Import from src.ssh.ssh_runner instead.
# NOTE: WebSocketListenerConfig removed - use ARPCommandManager._listen_for_output parameters directly
# NOTE: MapViewerConfig removed (SC-002) - unused dataclass, MapsManager builds runtime state directly


# NOTE: DeviceFetchConfig extracted to src/refactors/device_data_fetcher.py::DeviceFetchConfig.
# See specs/1015-misthelper-refactor-final-15/spec.md.


# ============================================================================
# EARLY DEPENDENCY AUTO-INSTALLER
# ============================================================================
# This section attempts to auto-install critical dependencies BEFORE any imports
# that might fail. This enables running the script directly without pre-setup.

# Load .env BEFORE dependency check so DISABLE_AUTO_INSTALL and
# AUTO_UPGRADE_TO_LATEST are honoured when set in .env.
try:  # Attempt to load environment variables from a .env file before any dependency checks
    from dotenv import (
        load_dotenv as _early_load_dotenv,
    )  # Import python-dotenv's loader (aliased to mark it as early-stage)

    _early_load_dotenv()  # Read .env and populate os.environ so config flags are available during startup
except Exception:  # If python-dotenv is not installed yet, fall back to a manual parser
    # Inline fallback: read .env manually so env vars are available
    try:  # Attempt a best-effort manual parse of the .env file
        with open(".env") as _ef:  # Open .env in the current working directory
            for _line in _ef:  # Process the file one line at a time
                _line = _line.strip()  # Remove surrounding whitespace and the trailing newline
                if (
                    _line and not _line.startswith("#") and "=" in _line
                ):  # Skip blanks, comment lines, and malformed entries
                    _k, _v = _line.split("=", 1)  # Split on the first '=' into key and value (values may contain '=')
                    os.environ.setdefault(
                        _k.strip(), _v.strip()
                    )  # Set the var only if not already defined (don't override real env)
    except Exception:  # nosec B110  # If .env is missing or unreadable, continue silently (the file is optional)
        pass  # No .env available; rely on the real process environment only

# NOTE: PACKAGE_IMPORT_MAP extracted to
# src/refactors/package_import_map.py::PackageImportMapManager.MAPPING
# per initiative 1011 SC-025 (FR-003: no wrapper shim; FR-005: fn->method).


def _get_installed_version(package_name: str) -> str:  # Look up the installed version string for a package
    """Get installed version of a package using importlib.metadata."""
    try:  # Attempt to read version metadata from the installed distribution
        from importlib.metadata import version as get_version  # Import the stdlib version lookup (Python 3.8+)

        return get_version(package_name)  # Return the installed version string (e.g., '0.59.3')
    except Exception:  # Package not installed or its metadata is missing
        return ""  # Return empty string to signal 'not installed' to callers


def _leading_digits(segment: str) -> str:  # Extract the numeric prefix of one version segment
    """Return the leading digit run of a version segment (e.g., '0a1' -> '0')."""
    numeric = ""  # Accumulate the leading digit characters of this segment
    for char in segment:  # Walk characters left to right until a non-digit ends the prefix
        if not char.isdigit():  # First non-digit (e.g., the 'a' in '0a1') ends the numeric prefix
            break  # Ignore any pre-release suffix for comparison purposes
        numeric += char  # Append this digit to the numeric prefix
    return numeric  # Caller defaults empty results to 0


def _parse_version(version_str: str) -> tuple:  # type: ignore[type-arg]  # Convert a version string into a comparable integer tuple
    """Parse version string into comparable tuple (e.g., '0.59.3' -> (0, 59, 3))."""
    try:  # Malformed input is handled by the except below
        parts = [
            int(_leading_digits(part) or "0") for part in version_str.split(".")
        ]  # Numeric prefix of each dotted segment, defaulting empty/non-numeric segments to 0
        return tuple(parts)  # Return as a tuple so versions compare element-by-element
    except Exception:  # Malformed version string that cannot be parsed
        return (0,)  # Return a minimal tuple so comparisons treat it as the lowest possible version


def _extract_version_constraint(spec: str) -> tuple[str, str]:  # Split a spec into operator + required version
    """Return (operator, required_version) parsed from a spec like '>=0.59.0'.

    Defaults to ('>=', '') when the spec carries no recognizable operator/version.
    """
    operators = [">=", "<=", "==", "!=", ">", "<"]  # Two-char operators first so '>=' matches before '>'
    for op in operators:  # Find which operator the spec uses
        if op in spec:  # The spec string contains this operator
            parts = spec.split(op, 1)  # Split once into [package-or-empty, version]
            if len(parts) == 2:  # Ensure the split produced both halves
                return op, parts[1].strip()  # Operator plus the required version text right of it
    return ">=", ""  # No operator found: signal 'no constraint' to the caller


def _pad_version_tuples(
    installed_tuple: tuple,
    required_tuple: tuple,  # type: ignore[type-arg]
) -> tuple[tuple, tuple]:  # type: ignore[type-arg]  # Zero-pad two version tuples to equal length
    """Right-pad both version tuples with zeros so they compare element-by-element."""
    max_len = max(len(installed_tuple), len(required_tuple))  # Longest of the two drives the padding width
    installed_padded = installed_tuple + (0,) * (max_len - len(installed_tuple))  # Pad installed (e.g., 1.2 -> 1.2.0)
    required_padded = required_tuple + (0,) * (max_len - len(required_tuple))  # Pad required to align lengths
    return installed_padded, required_padded  # Equal-length tuples ready for comparison


# Operator symbol -> comparison predicate; dict dispatch keeps _version_satisfies flat (no if/elif chain).
_VERSION_COMPARATORS: "dict[str, Callable[[tuple[int, ...], tuple[int, ...]], bool]]" = {
    ">=": lambda installed, required: installed >= required,  # 'at least' constraint
    ">": lambda installed, required: installed > required,  # 'strictly newer' constraint
    "<=": lambda installed, required: installed <= required,  # 'at most' constraint
    "<": lambda installed, required: installed < required,  # 'strictly older' constraint
    "==": lambda installed, required: installed == required,  # exact-match constraint
    "!=": lambda installed, required: installed != required,  # exclusion constraint
}


def _version_satisfies(installed: str, spec: str) -> bool:  # Decide whether installed meets the spec constraint
    """Check if installed version satisfies the version specification."""
    if not installed:  # An empty installed version means the package isn't present
        return False  # Treat 'not installed' as 'requirement not satisfied'

    operator_symbol, required_version = _extract_version_constraint(spec)  # Parse operator + required version
    if not required_version:  # No version constraint was found in the spec
        return True  # No version requirement, any version satisfies

    installed_tuple, required_tuple = _pad_version_tuples(  # Align both versions to equal length for comparison
        _parse_version(installed),
        _parse_version(required_version),  # Convert each to a comparable integer tuple
    )

    comparator = _VERSION_COMPARATORS.get(operator_symbol)  # Look up the predicate for this operator
    if comparator is None:  # Unknown operator (should not happen given the parser)
        return True  # Be permissive and treat the requirement as satisfied
    return comparator(installed_tuple, required_tuple)  # Apply the matched comparison predicate


def _get_latest_pypi_version(package_name: str) -> str:  # Ask PyPI for a package's newest published version
    """Query PyPI for the latest version of a package.

    Uses a bounded read to prevent hangs behind corporate
    proxies (e.g. Zscaler SSL inspection).
    """
    try:  # Network calls can fail many ways; treat any failure as 'latest unknown'
        import json as json_mod  # Local import keeps startup fast when this code path isn't used
        import ssl  # Needed to build a TLS context for the HTTPS request
        import urllib.request  # Standard-library HTTP client (avoids needing 'requests' this early)

        url = f"https://pypi.org/pypi/{package_name}/json"  # PyPI JSON API endpoint for this package's metadata
        ctx = ssl.create_default_context()  # Default TLS context (validates server certificates)
        request = urllib.request.Request(url)  # Build the HTTP GET request object
        max_bytes = 256 * 1024  # Cap the read at 256 KB to prevent hangs/abuse behind SSL-inspection proxies
        with urllib.request.urlopen(
            request, timeout=5, context=ctx
        ) as response:  # nosec B310  # 5s timeout avoids blocking startup on blocked networks
            raw = response.read(max_bytes)  # Read at most max_bytes of the JSON response body
            data = json_mod.loads(raw.decode())  # Parse the JSON metadata into a dict
            version = data.get("info", {}).get("version", "")  # Return latest version string, or '' if absent
            return str(version) if version else ""  # Cast to str for strict typing
    except Exception:  # Any error (offline, proxy block, parse failure) means we can't determine the latest version
        return ""  # Empty string signals 'latest unknown' so callers skip the upgrade check


def _parse_requirement_line(line: str) -> tuple[str, str] | None:  # Parse one requirements.txt line
    """Return (package_name, package_spec) for a dependency line, or None to skip it.

    Skips blank lines, full-line comments (including dev-only entries like '# pytest'),
    and lines that reduce to nothing after stripping a trailing inline comment.
    """
    stripped = line.strip()  # Remove surrounding whitespace and the trailing newline
    if not stripped or stripped.startswith("#"):  # Ignore blank lines and any full-line comment
        return None  # Nothing to parse on this line
    if "#" in stripped:  # Line has a trailing inline comment after the spec
        stripped = stripped.split("#")[0].strip()  # Keep only the spec text before the '#'
    if not stripped:  # The line was only an inline comment after stripping
        return None  # Nothing left to parse
    package_name = re.split(r"[><=!]", stripped)[0].strip()  # Name is everything before the first comparison operator
    return (package_name, stripped)  # (name, full spec including any version constraint)


def _parse_requirements_file(filepath="requirements.txt"):  # Read dependency specs from requirements.txt
    """Parse requirements.txt into a list of (package_name, package_spec) tuples.

    SECURITY: only reads requirements.txt (no arbitrary file access); skips comments/blanks/dev deps.
    """
    packages = []  # Accumulate (name, spec) tuples to return to the dependency checker
    try:  # The file may be missing or unreadable; handle that gracefully below
        with open(filepath, encoding="utf-8") as requirements_file:  # Open requirements.txt as UTF-8 text
            for line in requirements_file:  # Process one dependency line at a time
                parsed = _parse_requirement_line(line)  # Parse this line into (name, spec) or None to skip
                if parsed is not None:  # Only keep lines that yielded a real dependency
                    packages.append(parsed)  # Record this dependency for the caller
        logging.debug("Parsed %s packages from %s", len(packages), filepath)  # Debug aid: how many specs were parsed
        return packages  # Return the collected dependency list
    except FileNotFoundError:  # requirements.txt does not exist at the given path
        logging.warning("Requirements file not found: %s", filepath)  # Warn that auto-install is skipped
        return []  # No packages to check
    except Exception as parse_error:  # Any other read/parse error
        logging.warning("Error parsing requirements file: %s", parse_error)  # Log the failure reason
        return []  # Fail safe with an empty list rather than crashing startup


# _early_dependency_check_legacy_impl removed per issue #431 (ARCH-NAMING +
# dead-code). The function (~430 lines, cyclomatic 64) was a leftover legacy
# implementation never called from anywhere -- production startup uses the
# canonical _early_dependency_check() defined below which delegates to the
# extracted src/bootstrap/* orchestrator.


# Simplified facade delegating dependency bootstrap logic to extracted src/bootstrap modules.
def _early_dependency_check() -> None:  # Public entry point; delegates to the extracted bootstrap modules
    """Run early dependency checks through the extracted bootstrap orchestrator."""
    installer = PackageInstaller(  # Build the installer with stdlib modules injected (enables testing/mocking)
        os_module=os,  # Inject os for path/env operations
        subprocess_module=subprocess,  # Inject subprocess for running pip/uv
        sys_module=sys,  # Inject sys for the interpreter path
        logging_module=logging,  # Inject logging for progress messages
    )
    orchestrator = DependencyCheckOrchestrator(  # Build the orchestrator that drives the detect-and-install flow
        os_module=os,  # Inject os for env checks (DISABLE_AUTO_INSTALL, etc.)
        logging_module=logging,  # Inject logging for progress messages
        sys_module=sys,  # Inject sys for the interpreter path
        package_import_map=PackageImportMapManager.MAPPING,  # Provide the pip-name -> import-name mapping
        parse_requirements_file_fn=_parse_requirements_file,  # Reuse the requirements parser defined above
        get_installed_version_fn=_get_installed_version,  # Reuse the installed-version lookup
        version_satisfies_fn=_version_satisfies,  # Reuse the version-constraint checker
        get_latest_pypi_version_fn=_get_latest_pypi_version,  # Reuse the PyPI latest-version lookup
        parse_version_fn=_parse_version,  # Reuse the version-tuple parser
        installer=installer,  # Hand the orchestrator the installer built above
    )
    orchestrator.run()  # Execute the dependency check + install/upgrade workflow


# Run early dependency check (will be skipped if DISABLE_AUTO_INSTALL=true)
_early_dependency_check()  # Run the bootstrap immediately at import time

# Additional standard library imports
import concurrent.futures  # High-level parallelism primitives for batched API calls
import inspect  # Introspect functions/classes at runtime (signatures, source lookup)
import threading  # Locks and threads for safe concurrent operations

# Note: datetime class already imported at top of file (line 26)
# Only import timezone here to avoid shadowing datetime class
from datetime import UTC, timezone  # UTC marker plus timezone helper for tz-aware time math

# Third-party imports with fallbacks
# Required dependencies: raise clear error if missing (auto-installed by early dependency check)
# Optional dependencies: use _has_X availability flags for runtime guards
# Pylance uses the TYPE_CHECKING imports above for type analysis.
try:  # PrettyTable is required for formatted console tables
    from prettytable import PrettyTable  # ASCII table renderer used across menus and reports
except ImportError as _pt_err:  # Required dependency is missing
    raise ImportError(
        "PrettyTable is required but not installed. Run: pip install prettytable"
    ) from _pt_err  # Fail fast with install guidance

try:  # numpy is optional (only some analytics need it)
    import numpy as _np_impl  # Numerical arrays for analytics calculations

    np: "ModuleType | None" = _np_impl  # Union type lets guards detect absence
except ImportError:  # numpy not installed
    np = None  # None lets runtime guards detect absence

try:  # websocket-client is required for live device diagnostics
    import websocket  # WebSocket client fail-fast install guard (used by src.device.arp_command_manager)
except ImportError as _ws_err:  # Required dependency is missing
    raise ImportError(
        "websocket-client is required but not installed. Run: pip install websocket-client"
    ) from _ws_err  # Fail fast with install guidance

try:  # SequenceMatcher is optional (used for fuzzy string comparisons)
    from difflib import SequenceMatcher as _SequenceMatcherImpl  # Stdlib similarity-ratio helper

    SequenceMatcher: type[_SequenceMatcherImpl] | None = _SequenceMatcherImpl  # Class handle for guarded use
except ImportError:  # Extremely unlikely for a stdlib module, but guard anyway
    SequenceMatcher = None  # None lets callers detect absence

# Import mistapi later through GlobalImportManager for better dependency management
# Using Any type since mistapi is dynamically loaded but guaranteed to be available before use
mistapi: Any = None  # Placeholder; the real mistapi module is loaded later by GlobalImportManager


# tqdm wrapper: canonical home is src/utils/tqdm_wrapper.py (1015 T-14, Cat E).
# The wrapper resolves to the real tqdm package if installed, else a no-op pass-through.
# Re-exported here so ``MistHelper.tqdm`` / ``mh.tqdm`` callers keep working unchanged.
from src.utils.tqdm_wrapper import tqdm  # noqa: E402, I001  # Cat E canonical (1015 T-14) -- re-export.


try:  # requests is required for all HTTP calls
    import requests  # HTTP library fail-fast install guard (also used via function-local imports)
except ImportError as _req_err:  # Required dependency is missing
    raise ImportError(
        "requests is required but not installed. Run: pip install requests"
    ) from _req_err  # Fail fast with install guidance

try:  # urllib3 is optional (used to suppress noisy SSL warnings)
    import urllib3 as _urllib3_impl  # Low-level HTTP library underlying requests

    urllib3: "ModuleType | None" = _urllib3_impl  # Union type lets guards detect absence
except ImportError:  # urllib3 not installed
    urllib3 = None  # None lets guards detect absence

try:  # pyte is optional (terminal emulation for parsing WebSocket output)
    import pyte as _pyte_impl  # In-memory terminal emulator to render device CLI screens

    pyte: "ModuleType | None" = _pyte_impl  # Union type lets guards detect absence
    _has_pyte = True  # Flag that terminal-emulation features are available
except ImportError:  # pyte not installed
    pyte = None  # None lets guards detect absence
    _has_pyte = False  # Flag that terminal-emulation features are unavailable

try:  # paramiko is optional (used for direct SSH operations)
    import paramiko as _paramiko_impl  # SSH client library
    from paramiko import RejectPolicy as _RejectPolicyImpl  # Strict host-key policy
    from paramiko import SSHClient as _SSHClientImpl  # SSH client class

    paramiko: "ModuleType | None" = _paramiko_impl  # Union type lets guards detect absence
    SSHClient: type[_SSHClientImpl] | None = _SSHClientImpl  # Class handle for guarded use
    RejectPolicy: type[_RejectPolicyImpl] | None = _RejectPolicyImpl  # Class handle for guarded use
except ImportError:  # paramiko not installed
    paramiko = None  # None lets guards detect absence
    SSHClient = None  # None lets guards detect absence
    RejectPolicy = None  # None lets guards detect absence

# Optional imports with fallbacks
try:  # scourgify is optional (US street-address normalization)
    from scourgify import normalize_address_record  # Normalize messy US addresses into structured fields
except ImportError:  # scourgify not installed
    normalize_address_record = None  # None lets callers fall back to raw address strings

try:  # rapidfuzz is optional (fast fuzzy string matching)
    from rapidfuzz import fuzz as _fuzz_impl  # High-performance fuzzy match scoring

    fuzz: "ModuleType | None" = _fuzz_impl  # Union type lets guards detect absence
except ImportError:  # rapidfuzz not installed
    fuzz = None  # None lets callers skip fuzzy matching

# Keyboard listener functionality was extracted to src/refactors/keyboard_listener.py
# (PR-13). The extracted class KeyboardListener preserves the no-op stub for the
# single remaining call site (interactive SSR/SRX websocket shell). No wrapper or
# alias is retained here per FR-005 (no shims left in MistHelper).


# stop_listening() removed per issue #431: it was a `pass` no-op stub for a
# legacy keyboard listener that has no real implementation. The single call
# site inside `send_keyboard_input` (interactive SSR/SRX websocket shell) is
# also removed below since stopping a never-started listener is a no-op.


# ============================================================================
# CENTRALIZED PAGINATION DEFAULTS
# ============================================================================
# Several legacy code paths relied on the mistapi client's implicit default page
# size (commonly 100). That caused excessive paging (e.g., 10x HTTP calls for
# 1000-item datasets). We unify a single configurable default via environment
# variable MIST_PAGE_LIMIT (clamped to 1..1000). All new/updated listOrgSites /
# getOrgInventory calls should pass limit=DEFAULT_API_PAGE_LIMIT or use the
# helper wrappers below to ensure consistency and simpler tuning.
try:  # Read the configured API page size from the environment
    _raw_page_limit_env = os.environ.get("MIST_PAGE_LIMIT", "1000").strip()  # Raw env value, default '1000', trimmed
    _parsed_limit = int(_raw_page_limit_env)  # Convert to int (raises if non-numeric)
except Exception:  # Missing or non-numeric value
    _parsed_limit = 1000  # Fall back to a sensible default page size

DEFAULT_API_PAGE_LIMIT = max(1, min(_parsed_limit, 1000))  # Clamp to the 1..1000 range the Mist API accepts
if _parsed_limit != DEFAULT_API_PAGE_LIMIT:  # The configured value was out of range and had to be clamped
    logging.warning(
        "MIST_PAGE_LIMIT value %s adjusted to %s (valid range 1..1000)", _parsed_limit, DEFAULT_API_PAGE_LIMIT
    )  # Warn about the adjustment

logging.debug(
    "API Page Size Configuration Active: DEFAULT_API_PAGE_LIMIT=%s", DEFAULT_API_PAGE_LIMIT
)  # Record the effective page size for debugging


def _apply_dotenv_line(line: str) -> None:  # Set one KEY=VALUE pair from a .env line into the environment
    """Parse one .env line and set it into os.environ, skipping blanks/comments/malformed entries."""
    stripped = line.strip()  # Remove surrounding whitespace and the trailing newline
    if not stripped or stripped.startswith("#") or "=" not in stripped:  # Skip blanks, comments, malformed entries
        return  # Nothing assignable on this line
    key, value = stripped.split("=", 1)  # Split on the first '=' (values may themselves contain '=')
    os.environ[key.strip()] = value.strip()  # Set the env var (overwrites, unlike setdefault)


# Early dotenv import for configuration loading
def _fallback_load_dotenv() -> None:  # Minimal .env parser used when python-dotenv isn't installed
    """Fallback .env loader when python-dotenv package is not installed."""
    try:  # The .env file is optional; handle its absence/errors gracefully
        with open(".env") as dotenv_file:  # Open .env in the current working directory
            for line in dotenv_file:  # Process the file one line at a time
                _apply_dotenv_line(line)  # Set this KEY=VALUE pair (skips blanks/comments internally)
    except FileNotFoundError:  # No .env file present
        logging.debug("No .env file found")  # Not an error; just note it at debug level
    except Exception as parse_error:  # Any other read/parse problem
        logging.debug("Error loading .env file: %s", parse_error)  # Log the reason without crashing startup


try:  # Prefer the full-featured python-dotenv loader when available
    from dotenv import load_dotenv as _load_dotenv_impl  # Robust .env parser from python-dotenv

    load_dotenv: "Callable[..., object]" = _load_dotenv_impl  # Common signature: no-arg call, ignored return
    DOTENV_AVAILABLE = True  # Flag that the real loader is in use
    load_dotenv()  # Load .env now so config is available to the import manager
except ImportError:  # python-dotenv not installed
    DOTENV_AVAILABLE = False  # Flag that we're using the minimal fallback
    # Use fallback loader and create an alias for later calls
    load_dotenv = _fallback_load_dotenv  # Alias so later load_dotenv() calls still work
    _fallback_load_dotenv()  # Load .env now using the fallback parser


class GlobalImportManager:
    """
    Centralized import and dependency management system for MistHelper.

    This class handles:
    - UV-based package installation and upgrades
    - Centralized import management
    - Dependency verification and auto-installation
    - Graceful handling of optional dependencies
    - Performance optimization through early imports
    """

    _REQUIRED_PACKAGES: dict[str, str | None] = {  # Class-level required spec map (data, not behavior)
        # Core API and networking
        "mistapi": "mistapi>=0.63.1",  # Official Mist API SDK floor aligned with latest validated upstream release
        "requests": "requests>=2.28.0",  # HTTP client used for API calls
        "websocket-client": "websocket-client>=1.8.0",  # WebSocket client minimum aligned to modern mistapi needs
        # CLI and user interface
        "prettytable": "prettytable>=3.5.0",  # ASCII table rendering for menus/reports
        "tqdm": "tqdm>=4.64.0",  # Progress bars for long-running operations
        # Data processing
        "numpy": "numpy>=1.24.0",  # Numerical arrays for analytics
        "python-dotenv": "python-dotenv>=1.0.0",  # Loads configuration from .env
        # SSH and direct device connections
        "paramiko": "paramiko>=2.9.0",  # More compatible version for SSH
        # Standard library modules (no installation needed)
        "argparse": None,  # Built-in
        "csv": None,  # Built-in
        "json": None,  # Built-in
        "sqlite3": None,  # Built-in
        "time": None,  # Built-in
        "datetime": None,  # Built-in
        "threading": None,  # Built-in
        "concurrent.futures": None,  # Built-in
        "inspect": None,  # Built-in
        "http.client": None,  # Built-in
        "re": None,  # Built-in
        "difflib": None,  # Built-in
        "unicodedata": None,  # Built-in
        "collections": None,  # Built-in
        "ast": None,  # Built-in
        "math": None,  # Built-in
        "shutil": None,  # Built-in
        "glob": None,  # Built-in
        "traceback": None,  # Built-in
    }

    _OPTIONAL_PACKAGES_RAW: dict[str, str | None] = {  # Class-level optional spec map (data, not behavior)
        "sshkeyboard": "sshkeyboard>=2.3.0",  # Keyboard capture (legacy/optional)
        "pyte": "pyte>=0.8.0",  # Terminal emulation for parsing device output
        "usaddress-scourgify": "usaddress-scourgify>=0.6.0",  # US address normalization
        "rapidfuzz": "rapidfuzz>=3.8.0",  # Fast fuzzy string matching
        "urllib3": "urllib3>=1.26.0",  # Low-level HTTP (SSL warning control)
        "plotly": "plotly>=5.14.0",  # Interactive charts for reports
        "dash": "dash>=2.9.0",  # Web dashboards (maps viewer)
        "kaleido": "kaleido>=0.2.1",  # Static image export for plotly charts
        "matplotlib": "matplotlib>=3.5.0",  # Static plotting for analytics
    }

    def __init__(self) -> None:  # Read config from env and prepare dependency-tracking state
        """Initialize the import manager with configuration from environment variables."""
        self._load_upgrade_configuration()  # Read env-driven upgrade/UV/CSV freshness settings
        self._initialize_dependency_tracking()  # Prepare package-tracking lists and import/UV caches
        self._initialize_import_mappings()  # Build package->import name maps and special import handlers
        self._setup_logging()  # Configure handlers/levels before other init runs
        self._detect_virtual_environment()  # Log whether we're in a venv (affects installs)
        self._define_package_requirements()  # Populate the required/optional package dicts

    def _load_upgrade_configuration(self):  # Read upgrade/UV/CSV settings from the environment
        """Load upgrade, UV-check, and CSV-freshness settings from environment variables."""
        logging.debug("Loading import-manager upgrade configuration from environment")  # Trace config load
        self.auto_upgrade_uv = os.getenv("AUTO_UPGRADE_UV", "true").lower() == "true"  # Auto-upgrade UV manager itself
        self.auto_upgrade_dependencies = os.getenv("AUTO_UPGRADE_DEPENDENCIES", "true").lower() == "true"  # Auto deps
        self.upgrade_check_timeout = int(
            os.getenv("UPGRADE_CHECK_TIMEOUT", "30")
        )  # Seconds before giving up on a check
        self.csv_freshness_minutes = int(
            os.getenv("CSV_FRESHNESS_MINUTES", "15")
        )  # How long cached CSVs count as fresh
        self.uv_update_check_hours = int(os.getenv("UV_UPDATE_CHECK_HOURS", "24"))  # Throttle UV update checks to daily
        self.disable_uv_check = (
            os.getenv("DISABLE_UV_CHECK", "false").lower() == "true"
        )  # Skip all UV checks (container)
        self.disable_auto_install = os.getenv("DISABLE_AUTO_INSTALL", "false").lower() == "true"  # Skip auto-install

    def _initialize_dependency_tracking(self):  # Prepare package-tracking and import/UV caches
        """Initialize dependency-tracking containers and UV/deferred-init state flags."""
        logging.debug("Initializing dependency tracking containers and caches")  # Trace tracking setup
        self.required_packages = {}  # Will hold name -> spec for required packages
        self.optional_packages = {}  # Will hold name -> spec for optional packages
        self.failed_imports = []  # Names of packages that failed to import
        self.installed_packages = []  # Names of packages installed during this run
        self.imports = {}  # Cache of imported modules keyed by name for global reuse
        self._uv_available: bool = False  # Cached answer to 'is UV usable?'
        self._uv_checked: bool = False  # Whether the UV availability check has run yet
        self._last_uv_update_check: float | None = None  # Track when we last checked for UV updates
        self._deferred_init_done: bool = False  # Whether the deferred (lazy) init has run
        self._initialization_complete: bool = False  # Whether full initialization finished
        self._initialization_success: bool = False  # Whether initialization succeeded
        self._cached_global_assignments: dict[str, Any] = {}  # Module globals to publish once imports complete

    def _initialize_import_mappings(self):  # Build name maps and special import handlers
        """Build package->import name mappings and the special-case import handler table."""
        logging.debug("Initializing import name mappings and special handlers")  # Trace mapping setup
        self.import_name_mappings = {  # Map pip package names to import names where they differ
            "websocket-client": "websocket",  # websocket-client package provides websocket module
            "python-dotenv": "dotenv",  # python-dotenv package provides dotenv module
            "usaddress-scourgify": "scourgify",  # usaddress-scourgify package provides scourgify module
            "pillow": "PIL",  # Pillow package provides PIL module
            "beautifulsoup4": "bs4",  # beautifulsoup4 package provides bs4 module
            "pyyaml": "yaml",  # PyYAML package provides yaml module
            "python-dateutil": "dateutil",  # python-dateutil package provides dateutil module
            "msgpack-python": "msgpack",  # msgpack-python package provides msgpack module
        }
        self.special_import_handlers = {  # Map module names to custom import functions for tricky cases
            "concurrent.futures": self._import_concurrent_futures,  # Custom handler for concurrent.futures
            "datetime": self._import_datetime,  # Custom handler for datetime (avoids class shadowing)
            "tqdm": self._import_tqdm,  # Custom handler that swaps in the real tqdm
        }

    def _detect_virtual_environment(self) -> None:  # Determine and log whether a venv is active
        """Detect if we're running in a virtual environment and log info."""
        self.in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )  # venv when prefixes differ

        if self.in_venv:  # Running inside a virtual environment
            venv_path = getattr(sys, "prefix", "unknown")  # Path to the active venv
            logging.info("Running in virtual environment: %s", venv_path)  # Log the venv location
            logging.info("Python executable: %s", sys.executable)  # Log which interpreter is in use
        else:  # Running against the system Python
            logging.info("Running in system Python environment")  # Note the non-venv environment
            logging.info("Python executable: %s", sys.executable)  # Log which interpreter is in use

    def _setup_logging(self) -> None:  # Build console+file handlers with env-driven levels
        """Setup basic logging configuration with environment-specific levels."""
        console_log_level = int(os.environ.get("CONSOLE_LOG_LEVEL", logging.INFO))  # Console verbosity (default INFO)
        file_log_level = int(os.environ.get("LOGGING_LOG_LEVEL", logging.INFO))  # Log-file verbosity (default INFO)
        console_handler = self._build_console_log_handler(console_log_level)  # Build the console handler at env level
        file_handler = self._build_file_log_handler(file_log_level)  # Build the file handler (creates data/ if missing)
        logging.basicConfig(  # Wire up the root logger with both handlers
            level=logging.DEBUG,  # Root captures everything; handlers filter by their own levels
            format="%(asctime)s - %(levelname)s - %(message)s",  # Default format (handlers override with their own)
            handlers=[file_handler, console_handler],  # Register both the file and console handlers
            force=True,  # Replace the earlier module-import basicConfig
        )

    def _build_console_log_handler(self, level: int) -> logging.StreamHandler:  # Console handler factory
        """Build a stdout/stderr console log handler at the requested level."""
        logging.debug("_build_console_log_handler: creating console handler at level %s", level)  # Log before build
        console_handler = logging.StreamHandler()  # Handler that writes to stdout/stderr
        console_handler.setLevel(level)  # Apply the console verbosity threshold
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )  # Timestamped log line format
        console_handler.setFormatter(console_formatter)  # Attach the format to the console handler
        logging.debug("_build_console_log_handler: console handler ready")  # Log after build
        return console_handler  # Caller wires this into basicConfig

    def _build_file_log_handler(self, level: int) -> logging.FileHandler:  # File handler factory (data/script.log)
        """Build a data/script.log file handler at the requested level."""
        logging.debug("_build_file_log_handler: creating file handler at level %s", level)  # Log before build
        log_file_path = os.path.join("data", "script.log")  # Log path under data/ (writable in the container)
        os.makedirs("data", exist_ok=True)  # Create data/ if missing (no error if present)
        file_handler = logging.FileHandler(
            log_file_path, encoding="utf-8"
        )  # script.log writer; UTF-8 so non-cp1252 chars (e.g. Hawaiian 'okina) never crash logging
        file_handler.setLevel(level)  # Apply the file verbosity threshold
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  # Same timestamped format
        file_handler.setFormatter(file_formatter)  # Attach the format to the file handler
        logging.debug("_build_file_log_handler: file handler ready at %s", log_file_path)  # Log after build
        return file_handler  # Caller wires this into basicConfig

    def _define_package_requirements(self) -> None:  # Populate the required/optional package dictionaries
        """Define all required and optional package dependencies from class constants."""
        logging.debug("_define_package_requirements: loading spec maps from class constants")  # Log before copy
        self.required_packages = dict(self._REQUIRED_PACKAGES)  # Copy class-level required spec map (defensive copy)
        self.optional_packages = {  # Filter out any None specs defensively (platform-incompatible)
            k: v for k, v in self._OPTIONAL_PACKAGES_RAW.items() if v is not None
        }
        logging.debug(
            "_define_package_requirements: %d required, %d optional packages loaded",
            len(self.required_packages),
            len(self.optional_packages),
        )  # Log after copy with counts

    def _check_uv_installation(self) -> bool:  # Detect whether the UV package manager is usable (result cached)
        """Check if UV package manager is installed and accessible (cached)."""
        if self.disable_uv_check:  # Operator/container opted out of UV checks
            return False  # Treat UV as unavailable
        if self._uv_checked:  # We already probed UV earlier this run
            return self._uv_available  # Reuse the cached answer (avoids repeated subprocess calls)
        self._uv_available = self._probe_uv_binary()  # Probe via subprocess and cache the answer
        self._uv_checked = True  # Mark that we've probed UV so we don't repeat it
        return self._uv_available  # Return the (now cached) availability

    def _probe_uv_binary(self) -> bool:  # Run 'uv --version' to detect UV availability
        """Probe the UV binary by running 'uv --version' and log the outcome."""
        logging.debug("_probe_uv_binary: probing UV binary via subprocess")  # Log before probe
        try:  # Probing UV may fail if it's not installed
            result = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, timeout=10
            )  # nosec B603 B607  # Run 'uv --version'
            if result.returncode == 0:  # UV ran successfully
                logging.info("UV package manager found: %s", result.stdout.strip())  # Log detected version
                return True  # UV is usable
            logging.warning("UV package manager not found or not working properly")  # Note the problem
            return False  # UV is not usable
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:  # Missing/hung
            logging.warning("UV package manager check failed: %s", e)  # Log why the probe failed
            return False  # UV is not usable

    def _install_uv(self) -> bool:  # Attempt to install UV via pip when it's missing
        """Install UV package manager if not present."""
        if not self.auto_upgrade_uv:  # UV auto-management disabled by config
            logging.info("Auto-upgrade of UV is disabled in configuration")  # Note that we won't install UV
            return False  # Signal UV is unavailable

        logging.info("Attempting to install UV package manager...")  # Announce the install attempt
        try:  # The pip install may fail (no network, restricted env)
            # Try installing UV using pip as fallback
            result = subprocess.run(  # nosec B603  # Install uv via pip
                [sys.executable, "-m", "pip", "install", "uv"],  # pip install command for the current interpreter
                capture_output=True,  # Capture output for logging
                text=True,  # Decode output as text
                timeout=self.upgrade_check_timeout,  # Bound the install so startup can't hang
            )
            if result.returncode == 0:  # pip reported success
                logging.info("UV package manager installed successfully via pip")  # Confirm the install
                return True  # UV is now available
            else:  # pip returned an error
                logging.error("Failed to install UV via pip: %s", result.stderr)  # Log pip's error output
                return False  # UV remains unavailable
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:  # pip process hung or failed to launch
            logging.error("Failed to install UV package manager: %s", e)  # Log the exception
            return False  # UV remains unavailable

    def _upgrade_uv(self) -> bool:  # Keep UV up to date, throttled to once per configured interval
        """Upgrade UV package manager to latest version (only if needed)."""
        if not self.auto_upgrade_uv:  # UV auto-management disabled by config
            return True  # Nothing to do; treat as success
        now = time.time()  # Current timestamp used for throttling
        if self._uv_update_within_throttle(now):  # Still inside the throttle window
            return True  # No update needed yet
        return self._run_uv_self_update(now)  # Perform the (bounded) self-update attempt

    def _uv_update_within_throttle(self, now: float) -> bool:  # Decide if the UV update check is throttled
        """Return True when a UV update check ran recently enough to skip this one."""
        if not self._last_uv_update_check:  # No prior update-check time recorded
            return False  # Nothing to throttle against -- allow the check
        hours_since_last_check = (now - self._last_uv_update_check) / 3600  # Convert elapsed seconds to hours
        if hours_since_last_check < self.uv_update_check_hours:  # Still inside the throttle window
            logging.debug(  # Skip the check to avoid frequent network calls
                "UV update check skipped (last check %.1f hours ago, threshold: %s hours)",
                hours_since_last_check,
                self.uv_update_check_hours,
            )
            return True  # Throttled -- skip this update
        return False  # Throttle window elapsed -- allow the check

    def _run_uv_self_update(self, now: float) -> bool:  # Run 'uv self update', recording the attempt time
        """Attempt 'uv self update'; on failure, dispatch to the pip-fallback handler. Always non-fatal."""
        try:  # The update may fail; treat most failures as non-critical
            logging.info("Checking for UV package manager updates...")  # Announce the update check
            result = subprocess.run(  # nosec B603 B607  # Try uv's built-in self-update
                ["uv", "self", "update"],
                capture_output=True,
                text=True,
                timeout=self.upgrade_check_timeout,  # Bounded self-update call
            )
            self._last_uv_update_check = now  # Record this attempt so we honor the throttle next time
            if result.returncode == 0:  # Self-update succeeded
                logging.info("UV package manager updated successfully")  # Confirm the update
                return True  # Done
            return self._handle_uv_selfupdate_failure(result)  # Inspect stderr and try the pip fallback
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:  # Update process hung or failed to launch
            self._last_uv_update_check = now  # Record the attempt so we don't retry immediately
            logging.warning("UV self-update failed: %s", e)  # Log the exception
            return True  # Non-critical failure -- the current UV still works

    def _handle_uv_selfupdate_failure(self, result: Any) -> bool:  # Handle a non-zero 'uv self update' result
        """When self-update fails because UV was pip-installed, upgrade via pip; otherwise just log. Non-fatal."""
        pip_installed_marker = (  # Marker stderr emits when self-update isn't supported for this install method
            "Self-update is only available for uv binaries installed via the standalone installation scripts"
        )
        if pip_installed_marker not in result.stderr:  # Self-update failed for some other reason
            logging.warning("UV self-update returned non-zero: %s", result.stderr)  # Log the error
            return True  # Non-critical -- the current UV still works
        logging.info("UV was installed via pip, attempting pip upgrade...")  # Switch to the pip upgrade path
        pip_result = subprocess.run(  # nosec B603  # Upgrade uv via pip instead
            [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],  # pip upgrade command
            capture_output=True,  # Capture output for logging
            text=True,  # Decode output as text
            timeout=self.upgrade_check_timeout,  # Bound the upgrade
        )
        if pip_result.returncode == 0:  # pip upgrade succeeded
            logging.info("UV package manager updated successfully via pip")  # Confirm the upgrade
            return True  # Done
        logging.warning("Failed to upgrade UV via pip: %s", pip_result.stderr)  # Log the error
        return True  # Non-critical -- the current UV still works

    def _install_package_with_uv(self, package_spec: str) -> bool:
        """Install a package using UV package manager with fast resolution and virtual environment awareness."""
        try:
            logging.debug("Installing package with UV: %s", package_spec)  # Log which package is being installed
            uv_cmd = self._resolve_uv_binary()  # Pick venv-local UV when available, else PATH 'uv'
            first_cmd = self._build_uv_install_cmd(uv_cmd, package_spec, no_build_isolation=True)  # First attempt
            if self._attempt_uv_install(first_cmd, package_spec, fallback=False):  # First UV attempt succeeded
                return True  # Installation done
            logging.debug("UV install failed with --no-build-isolation, retrying without it")  # Note the retry
            retry_cmd = self._build_uv_install_cmd(uv_cmd, package_spec, no_build_isolation=False)  # Retry sans flag
            return self._attempt_uv_install(retry_cmd, package_spec, fallback=True)  # Fallback attempt (logs stderr)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:  # UV hung or failed to launch
            logging.warning("Failed to install %s with UV: %s", package_spec, e)  # Log the exception detail
            return False  # Signal failure so the caller can fall back to pip

    def _attempt_uv_install(self, cmd: list[str], package_spec: str, *, fallback: bool) -> bool:  # One UV install try
        """Run one UV install attempt; on success log+return True. On failure return False (logs stderr if fallback)."""
        result = subprocess.run(  # nosec B603  # Execute the UV install (trusted, fixed argv)
            cmd,  # The assembled UV command
            capture_output=True,  # Capture stdout/stderr for logging and fallback detection
            text=True,  # Decode output as text rather than bytes
            timeout=self.upgrade_check_timeout,  # Bound the install so it can't hang forever
        )
        if result.returncode == 0:  # UV reported a successful install
            label = "UV (fallback)" if fallback else "UV"  # Distinguish the first attempt from the retry in the log
            logging.info("Successfully installed %s with %s", package_spec, label)  # Confirm success
            return True  # Installation done
        if fallback:  # Only the final (fallback) attempt surfaces the UV error output
            logging.warning("UV install failed for %s: %s", package_spec, result.stderr)  # Log the UV error output
        return False  # This attempt did not install the package

    def _resolve_uv_binary(self) -> str:  # Choose which UV binary to invoke
        """Return the venv-local UV binary when running inside a venv that ships one, else PATH 'uv'."""
        if not (hasattr(self, "in_venv") and self.in_venv):  # Not running inside a virtual environment
            return "uv"  # Use the UV binary found on PATH
        venv_uv = os.path.join(os.path.dirname(sys.executable), "uv.exe")  # Build the venv-local UV path
        if os.path.exists(venv_uv):  # The venv ships its own UV binary
            logging.debug("Using venv UV: %s", venv_uv)  # Record which UV binary was chosen
            return venv_uv  # Prefer the venv's UV to stay environment-consistent
        return "uv"  # venv has no local UV -- fall back to PATH 'uv'

    def _build_uv_install_cmd(self, uv_cmd: str, package_spec: str, no_build_isolation: bool) -> list[str]:  # UV argv
        """Assemble the 'uv pip install' argv: pin to this interpreter in a venv; add --no-build-isolation if set."""
        cmd = [uv_cmd, "pip", "install"]  # Base UV install command
        if hasattr(self, "in_venv") and self.in_venv:  # Inside a venv -- pin the install to this interpreter
            cmd += ["--python", sys.executable]  # Target the current Python explicitly
        if no_build_isolation:  # First attempt requests no build isolation (faster, fewer surprises)
            cmd.append("--no-build-isolation")  # Disable build isolation for this attempt
        cmd.append(package_spec)  # The package to install (with any version constraint)
        return cmd  # Completed UV argv

    def _install_package_with_pip(self, package_spec: str) -> bool:
        """Install a package using pip as fallback with virtual environment awareness."""
        try:
            logging.info("Installing package with pip: %s", package_spec)  # Log the pip install attempt
            # Always use the current Python executable to ensure installation in the right environment
            result = subprocess.run(  # nosec B603  # Run pip against this exact interpreter (trusted argv)
                [sys.executable, "-m", "pip", "install", package_spec],  # Invoke pip as a module of this Python
                capture_output=True,  # Capture output for success/failure logging
                text=True,  # Decode output as text
                timeout=self.upgrade_check_timeout,  # Bound the install so it can't hang forever
            )
            if result.returncode == 0:  # pip reported a successful install
                logging.info("Successfully installed %s with pip", package_spec)  # Confirm success
                return True  # Installation done
            else:  # pip install failed
                logging.error(
                    "Failed to install %s with pip: %s", package_spec, result.stderr
                )  # Log pip's error output
                return False  # Signal failure to the caller
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:  # pip hung or failed to launch
            logging.error("Failed to install %s with pip: %s", package_spec, e)  # Log the exception detail
            return False  # Signal failure to the caller

    def _should_check_uv_update(self) -> bool:
        """Check if we should check for UV updates based on time since last check."""
        if not self.auto_upgrade_uv:  # UV auto-upgrade is disabled by configuration
            return False  # Never check when the feature is off

        if self._last_uv_update_check is None:  # No prior check has ever run this session
            return True  # Force an initial check

        time_since_check = time.time() - self._last_uv_update_check  # Seconds elapsed since the last check
        hours_since_check = time_since_check / 3600  # Convert elapsed seconds to hours
        return hours_since_check >= self.uv_update_check_hours  # Check again only after the configured interval

    def _check_uv_needs_update(self) -> bool:
        """Check if UV actually needs an update by comparing versions."""
        try:
            # Get current UV version
            result = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, timeout=5
            )  # nosec B603 B607  # Query installed UV version
            if result.returncode != 0:  # UV is missing or failed to report its version
                return False  # Can't determine an update is needed

            # For now, we'll assume UV is up to date since checking remote version is complex
            # In a production environment, you might want to implement version comparison
            logging.debug("UV version check complete - assuming current version is adequate")  # Note the no-op result
            return False  # Treat UV as up to date (remote comparison not implemented)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):  # Version probe hung or failed to launch
            return False  # Assume no update needed when the probe fails

    def _upgrade_all_dependencies(self) -> bool:
        """Install missing dependencies and upgrade existing ones."""
        if not self.auto_upgrade_dependencies:  # Auto-upgrade disabled by configuration
            logging.info("Auto-upgrade of dependencies is disabled in configuration")  # Note the skip
            return True  # Nothing to do; treat as success
        packages_to_process = self._collect_packages_to_process()  # (name, spec) pairs, built-ins excluded
        if not packages_to_process:  # Caller supplied an empty work list
            logging.info("No packages to process")  # Note there is nothing to do
            return True  # Success by default -- no work means no failures
        logging.info("Processing %s packages...", len(packages_to_process))  # Announce how many will be handled
        success_count = self._install_dependency_batch(packages_to_process)  # Install each, counting successes
        logging.info("Successfully processed %s/%s packages", success_count, len(packages_to_process))  # Summarize
        return success_count > 0  # Report success if at least one package installed

    def _install_dependency_batch(self, packages_to_process: list[tuple[str, str]]) -> int:  # Install a batch
        """Install each (name, spec) package via the best backend; return the count that installed successfully."""
        uv_available = self._check_uv_installation()  # Detect whether UV can be used as the fast installer
        logging.info(  # Record which installer backend will be used
            "Using UV package manager for installations"
            if uv_available
            else "Using pip for package installations (UV not available)"
        )
        success_count = 0  # Track how many packages installed successfully
        for _pkg_name, pkg_spec in packages_to_process:  # Install each package, counting successes
            if self._install_one_dependency(pkg_spec, uv_available):  # UV-then-pip attempt for this package
                success_count += 1  # Count this package as done
        return success_count  # Number of packages that installed successfully

    def _collect_packages_to_process(self) -> list[tuple[str, str]]:  # Build the installable (name, spec) list
        """Return (name, spec) pairs for required+optional packages, excluding built-in modules (spec is None)."""
        packages_to_process = []  # Accumulate installable (name, spec) pairs
        for pkg_name, pkg_spec in {**self.required_packages, **self.optional_packages}.items():  # Walk all packages
            if pkg_spec is not None:  # Skip built-in modules (no version spec)
                packages_to_process.append((pkg_name, pkg_spec))  # Keep this installable package
        return packages_to_process  # The filtered work list

    def _install_one_dependency(self, pkg_spec: str, uv_available: bool) -> bool:  # Install one package (UV then pip)
        """Install one package: try UV first when available, then fall back to pip. Errors are non-fatal."""
        try:  # Per-package failures must not abort the whole batch
            if uv_available and self._install_package_with_uv(pkg_spec):  # Fast UV path succeeded
                return True  # Installed via UV
            if self._install_package_with_pip(pkg_spec):  # pip fallback (or UV unavailable) succeeded
                return True  # Installed via pip
            logging.warning("Failed to install/upgrade %s", pkg_spec)  # Both paths failed -- warn, keep going
            return False  # This package did not install
        except Exception as e:  # Any unexpected error during install of this package
            logging.warning("Error processing package %s: %s", pkg_spec, e)  # Log and continue with remaining packages
            return False  # Treat as a failed package

    def _import_concurrent_futures(self) -> Any:
        """Special handler for concurrent.futures import."""
        from concurrent.futures import ThreadPoolExecutor, as_completed  # Import the thread-pool primitives on demand

        return type(
            "ConcurrentFutures", (), {"ThreadPoolExecutor": ThreadPoolExecutor, "as_completed": as_completed}
        )()  # Bundle them on a tiny namespace object

    class _DateTimeHandler:  # Adapter exposing both class-like and module-like datetime access
        """Adapter exposing both class-like and module-like datetime access."""

        def __init__(self) -> None:
            from datetime import datetime, timedelta  # Local import keeps handler self-contained

            self._datetime_cls = datetime  # Capture class for __call__ forwarding
            self.now = datetime.now  # Expose datetime.now() at the top level
            self.fromtimestamp = datetime.fromtimestamp  # Expose epoch->datetime conversion
            self.fromisoformat = datetime.fromisoformat  # Expose ISO-8601 string parsing
            self.strptime = datetime.strptime  # Expose format-string parsing
            # Preserve legacy naive-UTC behavior without calling the deprecated datetime.utcnow.
            # Expose UTC now() helper as naive UTC (legacy contract).
            self.utcnow = lambda: datetime.now(UTC).replace(tzinfo=None)
            self.datetime = datetime  # Allow handler.datetime to reach the real class
            self.timezone = timezone  # Provide timezone for tz-aware construction
            self.timedelta = timedelta  # Provide timedelta for date arithmetic

        def __call__(self, *args, **kwargs):
            return self._datetime_cls(*args, **kwargs)  # Forward calls to the datetime constructor

    def _import_datetime(self) -> Any:
        """Special handler for datetime import."""
        logging.debug("_import_datetime: returning _DateTimeHandler adapter")  # Log before construction
        return self._DateTimeHandler()  # Hand back the dual-purpose adapter

    def _import_tqdm(self) -> Any:
        """Special handler for tqdm import to ensure proper functionality."""
        try:
            from tqdm import tqdm  # Attempt to import the real progress-bar library

            logging.debug("Successfully imported tqdm from package")  # Note the real library is available
            return tqdm  # Use the genuine tqdm progress bar
        except ImportError:  # tqdm is not installed
            logging.warning("tqdm package not available, using fallback")  # Warn and degrade gracefully

            # Return the fallback function if tqdm is not available
            def tqdm_fallback(iterable, *args, **kwargs):
                """Fallback when tqdm package is not available."""
                desc = kwargs.get("desc", "Processing")  # Description label for the log line
                unit = kwargs.get("unit", "item")  # Unit noun for the progress message
                if hasattr(iterable, "__len__"):  # The iterable has a known length
                    total = len(iterable)  # Compute total item count for the message
                    logging.info("%s: %s %ss to process", desc, total, unit)  # Log a one-shot progress summary
                else:  # Length is unknown (e.g. a generator)
                    logging.info("%s: processing %ss...", desc, unit)  # Log an indefinite progress message
                return iterable  # Pass the iterable through unchanged (no live bar)

            return tqdm_fallback  # Provide the no-op progress shim to callers

    def _check_and_upgrade_package(self, module_name: str, package_spec: str) -> bool:
        """Check if a package needs upgrading and upgrade it if necessary. Always non-fatal (returns True)."""
        if not package_spec:  # No version spec provided (e.g. a stdlib module)
            return True  # Built-in modules don't need upgrading
        try:  # Upgrade problems must never block startup
            package_name = self._bare_package_name(package_spec)  # Strip version operators to the bare name
            result = self._run_pip_show(package_name)  # Ask pip what version is currently installed
            if result.returncode != 0:  # pip could not find the package
                logging.debug("Package %s not found, skipping upgrade check", package_name)  # Nothing to upgrade
                return True  # Treat as success -- not an error condition
            current_version = self._parse_pip_show_version(result.stdout)  # Parse the installed version
            if not current_version:  # Could not determine the installed version
                return True  # Treat as non-fatal -- nothing reliable to upgrade against
            logging.debug("Current version of %s: %s", package_name, current_version)  # Record the current version
            logging.info("  Checking for updates to %s...", package_name)  # Inform the user an upgrade check is running
            return self._upgrade_and_verify(package_name, package_spec, current_version)  # Upgrade + report
        except Exception as e:  # Any unexpected error during the check/upgrade
            logging.debug("Error checking/upgrading %s: %s", module_name, e)  # Log for diagnostics
            return True  # Non-critical failure -- never block startup on upgrade issues

    @staticmethod
    def _bare_package_name(package_spec: str) -> str:  # Strip version operators from a package spec
        """Return the bare package name from a spec (e.g. 'requests>=2.28.0' -> 'requests')."""
        return package_spec.split(">=")[0].split("==")[0].split("<")[0].split(">")[0].strip()  # Drop any constraint

    def _run_pip_show(self, package_name: str) -> Any:  # Query pip for a package's metadata
        """Run 'pip show <package_name>' for this interpreter with captured text output (10s timeout)."""
        return subprocess.run(  # nosec B603  # Ask pip about the installed package (trusted, fixed argv)
            [sys.executable, "-m", "pip", "show", package_name],  # pip show for this interpreter
            capture_output=True,  # Capture stdout for version parsing
            text=True,  # Decode output as text
            timeout=10,  # Bound the metadata query
        )

    @staticmethod
    def _parse_pip_show_version(pip_show_stdout: str) -> str | None:  # Extract the Version: field from pip show
        """Return the value of the 'Version:' line in pip show output, or None when absent."""
        for line in pip_show_stdout.split("\n"):  # Scan each line of pip show output
            if line.startswith("Version:"):  # Found the version field
                return line.split(":", 1)[1].strip()  # Extract and return the version value
        return None  # No Version: line present

    def _build_upgrade_cmd(self, package_spec: str) -> list[str]:  # Assemble the upgrade argv (UV or pip)
        """Build the '--upgrade' argv: UV (venv-pinned when applicable) when UV is installed, else pip."""
        if not self._check_uv_installation():  # UV unavailable -- upgrade via pip
            return [sys.executable, "-m", "pip", "install", "--upgrade", package_spec]  # pip upgrade for this Python
        cmd = [self._resolve_uv_binary(), "pip", "install"]  # UV base command (venv-local UV when present)
        if hasattr(self, "in_venv") and self.in_venv:  # Inside a venv -- pin the upgrade to this interpreter
            cmd += ["--python", sys.executable]  # Target the current Python explicitly
        cmd += ["--upgrade", package_spec]  # Upgrade the requested package
        return cmd  # Completed UV upgrade argv

    def _upgrade_and_verify(self, package_name: str, package_spec: str, current_version: str) -> bool:  # Run + verify
        """Run the upgrade command and log whether the version advanced. Always non-fatal (returns True)."""
        upgrade_result = subprocess.run(  # nosec B603  # Execute the chosen upgrade command
            self._build_upgrade_cmd(package_spec),  # UV or pip upgrade argv
            capture_output=True,  # Capture output for logging
            text=True,  # Decode output as text
            timeout=self.upgrade_check_timeout,  # Bound the upgrade so it can't hang
        )
        if upgrade_result.returncode != 0:  # The upgrade command failed
            logging.debug("  [WARN] %s: Upgrade check failed: %s", package_name, upgrade_result.stderr)  # Log detail
            return True  # Non-critical failure -- continue without blocking startup
        new_version = self._parse_pip_show_version(self._run_pip_show(package_name).stdout)  # Re-query post-upgrade
        if new_version and new_version != current_version:  # The version actually advanced
            logging.info("  [OK] %s: Upgraded from %s to %s", package_name, current_version, new_version)  # Report it
        else:  # Version did not change
            logging.debug("  [OK] %s: Already up to date (%s)", package_name, current_version)  # Already current
        return True  # Upgrade path is always non-fatal

    # _get_actual_import_name removed per issue #431 (ARCH-DELEGATE) -- callers
    # now do `self.import_name_mappings.get(name, name)` inline.

    def _resolve_and_import(self, module_name: str) -> Any:
        """Import a module via its special handler or its real import name (issue #470: shared by attempt + retry)."""
        if module_name in self.special_import_handlers:  # Some modules need custom construction logic.
            return self.special_import_handlers[module_name]()  # Invoke special handler.
        actual_import_name = self.import_name_mappings.get(module_name, module_name)  # Resolve package -> import name.
        return __import__(actual_import_name)  # Import the module by its real import name.

    def _should_upgrade_package(self, package_spec: str | None, skip_deps: bool, skip_upgrade: bool) -> bool:
        """Return True only when every opportunistic-upgrade gate passes (issue #470: hoisted to keep CC low)."""
        return bool(
            package_spec and self.auto_upgrade_dependencies and not skip_deps and not skip_upgrade
        )  # All four upgrade gates must pass before an opportunistic upgrade.

    def _auto_install_allowed(self, package_spec: str | None, skip_deps: bool) -> bool:
        """Return True only when auto-installing a missing dependency is permitted (issue #470: hoisted gate)."""
        return bool(
            package_spec and self.auto_upgrade_dependencies and not skip_deps and not self.disable_auto_install
        )  # All four install gates must pass before attempting an install.

    def _attempt_install(self, package_spec: str) -> bool:
        """Install a package, preferring UV then falling back to pip; return True if either succeeded."""
        installed = False  # Track whether any installer succeeded.
        if self._check_uv_installation():  # UV is the preferred fast installer.
            logging.debug("Trying UV installation for %s", package_spec)  # Note the UV attempt.
            installed = self._install_package_with_uv(package_spec)  # Attempt the UV install.
        if not installed:  # UV either failed or is unavailable.
            logging.debug("Trying pip installation for %s", package_spec)  # Note the pip attempt.
            installed = self._install_package_with_pip(package_spec)  # Attempt the pip install.
        return installed  # Report whether the package is now installed.

    def _clear_failed_import_cache(self, module_name: str) -> None:
        """Invalidate import caches and purge stale failed entries so a post-install retry imports cleanly."""
        import importlib  # Imported locally to invalidate caches only when needed.

        importlib.invalidate_caches()  # Force Python to notice the newly installed files.
        actual_import_name = self.import_name_mappings.get(module_name, module_name)  # Resolve package -> import name.
        for mod_name in (actual_import_name, module_name):  # Both names may be cached as failed.
            if mod_name in sys.modules:  # A stale/failed entry exists in the module cache.
                del sys.modules[mod_name]  # Remove it so the retry re-imports cleanly.
                logging.debug("Cleared cached module: %s", mod_name)  # Record the cache purge.

    def _retry_import_after_install(self, module_name: str, package_spec: str, required: bool) -> Any | None:
        """Re-import a module after a successful install; return it, or None if the import still fails."""
        try:  # The install may still not satisfy the import in this Python session.
            module = self._resolve_and_import(module_name)  # Re-import now that the package is installed.
            self.imports[module_name] = module  # Cache the now-successful import.
            self.installed_packages.append(package_spec)  # Record that we installed this package this run.
            logging.info("Successfully imported %s after installation", module_name)  # Confirm recovery.
            return module  # Return the freshly imported module.
        except ImportError as retry_e:  # Import still fails even after a successful install.
            logging.error("Import still failed after installation for %s: %s", module_name, retry_e)  # Log failure.
            if not required:  # Optional dependency -- degrade gracefully.
                logging.info(
                    "Optional package %s installation succeeded but import failed - likely needs system restart or different Python session",  # noqa: E501
                    module_name,
                )
            return None  # The retry import did not succeed.

    def _install_and_retry(
        self, module_name: str, package_spec: str | None, required: bool, skip_deps: bool
    ) -> Any | None:
        """Install a missing dependency (when permitted) and retry the import; return the module or None."""
        if not self._auto_install_allowed(package_spec, skip_deps):  # Auto-install must be permitted.
            return None  # Installation not allowed -- nothing to retry.
        assert package_spec is not None  # _auto_install_allowed rejects None; narrow for type-checker.
        logging.info("Attempting to install missing dependency: %s", package_spec)  # Announce the install attempt.
        if not self._attempt_install(package_spec):  # No installer succeeded.
            logging.error("Failed to install %s", package_spec)  # Report the install failure.
            return None  # Cannot retry without a successful install.
        self._clear_failed_import_cache(module_name)  # Purge stale caches before the retry.
        time.sleep(0.5)  # Brief pause to let filesystem writes settle before retrying.
        return self._retry_import_after_install(module_name, package_spec, required)  # Retry.

    def _record_import_failure(self, module_name: str, required: bool) -> None:
        """Record a terminal import failure (hard error for required deps, warning for optional)."""
        if required:  # This dependency is mandatory for the program to run.
            self.failed_imports.append(module_name)  # Track it among hard failures.
            logging.error("Required dependency %s could not be imported or installed", module_name)  # Hard error.
        else:  # Optional dependency.
            logging.warning("Optional dependency %s not available", module_name)  # Warn but allow continuation.

    def import_module_safely(
        self,
        module_name: str,
        package_spec: str | None = None,
        required: bool = True,
        skip_deps: bool = False,
        skip_upgrade: bool = True,
    ) -> Any | None:
        """Import a module, install on ImportError, and opportunistically upgrade."""
        try:  # First import attempt before any install fallback.
            module = self._resolve_and_import(module_name)  # Import via special handler or real import name.
            self._record_successful_import(module, module_name, package_spec, skip_deps, skip_upgrade)  # Cache+upgrade
            return module  # Hand the imported module back to the caller.
        except ImportError as e:  # The module is not installed or failed to load.
            logging.warning("Failed to import %s: %s", module_name, e)  # Note the import failure.
            module = self._install_and_retry(module_name, package_spec, required, skip_deps)  # Try install + retry.
            if module is not None:  # The install-and-retry recovered the import.
                return module  # Return the recovered module.
            self._record_import_failure(module_name, required)  # Record terminal failure (logs required/optional).
            return None  # Signal to the caller that the import was unavailable.

    def _record_successful_import(
        self,
        module: Any,
        module_name: str,
        package_spec: str | None,
        skip_deps: bool,
        skip_upgrade: bool,
    ) -> None:
        """Cache an imported module and run the opportunistic upgrade check."""
        logging.debug("_record_successful_import: caching '%s' and checking upgrade", module_name)  # Log before
        self.imports[module_name] = module  # Cache the imported module for later global assignment.
        logging.debug("Successfully imported %s", module_name)  # Record the successful import.
        if self._should_upgrade_package(package_spec, skip_deps, skip_upgrade):  # Opportunistic upgrade gate.
            assert package_spec is not None  # _should_upgrade_package rejects None; narrow for type-checker.
            self._check_and_upgrade_package(module_name, package_spec)  # Upgrade package.

    def _partition_dependencies(self, packages_dict):
        """Split a package map into (builtin, external) dicts by whether a spec is present."""
        logging.debug("_partition_dependencies: splitting %d packages", len(packages_dict))  # Log before split
        builtin_packages = {k: v for k, v in packages_dict.items() if v is None}  # No spec -> stdlib/built-in module
        external_packages = {k: v for k, v in packages_dict.items() if v is not None}  # Has spec -> needs install
        return builtin_packages, external_packages  # Return the two cohesive groups for separate processing

    def _import_single_dependency(self, package_info, required, skip_deps, log_lock):
        """Import one package and log its check and outcome under the shared thread lock."""
        module_name, package_spec = package_info  # Unpack the (name, spec) tuple for this worker
        package_type = "required" if required else "optional"  # Label used in user-facing log lines
        with log_lock:  # Serialize this log line against other worker threads
            logging.info(
                "  Checking %s dependency: %s (%s)", package_type, module_name, package_spec or "built-in"
            )  # Announce the check
        result = self.import_module_safely(  # Perform the actual import/install for this package
            module_name, package_spec, required=required, skip_deps=skip_deps, skip_upgrade=True
        )  # Skip upgrade for speed here
        with log_lock:  # Serialize the result log line against other worker threads
            self._log_dependency_result(module_name, result, required)  # Emit OK/FAIL/WARN for this package
        return module_name, result  # Return the outcome for aggregation by the caller

    def _log_dependency_result(self, module_name, result, required):
        """Log a single dependency outcome as OK, hard FAIL (required), or soft WARN (optional)."""
        if result:  # Import succeeded
            logging.info("  [OK] %s: Available", module_name)  # Report availability
        elif required:  # Mandatory dependency missing
            logging.error("  [FAIL] %s: Failed to import", module_name)  # Log a hard failure
        else:  # Optional dependency missing
            logging.warning("  [WARN] %s: Not available", module_name)  # Log a soft warning

    def _import_external_dependencies(self, external_packages, required, skip_deps, log_lock, max_workers):
        """Import external packages concurrently with a bounded thread pool."""
        logging.debug("_import_external_dependencies: importing %d external packages", len(external_packages))  # Log
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:  # Bounded import worker pool
            future_to_package = {  # Map each submitted future back to its source package
                executor.submit(self._import_single_dependency, item, required, skip_deps, log_lock): item
                for item in external_packages.items()  # Schedule every external import
            }
            for future in concurrent.futures.as_completed(future_to_package):  # Process results as imports finish
                self._collect_import_result(future, future_to_package, log_lock)  # Handle this future's outcome

    def _collect_import_result(self, future, future_to_package, log_lock):
        """Retrieve one import future's result, logging any worker exception under the lock."""
        package_info = future_to_package[future]  # Recover which package this future handled
        try:
            future.result()  # Retrieve the worker's return value (re-raises worker errors)
        except Exception as exc:  # A worker raised an unexpected exception
            with log_lock:  # Serialize the error log line against other worker threads
                logging.error("Package %s import generated an exception: %s", package_info[0], exc)  # Log the failure

    def _import_packages_concurrently(self, packages_dict, required=True, skip_deps=False, max_workers=4):
        """
        Import packages concurrently for faster dependency resolution.

        Args:
            packages_dict: Dictionary of package_name: package_spec
            required: Whether these are required (True) or optional (False) packages
            skip_deps: Whether to skip dependency installation
            max_workers: Maximum number of concurrent workers
        """
        log_lock = threading.Lock()  # Guards logging so concurrent threads don't interleave messages
        builtin_packages, external_packages = self._partition_dependencies(packages_dict)  # Split by spec presence
        for item in builtin_packages.items():  # Built-ins import instantly with no network needed
            self._import_single_dependency(item, required, skip_deps, log_lock)  # Import each sequentially
        if external_packages:  # Only spin up a thread pool if there is network work to do
            self._import_external_dependencies(external_packages, required, skip_deps, log_lock, max_workers)  # Pool

    def initialize_all_imports(
        self,
        skip_deps: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Initialize all imports and dependencies upfront.

        Args:
            skip_deps: Skip dependency checking and installation

        Returns:
            Tuple of (success: bool, global_assignments: dict)
        """
        from src.refactors.serial_cc.import_initialization_service import ImportInitializationService

        return ImportInitializationService.execute(self, skip_deps=skip_deps)

    def _get_global_assignments(self):
        """Get dictionary of global variable assignments for imported modules."""
        from src.refactors.serial_cc.global_assignments_builder import GlobalAssignmentsBuilderService

        return GlobalAssignmentsBuilderService.execute(self.imports, self._add_fallbacks_to_globals)

    # Simple module -> [(global_name, attr_name_or_None)] hoists. attr None binds the module object itself.
    # Used by _hoist_module_globals so _make_modules_global stays a flat loop instead of a long if/elif chain.
    _SIMPLE_GLOBAL_HOISTS = {
        "datetime": [("timezone", "timezone"), ("timedelta", "timedelta")],  # Hoist datetime's tz/delta helpers
        "concurrent.futures": [  # Hoist the thread-pool primitives plus the package itself
            ("ThreadPoolExecutor", "ThreadPoolExecutor"),
            ("as_completed", "as_completed"),
            ("concurrent", None),
        ],
        "prettytable": [("PrettyTable", "PrettyTable")],  # Hoist the PrettyTable class
        "numpy": [("np", None)],  # Bind numpy under its conventional alias np
        "tqdm": [("tqdm", None)],  # Bind tqdm by name for progress bars
        "collections": [("defaultdict", "defaultdict")],  # Bind defaultdict directly
        "difflib": [("SequenceMatcher", "SequenceMatcher")],  # Bind SequenceMatcher directly
    }

    def _make_modules_global(self):
        """Make all successfully imported modules available in the global namespace."""
        for module_name, module_obj in self.imports.items():  # Walk every imported module
            globals()[module_name] = module_obj  # Bind the module into the real module globals
            self._hoist_module_globals(module_name, module_obj)  # Hoist any commonly-used attributes for it
        logging.debug("Successfully made imported modules available globally")  # Confirm the global wiring completed

    def _hoist_module_globals(self, module_name, module_obj):  # Hoist known helper attributes into globals
        """Hoist commonly-used attributes of a known module into globals (data-driven, with optional-pkg cases)."""
        simple_hoists = self._SIMPLE_GLOBAL_HOISTS.get(module_name)  # Lookup the simple hoist list for this module
        if simple_hoists:  # This module has a fixed set of attributes to hoist
            self._apply_simple_hoists(module_obj, simple_hoists)  # Bind each (global_name, attr) pair
        elif module_name == "usaddress-scourgify":  # Optional address-normalization package needs custom handling
            self._hoist_scourgify_global(module_obj)  # Bind its normalize function (with direct-import fallback)
        elif module_name == "rapidfuzz":  # Optional fuzzy-matching package needs custom handling
            self._hoist_rapidfuzz_global(module_obj)  # Bind its fuzz submodule (with direct-import fallback)

    @staticmethod
    def _apply_simple_hoists(module_obj, hoists):  # Bind a module's fixed (global_name, attr) pairs into globals
        """Bind each (global_name, attr_name) pair: attr None binds the module object, else getattr(module, attr)."""
        for global_name, attr_name in hoists:  # Apply each configured binding for this module
            value = module_obj if attr_name is None else getattr(module_obj, attr_name, None)  # Module or its attribute
            globals()[global_name] = value  # Bind the resolved value into the real module globals

    @staticmethod
    def _hoist_scourgify_global(module_obj):  # Bind scourgify's normalize_address_record into globals
        """Hoist scourgify.normalize_address_record into globals, importing it directly when not an attribute."""
        if not module_obj:  # Package did not load
            return  # Nothing to hoist
        try:  # The function may be an attribute or require a direct import
            normalize_func = getattr(module_obj, "normalize_address_record", None)  # Look for the normalize function
            if not normalize_func:  # Attribute missing -- import directly from scourgify
                from scourgify import normalize_address_record  # Direct import fallback

                normalize_func = normalize_address_record  # Rebind the direct-import result
            globals()["normalize_address_record"] = normalize_func  # Bind the resolved function globally
        except (ImportError, AttributeError):  # Package present but function unavailable
            logging.debug("Could not import normalize_address_record from scourgify, using fallback")  # Note fallback

    @staticmethod
    def _hoist_rapidfuzz_global(module_obj):  # Bind rapidfuzz's fuzz submodule into globals
        """Hoist rapidfuzz.fuzz into globals, importing it directly when not an attribute."""
        if not module_obj:  # Package did not load
            return  # Nothing to hoist
        try:  # The submodule may be an attribute or require a direct import
            fuzz_module = getattr(module_obj, "fuzz", None)  # Look for the fuzz submodule attribute
            if not fuzz_module:  # Attribute missing -- import directly from rapidfuzz
                from rapidfuzz import fuzz as fuzz_module  # Direct import fallback
            globals()["fuzz"] = fuzz_module  # Bind the resolved fuzz module globally
        except (ImportError, AttributeError):  # Package present but submodule unavailable
            logging.debug("Could not import fuzz from rapidfuzz, using fallback")  # Note the fallback

    def _add_fallbacks_to_globals(self, global_vars):
        """Add fallbacks for optional modules that failed to import."""
        self._install_scourgify_fallback(global_vars)  # Address-normalization shim when scourgify is missing
        self._install_fuzz_fallback(global_vars)  # Fuzzy-match shim (difflib-backed) when rapidfuzz is missing
        self._install_ssh_fallbacks(global_vars)  # paramiko/redexpect shims that fail loudly with install guidance

    @staticmethod
    def _install_scourgify_fallback(global_vars):  # Install the scourgify normalize fallback when absent
        """When normalize_address_record is missing, install a shim returning the raw string with empty fields."""
        if global_vars.get("normalize_address_record") is not None:  # A real normalizer is already present
            return  # No fallback needed

        def normalize_address_record_fallback(address_string):
            """Fallback function when scourgify is not available."""
            logging.debug("Using fallback address normalization (scourgify not available)")  # Note the degraded path
            return {
                "address_line_1": address_string,
                "city": "",
                "state": "",
                "zip": "",
                "country": "",
            }  # Return the raw string with empty fields

        global_vars["normalize_address_record"] = normalize_address_record_fallback  # Install the shim by name

    @staticmethod
    def _install_fuzz_fallback(global_vars):  # Install the rapidfuzz fallback when absent
        """When fuzz is missing, install a difflib-backed shim exposing token_sort_ratio (0-100 score)."""
        if global_vars.get("fuzz") is not None:  # A real fuzzy matcher is already present
            return  # No fallback needed

        class FuzzFallback:
            """Fallback class when rapidfuzz is not available."""

            @staticmethod
            def token_sort_ratio(str1, str2):
                """Fallback using difflib SequenceMatcher."""
                if global_vars.get("difflib"):  # Use difflib if it is available as a substitute
                    return int(
                        global_vars["difflib"].SequenceMatcher(None, str1, str2).ratio() * 100
                    )  # Convert 0-1 ratio to a 0-100 score
                return 0  # No comparison library at all -- report no similarity

        global_vars["fuzz"] = FuzzFallback()  # Install the fuzzy-match shim under the expected name

    @classmethod
    def _install_ssh_fallbacks(cls, global_vars):  # Install paramiko/redexpect shims that fail loudly when used
        """Install paramiko and redexpect shims that raise ImportError with install guidance when accessed."""
        cls._install_paramiko_fallback(global_vars)  # SSH client shim when paramiko is absent
        cls._install_redexpect_fallback(global_vars)  # SSH automation shim when redexpect is absent

    @staticmethod
    def _install_paramiko_fallback(global_vars):  # Install a paramiko shim that errors on use
        """When paramiko is missing, install a shim whose SSHClient() raises ImportError with install guidance."""
        if global_vars.get("paramiko") is not None:  # paramiko (or an existing shim) is already present
            return  # No fallback needed

        class SSHFallback:
            """Fallback class when paramiko is not available."""

            @staticmethod
            def SSHClient():
                raise ImportError(  # Fail loudly with install guidance when SSH is attempted without paramiko
                    "SSH functionality requires 'paramiko' package. Install with: pip install paramiko"
                )

        global_vars["paramiko"] = SSHFallback()  # Install the SSH shim with a clear error path

    @staticmethod
    def _install_redexpect_fallback(global_vars):  # Install a redexpect shim that errors on use
        """When redexpect is missing, install a shim whose spawn() raises ImportError with install guidance."""
        if global_vars.get("redexpect") is not None:  # redexpect (or an existing shim) is already present
            return  # No fallback needed

        class RedexpectFallback:
            """Fallback class when redexpect is not available."""

            @staticmethod
            def spawn(*args, **kwargs):
                raise ImportError(  # Fail loudly with install guidance when redexpect is used but absent
                    "Cross-platform SSH automation requires 'redexpect' package. Install with: pip install redexpect"  # noqa: E501
                )

        global_vars["redexpect"] = RedexpectFallback()  # Install the redexpect shim with a clear error path

    def _import_special_modules(self):
        """Import special modules with custom handling."""
        logging.debug("_import_special_modules: wiring mistapi + websocket-client")  # Log before wiring
        self._wire_mistapi_module()  # Bind mistapi to module globals if it loaded
        self._log_websocket_availability()  # Log whether the websocket client is usable

    def _wire_mistapi_module(self):
        """Wire mistapi to module globals and confirm its API structure."""
        if "mistapi" not in self.imports:  # The base SDK never imported
            logging.debug("mistapi not imported, skipping sub-module imports")  # Nothing to wire up
            return  # No work to do
        try:  # Failed to even access the cached mistapi object
            mistapi = self.imports["mistapi"]  # Fetch the cached mistapi module object
            try:  # Sub-module wiring hit an unexpected issue
                globals()["mistapi"] = mistapi  # Expose mistapi at module global scope
                import sys  # Local import to reach this module's namespace object

                sys.modules[__name__].mistapi = mistapi  # type: ignore[attr-defined]  # Bind to module attr
                logging.debug("Successfully imported mistapi main module")  # Confirm SDK wired up
                self._verify_mistapi_api_structure(mistapi)  # Run the hasattr structural check
            except Exception as sub_e:  # Sub-module wiring hit an unexpected issue
                logging.debug("Note: mistapi sub-modules handled dynamically: %s", sub_e)  # Non-fatal
        except Exception as e:  # Failed to even access the cached mistapi object
            logging.warning("Error accessing mistapi: %s", e)  # Warn -- API features may be unavailable

    def _verify_mistapi_api_structure(self, mistapi):
        """Verify mistapi.api.v1 module structure is present and log the result."""
        if hasattr(mistapi, "api") and hasattr(mistapi.api, "v1"):  # Confirm expected nested API surface
            logging.debug("mistapi.api.v1 module structure confirmed")  # Structure looks correct
        else:  # The expected nested structure is missing
            logging.warning(
                "mistapi.api.v1 structure not found - this may cause API call failures"
            )  # Warn about likely failures

    def _log_websocket_availability(self):
        """Log whether websocket-client successfully loaded."""
        if "websocket-client" in self.imports:  # The websocket client library loaded
            logging.debug("websocket-client available for WebSocket operations")  # WebSocket features enabled
        else:  # The websocket client library is missing
            logging.debug(
                "websocket-client not available - WebSocket operations will be disabled"
            )  # WebSocket features disabled

    # get_import removed per issue #431 (ARCH-DELEGATE) -- callers access
    # `self.imports.get(name)` directly. `self.imports` is the public
    # dict already mutated elsewhere in this class.

    def is_available(self, module_name: str) -> bool:
        """Check if a module is available."""
        return module_name in self.imports  # True only if the module imported successfully

    def get_configuration(self) -> dict[str, Any]:
        """Get current configuration values."""
        return {  # Snapshot the manager's tunable settings for inspection/logging
            "auto_upgrade_uv": self.auto_upgrade_uv,  # Whether UV self-upgrades are enabled
            "auto_upgrade_dependencies": self.auto_upgrade_dependencies,  # Whether dependency auto-upgrade is enabled
            "upgrade_check_timeout": self.upgrade_check_timeout,  # Per-install subprocess timeout in seconds
            "csv_freshness_minutes": self.csv_freshness_minutes,  # How long cached CSVs are considered fresh
            "uv_update_check_hours": self.uv_update_check_hours,  # Interval between UV update checks
        }


# ============================================================================
# GLOBAL CONSTANTS
# ============================================================================


# File paths for configuration and data
# SECURITY / SAFETY: Place tuning data inside the data/ directory to avoid
# permission issues when running as non-root inside a container with read-only
# application root. The file is small and safe to persist across runs.
def _get_tuning_data_file_path() -> str:
    """Return full path to tuning data JSON stored in data/ directory.

    Ensures the directory exists. Separated for future extension (e.g.,
    namespacing by org or mode) without scattering path logic.
    """
    data_dir = os.path.join(os.getcwd(), "data")  # Build the path to the data/ subdirectory under the CWD
    try:
        os.makedirs(data_dir, exist_ok=True)  # Create data/ if it does not already exist (idempotent)
    except Exception:
        # If directory creation fails, fall back to current working directory;
        # logging deferred until logger configured.
        return os.path.join(os.getcwd(), "tuning_data.json")  # Degrade gracefully to a CWD-level file
    return os.path.join(data_dir, "tuning_data.json")  # Normal case: store tuning data inside data/


tuning_data_file = _get_tuning_data_file_path()  # Resolve the tuning-data path once at import time

# API usage tracking cache
_api_usage_cache = {  # Module-level cache for Mist API rate-limit accounting
    "timestamp": 0,  # Epoch seconds when the cache was last populated from the API
    "used": 0,  # Number of API requests the server reports as consumed
    "limit": 5000,  # Default per-window request quota until the real limit is learned
    "last_updated": 0,  # Epoch seconds of the most recent local update
    "perceived_requests": 0,  # Locally counted requests since the last server sync
    "initialized": False,  # Whether the cache has been seeded from a real API response yet
}

# ============================================================================
# GLOBAL IMPORT MANAGER INITIALIZATION
# ============================================================================

# Create global import manager instance
import_manager = GlobalImportManager()  # Single shared manager for all dependency imports

# Initialize imports immediately (unless deferred by CLI flags)
# Test mode and skip-deps both defer initialization to main() for better control
_initialize_imports_now = True  # Default: resolve all imports eagerly at module load

# Check for test mode or skip-deps from command line
if (
    "--test" in sys.argv or "--testinteractive" in sys.argv or "--skip-deps" in sys.argv
):  # Any flag that defers import setup
    _initialize_imports_now = False  # Defer initialization to main() for finer control
    if (
        "--test" in sys.argv or "--testinteractive" in sys.argv
    ) and "--skip-deps" not in sys.argv:  # Test mode without skip-deps
        logging.info(
            "Deferring import initialization for test mode (dependencies will still be checked)"
        )  # Explain the deferral
    elif "--skip-deps" in sys.argv:  # The caller explicitly asked to skip dependency handling
        logging.info("Deferring import initialization due to --skip-deps flag")  # Explain the deferral
    else:  # Some other deferring flag combination
        logging.info("Deferring import initialization due to CLI flags")  # Generic deferral notice

if _initialize_imports_now:  # Eager path: set up all imports now
    # Initialize all imports upfront for faster runtime performance
    success, global_assignments = (
        import_manager.initialize_all_imports()
    )  # Import everything and collect global bindings

    # Apply global assignments to module namespace
    if global_assignments:  # The manager produced name->object bindings to publish
        for var_name, var_value in global_assignments.items():  # Apply each binding to module globals
            globals()[var_name] = var_value  # Make the imported object available at module scope
            # Special handling for tqdm to ensure it overrides the fallback
            if var_name == "tqdm" and var_value is not None:  # Real tqdm must replace any earlier fallback
                logging.info(
                    "Successfully imported real tqdm: %s", type(var_value)
                )  # Confirm the real progress bar is active
        logging.debug(
            "Applied %s global variable assignments", len(global_assignments)
        )  # Report how many bindings were applied

        # Verify tqdm was properly imported
        if "tqdm" in global_assignments:  # tqdm binding is present
            logging.info(
                "tqdm is available in global namespace: %s", type(globals().get("tqdm"))
            )  # Confirm availability and type
        else:  # tqdm binding is missing
            logging.warning(
                "tqdm was not found in global assignments - progress bars will not be functional"
            )  # Warn progress bars are off

    if not success:  # One or more required imports failed
        logging.warning(
            "Some required imports failed - functionality may be limited"
        )  # Warn the user features may be degraded
else:  # Deferred path: imports happen later in main()
    # Deferred initialization - will be done in main()
    success, global_assignments = False, {}  # Placeholder values until main() runs initialization

# ============================================================================
# TEST MODE GLOBALS & TIME UTILITIES CLASS
# ============================================================================
# Central flag for test mode (available early so helper functions outside main can use it)
IS_TEST_MODE = "--test" in sys.argv or "--testinteractive" in sys.argv
# Last selected interactive site ID (used to keep testinteractive site context consistent)
LAST_SELECTED_SITE_ID: str | None = None


# NOTE: TimeUtils removed (1014 P6, Cat E) - canonical body at src/time/time_utils.py.
#       Import from src.time.time_utils. MistHelper.py re-exports at top import block.


# ============================================================================
# IMPORT STATUS AND INPUT UTILITIES CLASS
# ============================================================================


# NOTE: ``InputUtils`` extracted to ``src/utils/input_utils.py`` per initiative
# 1015 T-09 (Cat E fold-in). ``MistHelper.py`` re-exports the class so
# ``MistHelper.InputUtils`` / ``mh.InputUtils`` callers keep working
# transparently -- the re-exported symbol is the same class, not a delegator.
# The rebind dance ``ensure_tqdm_available`` used to perform is no longer
# needed since T-14 makes ``tqdm`` resolve through ``src.utils.tqdm_wrapper``
# at import time; the probe was retained for its logging side effect at the
# single caller (``src/refactors/main_entrypoint.py``).
from src.utils.input_utils import InputUtils  # noqa: E402, I001  # Cat E canonical (1015 T-09) -- re-export.


# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Configuration variables from .env (with defaults) - now managed by import manager
config = import_manager.get_configuration()  # Pull resolved settings from the import manager
CSV_FRESHNESS_MINUTES: int = config["csv_freshness_minutes"]  # Minutes a cached CSV stays "fresh" before refetch
AUTO_UPGRADE_UV: bool = config["auto_upgrade_uv"]  # Whether UV self-upgrades automatically
AUTO_UPGRADE_DEPENDENCIES: bool = config["auto_upgrade_dependencies"]  # Whether Python deps auto-upgrade on import
UPGRADE_CHECK_TIMEOUT: int = config["upgrade_check_timeout"]  # Seconds before an install/upgrade subprocess times out

# API Request Timeout (seconds) - prevents indefinite hangs on slow/dropped connections
# Default 120s is generous; most Mist API calls return within 30s
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "120"))  # Hard cap on a single API request
API_REQUEST_MAX_RETRIES = int(os.getenv("API_REQUEST_MAX_RETRIES", "3"))  # How many times to retry a failed API request
API_REQUEST_RETRY_DELAY = float(os.getenv("API_REQUEST_RETRY_DELAY", "5.0"))  # Seconds to wait between API retries

# Fast Mode Configuration from .env
FAST_MODE_MAX_RETRIES = int(os.getenv("FAST_MODE_MAX_RETRIES", "3"))  # Retry ceiling when --fast is active
FAST_MODE_RETRY_DELAY = float(os.getenv("FAST_MODE_RETRY_DELAY", "0.5"))  # Shorter retry delay for fast mode

org_id = None  # Active organization ID, populated after the user selects an org

# Additional Fast Mode Configuration from .env (continuing from earlier definitions)
# NOTE: FAST_MODE_BACKOFF_MULTIPLIER extracted to
# src/refactors/fast_mode_backoff_multiplier.py::FastModeBackoffMultiplier.VALUE
# per initiative 1011 SC-028 (FR-003: no wrapper shim; FR-005: const->classattr).
# NOTE: FAST_MODE_DEVICES_PER_THREAD extracted to
# src/refactors/fast_mode_devices_per_thread.py::FastModeDevicesPerThread.VALUE
# per initiative 1011 SC-029 (FR-003: no wrapper shim; FR-005: const->classattr).
# NOTE: FAST_MODE_SEQUENTIAL_MAX_RETRIES extracted to
# src/refactors/fast_mode_sequential_max_retries.py::FastModeSequentialMaxRetries.VALUE
# per initiative 1011 SC-030 (FR-003: no wrapper shim; FR-005: const->classattr).
FAST_MODE_RETRY_THREADS = int(os.getenv("FAST_MODE_RETRY_THREADS", "4"))  # Thread count for the retry pass
FAST_MODE_RETRY_MAX_RETRIES = int(os.getenv("FAST_MODE_RETRY_MAX_RETRIES", "2"))  # Retry ceiling within the retry pass
FAST_MODE_FALLBACK_THREADS = int(os.getenv("FAST_MODE_FALLBACK_THREADS", "8"))  # Thread count for the fallback pass
# NOTE: FAST_MODE_MAX_CONCURRENT_CONNECTIONS extracted to
# src/refactors/fast_mode_constants.py::FAST_MODE_MAX_CONCURRENT_CONNECTIONS.
# See specs/1015-misthelper-refactor-final-15/spec.md.
# NOTE: FAST_MODE_USE_CONNECTION_AWARE_THREADING extracted to
# src/refactors/fast_mode_constants.py::FAST_MODE_USE_CONNECTION_AWARE_THREADING (T-03).
# See specs/1015-misthelper-refactor-final-15/spec.md.
FAST_MODE_ENABLED: bool = False  # Set to True via --fast CLI flag at startup

# NOTE: MIST_WAN_TARGET_PORTS extracted to src/refactors/mist_wan_target_ports.py
# per initiative 1011 SC-032 (FR-003: no wrapper shim; FR-005: assignment->classattr).

# NOTE: MIST_SITE_EXCLUDE_PREFIX extracted to src/refactors/mist_site_exclude_prefix.py (T-15, Cat E).
# Site Exclusion Configuration from .env (REQUIRED - no defaults).
# The re-export below preserves MistHelper.MIST_SITE_EXCLUDE_PREFIX for backward-compat consumers
# (guardrail tests, historical mh.* callers) -- the canonical body lives in the extracted module.
from src.refactors.mist_site_exclude_prefix import (  # noqa: E402 - re-export after top-of-file imports.
    MIST_SITE_EXCLUDE_PREFIX,
)

# Global configuration for output format (CSV or Redis/SQLite)
# Default to CSV for general use, can be overridden by CLI flag
OUTPUT_FORMAT = "csv"  # Valid values: "csv", "sqlite"
DATABASE_PATH = os.path.join("data", "mist_data.db")  # Path to hybrid SQLite database with natural primary keys

# Global progress telemetry emitter (initialized in main(), best-effort per FR-008)
PROGRESS_EMITTER = None  # Set in main() to a telemetry sink; None disables progress reporting

# ============================================================================
# GLOBAL SESSION INITIALIZATION
# ============================================================================

# Initialize Mist API session (will be set up after authentication)
# Type annotation uses Any since mistapi is dynamically imported
apisession: Any | None = None

# MSP privilege tracking (populated after authentication)
msp_privileges: list[dict[str, Any]] = []  # List of {msp_id, msp_name, role, scope} dicts if user has MSP access
selected_msp: dict[str, Any] | None = None  # Currently selected MSP (from menu 115 or elsewhere)


# NOTE: detect_msp_privileges and its entire private helper chain (formerly
# _msp_resolve_name, _msp_parse_one_privilege, _msp_extract_from_user_data,
# _msp_fetch_user_data, _msp_cache_and_report, _extract_msp_name, _fetch_msp_name)
# were co-migrated to src/refactors/msp_privilege_detection.py during the T-05
# cleanup pass on initiative 1015. That module is fully self-contained and
# takes ``session`` as a required positional argument (no MistHelper reach-back,
# no module-global reads). Callers that want to publish the result into this
# module's ``msp_privileges`` global do so explicitly at the callsite:
# ``msp_privileges = detect_msp_privileges(apisession)``. See
# specs/1015-misthelper-refactor-final-15/spec.md.


def _snapshot_session_globals_to_state() -> dict:
    """Snapshot the live module-level session globals into a mutable state bag."""
    logging.debug("_snapshot_session_globals_to_state: capturing 5 module globals")  # Log before snapshot
    return {  # Map of global name -> current value for the LoginOrchestrator to mutate
        "apisession": apisession,  # Current API session object (may be None)
        "mistapi": mistapi,  # The mistapi SDK module reference
        "msp_privileges": msp_privileges,  # Any previously detected MSP grants
        "selected_msp": selected_msp,  # Currently selected MSP, if any
        "org_id": org_id,  # Currently selected org ID, if any
    }


def _restore_session_globals_from_state(state: dict) -> None:
    """Restore module-level session globals from a state bag mutated by the orchestrator."""
    global apisession, mistapi, msp_privileges, selected_msp, org_id  # Globals we may rebind
    logging.debug("_restore_session_globals_from_state: restoring 5 module globals")  # Log before restore
    apisession = state.get("apisession")  # Copy the (possibly new) session back to the global
    mistapi = state.get("mistapi")  # Copy the SDK reference back to the global
    msp_privileges = state.get("msp_privileges", msp_privileges)  # Copy detected MSP grants back
    selected_msp = state.get("selected_msp", selected_msp)  # Copy the selected MSP back
    org_id = state.get("org_id", org_id)  # Copy the selected org ID back
    ConfigUtils.set_apisession(apisession)  # Mirror the restored session into ConfigUtils class cache (1015 T-12)
    ConfigUtils.set_cached_org_id(org_id)  # Mirror the restored org_id into ConfigUtils class cache (1015 T-12)


# NOTE: initialize_mist_session_interactive() extracted to
# src/refactors/initialize_mist_session_interactive.py::MistSessionInteractiveInitializer.initialize
# per initiative 1011 SC-023 (FR-003: no wrapper shim; FR-005: fn->method).


def _print_switch_login_header():
    """Display switch to interactive login header and benefits."""
    logging.debug("Entering _print_switch_login_header()")  # Trace entry for debugging
    print("")  # Blank spacer line
    print("=" * 60)  # Top border of the header banner
    print("  SWITCH TO INTERACTIVE LOGIN")  # Banner title
    print("=" * 60)  # Bottom border of the header banner
    print("")  # Blank spacer line
    print("  This will replace your current API token session with")  # Explain the consequence (line 1)
    print("  an interactive (email/password) session.")  # Explain the consequence (line 2)
    print("")  # Blank spacer line
    print("  Benefits of interactive login:")  # Introduce the benefits list
    print("    - Can access MSP-level APIs (if you have MSP privileges)")  # Benefit: MSP API access
    print("    - Session-based auth with cookie management")  # Benefit: cookie session handling
    print("    - Supports 2FA authentication")  # Benefit: two-factor support
    print("    - Select and switch between MSPs and Organizations")  # Benefit: MSP/org switching
    print("")  # Blank spacer line
    if msp_privileges:  # The user already has MSP grants detected
        logging.debug("MSP privileges already detected: %s MSP(s)", len(msp_privileges))  # Trace the existing grants
        print(
            f"  Note: You already have MSP access to {len(msp_privileges)} MSP(s)"
        )  # Inform the user of existing access
        print("")  # Blank spacer line


def _attempt_interactive_login_with_rollback(old_session, old_org_id) -> bool:
    """Clear session and attempt interactive login with rollback on failure.

    Returns:
        bool: True if login succeeded, False if failed (session restored)
    """
    global apisession, msp_privileges, org_id  # We may overwrite or restore these globals

    logging.debug("Entering _attempt_interactive_login_with_rollback()")  # Trace entry for debugging
    logging.debug("Clearing existing session state for re-authentication")  # Note we're resetting before re-login

    apisession = None  # Drop the current session so the interactive flow starts clean
    msp_privileges = []  # Clear cached MSP grants from the old session
    org_id = None  # Clear the selected org from the old session
    ConfigUtils.set_apisession(None)  # Clear the ConfigUtils session cache to match (1015 T-12)
    ConfigUtils.set_cached_org_id(None)  # Clear the ConfigUtils org_id cache to match (1015 T-12)

    if not MistSessionInteractiveInitializer.initialize():  # Attempt the interactive login
        print("")  # Blank spacer line
        print("  X Login failed - restoring previous session")  # Inform the user of the rollback
        apisession = old_session  # Restore the prior API session
        org_id = old_org_id  # Restore the prior org selection
        msp_privileges = detect_msp_privileges(apisession)  # Re-detect MSP grants and publish to module global
        ConfigUtils.set_apisession(apisession)  # Mirror the restored session into ConfigUtils cache (1015 T-12)
        ConfigUtils.set_cached_org_id(org_id)  # Mirror the restored org_id into ConfigUtils cache (1015 T-12)
        logging.warning("Interactive login failed - restored previous API session")  # Log the failed attempt
        return False  # Signal failure to the caller
    logging.debug("Interactive login succeeded")  # Trace the successful login
    ConfigUtils.set_apisession(apisession)  # Publish new interactive session to ConfigUtils cache (1015 T-12)
    return True  # Signal success to the caller


def _handle_interactive_login_success():
    """Handle successful interactive login - display status and select MSP/org."""
    logging.debug("Entering _handle_interactive_login_success()")  # Trace entry for debugging
    print("")  # Blank spacer line
    print("  + Successfully switched to interactive login")  # Confirm the switch to the user
    if msp_privileges:  # The new session has MSP grants
        print(f"  + MSP access available: {len(msp_privileges)} MSP(s)")  # Report how many MSPs are accessible
        logging.info(
            "Successfully switched to interactive login session with %s MSP(s)", len(msp_privileges)
        )  # Log the success with MSP count
    else:  # No MSP grants on the new session
        logging.info(
            "Successfully switched to interactive login session (no MSP privileges)"
        )  # Log the success without MSPs

    if msp_privileges:  # Choose the selection flow based on MSP access
        _select_msp_and_org()  # MSP users pick an MSP then an org
    else:  # No MSP access
        _select_org_from_session()  # Non-MSP users pick an org directly


def _prompt_switch_login_confirmation() -> bool:
    """Prompt the user to confirm switching to interactive login.

    Returns True if the user typed 'y', False on cancel/EOF/SystemExit.
    """
    logging.debug("_prompt_switch_login_confirmation: prompting user for y/N")  # Log before prompt
    try:  # safe_input may raise SystemExit on EOF in some contexts
        confirm = (
            InputUtils.safe_input("  Proceed with re-authentication? (y/N): ", context="switch_login").strip().lower()
        )
    except SystemExit:  # EOF during the prompt
        logging.debug("SystemExit during confirmation prompt")  # Trace the early exit
        return False  # Treat as cancel
    logging.debug("User confirmation received: '%s'", confirm)  # Log the captured response
    if confirm != "y":  # User declined or pressed Enter
        print("  Cancelled.")  # Acknowledge the cancellation on stdout
        logging.warning("User cancelled switch to interactive login")  # Log the cancel
        return False  # Caller should stay on the menu
    return True  # User explicitly chose to proceed


def _select_msp_and_org() -> None:
    """Select MSP and organization via extracted interactive session manager."""
    global apisession, mistapi, msp_privileges, selected_msp, org_id  # These globals are updated by the selection flow

    state = {  # Snapshot current session globals into a mutable bag for the manager to update
        "apisession": apisession,  # Current API session object
        "mistapi": mistapi,  # The mistapi SDK module reference
        "msp_privileges": msp_privileges,  # Detected MSP grants to choose from
        "selected_msp": selected_msp,  # Currently selected MSP, if any
        "org_id": org_id,  # Currently selected org ID, if any
    }

    session_manager = MspOrgSelector(  # Build the MSP/org selector with injected deps
        state=state,  # Pass the mutable state bag the selector will update
        safe_input=InputUtils.safe_input,  # Inject the EOF-safe input function
        select_org_fallback=_select_org_from_session,  # Inject the non-MSP fallback org selector
    )
    session_manager.select()  # Run the interactive MSP-then-org selection flow

    apisession = state.get("apisession")  # Copy the (possibly switched) session back to the global
    mistapi = state.get("mistapi")  # Copy the SDK reference back to the global
    msp_privileges = state.get("msp_privileges", msp_privileges)  # Copy MSP grants back
    selected_msp = state.get("selected_msp", selected_msp)  # Copy the chosen MSP back
    org_id = state.get("org_id", org_id)  # Copy the chosen org ID back
    ConfigUtils.set_apisession(apisession)  # Mirror the switched session into ConfigUtils cache (1015 T-12)
    ConfigUtils.set_cached_org_id(org_id)  # Mirror the chosen org_id into ConfigUtils cache (1015 T-12)


def _invoke_mistapi_org_picker_and_apply() -> None:
    """Run mistapi's org picker and apply the user's choice to the org_id global."""
    global org_id  # The picker result writes through to the module-level org
    try:  # mistapi may raise on network errors or invalid sessions
        logging.debug("Invoking mistapi.cli.select_org()")  # Trace the SDK call
        org_id_list = mistapi.cli.select_org(apisession)  # Let mistapi present an org picker and return the choice
        if org_id_list and len(org_id_list) > 0:  # The user selected at least one org
            org_id = org_id_list[0]  # Use the first selected org ID
            ConfigUtils.set_cached_org_id(org_id)  # Mirror the picker's choice into ConfigUtils cache (1015 T-12)
            print(f"  + Organization ID set: {org_id}")  # Confirm the selection to the user
            logging.info("User selected org from session: %s", org_id)  # Log the chosen org
        else:  # Nothing was selected
            print("  X No organization selected")  # Inform the user no org was chosen
            logging.warning("No organization selected from session privileges")  # Log the empty selection
    except Exception as e:  # The SDK picker raised an error
        print(f"  X Error selecting organization: {e}")  # Show the error to the user
        logging.error("Failed to select org from session: %s", e)  # nosec B608  # Log the failure detail


def _select_org_from_session() -> None:
    """Pick an org via mistapi's built-in selector (non-MSP path)."""
    logging.debug("Entering _select_org_from_session()")  # Trace entry for debugging
    print("")  # Blank spacer line
    print("  Selecting organization from your session privileges...")  # Tell the user what's happening
    print("")  # Blank spacer line
    _invoke_mistapi_org_picker_and_apply()  # Run picker; updates the org_id global


def _load_mistapi_module(current_mistapi: Any) -> Any:
    """Ensure mistapi is imported, falling back to direct import if the global is not yet set.

    Args:
        current_mistapi: The current value of the module-level mistapi global (may be None).

    Returns:
        The mistapi module object, or None if import is unavailable.
    """
    if current_mistapi is not None:  # Already loaded -- return immediately without re-importing
        return current_mistapi  # Pass through existing module reference
    try:
        import mistapi as mistapi_fallback  # Attempt direct import as fallback when global not yet set

        logging.debug("Loaded mistapi via fallback import in initialize_mist_session")  # Confirm load path
        return mistapi_fallback  # Return newly imported module
    except ImportError as import_err:
        logging.error("Cannot import mistapi: %s", import_err)  # Log failure cause for operator visibility
        return None  # Signal that mistapi is unavailable -- caller must abort


def _split_env_tokens(raw_token_env: str | None) -> list[str]:  # Split a token env value into individual tokens
    """Split a newline/comma-separated token env value into a list of non-empty stripped tokens."""
    if not raw_token_env:  # No token env var set
        return []  # Caller will fall back to env_file or mistapi.Session
    return [token.strip() for token in re.split(r"[\n,]+", raw_token_env) if token.strip()]  # Split on newlines/commas


def _redact_tokens(tokens: list[str]) -> str:  # Build a secrets-safe preview of discovered tokens
    """Return a redacted, comma-joined preview (first4...last4, or *** when too short) for logging."""
    return ",".join((token[:4] + "..." + token[-4:]) if len(token) >= 8 else "***" for token in tokens)  # Redact each


def _parse_api_tokens() -> tuple[str, list[str]]:
    """Read API host and tokens from environment variables.

    Reads MIST_HOST (default: api.mist.com) and MIST_APITOKEN or MIST_API_TOKEN.
    Multiple tokens may be newline- or comma-separated in the env var value.

    Returns:
        A tuple of (host, tokens) where tokens is a list of stripped token strings.
    """
    host = os.getenv("MIST_HOST", "api.mist.com")  # Read host from env or use Mist cloud default
    raw_token_env = os.getenv("MIST_APITOKEN") or os.getenv("MIST_API_TOKEN")  # Accept both env var names
    tokens = _split_env_tokens(raw_token_env)  # Parse into individual non-empty tokens (empty list when unset)
    if tokens:  # Log a redacted preview so operators can confirm presence without exposing secrets
        logging.debug("Token(s) discovered for initialization (redacted): %s", _redact_tokens(tokens))  # Safe preview
    else:  # No tokens discovered in environment
        logging.debug("No tokens discovered in environment; will rely on env_file or mistapi.Session fallback")  # Note
    return host, tokens  # Return host string and parsed token list to caller


def _check_token_rate_limit(token: str, test_host: str) -> bool:
    """Probe a token via GET /self; True if rate-limited/unreachable, False if usable."""
    try:
        import requests  # Import here -- only needed for this edge-case rate-limit probe path

        url = f"https://{test_host}/api/v1/self"  # Lightweight endpoint requiring auth for rate-limit probe
        headers = {"Authorization": f"Token {token}"}  # Standard Mist API bearer token header
        response = requests.get(url, headers=headers, timeout=5)  # Short timeout -- probe, not full call
        if response.status_code == 429:  # HTTP 429 = Too Many Requests = rate-limited
            logging.debug("Token %s...%s is rate-limited (HTTP 429)", token[:4], token[-4:])
            return True  # Confirmed rate-limited -- skip this token
        elif response.status_code == 200:  # HTTP 200 = OK = token is functional
            logging.debug("Token %s...%s is available (HTTP 200)", token[:4], token[-4:])
            return False  # Token is usable -- include in available list
        else:  # Any unexpected status treated as unavailable (defensive)
            logging.warning("Token %s...%s returned unexpected status %d", token[:4], token[-4:], response.status_code)
            return True  # Treat unexpected response as unavailable for safety
    except Exception as test_err:
        logging.warning("Failed to test token %s...%s: %s", token[:4], token[-4:], test_err)
        return True  # Treat connection exception as unavailable to avoid broken tokens


def _introspect_apisession_class(mistapi_module: Any) -> tuple[Any, list[str]]:
    """Retrieve the APISession class and its constructor parameter names from mistapi.

    Introspecting the signature avoids hard-coding parameter names that may change
    across mistapi versions. Falls back to empty param list if introspection fails.

    Args:
        mistapi_module: The imported mistapi module.

    Returns:
        A tuple of (apisession_cls, sig_params). apisession_cls is None if absent.
        sig_params is a list of accepted constructor parameter name strings.
    """
    apisession_cls = getattr(mistapi_module, "APISession", None)  # Get APISession class (None if not present)
    if not apisession_cls:  # APISession class is absent in this mistapi version
        logging.debug("mistapi.APISession not found -- will attempt mistapi.Session fallback only")
        return None, []  # Return None class and empty param list to trigger fallback path
    try:
        sig_params = list(inspect.signature(apisession_cls).parameters.keys())  # Inspect constructor for param names
        logging.debug("mistapi.APISession accepted parameters: %s", sig_params)
        return apisession_cls, sig_params  # Return class and parameter name list
    except Exception:  # Introspection failed (unusual but non-fatal -- proceed with empty params)
        logging.debug("Failed to introspect APISession signature -- proceeding with empty param list")
        return apisession_cls, []  # Return class but no param info -- attempts list will be minimal


def _resolve_token_param_names(sig_params: list[str]) -> list[str]:
    """Return the supported token constructor parameter names, in priority order.

    Filters the known token kwargs against the introspected signature so callers
    only attempt parameter names the constructor actually accepts.
    """
    logging.debug("Resolving supported token parameter names from signature")  # Trace param resolution
    return [n for n in ["apitoken", "api_token", "token"] if n in sig_params]  # Keep only accepted token kwargs


def _build_token_session_attempts(
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> list[dict[str, str]]:
    """Build token-auth kwargs dicts (highest priority) for each supported token param."""
    logging.debug("Building token-based APISession attempts")  # Trace token attempt construction
    attempts: list[dict[str, str]] = []  # Accumulate token attempts in priority order
    token_param_names = _resolve_token_param_names(sig_params)  # Supported token kwargs from signature
    if not (tokens and token_param_names):  # Need both env tokens and an accepted token param name
        return attempts  # No token path possible -- return empty for caller to extend
    all_tokens_str = ",".join(tokens)  # Join as CSV -- mistapi rotates through them on HTTP 429
    for pname in token_param_names:  # Try each supported token parameter name in priority order
        base_kwargs: dict[str, str] = {pname: all_tokens_str}  # Build kwargs with this token param name
        if "host" in sig_params:  # Include host if constructor accepts it
            base_kwargs["host"] = host  # Set target API hostname
        attempts.append(base_kwargs)  # Add to ordered attempt list
    return attempts  # Ordered token attempts


def _build_fallback_session_attempts(
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> list[dict[str, str]]:
    """Build env_file/host fallback attempts, only when no env tokens are present."""
    logging.debug("Building fallback (env_file/host) APISession attempts")  # Trace fallback construction
    attempts: list[dict[str, str]] = []  # Accumulate fallback attempts
    if tokens:  # Env tokens present -- fallbacks are skipped to avoid duplicate token reads
        return attempts  # No fallback needed -- token attempts already cover auth
    if "env_file" in sig_params:  # env_file only when no env tokens (avoids double-read)
        attempts.append({"env_file": ".env"})  # Read credentials from .env file
    if "host" in sig_params:  # Host-only as last resort (unauthenticated probe)
        attempts.append({"host": host})  # Minimal connection -- API calls will fail without token
    return attempts  # Ordered fallback attempts


def _build_session_attempts(
    apisession_cls: Any,
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> list[dict[str, str]]:
    """Build a prioritized list of constructor kwargs dicts to attempt for APISession.

    Order: direct token param, then env_file (only when no env tokens), then host-only.
    Returns an empty list when no APISession class is available.
    """
    if not apisession_cls:  # Cannot build attempts without an APISession class to call
        return []  # Empty list -- caller will skip to Session fallback
    attempts = _build_token_session_attempts(sig_params, tokens, host)  # Preferred token-auth kwargs first
    attempts.extend(_build_fallback_session_attempts(sig_params, tokens, host))  # Append env_file/host fallbacks
    return attempts  # Prioritized list for _execute_session_attempts to iterate


def _log_session_attempt_traceback(exc: Exception) -> None:
    """Log the full traceback of a failed session initialization attempt at INFO level.

    Logs line-by-line so each line is a separate log entry, which works better
    with log aggregation tools. Non-fatal -- failure to log traceback is warned but ignored.

    Args:
        exc: The exception whose traceback to capture and log.
    """
    try:
        import traceback  # Import for traceback formatting -- deferred to avoid top-level overhead

        tb_details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))  # Format full traceback
        for line in tb_details.rstrip().splitlines():  # Split into individual lines for log aggregator
            logging.info("  TRACE: %s", line)  # Prefix with TRACE so operators can filter
    except Exception as trace_err:
        logging.warning("Failed to log traceback: %s", trace_err)  # Non-fatal -- continue without trace


def _try_single_session_kwargs(
    apisession_cls: Any,
    kwargs: dict[str, str],
    attempt_num: int,
    total: int,
) -> tuple[Any, bool]:
    """Try one APISession kwargs dict; return (session_or_None, rate_limit_seen)."""
    if apisession_cls is None:  # Guard: class must be present if attempts list was built
        raise AssertionError("apisession_cls should be set if attempts list is populated")
    try:  # APISession constructor may raise on auth/validation/rate-limit
        session = apisession_cls(**kwargs)  # Attempt APISession constructor with these kwargs
        logging.info("Mist API session initialized with mistapi.APISession using kwargs=%s", list(kwargs.keys()))
        return session, False  # Success -- no rate-limit signal needed
    except Exception as e:  # Constructor failed for this kwargs combination
        error_msg = str(e)  # Convert exception to string for rate-limit signature check
        logging.warning("APISession attempt %d/%d failed kwargs=%s: %s", attempt_num, total, kwargs, e)
        rate_limit = (
            "'NoneType' object is not iterable" in error_msg
        )  # Heuristic for rate-limit during token validation
        if rate_limit:  # Operator-visible signal that caller should switch to per-token retry path
            logging.warning("Detected possible rate limiting during token validation - tokens may be throttled")
        _log_session_attempt_traceback(e)  # Log full traceback for detailed debugging
        return None, rate_limit  # Return failure with rate-limit flag for caller to react


def _execute_session_attempts(
    apisession_cls: Any,
    attempts: list[dict[str, str]],
) -> tuple[Any, Any, bool, list[dict]]:
    """Try each kwargs dict until one constructs a valid APISession; track rate-limit signal."""
    tried_variants: list[dict] = []  # Track all attempted kwargs for error reporting on total failure
    successful_method: Any = None  # Will hold the kwargs dict that succeeded
    rate_limit_detected = False  # Set True if NoneType rate-limit error signature is seen
    session: Any = None  # Will hold the created APISession object on success
    for i, kwargs in enumerate(attempts, start=1):  # Try each kwargs dict in priority order
        tried_variants.append(kwargs)  # Record attempt before trying (in case of exception)
        session, attempt_rate_limit = _try_single_session_kwargs(
            apisession_cls, kwargs, i, len(attempts)
        )  # Try one kwargs dict; capture rate-limit signal
        if attempt_rate_limit:  # Even a failed attempt may surface the rate-limit signature
            rate_limit_detected = True  # Preserve the signal across iterations
        if session is not None:  # Successful construction -- record winning kwargs and stop
            successful_method = kwargs  # Downstream auth validation needs to know which kwargs worked
            break  # Success -- skip remaining attempts
    return session, successful_method, rate_limit_detected, tried_variants  # Return all state to orchestrator


def _filter_available_tokens(tokens: list[str], host: str) -> list[str]:
    """Probe each token individually and return only those not currently rate-limited.

    Iterates through all tokens, calling _check_token_rate_limit for each.
    Logs availability status per token so operators can see which are throttled.

    Args:
        tokens: Full list of tokens from environment to probe.
        host: Mist API hostname to use for probing via /api/v1/self.

    Returns:
        Subset of tokens that responded successfully and are not rate-limited.
    """
    available: list[str] = []  # Accumulate tokens that pass the rate-limit probe
    for index, token in enumerate(tokens, start=1):  # Probe each token with its 1-based position
        if not _check_token_rate_limit(token, host):  # Probe via /api/v1/self -- False means available
            available.append(token)  # This token is usable -- add to available list
            logging.info("Token %d/%d (%s...%s) is available", index, len(tokens), token[:4], token[-4:])
        else:  # Token is rate-limited or unreachable -- skip it
            logging.warning(
                "Token %d/%d (%s...%s) is rate-limited - skipping", index, len(tokens), token[:4], token[-4:]
            )
    return available  # Return only the usable tokens


def _build_filtered_session_kwargs(sig_params: list[str], tokens_csv: str, host: str) -> dict[str, str]:
    """Build APISession kwargs containing only fields the constructor accepts."""
    kwargs: dict[str, str] = {}  # Start with empty dict so we only include accepted params
    if "apitoken" in sig_params:  # Include token param only if constructor accepts it
        kwargs["apitoken"] = tokens_csv  # Pass comma-joined available tokens
    if "host" in sig_params:  # Include host if constructor accepts it
        kwargs["host"] = host  # Set target API hostname
    return kwargs  # Caller passes this into apisession_cls(**kwargs)


def _create_session_isolated_from_env(apisession_cls: Any, filtered_kwargs: dict[str, str]) -> Any:
    """Construct APISession after temporarily clearing MIST_APITOKEN to avoid stale-token re-read."""
    original_mist_token = os.environ.get("MIST_APITOKEN")  # Save original env value for finally cleanup
    try:  # Wrap so the env var is always restored even on construction failure
        if "MIST_APITOKEN" in os.environ:  # Clear env var to block mistapi from re-reading stale tokens
            del os.environ["MIST_APITOKEN"]  # Temporarily remove -- restored in finally block
            logging.debug("Temporarily cleared MIST_APITOKEN from environment for filtered token initialization")
        assert apisession_cls is not None, "apisession_cls should be set for retry logic"  # nosec B101
        session = apisession_cls(**filtered_kwargs)  # Create session with filtered token set
        logging.info("SUCCESS: API session initialized with filtered token kwargs=%s", list(filtered_kwargs.keys()))
        return session  # Caller pairs it back with filtered_kwargs for auth validation
    except Exception as filtered_err:  # Constructor still failed even with filtered tokens
        logging.error("Failed to initialize with filtered tokens: %s", filtered_err)  # Log failure reason
        return None  # Signal failure to caller
    finally:  # Always restore the env var even on success/exception
        if original_mist_token:  # Restore original env var regardless of success or failure
            os.environ["MIST_APITOKEN"] = original_mist_token  # Restore to prevent side effects
            logging.debug("Restored MIST_APITOKEN to environment")


def _create_session_with_available_tokens(
    apisession_cls: Any,
    sig_params: list[str],
    available_tokens: list[str],
    host: str,
) -> tuple[Any, Any]:
    """Create an APISession using only pre-filtered (non-rate-limited) tokens."""
    available_tokens_str = ",".join(available_tokens)  # Join as CSV for mistapi token rotation
    filtered_kwargs = _build_filtered_session_kwargs(
        sig_params, available_tokens_str, host
    )  # Build kwargs only with fields the constructor accepts
    logging.info("Initializing with %d available token(s)", len(available_tokens))  # Operator-visible progress
    session = _create_session_isolated_from_env(apisession_cls, filtered_kwargs)  # Construct with env-var isolation
    if session is None:  # Construction failed under env isolation
        return None, None  # Filtered token retry also failed
    return session, filtered_kwargs  # Return both for downstream auth validation


def _retry_with_filtered_tokens(
    apisession_cls: Any,
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> tuple[Any, Any]:
    """Retry session creation using only non-rate-limited tokens after a multi-token failure."""
    if not (apisession_cls and tokens and len(tokens) > 1):  # Guard: need class and multiple tokens to retry
        return None, None  # Cannot retry without multiple tokens and a class
    logging.warning("Multi-token init failed due to rate limiting - testing %d tokens individually", len(tokens))
    available_tokens = _filter_available_tokens(tokens, host)  # Probe each token for rate-limit status
    if not available_tokens:  # All tokens are throttled -- cannot recover
        logging.error("All %d tokens are currently rate-limited - cannot initialize API session", len(tokens))
        return None, None  # No usable tokens -- caller will try Session fallback
    logging.info("Found %d available token(s) out of %d total", len(available_tokens), len(tokens))
    return _create_session_with_available_tokens(apisession_cls, sig_params, available_tokens, host)  # Create session


def _try_session_fallback(mistapi_module: Any) -> tuple[Any, Any]:
    """Attempt legacy session creation via mistapi.Session() as last resort.

    mistapi.Session reads credentials from environment directly without explicit
    parameter passing. Used when all APISession constructor variants have failed.

    Args:
        mistapi_module: The imported mistapi module.

    Returns:
        Tuple of (session, successful_method), both None if Session class absent or fails.
    """
    if not (mistapi_module and hasattr(mistapi_module, "Session")):  # Guard: Session class must exist
        return None, None  # Session class absent -- cannot use this fallback
    try:
        session = mistapi_module.Session()  # Attempt legacy Session() with no explicit params
        logging.info("Mist API session initialized with mistapi.Session fallback")
        return session, {"fallback": "mistapi.Session"}  # Return session and method label for auth validation
    except Exception as e:
        logging.error("mistapi.Session fallback failed: %s", e)  # Log why the last resort failed
        return None, None  # Fallback also failed -- caller will report total failure


def _ensure_mist_get_method(session: Any) -> bool:
    """Ensure the session exposes a mist_get method, wrapping get() for compatibility if needed.

    Some mistapi versions expose get() instead of mist_get(). This function
    attaches a mist_get wrapper around get() so all callers can use mist_get uniformly.

    Args:
        session: The initialized APISession or Session object to check.

    Returns:
        True if mist_get is present or successfully wrapped, False if neither method exists.
    """
    if hasattr(session, "mist_get"):  # Preferred method already present -- nothing to do
        return True  # Session is compatible as-is
    if hasattr(session, "get") and callable(session.get):  # Alternate method found -- bind a compat callable

        def _mist_get_impl(*args, **kwargs):  # Closure binds `session` and implements mist_get on top of get().
            return session.get(*args, **kwargs)  # Forward to the session's native get() with identical signature.

        session.mist_get = _mist_get_impl  # Attach the closure so callers can use mist_get uniformly.
        logging.info("Added mist_get implementation around underlying get() method for compatibility")
        return True  # Session is now exposes mist_get via the bound closure
    logging.error("Initialized session lacks 'mist_get' or 'get' methods required for API calls")
    return False  # Session is unusable -- hard failure


def _detect_session_token(session: Any) -> bool:
    """Return True when the session exposes a readable, non-empty token attribute."""
    logging.debug("Detecting readable token attribute on session")  # Trace token attribute probe
    token_attr = next((a for a in ("apitoken", "api_token", "token") if hasattr(session, a)), None)  # Find auth attr
    return bool(token_attr and getattr(session, token_attr))  # True only if attr exists and holds a value


def _detect_session_method_flags(successful_method: Any) -> tuple[bool, bool, bool]:
    """Return (used_env_file, used_direct_token, used_fallback) from the winning kwargs."""
    logging.debug("Detecting auth method flags from successful constructor kwargs")  # Trace method-flag derivation
    direct_params = ["apitoken", "api_token", "token"]  # Constructor kwargs that denote direct token auth
    used_env_file = bool(successful_method and "env_file" in successful_method)  # env_file auth path used
    used_direct_token = bool(successful_method and any(p in successful_method for p in direct_params))  # Direct token
    used_fallback = bool(successful_method and "fallback" in successful_method)  # Legacy Session() path used
    return used_env_file, used_direct_token, used_fallback  # Surface flags for logging decisions


def _log_missing_auth_warning() -> None:
    """Emit operator-facing warnings when no authentication method can be detected."""
    logging.warning("Session established but no auth method detected; API calls may fail if auth required")  # Warn
    logging.warning("To fix: 1) Copy documentation/sample.env to .env, 2) Set MIST_APITOKEN to your token")  # Steps
    logging.warning("Get your API token from: https://manage.mist.com/admin/apitoken")  # Where to obtain a token


def _log_detected_auth(used_env_file: bool, used_direct_token: bool, has_readable_token: bool) -> None:
    """Emit a single debug line describing the detected auth path (env_file > token param > attr)."""
    if used_env_file:  # Highest-priority detected path -- credentials came from .env
        logging.debug("Session initialized using env_file - authentication configured via .env file")  # env_file path
    elif used_direct_token:  # Next priority -- a token was passed directly to the constructor
        logging.debug(
            "Session initialized using direct token parameter - authentication configured"
        )  # token-param path
    elif has_readable_token:  # Last -- session simply exposes a populated token attribute
        logging.debug("Session has readable token attribute - authentication appears configured")  # attribute path


def _log_session_auth_status(session: Any, successful_method: Any) -> None:
    """Log the authentication status of an initialized session.

    Warns if no authentication method is detectable, to help operators diagnose
    API calls that fail due to missing credentials.
    """
    has_readable_token = _detect_session_token(session)  # Token attribute presence/value
    used_env_file, used_direct_token, used_fallback = _detect_session_method_flags(successful_method)  # Method flags
    if not any([has_readable_token, used_env_file, used_direct_token, used_fallback]):  # No auth signal at all
        _log_missing_auth_warning()  # Surface remediation guidance to operators
        return  # Nothing further to log -- mirrors original early-out behavior
    _log_detected_auth(used_env_file, used_direct_token, has_readable_token)  # Debug-log the detected path


def _validate_initialized_session(session: Any, successful_method: Any) -> bool:
    """Validate that an initialized session has required methods and detectable authentication.

    Calls _ensure_mist_get_method to verify/add mist_get compatibility, then
    calls _log_session_auth_status to warn if authentication cannot be confirmed.
    Returns False only for hard failures (missing mist_get); auth warnings are non-fatal.

    Args:
        session: The initialized APISession or Session object.
        successful_method: Dict describing which constructor kwargs were used.

    Returns:
        True if the session is usable, False if required mist_get method is absent.
    """
    if not _ensure_mist_get_method(session):  # Verify or patch mist_get -- hard failure if absent
        return False  # Session is unusable without mist_get
    _log_session_auth_status(session, successful_method)  # Warn if authentication method is unclear
    return True  # Session passed all checks -- ready for API calls


def _attempt_all_session_strategies(apisession_cls, sig_params, tokens, host, mistapi_mod):
    """Try APISession kwargs, then filtered-token retry, then legacy Session(). Returns (session, method, tried)."""
    attempts = _build_session_attempts(apisession_cls, sig_params, tokens, host)  # Ordered kwargs candidates
    session_obj, method, rate_limited, tried = _execute_session_attempts(apisession_cls, attempts)  # First wave
    if not session_obj and rate_limited:  # Rate-limit signature — try tokens individually
        session_obj, method = _retry_with_filtered_tokens(apisession_cls, sig_params, tokens, host)
    if not session_obj:  # APISession exhausted — try legacy mistapi.Session()
        session_obj, method = _try_session_fallback(mistapi_mod)
    return session_obj, method, tried  # Caller validates / logs / patches


def _log_failed_session_variants(tried_variants) -> None:
    """Log every kwargs variant that failed (operator debugging on total init failure)."""
    logging.error("All Mist API session initialization attempts failed. Variants tried:")
    for variant in tried_variants:  # One log line per variant for clarity
        logging.error("  - %s", variant)


# NOTE: initialize_mist_session() extracted to
# src/refactors/initialize_mist_session.py::MistSessionInitializer.initialize
# per initiative 1011 SC-024 (FR-003: no wrapper shim; FR-005: fn->method).


def _install_default_request_timeout(inner_session: Any) -> None:
    """Install API_REQUEST_TIMEOUT as the default timeout on the requests.Session."""
    from requests.adapters import HTTPAdapter  # Lazy import; requests is large and only needed here

    class TimeoutAdapter(HTTPAdapter):  # Nested so we don't expose a public adapter class
        """HTTPAdapter that injects a default timeout."""

        def __init__(self, default_timeout: int, **kwargs):  # Capture the project-wide timeout default
            self.default_timeout = default_timeout  # Reused when send() gets timeout=None
            super().__init__(**kwargs)  # Real adapter setup (connection pool, retries)

        def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
            if timeout is None:  # Caller did not supply a per-call timeout -- substitute our default
                timeout = self.default_timeout
            # Issue #431: forward args verbatim; signature must match parent for adapter contract.
            return super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)

    adapter = TimeoutAdapter(default_timeout=API_REQUEST_TIMEOUT)  # Single instance shared by both schemes
    inner_session.mount("https://", adapter)  # Apply to HTTPS calls (standard Mist transport)
    inner_session.mount("http://", adapter)  # Apply to plain HTTP too for completeness


def _configure_session_timeout(session_obj: Any) -> None:
    """Patch the mistapi APISession's inner requests.Session with a default read timeout."""
    try:  # Defensive: any failure here is non-fatal -- log and move on
        inner = getattr(session_obj, "_session", None)  # Probe for the underlying requests.Session
        if inner is None:  # mistapi version did not expose a _session attribute
            logging.warning("Cannot configure timeout - session has no _session attribute")
            return  # Nothing to patch -- caller continues without timeout enforcement
        _install_default_request_timeout(inner)  # Build and install the timeout-injecting transport
        logging.info("Configured API request timeout: %ss", API_REQUEST_TIMEOUT)
    except Exception as timeout_err:  # Any failure -- log and continue without enforcement
        logging.warning("Failed to configure session timeout: %s", timeout_err)


# ============================================================================
# ENDPOINT PRIMARY KEY STRATEGY CONFIGURATION
# ============================================================================
# NOTE: ENDPOINT_PRIMARY_KEY_STRATEGIES has been extracted to
# src/refactors/endpoint_primary_key_strategies.py (initiative 1015 T-04, Cat E).
# External consumers (src/db/database_schema_utils.py, tests/test_ticket_manager.py)
# import the symbol directly from that module. MistHelper.py imports it at the
# top of the file solely for internal use at DatabaseRouter init -- there is no
# re-export shim, no facade, and no lazy `importlib.import_module("MistHelper")`
# lookup.


# ============================================================================
# CACHE UTILITIES CLASS
# ============================================================================
# NOTE: CacheUtils has been extracted to
# src/cache/cache_utils.py (initiative 1014 P14, Cat E position 14)
# The top-level from src.cache.cache_utils import CacheUtils re-export
# alias keeps historical MistHelper.CacheUtils callers working unchanged.


# ============================================================================
# DISPLAY UTILITIES CLASS
# ============================================================================
# NOTE: DisplayUtils has been extracted to
# src/ui/display_utils.py (issue #1013 SC-001 position 11)


# Issue #431: module-level alias `PacketCaptureManager = ExtractedPacketCaptureManager`
# was removed. The canonical name is now imported directly at module top.


# SFPTransceiverDataProcessor moved to src/reports/sfp_transceiver_data_processor.py  # noqa: E501
# (1013 SC-001 position 27)


# FilePathUtils moved to src/utils/file_path_utils.py (initiative 1015 T-13).
# The top-level from src.utils.file_path_utils import FilePathUtils re-export
# alias keeps historical MistHelper.FilePathUtils callers working unchanged.


# ============================================================================
# ENVIRONMENT UTILITIES CLASS
# ============================================================================
# EnvironmentUtils body removed 1013 SC-001 P33 -- see src/utils/environment_utils.py.


# ============================================================================
# VALIDATION UTILITIES CLASS
# ============================================================================
# NOTE: ValidationUtils removed (1014 P5, Cat E) - canonical body at
#       src/validation/validation_utils.py. Import from src.validation.validation_utils
#       instead. MistHelper.py re-exports ValidationUtils at the top import block
#       for legacy in-file callsites.


# ============================================================================
# CONFIGURATION UTILITIES CLASS
# ============================================================================
# NOTE: ConfigUtils removed (1015 T-12, Cat E) - canonical body at
#       src/config/config_utils.py. Import from src.config.config_utils
#       instead. MistHelper.py re-exports ConfigUtils at the top import block
#       for legacy in-file callsites.


# ============================================================================
# API FETCH UTILITIES CLASS
# ============================================================================
# NOTE: APICoreFetchUtils removed (1014 P10, Cat E) - canonical body at src/api/api_core_fetch_utils.py.


# APITenantFetchUtils extracted to src/api/tenant_fetch.py (issue #331).
# Dependency injection is used so the module has no circular import with MistHelper.
# Instances are created at each call site using the runtime apisession and org ID resolver.
from src.api.tenant_fetch import APITenantFetchUtils  # Re-exported for ServicePingLauncher late-binding

# NOTE: APIFetchUtils removed (1014 P8, Cat E) - canonical body at src/api/api_fetch_utils.py.
# ============================================================================
# DATA PROCESSING UTILITIES CLASS
# ============================================================================
# NOTE: ``DataProcessingUtils`` extracted to ``src/data/data_processing_utils.py``
# per initiative 1015 T-10 (Cat E). ``MistHelper.py`` re-exports the class so
# historical ``MistHelper.DataProcessingUtils`` / ``mh.DataProcessingUtils``
# callers keep working transparently -- the re-exported symbol is the same
# class, not a delegator. All methods are ``@staticmethod`` with no runtime
# dependencies, so no Pattern 1 wrapper is required.
from src.data.data_processing_utils import DataProcessingUtils  # noqa: E402, I001  # Cat E canonical (1015 T-10).

# MarvisDataUtils extracted to src/marvis/marvis_utils.py (issue #330).
# Dependency injection is used so the module has no circular import with MistHelper.
# NOTE: marvis_data_utils singleton extracted to
# src/refactors/marvis_data_utils.py::MarvisDataUtilsFactory.instance()
# per initiative 1011 SC-027 (FR-003: no wrapper shim; FR-005: fn->method).
# DatabaseSchemaUtils moved to src/db/database_schema_utils.py (1013 SC-001 position 38)
# DataExporter body extracted to src/export/data_exporter.py per issue #1015 T-08 (Cat E).
# Class is imported at module top via: from src.export.data_exporter import DataExporter
from src.export.data_exporter import DataExporter  # noqa: E402,F401  # T-08 re-export

# APIDataFetcher moved to src/api/api_data_fetcher.py (1013 SC-001 position 21)
# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute.
# See specs/1012-misthelper-refactor-hot-functions/spec.md.
# ============================================================================
# PROMPT UTILITIES CLASS
# ============================================================================
# PromptNetworkDeviceUtils -- extracted to src/device/prompt_utils.py (issue #332)
# PromptClientUtils moved to src/input/prompt_client_utils.py (1013 SC-001 position 35)
# PromptUtils body extracted to src/ui/prompt_utils.py per issue #1015 T-07 (Cat E).
# Class is imported at module top via: from src.ui.prompt_utils import PromptUtils
from src.ui.prompt_utils import PromptUtils  # noqa: E402,F401  # T-07 re-export

# NOTE: show_site_device_inventory() has been refactored into SiteDeviceExporter.device_inventory()


# NOTE: DeviceUtils has been extracted to src/device/device_utils.py (issue #1013 SC-001 position 6)


# OrgTicketManager moved to src/org/org_ticket_manager.py (1013 SC-001 Cat B position 46)


# OrgAlarmEventExporter moved to src/export/org_alarm_event_exporter.py (1013 SC-001 position 18)


# ============================================================================
# ORGANIZATION DATA EXPORT UTILITIES CLASS
# ============================================================================
# NOTE: OrgSiteExporter has been extracted to
# src/export/org_site_exporter.py (issue #1014 P9)


# --- OrgInventoryExporter body removed (1015 T-06 Cat E) ---
# Canonical implementation lives in src/export/org_inventory_exporter.py; re-exported above.


# --- OrgDeviceStatsExporter facade removed (1013 SC-001 Cat B pos 45) ---
# Canonical implementation lives in src/export/org_device_stats_exporter.py; re-exported above.


# --- OfflineDeviceReporter facade removed (1013 SC-001 Cat B pos 44) ---
# Canonical implementation lives in src/reports/offline_device_reporter.py; re-exported above.


# --- OrgDeviceInventorySummary facade removed (1013 SC-001 Cat B pos 29) ---
# Canonical implementation lives in src/inventory/org_device_inventory_summary_facade.py; re-exported above.


# OrgTemplateExporter moved to src/export/org_template_exporter.py (1013 SC-001 position 22)


# OrgClientSecurityExporter body removed 1013 SC-001 P32 -- see src/export/org_client_security_exporter.py.


# FilterOperatorEngine moved to src/utils/filter_operator_engine.py (1013 SC-001 position 40)


# GlobalWiredClientReportGenerator moved to src/reports/global_wired_client_report_generator.py (1013 SC-001 position 36)  # noqa: E501


# WiredClientManufacturerReportGenerator moved to src/reports/wired_client_manufacturer_report_generator.py  # noqa: E501
# (1013 SC-001 position 26)


# OrgAdminExporter moved to src/export/org_admin_exporter.py (1013 SC-001 position 20)


# LicenseExportUtils moved to src/export/license_export_utils.py (1013 SC-001 position 24)


# NOTE: SelfExportUtils has been extracted to src/export/self_export_utils.py (issue #1013 SC-001 position 7)


# OrgConfigExporter moved to src/export/org_config_exporter.py (issue #1013 SC-001 position 31)


# --- OrgExportUtils facade removed (1013 SC-001 Cat B pos 47); see src/export/org_export_utils.py ---


# ============================================================================
# SITE DATA EXPORT UTILITIES CLASS
# ============================================================================


# SiteDeviceExporter moved to src/export/site_device_exporter.py (1013 SC-001 position 34)


# SiteClientExporter moved to src/export/site_client_exporter.py (1013 SC-001 position 14)


# SiteConfigExporter moved to src/export/site_config_exporter.py (1013 SC-001 position 19)


# --- SiteAnomalyExporter facade removed (1013 SC-001 Cat B pos 43) ---
# Canonical implementation lives in src/export/site_anomaly_exporter.py; re-exported above.


# --- SitesByAPModelExporter facade removed (1013 SC-001 Cat B pos 28) ---
# Canonical implementation lives in src/export/sites_by_ap_model_exporter.py; re-exported above.

# ============================================================================
# WEBSOCKET COMMAND FUNCTIONS
# ============================================================================


# SiteExportUtils moved to src/export/site_export_utils.py (1014 P16 Cat A) — imported at top
# GatewayHaExporter moved to src/gateway/gateway_ha_exporter.py (1013 SC-001 position 23)


# ============================================================================
# ROUTING UTILITIES - Extracted to src/network/routing_utils.py (Issue #207)
# ============================================================================


# NOTE: RoutingUtils facade + _get_routing_utils_instance() removed (1014 P4, Cat A) -
#       canonical body at src/network/routing_utils.py:106. Menus 103-105 now inline
#       DI via lambdas (see MENU_ENTRIES).


# ============================================================================
# DEVICE UTILITY COMMANDS - Complete Mist API Coverage (Menus 123-157)
# Implementation extracted to src/device/utility_commands.py (Issue #210)
# ============================================================================


def _get_duc_instance():  # Build DeviceUtilityCommands.
    """Create DeviceUtilityCommands instance with MistHelper globals."""
    from src.device.utility_commands import (  # Import the extracted class + deps.
        DeviceUtilityCommands as _DUC,
    )
    from src.device.utility_commands import (
        UtilityCommandsDeps as _Deps,
    )

    deps = _Deps(  # Bundle 6 dependencies into a frozen dataclass.
        apisession=apisession,
        select_site_fn=PromptUtils.select_site_id_from_csv,
        select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype),
        safe_input_fn=InputUtils.safe_input,
        write_export_fn=lambda data, fn, api: DataExporter.write_with_format_selection(data, fn, api_function_name=api),
        websocket_manager_factory=WebSocketManager,
    )
    return _DUC(deps)  # Instantiate with bundled deps.


# NOTE: DeviceUtilityCommands facade removed 2026-07-07 (Issue #1013, SC-001 position 4).
# The 188-LOC facade of 35 @staticmethod delegates lived here; menu_actions callsites now
# invoke `lambda: _get_duc_instance().method_name()` directly against the canonical
# instance-based class in `src/device/utility_commands.py`. See PR history for details.


# ==============================
# INSIGHTS API FUNCTIONS - Organization & Site Analytics
# ==============================


# EndpointConfig moved to src/dataclasses/endpoint_config.py (1013 SC-001 position 16)


# ConstDefinitionsExporter moved to src/export/const_definitions_exporter.py (1013 SC-001 position 17)


# InsightMetricsUtils moved to src/analytics/insight_metrics_utils.py (1014 SC-001 position 11)


# NOTE: create_test_sites_from_csv moved to SiteConfigManager.create_test_sites_from_csv
# NOTE: create_country_rf_templates_and_assign moved to SiteConfigManager.create_country_rf_templates_and_assign
# NOTE: create_ap_model_device_profiles moved to SiteConfigManager.create_ap_model_device_profiles
# NOTE: assign_aps_to_matching_device_profiles moved to SiteConfigManager.assign_aps_to_matching_device_profiles
# NOTE: continuous_data_collection_loop moved to DataCollectionManager.continuous_loop
# NOTE: generate_support_package moved to DataCollectionManager.generate_support_packages


# DataCollectionManager moved to src/analytics/data_collection_manager.py (1013 SC-001 position 25)


# ============================================================================
# INTERACTIVE DISPLAY UTILITIES CLASS
# ============================================================================
# NOTE: InteractiveDisplayUtils has been extracted to
# src/ui/interactive_display_utils.py (issue #1013 SC-001 position 10)


# GatewayTestExporter moved to src/export/gateway_test_exporter.py (1013 SC-001 position 37)  # noqa: E501


# GatewayStatsExporter moved to src/gateway/gateway_stats_exporter.py (1014 SC-001 position 12)
# Top-level import above re-exports the canonical class. Menu dispatch uses the
# dispatch shims below to ensure _configure_gateway_module() runs (which cascades
# DI wiring through configure_gateway_stats_exporter_dependencies and the WAN
# override subsystem) before the canonical class methods execute.


def _build_gateway_export_kwargs() -> dict:
    """Build the kwargs dict passed to configure_gateway_export_utils_dependencies()."""
    return dict(  # Single dependency-wiring payload assembled in one place.
        apisession_dependency=apisession,  # Live mistapi session.
        mistapi_dependency=mistapi,  # mistapi root module.
        config_utils=ConfigUtils,  # Shared config helpers.
        cache_utils=CacheUtils,  # Disk-cache helpers.
        file_path_utils=FilePathUtils,  # Path helpers.
        data_exporter=DataExporter,  # Output backend writer.
        data_processing_utils=DataProcessingUtils,  # Flatten/normalize helpers.
        api_fetch_utils=APIFetchUtils,  # Paged fetch helpers.
        api_core_fetch_utils=APICoreFetchUtils,  # Core unwrap helpers.
        org_inventory_exporter=OrgInventoryExporter,  # For inventory lookups.
        org_site_exporter=OrgSiteExporter,  # For site lookups.
        input_utils=InputUtils,  # safe_input + prompts.
        execute_fn=ConnectionPoolExecutor.execute,  # Pool executor (1012 SC-003).
        validation_utils=ValidationUtils,  # Input validation.
        rate_limiting_utils=RateLimitingUtils,  # Adaptive delay.
        mist_wan_target_ports=MistWanTargetPorts.VALUE,  # Port list from extracted class attribute.
        mist_site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,  # Site filter prefix.
        fast_mode_max_retries=FAST_MODE_MAX_RETRIES,  # Retry cap.
        fast_mode_retry_delay=FAST_MODE_RETRY_DELAY,  # Delay between retries.
        api_usage_cache=_api_usage_cache,  # Shared API usage cache.
        tqdm_module=tqdm,  # Progress bar dependency.
    )


def _configure_gateway_module() -> None:
    """Wire DI into the canonical gateway_export_utils module (cascades to stats + WAN override)."""
    configure_gateway_export_utils_dependencies(**_build_gateway_export_kwargs())


def _dispatch_gateway_stats_device_stats_with_freshness(fast: bool = False) -> None:
    """Wire gateway DI then delegate to canonical GatewayStatsExporter.device_stats_with_freshness."""
    _configure_gateway_module()  # WHY: cascades DI wiring for stats exporter.
    GatewayStatsExporter.device_stats_with_freshness(fast=fast)


def _dispatch_gateway_stats_wan_port_conflicts() -> None:
    """Wire gateway DI then delegate to canonical GatewayStatsExporter.wan_port_conflicts."""
    _configure_gateway_module()  # WHY: cascades DI wiring for stats exporter.
    GatewayStatsExporter.wan_port_conflicts()


def _dispatch_gateway_management_ips(fast: bool = False) -> None:
    """Wire gateway DI then delegate to canonical GatewayExportUtils.management_ips."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.management_ips(fast=fast)


def _dispatch_gateway_templates() -> None:
    """Wire gateway DI then delegate to canonical GatewayExportUtils.templates."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.templates()


def _dispatch_gateway_with_wan_overrides(fast: bool = False) -> None:
    """Wire gateway DI then delegate to canonical GatewayExportUtils.with_wan_overrides."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.with_wan_overrides(fast=fast)


def _dispatch_gateway_wan2_variable_migration(fast: bool = False, dry_run: bool = False) -> None:
    """Wire gateway DI then delegate to canonical GatewayExportUtils.wan2_variable_migration."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.wan2_variable_migration(fast=fast, dry_run=dry_run)


def _dispatch_gateway_device_configs(debug: bool = False, fast: bool = False) -> None:
    """Wire gateway DI then delegate to canonical GatewayExportUtils.device_configs."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.device_configs(debug=debug, fast=fast)


# NOTE: GatewayExportUtils facade removed per 1013 SC-001 (Cat A, position 13).
# Canonical class lives at src/gateway/gateway_export_utils.py and is imported at
# top-of-file. DI wiring lives in _configure_gateway_module() above; menu callbacks
# route through _dispatch_gateway_* shims to ensure DI cascade runs first.


# NOTE: generate_support_package moved to DataCollectionManager.generate_support_packages


# ============================================================================
# TROUBLESHOOTING UTILITIES CLASS
# ============================================================================


# TroubleshootUtils moved to src/troubleshooting/troubleshoot_utils.py (1013 SC-001 position 39)


# NOTE: GatewayTemplateConfigManager facade removed per 1013 SC-001 (Cat A, position 1).
# Canonical class lives at src/gateway/template_config.py and is imported at top-of-file.
# Menu 105/106/111 handlers construct it directly with 8 injected deps (see menu_actions).


# NOTE: DeviceConfigTemplateClonerManager extracted per SC-020.
# Now lives at src/refactors/device_config_template_cloner_manager.py.
# Callers should reference the imported DeviceConfigTemplateClonerManager symbol (see top-of-file imports).


# ============================================================================
# SSH RUNNER MANAGER FACADE REMOVED (1014 P15, Cat A)
# ============================================================================
# Canonical class lives at src/ssh/ssh_runner_manager.py; imported at top of file.
# The helper below builds the DI container from MistHelper module globals.
def _build_ssh_runner_deps() -> SSHRunnerManagerDeps:  # Build the deps bundle for SSHRunnerManager entrypoints.
    """Build dependency container for SSH runner logic (reads MistHelper globals)."""
    cli_args = globals().get("args") if "args" in globals() else None  # Read parsed CLI args.
    _configure_gateway_module()  # 1014 P13: DI wire canonical gateway module before packaging class ref.
    return SSHRunnerManagerDeps(  # Assemble the deps.
        args=cli_args,
        progress_emitter=PROGRESS_EMITTER,
        enhanced_ssh_runner=EnhancedSSHRunner,
        input_utils=InputUtils,
        cache_utils=CacheUtils,
        gateway_export_utils=GatewayExportUtils,
        file_path_utils=FilePathUtils,
    )


# CLIShellManager was extracted to src/ssh/cli_shell_manager.py in initiative 1013 (Cat B, position 30).
# Re-exported via the alphabetized `from src.ssh.cli_shell_manager import CLIShellManager` alias above.


# ARPCommandManager moved to src/device/arp_command_manager.py (1013 SC-001 position 42)
# NOTE: listen_for_command_output removed - use ARPCommandManager._listen_for_output directly
# NOTE: loop_refresh_core_datasets moved to DataCollectionManager.continuous_loop


# ============================================================================
# RATE LIMITING & ADDRESS UTILITIES (extracted to src/utils/)
# ============================================================================
from src.utils.rate_limiting import RateLimitingUtils  # noqa: E402

# ============================================================================
# ORG CONFIG MIGRATION MANAGER CLASS
# ============================================================================
# NOTE: OrgConfigMigrationManager extracted to src/org/org_config_migration_manager.py
# (SC-001 position 5, issue #1013). Menus 176/177 continue to reference the class
# name directly via the top-of-file import.


# ============================================================================
# VIRTUAL CHASSIS MANAGER CLASS
# ============================================================================
# NOTE: VirtualChassisManager folded fully into src/device/virtual_chassis.py
# per 1015 T-11 (Cat E). Menu wire-up lives in _configure_virtual_chassis_manager()
# below (single seam for menu 161/162/14 dispatch lambdas). No stub or delegator
# remains in MistHelper.py after this extraction.
def _configure_virtual_chassis_manager() -> type[VirtualChassisManager]:
    """Wire VirtualChassisDependencies and return the canonical VirtualChassisManager class."""
    _configure_virtual_chassis_dependencies(  # Publish MistHelper globals into the impl module.
        _VirtualChassisDependencies(  # Frozen container of 9 injected collaborators.
            apisession=apisession,  # Live Mist API session.
            file_path_utils=FilePathUtils,  # Portable CSV path resolver + template writer.
            cache_utils=CacheUtils,  # check_and_generate_csv freshness gate.
            org_inventory_exporter=OrgInventoryExporter,  # Regenerates OrgInventory.csv.
            org_site_exporter=OrgSiteExporter,  # Regenerates SiteList.csv.
            input_utils=InputUtils,  # safe_input for destructive prompts.
            prompt_utils=PromptUtils,  # select_site interactive picker.
            data_processing_utils=DataProcessingUtils,  # flatten + escape helpers for CSV export.
            data_exporter=DataExporter,  # write_with_format_selection CSV writer.
        )
    )
    return VirtualChassisManager  # Canonical class ready for menu callback dispatch.


# ============================================================================
# SITE CONFIGURATION MANAGER CLASS
# ============================================================================
# NOTE: SiteConfigManager facade removed per 1013 SC-003 (Cat A, position 3).
# Canonical class lives at src/site/site_config_manager.py and is imported at
# top-of-file. DI wiring lives in _configure_site_config_manager() below
# (single seam for menu 171/172/173/174 lambdas).
def _configure_site_config_manager() -> type[SiteConfigManager]:
    """Wire SiteConfigDependencies and return the canonical SiteConfigManager class."""
    _configure_site_config_dependencies(
        _SiteConfigDependencies(  # Frozen container of 7 injected collaborators
            apisession=apisession,  # Live Mist API session
            config_utils=ConfigUtils,  # Org id caching + stop-signal check
            file_path_utils=FilePathUtils,  # Portable CSV path resolver
            input_utils=InputUtils,  # Safe input for destructive confirmations
            data_exporter=DataExporter,  # Result-report writer
            mistapi=mistapi,  # Root SDK module for calls + pagination
            default_api_page_limit=DEFAULT_API_PAGE_LIMIT,  # Bulk fetch page size
        )
    )
    return SiteConfigManager  # Canonical class ready for menu callback dispatch


# DeviceRebootManager moved to src/device/device_reboot_manager.py (1013 SC-001 position 41)


# The standalone function reboot_devices_by_gateway_template_list() has been
# refactored into DeviceRebootManager class methods.


# NOTE: FirmwareManager facade removed per 1013 SC-002 (Cat A, position 2).
# Canonical class lives at src/firmware/firmware_manager.py and is imported at top-of-file.
# DI wiring lives in _build_firmware_manager() below (single seam for menu 137/154/155/156
# plus the internal src re-check call via _MH._build_firmware_manager).
def _build_firmware_manager(session: Any, target_org_id: str) -> FirmwareManager:
    """Build a fully DI-wired FirmwareManager instance for menu callbacks and internal re-checks."""
    logging.debug("Building firmware manager impl for org %s", target_org_id)  # Trace factory build
    _configure_gateway_module()  # 1014 P13: DI wire canonical gateway module before packaging bound method.
    fw_config = FirmwareManagerConfig(  # Frozen value-object carries identity + six DI hooks
        apisession=session,  # Live Mist API session passed through
        org_id=target_org_id,  # Target organization identifier
        safe_input_fn=InputUtils.safe_input,  # EOF-safe prompt helper
        select_site_fn=PromptUtils.select_site,  # Interactive site picker
        check_cache_fn=CacheUtils.check_and_generate_csv,  # Validate/refresh cached CSV
        get_csv_path_fn=FilePathUtils.get_csv_path,  # Resolve data/ output paths
        gateway_templates_fn=GatewayExportUtils.templates,  # Fetch gateway templates
        sites_fn=OrgSiteExporter.sites,  # Fetch org site list
    )
    return FirmwareManager(fw_config)  # Single-positional-arg constructor per FR-014


# NOTE: check_firmware_upgrade_status_direct removed - use FirmwareManager.create(apisession, org_id).check_firmware_upgrade_status()  # noqa: E501

# NOTE: FirmwareUpgradeStatusChecker folded into src/firmware/firmware_manager.py per SC-019.
# Callers should use FirmwareManager.create(apisession, org_id).check_firmware_upgrade_status().

# NOTE: check_firmware_upgrade_status_impl removed - refactored into FirmwareUpgradeStatusChecker,
# which now lives at src/firmware/firmware_manager.py.

# NOTE: get_auto_upgrade_time_settings removed - dead code (never called)

# NOTE: The standalone functions bulk_upgrade_ap_firmware_by_site() and
# bulk_upgrade_switch_firmware_by_site() have been refactored. Menu entries
# now call FirmwareManager class methods directly.


# NOTE: BulkAPFirmwareUpgrader wrapper removed - folded into
# src/firmware/firmware_manager.py::FirmwareManager._dispatch_bulk_ap_upgrade
# per initiative 1011 SC-022 (FR-015 fold-in eliminates wrapper shim).


# NOTE: bulk_upgrade_ap_firmware_by_site_impl removed - use BulkAPFirmwareUpgrader class directly


# NOTE: MSPInventoryExporter has been extracted to src/export/msp_inventory_exporter.py (issue #1013 SC-001 position 8)


# NOTE: SiteAutoUpgradeConfigurator facade removed (1014 P2, Cat A) - canonical body at
# src/firmware/site_auto_upgrade.py:105. Menu 168 now inlines DI via lambda (see below).


# NOTE: OrgLevelAPFirmwareUpgrader facade removed per initiative 1014 SC-001 position 7
# (FR-004 fold-in / FR-003 no wrapper shim). The canonical body lives at
# src/firmware/org_ap_upgrader.py; menu 157 + menu 168 callbacks now build the
# implementation directly via _build_org_ap_upgrader() and inline DI.


def _build_org_ap_upgrader(**overrides: Any) -> _OrgLevelAPFirmwareUpgrader:
    """Construct an OrgLevelAPFirmwareUpgrader with MistHelper.py DI wiring.

    Callers may override ``org_id``, ``dry_run``, ``msp_privileges``, or
    ``selected_msp`` via keyword. All remaining hooks bind to canonical
    MistHelper.py collaborators.
    """
    global msp_privileges, apisession, selected_msp  # noqa: PLW0602  # WHY: read module globals
    kwargs: dict[str, Any] = dict(  # WHY: build DI kwargs dict for src class
        org_id=ConfigUtils.get_cached_or_prompted_org_id() or "",
        apisession=apisession,
        dry_run=getattr(globals().get("args", None), "dry_run", False),
        safe_input_fn=InputUtils.safe_input,
        check_stop_fn=ConfigUtils.check_stop_signal,
        get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
        fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
        write_results_fn=DataExporter.write_with_format_selection,
        is_debug_fn=IsDebugMode.check,
        msp_privileges=msp_privileges if msp_privileges else [],
        selected_msp=selected_msp if selected_msp else None,
    )
    kwargs.update(overrides)  # WHY: caller overrides win over defaults
    return _OrgLevelAPFirmwareUpgrader(**kwargs)  # WHY: single src-class construction path


# NOTE: BulkSwitchFirmwareUpgrader folded into FirmwareManager per initiative 1011 SC-033
# (FR-015: fold-in to caller; FR-003: no wrapper shim). Sole caller now dispatches directly
# to src.firmware.bulk_switch_upgrader.BulkSwitchFirmwareUpgrader.


# BulkRadiusWLANConfigManager moved to src/site/bulk_radius_wlan_config_manager.py (1013 SC-001 position 15)


# SiteAnalyticsConfigurator and SiteInventoryHealthAnalyzer were extracted to
# src/analytics/site_analytics_configurator.py and
# src/analytics/site_inventory_health_analyzer.py for phase-1 decomposition.


def _ws_cmd_deps() -> WebSocketCmdDeps:
    """Create WebSocket command dependency context for the dispatch table."""
    import mistapi.api.v1.sites.devices as _site_devices  # noqa: PLC0415

    return WebSocketCmdDeps(
        apisession=apisession,
        select_site_fn=PromptUtils.select_site_id_from_csv,
        select_device_fn=PromptUtils.select_device_id_from_inventory,
        validate_target_fn=ValidationUtils.validate_ping_target,
        list_devices_fn=_site_devices.listSiteDevices,
        safe_input_fn=InputUtils.safe_input,
    )


# ============================================================================
# AUDIT ANALYSIS OPS CLASS
# ============================================================================
# NOTE: AuditAnalysisOps has been extracted to
# src/audit/audit_analysis_ops.py (issue #1013 SC-001 position 12)


menu_actions: "dict[str, tuple[Callable[..., Any], str]]" = {
    # ==============================
    # SYSTEM OPERATIONS
    # ==============================
    "0": (lambda: sys.exit(0), "Exit MistHelper"),
    # ==============================
    # SITE ADDRESS AUDIT (read-only)
    # ==============================
    "195": (
        lambda: AddressAuditEngine().run(apisession, ConfigUtils.get_cached_or_prompted_org_id()),
        "Audit site addresses from CSV (data/) - fuse Mist + SNMP + CSV hints, verify vs. web; READ-ONLY, saves report. Tier-3 browser geocoding auto-engages when available (ADDRESS_AUDIT_GEOCODE=off to skip)",  # noqa: E501
    ),
    # ==============================
    # READ-ONLY OPERATIONS
    # ==============================
    # > Setup & Core Logs
    "20": (OrgAlarmEventExporter.alarms, "Export all organization alarms from the past day"),
    "21": (OrgAlarmEventExporter.device_events, "Export all device events from the past 24 hours"),
    "22": (
        lambda: OrgExportUtils.audit_logs(full_history=False),
        "Export audit logs for the organization (last 24 hours)",
    ),
    "31": (
        _dispatch_gateway_management_ips,  # 1014 P13: DI-wiring shim (cascades to canonical GatewayExportUtils)
        "Export gateway management overlay IPs grouped by template association",
    ),
    # > WebSocket Device Commands
    "102": (
        lambda: MacTableCommand.execute(_ws_cmd_deps()),
        "Show MAC table on switch device via WebSocket (Layer 2 switching table)",
    ),
    "103": (
        lambda: RoutingUtils(
            RoutingDeps(
                apisession=apisession,
                select_site_fn=PromptUtils.select_site_id_from_csv,
                select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(
                    site_id, device_type=dtype
                ),
                safe_input_fn=InputUtils.safe_input,
                websocket_manager_factory=WebSocketManager,
                check_fn=IsDebugMode.check,
            )
        ).execute_show_forwarding_table(),
        "Show forwarding table on gateway device via WebSocket (Layer 3 routing table)",
    ),
    "104": (
        lambda: RoutingUtils(
            RoutingDeps(
                apisession=apisession,
                select_site_fn=PromptUtils.select_site_id_from_csv,
                select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(
                    site_id, device_type=dtype
                ),
                safe_input_fn=InputUtils.safe_input,
                websocket_manager_factory=WebSocketManager,
                check_fn=IsDebugMode.check,
            )
        ).execute_show_routing_table(),
        "Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static)",
    ),
    "105": (
        lambda: RoutingUtils(
            RoutingDeps(
                apisession=apisession,
                select_site_fn=PromptUtils.select_site_id_from_csv,
                select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(
                    site_id, device_type=dtype
                ),
                safe_input_fn=InputUtils.safe_input,
                websocket_manager_factory=WebSocketManager,
                check_fn=IsDebugMode.check,
            )
        ).execute_show_ssr_routes(),
        "Show SSR/SRX routing table via dedicated API (128T/SRX gateways - Advanced BGP analysis)",
    ),
    # > Packet Capture Operations
    "134": (
        lambda: PacketCaptureManager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).start_site_packet_capture(),
        "Start Site Packet Capture - Wireless/Wired/Gateway/Scan captures with WebSocket streaming",
    ),
    "135": (
        lambda: PacketCaptureManager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).start_org_packet_capture(),
        "Start Organization Packet Capture - MxEdge captures for org-level Mist Edges only",
    ),
    # Organization-Level Exports
    "1": (OrgSiteExporter.sites, "Export a list of all sites in the organization"),
    "8": (OrgInventoryExporter.inventory, "Export the full inventory of devices in the organization"),
    "15": (OrgDeviceStatsExporter.device_stats, "Export statistics for all devices in the organization"),
    "19": (OrgDeviceStatsExporter.device_port_stats, "Export port-level statistics for switches and gateways"),
    "16": (OrgDeviceStatsExporter.vpn_peer_stats, "Export VPN peer path statistics for the organization"),
    # Gateway & Site-Wide Exports
    # Direct reference (removed lambda) so systematic test harness can introspect 'fast' parameter
    "33": (GatewayTestExporter.synthetic_tests, "Export synthetic test results for all gateways"),
    "9": (OrgInventoryExporter.devices, "Export a list of all devices in the organization"),
    "59": (SiteConfigExporter.settings, "Export configuration settings for all sites"),
    "34": (
        GatewayTestExporter.test_results_by_site,
        "Export all synthetic test results (including speed tests) for gateways",
    ),
    # > Location-Enriched Exports
    "2": (OrgSiteExporter.sites_with_location, "Export a list of sites with location and timezone info"),
    "11": (
        OrgInventoryExporter.gateways_with_site_info,
        "Export a list of gateways with associated site and address info",
    ),
    "10": (
        OrgInventoryExporter.devices_with_site_info,
        "Export a list of all devices with associated site and address info",
    ),
    "4": (
        lambda: (OrgSiteExporter.current_guests(), OrgSiteExporter.historical_guests()),
        "Export all current guest users and last 7 days of historical guests to CSV",
    ),
    "17": (OrgDeviceStatsExporter.switch_vc_stats, "Export all switch virtual chassis (VC/stacking) stats to CSV"),
    "12": (
        OrgInventoryExporter.combined_inventory_with_site_info,
        "Export combined inventory with site and address info by calendar week",
    ),
    "32": (_dispatch_gateway_templates, "Export gateway templates from the organization"),
    "3": (
        OrgSiteExporter.sites_list_api,
        "Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)",
    ),
    "35": (
        _dispatch_gateway_with_wan_overrides,  # 1014 P13: DI-wiring shim (cascades to canonical)
        "Find gateway ports overridden from template (outliers for compliance correction)",
    ),
    # Site-Specific Data Exports
    "62": (SiteDeviceExporter.port_stats, "Export port statistics for a selected site"),
    "65": (SiteClientExporter.clients, "Export client statistics for a selected site"),
    "60": (SiteDeviceExporter.devices, "Export device list for a selected site"),
    "61": (SiteDeviceExporter.device_stats, "Export device statistics for a selected site"),
    "63": (
        SiteDeviceExporter.device_virtual_chassis,
        "Export virtual chassis information for a selected switch device",
    ),
    "64": (
        SiteClientExporter.wifi_clients,
        "Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV",
    ),
    # Organization Template Exports
    "37": (OrgTemplateExporter.all_templates, "Export all organization templates (gateway, network, RF, site, AP)"),
    "38": (OrgTemplateExporter.network_templates, "Export network template information for the organization"),
    "39": (OrgTemplateExporter.rf_templates, "Export RF template information for the organization"),
    "40": (OrgTemplateExporter.ap_templates, "Export AP template information for the organization"),
    "41": (OrgTemplateExporter.switch_templates, "Export switch template information for the organization"),
    # Organization Statistics & Analytics
    "27": (OrgClientSecurityExporter.wireless_clients, "Export wireless client statistics for the organization"),
    "28": (OrgClientSecurityExporter.wired_clients, "Export wired client statistics for the organization"),
    # Security & Monitoring
    "24": (OrgClientSecurityExporter.security_events, "Export security events for the organization"),
    "29": (OrgClientSecurityExporter.rogue_clients, "Export rogue client detections for the organization"),
    "30": (OrgClientSecurityExporter.rogue_aps, "Export rogue AP detections for the organization"),
    # Configuration & Management (Read-Only)
    "42": (OrgAdminExporter.licenses, "Export license information for the organization"),
    "196": (
        LicenseExportUtils.export_org_license_async_claim_status,
        "Export async organization license-claim status summary (and optional per-device details)",
    ),
    "44": (OrgConfigExporter.psks, "Export PSK (Pre-Shared Key) information for the organization"),
    "45": (OrgConfigExporter.webhooks, "Export webhook configuration for the organization"),
    "46": (OrgConfigExporter.wlans, "Export WLAN configuration for the organization"),
    "69": (SiteConfigExporter.wlans, "Export WLAN configuration for a selected site"),
    "66": (SiteClientExporter.beacons, "Export beacon information for a selected site"),
    "67": (SiteConfigExporter.maps, "Export map information for a selected site"),
    "68": (SiteConfigExporter.zones, "Export zone information for a selected site"),
    "73": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).insights(),
        "Export SLE (Service Level Experience) metrics insights for a selected site",
    ),
    # ==============================
    # GATEWAY TEMPLATE VARIABLE OPERATIONS
    # ==============================
    "149": (
        lambda: WAN2MigrationLauncher().launch(),
        "Set WAN2 Interface Site Variable - Configure 'wan2_interface' site variable for template-based WAN migration (Reports sites with ge-0/0/1 overrides)",  # noqa: E501
    ),
    "163": (
        _dispatch_gateway_wan2_variable_migration,  # 1014 P13: DI-wiring shim (cascades to canonical)
        " DESTRUCTIVE: Update Gateway Templates to Use WAN2 Variable - Replace hardcoded 'ge-0/0/1' references with {{wan2_interface}} variable (Requires uppercase 'MIGRATE' confirmation, supports --dry-run)",  # noqa: E501
    ),
    "150": (
        lambda: GatewayTemplateConfigManager(
            org_id=ConfigUtils.get_cached_or_prompted_org_id(),
            apisession=apisession,
            input_fn=InputUtils.safe_input,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            save_data_fn=DataExporter.write_with_format_selection,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            generate_sites_fn=OrgSiteExporter.sites,
            sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename,
        ).extract(),
        "Extract Gateway Template Configuration (DIA_Pico, Picocell) - Save specific configs to JSON for replication",
    ),
    "164": (
        lambda: GatewayTemplateConfigManager(
            org_id=ConfigUtils.get_cached_or_prompted_org_id(),
            apisession=apisession,
            input_fn=InputUtils.safe_input,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            save_data_fn=DataExporter.write_with_format_selection,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            generate_sites_fn=OrgSiteExporter.sites,
            sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename,
        ).apply(),
        " DESTRUCTIVE: Apply Gateway Template Configuration - Replicate extracted configs to other templates (Requires uppercase 'APPLY' confirmation)",  # noqa: E501
    ),
    "148": (
        lambda: WLANRadiusTimerManager().manage(),
        "Manage WLAN RADIUS Authentication Timers - Configure auth_servers_timeout, auth_servers_retries, auth_server_selection, and fast_dot1x_timers for site or template WLANs",  # noqa: E501
    ),
    # Authentication Management
    "143": (
        lambda: SwitchToInteractiveLoginManager().run(),
        "Switch to interactive login (email/password) - Enables MSP-level API access for current session",
    ),
    # Organization Management (Read-Only)
    "47": (OrgAdminExporter.api_tokens, "Export API token information for the organization"),
    "48": (OrgAdminExporter.admins, "Export administrator information for the organization"),
    "136": (
        OrgConfigExporter.msp,
        "MSP (Managed Service Provider) info - Displays guidance only (MSP data requires MSP-level API access, not org-level)",  # noqa: E501
    ),
    "49": (OrgAdminExporter.sso, "Export SSO (Single Sign-On) information for the organization"),
    "43": (OrgAdminExporter.usage, "Export license usage information for the organization"),
    "50": (OrgConfigExporter.mx_edges, "Export MX Edge information for the organization"),
    # Status & Monitoring
    "137": (
        lambda: _build_firmware_manager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).check_firmware_upgrade_status(),
        "Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV",
    ),
    "138": (
        lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: InventoryCSVComparator(
            fast=fast, address_check=address_check, debug=debug, skip_ssl_verify=skip_ssl_verify
        ).execute(),
        "Compare inventory data with external CSV file using configurable address similarity threshold (ADDRESS_MATCH_THRESHOLD in .env)",  # noqa: E501
    ),
    "139": (
        TroubleshootUtils.launch_interactive,
        "Interactive Marvis (VNA) AI troubleshooting - guided client, device, and network analysis",
    ),
    # Long-Running Export Operations (Read-Only)
    "97": (
        OrgAlarmEventExporter.device_events_52w,
        "Export all org device events from the last 52 weeks (streaming with checkpoint/resume)",
    ),
    "98": (
        lambda: OrgExportUtils.audit_logs(full_history=True, duration="52w"),
        "Export ALL audit logs for the organization (last 52 weeks)",
    ),
    "99": (
        _dispatch_gateway_device_configs,  # 1014 P13: DI-wiring shim (cascades to canonical)
        "Export configuration details for all gateway devices across all sites",
    ),
    # ==============================
    # UNSAFE/INTERACTIVE OPERATIONS
    # ==============================
    # > Site Selection & Interactive Tools
    "92": (PromptUtils.select_site_with_logging, "Select a site (used by other functions)"),
    "93": (InteractiveDisplayUtils.site_inventory, "View device inventory for a selected site"),
    "94": (InteractiveDisplayUtils.device_stats, "View statistics for a selected device at a site"),
    "95": (InteractiveDisplayUtils.device_tests, "View synthetic test stats for a selected gateway device"),
    "96": (InteractiveDisplayUtils.device_config, "View configuration details for a selected device"),
    # > Continuous Operations & Monitoring
    "151": (
        DataCollectionManager.continuous_loop,
        "Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt'",  # noqa: E501
    ),
    "152": (
        DataCollectionManager.continuous_loop,
        "Run continuous data collection loop (5 core API calls with rate limiting)",
    ),
    # > File Processing & Support Operations
    "100": (
        SFPTransceiverDataProcessor.merge_transceiver_data,
        "Process and merge CSV files of SFP Module locations into a single CSV file",
    ),
    "101": (DataCollectionManager.generate_support_packages, "Generate support package for each site"),
    # > CLI & WebSocket Operations
    "140": (CLIShellManager.launch, "Interactively execute a CLI command on a gateway or switch (exit with ~)"),
    "121": (ARPCommandManager.execute, "Run ARP command on an AP and receive output via WebSocket"),
    # ! DESTRUCTIVE OPERATIONS - USE WITH EXTREME CAUTION
    "154": (
        lambda: _build_firmware_manager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_firmware_upgrade_with_mode_selection(),
        " DESTRUCTIVE: Advanced AP firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment",  # noqa: E501
    ),
    "158": (
        DeviceRebootManager.by_gateway_template_list,
        " DESTRUCTIVE: Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results",  # noqa: E501
    ),
    "161": (
        lambda dry_run=False: _configure_virtual_chassis_manager().launch_convert_single(dry_run=dry_run),
        " DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive, supports --dry-run)",
    ),
    "162": (
        lambda: _configure_virtual_chassis_manager().launch_convert_by_site_list(),
        " DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation)",
    ),
    "14": (
        lambda: _configure_virtual_chassis_manager().launch_check_status(),
        "Check virtual chassis to virtual MAC conversion status for all switches",
    ),
    "18": (
        lambda fast=False: _dispatch_gateway_stats_device_stats_with_freshness(fast=fast),
        "Export detailed device statistics for all gateways (with freshness check)",
    ),
    "36": (
        _dispatch_gateway_stats_wan_port_conflicts,
        "Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2)",
    ),
    "175": (
        lambda: SSHRunnerManager.interactive(_build_ssh_runner_deps()),
        "Enhanced SSH Command Runner - Execute commands on remote network devices via SSH",
    ),
    "176": (
        # Wire menu directly to canonical SSH runner impl (facade wrapper removed, 1014 P15).
        lambda: SSHRunnerManager.by_gateway_template(_build_ssh_runner_deps()),
        "SSH Runner - Target gateways by template name (online gateways with management IPs only)",
    ),
    # ==============================
    # INSIGHTS API OPERATIONS - Organization & Site Analytics
    # ==============================
    "51": (OrgExportUtils.sle_metrics, "Export Organization SLE Metrics (Service Level Experience)"),
    "52": (OrgExportUtils.sites_sle_summary, "Export SLE summary metrics for all sites in the organization"),
    "74": (
        lambda: SiteMetricOperation(
            apisession=apisession,
            PromptUtils=PromptUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            mistapi=mistapi,
        ).execute(),
        "Export general insight metrics for a selected site",
    ),
    "75": (SiteClientExporter.client_insights, "Export client-specific insight metrics for a selected site"),
    "76": (
        lambda: DeviceMetricOperation(
            apisession=apisession,
            PromptUtils=PromptUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            mistapi=mistapi,
        ).execute(),
        "Export device-specific insight metrics for a selected site",
    ),
    "54": (
        lambda: ConstDefinitionsExporter(apisession).export_all(),
        "Export all available const definitions from the Mist API (comprehensive endpoint coverage)",
    ),
    "53": (OrgExportUtils.insight_metrics, "Export Organization Insight Metrics (comprehensive operational insights)"),
    "77": (
        SiteAnomalyExporter.anomaly_events,
        "Export Site Anomaly Events (dynamic discovery of all anomaly-related metrics from Mist API)",
    ),
    "78": (
        SiteAnomalyExporter.device_anomaly_events,
        "Export Site Device Anomaly Events (device-specific anomaly detection)",
    ),
    "79": (
        SiteAnomalyExporter.client_anomaly_events,
        "Export Site Client Anomaly Events (client-specific anomaly detection: connectivity, roaming, throughput)",
    ),
    "118": (
        lambda: PingDeviceExecutor().execute(_ws_cmd_deps()),
        "WebSocket Device Ping - Execute ping command on device via WebSocket stream (real-time output)",
    ),
    "119": (
        lambda: ArpDeviceExecutor().execute(_ws_cmd_deps()),
        "WebSocket Device ARP - Execute ARP command on device via WebSocket stream (real-time output)",
    ),
    "120": (
        lambda: ServicePingLauncher().launch(),
        "WebSocket Service Ping - Execute service-specific ping on SSR gateways via WebSocket stream (real-time output)",  # noqa: E501
    ),
    # ==============================
    # POST API OPERATIONS - Device Commands (Starting at 100)
    # ==============================
    # Device Network Operations removed (options 100, 101)
    # ==============================
    # SWITCH FIRMWARE OPERATIONS
    # ==============================
    "155": (
        lambda: _build_firmware_manager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_switch_firmware_upgrade_with_mode_selection(),
        " DESTRUCTIVE: Advanced Switch firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment",  # noqa: E501
    ),
    # ==============================
    # SSR FIRMWARE OPERATIONS
    # ==============================
    "156": (
        lambda: _build_firmware_manager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_ssr_firmware_upgrade_with_mode_selection(),
        " DESTRUCTIVE: Advanced SSR firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment",  # noqa: E501
    ),
    # ==============================
    # TERMINAL USER INTERFACE MODE
    # ==============================
    "141": (
        lambda: TUILauncher().launch(),
        "Launch Terminal User Interface (TUI) mode - Visual navigation of Mist API library with interactive exploration",  # noqa: E501
    ),
    # ==============================
    # TEST DATA GENERATION
    # ==============================
    "171": (
        lambda: _configure_site_config_manager().create_test_sites_from_csv(),
        " DESTRUCTIVE: Create 137 test sites from NorthAmericanTestSites.csv - Real landmarks across 13 North American countries (Requires uppercase 'CREATE' confirmation)",  # noqa: E501
    ),
    "172": (
        lambda: _configure_site_config_manager().create_country_rf_templates_and_assign(),
        " DESTRUCTIVE: Create country-specific RF templates and assign sites to matching templates (Requires uppercase 'CREATE' confirmation)",  # noqa: E501
    ),
    "173": (
        lambda: _configure_site_config_manager().create_ap_model_device_profiles(),
        " DESTRUCTIVE: Scan org for AP models and create Device Profile per model with inherit/auto settings (Requires uppercase 'CREATE' confirmation)",  # noqa: E501
    ),
    "174": (
        lambda: _configure_site_config_manager().assign_aps_to_matching_device_profiles(),
        " DESTRUCTIVE: Assign APs to Device Profiles matching their model type (AP-{model}) - Skips APs without matching profiles (Requires uppercase 'ASSIGN' confirmation)",  # noqa: E501
    ),
    "165": (
        lambda: GatewayTemplateConfigManager(
            org_id=ConfigUtils.get_cached_or_prompted_org_id(),
            apisession=apisession,
            input_fn=InputUtils.safe_input,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            save_data_fn=DataExporter.write_with_format_selection,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            generate_sites_fn=OrgSiteExporter.sites,
            sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename,
        ).clone_by_location(),
        " DESTRUCTIVE: Clone Gateway Template by State and Country - Create state/country-specific templates and assign sites (Requires uppercase 'CLONE' confirmation)",  # noqa: E501
    ),
    "166": (
        lambda dry_run=False: WANProbeConfigManager.configure(dry_run=dry_run),
        " DESTRUCTIVE: Configure WAN Probe Override on Gateway Templates - Set ICMP probe IPs and profile for all WAN interfaces (Requires uppercase 'APPLY' confirmation, supports --dry-run)",  # noqa: E501
    ),
    "167": (
        lambda dry_run=False: WANProbeDeviceOverrideManager.configure(dry_run=dry_run),
        " DESTRUCTIVE: Configure WAN Probe on Device Port Overrides - Set ICMP probe on device-level WAN overrides only (Requires uppercase 'APPLY' confirmation, supports --dry-run)",  # noqa: E501
    ),
    # ==============================
    # ORG-LEVEL FIRMWARE OPERATIONS
    # ==============================
    "157": (
        lambda: _build_org_ap_upgrader().run(),
        " DESTRUCTIVE: Org-Level AP Firmware Upgrade - Efficient multi-site upgrade using org-level API (1 call per version vs 1 per site), MSP multi-org support, supports --dry-run",  # noqa: E501
    ),
    # ==============================
    # MSP OPERATIONS
    # ==============================
    "144": (
        MSPInventoryExporter.execute,
        "MSP Inventory Export - Export device inventory across all MSPs and all organizations to CSV (requires MSP privileges via --login)",  # noqa: E501
    ),
    # ==============================
    # SITE AUTO-UPGRADE CONFIGURATION
    # ==============================
    "168": (
        lambda: SiteAutoUpgradeConfigurator.execute(
            apisession=apisession,
            msp_privileges=msp_privileges if msp_privileges else [],
            safe_input_fn=InputUtils.safe_input,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            check_stop_fn=ConfigUtils.check_stop_signal,
            dry_run=getattr(globals().get("args", None), "dry_run", False),
            select_msps_fn=lambda: _build_org_ap_upgrader(org_id="")._select_msps(),
            select_orgs_fn=lambda msp: _build_org_ap_upgrader(org_id="")._select_orgs_from_msp(msp),
        ),
        "Site Auto-Upgrade Configuration - Configure AP auto-upgrade settings for sites with MSP multi-org support (supports --dry-run)",  # noqa: E501
    ),
    # ==============================
    # ZONE & ENGAGEMENT CONFIGURATION ANALYSIS
    # ==============================
    "6": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).zone_config_analysis(),
        "Site Config Analysis - Scan all sites for zone, engagement dwell tag, and occupancy setting deviations",
    ),
    # ==============================
    # SITE ANALYTICS CONFIGURATION (DESTRUCTIVE)
    # ==============================
    "169": (
        lambda: ExtractedSiteAnalyticsConfigurator.execute(
            SiteAnalyticsConfiguratorDeps(
                apisession=apisession,
                mistapi=mistapi,
                get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
                check_stop_fn=ConfigUtils.check_stop_signal,
                safe_input_fn=InputUtils.safe_input,
                all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
                save_data_fn=DataExporter.write_with_format_selection,
                tqdm_fn=tqdm,
            )
        ),
        " DESTRUCTIVE: Site Analytics Configuration - Apply standard RTSA/Rogue/Engagement/Occupancy settings to deviating sites",  # noqa: E501
    ),
    # ==============================
    # SITE INVENTORY HEALTH ANALYSIS
    # ==============================
    "7": (
        lambda: ExtractedSiteInventoryHealthAnalyzer.analyze(
            SiteInventoryHealthAnalyzerDeps(
                apisession=apisession,
                mistapi=mistapi,
                get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
                all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
                save_data_fn=DataExporter.write_with_format_selection,
            )
        ),
        "Site Inventory Health Analysis - Find sites with APs missing switches/gateways, or with offline infrastructure",  # noqa: E501
    ),
    # ==============================
    # BULK RADIUS WLAN CONFIGURATION
    # ==============================
    "170": (
        lambda dry_run=False: BulkRadiusWLANConfigManager().manage(dry_run=dry_run),
        "Bulk RADIUS WLAN Configuration - Configure auth_servers_timeout, auth_servers_retries, fast_dot1x_timers for org-level RADIUS WLANs",  # noqa: E501
    ),
    # ==============================
    # MAPS MANAGER (External Module)
    # ==============================
    "142": (
        lambda: MapsManagerLauncher().launch(),
        "Maps Manager - Interactive site floorplan and map operations (sub-menu)",
    ),
    # ==============================
    # DEVICE UTILITY COMMANDS (Menus 123-157)
    # ==============================
    # > Diagnostic Commands
    "123": (lambda: _get_duc_instance().traceroute(), "Traceroute from device to destination host (AP/Switch/Gateway)"),
    "106": (lambda: _get_duc_instance().show_ospf_neighbors(), "Show OSPF Neighbors on SSR/SRX Gateway"),
    "107": (lambda: _get_duc_instance().show_ospf_interfaces(), "Show OSPF Interfaces on SSR/SRX Gateway"),
    "108": (lambda: _get_duc_instance().show_ospf_database(), "Show OSPF Database on SSR/SRX Gateway"),
    "109": (lambda: _get_duc_instance().show_ospf_summary(), "Show OSPF Summary on SSR/SRX Gateway"),
    "117": (lambda: _get_duc_instance().resolve_dns(), "Test DNS Resolution on SSR Gateway"),
    "124": (
        lambda: _get_duc_instance().monitor_traffic(),
        "Monitor Traffic on Switch/SRX Port (streaming, Ctrl+C to stop)",
    ),
    "125": (lambda: _get_duc_instance().run_top(), "Run Top Command on Switch/SRX (streaming, Ctrl+C to stop)"),
    # > Show Commands
    "110": (lambda: _get_duc_instance().show_session(), "Show Sessions on SSR/SRX Gateway"),
    "111": (lambda: _get_duc_instance().show_service_path(), "Show Service Path on SSR Gateway"),
    "112": (lambda: _get_duc_instance().show_bgp_summary(), "Show BGP Summary on Switch or Gateway"),
    "113": (lambda: _get_duc_instance().show_arp_table(), "Show ARP Table on Switch or Gateway"),
    "114": (lambda: _get_duc_instance().show_dhcp_leases(), "Show DHCP Leases on Switch or Gateway"),
    "115": (lambda: _get_duc_instance().show_dot1x(), "Show 802.1X Table on Switch"),
    "116": (lambda: _get_duc_instance().show_evpn_database(), "Show EVPN Database on Switch or Gateway"),
    # > Management Commands
    "128": (lambda: _get_duc_instance().locate_device(), "Locate Device - Blink LED on AP or Switch"),
    "129": (lambda: _get_duc_instance().unlocate_device(), "Unlocate Device - Stop LED Blinking on AP or Switch"),
    "159": (lambda: _get_duc_instance().bounce_port(), " Bounce Switch/Gateway Port (y/N confirmation)"),
    "122": (lambda: _get_duc_instance().cable_test(), "Cable Test on Switch Port"),
    "160": (lambda: _get_duc_instance().reprovision_device(), " Reprovision Switch/Gateway (y/N confirmation)"),
    "130": (lambda: _get_duc_instance().readopt_device(), "Re-adopt Switch Device"),
    "131": (lambda: _get_duc_instance().get_ztp_password(), "Get ZTP Password for Switch/Gateway (console only)"),
    "132": (lambda: _get_duc_instance().get_config_commands(), "Get Config CLI Commands for Switch Adoption"),
    "133": (lambda: _get_duc_instance().upload_support_file(), "Upload Support File from Switch/Gateway"),
    # > Clear/Reset Commands
    "177": (lambda: _get_duc_instance().clear_arp_cache(), " DESTRUCTIVE: Clear ARP Cache (type CLEAR)"),
    "178": (lambda: _get_duc_instance().clear_bgp_routes(), " DESTRUCTIVE: Clear BGP Routes (type CLEAR)"),
    "179": (lambda: _get_duc_instance().clear_session(), " DESTRUCTIVE: Clear Session on SSR/SRX (type CLEAR)"),
    "180": (lambda: _get_duc_instance().clear_mac_table(), " DESTRUCTIVE: Clear MAC Table (type CLEAR)"),
    "181": (lambda: _get_duc_instance().clear_bpdu_error(), " DESTRUCTIVE: Clear BPDU Errors on Switch (type CLEAR)"),
    "182": (
        lambda: _get_duc_instance().clear_learned_macs(),
        " DESTRUCTIVE: Clear Learned MACs from Switch Port (type CLEAR)",
    ),
    "183": (
        lambda: _get_duc_instance().clear_policy_hit_count(),
        " DESTRUCTIVE: Clear Policy Hit Count on SSR (type CLEAR)",
    ),
    "184": (lambda: _get_duc_instance().release_dhcp_lease(), " Release DHCP Lease on Switch/Gateway (y/N)"),
    "185": (lambda: _get_duc_instance().release_dhcp_ssr(), " Release DHCP Lease on SSR/SRX (y/N)"),
    # > Hardware Commands
    "126": (lambda: _get_duc_instance().poll_switch_stats(), "Poll Fresh Statistics from Switch"),
    "127": (lambda: _get_duc_instance().create_device_snapshot(), "Create Device Snapshot on Switch"),
    # > Offline / Reporting
    "26": (OfflineDeviceReporter.execute, "Offline Device Report"),
    "145": (OrgExportUtils.ssid_template_consolidation, "SSID Template Consolidation (5-Phase Guided Workflow)"),
    "89": (OrgExportUtils.e911_bssid_compliance_report, "E911 BSSID Compliance Report"),
    "90": (GlobalWiredClientReportGenerator.execute, "Global Wired Client Report (operator-based MAC/MFG filtering)"),
    "91": (
        WiredClientManufacturerReportGenerator.execute,
        "Wired Client Manufacturer Report (browse & select)",
    ),
    "146": (
        lambda: WanHubGroupNumberManager.execute(
            apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ),
        "WAN Hub Group Number Manager",
    ),
    "147": (
        lambda: WanVpnBuilder.execute(apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input),
        "WAN Hub-Spoke VPN Builder",
    ),
    # > Bulk Data Collection
    "153": (
        lambda: OrgDataCollector.execute(
            OrgExportUtils.export_data, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ),
        "Bulk Org Data Collection (populate ArangoDB/Redis/SQLite with all org-level APIs)",
    ),
    # ==============================
    # MISTAPI 0.62.0 NEW ENDPOINTS
    # ==============================
    "5": (OrgExportUtils.e911_report, "Export E911 report for the organization"),
    "56": (OrgExportUtils.jsi_pbn, "Export JSI PBN (Product Bulletin Notifications) data"),
    "57": (OrgExportUtils.jsi_sirt, "Export JSI SIRT (Security Incident Response) advisories"),
    "55": (OrgExportUtils.ospf_stats, "Export OSPF adjacency statistics for the organization"),
    "70": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).ospf_stats(),
        "Export OSPF adjacency statistics for a selected site",
    ),
    "71": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).mxedge_upgrade_status(),
        "Export MxEdge upgrade status for a selected site",
    ),
    "72": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).auto_map_assignment_status(),
        "Export auto-map assignment status for a selected site",
    ),
    "88": (SitesByAPModelExporter.export_sites_by_ap_model, "Export sites by AP model with site address (CSV)"),
    "25": (AuditAnalysisOps.audit_log_analysis, "Audit Log Analysis - Mermaid timeline + interactive HTML report"),
    "186": (CacheUtils.clear_cache, "Clear CSV Cache Files (delete all generated cache CSVs)"),
    "58": (
        lambda: OrgConfigMigrationManager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ).export_config(),
        "Export Org WAN/Gateway Config (JSON bundle for cross-org migration)",
    ),
    "187": (
        lambda: OrgConfigMigrationManager(
            apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ).import_config(),
        "Import Org WAN/Gateway Config (cross-org migration with conflict detection)",
    ),
    # ==============================
    # SITE STATS, METRICS & CHANNEL PLANNING
    # ==============================
    "80": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).site_stats(),
        "Export site aggregate health & capacity statistics",
    ),
    "81": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).gateway_metrics(),
        "Export site gateway performance metrics summary",
    ),
    "82": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).switches_metrics(),
        "Export site switch performance metrics summary",
    ),
    "83": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).beacons_stats(),
        "Export site BLE beacon statistics",
    ),
    "84": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).wxrules_usage(),
        "Export site WxLAN rule usage statistics",
    ),
    "85": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).assets_stats(),
        "Export site asset statistics",
    ),
    "86": (
        lambda: SiteExportUtils(
            apisession=apisession,
            PromptUtils=PromptUtils,
            ConfigUtils=ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            TimeUtils=TimeUtils,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            APICoreFetchUtils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            PrettyTable=PrettyTable,
            tqdm=tqdm,
            mistapi=mistapi,
        ).current_channel_planning(),
        "Export current RRM channel & power plan per AP radio",
    ),
    "23": (SelfExportUtils.audit_logs, "Export self (admin account) audit log"),
    "87": (GatewayHaExporter.ha_cluster_info, "Export HA gateway cluster info, stats & node pair for a site"),
    "13": (
        OrgDeviceInventorySummary.dispatch,
        "Export org device model counts, firmware version distribution, and versions per model (MSP-aware)",
    ),
    # ==============================
    # SUPPORT TICKETS
    # ==============================
    "188": (OrgTicketManager.list_tickets, "Export all organization support tickets to CSV"),
    "189": (OrgTicketManager.create_ticket, "Create a new organization support ticket"),
    "190": (OrgTicketManager.add_comment, "Add a comment (with optional file attachment) to a support ticket"),
    "191": (OrgTicketManager.update_ticket, "Update fields on an existing support ticket"),
    "192": (OrgTicketManager.view_ticket, "View a support ticket with full comments and history"),
    "193": (OrgTicketManager.export_ticket_details, "Export all tickets with full details and comments"),
    "194": (
        DeviceConfigTemplateClonerManager.clone,  # Delegate to extracted implementation class
        " DESTRUCTIVE: Clone Device Config to Gateway Template"
        " - Select a gateway, extract its local config, and create a new org gateway template"
        " (Requires typing 'CREATE' to confirm)",
    ),
}


# NOTE: TelemetryEmitter has been extracted to src/analytics/telemetry_emitter.py (issue #1013 SC-001 position 9)


# OperationRegistry moved to src/utils/operation_registry.py (1013 SC-001 position 13)


def _systematic_test_build_safe_list(
    all_options: list[str], optimized_test_order: list[str]
) -> tuple[list[str], list[str]]:
    """Build the ordered safe-options list and compute the unsafe skip list for systematic tests."""
    unsafe_list = OperationRegistry.unsafe_options(
        all_options
    )  # Delegate classification to OperationRegistry so business rules stay centralized.
    safe_options_set = set(
        OperationRegistry.safe_options(all_options)
    )  # Build a set for O(1) membership tests during ordering.
    safe_options: list[str] = []  # Will hold options in optimized execution order followed by unordered remainder.
    remaining = set(safe_options_set)  # Clone set so we can discard items as we process them.
    for opt in optimized_test_order:  # Place optimized-order options first to minimize total test run time.
        if opt in remaining:  # Only include options present in the actual safe set.
            safe_options.append(opt)  # Add to the ordered result.
            remaining.discard(opt)  # Remove so it won't appear in the remainder block.
    safe_options.extend(
        sorted(remaining, key=lambda x: float(x.replace("a", ".1")))
    )  # Append all remaining safe options in natural numeric order.
    return safe_options, unsafe_list  # Return both lists so caller can emit skips and run tests.


def _systematic_test_emit_skips(emitter: Any, unsafe_list: list[str]) -> int:
    """Emit a skip event for each unsafe operation and print an explanation."""
    print(" Skipping unsafe operations:")  # Announce the skip section before listing individual items.
    for opt in unsafe_list:  # Iterate every unsafe option so none are silently omitted.
        if opt in menu_actions:  # Guard against stale unsafe lists that reference removed options.
            _, description = menu_actions[opt]  # Unpack action tuple to get the display description.
            reason = OperationRegistry.skip_reason(opt)  # Retrieve structured skip reason text from registry.
            print(
                f"   {opt:>3}: {description[:60]}... (Reason: {reason})"
            )  # Print padded option number with truncated description and reason.
            emitter.emit_test_skip(
                opt, description, reason, OperationRegistry.skip_category(opt), "systematic"
            )  # Record skip in telemetry for coverage reporting.
    print()  # Blank line after skip list for readability.
    return len([opt for opt in unsafe_list if opt in menu_actions])  # Return actual skip count for summary reporting.


def _resolve_systematic_test_invoke_kwargs(func: Any, fast_enabled: bool) -> dict[str, Any]:
    """Inspect a menu function's signature and build invoke kwargs (fast=True only if supported)."""
    supports_fast = False  # Default to no fast-mode support until introspection confirms it.
    try:  # inspect.signature can raise on built-in callables; degrade gracefully.
        sig = inspect.signature(func)  # Detect optional 'fast' parameter
        supports_fast = "fast" in sig.parameters  # True when function accepts fast-mode
    except Exception:  # Signature inspection failure is non-fatal
        supports_fast = False  # Treat as non-fast-capable when signature is uninspectable
    invoke_kwargs: dict[str, Any] = {}  # Build kwargs dict
    if supports_fast and fast_enabled:  # Both function and global mode agree
        invoke_kwargs["fast"] = True  # Activate fast mode for this operation
    return invoke_kwargs


def _invoke_one_systematic_test(
    emitter: Any, case: SystematicTestOption, invoke_kwargs: dict, op_start: float
) -> tuple[bool, float]:
    """Call one menu func with the resolved kwargs; record pass/fail in telemetry and return (success, duration)."""
    option, func, description = case.option, case.func, case.description  # Unpack identity (issue #470)
    try:  # Each option runs independently so one failure does not abort remaining tests
        func(**invoke_kwargs)  # Call menu action
        duration = time.time() - op_start  # Elapsed seconds
        print(f"   [SUCCESS] Option {option} completed successfully")
        emitter.emit_test_pass(option, description, duration, "systematic")  # Record pass
        logging.info("SYSTEMATIC_TEST: Successfully completed menu option %s", option)
        return True, duration
    except Exception as exc:  # Catch all so harness continues
        duration = time.time() - op_start  # Still record elapsed
        print(f"   [FAILED]  Option {option} failed: {str(exc)[:100]}...")
        emitter.emit_test_fail(option, description, duration, exc, "systematic")  # Record failure
        logging.error("SYSTEMATIC_TEST: Failed menu option %s: %s", option, exc)
        return False, duration


def _systematic_test_run_option(
    emitter: Any,
    case: SystematicTestOption,
    i: int,
    total_safe: int,
    fast_enabled: bool,
) -> tuple[bool, float]:
    """Run one menu option in the systematic test harness and return (success, duration)."""
    option, func, description = case.option, case.func, case.description  # Unpack identity (issue #470)
    print(f"   [{i:2}/{total_safe}] Testing option {option:>3}: {description[:60]}...")
    emitter.emit_test_start(option, description, "systematic")  # Telemetry start
    op_start = time.time()  # Capture start time before invocation overhead
    invoke_kwargs = _resolve_systematic_test_invoke_kwargs(func, fast_enabled)  # Signature-aware kwargs
    logging.info(
        "SYSTEMATIC_TEST: INVOKE option=%s fast_supported=%s fast_enabled=%s test_mode=True description='%s'",
        option,
        "fast" in invoke_kwargs,
        fast_enabled,
        description,
    )  # Log invocation details for post-mortem correlation
    return _invoke_one_systematic_test(emitter, case, invoke_kwargs, op_start)


def _fast_mode_from_global() -> bool:
    """Return True iff the module-level ``FAST_MODE_ENABLED`` flag is set (errors -> False)."""
    try:  # globals() access is normally safe but guarded for parity with original.
        return bool(globals().get("FAST_MODE_ENABLED", False))  # Module flag set by CLI parse at startup.
    except Exception:  # Defensive -- never propagate.
        return False  # Safe default for any introspection failure.


def _fast_mode_from_cli_args() -> bool:
    """Return True iff parsed ``args`` exist in globals and carry ``--fast`` (errors -> False)."""
    try:  # CLI args presence + attribute lookup can both fail; degrade safely.
        cli_args = globals().get("args") if "args" in globals() else None  # Locate parsed args, if any.
        return bool(cli_args and getattr(cli_args, "fast", False))  # Truthy only when --fast was set.
    except Exception:  # Defensive -- never propagate.
        return False  # Safe default for any introspection failure.


def _systematic_test_resolve_fast_mode() -> bool:
    """Return whether fast mode is active for the current systematic test run."""
    if _fast_mode_from_global():  # Primary source: module-level flag set at startup.
        return True
    if _fast_mode_from_cli_args():  # Fallback: parsed --fast on CLI args namespace.
        return True
    return False  # Neither source enabled fast mode.


def _print_systematic_banner():
    """Print the test-start banner + timestamp + separator to the operator console."""
    print(" Starting systematic test of MistHelper menu options...")  # Announce test start.
    print(
        "  Note: This will skip interactive, websocket, POST, and destructive operations"
    )  # Set operator expectations.
    print(
        f"! Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )  # Emit timestamped start marker for log correlation.
    print("=" * 80)  # Visual separator before first section.


_SYSTEMATIC_TEST_OPTIMIZED_ORDER = [  # Shortest-running operations first to surface failures early.
    "22",
    "9",
    "1",  # Fast tests (~0.6-3.5 seconds)
    "8",
    "51",
    "52",
    "20",  # Medium tests (~18-30 seconds)
    "15",
    "16",  # Slower tests (~1-5 minutes)
    "21",
    "33",  # Slow tests (~8+ minutes)
]


def _build_systematic_test_options():
    """Compute the safe/unsafe option lists in optimized execution order.

    Returns:
        tuple: ``(safe_options, unsafe_list, all_options)``
    """
    all_options = sorted(
        menu_actions.keys(), key=lambda x: float(x.replace("a", ".1"))
    )  # Sort option keys numerically for consistent ordering.
    safe_options, unsafe_list = _systematic_test_build_safe_list(
        all_options, _SYSTEMATIC_TEST_OPTIMIZED_ORDER
    )  # Classify all options and order safe ones optimally.
    return safe_options, unsafe_list, all_options


def _print_systematic_pre_run_counts(all_options, safe_options, unsafe_list):
    """Print the total / safe / unsafe option counts before the test loop runs."""
    print(f"! Found {len(all_options)} total menu options")  # Report total option count before filtering.
    print(f"! {len(safe_options)} safe options will be tested")  # Confirm how many options will run.
    print(f"!  {len(unsafe_list)} unsafe options will be skipped")  # Confirm how many options will be skipped.
    print()  # Blank line before skip listing.


def _initialize_systematic_telemetry(unsafe_list):
    """Open the timestamped telemetry emitter and emit skip events. Return (emitter, path, skip_count)."""
    telemetry_path = TelemetryEmitter.timestamped_path(
        "data"
    )  # Compute timestamped telemetry file path before starting events.
    emitter = TelemetryEmitter(telemetry_path)  # Open emitter so all events land in one timestamped file.
    skip_count = _systematic_test_emit_skips(
        emitter, unsafe_list
    )  # Print skip list and emit skip events; returns actual skip count.
    return emitter, telemetry_path, skip_count


def _resolve_systematic_test_context():
    """Resolve module-level org_id and the fast-mode flag once before the test loop."""
    global org_id  # Access module-level org_id so tests inherit the resolved org context.
    if not org_id:  # Resolve org_id once before the test loop so every option shares the same org.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Prompt or use cached org identifier.
    return _systematic_test_resolve_fast_mode()  # Resolve fast-mode flag once for the loop.


def _execute_systematic_test_loop(emitter, safe_options, fast_enabled):
    """Iterate safe options through the runner, counting successes/failures."""
    print(" Testing safe operations:")  # Announce test execution phase.
    success_count = 0  # Track how many options completed without raising.
    error_count = 0  # Track how many options raised an exception.
    for i, option in enumerate(safe_options, 1):  # Iterate options in optimized order, 1-indexed for display.
        func, description = menu_actions[option]  # Unpack callable and display name for this option.
        success, _duration = _systematic_test_run_option(
            emitter, SystematicTestOption(option, func, description), i, len(safe_options), fast_enabled
        )  # Execute option with telemetry (issue #470: option identity bundled).
        if success:  # Count success and failure separately for the final summary.
            success_count += 1  # Increment on successful option execution.
        else:  # Non-success means the option raised or returned an error.
            error_count += 1  # Increment on failed option execution.
        if not fast_enabled:  # API-respectful delay between test runs in normal mode.
            time.sleep(1)  # One-second pause so the API isn't hammered by rapid-fire requests.
    return success_count, error_count


def _finalize_systematic_telemetry(emitter, summary):
    """Emit the final summary event, close the telemetry file, and enforce retention."""
    emitter.emit_test_summary(summary)  # Emit aggregate telemetry summary.
    emitter.close()  # Flush and close telemetry file before printing summary.
    emitter.enforce_retention()  # Clean up old telemetry files per configured retention policy.


def _print_systematic_summary(summary, telemetry_path):
    """Print the human-readable summary block (totals, coverage %, paths)."""
    print()  # Blank line before summary.
    print("=" * 80)  # Visual separator for summary section.
    print(" Systematic Test Summary:")  # Label the results block.
    print(f"   Successful operations: {summary.passed}")  # Show successful count.
    print(f"   Failed operations: {summary.failed}")  # Show failure count.
    print(f"   Skipped unsafe operations: {summary.skipped}")  # Show skip count.
    coverage_pct = summary.passed / summary.total * 100 if summary.total else 0.0  # Coverage as a percent.
    print(f"   Total coverage: {summary.passed}/{summary.total} ({coverage_pct:.1f}%)")  # Show coverage percentage.
    print(f"    Total execution time: {summary.elapsed:.2f} seconds")  # Show total elapsed time.
    print(f"   Telemetry written to: {telemetry_path}")  # Tell operator where telemetry landed.
    print("   Detailed logs in: script.log")  # Remind operator of the log file location.


def _report_systematic_outcome(success_count, error_count, safe_count, total_time):
    """Emit the final all-pass / partial-failure message and return the boolean result."""
    if error_count == 0:  # All-pass outcome deserves an explicit success message.
        print("   All tested operations completed successfully!")  # Confirm all-green result to the operator.
        logging.info(
            "SYSTEMATIC_TEST: All %s tested operations completed successfully in %.2fs",
            success_count,
            total_time,
        )  # Record all-pass event for monitoring.
        return True  # Signal all-pass to callers (e.g., for exit-code logic).
    print(f"    {error_count} operations failed - check logs for details")  # Prompt operator to review logs.
    logging.warning(
        "SYSTEMATIC_TEST: %s operations failed out of %s tested", error_count, safe_count
    )  # Log failure count for alerting systems.
    return False  # Signal partial failure to callers.


def _build_interactive_test_runner(get_org_id: Any, set_org_id: Any) -> Any:
    """Construct InteractiveTestRunner with the current runtime context and return it."""
    logging.info("Constructing InteractiveTestRunner dependencies")  # Log before instance creation
    runner = InteractiveTestRunner(  # Build runner with runtime deps
        menu_actions=menu_actions,
        operation_registry=OperationRegistry,
        telemetry_emitter_cls=TelemetryEmitter,
        config_utils=ConfigUtils,
        mistapi_module=mistapi,
        apisession=apisession,
        org_id_getter=get_org_id,
        org_id_setter=set_org_id,
    )
    logging.debug("InteractiveTestRunner initialized successfully")  # Confirm construction
    return runner


def _run_web_portal_server(app: Any, host: str, port: int, dev_debug: bool) -> None:
    """Start the Flask app in container mode (Gunicorn-aware) or local Flask dev server mode."""
    in_container = EnvironmentUtils.is_running_in_container()  # Detect container runtime to switch banner + debug flag
    if in_container:
        logging.info("WEB_PORTAL: Container detected - use wsgi.py with Gunicorn")  # Log container path
        print(f">> Running Flask dev server on {host}:{port}")  # Notify user
        print(">> For production, use: gunicorn wsgi:app")  # Hint at prod runner
        app.run(host=host, port=port, debug=False)  # Force debug=False inside container
    else:
        logging.info("WEB_PORTAL: Local mode - Flask dev server on %s:%s", host, port)  # Log local dev path
        print(f">> Web portal starting at http://127.0.0.1:{port}")  # Notify user
        app.run(host=host, port=port, debug=dev_debug)  # Honor caller's debug flag locally


def _launch_web_portal(args: argparse.Namespace) -> None:
    """Launch the Flask web portal.

    Determines whether to use Gunicorn (container)
    or Flask dev server (local Windows) and starts
    the portal with the current apisession, org_id,
    and menu_actions.
    """
    from web_portal.app import WebPortalApp
    from web_portal.services.config import PortalConfigLoader

    loader = PortalConfigLoader()  # Read web_port + other portal settings from env/.env
    config = loader.load_config()
    port = config["web_port"]
    host = "0.0.0.0"  # nosec B104  # Bind all interfaces so container port maps work

    app = WebPortalApp.create_app(  # Construct Flask app with shared API session + menu registry
        apisession=apisession,
        menu_actions=menu_actions,
        org_id=org_id,
    )

    _run_web_portal_server(app, host, port, args.debug)  # Dispatch to container/local runner


def _report_tqdm_status() -> None:
    """Log whether the real tqdm landed in the global namespace after deferred imports."""
    logging.debug("_report_tqdm_status: checking tqdm namespace availability")  # Trace tqdm status check
    if "tqdm" in global_assignments:  # tqdm injection succeeded -- confirm availability for progress bars
        logging.info(
            "tqdm is available in global namespace: %s", type(globals().get("tqdm"))
        )  # Log tqdm availability  # noqa: E501
    else:  # tqdm missing from resolved assignments -- progress bars will be non-functional
        logging.warning(
            "tqdm was not found in global assignments - progress bars will not be functional"
        )  # Warn if missing  # noqa: E501


def _apply_deferred_assignments() -> None:
    """Inject deferred import symbols into the namespace and report tqdm availability."""
    logging.debug("_apply_deferred_assignments: publishing deferred symbols")  # Trace publish
    if not global_assignments:  # No symbols resolved -- nothing to publish to namespace
        return  # Skip injection entirely when the import cycle produced no assignments
    for var_name, var_value in global_assignments.items():  # Publish each resolved symbol
        globals()[var_name] = var_value  # Inject the imported symbol into module scope for global reuse
        if var_name == "tqdm" and var_value is not None:  # Real tqdm replacing the stub warrants an explicit note
            logging.info(
                "Successfully imported real tqdm in deferred mode: %s", type(var_value)
            )  # Log tqdm override  # noqa: E501
    logging.debug("Applied %d global variable assignments", len(global_assignments))  # Log assignment count
    _report_tqdm_status()  # Log whether tqdm is available in the global namespace


def _run_deferred_import_cycle() -> None:
    """Run the deferred import cycle, publish symbols, and warn on partial failure."""
    global success, global_assignments  # Update module-level import tracking state for downstream readers
    logging.info("Initializing deferred imports at application start...")  # Log before import process
    success, global_assignments = import_manager.initialize_all_imports()  # Run full deferred import cycle
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_deferred_assignments()  # Inject resolved symbols and report tqdm availability
    if not success:  # Non-fatal warning: caller decides whether to abort on partial import failure
        logging.warning("Some required imports failed - functionality may be limited")  # Warn limited functionality


def _initialize_deferred_imports() -> None:
    """Initialize deferred module imports if not already completed at startup."""
    logging.debug("_initialize_deferred_imports: checking deferred import status")  # Log entry
    already_done = hasattr(import_manager, "_deferred_init_done")  # Detect whether deferred init already ran
    if not success and not global_assignments and not already_done:  # First-time deferred init required
        _run_deferred_import_cycle()  # Run the import cycle and publish resolved symbols
    elif already_done:  # Already initialized -- skip to avoid duplicate work
        logging.debug("Deferred imports already initialized, skipping duplicate initialization")  # Note the skip
    logging.debug("_initialize_deferred_imports: complete")  # Log exit


def _add_target_selection_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the org/menu/site/device/port target-selection flags on the parser."""
    logging.debug("_add_target_selection_arguments: registering target-selection flags")  # Log before adding
    parser.add_argument("-O", "--org", help="Organization ID")  # Short -O flag maps to --org for quick use
    parser.add_argument("-M", "--menu", help="Menu option number to execute")  # Short -M for non-interactive dispatch
    parser.add_argument("-S", "--site", help="Human-readable site name")  # Site name that gets resolved to site_id
    parser.add_argument("-D", "--device", help="Human-readable device name")  # Device name resolved to device_id
    parser.add_argument("-P", "--port", help="Port ID")  # Port identifier passed directly to menu functions


def _add_execution_mode_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the debug/delay/fast/skip-deps execution-mode flags on the parser."""
    logging.debug("_add_execution_mode_arguments: registering execution-mode flags")  # Log before adding
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output (includes detailed table data in logs)"
    )  # Debug mode flag  # noqa: E501
    parser.add_argument(
        "--delay", type=int, help="Fixed delay between loop iterations (in seconds). If omitted, delay is dynamic."
    )  # Rate limit override  # noqa: E501
    parser.add_argument(
        "--fast", action="store_true", help="Enable fast mode with multithreading (bypasses rate limiting)"
    )  # Concurrency mode  # noqa: E501
    parser.add_argument(
        "--skip-deps", action="store_true", help="Skip dependency check on startup for faster script initialization"
    )  # Skip dep check  # noqa: E501


def _add_output_format_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the output-format and systematic-test flags on the parser."""
    logging.debug("_add_output_format_arguments: registering output-format and test flags")  # Log before adding
    parser.add_argument(
        "--output-format",
        choices=["csv", "sqlite"],
        default="csv",
        help="Output format: 'csv' for CSV files (default) or 'sqlite' for hybrid database with natural primary keys",  # Output backend selector  # noqa: E501
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run systematic test of all safe menu options (GET operations only, no interactive/websocket/POST operations)",  # noqa: E501
    )
    parser.add_argument(
        "--testinteractive",
        action="store_true",
        help="Run systematic test of read-only menu options requiring interactive site/device/client selection (excludes destructive operations)",  # noqa: E501
    )


def _add_safety_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the dry-run/address-check/SSL/no-env safety flags on the parser."""
    logging.debug("_add_safety_arguments: registering safety and validation flags")  # Log before adding
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry-run mode for destructive operations (show what would be changed without making actual changes)",  # noqa: E501
    )
    parser.add_argument(
        "--address-check",
        action="store_true",
        help="Enable external address validation using Nominatim API for address comparison operations",  # Nominatim toggle  # noqa: E501
    )
    parser.add_argument(
        "--skip-ssl-verify",
        action="store_true",
        help="Skip SSL certificate verification for external API calls (use with caution - for corporate networks only)",  # noqa: E501
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="Disable .env file loading for SSH operations (require explicit command line parameters)",  # SSH env override  # noqa: E501
    )


def _add_interface_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the TUI/login/web-portal/standalone interface flags on the parser."""
    logging.debug("_add_interface_arguments: registering interface and auth flags")  # Log before adding
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch MistHelper in Terminal User Interface (TUI) mode for visual navigation of Mist API library",  # Rich TUI mode  # noqa: E501
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Use interactive login (email/password) instead of API token - enables MSP-level API access",  # Interactive auth  # noqa: E501
    )
    parser.add_argument(
        "--web-portal",
        action="store_true",
        help="Launch the web portal interface on port 8055 (or WEB_PORT env var) instead of the CLI menu",  # Gunicorn web portal  # noqa: E501
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Force standalone/CSV-only mode, disabling ArangoDB and Redis connections",  # Force CSV-only mode
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser for MistHelper with all supported flags."""
    logging.debug("_build_argument_parser: building argument parser")  # Log before parser creation
    parser = argparse.ArgumentParser(description="MistHelper CLI Interface")  # Create base parser with description
    _add_target_selection_arguments(parser)  # Register org/menu/site/device/port selection flags
    _add_execution_mode_arguments(parser)  # Register debug/delay/fast/skip-deps execution-mode flags
    _add_output_format_arguments(parser)  # Register output-format and systematic-test flags
    _add_safety_arguments(parser)  # Register dry-run/address-check/SSL/no-env safety flags
    _add_interface_arguments(parser)  # Register TUI/login/web-portal/standalone interface flags
    logging.debug("_build_argument_parser: parser ready with all arguments configured")  # Log completion
    return parser  # Return parser for caller to call parse_args() on


_FAST_MODE_CAPABLE_FUNCTIONS: tuple[str, ...] = (
    "export_gateway_synthetic_tests_to_csv",
    "get_gateway_devices_with_sites",
    "export_gateway_device_stats_to_csv_with_freshness_check",
    "export_gateway_device_stats_to_csv",
    "GatewayTestExporter.test_results_by_site",
    "OrgInventoryExporter.devices_with_site_info",
    "export_gateway_device_configs_to_csv",
    "APIFetchUtils.gateway_device_configs",
    "InventoryCSVComparator",
    "export_gateways_with_wan_overrides_to_csv",
    "OrgDeviceStatsExporter.device_stats",
    "OrgDeviceStatsExporter.device_port_stats",
    "OrgDeviceStatsExporter.vpn_peer_stats",
    "OrgDeviceStatsExporter.switch_vc_stats",
)


def _announce_fast_mode_scope() -> None:
    """Log and print the list of fast-capable functions so operators know which paths get accelerated."""
    logging.info(
        "FAST MODE ACTIVE: Enabling caching/concurrency shortcuts for: %s",
        ", ".join(_FAST_MODE_CAPABLE_FUNCTIONS),
    )  # Log fast scope for log-correlation
    print("* Fast mode active (caching/concurrency). Functions optimized:")  # Inform operator at console
    for name in _FAST_MODE_CAPABLE_FUNCTIONS:  # Iterate the module-level constant
        print(f"  - {name}")  # Print each fast-capable function name for operator awareness


def _setup_runtime_flags(args: argparse.Namespace) -> None:
    """Apply standalone env flag, register args globally, and configure FAST_MODE_ENABLED."""
    logging.debug("_setup_runtime_flags: applying standalone and fast mode flags")  # Log entry
    if args.standalone:  # --standalone flag disables ArangoDB/Redis connections org-wide
        os.environ["MISTHELPER_STANDALONE"] = "true"  # Write env var so all components detect standalone mode
        logging.info("Standalone mode enabled via --standalone flag: ArangoDB/Redis disabled")  # Log env write
    globals()["args"] = args  # Register parsed args globally so menu functions can read CLI flags
    logging.debug("CLI args registered in globals()['args'] for menu function access")  # Log global assignment
    global FAST_MODE_ENABLED  # Declare intent to modify module-level flag used by test harness
    try:
        FAST_MODE_ENABLED = bool(args.fast)  # Derive flag from --fast CLI argument (bool is safe cast)
    except Exception:
        FAST_MODE_ENABLED = False  # Fail-safe: ensure symbol exists even if args access fails
    logging.debug("FAST_MODE_ENABLED set to %s", FAST_MODE_ENABLED)  # Log fast mode state
    if args.fast:  # Announce scope only when fast mode actually engaged
        _announce_fast_mode_scope()  # Log + print fast-capable function list
    logging.debug("_setup_runtime_flags: complete")  # Log exit


def _apply_dependency_assignments(skip_mode: bool) -> None:
    """Inject resolved global symbol assignments into the module namespace."""
    logging.debug("_apply_dependency_assignments: publishing symbols (skip_mode=%s)", skip_mode)  # Trace publish
    if not global_assignments:  # No symbols resolved -- nothing to publish to namespace
        return  # Skip injection entirely when the import cycle produced no assignments
    for var_name, var_value in global_assignments.items():  # Publish each resolved symbol
        globals()[var_name] = var_value  # Inject the imported symbol into module scope for global reuse
    if skip_mode:  # Differentiate the log message so operators see the skip-deps code path was taken
        logging.debug(
            "Applied %d global variable assignments in skip mode", len(global_assignments)
        )  # Log skip-mode count  # noqa: E501
    else:  # Full dependency path -- preserve the original (non-skip) log message wording
        logging.debug("Applied %d global variable assignments", len(global_assignments))  # Log assignment count


def _run_full_dependency_init(args: argparse.Namespace) -> None:
    """Run the full dependency import cycle and abort on critical, non-test failure."""
    global success, global_assignments  # Update module-level import tracking state for downstream readers
    logging.info("Initializing deferred dependencies with full checking...")  # Log before full init
    success, global_assignments = import_manager.initialize_all_imports(skip_deps=False)  # Run full import cycle
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_dependency_assignments(skip_mode=False)  # Publish resolved symbols into module namespace
    if not success and not args.test:  # Abort on critical failure unless running in test mode
        logging.error("Critical dependencies missing. Exiting.")  # Log fatal dependency failure before exit
        print(
            "!! Critical dependencies missing. Use --skip-deps to bypass or install missing packages."
        )  # Inform user  # noqa: E501
        sys.exit(1)  # Exit with error code -- cannot continue without required modules


def _run_skip_dependency_init() -> None:
    """Run the minimal dependency import cycle used by the --skip-deps path."""
    global success, global_assignments  # Update module-level import tracking state for downstream readers
    logging.info("Dependency initialization skipped due to --skip-deps flag")  # Log skip reason
    success, global_assignments = import_manager.initialize_all_imports(skip_deps=True)  # Minimal import cycle
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_dependency_assignments(skip_mode=True)  # Publish whatever symbols resolved even in skip mode


def _initialize_dependencies(args: argparse.Namespace) -> None:
    """Initialize deferred module imports based on --skip-deps flag, aborting on critical failure."""
    logging.debug("_initialize_dependencies: checking if dependency initialization is needed")  # Log entry
    already_done = hasattr(import_manager, "_deferred_init_done")  # Detect whether deferred init already ran
    if not _initialize_imports_now and not already_done:  # First-time deferred init required
        if args.skip_deps:  # Minimal path when the caller passed --skip-deps
            _run_skip_dependency_init()  # Run the minimal import cycle for core functionality only
        else:  # Default path performs full dependency checking
            _run_full_dependency_init(args)  # Run the full import cycle (may sys.exit on critical failure)
    elif already_done:  # Already initialized -- skip to avoid duplicate work
        logging.debug("Dependencies already initialized, skipping duplicate initialization")  # Note the skip
    logging.debug("_initialize_dependencies: complete")  # Log exit


def _establish_mist_session(args: argparse.Namespace) -> None:
    """Initialize Mist API session using interactive login or API token, then detect MSP privileges."""
    global msp_privileges  # We publish detected MSP grants to the module global for later menus/exporters to reuse
    logging.debug("_establish_mist_session: starting session initialization")  # Log entry
    if args.login:  # Interactive login requested via --login flag
        logging.info("Interactive login mode requested via --login flag")  # Log before interactive login
        if not MistSessionInteractiveInitializer.initialize():  # Attempt email/password login
            logging.error("Failed to initialize Mist API session via interactive login")  # Log auth failure
            print(" Failed to initialize Mist API session. Check your credentials.")  # Inform user
            sys.exit(1)  # Exit -- cannot proceed without authenticated session
        ConfigUtils.set_apisession(apisession)  # Publish authenticated session to ConfigUtils cache (1015 T-12)
    else:  # Default path: use API token from .env or environment variables
        if not MistSessionInitializer.initialize():  # Attempt token-based session init
            logging.error("Failed to initialize Mist API session")  # Log token auth failure
            print(" Failed to initialize Mist API session. Check your credentials.")  # Inform user
            sys.exit(1)  # Exit -- cannot proceed without authenticated session
        ConfigUtils.set_apisession(apisession)  # Publish authenticated session to ConfigUtils cache (1015 T-12)
        msp_privileges = detect_msp_privileges(apisession)  # Detect MSP grants for token session and publish to global
    logging.debug("_establish_mist_session: session established successfully")  # Log successful auth


def _apply_debug_log_level() -> None:
    """Set DEBUG on root + file handlers and keep console at INFO so DEBUG noise stays out of the terminal."""
    logging.getLogger().setLevel(logging.DEBUG)  # Enable DEBUG on root logger
    for handler in logging.getLogger().handlers:  # Iterate each registered handler
        if isinstance(handler, logging.FileHandler):  # File handlers get full DEBUG output
            handler.setLevel(logging.DEBUG)
        elif isinstance(handler, logging.StreamHandler):  # Console stays at INFO to avoid noise
            handler.setLevel(logging.INFO)
    logging.debug("Debug logging enabled via --debug flag")  # Confirm debug mode active in log file
    logging.debug("Command line arguments: %s", " ".join(sys.argv))  # Log full command line for diagnostics
    logging.debug("Performance monitoring will trigger circuit breakers for infinite loops")  # Remind about CBs


def _configure_runtime_options(args: argparse.Namespace) -> None:
    """Set OUTPUT_FORMAT, initialize PROGRESS_EMITTER, and configure debug log level."""
    global OUTPUT_FORMAT, PROGRESS_EMITTER  # Declare intent to modify module-level runtime config
    logging.debug("_configure_runtime_options: applying runtime configuration")  # Log entry
    OUTPUT_FORMAT = args.output_format  # Apply --output-format (csv or sqlite) to global used by all exporters
    timestamp = datetime.now(UTC).isoformat()  # Capture current UTC time for audit trail
    logging.info("Output format set to: %s at %s", OUTPUT_FORMAT, timestamp)  # Log format selection with timestamp
    try:
        PROGRESS_EMITTER = TelemetryEmitter(
            os.path.join("data", "test_events.jsonl")
        )  # Initialize JSONL telemetry emitter
        logging.info("Progress telemetry emitter initialized: data/test_events.jsonl")  # Log emitter ready
    except Exception as emitter_exc:
        logging.warning(
            "Progress telemetry emitter init failed (non-blocking): %s", emitter_exc
        )  # Log non-fatal failure
        PROGRESS_EMITTER = None  # Set to None so callers skip telemetry gracefully
    if args.debug:  # Apply debug logging level to file handlers; keep console at INFO to avoid noise
        _apply_debug_log_level()  # Promote root + file handlers to DEBUG
    logging.debug("_configure_runtime_options: complete")  # Log exit


def _run_tui_mode(args: argparse.Namespace) -> None:
    """Launch MistHelper Terminal User Interface (TUI) mode using the Rich library."""
    logging.info("TUI_MODE: Starting Terminal User Interface mode")  # Log before TUI launch
    print(">> Terminal User Interface mode activated")  # Inform user TUI is starting
    _ensure_tui_api_session()  # Initialize the Mist API session if not already established.
    _silence_console_handlers_for_tui()  # Remove console log handlers so Rich owns the screen.
    _run_tui_event_loop(args)  # Run the TUI event loop (handles Ctrl+C + fatal errors internally).
    if args.debug:  # Debug: log a final timestamped marker after the loop exits cleanly.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format ms timestamp.
        logging.debug(
            "TUI_DEBUG: [%s] TUI mode completed successfully - about to exit", timestamp
        )  # Log clean completion.
    logging.info("TUI_MODE: TUI mode completed successfully")  # Log clean exit.


def _ensure_tui_api_session() -> None:
    """Initialize the Mist API session if not already established. Exits 1 on auth failure."""
    if apisession:  # Already authenticated -- nothing to do.
        return  # Reuse the existing session.
    print(">> Initializing Mist API session...")  # Inform user session is being set up.
    if not MistSessionInitializer.initialize():  # Attempt session init for TUI
        print("[ERROR] Failed to initialize Mist API session")  # Inform user of auth failure.
        logging.error("TUI_MODE: Could not initialize API session")  # Log auth failure.
        sys.exit(1)  # Exit -- TUI cannot function without a session.
    print(">> API session initialized successfully")  # Confirm session ready.


def _silence_console_handlers_for_tui() -> None:
    """Remove non-file console handlers from the root logger so they don't disrupt the Rich UI."""
    root_logger = logging.getLogger()  # Access root logger to modify handlers.
    console_handlers = [  # Identify console handlers to suppress during TUI.
        h
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    for handler in console_handlers:  # Iterate handlers to remove each.
        root_logger.removeHandler(handler)  # Remove console handler so logs don't disrupt Rich display.
        logging.debug("TUI_MODE: Removed console handler to prevent interference with Rich TUI")  # Log removal.


def _handle_tui_keyboard_interrupt(debug: bool) -> None:
    """Log clean exit when user pressed Ctrl+C inside the TUI and inform them at the console."""
    if debug:  # Debug: log timestamped interrupt event
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format timestamp
        logging.debug(
            "TUI_DEBUG: [%s] KeyboardInterrupt caught - user pressed Ctrl+C", timestamp
        )  # Log interrupt with time
    logging.info("TUI_MODE: User interrupted with Ctrl+C")  # Log clean user exit
    print("\n[EXIT] TUI mode stopped by user")  # Inform user TUI was stopped


def _handle_tui_exception(debug: bool, error: Exception) -> None:
    """Log fatal error from the TUI event loop and exit with code 1."""
    if debug:  # Debug: log timestamped exception detail
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format timestamp
        logging.debug(
            "TUI_DEBUG: [%s] Exception caught in TUI mode: %s: %s",
            timestamp,
            type(error).__name__,
            error,
        )  # Log error
    logging.exception("TUI_MODE: Fatal error - %s", error)  # Log full traceback to file
    print(f"\n[ERROR] TUI mode crashed: {error}")  # Inform user of crash
    sys.exit(1)  # Exit with error code after TUI crash


def _run_tui_event_loop(args: argparse.Namespace) -> None:
    """Instantiate and run the TUI event loop. Handles Ctrl+C cleanly and Exceptions with traceback."""
    try:
        from src.ui.tui import MistHelperTUI  # PLC0415: lazy import avoids loading Rich at startup

        tui = MistHelperTUI(debug_mode=args.debug)  # Create TUI with debug flag
        tui.apisession = apisession  # Pass global API session so TUI can execute live API calls
        if args.debug:  # Debug: record that TUI was launched with debug enabled
            logging.debug("TUI_MODE: Debug mode is ACTIVE - enhanced logging enabled")  # Log debug state
        tui.run()  # Launch TUI event loop (blocks until user exits)
    except KeyboardInterrupt:  # User pressed Ctrl+C inside the TUI
        _handle_tui_keyboard_interrupt(args.debug)  # Log and inform user of clean exit
    except Exception as error:  # Unexpected error inside the TUI event loop
        _handle_tui_exception(args.debug, error)  # Log + print + exit(1)


def _run_cli_mode(args: argparse.Namespace) -> None:
    """Resolve org/site/device IDs from CLI args, dispatch to the target menu function, and exit."""
    global org_id  # Modify module-level org_id used by all menu functions.
    logging.info("CLI arguments detected, running in non-interactive mode.")  # Log before CLI dispatch.
    _log_cli_invocation(args)  # Verbose log of every parsed CLI flag for diagnostics.
    org_id = _resolve_cli_org_id(args)  # Use --org if given, otherwise prompt/cache.
    site_id = _resolve_cli_site_id(args, org_id)  # Resolve --site name -> site_id (or None).
    device_id = _resolve_cli_device_id(args, site_id)  # Resolve --device name -> device_id (or None).
    _dispatch_cli_menu_action(args, site_id, device_id)  # Dispatch + exit. Never returns on success.


def _log_cli_invocation(args: argparse.Namespace) -> None:
    """Log every parsed CLI argument at DEBUG level for diagnostics."""
    logging.debug(
        "Parsed CLI arguments: org=%s, menu=%s, site=%s, device=%s, port=%s, debug=%s, delay=%s, fast=%s, skip_deps=%s, output_format=%s, test=%s, address_check=%s, tui=%s",  # noqa: E501
        args.org,
        args.menu,
        args.site,
        args.device,
        args.port,
        args.debug,
        args.delay,
        args.fast,
        args.skip_deps,
        args.output_format,
        args.test,
        args.address_check,
        args.tui,
    )


def _resolve_cli_org_id(args: argparse.Namespace) -> str:
    """Return --org if given, otherwise resolve from cache / interactive prompt."""
    if args.org:  # CLI explicitly provided the org ID.
        logging.info("Using org_id from CLI argument: %s", args.org)  # Log CLI org ID.
        return str(args.org)  # Return the CLI org ID (argparse gives Any; narrow to str).
    return ConfigUtils.get_cached_or_prompted_org_id()  # Fall back to cache or prompt.


def _build_site_name_to_id_map(sites: list[dict[str, Any]]) -> dict[str, str]:
    """Build a {name: id} lookup map from a list of site dicts, skipping entries missing either field."""
    return {
        str(site["name"]): str(site["id"]) for site in sites if site.get("name") and site.get("id")
    }  # Build name->id map; drop sites missing name or id


def _resolve_cli_site_id(args: argparse.Namespace, org_id: str) -> str | None:
    """Resolve --site name to a site_id via API lookup. Exit 1 if name not found. Return None if no --site."""
    if not args.site:  # No --site supplied; nothing to resolve.
        return None  # Caller treats None as "no site filter".
    logging.info(
        "Resolving site name '%s' to site_id using unified pagination limit %d...",
        args.site,
        DEFAULT_API_PAGE_LIMIT,
    )  # Log before site resolution.
    sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all org sites from Mist API.
    site_lookup = _build_site_name_to_id_map(sites)  # Delegate name->id map construction
    site_id = site_lookup.get(args.site)  # Look up site ID by human-readable name.
    if not site_id:  # Site name not found in org -- abort with error.
        logging.error("! Site name '%s' not found.", args.site)  # Log resolution failure.
        print(f"! Site name '{args.site}' not found.")  # Inform user of bad site name.
        sys.exit(1)  # Exit -- cannot proceed with unknown site.
    logging.info("Resolved site name '%s' to site_id '%s'.", args.site, site_id)  # Log resolution success.
    return site_id  # Return the resolved site_id.


def _resolve_cli_device_id(args: argparse.Namespace, site_id: str | None) -> str | None:
    """Resolve --device name to a device_id via site-scoped API lookup. Requires site context."""
    if not (args.device and site_id):  # Either no --device or no site context; nothing to resolve.
        return None  # Caller treats None as "no device filter".
    logging.info("Resolving device name '%s' at site_id '%s'...", args.device, site_id)  # Log before device resolution.
    response = mistapi.api.v1.sites.devices.listSiteDevices(
        apisession, site_id, type="all"
    )  # Fetch all devices at site.
    devices = mistapi.get_all(response=response, mist_session=apisession)  # Page through all results.
    device_lookup = {dev["name"]: dev["id"] for dev in devices}  # Build name->id map from device list.
    device_id = device_lookup.get(args.device)  # Look up device ID by human-readable name.
    if not device_id:  # Device name not found at site -- abort with error.
        logging.error("! Device name '%s' not found at site '%s'.", args.device, args.site)  # Log resolution failure.
        print(f"! Device name '{args.device}' not found at site '{args.site}'.")  # Inform user.
        sys.exit(1)  # Exit -- cannot proceed with unknown device.
    logging.info("Resolved device name '%s' to device_id '%s'.", args.device, device_id)  # Log resolution success.
    return str(device_id)  # Return the resolved device_id (dev["id"] is Any; narrow to str).


def _dispatch_cli_menu_action(args: argparse.Namespace, site_id: str | None, device_id: str | None) -> None:
    """Look up args.menu in menu_actions, build kwargs, call the target. Exits 0/1 -- never returns on success."""
    if args.menu not in menu_actions:  # Invalid menu number -- abort with error.
        logging.error("! Invalid menu option: %s", args.menu)  # Log invalid menu selection.
        print(f"! Invalid menu option: {args.menu}")  # Inform user of bad menu number.
        sys.exit(1)  # Exit with error code on invalid menu option.
    func, _ = menu_actions[args.menu]  # Extract callable from menu_actions dispatch table.
    logging.info("Executing menu action '%s'.", args.menu)  # Log before function dispatch.
    func_args = _build_cli_func_kwargs(args, site_id, device_id)  # Build the full candidate kwargs dict.
    sig = inspect.signature(func)  # Introspect signature to keep only valid kwargs.
    accepted_args = {
        k: v for k, v in func_args.items() if k in sig.parameters and v is not None
    }  # Filter to accepted params.
    func(**accepted_args)  # Call menu function with filtered args.
    logging.info("CLI execution complete. Exiting.")  # Log successful CLI completion.
    logging.debug("EXIT: _run_cli_mode - CLI success")  # Log exit point.
    sys.exit(0)  # Clean exit after successful CLI execution.


def _build_cli_func_kwargs(args: argparse.Namespace, site_id: str | None, device_id: str | None) -> dict:
    """Build the candidate kwargs dict used to call a menu function in CLI mode."""
    return {
        "site_id": site_id,  # Pass resolved site ID (or None if not provided).
        "device_id": device_id,  # Pass resolved device ID (or None if not provided).
        "port": args.port,  # Pass port ID directly from CLI.
        "org_id": org_id,  # Pass resolved organization ID.
        "debug": args.debug,  # Pass debug mode flag to enable verbose logging.
        "delay": args.delay,  # Pass custom delay override (or None for dynamic).
        "fast": args.fast,  # Pass fast mode flag to enable concurrency.
        "dry_run": args.dry_run,  # Pass dry-run flag to skip destructive actions.
        "address_check": args.address_check,  # Pass address validation toggle.
        "skip_ssl_verify": args.skip_ssl_verify,  # Pass SSL verification bypass flag.
    }


def _run_interactive_mode(args: argparse.Namespace) -> None:
    """Present the interactive menu loop, dispatching to functions until user exits."""
    global org_id  # Modify module-level org_id for all menu functions.
    logging.info("No CLI arguments detected, running in interactive menu mode.")  # Log before interactive start.
    org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org ID from cache or prompt.
    logging.info("Organization ID initialized for interactive mode: %s", org_id)  # Log org ID.
    container_mode = _setup_interactive_container_mode()  # Detect container runtime and print banner if active.
    while True:  # Main menu loop -- runs until user selects exit or input stream closes.
        _print_interactive_menu()  # Print the sorted menu options.
        iwant = _prompt_interactive_selection()  # Get the user's selection (stripped, with __EXIT__ on EOF).
        if iwant == "__EXIT__":  # EOF sentinel signals Ctrl+D / SSH disconnect / broken pipe.
            _handle_interactive_eof(container_mode)  # Print EOF messages and exit the loop.
            break  # Exit the while loop cleanly.
        if iwant == "":  # Empty input: redisplay menu without logging an error.
            _handle_interactive_empty_input(container_mode)  # Print empty-input notice.
            continue  # Loop back to show menu again.
        selected = menu_actions.get(iwant)  # Look up user selection in dispatch table.
        if not selected:  # Invalid (non-empty) selection entered -- redisplay or exit.
            _handle_interactive_invalid_selection(iwant, container_mode)  # Print + maybe exit on invalid input.
            continue  # In container mode, loop again; direct mode already exited inside the handler.
        func, _ = selected  # Extract callable from menu_actions entry.
        logging.info(
            "User selected menu option '%s'. Executing associated function.", iwant
        )  # Log selection before dispatch.
        _execute_interactive_menu_action(iwant, func, container_mode)  # Run the func with full error handling.


def _setup_interactive_container_mode() -> bool:
    """Detect whether MistHelper is running inside a container; print banner if yes."""
    container_mode = EnvironmentUtils.is_running_in_container()  # Check Podman/Docker container marker files.
    if container_mode:  # Container mode: show banner and loop after each operation.
        logging.info("Container mode detected - enabling continuous menu loop")  # Log container detection.
        print(
            "[CONTAINER MODE] MistHelper will return to menu after each operation"
        )  # Inform user of container behavior.
        print("                 Use option 0 to exit the container")  # Show exit instruction.
    return container_mode  # Return flag so the loop can branch on container vs. direct mode.


def _print_interactive_menu() -> None:
    """Print the sorted list of available menu options."""
    print("\nAvailable Options:")  # Print menu header before listing options.
    sorted_menu_keys = sorted(
        menu_actions.keys(), key=lambda x: float(x.replace("a", ".1"))
    )  # Sort numerically (not lexically) so 10 sorts after 9.
    for key in sorted_menu_keys:  # Iterate every menu key in numeric order.
        _, description = menu_actions[key]  # Unpack description from dispatch table tuple.
        print(f"{key}: {description}")  # Print each menu option as key: description.


def _prompt_interactive_selection() -> str:
    """Prompt the user for a menu selection. Returns stripped input, or __EXIT__ on EOF."""
    return InputUtils.safe_input(
        "\nEnter your selection number now: ",
        default_value="__EXIT__",  # EOF returns __EXIT__ sentinel to trigger clean shutdown.
        context="main_menu_selection",  # Context label for EOF logging.
    ).strip()  # Strip whitespace from user input.


def _handle_interactive_eof(container_mode: bool) -> None:
    """Print the EOF (Ctrl+D / SSH disconnect / pipe close) messages."""
    print("\n[EOF] Input stream closed. Exiting gracefully...")  # Inform user of EOF.
    logging.info("EOF encountered on input - user disconnected or input stream closed")  # Log EOF event.
    if container_mode:  # Container mode: additional context message for SSH session termination.
        print("[CONTAINER MODE] SSH session ended. Terminating MistHelper.")  # Container-specific EOF message.


def _handle_interactive_empty_input(container_mode: bool) -> None:
    """Print the empty-input notice (different copy for container vs direct mode)."""
    if container_mode:  # Container mode shows prompt to clarify nothing happened.
        print("[CONTAINER MODE] No selection entered. Redisplaying menu...")  # Container empty input message.
        print("=" * 60)  # Visual separator before menu redisplay.
    else:  # Direct mode shows simpler reminder.
        print("No selection entered. Please enter a menu number.")  # Direct mode empty input message.


def _handle_interactive_invalid_selection(iwant: str, container_mode: bool) -> None:
    """Handle an invalid (non-empty, not in dispatch table) menu selection. May call sys.exit."""
    logging.error("Invalid selection '%s' entered by user.", iwant)  # Log invalid selection.
    print("Invalid selection. Please try again.")  # Inform user of invalid input.
    if not container_mode:  # Direct mode: exit on invalid selection.
        logging.debug("EXIT: _run_interactive_mode - invalid selection (direct mode)")  # Log exit point.
        sys.exit(1)  # Exit with error code on invalid selection in direct mode.
    logging.debug("Container mode: invalid selection '%s', redisplaying menu", iwant)  # Log container invalid.


def _execute_interactive_menu_action(iwant: str, func, container_mode: bool) -> None:
    """Run the selected menu function with full error handling (success, Ctrl+C, exception)."""
    try:
        if iwant == "0":  # Option 0 is the explicit exit shortcut.
            logging.info("Exit option selected by user.")  # Log user-requested exit.
            logging.debug("EXIT: _run_interactive_mode - user requested exit")  # Log exit point.
            sys.exit(0)  # Exit cleanly on user selection of option 0.
        func()  # Execute the selected menu function.
        logging.info("Menu option '%s' execution complete.", iwant)  # Log completion after function returns.
        _dispatch_post_menu_success(iwant, container_mode)  # Branch on container vs direct + session-management ops.
    except KeyboardInterrupt:  # User pressed Ctrl+C during operation.
        _handle_post_menu_interrupt(iwant, container_mode)  # Container loops; direct exits with SIGINT code.
    except Exception as error:  # Unexpected error during menu function execution.
        _handle_post_menu_exception(iwant, error, container_mode)  # Container loops; direct exits with error code.


def _dispatch_post_menu_success(iwant: str, container_mode: bool) -> None:
    """Dispatch follow-up after a successful menu call (continue loop vs sys.exit)."""
    session_management_options = {"115", "143"}  # Options that re-enter menu to use new context.
    if container_mode:  # Container mode: always return to menu after each operation.
        logging.debug(
            "Container mode: option '%s' completed successfully, returning to menu", iwant
        )  # Log container loop.
        print(f"\n[CONTAINER MODE] Operation '{iwant}' completed. Returning to menu...")  # Inform user.
        print("=" * 60)  # Visual separator before menu redisplay.
        return  # Return so the outer while loop continues.
    if iwant in session_management_options:  # Direct mode + session management: keep loop running.
        logging.info("Session management option '%s' completed - returning to menu", iwant)  # Log session update.
        print("\n[SESSION] Context updated. Returning to menu...")  # Inform user of context change.
        print("=" * 60)  # Visual separator.
        return  # Return so the outer while loop continues with updated session context.
    logging.debug("EXIT: _run_interactive_mode - interactive success (direct mode)")  # Log exit point.
    sys.exit(0)  # Exit after single operation in direct mode.


def _handle_post_menu_interrupt(iwant: str, container_mode: bool) -> None:
    """Handle a Ctrl+C interrupt during a menu function call."""
    logging.info("Operation interrupted by user (Ctrl+C)")  # Log user interrupt.
    if container_mode:  # Container mode: return to menu after interrupt.
        logging.debug("Container mode: option '%s' interrupted, returning to menu", iwant)  # Log container interrupt.
        print("\n[CONTAINER MODE] Operation interrupted. Returning to menu...")  # Inform user.
        print("=" * 60)  # Visual separator.
        return  # Return so the outer while loop continues.
    logging.debug("EXIT: _run_interactive_mode - user interrupt")  # Log exit point.
    sys.exit(130)  # Exit 130 is the standard exit code for SIGINT (Ctrl+C).


def _handle_post_menu_exception(iwant: str, error: Exception, container_mode: bool) -> None:
    """Handle an unexpected exception raised during a menu function call."""
    logging.error("Error executing menu option '%s': %s", iwant, error)  # Log error with context.
    if container_mode:  # Container mode: show error but return to menu.
        logging.debug("Container mode: option '%s' failed with error, returning to menu", iwant)  # Log container error.
        print(f"\n[CONTAINER MODE] Error in operation '{iwant}': {error}")  # Show error to user.
        print("Returning to menu...")  # Inform user we are continuing.
        print("=" * 60)  # Visual separator.
        return  # Return so the outer while loop continues despite the error.
    logging.debug("EXIT: _run_interactive_mode - interactive error (direct mode)")  # Log exit point.
    sys.exit(1)  # Exit with error code on unexpected exception in direct mode.


# NOTE: main entrypoint extracted to
# src/refactors/main_entrypoint.py::MainEntrypoint.run
# per initiative 1011 SC-026 (FR-003: no wrapper shim; FR-005: fn->method).


def _run_systematic_test_mode(_args: argparse.Namespace) -> None:
    """Run all safe menu options once and exit 0 on pass / 1 on fail."""
    logging.info("SYSTEMATIC_TEST: Starting systematic test mode")  # Trace before dispatch
    from src.refactors.run_systematic_test import (
        RunSystematicTestManager,  # noqa: PLC0415 - lazy import keeps module startup path light
    )

    sys.exit(0 if RunSystematicTestManager().run() else 1)  # Delegate to extracted manager


def _run_interactive_test_mode(_args: argparse.Namespace) -> None:
    """Run interactive test mode (read-only menus with site/device selection) and exit."""
    logging.info("INTERACTIVE_TEST: Starting interactive test mode")  # Trace before dispatch
    sys.exit(0 if RunInteractiveTestManager().run() else 1)  # Route to extracted manager (PR-12)


def _run_tui_mode_and_exit(args: argparse.Namespace) -> None:
    """Launch the Rich Terminal UI and exit cleanly when the user closes it."""
    _run_tui_mode(args)  # TUI handles its own event loop and exceptions
    sys.exit(0)


def _run_web_portal_mode(args: argparse.Namespace) -> None:
    """Launch the Gunicorn web portal on port 8055 and exit cleanly on shutdown."""
    logging.info("WEB_PORTAL: Starting web portal mode")  # Trace before launch
    _launch_web_portal(args)  # Blocks until shutdown
    sys.exit(0)


def _dispatch_main_mode(args: argparse.Namespace) -> None:
    """Dispatch to the appropriate mode entry point based on parsed CLI flags."""
    mode_table = (  # Ordered (predicate, handler) pairs — first match wins
        (lambda a: bool(a.test), _run_systematic_test_mode),
        (lambda a: bool(a.testinteractive), _run_interactive_test_mode),
        (lambda a: bool(a.tui), _run_tui_mode_and_exit),
        (lambda a: bool(getattr(a, "web_portal", False)), _run_web_portal_mode),
        (_has_meaningful_cli_args, _run_cli_mode),
    )
    for predicate, handler in mode_table:  # Stop on first predicate that matches
        if predicate(args):
            handler(args)
            return  # Most handlers sys.exit; return is defensive for _run_cli_mode
    _run_interactive_mode(args)  # Fallback: interactive menu loop


_MEANINGFUL_CLI_ATTRS: tuple[str, ...] = (
    "menu",
    "org",
    "site",
    "device",
    "port",
    "test",
)  # CLI flags that flip MistHelper into non-interactive one-shot dispatch mode


def _has_meaningful_cli_args(args: argparse.Namespace) -> bool:
    """Return True if any non-interactive CLI flag was provided (triggers CLI dispatch mode)."""
    return any(getattr(args, name, None) for name in _MEANINGFUL_CLI_ATTRS)  # Any flag => CLI mode


if __name__ == "__main__":
    try:
        # When run as a script the interpreter registers this module as "__main__", so a later
        # importlib.import_module("MistHelper") (used by the src/refactors/serial_cc/* services to
        # resolve runtime deps) would load a SECOND, uninitialized copy whose mistapi/apisession
        # globals are still None -- causing "'NoneType' object has no attribute 'api'" failures.
        # Alias "MistHelper" to this live __main__ instance before main() runs so those late imports
        # resolve to the authenticated module. No-op when imported normally (__name__ == "MistHelper").
        sys.modules["MistHelper"] = sys.modules["__main__"]  # Point both names at the live module
        logging.info("=== MistHelper application starting ===")
        # Single explicit banner for test mode to clarify reduced lookbacks
        try:
            if IS_TEST_MODE:
                logging.info("TEST MODE ACTIVE: Reducing default 24h lookback windows to 1h for eligible exports.")
        except NameError:
            # IS_TEST_MODE may not yet be defined if refactor order changes; ignore safely
            pass

        # Install a global exception hook early so we capture full tracebacks for unexpected issues
        def _global_excepthook(exc_type, exc_value, exc_traceback):
            try:
                import traceback as _tb

                if issubclass(exc_type, KeyboardInterrupt):
                    # Defer to default behavior for Ctrl+C
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                formatted = "".join(_tb.format_exception(exc_type, exc_value, exc_traceback))
                logging.error("UNHANDLED TOP-LEVEL EXCEPTION TRACEBACK FOLLOWS")
                for line in formatted.rstrip().splitlines():
                    logging.error(line)
            except Exception as hook_err:
                logging.error("Exception in global excepthook: %s", hook_err)

        try:
            import sys as _sys_mod

            _sys_mod.excepthook = _global_excepthook
        except Exception as hook_setup_err:
            logging.warning("Failed to install global excepthook: %s", hook_setup_err)
        MainEntrypoint.run()  # Invoke extracted CLI main entrypoint (SC-026)
    except KeyboardInterrupt:
        logging.info("Application interrupted by user (Ctrl+C)")
        logging.debug("EXIT: __main__ - user interrupt")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logging.error("Unhandled exception in main application: %s", e)
        try:
            import traceback

            traceback_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            for line in traceback_details.rstrip().splitlines():
                logging.error(line)
        except Exception as trace_err:
            logging.error("Failed to log exception traceback: %s", trace_err)
        logging.debug("EXIT: __main__ - unhandled exception")
        sys.exit(1)
    finally:
        logging.info("=== MistHelper application ending ===")
# hi
