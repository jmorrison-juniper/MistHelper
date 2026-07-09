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
import csv  # Import csv module for writing CSV export files to data/ directory
import logging  # Import logging for structured logging to script.log and console
import os  # Import os for file path operations, environment variables, and data/ directory setup
import re  # Import re for regex pattern matching in data parsing (SSIDs, descriptions, etc.)
import subprocess  # nosec B404  # Import subprocess for executing external commands (SSH, JSON parsing) with security review
import time  # Import time for rate limiting, delays, and performance monitoring
import traceback  # Import traceback for detailed exception context in error logs
from collections.abc import Callable  # Import Callable type hint for callback functions passed to API methods
from dataclasses import dataclass  # Import dataclass decorator for configuration objects and entity classes
from datetime import datetime  # Import datetime for timestamping logs and events
from typing import TYPE_CHECKING, Any, Literal  # Import type hints for static analysis without runtime overhead

# Type stubs for dynamically imported modules
# These allow type checking while the actual imports happen at runtime via GlobalImportManager
# Pylance uses these unconditionally; runtime try/except blocks below handle actual loading.
if TYPE_CHECKING:  # These imports only used by static type checkers (Pylance, mypy), not at runtime
    import pyte  # Type stub for pyte (terminal emulator for WebSocket output parsing)
    import requests  # Type stub for requests (HTTP library used by mistapi)
    from prettytable import PrettyTable  # Type stub for prettytable (ASCII table formatting)

    import websocket  # Type stub for websocket (WebSocket client for device diagnostics)

# ============================================================================
# POLYGLOT DATABASE LAYER (OPTIONAL)
# ============================================================================
# Conditional import for ArangoDB + Redis TimeSeries backends.
# Falls back gracefully in standalone mode (no python-arango/redis installed).
try:  # Attempt to import polyglot database layer for ArangoDB/Redis export backends
    from src.db import DatabaseConfig, configure_db_logging  # Import database configuration classes
    from src.db.router import DatabaseRouter  # Import database router for multi-backend write operations

    DB_LAYER_AVAILABLE = True  # Set flag indicating database backends are available for export operations
except ImportError:  # If database dependencies (python-arango, redis) not installed, gracefully disable
    DatabaseConfig = None  # type: ignore[assignment, misc]  # None lets runtime guards detect DB-layer absence
    configure_db_logging = None  # type: ignore[assignment]  # None lets runtime guards detect DB-layer absence
    DatabaseRouter = None  # type: ignore[assignment, misc]  # None lets runtime guards detect DB-layer absence
    DB_LAYER_AVAILABLE = False  # Set flag to disable database output formats (CSV/SQLite only)

from src.analytics.data_collection_manager import (  # pylint: disable=unused-import
    DataCollectionManager,  # noqa: F401  # Cat B (1013 SC-001 position 25) -- re-export for MistHelper.DataCollectionManager callers
)
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
from src.analytics.telemetry_emitter import (  # pylint: disable=unused-import
    TelemetryEmitter,  # noqa: F401  # Cat B (1013 SC-001 position 9) -- re-export for callers at 18629/18632/18711/19062
)
from src.api.api_core_fetch_utils import (
    APICoreFetchUtils,
)  # Cat E canonical (1014 P10) -- re-export for MistHelper.APICoreFetchUtils callers
from src.api.api_data_fetcher import (  # pylint: disable=unused-import
    APIDataFetcher,  # noqa: F401  # Cat B (1013 SC-001 position 21) -- re-export for MistHelper.APIDataFetcher callers
)
from src.api.api_fetch_utils import (
    APIFetchUtils,
)  # Cat E canonical (1014 P8) -- re-export for MistHelper.APIFetchUtils callers
from src.audit.audit_analysis_ops import (  # pylint: disable=unused-import
    AuditAnalysisOps,  # noqa: F401  # Cat B (1013 SC-001 position 12) -- re-export for menu_actions #25/#174 dispatch
)
from src.auth.interactive import (
    LoginOrchestrator,  # noqa: F401  # Re-exported so extracted refactors can resolve it via MistHelper (SC-023)
    MspOrgSelector,
)  # Duplicate import (re-stated with comment below); kept to preserve module load behavior
from src.bootstrap.dependency_check import (
    DependencyCheckOrchestrator,
)  # Duplicate import; harmless re-import of dependency check orchestrator
from src.bootstrap.package_installer import (
    PackageInstaller,
)  # Duplicate import; harmless re-import of package installer
from src.capture.packet_capture import (
    PacketCaptureManager,
)  # Import packet capture manager directly under its canonical name (issue #431: alias removed)

# BatchWorkerConfig import removed: pool machinery moved to ConnectionPoolExecutor (1012 SC-003)
from src.dataclasses.endpoint_config import (  # pylint: disable=unused-import
    EndpointConfig,  # noqa: F401  # Cat B (1013 SC-001 position 16) -- re-export for MistHelper.EndpointConfig callers
)
from src.dataclasses.export_backend_options import (
    ExportBackendOptions,
)  # Issue #470: groups output-backend overrides to keep write_with_format_selection within the 5-Item Rule.
from src.dataclasses.progress_event import (
    ProgressContext,
)  # Issue #470: groups progress-event fields to keep emit_progress_* signatures within the 5-Item Rule.
from src.dataclasses.systematic_test_option import (
    SystematicTestOption,
)  # Issue #470: groups menu-option identity to keep _systematic_test_run_option within the 5-Item Rule.
from src.dataclasses.websocket_stream_target import (  # pylint: disable=unused-import
    WebSocketStreamTarget,  # noqa: F401  # Re-export for MistHelper.WebSocketStreamTarget consumers after ARPCommandManager extraction (1013 SC-001 position 42)
)
from src.db.database_schema_utils import (  # pylint: disable=unused-import
    DatabaseSchemaUtils,  # noqa: F401  # Cat B (1013 SC-001 position 38) -- re-export for MistHelper.DatabaseSchemaUtils callers
)
from src.device.arp_command_manager import (  # pylint: disable=unused-import
    ARPCommandManager,  # noqa: F401  # Cat B (1013 SC-001 position 42) -- re-export for MistHelper.ARPCommandManager callers
)
from src.device.device_reboot_manager import (  # pylint: disable=unused-import
    DeviceRebootManager,  # noqa: F401  # Cat B (1013 SC-001 position 41) -- re-export for MistHelper.DeviceRebootManager callers
)
from src.device.device_utils import (  # pylint: disable=unused-import
    DeviceUtils,  # noqa: F401  # Cat B (1013 SC-001 position 6) -- re-export for dynamic _mh.DeviceUtils lookup
)
from src.export.const_definitions_exporter import (  # pylint: disable=unused-import
    ConstDefinitionsExporter,  # noqa: F401  # Cat B (1013 SC-001 position 17) -- re-export for MistHelper.ConstDefinitionsExporter callers
)
from src.export.device_events_52w_exporter import (  # pylint: disable=unused-import
    DeviceEvents52wExporter,  # noqa: F401  # Re-export preserved after OrgAlarmEventExporter extraction (1013 SC-001 position 18)
)
from src.export.gateway_test_exporter import (  # pylint: disable=unused-import
    GatewayTestExporter,  # noqa: F401  # Cat B (1013 SC-001 position 37) -- re-export for MistHelper.GatewayTestExporter callers
)
from src.export.license_export_utils import (  # pylint: disable=unused-import
    LicenseExportUtils,  # noqa: F401  # Cat B (1013 SC-001 position 24) -- re-export for MistHelper.LicenseExportUtils callers
)
from src.export.msp_inventory_exporter import (  # pylint: disable=unused-import
    MSPInventoryExporter,  # noqa: F401  # Cat B (1013 SC-001 position 8) -- re-export for menu tuple + static call rewire
)
from src.export.org_admin_exporter import (  # pylint: disable=unused-import
    OrgAdminExporter,  # noqa: F401  # Cat B (1013 SC-001 position 20) -- re-export for MistHelper.OrgAdminExporter callers
)
from src.export.org_alarm_event_exporter import (  # pylint: disable=unused-import
    OrgAlarmEventExporter,  # noqa: F401  # Cat B (1013 SC-001 position 18) -- re-export for MistHelper.OrgAlarmEventExporter callers
)
from src.export.org_client_security_exporter import (  # pylint: disable=unused-import
    OrgClientSecurityExporter,  # noqa: F401  # Cat B (1013 SC-001 position 32) -- re-export for MistHelper.OrgClientSecurityExporter callers
)
from src.export.org_config_exporter import (  # pylint: disable=unused-import
    OrgConfigExporter,  # noqa: F401  # Cat B (1013 SC-001 position 31) -- re-export for MistHelper.OrgConfigExporter callers
)
from src.export.org_device_stats_exporter import (  # pylint: disable=unused-import
    OrgDeviceStatsExporter,  # noqa: F401  # Cat B (1013 SC-001 position 45) -- re-export for MistHelper.OrgDeviceStatsExporter callers
)
from src.export.org_export_utils import (  # pylint: disable=unused-import
    OrgExportUtils,  # noqa: F401  # Cat B (1013 SC-001 position 47) -- re-export for MistHelper.OrgExportUtils callers
)
from src.export.org_site_exporter import (  # pylint: disable=unused-import
    OrgSiteExporter,  # noqa: F401  # Cat E canonical (1014 P9) -- re-export for MistHelper.OrgSiteExporter callers
)
from src.export.org_template_exporter import (  # pylint: disable=unused-import
    OrgTemplateExporter,  # noqa: F401  # Cat B (1013 SC-001 position 22) -- re-export for MistHelper.OrgTemplateExporter callers
)
from src.export.self_export_utils import (  # pylint: disable=unused-import
    SelfExportUtils,  # noqa: F401  # Cat B (1013 SC-001 position 7) -- re-export for menu tuple at MistHelper:18167
)
from src.export.site_anomaly_exporter import (  # pylint: disable=unused-import
    SiteAnomalyExporter,  # noqa: F401  # Cat B (1013 SC-001 position 43) -- re-export for MistHelper.SiteAnomalyExporter callers
)
from src.export.site_client_exporter import (  # pylint: disable=unused-import
    SiteClientExporter,  # noqa: F401  # Cat B (1013 SC-001 position 14) -- re-export for MistHelper.SiteClientExporter callers
)
from src.export.site_config_exporter import (  # pylint: disable=unused-import
    SiteConfigExporter,  # noqa: F401  # Cat B (1013 SC-001 position 19) -- re-export for MistHelper.SiteConfigExporter callers
)
from src.export.site_device_exporter import (  # pylint: disable=unused-import
    SiteDeviceExporter,  # noqa: F401  # Cat B (1013 SC-001 position 34) -- re-export for MistHelper.SiteDeviceExporter callers
)
from src.export.site_export_utils import (
    configure_site_export_utils_dependencies,
)  # Import site export utility configuration
from src.export.site_insights.device_metric_operation import (
    DeviceMetricOperation,
)  # Decomposed Menu 76 entry point
from src.export.site_insights.site_metric_operation import (
    SiteMetricOperation,
)  # Decomposed Menu 74 entry point
from src.export.sites_by_ap_model_exporter import (  # pylint: disable=unused-import
    SitesByAPModelExporter,  # noqa: F401  # Cat B (1013 SC-001 position 28) -- re-export for MistHelper.SitesByAPModelExporter callers
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
from src.gateway.gateway_export_utils import (
    configure_gateway_export_utils_dependencies,
)  # Import gateway export utility configuration
from src.gateway.gateway_ha_exporter import (  # pylint: disable=unused-import
    GatewayHaExporter,  # noqa: F401  # Cat B (1013 SC-001 position 23) -- re-export for MistHelper.GatewayHaExporter callers
)
from src.gateway.template_config import GatewayTemplateConfigManager  # Cat A canonical (1013 SC-001)
from src.input.prompt_client_utils import (  # pylint: disable=unused-import
    PromptClientUtils,  # noqa: F401  # Cat B (1013 SC-001 position 35) -- re-export for MistHelper.PromptClientUtils callers
)
from src.inventory.org_device_inventory_summary_facade import (  # pylint: disable=unused-import
    OrgDeviceInventorySummary,  # noqa: F401  # Cat B (1013 SC-001 position 29) -- re-export for MistHelper.OrgDeviceInventorySummary callers
)
from src.network.routing_utils import (  # Cat A canonical (1014 P4)
    RoutingDeps,
    RoutingUtils,
)
from src.org.org_config_migration_manager import OrgConfigMigrationManager  # Cat B (1013 SC-001 position 5)
from src.org.org_ticket_manager import (  # pylint: disable=unused-import
    OrgTicketManager,  # noqa: F401  # Cat B (1013 SC-001 position 46) -- re-export for MistHelper.OrgTicketManager callers
)
from src.org_data_collector import OrgDataCollector  # Import org-level data collection orchestrator
from src.refactors.anomaly_metrics_discovery import (  # pylint: disable=unused-import
    AnomalyMetricsDiscovery,  # noqa: F401  # Cat B (1013 SC-001 pos 43) -- lazy access via mh.AnomalyMetricsDiscovery
)
from src.refactors.connection_pool_executor import ConnectionPoolExecutor  # Extracted pool executor (1012 SC-003)
from src.refactors.data_directory_checker import DataDirectoryChecker  # Early data-dir writable check (SC-005)
from src.refactors.device_config_template_cloner_manager import (
    DeviceConfigTemplateClonerManager,  # Extracted device config template cloner (SC-020)
)
from src.refactors.device_data_fetcher import (  # pylint: disable=unused-import
    DeviceDataFetcher,  # noqa: F401  # Extracted interactive device data fetcher (SC-017) -- re-export for src.ui.interactive_display_utils lazy access
)
from src.refactors.fast_mode_backoff_multiplier import (  # pylint: disable=unused-import
    FastModeBackoffMultiplier,  # noqa: F401  # Extracted fast-mode backoff multiplier constant (SC-028); re-export for src.export.org_device_stats_exporter lazy access
)

# FastModeDevicesPerThread import removed: only referenced from within ConnectionPoolExecutor (1012 SC-003)
from src.refactors.fast_mode_sequential_max_retries import (  # pylint: disable=unused-import
    FastModeSequentialMaxRetries,  # noqa: F401  # Cat E (1014 P8) -- re-export for lazy mh.FastModeSequentialMaxRetries in api_fetch_utils.py
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
from src.refactors.keyboard_listener import (  # noqa: F401  # pylint: disable=unused-import
    KeyboardListener,  # Re-exported for src.ssh.cli_shell_manager.CLIShellManager lazy `mh.KeyboardListener` access
)
from src.refactors.main_entrypoint import MainEntrypoint  # Extracted CLI main entrypoint (SC-026)
from src.refactors.maps_manager_launcher import MapsManagerLauncher  # Extracted Maps Manager launcher (SC-006)
from src.refactors.marvis_data_utils import (  # pylint: disable=unused-import
    MarvisDataUtilsFactory,  # noqa: F401  # Cat B (1013 SC-001 position 39) -- re-export for lazy mh.MarvisDataUtilsFactory callers in troubleshoot_utils.py
)
from src.refactors.mist_wan_target_ports import (
    MistWanTargetPorts,  # Extracted operator-configured WAN target-ports list (SC-032)
)
from src.refactors.package_import_map import (
    PackageImportMapManager,  # Extracted pip-name -> import-name mapping (SC-025)
)
from src.refactors.run_interactive_test import (
    RunInteractiveTestManager,  # Extracted interactive-test manager (SC-011)
)
from src.refactors.service_ping_launcher import ServicePingLauncher  # Extracted Service Ping launcher (SC-008)
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter  # Extracted SQLite writer (SC-003)
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
from src.reports.e911_bssid import (  # pylint: disable=unused-import
    E911BSSIDReportGenerator,  # noqa: F401  # Module-level for tests + lazy-import re-export for src.export.org_export_utils
)
from src.reports.global_wired_client_report_generator import (  # pylint: disable=unused-import
    GlobalWiredClientReportGenerator,  # noqa: F401  # Cat B (1013 SC-001 position 36) -- re-export for MistHelper.GlobalWiredClientReportGenerator callers
)
from src.reports.offline_device_reporter import (  # pylint: disable=unused-import
    OfflineDeviceReporter,  # noqa: F401  # Cat B (1013 SC-001 position 44) -- re-export for MistHelper.OfflineDeviceReporter callers
)
from src.reports.sfp_transceiver_data_processor import (  # pylint: disable=unused-import
    SFPTransceiverDataProcessor,  # noqa: F401  # Cat B (1013 SC-001 position 27) -- re-export for MistHelper.SFPTransceiverDataProcessor callers
)
from src.reports.wired_client_manufacturer_report_generator import (  # pylint: disable=unused-import
    WiredClientManufacturerReportGenerator,  # noqa: F401  # Cat B (1013 SC-001 position 26) -- re-export for MistHelper.WiredClientManufacturerReportGenerator callers
)
from src.site.address_audit import AddressAuditEngine  # Menu 195: read-only CSV site-address audit
from src.site.bulk_radius_wlan_config_manager import (  # pylint: disable=unused-import
    BulkRadiusWLANConfigManager,  # noqa: F401  # Cat B (1013 SC-001 position 15) -- re-export for MistHelper.BulkRadiusWLANConfigManager callers
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
from src.ssh.cli_shell_manager import CLIShellManager  # pylint: disable=unused-import  # noqa: F401
from src.ssh.ssh_runner import EnhancedSSHRunner  # Import SSH command execution and result parsing
from src.ssh.ssh_runner_manager import (
    SSHRunnerManager as ExtractedSSHRunnerManager,
)  # Import SSH runner manager (renamed to avoid conflicts)
from src.ssh.ssh_runner_manager import SSHRunnerManagerDeps  # Import SSH runner manager dependency injection class
from src.time.time_utils import TimeUtils  # Cat E canonical (1014 P6)
from src.troubleshooting.interactive_test_runner import (
    InteractiveTestRunner,
)  # Import interactive diagnostic test runner
from src.troubleshooting.marvis_troubleshoot_utils import (  # pylint: disable=unused-import
    MarvisTroubleshootDeps,  # noqa: F401  # Cat B (1013 SC-001 position 39) -- re-export for lazy mh.MarvisTroubleshootDeps callers in troubleshoot_utils.py
)
from src.troubleshooting.marvis_troubleshoot_utils import (  # pylint: disable=unused-import
    MarvisTroubleshootUtils as ExtractedMarvisTroubleshootUtils,  # noqa: F401  # Cat B (1013 SC-001 position 39) -- re-export for lazy mh.ExtractedMarvisTroubleshootUtils callers
)
from src.troubleshooting.troubleshoot_utils import (  # pylint: disable=unused-import
    TroubleshootUtils,  # noqa: F401  # Cat B (1013 SC-001 position 39) -- re-export for MistHelper.TroubleshootUtils callers
)
from src.ui.display_utils import (  # pylint: disable=unused-import
    DisplayUtils,  # noqa: F401  # Cat B (1013 SC-001 position 11) -- re-export for lazy _MH.DisplayUtils callers
)
from src.ui.interactive_display_utils import (  # pylint: disable=unused-import
    InteractiveDisplayUtils,  # noqa: F401  # Cat B (1013 SC-001 position 10) -- re-export for callers at 17392/17393/17394/17395
)
from src.utils.environment_utils import (  # pylint: disable=unused-import
    EnvironmentUtils,  # noqa: F401  # Cat B (1013 SC-001 position 33) -- re-export for MistHelper.EnvironmentUtils callers
)
from src.utils.filter_operator_engine import (  # pylint: disable=unused-import
    FilterOperatorEngine,  # noqa: F401  # Cat B (1013 SC-001 position 40) -- re-export for MistHelper.FilterOperatorEngine callers
)
from src.utils.operation_registry import (  # pylint: disable=unused-import
    OperationRegistry,  # noqa: F401  # Cat B (1013 SC-001 position 13) -- re-export for menu safety classification
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


@dataclass
class DeviceFetchConfig:
    """Configuration for interactive device data fetching - groups fetch parameters."""

    fetch_function: Any  # Callable that performs the actual API fetch for the chosen data
    filename: str  # Output filename for the exported data
    description: str  # Human-readable description shown to the user during the fetch
    device_type: str = "all"  # Device type filter (all/ap/switch/gateway); 'all' avoids the AP-only API default
    site_id: str | None = None  # Optional site scope; None means an org-wide fetch
    device_id: str | None = None  # Optional single-device scope; None means all matching devices


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
_VERSION_COMPARATORS = {
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
            return data.get("info", {}).get("version", "")  # type: ignore[no-any-return]  # Return latest version string, or '' if absent
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
def _early_dependency_check():  # Public entry point; delegates to the extracted bootstrap modules
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
_early_dependency_check()  # type: ignore[no-untyped-call]  # Run the bootstrap immediately at import time

# Additional standard library imports
import ast  # Safely parse Python literals from strings (config/data deserialization)
import concurrent.futures  # High-level parallelism primitives for batched API calls
import inspect  # Introspect functions/classes at runtime (signatures, source lookup)
import json  # Encode/decode JSON for API payloads and cache files
import threading  # Locks and threads for safe concurrent operations
from collections import defaultdict  # Dict that auto-creates default values (avoids key-exists checks)

# Note: datetime class already imported at top of file (line 26)
# Only import timezone, timedelta here to avoid shadowing datetime class
from datetime import UTC, timedelta, timezone  # UTC marker plus helpers for timezone-aware time math

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
    import numpy as np  # Numerical arrays for analytics calculations
except ImportError:  # numpy not installed
    np = None  # type: ignore[assignment]  # Optional - analytics features limited  # None lets runtime guards detect absence

try:  # websocket-client is required for live device diagnostics
    import websocket  # noqa: F401  # WebSocket client fail-fast install guard (used by src.device.arp_command_manager)
except ImportError as _ws_err:  # Required dependency is missing
    raise ImportError(
        "websocket-client is required but not installed. Run: pip install websocket-client"
    ) from _ws_err  # Fail fast with install guidance

try:  # SequenceMatcher is optional (used for fuzzy string comparisons)
    from difflib import SequenceMatcher  # Stdlib similarity-ratio helper
except ImportError:  # Extremely unlikely for a stdlib module, but guard anyway
    SequenceMatcher = None  # type: ignore[assignment, misc]  # None lets callers detect absence

# Import mistapi later through GlobalImportManager for better dependency management
# Using Any type since mistapi is dynamically loaded but guaranteed to be available before use
mistapi: Any = None  # Placeholder; the real mistapi module is loaded later by GlobalImportManager


# tqdm will be properly imported by GlobalImportManager
# This fallback will be overridden by the real tqdm import
# NOTE: tqdm extracted to SKIP_ALWAYS (bootstrap-critical). See specs/1012-misthelper-refactor-hot-functions/spec.md.
def tqdm(iterable, *args, **kwargs):  # No-op progress-bar stand-in until the real tqdm loads
    """Fallback tqdm function - will be replaced by real tqdm after import initialization."""
    return iterable  # Return the iterable unchanged (no progress bar yet)


try:  # requests is required for all HTTP calls
    import requests  # noqa: F401  # HTTP library fail-fast install guard (also used via function-local imports)
except ImportError as _req_err:  # Required dependency is missing
    raise ImportError(
        "requests is required but not installed. Run: pip install requests"
    ) from _req_err  # Fail fast with install guidance

try:  # urllib3 is optional (used to suppress noisy SSL warnings)
    import urllib3  # Low-level HTTP library underlying requests
except ImportError:  # urllib3 not installed
    urllib3 = None  # type: ignore[assignment]  # Optional - SSL warning suppression  # None lets guards detect absence

try:  # pyte is optional (terminal emulation for parsing WebSocket output)
    import pyte  # In-memory terminal emulator to render device CLI screens

    _has_pyte = True  # Flag that terminal-emulation features are available
except ImportError:  # pyte not installed
    pyte = None  # type: ignore[assignment]  # Optional - terminal emulation  # None lets guards detect absence
    _has_pyte = False  # Flag that terminal-emulation features are unavailable

try:  # paramiko is optional (used for direct SSH operations)
    import paramiko  # type: ignore[import-untyped]  # SSH client library
    from paramiko import RejectPolicy, SSHClient  # Strict host-key policy and the SSH client class
except ImportError:  # paramiko not installed
    paramiko = None  # type: ignore[assignment]  # Optional - SSH operations  # None lets guards detect absence
    SSHClient = None  # type: ignore[assignment, misc]  # Optional - SSH operations  # None lets guards detect absence
    RejectPolicy = None  # type: ignore[assignment, misc]  # Optional - SSH operations  # None lets guards detect absence

# Optional imports with fallbacks
try:  # scourgify is optional (US street-address normalization)
    from scourgify import normalize_address_record  # Normalize messy US addresses into structured fields
except ImportError:  # scourgify not installed
    normalize_address_record = None  # None lets callers fall back to raw address strings

try:  # rapidfuzz is optional (fast fuzzy string matching)
    from rapidfuzz import fuzz  # High-performance fuzzy match scoring
except ImportError:  # rapidfuzz not installed
    fuzz = None  # type: ignore[assignment]  # None lets callers skip fuzzy matching

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
    from dotenv import load_dotenv  # Robust .env parser from python-dotenv

    DOTENV_AVAILABLE = True  # Flag that the real loader is in use
    load_dotenv()  # Load .env now so config is available to the import manager
except ImportError:  # python-dotenv not installed
    DOTENV_AVAILABLE = False  # Flag that we're using the minimal fallback
    # Use fallback loader and create an alias for later calls
    load_dotenv = _fallback_load_dotenv  # type: ignore[assignment]  # Alias so later load_dotenv() calls still work
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

    def __init__(self):  # Read config from env and prepare dependency-tracking state
        """Initialize the import manager with configuration from environment variables."""
        self._load_upgrade_configuration()  # Read env-driven upgrade/UV/CSV freshness settings
        self._initialize_dependency_tracking()  # Prepare package-tracking lists and import/UV caches
        self._initialize_import_mappings()  # Build package->import name maps and special import handlers
        self._setup_logging()  # type: ignore[no-untyped-call]  # Configure handlers/levels before other init runs
        self._detect_virtual_environment()  # type: ignore[no-untyped-call]  # Log whether we're in a venv (affects installs)
        self._define_package_requirements()  # type: ignore[no-untyped-call]  # Populate the required/optional package dicts

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

    def _detect_virtual_environment(self):  # Determine and log whether a venv is active
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

    def _setup_logging(self):  # Build console+file handlers with env-driven levels
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

    def _define_package_requirements(self):  # Populate the required/optional package dictionaries
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

    def _import_concurrent_futures(self):
        """Special handler for concurrent.futures import."""
        from concurrent.futures import ThreadPoolExecutor, as_completed  # Import the thread-pool primitives on demand

        return type(
            "ConcurrentFutures", (), {"ThreadPoolExecutor": ThreadPoolExecutor, "as_completed": as_completed}
        )()  # Bundle them on a tiny namespace object

    class _DateTimeHandler:  # Adapter exposing both class-like and module-like datetime access
        """Adapter exposing both class-like and module-like datetime access."""

        def __init__(self):
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

    def _import_datetime(self):
        """Special handler for datetime import."""
        logging.debug("_import_datetime: returning _DateTimeHandler adapter")  # Log before construction
        return self._DateTimeHandler()  # type: ignore[no-untyped-call]  # Hand back the dual-purpose adapter

    def _import_tqdm(self):
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
            return self.special_import_handlers[module_name]()  # type: ignore[no-untyped-call]  # Invoke special handler.
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
        logging.info("Attempting to install missing dependency: %s", package_spec)  # Announce the install attempt.
        if not self._attempt_install(package_spec):  # type: ignore[arg-type]  # No installer succeeded.
            logging.error("Failed to install %s", package_spec)  # Report the install failure.
            return None  # Cannot retry without a successful install.
        self._clear_failed_import_cache(module_name)  # Purge stale caches before the retry.
        time.sleep(0.5)  # Brief pause to let filesystem writes settle before retrying.
        return self._retry_import_after_install(module_name, package_spec, required)  # type: ignore[arg-type]  # Retry.

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
            self._check_and_upgrade_package(module_name, package_spec)  # type: ignore[arg-type]  # Upgrade package.

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
    ) -> tuple[bool, dict[str, Any]]:  # noqa: C901, PLR0912, PLR0915
        """
        Initialize all imports and dependencies upfront.

        Args:
            skip_deps: Skip dependency checking and installation

        Returns:
            Tuple of (success: bool, global_assignments: dict)
        """
        from src.refactors.serial_cc.import_initialization_service import ImportInitializationService

        return ImportInitializationService.execute(self, skip_deps=skip_deps)

    def _get_global_assignments(self):  # noqa: C901, PLR0912, PLR0915
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
                from scourgify import normalize_address_record as normalize_func  # Direct import fallback
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
import_manager = GlobalImportManager()  # type: ignore[no-untyped-call]  # Single shared manager for all dependency imports

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


class InputUtils:
    """
    Centralized input handling utilities.
    Handles safe input with EOF handling, tqdm availability, etc.
    """

    @staticmethod
    def ensure_tqdm_available() -> bool:
        """Ensure tqdm is available and properly imported."""
        global tqdm  # Rebind the module-level tqdm if we recover a better implementation
        if hasattr(tqdm, "__module__") and tqdm.__module__ == "tqdm":  # Real tqdm already active
            logging.debug("tqdm is properly imported and available")  # Nothing to do
            return True  # Progress bars are functional
        return InputUtils._try_recover_tqdm()  # Probe import_manager then direct import

    @staticmethod
    def _try_recover_tqdm() -> bool:
        """Try to recover tqdm from import_manager cache, then by direct import."""
        global tqdm  # We may rebind the module global with the recovered implementation
        logging.debug("_try_recover_tqdm: probing import_manager.imports and direct import")  # Log before probe
        tqdm_from_manager = import_manager.imports.get("tqdm")  # Issue #431: inlined get_import.
        if tqdm_from_manager:  # The manager has a usable tqdm
            tqdm = tqdm_from_manager  # Replace the fallback with the real implementation
            logging.info("Retrieved tqdm from import manager")  # Record the recovery
            return True  # Progress bars are now functional
        try:  # Last-resort direct import path
            from tqdm import tqdm as real_tqdm  # Last-resort direct import

            tqdm = real_tqdm  # Adopt the directly-imported progress bar
            logging.info("Successfully imported tqdm directly")  # Record the successful import
            return True  # Progress bars are now functional
        except ImportError:  # tqdm simply is not installed
            logging.warning("tqdm package is not available - progress bars will be disabled")  # Warn of degraded UX
            return False  # Caller should proceed without progress bars

    @staticmethod
    def safe_input(prompt: str, default_value: str = "", allow_empty: bool = True, context: str = "unknown") -> str:
        """EOF/Interrupt-safe input wrapper that returns default_value on EOF and "" on Ctrl+C.

        allow_empty: when False, blank input returns "" (the caller decides what to do).
        context: short label used in the EOF/interrupt messages and logs.
        """
        try:  # Read may raise EOFError on disconnect or KeyboardInterrupt on Ctrl+C
            user_input = input(prompt).strip()  # Read a line and trim surrounding whitespace
            if not user_input:  # Blank input -- delegate the 3-way decision to the helper
                return InputUtils._resolve_empty_input(default_value, allow_empty, context)  # Default/empty/reject
            return user_input  # Normal path: return the trimmed user response
        except EOFError:  # Stream closed (Ctrl+D, broken pipe, SSH disconnect)
            print(
                f"\n[EOF] Input stream closed during {context}. Using default value: '{default_value}'"
            )  # Inform the user
            logging.info(
                "EOF encountered on input during %s - returning default: '%s'", context, default_value
            )  # Log the disconnect
            return default_value  # Degrade gracefully to the default instead of crashing
        except KeyboardInterrupt:  # User pressed Ctrl+C
            print(f"\n[INTERRUPT] User interrupted {context}. Canceling...")  # Acknowledge the cancellation
            logging.info("KeyboardInterrupt encountered during %s", context)  # Log the interrupt
            return ""  # Return empty to signal the caller should abort this prompt

    @staticmethod
    def _resolve_empty_input(default_value: str, allow_empty: bool, context: str) -> str:
        """Decide what to return when safe_input received a blank line."""
        if default_value:  # A default is configured -- substitute it
            logging.debug(
                "Empty input for %s, using default: '%s'", context, default_value
            )  # Note the default substitution
            return default_value  # Return the caller-supplied default
        if allow_empty:  # Blank entry is acceptable here
            return ""  # Return the empty string as-is
        logging.warning(
            "Empty input not allowed for %s, returning empty string", context
        )  # Warn about the rejected blank
        return ""  # Signal an invalid/empty response to the caller


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
FAST_MODE_MAX_CONCURRENT_CONNECTIONS = int(
    os.getenv("FAST_MODE_MAX_CONCURRENT_CONNECTIONS", "8")
)  # Cap on simultaneous API connections
FAST_MODE_USE_CONNECTION_AWARE_THREADING = (  # Whether to size threads based on connection limits
    os.getenv("FAST_MODE_USE_CONNECTION_AWARE_THREADING", "true").lower() == "true"  # Parse the boolean env flag
)
FAST_MODE_ENABLED: bool = False  # Set to True via --fast CLI flag at startup

# NOTE: MIST_WAN_TARGET_PORTS extracted to src/refactors/mist_wan_target_ports.py
# per initiative 1011 SC-032 (FR-003: no wrapper shim; FR-005: assignment->classattr).

# Site Exclusion Configuration from .env (REQUIRED - no defaults)
# MIST_SITE_EXCLUDE_PREFIX: Site name prefix to exclude from destructive operations
# Example: "VRE" to exclude Juniper internal VRE sites
MIST_SITE_EXCLUDE_PREFIX = os.getenv(
    "MIST_SITE_EXCLUDE_PREFIX", ""
)  # Name prefix that shields sites from destructive ops

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


def _msp_resolve_name(msp_id: str, priv: dict) -> str:
    """Resolve a human-readable MSP name from a grant, falling back to the MSP API or a short id label."""
    msp_name = priv.get("msp_name") or priv.get("name")  # The API uses different keys across versions.
    if not msp_name or msp_name == "Unknown":  # Name absent or placeholder.
        return _fetch_msp_name(msp_id) or f"MSP-{msp_id[:8]}"  # Look it up, else derive a short label.
    return msp_name  # The grant already carried a usable name.


def _msp_parse_one_privilege(priv: Any) -> dict | None:  # type: ignore[type-arg]
    """Parse one privilege grant into a normalized MSP record, or None when it is not a valid MSP grant."""
    if not (isinstance(priv, dict) and priv.get("msp_id")):  # Only MSP-scoped dict grants qualify.
        return None  # Not an MSP grant; skip it.
    logging.debug(
        "MSP privilege found: scope=%s, role=%s", priv.get("scope"), priv.get("role")
    )  # Log the grant details.
    msp_id = priv.get("msp_id")  # Extract the MSP identifier.
    if not msp_id or not isinstance(msp_id, str):  # Guard against missing/invalid IDs.
        return None  # Skip malformed grants.
    msp_name = _msp_resolve_name(msp_id, priv)  # Resolve the human-readable MSP name.
    msp_info = {  # Build a normalized record for this MSP grant.
        "msp_id": msp_id,  # The MSP's unique identifier.
        "msp_name": msp_name,  # Human-readable MSP name.
        "role": priv.get("role", "unknown"),  # The user's role within this MSP.
        "scope": priv.get("scope", "unknown"),  # The scope of the grant.
    }
    logging.info(
        "Detected MSP privilege: %s (ID: %s..., role: %s, scope: %s)",
        msp_info["msp_name"],
        msp_info["msp_id"][:8],
        msp_info["role"],
        msp_info["scope"],
    )  # Report the detected grant.
    return msp_info  # Hand back the normalized MSP record.


def _msp_extract_from_user_data(user_data: dict) -> list[dict]:  # type: ignore[type-arg]
    """Extract all MSP-scoped privilege records from a getSelf user-data payload."""
    privileges = user_data.get("privileges", [])  # Pull the list of privilege grants.
    logging.debug("MSP detection: parsing %s privilege entries", len(privileges))  # Log how many grants we'll scan.
    detected_msps = []  # Accumulate any MSP-scoped privileges we find.
    for priv in privileges:  # Examine each privilege grant.
        msp_info = _msp_parse_one_privilege(priv)  # Normalize this grant (None when not an MSP grant).
        if msp_info is not None:  # The grant was a valid MSP grant.
            detected_msps.append(msp_info)  # Record it.
    return detected_msps  # Return every MSP grant found in the payload.


def _msp_fetch_user_data() -> dict | None:  # type: ignore[type-arg]
    """Call getSelf and return the validated user-data dict, or None when unavailable or malformed."""
    import mistapi.api.v1.self.self as self_api  # Import the "self" endpoint module lazily.

    assert apisession is not None  # Caller guarantees session is initialized before MSP detection.
    response = self_api.getSelf(apisession)  # Ask the API who the authenticated user is.
    if not response or not hasattr(response, "data"):  # No usable payload came back.
        logging.warning("getSelf returned no data - cannot detect MSP privileges")  # Warn we can't determine access.
        return None  # No privileges could be detected.
    user_data = response.data  # Extract the decoded JSON body.
    if not isinstance(user_data, dict):  # The body should be a JSON object.
        logging.warning("getSelf returned unexpected type: %s", type(user_data))  # Warn about the malformed shape.
        return None  # Cannot parse privileges from this.
    return user_data  # Hand back the validated user-data payload.


def _msp_cache_and_report(detected_msps: list[dict]) -> None:  # type: ignore[type-arg]
    """Cache detected MSP grants to the module global and log the outcome."""
    global msp_privileges  # We publish the detected grants for later menus to reuse.
    if detected_msps:  # At least one MSP grant was found.
        msp_privileges = detected_msps  # Cache the grants in the module-level global.
        logging.info("User has MSP-level access to %s MSP(s)", len(detected_msps))  # Report the count.
    else:  # No MSP grants present.
        logging.debug("No MSP privileges detected for current user")  # Note the absence at debug level.


def detect_msp_privileges(session=None):
    """Detect MSP-level privileges from the authenticated user's profile via GET /api/v1/self.

    An explicit ``session`` (passed by the interactive login before the module-global
    ``apisession`` is published) is promoted to the global. Returns MSP privilege dicts
    (msp_id, msp_name, role, scope), or [] when there is no MSP access or detection fails.
    """
    global apisession  # Session promotion below may update the module-global session.
    if session is not None:  # Caller supplied an explicit session (interactive login, before the global is published).
        apisession = session  # Promote it to the global so getSelf and _fetch_msp_name use the same session.

    if not apisession:  # Still no usable session from either the argument or the global.
        logging.warning("Cannot detect MSP privileges - no active session")  # Warn that detection cannot proceed.
        return []  # Treat as no MSP access.

    try:  # API or parsing failures must degrade to "no MSP access" rather than crash the session.
        user_data = _msp_fetch_user_data()  # Call getSelf and validate the payload (None when unavailable).
        if user_data is None:  # getSelf failed or returned a malformed payload.
            return []  # No privileges could be detected.
        detected_msps = _msp_extract_from_user_data(user_data)  # Parse every MSP-scoped grant.
        _msp_cache_and_report(detected_msps)  # Cache to the global and log the outcome.
        return detected_msps  # Hand the parsed MSP list back to the caller.
    except Exception as e:  # Any API or parsing failure.
        logging.warning("Failed to detect MSP privileges: %s", e)  # Warn but don't crash the session.
        return []  # Treat as no MSP access on error.


def _extract_msp_name(response: Any) -> str | None:  # Pull the MSP name out of a getMspDetails response
    """Return the 'name' string from an MSP details response, or None when absent/malformed."""
    data = getattr(response, "data", None)  # Unwrap the response payload if present
    if not isinstance(data, dict):  # Need a dict payload to read the name field
        return None  # Malformed or empty response
    name = data.get("name")  # Extract the MSP's name field
    return name if isinstance(name, str) else None  # Return the name only if it's a valid string


def _fetch_msp_name(msp_id: str) -> str | None:
    """Helper to fetch MSP name from MSP API when not provided in privileges.

    Args:
        msp_id: The MSP ID to look up

    Returns:
        MSP name string, or None if lookup fails
    """
    if apisession is None:  # No active session to query with
        return None  # Can't look anything up
    try:
        import mistapi.api.v1.msps.msps as msps_api  # Import the MSP details endpoint lazily

        response = msps_api.getMspDetails(apisession, msp_id)  # Fetch the MSP record by ID
        return _extract_msp_name(response)  # Pull the name from the payload (None when absent/malformed)
    except Exception as e:  # Lookup failed (network, permissions, etc.)
        logging.debug("Could not fetch MSP name for %s...: %s", msp_id[:8], e)  # Note the failure at debug level
        return None  # Default to None when the name can't be resolved


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

    if not MistSessionInteractiveInitializer.initialize():  # Attempt the interactive login
        print("")  # Blank spacer line
        print("  X Login failed - restoring previous session")  # Inform the user of the rollback
        apisession = old_session  # Restore the prior API session
        org_id = old_org_id  # Restore the prior org selection
        detect_msp_privileges()  # type: ignore[no-untyped-call]  # Re-detect MSP grants for the restored session
        logging.warning("Interactive login failed - restored previous API session")  # Log the failed attempt
        return False  # Signal failure to the caller
    logging.debug("Interactive login succeeded")  # Trace the successful login
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
        _select_msp_and_org()  # type: ignore[no-untyped-call]  # MSP users pick an MSP then an org
    else:  # No MSP access
        _select_org_from_session()  # type: ignore[no-untyped-call]  # Non-MSP users pick an org directly


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


def _select_msp_and_org():
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


def _invoke_mistapi_org_picker_and_apply() -> None:
    """Run mistapi's org picker and apply the user's choice to the org_id global."""
    global org_id  # The picker result writes through to the module-level org
    try:  # mistapi may raise on network errors or invalid sessions
        logging.debug("Invoking mistapi.cli.select_org()")  # Trace the SDK call
        org_id_list = mistapi.cli.select_org(apisession)  # Let mistapi present an org picker and return the choice
        if org_id_list and len(org_id_list) > 0:  # The user selected at least one org
            org_id = org_id_list[0]  # Use the first selected org ID
            print(f"  + Organization ID set: {org_id}")  # Confirm the selection to the user
            logging.info("User selected org from session: %s", org_id)  # Log the chosen org
        else:  # Nothing was selected
            print("  X No organization selected")  # Inform the user no org was chosen
            logging.warning("No organization selected from session privileges")  # Log the empty selection
    except Exception as e:  # The SDK picker raised an error
        print(f"  X Error selecting organization: {e}")  # Show the error to the user
        logging.error("Failed to select org from session: %s", e)  # nosec B608  # Log the failure detail


def _select_org_from_session():
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

        def send(  # noqa: PLR0913, STRUCT-PARAMS  # external contract: requests.HTTPAdapter.send signature
            self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
        ):
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
# This configuration determines how each API endpoint's data should be stored in Redis/SQLite
# with proper primary keys to eliminate artificial api_id fields and enable efficient queries
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # Type 1: Natural primary key using API id field (for entity APIs)
    # These APIs return objects with stable UUID identifiers that make perfect primary keys
    "getOrgInventory": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
        "unique_constraints": [],
        "description": "Organization device inventory with stable UUID identifiers",
    },
    "listOrgSites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "country_code", "address"],
        "unique_constraints": [],
        "description": "Organization sites with stable UUID identifiers",
    },
    "listSiteDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "serial", "model", "type", "name"],
        "unique_constraints": [],
        "description": "Site devices with stable UUID identifiers",
    },
    "getOrgDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
        "unique_constraints": [],
        "description": "Organization devices with stable UUID identifiers",
    },
    # Template and configuration entities
    "createOrgGatewayTemplate": {
        "type": "natural_pk",  # API returns a UUID id field on the newly created template
        "primary_key": ["id"],  # Template UUID is the stable natural key for upsert
        "indexes": ["org_id", "name", "type"],  # Secondary lookup fields for queries
        "unique_constraints": [],  # No additional unique constraints beyond PK
        "description": "Newly created org gateway template from device config clone",
    },
    "listOrgGatewayTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Gateway templates with stable UUID identifiers",
    },
    "listOrgNetworkTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Network templates with stable UUID identifiers",
    },
    "listOrgRfTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "band"],
        "unique_constraints": [],
        "description": "RF templates with stable UUID identifiers",
    },
    "listOrgSiteTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Site templates with stable UUID identifiers",
    },
    "listOrgAptemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "AP templates with stable UUID identifiers",
    },
    "listOrgSecPolicies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Security policies with stable UUID identifiers",
    },
    "listOrgPsks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "ssid"],
        "unique_constraints": [],
        "description": "Pre-shared keys with stable UUID identifiers",
    },
    "listOrgWebhooks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Webhooks with stable UUID identifiers",
    },
    # Type 2: Composite primary key for event and log APIs
    # These APIs return time-series data that requires composite keys for uniqueness
    "searchOrgAlarms": {
        "type": "composite_pk",
        "primary_key": ["id", "org_id", "timestamp"],
        "indexes": ["org_id", "timestamp", "severity", "type", "site_id"],
        "unique_constraints": [],
        "description": "Organization alarms with composite key for time-series data",
    },
    "searchOrgDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "type", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "Device events with composite key for uniqueness",
    },
    "searchOrgClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "site_id", "timestamp"],
        "indexes": ["site_id", "timestamp", "type", "client_mac", "device_id"],
        "unique_constraints": [],
        "description": "Client events with composite key for uniqueness",
    },
    "searchOrgSystemEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "org_id", "timestamp"],
        "indexes": ["org_id", "timestamp", "type"],
        "unique_constraints": [],
        "description": "System events with composite key for uniqueness",
    },
    # Type 3: TimeSeries metrics -- pure-numeric endpoints routed to Redis TimeSeries
    # These APIs return time-series data with explicit numeric and label fields
    "listOrgDevicesStats": {
        "type": "timeseries_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "Organization device statistics routed to Redis TimeSeries",
        "ts_value_fields": ["cpu_util", "mem_util", "uptime", "num_clients"],
        "ts_label_fields": ["hostname", "model", "type", "site_id"],
    },
    "listSiteDevicesStats": {
        "type": "timeseries_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "site_id", "type"],
        "unique_constraints": [],
        "description": "Site device statistics routed to Redis TimeSeries",
        "ts_value_fields": ["cpu_util", "mem_util", "uptime", "num_clients"],
        "ts_label_fields": ["hostname", "model", "type"],
    },
    "listSiteWirelessClientsStats": {
        "type": "timeseries_pk",
        "primary_key": ["client_mac", "timestamp"],
        "indexes": ["client_mac", "timestamp", "site_id", "device_id"],
        "unique_constraints": [],
        "description": "Wireless client statistics routed to Redis TimeSeries",
        "ts_value_fields": ["rssi", "snr", "rx_rate", "tx_rate"],
        "ts_label_fields": ["ssid", "hostname", "device_id"],
    },
    "searchOrgSwOrGwPorts": {
        "type": "timeseries_pk",
        "primary_key": ["device_id", "port_id", "timestamp"],
        "indexes": ["device_id", "port_id", "timestamp", "org_id"],
        "unique_constraints": [],
        "description": "Switch/gateway port statistics routed to Redis TimeSeries",
        "ts_value_fields": ["rx_bytes", "tx_bytes", "rx_errors", "tx_errors"],
        "ts_label_fields": ["port_id", "device_id", "org_id"],
    },
    "searchSiteSwOrGwPorts": {
        "type": "timeseries_pk",
        "primary_key": ["device_id", "port_id", "timestamp"],
        "indexes": ["device_id", "port_id", "timestamp", "site_id"],
        "unique_constraints": [],
        "description": "Site port statistics routed to Redis TimeSeries",
        "ts_value_fields": ["rx_bytes", "tx_bytes", "rx_errors", "tx_errors"],
        "ts_label_fields": ["port_id", "device_id", "site_id"],
    },
    "searchOrgPeerPathStats": {
        "type": "timeseries_pk",
        "primary_key": ["from_device", "to_device", "timestamp"],
        "indexes": ["from_device", "to_device", "timestamp", "org_id"],
        "unique_constraints": [],
        "description": "Peer path statistics routed to Redis TimeSeries",
        "ts_value_fields": ["latency", "jitter", "loss"],
        "ts_label_fields": ["from_device", "to_device", "org_id"],
    },
    # -- Issue #177: Site routing / network topology endpoints --
    "searchSiteBgpStats": {
        "type": "composite_pk",
        "primary_key": ["mac", "neighbor", "timestamp"],
        "indexes": ["site_id", "org_id", "state", "neighbor_as"],
        "unique_constraints": [],
        "description": "Site BGP peering statistics",
    },
    "searchSiteOspfStats": {
        "type": "composite_pk",
        "primary_key": ["mac", "peer_ip", "timestamp"],
        "indexes": ["site_id", "org_id", "state", "port_id"],
        "unique_constraints": [],
        "description": "Site OSPF adjacency statistics",
    },
    "listSiteEvpnTopologies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "name"],
        "unique_constraints": [],
        "description": "Site EVPN topology definitions",
    },
    "searchSiteDiscoveredSwitches": {
        "type": "composite_pk",
        "primary_key": ["system_name", "mgmt_addr", "timestamp"],
        "indexes": ["site_id", "org_id", "vendor", "model"],
        "unique_constraints": [],
        "description": "Site discovered (unadopted) switches",
    },
    "listSiteDiscoveredSwitchesMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id", "org_id"],
        "unique_constraints": [],
        "description": "Site discovered switch aggregate metrics",
    },
    "searchSiteDiscoveredSwitchesMetrics": {
        "type": "composite_pk",
        "primary_key": ["system_name", "type", "timestamp"],
        "indexes": ["site_id", "org_id", "scope", "score"],
        "unique_constraints": [],
        "description": "Site discovered switch metric search results",
    },
    "listSiteCurrentRrmNeighbors": {
        "type": "composite_pk",
        "primary_key": ["mac"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Site RRM AP neighbor relationships",
    },
    # Map-related endpoints
    "listSiteMaps": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "type", "created_time", "modified_time"],
        "unique_constraints": [],
        "description": "Site maps with stable UUID identifiers",
    },
    "getSiteMap": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "type"],
        "unique_constraints": [],
        "description": "Individual site map with stable UUID identifier",
    },
    "listSiteMapStacks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "created_time", "modified_time"],
        "unique_constraints": [],
        "description": "Site map stacks (multi-floor groupings)",
    },
    # Zone and RSSI zone endpoints
    "listSiteZones": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "map_id", "name"],
        "unique_constraints": [],
        "description": "Zones defined on site maps",
    },
    "listSiteZonesStats": {
        "type": "composite_pk",
        "primary_key": ["id", "map_id"],
        "indexes": ["site_id", "map_id", "name", "num_clients"],
        "unique_constraints": [],
        "description": "Zone statistics with client counts",
    },
    "listSiteRssiZones": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name"],
        "unique_constraints": [],
        "description": "RSSI-based zones for location analytics",
    },
    "listSiteRssiZonesStats": {
        "type": "composite_pk",
        "primary_key": ["id", "map_id"],
        "indexes": ["site_id", "map_id", "name"],
        "unique_constraints": [],
        "description": "RSSI zone statistics",
    },
    # Beacon endpoints
    "listSiteBeacons": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "map_id", "name", "type"],
        "unique_constraints": [],
        "description": "BLE beacons deployed on site maps",
    },
    "listSiteVBeacons": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "map_id", "name"],
        "unique_constraints": [],
        "description": "Virtual BLE beacons on site maps",
    },
    # Zone session search
    "searchSiteZoneSessions": {
        "type": "composite_pk",
        "primary_key": ["zone_id", "mac", "enter"],
        "indexes": ["site_id", "map_id", "zone_id", "mac", "enter", "exit"],
        "unique_constraints": [],
        "description": "Client zone session events for location analytics",
    },
    # -- Issue #174: Site events & alarms --
    "searchSiteAlarms": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["site_id", "type", "severity"],
        "unique_constraints": [],
        "description": "Site alarm search results",
    },
    "searchSiteDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["site_id", "device_type", "type", "mac"],
        "unique_constraints": [],
        "description": "Site device event search results",
    },
    "searchSiteSystemEvents": {
        "type": "composite_pk",
        "primary_key": ["type", "timestamp"],
        "indexes": ["site_id", "type"],
        "unique_constraints": [],
        "description": "Site system event search results",
    },
    "searchSiteOtherDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["site_id", "mac", "type"],
        "unique_constraints": [],
        "description": "Site other device event search results",
    },
    "searchSiteSkyatpEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["site_id", "mac", "type"],
        "unique_constraints": [],
        "description": "Site Sky ATP event search results",
    },
    "searchSiteServicePathEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["site_id", "mac", "type", "vpn_name"],
        "unique_constraints": [],
        "description": "Site WAN service path event search results",
    },
    "listSiteRoamingEvents": {
        "type": "composite_pk",
        "primary_key": ["client_mac", "timestamp"],
        "indexes": ["site_id", "client_mac", "ap"],
        "unique_constraints": [],
        "description": "Site client roaming events",
    },
    "listSiteRrmEvents": {
        "type": "composite_pk",
        "primary_key": ["ap_id", "timestamp"],
        "indexes": ["site_id", "ap_id", "band"],
        "unique_constraints": [],
        "description": "Site radio resource management events",
    },
    "listSiteAnomalyEvents": {
        "type": "composite_pk",
        "primary_key": ["timestamp"],
        "indexes": ["site_id", "metric"],
        "unique_constraints": [],
        "description": "Site anomaly detection events",
    },
    # Type 3b: Config history, synthetic tests, webhook deliveries, packet captures
    "searchSiteDeviceConfigHistory": {
        "type": "composite_pk",
        "primary_key": ["timestamp"],
        "indexes": ["site_id", "version", "channel_24", "channel_5"],
        "unique_constraints": [],
        "description": "Site device config change history",
    },
    "searchSiteDeviceLastConfigs": {
        "type": "composite_pk",
        "primary_key": ["timestamp"],
        "indexes": ["site_id", "version", "channel_24", "channel_5"],
        "unique_constraints": [],
        "description": "Site device last known configurations",
    },
    "searchSiteSyntheticTest": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["site_id", "mac", "type", "status", "port_id"],
        "unique_constraints": [],
        "description": "Site synthetic test results",
    },
    "searchSiteWebhooksDeliveries": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["site_id", "org_id", "webhook_id", "status", "topic"],
        "unique_constraints": [],
        "description": "Site webhook delivery audit records",
    },
    "listSitePacketCaptures": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "type", "timestamp"],
        "unique_constraints": [],
        "description": "Site packet capture metadata",
    },
    # Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies
    "listSiteWlans": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "ssid", "template_id"],
        "unique_constraints": [],
        "description": "Site-level WLAN configurations",
    },
    "listSitePsks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "ssid", "name"],
        "unique_constraints": [],
        "description": "Site-level pre-shared key configurations",
    },
    "listSiteWebhooks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Site-level webhook configurations",
    },
    "listSiteWxRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "order"],
        "unique_constraints": [],
        "description": "Site-level WxLAN rules",
    },
    "listSiteWxTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Site-level WxLAN tags",
    },
    "listSiteWxTunnels": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "name"],
        "unique_constraints": [],
        "description": "Site-level WxLAN tunnel configurations",
    },
    # Issue #172: Site-level client search endpoints
    "searchSiteWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "ssid", "ap"],
        "unique_constraints": [],
        "description": "Site-level wireless client search results",
    },
    "searchSiteWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_mac"],
        "unique_constraints": [],
        "description": "Site-level wired client search results",
    },
    "searchSiteWanClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "hostname"],
        "unique_constraints": [],
        "description": "Site-level WAN client search results",
    },
    "searchSiteNacClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id"],
        "unique_constraints": [],
        "description": "Site-level NAC client search results",
    },
    "searchSiteNacClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["site_id", "type", "nacrule_id"],
        "unique_constraints": [],
        "description": "Site-level NAC client event search results",
    },
    "searchSiteWirelessClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["site_id", "type", "ap", "ssid"],
        "unique_constraints": [],
        "description": "Site-level wireless client event search results",
    },
    "searchSiteWirelessClientSessions": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["site_id", "ap", "ssid", "wlan_id"],
        "unique_constraints": [],
        "description": "Site-level wireless client session search results",
    },
    "searchSiteWanClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["site_id", "ev_type", "wcid"],
        "unique_constraints": [],
        "description": "Site-level WAN client event search results",
    },
    "listSiteUnconnectedClientStats": {
        "type": "composite_pk",
        "primary_key": ["mac", "map_id"],
        "indexes": ["mac", "map_id", "ap_mac"],
        "unique_constraints": [],
        "description": "Unconnected client statistics per map",
    },
    # Issue #171: Site-level device endpoints
    "searchSiteDevices": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "model", "type"],
        "unique_constraints": [],
        "description": "Site-level device search results",
    },
    "listSiteOtherDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "device_mac", "vendor", "model"],
        "unique_constraints": [],
        "description": "Non-Juniper devices discovered at site",
    },
    "listSiteAvailableDeviceVersions": {
        "type": "composite_pk",
        "primary_key": ["model", "version"],
        "indexes": ["model", "tag"],
        "unique_constraints": [],
        "description": "Available firmware versions per device model",
    },
    "listSiteSpectrumAnalysis": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "band"],
        "unique_constraints": [],
        "description": "RF spectrum analysis data from AP radios",
    },
    "listSiteDeviceRadioChannels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["key", "name", "code"],
        "unique_constraints": [],
        "description": "AP radio channel configuration per country",
    },
    "listSiteDeviceUpgrades": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["status", "target_version", "strategy"],
        "unique_constraints": [],
        "description": "Device firmware upgrade status and progress",
    },
    # Issue #184: Derived config endpoints (effective merged config at site)
    "listSiteWlansDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "ssid", "template_id"],
        "unique_constraints": [],
        "description": "Effective WLAN config after template inheritance",
    },
    "listSiteNetworksDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name", "vlan_id"],
        "unique_constraints": [],
        "description": "Effective network config after template inheritance",
    },
    "listSiteVpnsDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective VPN config after template inheritance",
    },
    "listSiteServicesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name", "type"],
        "unique_constraints": [],
        "description": "Effective service definitions after template inheritance",
    },
    "listSiteServicePoliciesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective service policies after template inheritance",
    },
    "listSiteUiSettingDerived": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "Effective UI settings (object response, no array key)",
    },
    "listSiteAllGuestAuthorizationsDerived": {
        "type": "natural_pk",
        "primary_key": ["mac"],
        "indexes": ["site_id", "ssid", "wlan_id", "authorized"],
        "unique_constraints": [],
        "description": "Effective guest authorizations after template inheritance",
    },
    "listSiteApTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective AP template config after inheritance",
    },
    "listSiteRfTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective RF template config after inheritance",
    },
    "listSiteNetworkTemplatesDerived": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "Effective network template (object response, no array key)",
    },
    "listSiteGatewayTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective gateway template config after inheritance",
    },
    "listSiteSiteTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective site template config after inheritance",
    },
    "listSiteDeviceProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name", "type"],
        "unique_constraints": [],
        "description": "Effective device profiles after template inheritance",
    },
    "listSiteIdpProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective IDP profiles after template inheritance",
    },
    "listSiteAAMWProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective AAMW profiles after template inheritance",
    },
    "listSiteAntivirusProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Effective antivirus profiles after template inheritance",
    },
    "listSiteSecIntelProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "Effective SecIntel profiles after template inheritance",
    },
    # Type 4: Client search APIs (special handling for large datasets)
    "searchOrgWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "ssid"],
        "unique_constraints": [],
        "description": "Wireless client data with composite key for time-series",
    },
    "searchOrgWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "port_id"],
        "unique_constraints": [],
        "description": "Wired client data with composite key for time-series",
    },
    "globalWiredClientReport": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "manufacture"],
        "unique_constraints": [],
        "description": "Global wired client report with operator-based filtering",
    },
    "wiredClientManufacturerReport": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "manufacture"],
        "unique_constraints": [],
        "description": "Wired client report filtered by manufacturer selection",
    },
    # Type 5: License and summary APIs (often aggregated data)
    "getOrgLicensesSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "sku", "type"],
        "unique_constraints": [],
        "description": "License summary data (aggregated, no stable primary key)",
    },
    "getOrgLicenseAsyncClaimStatus": {  # Register composite key strategy for claim-status summary snapshots.
        "type": "composite_pk",  # Use composite primary key because org_id + scheduled_at uniquely identifies one job.
        "primary_key": ["org_id", "scheduled_at"],  # Keep one row per org/job across repeated polls.
        "indexes": ["status"],  # Index status to accelerate prepared/ongoing/done filtering.
        "unique_constraints": [],  # Composite PK already enforces uniqueness without extra constraints.
        "table": "org_claim_status_summary",  # Persist summary rows to explicit SQLite table name.
        "description": "Async org claim job summary keyed by org and scheduled timestamp",  # Document storage intent.
    },
    "getOrgLicenseAsyncClaimStatusDetails": {  # Register detail-row strategy for per-device claim status records.
        "type": "composite_pk",  # Use composite key to avoid duplicate device rows per job.
        "primary_key": ["org_id", "scheduled_at", "mac"],  # Scope device status by org + job + device MAC.
        "indexes": ["mac"],  # Index MAC for fast per-device lookup queries.
        "unique_constraints": [],  # Composite PK provides uniqueness guarantee.
        "table": "org_claim_status_details",  # Persist detail rows to dedicated detail table.
        "description": "Async org claim detail rows keyed by org/job/mac",  # Describe per-device table purpose.
    },
    "listOrgLicenses": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "sku", "type"],
        "unique_constraints": [],
        "description": "License records from canonical list endpoint",
    },
    # Site Inventory Health Analysis reports
    "sitesMissingInfrastructure": {
        "type": "natural_pk",
        "primary_key": ["site_id"],
        "indexes": ["site_name", "missing_types", "ap_count"],
        "unique_constraints": [],
        "description": "Sites with APs but missing switches or gateways",
    },
    "sitesWithOfflineInfrastructure": {
        "type": "natural_pk",
        "primary_key": ["site_id"],
        "indexes": ["site_name", "offline_switches", "offline_gateways"],
        "unique_constraints": [],
        "description": "Sites with APs where switches or gateways are offline",
    },
    # E911 BSSID compliance report (derived data, one row per BSSID)
    "generateE911BSSIDReport": {
        "type": "natural_pk",
        "primary_key": ["bssid"],
        "indexes": ["site_name", "ap_name", "map_name"],
        "unique_constraints": [],
        "description": "E911 BSSID compliance report - one row per BSSID with location context",
    },
    # Default fallback strategy for unclassified endpoints
    # Uses auto-increment with unique constraint on API id field if present
    # Device Utility Commands - Diagnostic/Show command results (menus 123-157)
    "tracerouteFromDevice": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id", "command"],
        "unique_constraints": [],
        "description": "Traceroute results from device utility command",
    },
    "showSiteGatewayOspfNeighbors": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "OSPF neighbor table from gateway",
    },
    "showSiteGatewayOspfInterfaces": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "OSPF interface table from gateway",
    },
    "showSiteGatewayOspfDatabase": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "OSPF database from gateway",
    },
    "showSiteGatewayOspfSummary": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "OSPF summary from gateway",
    },
    "showSiteSsrAndSrxSessions": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "SSR/SRX session table",
    },
    "showSiteSsrServicePath": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "SSR service path table",
    },
    "showSiteDeviceBgpSummary": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "BGP summary table",
    },
    "showSiteDeviceArpTable": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "ARP table from device",
    },
    "showSiteDeviceDhcpLeases": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "DHCP lease table",
    },
    "showSiteDeviceDot1xTable": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "802.1X authentication table from switch",
    },
    "showSiteDeviceEvpnDatabase": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "EVPN database entries",
    },
    "testSiteSsrDnsResolution": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "DNS resolution test results from SSR",
    },
    "cableTestFromSwitch": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Cable test results from switch port",
    },
    # SSID Template Consolidation (Menu 159) strategies
    "ssidConsolidationMatrix": {
        "type": "composite_pk",
        "primary_key": ["site_id", "ssid_id"],
        "indexes": ["site_name", "template_id", "mxtunnel_id", "target_group"],
        "unique_constraints": [],
        "description": "SSID consolidation matrix - one row per site per target SSID",
    },
    "ssidConsolidationDeviation": {
        "type": "composite_pk",
        "primary_key": ["cluster_id", "parameter"],
        "indexes": ["cluster_name"],
        "unique_constraints": [],
        "description": "SSID parameter deviations within cluster groups",
    },
    "ssidConsolidationSiteVars": {
        "type": "composite_pk",
        "primary_key": ["site_id", "variable_name"],
        "indexes": ["site_name", "status"],
        "unique_constraints": [],
        "description": "Site variable assignments for SSID consolidation",
    },
    "ssidConsolidationSiteGroups": {
        "type": "composite_pk",
        "primary_key": ["site_id", "group_id"],
        "indexes": ["group_name", "status"],
        "unique_constraints": [],
        "description": "Site group assignments for SSID consolidation",
    },
    "ssidConsolidationTemplates": {
        "type": "composite_pk",
        "primary_key": ["template_id", "ssid_name"],
        "indexes": ["template_name", "group_name", "status"],
        "unique_constraints": [],
        "description": "Consolidated template creation results",
    },
    "ssidConsolidationDisable": {
        "type": "composite_pk",
        "primary_key": ["site_id", "ssid_id"],
        "indexes": ["old_template_id", "status"],
        "unique_constraints": [],
        "description": "Old SSID disable results for SSID consolidation",
    },
    # ========================================================================
    # ORG DATA COLLECTOR -- bulk collection endpoints (menu 165)
    # ========================================================================
    # -- Security Profiles (natural_pk) --------------------------------------
    "listOrgAAMWProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization Advanced Anti-Malware profiles",
    },
    "listOrgAntivirusProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization antivirus profiles",
    },
    "listOrgIdpProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization IDP profiles",
    },
    # -- Network & VPN (natural_pk) ------------------------------------------
    "listOrgVpns": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization VPN configurations",
    },
    "listOrgEvpnTopologies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization EVPN topology configurations",
    },
    "listOrgWxTunnels": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization WxLAN tunnel configurations",
    },
    # -- Wireless Policy (natural_pk) ----------------------------------------
    "listOrgWxRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "order"],
        "unique_constraints": [],
        "description": "Organization WxLAN rules",
    },
    "listOrgWxTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization WxLAN tags",
    },
    # -- Edge Infrastructure -------------------------------------------------
    "listOrgMxEdgeClusters": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization MxEdge cluster configurations",
    },
    "listOrgMxEdgeUpgrades": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "mxedge_id", "status"],
        "unique_constraints": [],
        "description": "MxEdge firmware upgrade records",
    },
    # -- Device Management ---------------------------------------------------
    "listOrgDeviceUpgrades": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "site_id", "status"],
        "unique_constraints": [],
        "description": "Device firmware upgrade records",
    },
    "listOrgOtherDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "mac", "vendor"],
        "unique_constraints": [],
        "description": "Non-Juniper devices tracked by the organization",
    },
    # -- Assets & Inventory --------------------------------------------------
    "listOrgAssets": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "mac", "site_id"],
        "unique_constraints": [],
        "description": "Organization BLE asset definitions",
    },
    "listOrgAssetFilters": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization asset filter rules",
    },
    "listOrgAssetsStats": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Organization BLE asset statistics",
    },
    # -- JSI (Juniper Support Insights) --------------------------------------
    "listOrgJsiDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "serial", "mac"],
        "unique_constraints": [],
        "description": "JSI-tracked device inventory",
    },
    "listOrgJsiPastPurchases": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "JSI historical purchase records",
    },
    # -- Access & Auth -------------------------------------------------------
    "listOrgCertificates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization TLS/SSL certificates",
    },
    "listOrgSsoRoles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization SSO role mappings",
    },
    "listOrgSsoLatestFailures": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "timestamp"],
        "unique_constraints": [],
        "description": "Latest SSO authentication failures",
    },
    "listOrgIssuedClientCertificates": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Client certificates issued by the organization",
    },
    "listOrgNacPortalSsoLatestFailures": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "timestamp"],
        "unique_constraints": [],
        "description": "NAC portal SSO authentication failures",
    },
    "listOrgGuestAuthorizations": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac"],
        "unique_constraints": [],
        "description": "Guest network authorization records",
    },
    "listSiteAllGuestAuthorizations": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "wlan_id", "ap_mac"],
        "unique_constraints": [],
        "description": "Site-level guest WiFi authorization records",
    },
    # -- Site Rogues (insight-based, no API id field) -------------------------
    "listSiteRogueAPs": {
        "type": "composite_pk",
        "primary_key": ["bssid", "ap_mac"],
        "indexes": ["site_id", "ssid", "channel"],
        "unique_constraints": [],
        "description": "Rogue APs detected at a site via RF scanning",
    },
    "listSiteRogueClients": {
        "type": "composite_pk",
        "primary_key": ["client_mac", "bssid"],
        "indexes": ["site_id", "ap_mac", "band"],
        "unique_constraints": [],
        "description": "Rogue clients detected at a site via RF scanning",
    },
    # -- PSK Portals ---------------------------------------------------------
    "listOrgPskPortals": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization PSK portal configurations",
    },
    "listOrgPskPortalLogs": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "psk_portal_id"],
        "unique_constraints": [],
        "description": "PSK portal access log entries",
    },
    # -- SDK & Invites -------------------------------------------------------
    "listSdkInvites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "SDK invite records",
    },
    "listSdkTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "SDK template definitions",
    },
    "listOrgMarvisClientInvites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Marvis client invite records",
    },
    # -- Alarms & Tickets ----------------------------------------------------
    "listOrgSuppressedAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Suppressed alarm rules",
    },
    "listOrgTickets": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "status", "type"],
        "unique_constraints": [],
        "description": "Organization support tickets",
    },
    "getOrgTicket": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "status", "type"],
        "unique_constraints": [],
        "description": "Organization support ticket detail with comments",
    },
    # -- Dashboards & UI -----------------------------------------------------
    "listOrgPmaDashboards": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "PMA dashboard configurations",
    },
    "listOrgUiSettings": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization UI preference settings",
    },
    # -- Search Endpoints (composite_pk for time-series/event data) ----------
    "searchOrgDevices": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "model", "type", "hostname"],
        "unique_constraints": [],
        "description": "Organization device search results",
    },
    "searchOrgDeviceLastConfigs": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Last pushed device configurations",
    },
    "searchOrgInventory": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "serial", "model", "type"],
        "unique_constraints": [],
        "description": "Organization inventory search results",
    },
    "searchOrgWirelessClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "type", "ap"],
        "unique_constraints": [],
        "description": "Wireless client event search results",
    },
    "searchOrgWirelessClientSessions": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "ap", "ssid"],
        "unique_constraints": [],
        "description": "Wireless client session search results",
    },
    "searchOrgWanClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "WAN client event search results",
    },
    "searchOrgWanClients": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "hostname"],
        "unique_constraints": [],
        "description": "WAN client search results",
    },
    "searchOrgMistEdgeEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mxedge_id", "timestamp"],
        "indexes": ["org_id", "type"],
        "unique_constraints": [],
        "description": "MistEdge event search results",
    },
    "searchOrgOtherDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "Other device event search results",
    },
    "searchOrgMxEdges": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "name", "model"],
        "unique_constraints": [],
        "description": "MxEdge search results",
    },
    "searchOrgSites": {
        "type": "composite_pk",
        "primary_key": ["id", "name"],
        "indexes": ["org_id", "country_code"],
        "unique_constraints": [],
        "description": "Organization site search results",
    },
    "searchOrgOspfStats": {
        "type": "composite_pk",
        "primary_key": ["device_id", "neighbor", "timestamp"],
        "indexes": ["org_id", "site_id", "state"],
        "unique_constraints": [],
        "description": "OSPF neighbor statistics search results",
    },
    "searchOrgUserMacs": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization user MAC address search results",
    },
    "searchOrgPskPortalLogs": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "psk_portal_id"],
        "unique_constraints": [],
        "description": "PSK portal log search results",
    },
    "searchOrgJsiAssetsAndContracts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "serial"],
        "unique_constraints": [],
        "description": "JSI assets and contract search results",
    },
    "searchOrgJsiPbn": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "JSI PBN search results",
    },
    "searchOrgJsiSirt": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "JSI SIRT search results",
    },
    "searchOrgVars": {
        "type": "composite_pk",
        "primary_key": ["site_id", "name"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization variable search results",
    },
    "searchOrgWebhooksDeliveries": {
        "type": "composite_pk",
        "primary_key": ["id", "webhook_id", "timestamp"],
        "indexes": ["org_id", "status_code"],
        "unique_constraints": [],
        "description": "Webhook delivery search results",
    },
    # -- GET Endpoints (org-level summaries) ---------------------------------
    "getOrgSettings": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization settings snapshot",
    },
    "getOrgStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization-level statistics snapshot",
    },
    "getOrgApplicationList": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization application definitions",
    },
    # -- Count Endpoints (aggregated counts → auto_increment) ------------------
    "countOrgAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Organization alarm count aggregates",
    },
    "countOrgAssetsByDistanceField": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Asset count by distance field aggregates",
    },
    "countOrgAuditLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Audit log count aggregates",
    },
    "countOrgBgpStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "BGP statistics count aggregates",
    },
    "countOrgDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Device event count aggregates",
    },
    "countOrgDeviceLastConfigs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Device last config count aggregates",
    },
    "countOrgDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Device count aggregates",
    },
    "orgDeviceModelSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "device_type", "model"],
        "unique_constraints": [],
        "description": "Device count by model across all device types (menu 187)",
    },
    "orgDeviceFirmwareSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "device_type", "version"],
        "unique_constraints": [],
        "description": "Device count by firmware version and device type (menu 187)",
    },
    "orgDeviceVersionPerModel": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "device_type", "model", "version"],
        "unique_constraints": [],
        "description": "Device count by firmware version broken down per model (menu 187)",
    },
    "countOrgGuestAuthorizations": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Guest authorization count aggregates",
    },
    "countOrgInventory": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Inventory count aggregates",
    },
    "countOrgJsiAssetsAndContracts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "JSI assets and contracts count aggregates",
    },
    "countOrgJsiPbn": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "JSI PBN count aggregates",
    },
    "countOrgJsiSirt": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "JSI SIRT count aggregates",
    },
    "countOrgMxEdges": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "MxEdge count aggregates",
    },
    "countOrgNacClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "NAC client event count aggregates",
    },
    "countOrgNacClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "NAC client count aggregates",
    },
    "countOrgOspfStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "OSPF statistics count aggregates",
    },
    "countOrgOtherDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Other device event count aggregates",
    },
    "countOrgPeerPathStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Peer path statistics count aggregates",
    },
    "countOrgPskPortalLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "PSK portal log count aggregates",
    },
    "countOrgSiteMxEdgeEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Site MxEdge event count aggregates",
    },
    "countOrgSites": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Site count aggregates",
    },
    "countOrgSwOrGwPorts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Switch/gateway port count aggregates",
    },
    "countOrgSystemEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "System event count aggregates",
    },
    "countOrgTickets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Ticket count aggregates",
    },
    "createOrgTicket": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "status", "type"],
        "unique_constraints": [],
        "description": "Newly created organization support ticket",
    },
    "updateOrgTicket": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "status", "type"],
        "unique_constraints": [],
        "description": "Updated organization support ticket",
    },
    "addOrgTicketComment": {
        "type": "composite_pk",
        "primary_key": ["ticket_id", "created_at"],
        "indexes": ["ticket_id", "author"],
        "unique_constraints": [],
        "description": "Comment added to an organization support ticket",
    },
    "countOrgTunnelsStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Tunnel statistics count aggregates",
    },
    "countOrgUserMacs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "User MAC address count aggregates",
    },
    "countOrgWanClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "WAN client count aggregates",
    },
    "countOrgWiredClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Wired client count aggregates",
    },
    "countOrgWirelessClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Wireless client event count aggregates",
    },
    "countOrgWirelessClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Wireless client count aggregates",
    },
    "countOrgWirelessClientsSessions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "distinct"],
        "unique_constraints": [],
        "description": "Wireless client session count aggregates",
    },
    # -- GET Endpoints (additional org-level data) ---------------------------
    "getOrg": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization details snapshot",
    },
    "getOrgCapturingStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization packet capture status",
    },
    "getOrgLicensesBySite": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "License allocation by site",
    },
    # -- LIST Endpoints (additional org-level entities) ----------------------
    "listOrgAdmins": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "email"],
        "unique_constraints": [],
        "description": "Organization administrator accounts",
    },
    "listOrgAlarmTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization alarm template configurations",
    },
    "listOrgApiTokens": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization API token records",
    },
    "listOrgApsMacs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "mac"],
        "unique_constraints": [],
        "description": "Organization AP MAC address list",
    },
    "listOrgAuditLogs": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "admin_name", "message"],
        "unique_constraints": [],
        "description": "Organization audit log entries",
    },
    "listOrgAvailableDeviceVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "model", "version"],
        "unique_constraints": [],
        "description": "Available firmware versions for org devices",
    },
    "listOrgAvailableSsrVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "version"],
        "unique_constraints": [],
        "description": "Available SSR firmware versions",
    },
    "listOrgDeviceProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Organization device profile configurations",
    },
    "listOrgDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac", "serial", "model"],
        "unique_constraints": [],
        "description": "Organization devices list",
    },
    "listOrgDevicesSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Organization device summary statistics",
    },
    "listOrgMxEdges": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "model"],
        "unique_constraints": [],
        "description": "Organization MxEdge appliances",
    },
    "listOrgMxEdgesStats": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "name", "model"],
        "unique_constraints": [],
        "description": "Organization MxEdge statistics",
    },
    "listOrgMxTunnels": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization Mist tunnel configurations",
    },
    "listOrgNacPortals": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization NAC portal configurations",
    },
    "listOrgNacRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "order"],
        "unique_constraints": [],
        "description": "Organization NAC rules",
    },
    "listOrgNacTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Organization NAC tags",
    },
    "listOrgNetworks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization network definitions",
    },
    "listOrgPacketCaptures": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "Organization packet capture records",
    },
    "listOrgSecIntelProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization security intelligence profiles",
    },
    "listOrgServicePolicies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization service policy configurations",
    },
    "listOrgServices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Organization service definitions",
    },
    "listOrgSiteGroups": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization site group configurations",
    },
    "listOrgSiteStats": {
        "type": "composite_pk",
        "primary_key": ["id", "name"],
        "indexes": ["org_id", "country_code"],
        "unique_constraints": [],
        "description": "Organization site statistics",
    },
    "listOrgSsos": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization SSO configurations",
    },
    "listOrgSsrUpgrades": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "device_id", "status"],
        "unique_constraints": [],
        "description": "SSR firmware upgrade records",
    },
    "listOrgTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Organization WLAN template configurations",
    },
    "listOrgWlans": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "ssid"],
        "unique_constraints": [],
        "description": "Organization WLAN configurations",
    },
    # -- SEARCH Endpoints (additional) --------------------------------------
    "searchOrgAssets": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id", "name"],
        "unique_constraints": [],
        "description": "Organization asset search results",
    },
    "searchOrgBgpStats": {
        "type": "composite_pk",
        "primary_key": ["device_id", "neighbor", "timestamp"],
        "indexes": ["org_id", "site_id", "state"],
        "unique_constraints": [],
        "description": "BGP neighbor statistics search results",
    },
    "searchOrgEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "Organization event search results",
    },
    "searchOrgGuestAuthorization": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "Guest authorization search results",
    },
    "searchSiteGuestAuthorization": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["site_id", "wlan_id", "ap_mac"],
        "unique_constraints": [],
        "description": "Site-level guest authorization search results",
    },
    "searchSiteRogueEvents": {
        "type": "composite_pk",
        "primary_key": ["bssid", "timestamp"],
        "indexes": ["site_id", "ap", "ssid"],
        "unique_constraints": [],
        "description": "Rogue AP/client event search results",
    },
    # -- Site MxEdge endpoints (issue #178) --
    "listSiteMxEdges": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "mxcluster_id"],
        "unique_constraints": [],
        "description": "Site MxEdge appliances",
    },
    "listSiteMxEdgesStats": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["site_id", "name", "status"],
        "unique_constraints": [],
        "description": "Site MxEdge statistics",
    },
    "searchSiteMistEdgeEvents": {
        "type": "composite_pk",
        "primary_key": ["mxedge_id", "timestamp"],
        "indexes": ["site_id", "mac", "type"],
        "unique_constraints": [],
        "description": "Site MxEdge event search results",
    },
    # -- Site Asset endpoints (issue #176) --
    "listSiteAssets": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "map_id", "name"],
        "unique_constraints": [],
        "description": "Site BLE asset definitions",
    },
    "searchSiteAssets": {
        "type": "composite_pk",
        "primary_key": ["mac", "map_id"],
        "indexes": ["site_id", "name", "device_name"],
        "unique_constraints": [],
        "description": "Site asset search results",
    },
    "listSiteAssetsStats": {
        "type": "composite_pk",
        "primary_key": ["mac", "map_id"],
        "indexes": ["site_id", "name", "device_name"],
        "unique_constraints": [],
        "description": "Site BLE asset statistics",
    },
    "listSiteDiscoveredAssets": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "map_id", "name"],
        "unique_constraints": [],
        "description": "Site discovered BLE assets",
    },
    "listSiteAssetFilters": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "ap_mac"],
        "unique_constraints": [],
        "description": "Site asset filter rules",
    },
    # -- Site Applications, Calls, WAN Usage & Fingerprints (issue #183) --
    "listSiteApps": {
        "type": "composite_pk",
        "primary_key": ["key", "group"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "Site application visibility",
    },
    "searchSiteCalls": {
        "type": "composite_pk",
        "primary_key": ["mac", "start_time"],
        "indexes": ["app", "meeting_id", "site_id", "rating"],
        "unique_constraints": [],
        "description": "Site call quality records",
    },
    "searchSiteWanUsage": {
        "type": "composite_pk",
        "primary_key": ["mac", "port_id", "peer_mac"],
        "indexes": ["policy", "tenant", "path_type"],
        "unique_constraints": [],
        "description": "Site WAN link usage",
    },
    "searchOrgClientFingerprints": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["site_id", "os_type", "mfg", "family"],
        "unique_constraints": [],
        "description": "Client NAC fingerprints",
    },
    "listSiteUiSettings": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "org_id", "name", "purpose"],
        "unique_constraints": [],
        "description": "Site UI dashboard settings",
    },
    "listSiteTroubleshootCalls": {
        "type": "composite_pk",
        "primary_key": ["meeting_id", "mac"],
        "indexes": ["site_id", "app"],
        "unique_constraints": [],
        "description": "Site call troubleshooting diagnostics",
    },
    # -- Issue #185: SLE impacted entity endpoints --
    "listSiteSlesMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "SLE metric availability per site scope",
    },
    "listSiteSleMetricClassifiers": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "SLE metric classifier breakdown",
    },
    "listSiteSleImpactedAps": {
        "type": "composite_pk",
        "primary_key": ["ap_mac", "metric", "classifier"],
        "indexes": ["name", "failure"],
        "unique_constraints": [],
        "description": "APs impacted by SLE metric degradation",
    },
    "listSiteSleImpactedSwitches": {
        "type": "composite_pk",
        "primary_key": ["switch_mac", "metric", "classifier"],
        "indexes": ["name", "failure"],
        "unique_constraints": [],
        "description": "Switches impacted by SLE metric degradation",
    },
    "listSiteSleImpactedGateways": {
        "type": "composite_pk",
        "primary_key": ["gateway_mac", "metric", "classifier"],
        "indexes": ["name", "failure"],
        "unique_constraints": [],
        "description": "Gateways impacted by SLE metric degradation",
    },
    "listSiteSleImpactedInterfaces": {
        "type": "composite_pk",
        "primary_key": ["switch_mac", "interface_name", "metric", "classifier"],
        "indexes": ["switch_name", "failure"],
        "unique_constraints": [],
        "description": "Switch interfaces impacted by SLE metric degradation",
    },
    "listSiteSleImpactedChassis": {
        "type": "composite_pk",
        "primary_key": ["switch_mac", "chassis", "metric", "classifier"],
        "indexes": ["role", "failure"],
        "unique_constraints": [],
        "description": "Switch chassis impacted by SLE metric degradation",
    },
    "listSiteSleImpactedWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "metric", "classifier"],
        "indexes": ["name", "failure", "ssid"],
        "unique_constraints": [],
        "description": "Wireless clients impacted by SLE metric degradation",
    },
    "listSiteSleImpactedWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "metric", "classifier"],
        "indexes": ["name", "failure"],
        "unique_constraints": [],
        "description": "Wired clients impacted by SLE metric degradation",
    },
    "listSiteSleImpactedApplications": {
        "type": "composite_pk",
        "primary_key": ["app", "metric", "classifier"],
        "indexes": ["name", "failure"],
        "unique_constraints": [],
        "description": "Applications impacted by SLE metric degradation",
    },
    "searchOrgNacClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "mac", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "NAC client event search results",
    },
    "searchOrgNacClients": {
        "type": "composite_pk",
        "primary_key": ["id", "mac"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "NAC client search results",
    },
    "searchOrgTunnelsStats": {
        "type": "composite_pk",
        "primary_key": ["id", "device_id", "timestamp"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "Tunnel statistics search results",
    },
    # -- New operations for complete SDK coverage ----------------------------
    "getOrgJseInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "JSE integration info",
    },
    "getOrgJseIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "JSE integration details",
    },
    "getOrgSkyAtpIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Sky ATP integration",
    },
    "getOrgZscalerIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Zscaler integration",
    },
    "getOrgMistScep": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Mist SCEP configuration",
    },
    "getOrgNacCrl": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "NAC CRL configuration",
    },
    "getOrgCrlFile": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "CRL file",
    },
    "getOrgSslProxyCert": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "SSL proxy certificate",
    },
    "getOrgAosRegisterCmd": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "AOS register command",
    },
    "getOrgSsrRegistrationCommands": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "SSR registration commands",
    },
    "getOrgMxEdgeUpgradeInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "MxEdge upgrade info",
    },
    "getOrgSitesSle": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "Sites SLE metrics",
    },
    "countOrgWanClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "WAN client events count",
    },
    # Default fallback strategy for unclassified endpoints
    # Uses auto-increment with unique constraint on API id field if present
    "default": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],  # Will be determined at runtime based on available fields
        "unique_constraints": [],  # Will be applied if 'id' field exists in data
        "description": "Fallback strategy with auto-increment primary key and unique constraint on API id",
    },
    "getOrgE911Report": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id"],
        "unique_constraints": [],
        "description": "E911 report data for the organization",
    },
    "listSiteMxEdgeUpgrades": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "status"],
        "unique_constraints": [],
        "description": "MxEdge upgrade status records for a site",
    },
    "getSiteAutoMapAssignmentStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Auto-map assignment status for a site",
    },
    "getSitesByAPModel": {
        "type": "natural_pk",
        "primary_key": ["site_id"],
        "indexes": ["org_id", "site_name", "ap_model", "ap_count"],
        "unique_constraints": [],
        "description": "Sites filtered by AP model with site address and AP count",
    },
    # ==============================
    # NET-NEW ENTRIES FROM PROBE RUN 3
    # 15 natural_pk + 3 composite_pk + key auto_increment reference endpoints
    # Added in version 26.05 to align EPKS with all reachable mistapi endpoints
    # ==============================
    # --- natural_pk (single-entity GET endpoints with stable UUID key) ---
    "getSiteInfo": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "country_code"],
        "unique_constraints": [],
        "description": "Full configuration snapshot for a single site",
    },
    "getSiteDevice": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "model", "type"],
        "unique_constraints": [],
        "description": "Single device configuration (AP, switch, or gateway) at a site",
    },
    "getSiteDeviceStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "type"],
        "unique_constraints": [],
        "description": "Runtime statistics for a single device at a site",
    },
    "getSiteDeviceVirtualChassis": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Virtual chassis topology for a single switch at a site",
    },
    "getOrgMxEdge": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Configuration for a single MxEdge appliance in the org",
    },
    "getOrgMxEdgeStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Runtime statistics for a single MxEdge appliance in the org",
    },
    "getOrgWebhook": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "url"],
        "unique_constraints": [],
        "description": "Configuration for a single webhook endpoint in the org",
    },
    "getSiteAssetsOfInterest": {
        "type": "natural_pk",
        "primary_key": ["mac"],
        "indexes": ["site_id", "name"],
        "unique_constraints": [],
        "description": "Tracked BLE/WiFi assets flagged as assets of interest at a site",
    },
    "getSiteSetting": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Full settings object for a single site (single-row result)",
    },
    "getSiteSettingDerived": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Derived (merged org + site) settings for a single site",
    },
    "getSiteWxRulesUsage": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "WxLAN rule usage statistics for a site (aggregate, no stable key)",
    },
    "ListSiteWxRulesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "WxLAN rules with org-level inheritance resolved for a site",
    },
    "getSiteSiteRfdiagRecording": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "RF diagnostics recording for a site",
    },
    "listSiteBeaconsStats": {
        "type": "composite_pk",
        "primary_key": ["id", "site_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "BLE beacon statistics per site (composite key: beacon id + site)",
    },
    # --- composite_pk (no single stable UUID; identity is multi-field) ---
    "getSiteCurrentChannelPlanning": {
        "type": "composite_pk",
        "primary_key": ["ap", "band"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Current RRM channel and power plan per AP radio at a site",
    },
    "listNacEventsDefinitions": {
        "type": "composite_pk",
        "primary_key": ["key"],
        "indexes": [],
        "unique_constraints": [],
        "description": "NAC event type definitions and descriptions (reference data)",
    },
    "listSelfAuditLogs": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": [],
        "unique_constraints": [],
        "description": "Audit log of changes made by the authenticated admin account",
    },
    # --- auto_increment_with_unique (site/org summary objects without stable keys) ---
    "getSiteStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Aggregate health and capacity statistics for a site",
    },
    "getSiteGatewayMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Gateway performance metrics summary for a site",
    },
    "getSiteSwitchesMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "Switch performance metrics summary for a site",
    },
    # --- HA Gateway Cluster ---
    "GetSiteDeviceHaClusterNode": {
        "type": "composite_pk",
        "primary_key": ["site_id", "device_id"],  # Each device has one HA node record per site
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "HA cluster node membership (node0/node1 MAC pair) for a gateway at a site",
    },
    "listSiteGatewayHaStats": {
        "type": "composite_pk",
        "primary_key": ["site_id", "mac"],  # Gateway MAC is unique per site
        "indexes": ["site_id", "is_ha", "node_name"],
        "unique_constraints": [],
        "description": "Combined HA gateway stats and cluster node membership for all HA gateways at a site",
    },
}


# ============================================================================
# CACHE UTILITIES CLASS
# ============================================================================
class CacheUtils:
    """
    Centralized cache management utilities.
    Handles CSV caching, freshness checks, regeneration, etc.
    """

    _ADDRESS_PARSE_FAILURE_FIELDNAMES: list[str] = [  # Stable column order for AddressParseFailures CSV
        "site_id",
        "site_name",
        "device_id",
        "device_serial",
        "device_name",
        "original_address",
        "parsed_tokens",
        "failure_reason",
        "timestamp",
    ]

    @staticmethod
    def check_and_generate_csv(
        file_name: str,
        generate_function: Callable,  # type: ignore[type-arg]
        freshness_minutes: int | None = None,
    ) -> bool:
        """Return True if file_name's CSV exists and is fresh; otherwise run generate_function.

        freshness_minutes defaults to CSV_FRESHNESS_MINUTES (.env). Returns True when the file is
        fresh or was regenerated successfully, False if regeneration failed.
        """
        logging.debug(
            "ENTRY: CacheUtils.check_and_generate_csv(file_name=%s, generate_function=%s, freshness_minutes=%s)",
            file_name,
            generate_function.__name__,
            freshness_minutes,
        )

        if freshness_minutes is None:  # No explicit override supplied
            freshness_minutes = CSV_FRESHNESS_MINUTES  # Fall back to the configured default freshness

        full_file_path = FilePathUtils.get_csv_path(file_name)  # Resolve the CSV path under data/
        if CacheUtils._is_csv_fresh(full_file_path, file_name, freshness_minutes):  # Existing file still fresh?
            return True  # Use the cached file -- no regeneration needed
        return CacheUtils._run_csv_generator(generate_function, file_name)  # Stale/missing -- (re)generate now

    @staticmethod
    def _is_csv_fresh(full_file_path: str, file_name: str, freshness_minutes: int) -> bool:  # Cache freshness check
        """Return True only when the file exists and was modified within freshness_minutes (else regenerate)."""
        if not os.path.exists(full_file_path):  # File missing entirely
            logging.info("* %s not found. Generating...", file_name)  # Tell operator it will be generated
            return False  # Not fresh -- caller regenerates
        try:  # Reading mtime can fail on permission/metadata errors
            file_mtime = datetime.fromtimestamp(os.path.getmtime(full_file_path))  # Last-modified timestamp
            logging.debug("File I/O: read mtime for %s: %s", full_file_path, file_mtime)  # Trace the mtime read
            if datetime.now() - file_mtime < timedelta(minutes=freshness_minutes):  # Within the freshness window
                logging.info("! Using cached %s (fresh)", file_name)  # Tell operator the cache is being used
                return True  # Fresh -- skip regeneration
            logging.info("* %s is older than %s minutes. Regenerating...", file_name, freshness_minutes)  # Stale notice
            return False  # Stale -- caller regenerates
        except OSError as error:  # Could not read the file's metadata
            logging.error("File I/O: Failed to read modification time for %s: %s", full_file_path, error)  # Log failure
            logging.info("* %s exists but cannot read metadata. Regenerating...", file_name)  # Tell operator
            return False  # Treat unreadable metadata as stale

    @staticmethod
    def _run_csv_generator(generate_function: Callable, file_name: str) -> bool:  # type: ignore[type-arg]  # Run generator
        """Invoke the generate_function to produce the CSV; return True on success, False on failure."""
        logging.info("* Running %s to generate %s...", generate_function.__name__, file_name)  # Log before generating
        try:  # The generator may raise; never let that crash the caller
            generate_function()  # Produce or refresh the CSV file
            logging.info("! %s generated or refreshed.", file_name)  # Confirm success to operator
            return True  # Generation succeeded
        except Exception as error:  # Generation failed for any reason
            logging.error("Failed to generate %s using %s: %s", file_name, generate_function.__name__, error)  # Log it
            return False  # Generation failed

    @staticmethod
    def load_csv_grouped_by_key(filename: str, key: str) -> dict[str, list[dict[str, Any]]]:
        """Load a CSV into a dict keyed by the named column; value is the list of rows sharing it."""
        logging.info(
            "Loading CSV file '%s' into dictionary keyed by '%s'...", filename, key
        )  # Log before reading the file
        csv_file_path = FilePathUtils.get_csv_path(filename)  # Resolve the CSV path under the data/ directory
        with open(csv_file_path, encoding="utf-8") as file:  # Open the CSV for reading
            reader = csv.DictReader(file)  # Parse each row into a dictionary keyed by column name
            data_dict: dict[str, list[dict[str, Any]]] = {}  # Group rows by the chosen key column
            row_count = 0  # Count how many valid rows we ingest
            for row in reader:  # Process each CSV row
                data_key = row.get(key)  # Extract the grouping key value from this row
                if data_key is None:  # The key column is missing on this row
                    logging.warning("Row missing key '%s': %s", key, row)  # Warn about the malformed row
                    continue  # Skip rows that can't be grouped
                if data_key not in data_dict:  # First time we've seen this key value
                    data_dict[data_key] = []  # Start a new bucket for it
                data_dict[data_key].append(row)  # Add this row to its key's bucket
                row_count += 1  # Tally the ingested row
            logging.info(
                "Loaded %s rows from '%s'. Found %s unique keys for '%s'.", row_count, filename, len(data_dict), key
            )  # Summary log
        return data_dict  # Return the grouped-by-key dictionary

    @staticmethod
    def _collect_csv_fieldnames(data: dict[str, list[dict[str, Any]]]) -> list[str]:
        """Return sorted union of keys across every row in every section."""
        fieldnames: set[str] = set()  # Accumulate every distinct key seen across all sections
        for section_name, section in data.items():  # Walk each named section once
            logging.debug("Processing section '%s' with %s rows.", section_name, len(section))
            for row in section:  # Each row contributes its keys to the union
                fieldnames.update(row.keys())  # Set update is O(k) and dedupes for us
        return sorted(fieldnames)  # Sort so the CSV column order is deterministic

    @staticmethod
    def _write_data_rows_to_csv(writer: csv.DictWriter, data: dict[str, list[dict[str, Any]]]) -> int:
        """Write every row from every section through writer; return total row count."""
        row_count = 0  # Tally rows actually written so the caller can log the total
        for section in data.values():  # Iterate sections in insertion order; keys are unused here
            for row in section:  # Write each row through the DictWriter
                writer.writerow(row)  # csv handles encoding/escaping for us
                row_count += 1  # Increment after a successful write
        return row_count  # Caller logs this for operator visibility

    @staticmethod
    def write_support_data_to_csv(data: dict[str, list[dict[str, Any]]], filename: str) -> None:
        """Write the support package (dict of section -> rows) to filename under data/."""
        logging.debug("Preparing to write support package to %s...", filename)  # Log before doing IO
        fieldnames_sorted = CacheUtils._collect_csv_fieldnames(data)  # Union of keys, deterministic order
        logging.debug("Final CSV fieldnames: %s", fieldnames_sorted)  # Trace exact header order
        csv_file_path = FilePathUtils.get_csv_path(filename)  # SECURITY: anchor under data/
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:  # Open for writing
            writer = csv.DictWriter(file, fieldnames=fieldnames_sorted)  # Bind writer to fixed header
            writer.writeheader()  # Emit header before any data rows
            row_count = CacheUtils._write_data_rows_to_csv(writer, data)  # Stream all rows through
            logging.info("Wrote %s rows to %s for support package.", row_count, csv_file_path)
        logging.info("Support package written to %s", csv_file_path)  # Final success message

    # Known generated cache CSV filenames -- cleared by Menu 175
    GENERATED_FILES: set[str] = {  # Explicit list of MistHelper-generated cache CSVs to protect non-data files
        "AllDevicesWithSiteInfo.csv",
        "GatewayDeviceStats.csv",
        "GatewayDeviceStatsWithSiteInfo.csv",
        "GatewayMgmtIPs.csv",
        "OrgDeviceEvents.csv",
        "OrgInventory.csv",
        "OrgSwitchVCStats.csv",
        "PortStats.csv",
        "SiteList.csv",
        "SitePortStats.csv",
        "VPNPeerStats.csv",
    }

    # Generated CSV filename prefixes -- any file in data/ matching these is a cache candidate
    GENERATED_PREFIXES: tuple[str, ...] = (  # Prefixes that identify auto-generated cache files
        "AllDevices",
        "AuditLogs",
        "DeviceEvents",
        "DevicePort",
        "Gateway",
        "Org",
        "Port",
        "Site",
        "Switch",
        "VPN",
    )

    @staticmethod
    def _is_generated_file(filename: str) -> bool:  # Check if file is MistHelper-generated
        """Return True if the filename matches a known generated cache file."""
        name = os.path.basename(filename)  # Strip any path component for clean matching
        if name in CacheUtils.GENERATED_FILES:  # Exact match against the explicit allowlist
            return True  # Explicitly listed -- safe to delete
        if name.endswith(".csv") and name.startswith(CacheUtils.GENERATED_PREFIXES):  # Prefix match
            return True  # Prefix match -- safe to delete
        return False  # Not a recognised generated file -- leave it alone

    @staticmethod
    def clear_cache() -> None:  # Menu 175: delete all generated cache CSVs from data/ directory
        """Delete all MistHelper-generated cache CSV files from the data/ directory."""
        data_dir = "data"  # Relative path to data/ consistent with FilePathUtils.get_csv_path()
        logging.info("Scanning data directory for generated cache CSVs: %s", data_dir)  # Log scan target
        candidates = CacheUtils._scan_cache_candidates(data_dir)  # List safe-to-delete files (None on scan error)
        if candidates is None:  # Directory could not be listed (already reported by the scanner)
            return  # Abort -- nothing to delete if we can't list the directory
        if not candidates:  # Nothing to delete -- inform operator and return early
            print("! No generated cache CSV files found to delete.")  # User-friendly empty state message
            logging.info("No generated cache CSVs found in %s", data_dir)  # Log empty result
            return  # Early return -- nothing to do
        print(f"Found {len(candidates)} generated cache CSV file(s) to delete:")  # Show operator what will be removed
        for name in sorted(candidates):  # Sort for readable output
            print(f"  {name}")  # List each file so operator knows exactly what is affected
        deleted, errors = CacheUtils._delete_cache_files(data_dir, candidates)  # Delete each file, counting outcomes
        print(f"! Cache cleared: {deleted} file(s) deleted, {errors} error(s).")  # Summary line for operator
        logging.info("Cache clear complete: %d deleted, %d errors", deleted, errors)  # Log summary for post-run review

    @staticmethod
    def _scan_cache_candidates(data_dir: str) -> list[str] | None:  # List generated cache files, or None on error
        """Return the list of generated cache filenames in data_dir, or None if the directory can't be listed."""
        logging.debug("Listing generated cache candidates in %s", data_dir)  # Trace the scan before listing
        try:  # Listing can fail on permissions or a missing directory
            return [
                name for name in os.listdir(data_dir) if CacheUtils._is_generated_file(name)
            ]  # Keep only MistHelper-generated cache files (safe to delete)
        except OSError as scan_error:  # Permission or missing-directory error
            logging.error("Failed to list data directory %s: %s", data_dir, scan_error)  # Log I/O failure with context
            print(f"! Error scanning data directory: {scan_error}")  # Surface error to operator
            return None  # Signal the caller to abort

    @staticmethod
    def _delete_cache_files(data_dir: str, candidates: list[str]) -> tuple[int, int]:  # Delete files, count outcomes
        """Delete each candidate cache file; return (deleted_count, error_count)."""
        deleted = 0  # Track successful deletions for summary
        errors = 0  # Track failures for summary
        for name in candidates:  # Delete each identified cache file
            full_path = os.path.join(data_dir, name)  # Build the path for deletion
            logging.info("Deleting cache CSV: %s", full_path)  # Log before deletion for audit trail
            try:  # Individual deletions may fail without aborting the batch
                os.remove(full_path)  # Delete the file from disk
                logging.debug("Deleted: %s", full_path)  # Confirm deletion at debug level
                deleted += 1  # Increment success counter
            except OSError as delete_error:  # Handle individual file deletion failures
                logging.error("Failed to delete %s: %s", full_path, delete_error)  # Log failure with path and reason
                print(f"  ! Could not delete {name}: {delete_error}")  # Surface individual failure to operator
                errors += 1  # Increment error counter
        return deleted, errors  # Report totals to the caller

    @staticmethod
    def create_address_parse_failures_csv(
        parse_failures: list[dict[str, Any]], filename: str = "AddressParseFailures.csv"
    ) -> None:
        """Write address-parse failures to a CSV in data/; safe no-op when list is empty."""
        if not parse_failures:
            logging.info("No address parsing failures to document.")
            return
        try:
            output_path = FilePathUtils.get_csv_path(filename)  # Resolve target path under data/
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CacheUtils._ADDRESS_PARSE_FAILURE_FIELDNAMES)
                writer.writeheader()  # Header row first
                for failure in parse_failures:
                    writer.writerow(failure)  # One row per failure record
            logging.info("Address parsing failures documented in: %s (%s records)", filename, len(parse_failures))
            print(f"! Address parsing failures documented in: {filename} ({len(parse_failures)} records)")
        except Exception as e:
            logging.error("Failed to create address parse failures CSV: %s", e)
            print(f"! Failed to create address parse failures CSV: {e}")

    @staticmethod
    def fast_cache_hit(filename: str, max_age_minutes: int = 60) -> bool:  # Check if cached output file is fresh
        """Return True when filename exists in data/ and is younger than max_age_minutes."""
        full_path = FilePathUtils.get_csv_path(filename)  # Resolve path inside data/ directory
        logging.debug("fast_cache_hit check for %s (max_age=%d min)", filename, max_age_minutes)  # Log check
        if not os.path.exists(full_path):  # File not present -- always a miss
            logging.debug("fast_cache_hit MISS: %s not found", filename)  # Log miss reason
            return False  # Cache miss -- caller should generate the file
        try:
            age_seconds = time.time() - os.path.getmtime(full_path)  # Seconds since last modification
            age_minutes = age_seconds / 60.0  # Convert to minutes for readable comparison
            if age_minutes <= max_age_minutes:  # File is within the freshness window
                logging.info("fast_cache_hit HIT: %s (%.1f min old)", filename, age_minutes)  # Log cache hit
                print(f"! Using cached {filename} ({age_minutes:.0f} min old) -- skipping re-generation.")
                return True  # Cache hit -- caller can skip expensive work
            logging.debug("fast_cache_hit MISS: %s is stale (%.1f min old)", filename, age_minutes)  # Log stale
            return False  # File is too old -- cache miss
        except OSError as stat_error:  # Handle race conditions or permission issues
            logging.warning("fast_cache_hit: could not stat %s: %s", filename, stat_error)  # Log I/O issue
            return False  # Treat stat failure as a miss to be safe


# ============================================================================
# DISPLAY UTILITIES CLASS
# ============================================================================
# NOTE: DisplayUtils has been extracted to
# src/ui/display_utils.py (issue #1013 SC-001 position 11)


# Issue #431: module-level alias `PacketCaptureManager = ExtractedPacketCaptureManager`
# was removed. The canonical name is now imported directly at module top.


# SFPTransceiverDataProcessor moved to src/reports/sfp_transceiver_data_processor.py  # noqa: E501
# (1013 SC-001 position 27)


class FilePathUtils:
    """
    Centralized file path utilities for consistent data directory handling.
    Ensures all CSV and data files are placed in the correct data directory.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def get_csv_path(filename: str) -> str:  # Resolve a CSV name to a path under data/.
        """
        Helper function to ensure consistent CSV file paths in the data directory.

        Args:
            filename (str): The CSV filename (with or without path)

        Returns:
            str: Full path to the CSV file in the data directory
        """
        # Ensure data directory exists
        data_dir = "data"  # All exports are confined to the data/ directory.
        os.makedirs(data_dir, exist_ok=True)  # Create data/ on first use; no error if it exists.

        # If filename already includes a path, use it as-is
        if os.path.dirname(filename):  # Caller supplied an explicit directory.
            return filename  # Respect caller-provided paths verbatim.

        # Otherwise, place it in the data directory
        return os.path.join(data_dir, filename)  # Join bare names under data/ portably.

    @staticmethod
    def create_csv_template(
        filename: str, headers: list[str] | None = None, sample_data: list[list[str]] | None = None
    ) -> str:  # Create an empty CSV placeholder with optional headers.
        """Create an empty CSV under data/ with optional header row; sample_data is intentionally ignored."""
        del sample_data  # Kept in signature for API compatibility; explicitly discard so linters do not flag it.
        file_path = FilePathUtils.get_csv_path(filename)  # Normalize the destination under data/.
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:  # Truncate/create the file.
                if headers:  # Only write a header row when headers were provided.
                    writer = csv.writer(f)  # Wrap the handle in a CSV writer.
                    writer.writerow(headers)  # Emit the single header row.
            logging.info("Created template file: %s", file_path)  # Record the created placeholder.
            return file_path  # Hand the path back to the caller.
        except Exception as error:  # Never leave a partial file without surfacing the cause.
            logging.error("Failed to create template file %s: %s", filename, error)  # Log the failure cause.
            raise  # Re-raise so callers can handle the failure.


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
class ConfigUtils:  # Org id and run-control helpers.
    """
    Centralized configuration utilities.
    Handles org_id retrieval, credentials, and configuration management.
    """

    @staticmethod
    def _resolve_org_id_from_dotenv() -> str | None:
        """Try to parse org_id from a sibling .env file; return value or None."""
        try:
            with open(".env") as env_file:  # Fall back to the .env file
                for line in env_file:  # Scan each line for org_id
                    if line.strip().startswith("org_id="):  # Match the org_id assignment
                        return line.strip().split("=", 1)[1].strip().strip('"')  # Extract and unquote
        except FileNotFoundError:  # No .env file present
            logging.warning("! .env file not found.")
        return None  # No value found

    @staticmethod
    def _resolve_org_id_via_prompt() -> str:
        """Prompt the user (via mistapi) to select an org; sys.exit on failure."""
        logging.info("* No org_id found in .env or CLI. Prompting user...")  # Prompt the user as last resort
        org_id_list = mistapi.cli.select_org(apisession)  # Interactive org selection
        if not org_id_list:  # Selection returned nothing
            logging.error("Failed to retrieve org list. Check your API token and authentication.")
            print("[ERROR] Unable to retrieve organizations. Your API token may be invalid or expired.")
            print("[ERROR] Please update MIST_API_TOKEN in your .env file and try again.")
            sys.exit(1)  # Abort: no org to proceed with
        return org_id_list[0]  # Use the first selected org

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:  # Resolve org_id from cache/env/.env/prompt.
        """Resolve org_id by precedence: module global -> env vars -> .env file -> interactive prompt."""
        global org_id  # Cache resolved id in the module global
        if org_id:  # Reuse an already-resolved id
            logging.info("! Using org_id from global variable: %s", org_id)
            return org_id  # type: ignore[no-any-return]
        org_id_env = os.environ.get("org_id") or os.environ.get("ORG_ID")  # Try environment variables next
        if org_id_env:  # Environment provided the id
            org_id = org_id_env  # Cache the env value
            logging.info("! Loaded org_id from environment: %s", org_id)
            return org_id
        dotenv_org = ConfigUtils._resolve_org_id_from_dotenv()  # Try the .env file fallback
        if dotenv_org:  # .env file provided the id
            org_id = dotenv_org  # Cache the .env value
            logging.info("! Loaded org_id from .env: %s", org_id)
            return org_id
        org_id = ConfigUtils._resolve_org_id_via_prompt()  # Last resort: interactive prompt
        return org_id  # type: ignore[no-any-return]

    @staticmethod
    def check_stop_signal() -> bool:  # Check for the user stop sentinel.
        """Check for stop_loop.txt signal file and remove if found.

        Any long-running loop that iterates over sites or devices with API
        calls should call this once per iteration so the user can cancel
        gracefully by creating the stop file.

        Returns:
            True if the stop signal was detected (caller should break).
        """
        if os.path.exists("stop_loop.txt"):  # Sentinel file requests a stop.
            try:
                os.remove("stop_loop.txt")  # Consume the sentinel once.
            except OSError:  # Ignore removal races.
                pass  # Best-effort cleanup only.
            print(" Stop signal detected. Ending operation early.")  # Notify the user of early stop.
            logging.info("Stop signal (stop_loop.txt) detected - operation stopped by user.")  # Log user stop.
            return True  # Signal callers to stop.
        return False  # No stop requested.


# ============================================================================
# API FETCH UTILITIES CLASS
# ============================================================================
# NOTE: APICoreFetchUtils removed (1014 P10, Cat E) - canonical body at src/api/api_core_fetch_utils.py.


# APITenantFetchUtils extracted to src/api/tenant_fetch.py (issue #331).
# Dependency injection is used so the module has no circular import with MistHelper.
# Instances are created at each call site using the runtime apisession and org ID resolver.
from src.api.tenant_fetch import APITenantFetchUtils  # noqa: F401  # Re-exported for ServicePingLauncher late-binding

# NOTE: APIFetchUtils removed (1014 P8, Cat E) - canonical body at src/api/api_fetch_utils.py.

# ============================================================================
# DATA PROCESSING UTILITIES CLASS
# ============================================================================


class DataProcessingUtils:  # JSON flattening/normalization.
    """
    Centralized data processing utilities.
    Groups all data transformation functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.

    Implementation Note: Methods contain the actual logic rather than delegating
    to standalone functions, per the 5-Item Rule class organization requirement.
    """

    @staticmethod
    def _flatten_list_value(new_key: str, sep: str, v: list) -> list[tuple[str, Any]]:
        """Flatten a list value: list-of-dicts gets index keys; scalar lists join as CSV. Returns pairs to extend."""
        out: list[tuple[str, Any]] = []  # Accumulator for produced pairs
        if all(isinstance(i, dict) for i in v):  # List of dicts: index each
            for idx, item in enumerate(v):  # Walk list items
                out.extend(DataProcessingUtils.flatten_dict(item, f"{new_key}{sep}{idx}", sep=sep).items())
            return out
        out.append((new_key, ",".join(map(str, v))))  # Join scalar list as CSV
        return out

    @staticmethod
    def flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:  # Flatten nested dict.
        """Recursively flatten nested dict for CSV/JSON; lists-of-dicts get index keys, scalar lists join as CSV."""
        items: list[tuple[str, Any]] = []  # Accumulate flattened pairs
        for k, v in d.items():  # Walk each key/value
            k_str = str(k)  # Stringify the key
            new_key = f"{parent_key}{sep}{k_str}" if parent_key else k_str  # Compose the dotted key
            if isinstance(v, dict):  # Recurse into nested dicts
                items.extend(DataProcessingUtils.flatten_dict(v, new_key, sep=sep).items())
                continue
            if isinstance(v, list):  # Lists need index expansion
                items.extend(DataProcessingUtils._flatten_list_value(new_key, sep, v))
                continue
            items.append((new_key, v))  # Keep scalar value as-is
        return dict(items)  # Return the flat dict

    @staticmethod
    def flatten_nested_fields(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Flatten nested fields in a list of dictionaries.
        Attempts to parse stringified dicts/lists.
        Recursively flattens nested dicts and lists of dicts.
        Joins non-dict lists as comma-separated strings.

        Args:
            data: List of dictionaries to process

        Returns:
            list: List of dictionaries with flattened nested fields
        """
        flattened = []  # Collect flattened rows.
        for entry in data:  # Process each record.
            if not isinstance(entry, dict):  # Skip non-dict records.
                logging.debug("Skipping non-dictionary entry: %s", type(entry).__name__)  # Trace skipped entry.
                continue  # Move to next record.
            flattened.append(DataProcessingUtils._flatten_entry(entry))  # Delegate per-entry flattening.
        return flattened  # Return all flattened rows.

    @staticmethod
    def _flatten_entry(entry):
        """Flatten a single dict entry, returning a new dict with nested values expanded."""
        new_entry = {}  # Accumulator for the flattened output of this entry
        for key, value in entry.items():  # Walk every field of the entry
            parsed = DataProcessingUtils._parse_stringified_value(value)  # Maybe parse stringified JSON
            DataProcessingUtils._flatten_value_into(new_entry, key, parsed)  # Expand nested into new_entry
        return new_entry  # Return the flattened entry

    @staticmethod
    def _parse_stringified_value(value):
        """Try to parse a string starting with { or [ as Python literal or JSON; return original on failure."""
        if not isinstance(value, str):  # Non-string values pass through unchanged
            return value  # Nothing to parse
        if not value.startswith(("{", "[")):  # Not embedded JSON-ish - skip parsing
            return value  # Return as-is
        try:
            return ast.literal_eval(value)  # Try Python-literal parse first
        except Exception:  # ast.literal_eval failed
            try:
                return json.loads(value)  # Fall back to JSON parse
            except Exception:  # nosec B110 - both parses failed, leave as string
                return value  # Final fallback: original string

    @staticmethod
    def _flatten_value_into(new_entry, key, value):
        """Merge a single (key, value) into new_entry, expanding nested dicts/lists per legacy rules."""
        if isinstance(value, dict):  # Nested dict needs flattening
            new_entry.update(DataProcessingUtils.flatten_dict(value, parent_key=key))  # Merge flattened keys
            return  # Done for dict path
        if not isinstance(value, list):  # Scalar (non-dict, non-list)
            new_entry[key] = value  # Keep scalar value as-is
            return  # Done for scalar path
        if DataProcessingUtils._is_list_of_dicts(value):  # List of dicts: index each element
            for idx, item in enumerate(value):  # Walk list items
                new_entry.update(DataProcessingUtils.flatten_dict(item, parent_key=f"{key}_{idx}"))  # Merge item keys
            return  # Done for list-of-dicts path
        new_entry[key] = ",".join(map(str, value))  # Scalar list - join as CSV

    @staticmethod
    def _is_list_of_dicts(value):
        """Return True when every element of value is a dict (used by _flatten_value_into)."""
        return all(isinstance(i, dict) for i in value)  # Check every element is dict-typed

    @staticmethod
    def convert_list_values_to_strings(data):  # Stringify list-valued fields.
        """
        Convert list, tuple, or set values to CSV-compatible comma-separated strings.

        Args:
            data: List of dictionaries containing list values

        Returns:
            Data with list values converted to strings
        """
        for entry in data:  # Process each record.
            for key, value in entry.items():  # Walk each field.
                if isinstance(value, (list, tuple, set)):  # Only convert collections.
                    logging.debug("Converting list/tuple/set at key '%s' to string", key)  # Trace the conversion.
                    entry[key] = ",".join(map(str, value))  # Join as CSV string.
        return data  # Return converted records.

    @staticmethod
    def get_unique_keys(data):  # Collect the union of all keys.
        """
        Get all unique dictionary keys from a list of dictionaries.
        Returns a sorted list of string keys.

        Args:
            data: List of dictionaries

        Returns:
            list: Sorted list of unique keys as strings
        """
        fields = set()  # Accumulate distinct keys.
        for entry in data:  # Scan each record.
            fields.update(entry.keys())  # Add this record's keys.
        return sorted(str(f) for f in fields)  # Return sorted field names.

    @staticmethod
    def escape_multiline(data):  # Escape newlines for CSV safety.
        """
        Escape multiline strings for CSV compatibility.
        Joins list values as comma-separated strings.
        Replaces newline characters with escaped versions.

        Args:
            data: List of dictionaries containing multiline strings

        Returns:
            Data with escaped multiline strings
        """
        for entry in data:  # Process each record.
            for key, value in entry.items():  # Walk each field.
                if isinstance(value, list):  # Join lists to a string.
                    entry[key] = ",".join(map(str, value))  # CSV-join the list.
                elif isinstance(value, str):  # Escape string newlines.
                    entry[key] = value.replace("\n", "\\n").replace("\r", "")  # Escape CR/LF for CSV.
        return data  # Return escaped records.


# MarvisDataUtils extracted to src/marvis/marvis_utils.py (issue #330).
# Dependency injection is used so the module has no circular import with MistHelper.

# NOTE: marvis_data_utils singleton extracted to
# src/refactors/marvis_data_utils.py::MarvisDataUtilsFactory.instance()
# per initiative 1011 SC-027 (FR-003: no wrapper shim; FR-005: fn->method).


# DatabaseSchemaUtils moved to src/db/database_schema_utils.py (1013 SC-001 position 38)


class DataExporter:  # Multi-backend export facade.
    """
    Handles data export operations for CSV and Redis/SQLite output formats.
    Centralizes all data saving logic that was previously scattered across functions.
    Uses static methods to avoid unnecessary object instantiation.
    """

    _router: "DatabaseRouter | None" = None  # type: ignore[name-defined]
    _router_initialized: bool = False  # One-shot guard so the lazy router init runs exactly once per process.
    _last_snapshot_times: dict[str, float] = {}  # Per-table last-snapshot epoch times used to throttle snapshots.

    @staticmethod
    def _polyglot_db_layer_available() -> bool:
        """True when the optional polyglot DB layer was imported and exposes every name we use."""
        if not DB_LAYER_AVAILABLE:  # Optional dependency not installed
            return False
        if DatabaseConfig is None:  # Module loaded but config class missing — treat as unavailable
            return False
        if configure_db_logging is None:  # Logger setup missing
            return False
        return DatabaseRouter is not None  # Final required symbol

    @classmethod
    def _build_polyglot_router(cls) -> None:
        """Construct DatabaseRouter from env (called only when the polyglot layer is available)."""
        try:  # Router construction reads env and opens connections — guard against any startup failure
            assert configure_db_logging is not None  # Guarded by _polyglot_db_layer_available
            assert DatabaseConfig is not None  # Guarded by _polyglot_db_layer_available
            assert DatabaseRouter is not None  # Guarded by _polyglot_db_layer_available
            configure_db_logging()  # Route DB layer's logger into MistHelper logging before first use
            config = DatabaseConfig.from_env()  # Build connection settings from .env so secrets stay out of code
            cls._router = DatabaseRouter(  # Cache the shared router on the class for every later export call
                config,  # Pass env-derived connection/configuration object
                strategies=ENDPOINT_PRIMARY_KEY_STRATEGIES,  # Per-endpoint primary-key upsert strategies
            )
            logging.info("Polyglot DatabaseRouter initialized")  # Confirm successful backend startup
        except Exception as error:  # Never let optional-backend startup crash a core CSV/SQLite export
            logging.warning("DatabaseRouter init failed, CSV/SQLite only: %s", error)  # Surface degraded mode
            cls._router = None  # Force safe CSV/SQLite path when router could not be constructed

    @classmethod
    def _init_router(cls) -> None:  # Lazy polyglot router init.
        """Initialize polyglot DatabaseRouter once (lazy, idempotent)."""
        if cls._router_initialized:  # Skip when a prior call already attempted init
            return
        cls._router_initialized = True  # Latch the guard before fallible work
        if not DataExporter._polyglot_db_layer_available():  # Optional polyglot layer not installed
            logging.debug("Polyglot DB layer not installed - CSV/SQLite only")
            return
        cls._build_polyglot_router()  # Construct router (catches startup failures internally)

    @staticmethod
    def _dispatch_format_write(
        data: list[dict[str, Any]],
        filename_or_table: str,
        output_format: str,
        fieldnames: list[str] | None,
        api_function_name: str | None,
    ) -> bool:
        """Pick CSV vs SQLite write path; return success flag; catches and logs write exceptions."""
        try:
            if output_format == "csv":  # CSV branch
                return DataExporter._write_csv_format(data, filename_or_table, fieldnames=fieldnames)
            return DataExporter._write_sqlite_format(data, filename_or_table, api_function_name)  # SQLite branch
        except Exception as error:  # Never crash on write
            logging.error("Failed to write data to %s in %s format: %s", filename_or_table, output_format, error)
            return False

    @staticmethod
    def write_with_format_selection(  # Public export entry point.
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str | None = None,
        fieldnames: list[str] | None = None,
        backend_options: "ExportBackendOptions | None" = None,
    ) -> bool:
        """Write data to CSV or SQLite per OUTPUT_FORMAT (or backend_options.format_override); mirror to polyglot DB."""
        opts = backend_options if backend_options is not None else ExportBackendOptions()  # Resolve defaults
        output_format = opts.format_override if opts.format_override else OUTPUT_FORMAT  # Override or global format
        logging.debug(
            "DataExporter.write_with_format_selection: rows=%s, target=%s, format=%s, api_func=%s",
            len(data) if data else 0,
            filename_or_table,
            output_format,
            api_function_name,
        )
        if not DataExporter._validate_write_inputs(data, filename_or_table, output_format):  # Pre-validate
            return False
        csv_ok = DataExporter._dispatch_format_write(
            data, filename_or_table, output_format, fieldnames, api_function_name
        )  # Run the chosen writer
        DataExporter._route_to_polyglot(data, api_function_name, raw_data=opts.raw_data)  # Mirror to polyglot DB
        return csv_ok  # Return the primary result

    _standalone_logged = False  # One-shot standalone log guard.

    @staticmethod
    def _is_standalone_mode() -> bool:  # Detect non-container standalone.
        """Auto-detect standalone mode: skip polyglot when not in a container."""
        standalone_env = os.getenv("MISTHELPER_STANDALONE", "").lower()  # Read the override env.
        if standalone_env == "true":  # Explicit standalone request.
            return True  # Forced standalone.
        if standalone_env == "false":  # Forced non-standalone.
            return False  # Not standalone.
        if not EnvironmentUtils.is_running_in_container():  # Auto-detect when not in container.
            if not DataExporter._standalone_logged:  # Log once.
                logging.info("Standalone mode auto-detected (not in container), skipping polyglot database")
                DataExporter._standalone_logged = True  # Latch the one-shot log.
            return True  # Standalone outside a container.
        return False  # Containerized: not standalone.

    @staticmethod
    def _should_skip_polyglot(api_function_name: str | None) -> bool:
        """Decide whether the polyglot write should be skipped (no API name / layer / standalone / no router)."""
        if not api_function_name or not DB_LAYER_AVAILABLE:  # Need API name AND DB layer present
            return True
        if DataExporter._is_standalone_mode():  # Standalone bypasses polyglot
            return True
        DataExporter._init_router()  # Lazy router init
        return DataExporter._router is None  # Skip if router could not be built

    @staticmethod
    def _perform_polyglot_write(payload: list[dict[str, Any]], api_function_name: str) -> None:
        """Issue the actual router write call, logging result; never raises (logs warning on failure)."""
        try:
            assert DataExporter._router is not None  # Caller checks _should_skip_polyglot first
            result = DataExporter._router.write(payload, api_function_name)  # Write to polyglot DB
            logging.info(  # Log the polyglot result
                "Polyglot write: backend=%s, written=%s, failed=%s",
                result.backend,
                result.records_written,
                result.records_failed,
            )
        except Exception as error:  # Never let polyglot break CSV
            logging.warning("Polyglot write failed (CSV preserved): %s", error)

    @staticmethod
    def _route_to_polyglot(  # Mirror writes to polyglot DB.
        data: list[dict[str, Any]],
        api_function_name: str | None,
        raw_data: list[dict[str, Any]] | None = None,
    ) -> None:
        """Send data to polyglot backends (ArangoDB/Redis) if available."""
        if DataExporter._should_skip_polyglot(api_function_name):  # Combined eligibility check
            return
        polyglot_data = raw_data or data  # Prefer raw payload when caller supplied it
        assert api_function_name is not None  # _should_skip_polyglot returns True for None
        DataExporter._perform_polyglot_write(polyglot_data, api_function_name)  # Issue write (catches errors)

    @classmethod
    def _check_periodic_snapshot(  # Throttle periodic snapshots.
        cls,
        api_function_name: str,
        threshold_seconds: float = 3600.0,
    ) -> bool:
        """Check if enough time elapsed since last snapshot for this API.

        Returns True if a snapshot should be taken (threshold exceeded).
        Updates the timestamp when returning True.
        """
        now = time.time()  # Current time.
        last_time = cls._last_snapshot_times.get(api_function_name, 0.0)  # Last snapshot time.
        if (now - last_time) < threshold_seconds:  # Too soon for another.
            return False  # Skip this snapshot.
        cls._last_snapshot_times[api_function_name] = now  # Record snapshot time.
        return True  # Allow the snapshot.

    @staticmethod
    def _validate_write_inputs(data: list[dict[str, Any]], filename_or_table: str, output_format: str) -> bool:
        """Validate inputs for write operation. Returns True if valid."""
        if not data:  # No rows to write.
            logging.warning("No data provided for output to %s", filename_or_table)  # warn no data.
            return False  # Reject empty data.

        if output_format not in ["csv", "sqlite"]:  # Only csv/sqlite allowed.
            logging.error("Invalid output format: %s. Must be 'csv' or 'sqlite'", output_format)  # bad format.
            return False  # Reject bad format.

        return True  # Inputs valid.

    @staticmethod
    def _write_csv_format(  # Write rows to a CSV file.
        data: list[dict[str, Any]],
        filename_or_table: str,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Write data to CSV format.  Pass fieldnames to preserve a specific column order."""
        csv_filename = filename_or_table if filename_or_table.endswith(".csv") else f"{filename_or_table}.csv"
        logging.info("Writing %s rows to CSV file: %s", len(data), csv_filename)  # Log CSV write.
        DataExporter.write_to_csv(data, csv_filename, fieldnames=fieldnames)  # Thread explicit column order through
        return True  # CSV written.

    @staticmethod
    def _write_sqlite_format(data: list[dict[str, Any]], filename_or_table: str, api_function_name: str | None) -> bool:
        """Write data to SQLite format. Returns True on success."""
        table_name = filename_or_table[:-4] if filename_or_table.endswith(".csv") else filename_or_table
        logging.debug(  # Trace SQLite write.
            "SQLite write: table=%s, api_function=%s, strategy lookup initiated", table_name, api_function_name
        )
        logging.info("Writing %s rows to SQLite table: %s", len(data), table_name)  # Log SQLite write.
        return SQLiteDatabaseWriter(data, table_name, api_function_name).write()  # Run the writer.

    @staticmethod
    def write_to_csv(
        data: list[dict[str, Any]],
        csv_file: str,
        fieldnames: list[str] | None = None,
    ) -> None:
        """Write rows to a CSV file, escaping multiline values and honoring an optional column order.

        Args:
            data: Rows to write.
            csv_file: Destination filename (placed in data/ if no directory is given).
            fieldnames: Optional explicit column order; defaults to sorted unique keys.
        """
        logging.debug("ENTRY: DataExporter.write_to_csv(data_rows=%s, csv_file=%s)", len(data) if data else 0, csv_file)
        if not data:  # No rows to write -- short-circuit and trace the early exit
            logging.warning("No data provided to write to %s", csv_file)  # Inform caller of empty payload
            logging.debug("EXIT: DataExporter.write_to_csv - no data to write")  # Trace early exit
            return  # Nothing to do
        csv_file_path = DataExporter._resolve_csv_path(csv_file)  # Place bare filenames under data/
        logging.debug("Preparing to write %s rows to %s...", len(data), csv_file_path)  # Trace write prep
        escaped_data = DataProcessingUtils.escape_multiline(data)  # type: ignore[no-untyped-call]
        fields = DataExporter._resolve_csv_fields(escaped_data, fieldnames)  # Final column order for the CSV
        logging.debug("CSV fields determined: %s", fields)  # Trace fields
        DataExporter._write_csv_with_exception_handling(csv_file_path, escaped_data, fields)  # Open + write rows
        logging.info("File I/O: Successfully wrote %s rows to %s", len(escaped_data), csv_file_path)  # Log success
        logging.debug("EXIT: DataExporter.write_to_csv - success")  # Trace exit

    @staticmethod
    def _resolve_csv_path(csv_file: str) -> str:
        """Return the on-disk path for csv_file, placing bare filenames under data/."""
        data_dir = "data"  # Confine bare filenames to data/ for container persistence
        os.makedirs(data_dir, exist_ok=True)  # Ensure data/ exists before any write
        if not os.path.dirname(csv_file):  # Caller passed a bare filename (no directory component)
            resolved = os.path.join(data_dir, csv_file)  # Place under data/
        else:
            resolved = csv_file  # Caller-provided full path is honored verbatim
        logging.debug("Resolved CSV destination path: %s", resolved)  # Trace path resolution
        return resolved  # Final destination

    @staticmethod
    def _resolve_csv_fields(escaped_data: list[dict[str, Any]], fieldnames: list[str] | None) -> list[str]:
        """Return the CSV column order; honor caller-supplied fieldnames or fall back to sorted unique keys."""
        if fieldnames is not None:  # Caller supplied an explicit column order -- preserve it verbatim
            logging.debug("Using caller-supplied fieldnames for CSV column order")  # Trace explicit ordering
            return fieldnames  # Use as-is
        derived = DataProcessingUtils.get_unique_keys(escaped_data)  # type: ignore[no-untyped-call]
        logging.debug("Derived %s unique CSV columns from data", len(derived))  # Trace derived ordering
        return derived  # Sorted unique keys

    @staticmethod
    def _emit_rows(writer: csv.DictWriter, escaped_data: list[dict[str, Any]], fields: list[str]) -> None:
        """Write every row in escaped_data through writer; debug-log the first three for diagnostics."""
        for idx, row in enumerate(escaped_data):  # Walk each row in input order
            writer.writerow({field_name: row.get(field_name, "") for field_name in fields})  # Emit in col order
            if idx < 3:  # Trace the first three rows to aid post-mortem debugging
                logging.debug("Row %s written: %s", idx, row)  # Per-row trace

    @staticmethod
    def _write_csv_open_and_emit(
        csv_file_path: str,
        escaped_data: list[dict[str, Any]],
        fields: list[str],
    ) -> None:
        """Open the destination CSV and write header + rows; lets I/O errors propagate to the caller."""
        logging.debug("File I/O: Attempting to open %s for writing", csv_file_path)  # Trace pre-open
        with open(csv_file_path, "w", newline="", encoding="utf-8") as file_handle:  # Open CSV for writing
            writer = csv.DictWriter(file_handle, fieldnames=fields)  # Dict-based CSV writer
            writer.writeheader()  # Write the header row first
            logging.debug("File I/O: Successfully wrote CSV header to %s", csv_file_path)  # Trace header write
            DataExporter._emit_rows(writer, escaped_data, fields)  # Stream rows through the writer

    @staticmethod
    def _write_csv_with_exception_handling(
        csv_file_path: str,
        escaped_data: list[dict[str, Any]],
        fields: list[str],
    ) -> None:
        """Run the CSV write under structured error handling -- map I/O failures to user-friendly diagnostics."""
        try:  # Wrap the write to translate I/O failures into the legacy diagnostic surface
            DataExporter._write_csv_open_and_emit(csv_file_path, escaped_data, fields)  # Open + emit
        except PermissionError as perm_error:  # File locked or write denied
            logging.error("File I/O: Permission denied when writing to %s: %s", csv_file_path, perm_error)
            print(f"! Cannot write to {csv_file_path}. Is it open in another program?")  # User-facing hint
            logging.debug("EXIT: DataExporter.write_to_csv - permission error")  # Trace exit on perm denial
            raise  # Propagate to the caller
        except OSError as os_error:  # OS-level write failure (disk full, path invalid, etc.)
            logging.error("File I/O: OS error when writing to %s: %s", csv_file_path, os_error)  # Log OS failure
            logging.debug("EXIT: DataExporter.write_to_csv - OS error")  # Trace OS error exit
            raise  # Propagate to the caller
        except Exception as unexpected_error:  # Any other unexpected failure
            logging.error(
                "File I/O: Unexpected error when writing to %s: %s", csv_file_path, unexpected_error
            )  # Log unexpected
            logging.debug("EXIT: DataExporter.write_to_csv - unexpected error")  # Trace unexpected exit
            raise  # Propagate to the caller

    # save_data_to_output removed per issue #431 (ARCH-DELEGATE). All call
    # sites now invoke DataExporter.write_with_format_selection(data, filename,
    # api_function_name=...) directly -- it is the canonical implementation
    # and accepts the identical (data, filename, api_function_name=) form.

    @staticmethod
    def export_with_processing(data, filename, sort_key=None, api_function_name=None):  # Process then export records.
        """Flatten, optionally sort, and export records via the selected backend.

        Returns the number of records exported (0 when there is no data or the export fails).
        """
        if not data:  # Nothing to export.
            logging.warning("No data to export for %s", filename)  # warn no data.
            return 0  # Zero exported.

        raw_data = [entry for entry in data if isinstance(entry, dict)]  # Keep dict rows only (defensive).
        raw_data = DataExporter._sort_records(raw_data, sort_key)  # Optionally sort by the requested key.

        processed_data = DataProcessingUtils.flatten_nested_fields(raw_data)  # Flatten nested fields for CSV/SQLite.
        processed_data = DataProcessingUtils.escape_multiline(processed_data)  # type: ignore[no-untyped-call]

        success = DataExporter.write_with_format_selection(  # Write flattened to CSV/SQLite, raw to polyglot
            processed_data,
            filename,
            api_function_name=api_function_name,
            backend_options=ExportBackendOptions(raw_data=raw_data),  # Issue #470: raw_data bundled.
        )

        return DataExporter._finalize_export(success, len(processed_data), filename)  # Log outcome, return count

    @staticmethod
    def _sort_records(raw_data: list[dict[str, Any]], sort_key: str | None) -> list[dict[str, Any]]:  # Optional sort
        """Return raw_data sorted by sort_key (missing values sort as ''), or unchanged when no key given."""
        if not sort_key:  # No sort requested
            return raw_data  # Preserve original order
        sorted_data = sorted(raw_data, key=lambda entry: entry.get(sort_key, ""))  # Sort by key (missing -> '')
        logging.debug("Data sorted by key: %s", sort_key)  # Trace the sort.
        return sorted_data  # Sorted rows

    @staticmethod
    def _finalize_export(success: bool, processed_count: int, filename: str) -> int:  # Log + return export outcome
        """Log the export result and return the processed-row count on success, 0 on failure."""
        if success:  # Export succeeded.
            logging.info("Exported %s records to %s", processed_count, filename)  # Log export count.
            return processed_count  # Return rows exported.
        logging.error("Failed to export data to %s", filename)  # log export failure.
        return 0  # Zero exported.


# APIDataFetcher moved to src/api/api_data_fetcher.py (1013 SC-001 position 21)


# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute.
# See specs/1012-misthelper-refactor-hot-functions/spec.md.


# ============================================================================
# PROMPT UTILITIES CLASS
# ============================================================================
# PromptNetworkDeviceUtils -- extracted to src/device/prompt_utils.py (issue #332)


# PromptClientUtils moved to src/input/prompt_client_utils.py (1013 SC-001 position 35)


class PromptUtils:  # General prompt helpers.
    """
    Centralized prompt utilities for user input and selection operations.
    Groups all interactive selection functions (sites, devices, ports, clients).
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def select_device_id_from_inventory(
        site_id: str, device_type: str = "all", csv_filename: str = "SiteInventory.csv"
    ) -> str | None:
        """Prompt operator to select a device from ``site_id`` inventory and return its device id.

        Always fetches type=all from the API (Mist default is APs-only) and filters locally.
        """
        inventory = PromptUtils._fetch_and_filter_devices(site_id, device_type)  # API + local filter.
        if not inventory:  # Nothing matched the requested filter.
            return None  # Abort selection.
        table, index_to_device, name_to_device = PromptUtils._export_and_index_inventory(inventory, csv_filename)
        print(table)  # Render the device table.
        logging.info("Displayed device selection table to user.")  # Log table display.
        user_input = InputUtils.safe_input(  # Read operator device choice.
            "Enter the index or name of the device to view device: ",
            context="device_inventory_selection",
        ).strip()
        logging.debug("User input for device selection: %s", user_input)  # Log raw device input.
        return PromptUtils._resolve_device_selection(user_input, index_to_device, name_to_device)  # Resolve.

    @staticmethod
    def _filter_inventory_by_type(inventory: list, device_type: str) -> list:
        """Filter inventory rows by comma-separated device types (case-insensitive); 'all' returns input as-is."""
        if device_type == "all":  # No filter needed
            return inventory
        requested_types = [dtype.strip() for dtype in device_type.split(",")]  # Split requested filter
        return [device for device in inventory if device.get("type", "").lower() in requested_types]

    @staticmethod
    def _fetch_and_filter_devices(site_id: str, device_type: str) -> list | None:
        """Fetch the full site inventory (``type=all``) and filter locally to ``device_type``."""
        rawdata = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all").data  # Fetch
        if not rawdata:  # Empty inventory path
            print("No devices found for the selected site.")
            logging.warning("No devices found for site_id: %s", site_id)
            return None
        filtered = PromptUtils._filter_inventory_by_type(rawdata, device_type)  # Apply type filter
        if not filtered:  # Filter produced empty set
            print(f"No devices of type '{device_type}' found at the selected site.")
            logging.warning("No devices of type '%s' found for site_id: %s", device_type, site_id)
            return None
        return filtered

    @staticmethod
    def _export_and_index_inventory(rawdata: list, csv_filename: str) -> tuple:
        """Sort + flatten + CSV-export ``rawdata`` and return ``(table, index_map, name_map)``."""
        inventory = sorted(rawdata, key=lambda x: x.get("model", ""))  # Sort by model.
        inventory = DataProcessingUtils.flatten_nested_fields(inventory)  # Flatten nested fields.
        inventory = DataProcessingUtils.escape_multiline(inventory)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(inventory, csv_filename)  # type: ignore[no-untyped-call]
        logging.info("Device inventory for site_id written to %s", csv_filename)  # Log CSV write location.
        table = PrettyTable()  # Build selection table.
        table.field_names = ["Index", "name", "mac", "model", "serial"]  # Columns.
        index_to_device: dict = {}  # Index lookup.
        name_to_device: dict = {}  # Name lookup.
        for idx, item in enumerate(inventory):  # Build rows.
            table.add_row(
                [idx, item.get("name", ""), item.get("mac", ""), item.get("model", ""), item.get("serial", "")]
            )
            index_to_device[idx] = item  # Map index to device.
            name_to_device[item.get("name", "")] = item  # Map name to device.
        return table, index_to_device, name_to_device  # Return all three for caller.

    @staticmethod
    def _resolve_device_selection(user_input: str, index_to_device: dict, name_to_device: dict) -> str | None:
        """Resolve ``user_input`` to a device id by index or name; return None on miss."""
        normalized = user_input[1:] if user_input.startswith(".") else user_input  # Strip leading dot.
        if normalized.isdigit():  # Numeric index path.
            idx = int(normalized)  # Parse index.
            if idx in index_to_device:  # Valid index.
                device_id = index_to_device[idx].get("id")  # Read id.
                logging.info("User selected device by index: %s (device_id: %s)", idx, device_id)  # Log.
                return device_id  # type: ignore[no-any-return]
            logging.error(" Invalid index.")  # Log invalid index.
            return None  # Abort.
        if normalized in name_to_device:  # Name match path.
            device_id = name_to_device[normalized].get("id")  # Read id by name.
            logging.info("User selected device by name: %s (device_id: %s)", normalized, device_id)  # Log.
            return device_id  # type: ignore[no-any-return]
        logging.error(" Device not found by name or index.")  # Log not-found.
        return None  # Abort.

    @staticmethod
    def select_site_id_from_csv(csv_file: str = "SiteList.csv") -> str | None:  # Prompt site id from CSV.
        """Prompt user to select a site by index or name from csv_file; returns the site ID or None."""
        CacheUtils.check_and_generate_csv(csv_file, OrgSiteExporter.sites)  # Ensure site CSV exists/fresh.
        index_to_site, name_to_site = PromptUtils._load_site_csv_maps(csv_file)  # Read CSV into index/name maps.
        print("\nAvailable Sites:")  # Print available sites heading.
        for idx, row in index_to_site.items():  # Enumerate site rows.
            print(f"[{idx}] {row.get('name', 'Unnamed')}")  # Print each site option.
        user_input = InputUtils.safe_input("\nEnter site index or name: ", context="site_selection").strip()
        logging.debug("User input for site selection: %s", user_input)  # Log raw site input.
        global LAST_SELECTED_SITE_ID  # Track last selected site globally.
        if user_input.isdigit():  # Branch: numeric index choice.
            site_id = PromptUtils._pick_site_by_index(int(user_input), index_to_site)  # Resolve by index.
            if site_id is not None:  # Cache successful selection.
                LAST_SELECTED_SITE_ID = site_id  # Remember last selected site.
            return site_id  # Return resolved id (or None on invalid index).
        if user_input in name_to_site:  # Branch: name match.
            site_id = PromptUtils._pick_site_by_name(user_input, name_to_site)  # Resolve by name.
            LAST_SELECTED_SITE_ID = site_id  # Remember last selected site.
            return site_id  # Return resolved id.
        print(" Site not found by name or index.")  # Report not-found site.
        logging.warning("Site not found by name or index: %s", user_input)  # Log not-found site.
        return None  # Abort on not found.

    @staticmethod
    def _load_site_csv_maps(csv_file: str) -> tuple[dict[int, dict], dict[str, dict]]:  # type: ignore[type-arg]
        """Read site CSV at FilePathUtils.get_csv_path(csv_file) and return (index_to_site, name_to_site) maps."""
        csv_file_path = FilePathUtils.get_csv_path(csv_file)  # Resolve CSV file path.
        with open(csv_file_path, encoding="utf-8") as file:  # Open the site CSV.
            reader = list(csv.DictReader(file))  # Read all CSV rows.
        index_to_site = {i: row for i, row in enumerate(reader)}  # Map index to site row.
        name_to_site = {row["name"]: row for row in reader if "name" in row}  # Map name to site row.
        return index_to_site, name_to_site

    @staticmethod
    def _pick_site_by_index(idx: int, index_to_site: dict[int, dict]) -> str | None:  # type: ignore[type-arg]
        """Resolve a numeric site index to a site_id; print/log selection or invalid-index message."""
        if idx not in index_to_site:  # Validate index exists.
            print(" Invalid index.")  # Reject out-of-range index.
            logging.warning("Invalid site index entered: %s", idx)  # Log invalid index.
            return None  # Abort on invalid index.
        site_id = index_to_site[idx].get("id")  # Read selected site id.
        print(f"! Selected site: {index_to_site[idx].get('name')} (ID: {site_id})")  # Confirm site selection.
        logging.info("User selected site by index: %s (site_id: %s)", idx, site_id)  # Log index selection.
        return site_id  # Return selected site id.

    @staticmethod
    def _pick_site_by_name(name: str, name_to_site: dict[str, dict]) -> str | None:  # type: ignore[type-arg]
        """Resolve a site name to a site_id; print/log the selection."""
        site_id = name_to_site[name].get("id")  # Read site id by name.
        print(f"! Selected site: {name} (ID: {site_id})")  # Confirm site selection.
        logging.info("User selected site by name: %s (site_id: %s)", name, site_id)  # Log name selection.
        return site_id  # Return selected site id.

    @staticmethod
    def select_site() -> str | None:  # Convenience site selector.
        """
        Prompts the user to select a site and returns the site_id.
        Uses the existing CSV-based site selection functionality.

        Returns:
            str: The selected site ID or None if no selection made
        """
        return PromptUtils.select_site_id_from_csv()  # Delegate to CSV selector.

    @staticmethod
    def select_site_with_logging() -> str | None:  # Site selector with logging.
        """
        Prompts the user to select a site from the CSV list and logs the selection.

        Returns:
            str: The selected site ID or None if no selection made
        """
        logging.info("Prompting user to select a site from SiteList.csv...")  # Log selection prompt start.
        site_id = PromptUtils.select_site_id_from_csv()  # Prompt site from CSV.
        if site_id:  # Handle successful selection.
            logging.info("! Selected site ID: %s", site_id)  # Log selected site id.
        else:
            logging.error(" No site selected. User may have entered an invalid value or cancelled the prompt.")
        return site_id  # Return selected site id.

    # PromptUtils.select_device removed per issue #431 (ARCH-DELEGATE).
    # Callers now use PromptUtils.select_device_id_from_inventory(site_id, device_type)
    # directly -- it is the canonical implementation and accepts the same arguments.

    @staticmethod
    def _determine_search_scope(site_id: str | None) -> str | None | Literal[False]:  # Determine client search scope.
        """Resolve search scope: provided site_id, prompted site_id, None (org-wide), or False (user cancelled)."""
        if site_id:  # Use provided site directly.
            return site_id  # Return supplied site id.
        scope_choice = (  # Prompt for scope choice.
            InputUtils.safe_input(
                "Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ",
                context="client_search_scope",
            )
            .strip()
            .lower()
        )
        if scope_choice == "s":  # Branch: single-site scope.
            selected_site = PromptUtils.select_site()  # Prompt to pick a site.
            if not selected_site:  # Handle no-site selection.
                print(" No site selected.")  # Tell operator none selected.
                return False  # Signal scope failure.
            return selected_site  # Return chosen site scope.
        return None  # Org-wide search

    @staticmethod
    def _fetch_all_clients(org_id: str, site_id: str | None) -> list[dict]:  # type: ignore[type-arg]
        """
        Fetches wireless and wired clients from site or org.

        Returns:
            List of client dictionaries with client_type added.
        """
        all_clients = []  # Combined client accumulator.

        if site_id:  # Branch: site-scoped search.
            print("! Searching for clients in selected site...")  # Inform operator of site search.
            wireless = PromptUtils._fetch_site_wireless_clients(site_id)  # Fetch site wireless clients.
            wired = PromptUtils._fetch_site_wired_clients(site_id)  # Fetch site wired clients.
        else:
            print("! Searching for clients across organization...")  # Inform operator of org search.
            wireless = PromptUtils._fetch_org_wireless_clients(org_id)  # Fetch org wireless clients.
            wired = PromptUtils._fetch_org_wired_clients(org_id)  # Fetch org wired clients.

        all_clients.extend(wireless)  # Add wireless clients to list.
        all_clients.extend(wired)  # Add wired clients to list.

        return sorted(all_clients, key=lambda x: (x.get("hostname", ""), x.get("mac", "")))

    @staticmethod
    def _fetch_site_wireless_clients(site_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wireless clients for a specific site."""
        try:
            response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(apisession, site_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wireless"  # Mark as wireless type.
                client["source_site_id"] = site_id  # Record source site id.
            logging.info("Found %s wireless clients in site", len(clients))  # Log wireless client count.
            return clients  # Return wireless clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wireless clients for site: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_site_wired_clients(site_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wired clients for a specific site."""
        try:
            response = mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(apisession, site_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wired"  # Mark as wired type.
                client["source_site_id"] = site_id  # Record source site id.
            logging.info("Found %s wired clients in site", len(clients))  # Log wired client count.
            return clients  # Return wired clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wired clients for site: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_org_wireless_clients(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wireless clients for the entire organization."""
        try:
            response = mistapi.api.v1.orgs.clients.searchOrgWirelessClients(apisession, org_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wireless"  # Mark as wireless type.
            logging.info("Found %s wireless clients in organization", len(clients))  # Log wireless client count.
            return clients  # Return wireless clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wireless clients for org: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_org_wired_clients(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wired clients for the entire organization."""
        try:
            response = mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients(apisession, org_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wired"  # Mark as wired type.
            logging.info("Found %s wired clients in organization", len(clients))  # Log wired client count.
            return clients  # Return wired clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wired clients for org: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _load_sites_cache(org_id: str) -> dict[str, str]:  # Load site id-to-name cache.
        """Loads site ID to name mapping for display purposes."""
        try:
            print(" Loading site information...")  # Inform operator of load.
            sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites for org.
            cache = {site["id"]: site["name"] for site in sites}  # Build id-to-name map.
            logging.info("Cached %s sites for client display", len(cache))  # Log cached site count.
            return cache  # Return the cache.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch sites for display: %s", exception)  # Log fetch failure.
            return {}  # Return empty cache on error.

    @staticmethod
    def _print_client_type_summary(all_clients: list[dict]) -> None:
        """Print the wireless/wired count line and status legend for the client selection table."""
        wireless_count = sum(1 for c in all_clients if c.get("client_type") == "wireless")  # Count wireless
        wired_count = sum(1 for c in all_clients if c.get("client_type") == "wired")  # Count wired
        print(f"\n  Summary: {wireless_count} wireless, {wired_count} wired clients")
        print("\n  [+] = Online  [~] = Recently seen  [-] = Offline")
        print("---" * 20)

    @staticmethod
    def _display_client_table(all_clients: list[dict], sites_cache: dict[str, str]) -> dict[int, dict]:  # type: ignore[type-arg]
        """Render the client selection table and a summary line; return an index-to-client map for selection."""
        table = PromptUtils._build_client_table_skeleton()  # Build empty table with columns + alignment
        for idx, client in enumerate(all_clients):  # Enumerate clients for rows
            row = PromptUtils._format_client_row(idx, client, sites_cache)  # Format a client row
            table.add_row(row)
        print(f"\n  Found {len(all_clients)} clients:")
        print(table)
        PromptUtils._print_client_type_summary(all_clients)  # Type counts + legend
        return dict(enumerate(all_clients))  # Index-to-client map for caller

    @staticmethod
    def _build_client_table_skeleton() -> PrettyTable:  # Build empty client display table.
        """Build an empty PrettyTable with the client-selection columns, alignment, and per-column max widths."""
        table = PrettyTable()  # Build client display table.
        table.field_names = ["#", "Hostname", "MAC Address", "Type", "IP Address", "SSID/VLAN", "Site", "Status"]
        # Typed so PrettyTable AlignType is preserved through the tuple literal.
        column_alignments: tuple[tuple[str, Literal["l", "c", "r"]], ...] = (
            ("#", "r"),
            ("Hostname", "l"),
            ("MAC Address", "l"),
            ("Type", "c"),
            ("IP Address", "l"),
            ("SSID/VLAN", "l"),
            ("Site", "l"),
            ("Status", "c"),
        )
        for column, alignment in column_alignments:
            table.align[column] = alignment  # Apply column alignment.
        for column, width in (("Hostname", 20), ("IP Address", 16), ("SSID/VLAN", 15), ("Site", 15)):
            table.max_width[column] = width  # Cap column width.
        return table

    @staticmethod
    def _format_client_row(idx: int, client: dict, sites_cache: dict[str, str]) -> list:  # type: ignore[type-arg]
        """Formats a single client row for the selection table."""
        site_name = PromptUtils._get_client_site_name(client, sites_cache)  # Resolve site name for row.
        status = PromptUtils._get_client_status(client)  # Resolve status marker.
        hostname = PromptUtils._truncate_string(client.get("hostname", client.get("name", "Unknown")) or "Unknown", 20)
        ip_address = PromptUtils._format_client_ip(client)  # Format client IP.
        ssid_vlan = PromptUtils._format_client_ssid_vlan(client)  # Format SSID/VLAN field.

        return [  # Return formatted row cells.
            idx,
            hostname,
            client.get("mac", "Unknown"),
            client.get("client_type", "unknown")[:8],
            ip_address,
            ssid_vlan,
            PromptUtils._truncate_string(site_name, 15),
            status,
        ]

    @staticmethod
    def _get_client_site_name(client: dict, sites_cache: dict[str, str]) -> str:  # type: ignore[type-arg]
        """Gets site name from cache or returns site ID."""
        site_id = client.get("site_id", "")  # Read client site id.
        if site_id in sites_cache:  # Branch: site found in cache.
            return sites_cache[site_id]  # Return cached site name.
        return site_id if site_id else ""  # Fallback to raw site id.

    @staticmethod
    def _get_client_status(client: dict) -> str:  # type: ignore[type-arg]
        """Determines client connection status indicator."""
        if client.get("connected", True):  # Branch: client connected.
            status = "[+]"  # Mark online status.
        else:
            status = "[-]"  # Mark offline status.

        if "last_seen" in client:  # Branch: last_seen present.
            last_seen = client.get("last_seen", 0)  # Read last_seen timestamp.
            current_time = int(time.time())  # Capture current time.
            if current_time - last_seen > 300:  # More than 5 minutes ago
                status = "[~]"  # Mark recently-seen status.

        return status  # Return status marker.

    @staticmethod
    def _format_client_ip(client: dict) -> str:  # type: ignore[type-arg]
        """Formats client IP address, handling arrays."""
        ip_address = client.get("ip", "")  # Read client IP field.
        if isinstance(ip_address, list):  # Branch: IP is a list.
            return ip_address[0] if ip_address else "N/A"  # Return first IP or N/A.
        return ip_address if ip_address and ip_address != "[]" else "N/A"  # Return IP or N/A.

    @staticmethod
    def _format_client_ssid_vlan(client: dict) -> str:  # type: ignore[type-arg]
        """Formats client SSID/VLAN, handling arrays."""
        ssid_vlan = client.get("ssid", client.get("vlan", ""))  # Read SSID or VLAN field.
        if isinstance(ssid_vlan, list):  # Branch: value is a list.
            ssid_vlan = str(ssid_vlan[0]) if ssid_vlan else "N/A"  # Use first element or N/A.
        elif not ssid_vlan or ssid_vlan == "[]":  # Branch: empty value.
            ssid_vlan = "N/A"  # Default to N/A.
        return PromptUtils._truncate_string(str(ssid_vlan), 15)  # Truncate for column width.

    @staticmethod
    def _truncate_string(value: str, max_length: int) -> str:  # Truncate helper.
        """Truncates string with ellipsis if too long."""
        if len(value) > max_length:  # Branch: over max length.
            return value[: max_length - 3] + "..."  # Truncate with ellipsis.
        return value  # Return unchanged value.

    @staticmethod
    def _handle_client_selection(
        all_clients: list[dict],  # type: ignore[type-arg]
        sites_cache: dict[str, str],
        default_site_id: str | None,
    ) -> tuple[str | None, str | None, str | None]:
        """Read operator client choice. Returns (mac, type, site_id) or (None, None, None)."""
        max_index = len(all_clients) - 1  # Compute max valid index for prompt
        user_input = InputUtils.safe_input(  # Read operator choice from stdin
            f"\n  Enter client index (0-{max_index}) or 'q' to quit: ",
            context="client_selection_index",
        ).strip()
        idx = PromptClientUtils._parse_client_choice(user_input, max_index)  # Parse to validated index
        if idx is None:  # Quit / invalid / out-of-range -- abort
            return None, None, None  # Signal no selection to caller
        return PromptUtils._extract_selected_client(all_clients[idx], sites_cache, default_site_id)

    @staticmethod
    def _extract_selected_client(
        client: dict,  # type: ignore[type-arg]
        sites_cache: dict[str, str],
        default_site_id: str | None,
    ) -> tuple[str, str, str]:
        """Extracts and displays selected client information."""
        client_mac = client.get("mac", "")  # Read client MAC.
        client_type = client.get("client_type", "unknown")  # Read client type.
        client_site_id = client.get("site_id", default_site_id) or ""  # Resolve client site id.
        hostname = client.get("hostname", client.get("name", "Unknown"))  # Read hostname/name.

        print("\n Selected client:")  # Print selection heading.
        print(f"   Name: {hostname}")  # Show client name.
        print(f"   MAC: {client_mac}")  # Show client MAC.
        print(f"   Type: {client_type}")  # Show client type.
        if client_site_id and client_site_id in sites_cache:  # Branch: known site.
            print(f"   Site: {sites_cache[client_site_id]}")  # Show resolved site name.

        logging.info("User selected client: MAC=%s, type=%s, site=%s", client_mac, client_type, client_site_id)
        return client_mac, client_type, client_site_id  # Return client id triple.


# NOTE: show_site_device_inventory() has been refactored into SiteDeviceExporter.device_inventory()


# NOTE: DeviceUtils has been extracted to src/device/device_utils.py (issue #1013 SC-001 position 6)


# OrgTicketManager moved to src/org/org_ticket_manager.py (1013 SC-001 Cat B position 46)


# OrgAlarmEventExporter moved to src/export/org_alarm_event_exporter.py (1013 SC-001 position 18)


# ============================================================================
# ORGANIZATION DATA EXPORT UTILITIES CLASS
# ============================================================================
# NOTE: OrgSiteExporter has been extracted to
# src/export/org_site_exporter.py (issue #1014 P9)


class OrgInventoryExporter:  # Org inventory exporters.
    """
    Organization Inventory and Device Exporter

    Handles inventory, device, and combined site-device exports.
    Extracted from OrgExportUtils.
    """

    # Stable weekly-export column order for CombinedInventory outputs (downstream consumers depend on it).
    _COMBINED_INVENTORY_FIELDNAMES = [
        "Full Site",
        "System Serial Number",
        "System MAC Address",
        "System Model Number",
        "End Customer Name",
        "Address Line 1",
        "Address Line 2",
        "City",
        "State",
        "Country",
        "Zip Code / Postal Code",
        "End Customer Account ID",
    ]

    @staticmethod
    def inventory():  # Export org device inventory.
        """
        Fetches and exports the full inventory of devices in the organization to OrgInventory.csv.
        Uses APIDataFetcher to handle API call, CSV writing, and table display.
        """
        logging.info("Starting export of organization device inventory...")  # Log inventory export start.
        emitter = PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("12", "inventory", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        APIDataFetcher(
            title="Org Inventory:",
            api_call=mistapi.api.v1.orgs.inventory.getOrgInventory,
            filename="OrgInventory.csv",
            sort_key="model",
            vc=True,  # Include all physical VC member devices (6186 vs 3224 logical)
            limit=1000,
        ).execute()
        logging.info("Completed organization inventory export and wrote results to OrgInventory.csv.")
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(ProgressContext("12", "inventory", 1), 1, False, time.time() - op_start)

    @staticmethod
    def devices():  # Export all org devices.
        """
        Fetches and exports a list of all devices in the organization to OrgDevices.csv.
        Uses APIDataFetcher to handle API call, CSV writing, and table display.
        """
        logging.info("Starting export of all organization devices...")  # Log devices export start.
        emitter = PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("17", "devices", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        APIDataFetcher(  # Fetch and write devices.
            title="Org Devices:",
            api_call=mistapi.api.v1.orgs.devices.listOrgDevices,
            filename="OrgDevices.csv",
            sort_key="type",
        ).execute()
        logging.info("Completed organization devices export and wrote results to OrgDevices.csv.")
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(ProgressContext("17", "devices", 1), 1, False, time.time() - op_start)

    @staticmethod
    def _resolve_combined_inventory_org_name(current_org_id: str | None, fallback_org_name: str | None) -> str:
        """Resolve organization name used for combined inventory output filenames."""
        org_name_for_filename = None  # Start with no resolved org name so API lookup can fill it in.
        try:  # Resolve org name from live Mist API first so filenames follow authoritative naming.
            org_response = mistapi.api.v1.orgs.orgs.getOrg(
                apisession, current_org_id
            )  # Fetch org details for filename metadata.
            org_name_for_filename = getattr(org_response, "data", {}).get(
                "name"
            )  # Pull org name from the response payload if present.
        except Exception as exception:  # API resolution failure should not block report generation.
            logging.warning(
                "Unable to resolve org name from API for combined inventory filename: %s", exception
            )  # Log fallback reason for operators.
        if not org_name_for_filename:  # Fall back to customer name from environment when API name is unavailable.
            org_name_for_filename = fallback_org_name  # Use configured customer-friendly name if present.
        if not org_name_for_filename:  # Final fallback ensures a stable filename even with missing metadata.
            org_name_for_filename = current_org_id or "UnknownOrg"  # Use org ID or sentinel value as a last resort.
        return org_name_for_filename  # Return resolved display name for downstream filename sanitization.

    @staticmethod
    def _build_safe_org_name(org_name_for_filename: str) -> str:  # Build filesystem-safe org name.
        """Sanitize organization name so generated filenames stay filesystem-safe."""
        return "".join(  # Build safe filename character-by-character to preserve readable names.
            character if character.isalnum() or character in "-_" else "_" for character in org_name_for_filename
        )

    @staticmethod
    @staticmethod
    def _fetch_and_persist_raw_inventory_variant(
        filename: str, request_kwargs: dict, current_org_id: str, output_folder: str
    ) -> int:
        """Fetch one inventory variant and persist as raw JSON; return row count."""
        logging.info("Fetching raw inventory variant for %s...", filename)  # Log before API call
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, current_org_id, **request_kwargs)
        raw_inventory = mistapi.get_all(response=response, mist_session=apisession)  # Paginate all results
        output_path = os.path.join(output_folder, filename)  # Build deterministic file path
        with open(output_path, "w", encoding="utf-8") as json_file:  # UTF-8 for portable JSON encoding
            json.dump(raw_inventory, json_file, indent=2, default=str)  # Pretty-print so humans can diff variants
        logging.info("Saved %d entries to %s", len(raw_inventory), output_path)  # Log per-file count
        return len(raw_inventory)  # Return for summary aggregation

    @staticmethod
    def _export_combined_inventory_raw_json(output_folder: str, current_org_id: str) -> None:
        """Export raw inventory JSON variants used for VC delta analysis."""
        logging.info("Saving raw inventory JSON for delta comparison...")  # Log start of diagnostic exports
        try:  # Raw JSON export is diagnostic only and must never block the main report
            os.makedirs(output_folder, exist_ok=True)  # Ensure shared output folder exists
            request_specs = [  # One spec per inventory query variant for consistent export loop
                ("raw_inventory_vc_true.json", {"vc": True, "type": "switch", "limit": DEFAULT_API_PAGE_LIMIT}),
                ("raw_inventory_vc_false.json", {"vc": False, "type": "switch", "limit": DEFAULT_API_PAGE_LIMIT}),
                ("raw_inventory_no_vc_param.json", {"type": "switch", "limit": DEFAULT_API_PAGE_LIMIT}),
            ]
            counts_by_filename: dict[str, int] = {
                filename: OrgInventoryExporter._fetch_and_persist_raw_inventory_variant(
                    filename, kwargs, current_org_id, output_folder
                )
                for filename, kwargs in request_specs
            }
            print(  # Show concise operator summary once all diagnostic files are written
                f"  Raw JSON saved: vc=True ({counts_by_filename.get('raw_inventory_vc_true.json', 0)}), "
                f"vc=False ({counts_by_filename.get('raw_inventory_vc_false.json', 0)}), "
                f"no-vc ({counts_by_filename.get('raw_inventory_no_vc_param.json', 0)}) entries"
            )
        except Exception as json_save_error:  # Diagnostic failure is non-fatal by design
            logging.warning("Failed to save raw inventory JSON: %s", json_save_error)  # Preserve root cause

    @staticmethod
    def _load_combined_inventory_rows() -> list[dict[str, str]]:  # Load combined inventory rows.
        """Load enriched device rows from AllDevicesWithSiteInfo.csv."""
        devices_with_site_info_path = FilePathUtils.get_csv_path(
            "AllDevicesWithSiteInfo.csv"
        )  # Resolve current CSV path through shared path utility.
        with open(
            devices_with_site_info_path, encoding="utf-8"
        ) as file:  # Open generated enrichment CSV for downstream grouping logic.
            return list(csv.DictReader(file))  # Materialize all rows so weekly grouping can iterate more than once.

    @staticmethod
    @staticmethod
    def _split_physical_vs_virtual_inventory(
        all_devices: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Split combined inventory into (physical_devices, virtual_vc_placeholders)."""
        virtual_entries = [
            d for d in all_devices if d.get("mac", "").startswith("020003")
        ]  # 020003* = synthetic VC MAC
        site_configs = [d for d in all_devices if not d.get("mac", "").startswith("020003")]  # Real chassis only
        return site_configs, virtual_entries  # Caller continues with VC classification

    @staticmethod
    def _classify_empty_vc_shells(
        virtual_entries: list[dict[str, str]], site_configs: list[dict[str, str]]
    ) -> tuple[list[dict[str, str]], int]:
        """Return (empty_vc_shells, duplicate_vc_entries) for the virtual-entry analysis."""
        physical_vc_macs = {d.get("vc_mac", "") for d in site_configs if d.get("vc_mac")}  # Set of VC parent MACs
        empty_shells = [e for e in virtual_entries if e.get("mac") not in physical_vc_macs]  # No physical members
        duplicates = len(virtual_entries) - len(empty_shells)  # Remainder mirrors real hardware
        return empty_shells, duplicates  # Caller logs the diagnostics

    @staticmethod
    def _partition_combined_inventory_rows(  # Partition combined inventory rows.
        all_devices: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
        """Separate physical inventory rows from virtual VC placeholders and count duplicates."""
        site_configs, virtual_entries = OrgInventoryExporter._split_physical_vs_virtual_inventory(
            all_devices
        )  # Bucket by MAC prefix
        empty_vc_shells, duplicate_vc_entries = OrgInventoryExporter._classify_empty_vc_shells(
            virtual_entries, site_configs
        )  # Analyze the virtual bucket
        return site_configs, empty_vc_shells, duplicate_vc_entries  # Physical rows + shell diagnostics

    @staticmethod
    def _emit_vc_shell_dashboard_diff(
        site_configs: list[dict[str, str]], empty_vc_shells: list[dict[str, str]]
    ) -> None:
        """Print the dashboard-vs-report parity note when empty VC shells exist."""
        print(
            f"  NOTE: {len(empty_vc_shells)} provisioned VC shells exist with no physical members."
        )  # Explain why dashboard counts may exceed report counts
        print(  # Provide explicit comparison so operators trust the physical-only report totals
            f"        Dashboard shows {len(site_configs) + len(empty_vc_shells)} 'Physical Devices' "
            f"but {len(empty_vc_shells)} are empty VC placeholders (020003* MAC, no serial/SKU)."
        )
        print(
            f"        Report correctly includes only {len(site_configs)} devices with real hardware."
        )  # Confirm report logic remains intentional

    @staticmethod
    def _log_combined_inventory_vc_summary(  # Log virtual-chassis summary.
        all_devices: list[dict[str, str]],
        site_configs: list[dict[str, str]],
        empty_vc_shells: list[dict[str, str]],
        duplicate_vc_entries: int,
    ) -> None:
        """Log and print the virtual chassis filtering summary for operators."""
        logging.info(  # Explain how many rows were filtered to reach physical-hardware-only reporting
            "Loaded %d total devices, filtered to %d physical devices (excluded %d virtual VC identifiers)",
            len(all_devices),
            len(site_configs),
            len(all_devices) - len(site_configs),
        )
        logging.info(  # Break down virtual rows into duplicates versus empty VC shells
            "Virtual VC breakdown: %d duplicate entries (real hardware counted elsewhere) + %d empty VC shells (provisioned but no physical members assigned)",  # noqa: E501
            duplicate_vc_entries,
            len(empty_vc_shells),
        )
        if empty_vc_shells:  # Surface dashboard/report parity nuance only when empty shells actually exist
            OrgInventoryExporter._emit_vc_shell_dashboard_diff(site_configs, empty_vc_shells)  # Print parity note

    @staticmethod
    def _build_combined_inventory_weekly_row(  # Build one weekly inventory row.
        device: dict[str, str],
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> dict[str, str | None]:
        """Build one weekly export row from a physical device record."""
        return {  # Shape output row once so weekly writer can stay simple and deterministic.
            "Full Site": device.get("site_name", ""),
            "System Serial Number": device.get("serial", ""),
            "System MAC Address": device.get("mac", ""),
            "System Model Number": device.get("model", ""),
            "End Customer Name": end_customer_name,
            "Address Line 1": device.get("street", ""),
            "Address Line 2": "",
            "City": device.get("city", ""),
            "State": device.get("state", ""),
            "Country": device.get("country", "US"),
            "Zip Code / Postal Code": device.get("zip_code", ""),
            "End Customer Account ID": end_customer_account_id,
        }

    @staticmethod
    def _bucket_device_into_week(
        device: dict[str, str],
        weekly_data: defaultdict,
        summary_data: defaultdict,
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> None:
        """Bucket one device into the correct ISO-week weekly_data + summary_data."""
        try:  # One bad device row must not derail the full export
            created_time = int(device.get("created_time", 0))  # Convert API timestamp to epoch seconds
            created_date = datetime.fromtimestamp(created_time, tz=UTC)  # UTC for deterministic bucketing
            year, week, _ = created_date.isocalendar()  # Derive ISO calendar week for CSV naming
            week_key = f"{year}_Week_{week:02d}"  # Stable filename segment
            weekly_data[week_key].append(  # Append detailed export row to the correct weekly bucket
                OrgInventoryExporter._build_combined_inventory_weekly_row(
                    device, end_customer_name, end_customer_account_id
                )
            )
            summary_data[(year, week)] += 1  # Increment summary counter for the same ISO week
        except Exception as exception:  # Row-level failure logged for cleanup
            logging.warning("! Skipping device due to error: %s", exception)  # Log row-level failure

    @staticmethod
    def _build_combined_inventory_weekly_data(  # Build weekly inventory dataset.
        site_configs: list[dict[str, str]],
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> tuple[defaultdict[str, list[dict[str, str | None]]], defaultdict[tuple[int, int], int]]:
        """Group physical devices into ISO calendar-week buckets and summary counts."""
        weekly_data: defaultdict[str, list[dict[str, str | None]]] = defaultdict(list)  # Per-week export rows
        summary_data: defaultdict[tuple[int, int], int] = defaultdict(int)  # Per-week device counts
        for device in site_configs:  # Process each physical device row exactly once
            OrgInventoryExporter._bucket_device_into_week(
                device,
                weekly_data,
                summary_data,
                end_customer_name,
                end_customer_account_id,
            )
        return weekly_data, summary_data  # Return both detailed buckets and summary counts

    @staticmethod
    def _write_combined_inventory_weekly_csvs(  # Write weekly inventory CSVs.
        output_folder: str,
        fieldnames: list[str],
        weekly_data: defaultdict[str, list[dict[str, str | None]]],
    ) -> None:
        """Write one CSV file per ISO week bucket."""
        for (
            week_key,
            rows,
        ) in (
            weekly_data.items()
        ):  # Emit each week as its own CSV so downstream consumers can process incremental periods.
            output_file = os.path.join(output_folder, f"{week_key}.csv")  # Build deterministic weekly CSV path.
            with open(
                output_file, mode="w", newline="", encoding="utf-8"
            ) as file:  # Open weekly file for a clean rewrite each run.
                writer = csv.DictWriter(
                    file, fieldnames=fieldnames
                )  # Use explicit field order so exports stay stable over time.
                writer.writeheader()  # Always emit header row for spreadsheet compatibility.
                writer.writerows(rows)  # Write all device rows for this ISO week.

    @staticmethod
    def _write_combined_inventory_summary(  # Write combined inventory summary.
        output_folder: str,
        summary_data: defaultdict[tuple[int, int], int],
    ) -> None:
        """Write summary CSV containing device counts per ISO year/week."""
        summary_file = os.path.join(
            output_folder, "CombinedInventory_Summary.csv"
        )  # Use fixed summary filename for discoverability.
        with open(
            summary_file, mode="w", newline="", encoding="utf-8"
        ) as file:  # Rewrite summary on each run so counts remain current.
            summary_writer = csv.writer(file)  # Use plain CSV writer because summary rows are positional.
            summary_writer.writerow(["Year", "Week", "Device Count"])  # Emit stable summary header.
            for (year, week), count in sorted(summary_data.items()):  # Sort chronologically for human readability.
                summary_writer.writerow([year, week, count])  # Persist per-week device totals.

    @staticmethod
    def _build_master_csv_row(device: dict[str, str]) -> dict[str, str]:
        """Build one flattened master-CSV row from a physical device record."""
        return {  # Simplified headers expected by downstream consumers
            "serial": device.get("serial", ""),
            "mac": device.get("mac", ""),
            "model": device.get("model", ""),
            "Street Address": device.get("street", ""),
            "City": device.get("city", ""),
            "State": device.get("state", ""),
            "Zip": device.get("zip_code", ""),
        }

    @staticmethod
    def _persist_master_csv(master_csv_file: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        """Write master inventory rows to CSV with explicit field order."""
        with open(master_csv_file, mode="w", newline="", encoding="utf-8") as file:  # Rewrite each run
            writer = csv.DictWriter(file, fieldnames=fieldnames)  # Explicit header ordering
            writer.writeheader()  # Column names for spreadsheet/ETL workflows
            writer.writerows(rows)  # Persist all physical-device rows

    @staticmethod
    def _write_combined_inventory_master_csv(  # Write combined inventory master CSV.
        output_folder: str,
        safe_org_name: str,
        site_configs: list[dict[str, str]],
    ) -> tuple[str, int]:
        """Write simplified master combined-inventory CSV and return filename plus row count."""
        master_csv_data = [
            OrgInventoryExporter._build_master_csv_row(device) for device in site_configs
        ]  # Build all master rows up front
        master_csv_filename = (
            f"{safe_org_name}_CombinedInventory_Master.csv"  # Include org for multi-org runs  # noqa: E501
        )
        master_csv_file = os.path.join(output_folder, master_csv_filename)  # Final path
        master_csv_fieldnames = ["serial", "mac", "model", "Street Address", "City", "State", "Zip"]  # Stable order
        OrgInventoryExporter._persist_master_csv(master_csv_file, master_csv_fieldnames, master_csv_data)
        return master_csv_filename, len(master_csv_data)  # Metadata for final summary message

    @staticmethod
    def _prepare_combined_inventory_context() -> tuple[str, str | None, str | None, str, str]:
        """Resolve org, customer, safe org name, and output folder for combined inventory export."""
        load_dotenv()  # Load customer metadata from .env
        end_customer_name = os.getenv("END_CUSTOMER_NAME")  # Used in weekly export columns
        end_customer_account_id = os.getenv("END_CUSTOMER_ACCOUNT_ID")  # Used in weekly export columns
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org context first
        org_name_for_filename = OrgInventoryExporter._resolve_combined_inventory_org_name(
            current_org_id, end_customer_name
        )  # Authoritative org name with safe fallbacks
        safe_org_name = OrgInventoryExporter._build_safe_org_name(org_name_for_filename)  # Portable filenames
        output_folder = os.path.join("data", "CombinedInventory_ByWeek")  # Predictable subfolder
        return current_org_id, end_customer_name, end_customer_account_id, safe_org_name, output_folder

    @staticmethod
    def _emit_combined_inventory_outputs(
        output_folder: str,
        safe_org_name: str,
        site_configs: list[dict[str, str]],
        weekly_data: defaultdict,
        summary_data: defaultdict,
    ) -> tuple[str, int]:
        """Emit weekly CSVs + summary + master CSV; return master filename + row count."""
        fieldnames = OrgInventoryExporter._COMBINED_INVENTORY_FIELDNAMES  # Stable weekly-export column order
        OrgInventoryExporter._write_combined_inventory_weekly_csvs(output_folder, fieldnames, weekly_data)
        OrgInventoryExporter._write_combined_inventory_summary(output_folder, summary_data)  # Year/week summary
        return OrgInventoryExporter._write_combined_inventory_master_csv(
            output_folder, safe_org_name, site_configs
        )  # Simplified master CSV used by external consumers

    @staticmethod
    def combined_inventory_with_site_info():  # Export devices with site info.
        """Combine fresh AllDevicesWithSiteInfo data into weekly CSV files + summary + master CSV."""
        print("Combined Inventory with Site Info by Calendar Week:")  # Announce menu 25 export scope
        ctx = OrgInventoryExporter._prepare_combined_inventory_context()  # Resolve org + customer + paths
        current_org_id, end_customer_name, end_customer_account_id, safe_org_name, output_folder = ctx
        OrgInventoryExporter.devices_with_site_info()  # Regenerate enriched inventory CSV first
        OrgInventoryExporter._export_combined_inventory_raw_json(output_folder, current_org_id)  # Diagnostic JSON
        all_devices = OrgInventoryExporter._load_combined_inventory_rows()  # Load enriched CSV rows
        site_configs, empty_vc_shells, duplicate_vc_entries = OrgInventoryExporter._partition_combined_inventory_rows(
            all_devices
        )  # Separate physical devices from virtual VC placeholders
        OrgInventoryExporter._log_combined_inventory_vc_summary(
            all_devices, site_configs, empty_vc_shells, duplicate_vc_entries
        )  # Surface physical-vs-virtual filtering details
        weekly_data, summary_data = OrgInventoryExporter._build_combined_inventory_weekly_data(
            site_configs, end_customer_name, end_customer_account_id
        )  # Group into per-week export buckets
        master_csv_filename, master_row_count = OrgInventoryExporter._emit_combined_inventory_outputs(
            output_folder, safe_org_name, site_configs, weekly_data, summary_data
        )
        OrgInventoryExporter._print_combined_inventory_summary(
            weekly_data, site_configs, master_csv_filename, master_row_count
        )  # Tell operator where the three output artifacts landed

    @staticmethod
    def _print_combined_inventory_summary(
        weekly_data: Any,
        site_configs: Any,
        master_csv_filename: str,
        master_row_count: int,
    ) -> None:
        """Print the three CombinedInventory output locations (weekly CSVs, summary, master) for the operator."""
        print(
            f"! {len(weekly_data)} weekly CSV files created in data/CombinedInventory_ByWeek/ folder ({len(site_configs)} total devices processed)"  # noqa: E501
        )  # Summarize weekly export output counts for the operator.
        print(
            "! Summary report exported to data/CombinedInventory_ByWeek/CombinedInventory_Summary.csv"
        )  # Confirm summary report location.
        print(
            f"! Master inventory exported to data/CombinedInventory_ByWeek/{master_csv_filename} ({master_row_count} devices)"  # noqa: E501
        )  # Confirm master report path and row count.

    @staticmethod
    def _build_site_lookup_from_api(org_id: str) -> dict:  # type: ignore[type-arg]
        """Fetch sites from the API and build an id -> {name, address} lookup map."""
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch sites from API.
        site_lookup = {  # Build site lookup from API rows.
            site["id"]: {"name": site.get("name", ""), "address": site.get("address", "")} for site in sites
        }
        logging.debug("Loaded %s sites for lookup.", len(site_lookup))  # Log loaded site count.
        return site_lookup  # Site id -> info map.

    @staticmethod
    def _load_site_lookup_from_cache(org_id: str) -> dict:  # type: ignore[type-arg]
        """Load the site lookup from cached SiteList.csv, falling back to the API on any read failure."""
        try:  # Cached CSV is preferred; fall back to the API if it is missing or unreadable.
            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # Resolve site CSV path.
            with open(site_list_path, encoding="utf-8") as file:  # Open cached site CSV.
                reader = csv.DictReader(file)  # Read site CSV rows.
                site_lookup = {  # Build site lookup from CSV rows.
                    row["id"]: {"name": row.get("name", ""), "address": row.get("address", "")} for row in reader
                }
            logging.debug("Loaded %s sites from cached SiteList.csv", len(site_lookup))  # Log loaded site count.
            return site_lookup  # Cached site lookup.
        except Exception as exception:  # Cached read failed.
            logging.warning("Failed to load from cached SiteList.csv, falling back to API: %s", exception)  # Warn.
            return OrgInventoryExporter._build_site_lookup_from_api(org_id)  # API fallback.

    @staticmethod
    def _load_inventory_from_cache(org_id: str) -> list:  # type: ignore[type-arg]
        """Load the org inventory from cached OrgInventory.csv, falling back to the API on any read failure."""
        try:  # Cached CSV is preferred; fall back to the API if it is missing or unreadable.
            inventory_path = FilePathUtils.get_csv_path("OrgInventory.csv")  # Resolve inventory CSV path.
            with open(inventory_path, encoding="utf-8") as file:  # Open cached inventory CSV.
                reader = csv.DictReader(file)  # Read inventory CSV rows.
                inventory = list(reader)  # Materialize inventory rows.
            logging.debug("Loaded %s devices from cached OrgInventory.csv", len(inventory))  # Log loaded device count.
            return inventory  # Cached inventory rows.
        except Exception as exception:  # Cached read failed.
            logging.warning("Failed to load from cached OrgInventory.csv, falling back to API: %s", exception)  # Warn.
            inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Fetch inventory from API.
            logging.debug("Loaded %s devices from API fallback", len(inventory))  # Log API fallback count.
            return inventory  # API fallback inventory rows.

    @staticmethod
    def _devices_load_data(org_id: str, fast: bool) -> tuple[dict, list]:  # type: ignore[type-arg]
        """Load (site_lookup, inventory): cached CSVs (with API fallback) in fast mode, else direct API."""
        if fast:  # Fast mode reuses cached CSVs to avoid redundant API calls.
            CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # Ensure site CSV cached.
            CacheUtils.check_and_generate_csv("OrgInventory.csv", OrgInventoryExporter.inventory)  # Ensure inv cached.
            site_lookup = OrgInventoryExporter._load_site_lookup_from_cache(org_id)  # Load sites from cache (or API).
            inventory = OrgInventoryExporter._load_inventory_from_cache(org_id)  # Load inventory from cache (or API).
            return site_lookup, inventory  # Cached data (with fallback already applied).
        site_lookup = OrgInventoryExporter._build_site_lookup_from_api(org_id)  # Non-fast: fetch sites from API.
        inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Non-fast: fetch inventory from API.
        logging.debug("Loaded %s devices from org inventory.", len(inventory))  # Log loaded device count.
        return site_lookup, inventory  # Direct-API data.

    @staticmethod
    def _build_mac_to_site_id(inventory: list) -> dict:  # type: ignore[type-arg]
        """Index every device's mac -> site_id so VC members without a site_id can inherit one from their parent.

        Physical VC members carry vc_mac but no site_id; that vc_mac may point at the virtual VC entry (020003* MAC)
        or the primary physical chassis MAC. Indexing ALL devices with a site_id covers both cases.
        """
        mac_to_site_id: dict[str, str] = {}  # Universal mac -> site_id lookup for inheritance.
        for device in inventory:  # Scan all inventory entries.
            mac = device.get("mac", "")  # Get device MAC address.
            if mac and device.get("site_id"):  # Any device with a site assignment.
                mac_to_site_id[mac] = device["site_id"]  # Index for vc_mac lookups.
        logging.info(  # Log the built index size.
            "Built mac->site_id lookup with %d entries for VC member site inheritance", len(mac_to_site_id)
        )
        return mac_to_site_id  # mac -> site_id inheritance map.

    @staticmethod
    def _enrich_one_device(device: dict, site_lookup: dict, mac_to_site_id: dict) -> bool:  # type: ignore[type-arg]
        """Attach site name/address + split-address fields to one device; return True if its site was VC-inherited."""
        site_id = device.get("site_id")  # Check if device has its own site_id.
        inherited = False  # Track whether this device inherited its site from a VC parent.
        if not site_id and device.get("vc_mac"):  # Device missing a site assignment but part of a VC.
            inherited_site_id = mac_to_site_id.get(device["vc_mac"])  # Look up site from the VC parent MAC.
            if inherited_site_id:  # Found the parent's site.
                site_id = inherited_site_id  # Use the parent's site_id for enrichment.
                device["site_id"] = inherited_site_id  # Persist inherited site_id on the device record.
                inherited = True  # Mark this device as having inherited its site.
        site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})  # Resolve site details.
        device["site_name"] = site_info["name"]  # Apply site name to device record.
        device["site_address"] = site_info["address"]  # Apply full site address to device record.
        street, city, state, zip_code, country = OrgInventoryExporter._split_full_address(
            site_info["address"]
        )  # Split.
        device["street"] = street  # Set street address component.
        device["city"] = city  # Set city component.
        device["state"] = state  # Set state/province component.
        device["zip_code"] = zip_code  # Set postal/zip code component.
        device["country"] = country  # Set country component.
        return inherited  # Whether the site was inherited from a VC parent.

    @staticmethod
    def _enrich_devices_with_site_info(inventory: list, site_lookup: dict, mac_to_site_id: dict) -> list:  # type: ignore[type-arg]
        """Enrich every device with site info (inheriting VC-member sites) and return the enriched list."""
        enriched_devices = []  # Init enriched device list.
        vc_inherited_count = 0  # Track how many physical members inherited site info from their VC.
        for device in tqdm(inventory, desc="Processing Devices", unit="device"):  # type: ignore[no-untyped-call]
            inherited = OrgInventoryExporter._enrich_one_device(device, site_lookup, mac_to_site_id)  # Enrich one.
            if inherited:  # The device inherited its site from a VC parent.
                vc_inherited_count += 1  # Count successful inheritance.
            enriched_devices.append(device)  # Add enriched device to output list.
            logging.debug("Enriched device %s (%s) with site info.", device.get("name", ""), device.get("mac", ""))
        if vc_inherited_count:  # Log inheritance summary if any members were fixed.
            logging.info("%d physical VC members inherited site info from their VC parent", vc_inherited_count)
        return enriched_devices  # Enriched device records.

    @staticmethod
    def _flatten_sort_export_devices(devices: list) -> list:  # type: ignore[type-arg]
        """Flatten, escape, sort by site name, and write the all-devices CSV; return the processed rows for display."""
        devices = DataProcessingUtils.flatten_nested_fields(devices)  # Flatten enriched fields.
        devices = DataProcessingUtils.escape_multiline(devices)  # type: ignore[no-untyped-call]
        devices = sorted(devices, key=lambda x: x.get("site_name", ""))  # Sort by site name.
        DataExporter.write_with_format_selection(devices, "AllDevicesWithSiteInfo.csv")  # type: ignore[no-untyped-call]
        print(f"! {len(devices)} devices exported to AllDevicesWithSiteInfo.csv")  # Confirm export to operator.
        logging.info("All device data written to AllDevicesWithSiteInfo.csv (%s records).", len(devices))  # Log write.
        return devices  # Processed rows for the summary table.

    @staticmethod
    def _display_devices_summary_table(devices: list) -> None:  # type: ignore[type-arg]
        """Build a PrettyTable of the enriched devices and debug-log it for operator visibility."""
        table = PrettyTable()  # Build display table.
        table.field_names = [  # Define table columns.
            "name",
            "mac",
            "model",
            "serial",
            "type",
            "site_name",
            "street",
            "city",
            "state",
            "zip_code",
            "country",
        ]
        for device in devices:  # Iterate enriched devices for rows.
            table.add_row([device.get(column, "") for column in table.field_names])  # One cell per defined column.
        logging.debug("\n%s", table.get_string())  # Debug-log the table.

    @staticmethod
    def devices_with_site_info(fast: bool = False):
        """Fetch all org devices, enrich them with site/address info, and export AllDevicesWithSiteInfo.csv.

        When ``fast`` is True, cached SiteList.csv / OrgInventory.csv are used (with API fallback); otherwise
        the data is fetched directly from the API. Physical VC members without a site_id inherit one from
        their VC parent. Also debug-logs a summary table.
        """
        print("All Devices with Site and Address Info:")  # Inform operator of export.
        logging.info("Fetching All Devices with Site Info...")  # Log fetch start.
        if fast:  # Fast mode reuses cached CSVs.
            logging.info(" Fast mode enabled for devices with site info export")  # Log fast mode enabled.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        site_lookup, inventory = OrgInventoryExporter._devices_load_data(org_id, fast)  # Load sites + inventory.
        mac_to_site_id = OrgInventoryExporter._build_mac_to_site_id(inventory)  # Build VC inheritance index.
        enriched_devices = OrgInventoryExporter._enrich_devices_with_site_info(  # Enrich every device with site info.
            inventory, site_lookup, mac_to_site_id
        )
        processed = OrgInventoryExporter._flatten_sort_export_devices(enriched_devices)  # Flatten/sort/write the CSV.
        OrgInventoryExporter._display_devices_summary_table(processed)  # Debug-log a summary table of the devices.

    @staticmethod
    def gateways_with_site_info():  # Export gateways with site info.
        """
        Fetches all gateway devices in the organization, enriches them with site and address info,
        and exports the result to GatewaysWithSiteInfo.csv. Also logs and displays a summary table.
        """
        print("Gateways with Site and Address Info:")  # Inform operator of export.
        logging.info("Fetching Gateways with Site Info...")  # Log fetch start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.

        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch sites from API.
        site_lookup = {site["id"]: {"name": site.get("name", ""), "address": site.get("address", "")} for site in sites}
        logging.debug("Loaded %s sites for lookup.", len(site_lookup))  # Log loaded site count.

        inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Fetch inventory from API.
        logging.debug("Loaded %s devices from org inventory.", len(inventory))  # Log loaded device count.

        gateways = OrgInventoryExporter._enrich_gateways_with_site_info(inventory, site_lookup)  # Filter + enrich
        logging.info("Enriched %s gateway devices with site info.", len(gateways))  # Log enriched gateway count.
        gateways = OrgInventoryExporter._flatten_sort_export_gateways(gateways)  # Flatten/sort/write CSV; returns rows
        OrgInventoryExporter._display_gateways_summary_table(gateways)  # Debug-log a PrettyTable of the gateways.

    @staticmethod
    def _flatten_sort_export_gateways(gateways: list) -> list:  # type: ignore[type-arg]  # Flatten/sort/write the CSV
        """Flatten, escape, sort by site name, and write the gateways CSV; return the processed rows for display."""
        gateways = DataProcessingUtils.flatten_nested_fields(gateways)  # Flatten gateway fields.
        gateways = DataProcessingUtils.escape_multiline(gateways)  # type: ignore[no-untyped-call]
        gateways = sorted(gateways, key=lambda x: x.get("site_name", ""))  # Sort by site name.
        DataExporter.write_with_format_selection(gateways, "GatewaysWithSiteInfo.csv")  # type: ignore[no-untyped-call]
        print(f"! {len(gateways)} gateways exported to GatewaysWithSiteInfo.csv")  # Confirm export to operator.
        logging.info("Gateway data written to GatewaysWithSiteInfo.csv")  # Log write success.
        return gateways  # Processed rows for the summary table

    @staticmethod
    def _split_full_address(address: str) -> tuple[str, str, str, str, str]:  # Parse address into parts.
        """Split a full address into (street, city, state, zip, country); raw street + blanks on parse failure."""
        try:
            parts = address.split(", ")  # Split on comma separators.
            state_zip = parts[2].split()  # Split state and zip.
            return parts[0], parts[1], state_zip[0], state_zip[1], parts[3]  # street, city, state, zip, country
        except Exception as exception:  # Catch parse errors.
            logging.debug("Failed to split address '%s': %s", address, exception)  # Log parse failure.
            return address, "", "", "", ""  # Return raw address fallback.

    @staticmethod
    def _enrich_gateways_with_site_info(inventory: list, site_lookup: dict) -> list:  # type: ignore[type-arg]
        """Filter inventory to gateways and attach site name/address plus split address fields to each."""
        gateways = []  # Init gateway list.
        for device in tqdm(inventory, desc="Processing Gateways", unit="device"):  # type: ignore[no-untyped-call]
            if device.get("type") != "gateway":  # Only gateways are enriched/exported
                continue  # Skip non-gateway devices
            site_id = device.get("site_id")  # Read device site id.
            site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})  # Look up site info.
            device["site_name"] = site_info["name"]  # Attach site name.
            device["site_address"] = site_info["address"]  # Attach site address.
            street, city, state, zip_code, country = OrgInventoryExporter._split_full_address(site_info["address"])
            device["street"] = street  # Attach street.
            device["city"] = city  # Attach city.
            device["state"] = state  # Attach state.
            device["zip_code"] = zip_code  # Attach zip code.
            device["country"] = country  # Attach country.
            gateways.append(device)  # Add gateway to list.
        return gateways  # Enriched gateway records

    @staticmethod
    def _display_gateways_summary_table(gateways: list) -> None:  # type: ignore[type-arg]  # Debug-log a table
        """Build a PrettyTable of the enriched gateways and debug-log it for operator visibility."""
        table = PrettyTable()  # Build display table.
        table.field_names = [  # Define table columns.
            "name",
            "mac",
            "model",
            "serial",
            "site_name",
            "street",
            "city",
            "state",
            "zip_code",
            "country",
        ]
        for gateway in gateways:  # Iterate gateways for rows.
            table.add_row(  # Add gateway row to table.
                [gateway.get(column, "") for column in table.field_names]  # One cell per defined column
            )
        logging.debug("\n%s", table.get_string())  # Debug-log the table.


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


class SiteExportUtils:  # Site export delegators.
    """Delegation wrapper for extracted site export implementation."""

    @staticmethod
    def _configure_module():  # Configure the export module.
        """Configure extracted module dependencies and return module handle."""
        from src.export import site_export_utils as site_export_module  # noqa: PLC0415,I001

        configure_site_export_utils_dependencies(  # Wire dependencies.
            apisession_dependency=apisession,
            prompt_utils=PromptUtils,
            config_utils=ConfigUtils,
            data_processing_utils=DataProcessingUtils,
            data_exporter=DataExporter,
            time_utils=TimeUtils,
            enhanced_ssh_runner=EnhancedSSHRunner,
            insight_metrics_utils=InsightMetricsUtils,
            packet_capture_manager=PacketCaptureManager,
            api_core_fetch_utils=APICoreFetchUtils,
            check_fn=IsDebugMode.check,
            pretty_table_class=PrettyTable,
            tqdm_module=tqdm,
            mistapi_dependency=mistapi,
        )
        return site_export_module  # Return the module.

    @staticmethod
    def _export_data(api_call, data_type, sort_key="name", **api_kwargs):  # Export a site endpoint.
        """Delegate generic site export flow to extracted module."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils._export_data(api_call, data_type, sort_key=sort_key, **api_kwargs)

    @staticmethod
    def insight_metrics():  # Export site insight metrics.
        """Menu #74 entry: configures deps then runs decomposed SiteMetricOperation."""
        SiteExportUtils._configure_module()  # Wire apisession / mistapi / DataExporter globals on the extracted module
        SiteMetricOperation.execute()  # Run the decomposed operation directly (no inheritance delegation)

    @staticmethod
    def device_insights():  # Export device insights.
        """Menu #76 entry: configures deps then runs decomposed DeviceMetricOperation."""
        SiteExportUtils._configure_module()  # Wire apisession / mistapi / DataExporter globals on the extracted module
        DeviceMetricOperation.execute()  # Run the decomposed operation directly (no inheritance delegation)

    @staticmethod
    def insights():  # Export site insights.
        """Menu #73 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.insights()  # Delegate the export.

    @staticmethod
    def _system_events():  # Export system events.
        """Delegated site system events export."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils._system_events()  # Delegate the export.

    @staticmethod
    def _fast_roam_events():  # Export fast-roam events.
        """Delegated site fast-roam events export."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils._fast_roam_events()  # Delegate the export.

    @staticmethod
    def ospf_stats():  # Export OSPF stats.
        """Menu #70 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.ospf_stats()  # Delegate the export.

    @staticmethod
    def mxedge_upgrade_status():  # Export Mist Edge upgrades.
        """Menu #71 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.mxedge_upgrade_status()  # Delegate the export.

    @staticmethod
    def auto_map_assignment_status():  # Export auto-map status.
        """Menu #72 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.auto_map_assignment_status()  # Delegate the export.

    @staticmethod
    def site_stats() -> None:  # Export site stats.
        """Menu #80 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.site_stats()  # Delegate the export.

    @staticmethod
    def gateway_metrics() -> None:  # Export gateway metrics.
        """Menu #81 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.gateway_metrics()  # Delegate the export.

    @staticmethod
    def switches_metrics() -> None:  # Export switch metrics.
        """Menu #82 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.switches_metrics()  # Delegate the export.

    @staticmethod
    def beacons_stats() -> None:  # Export beacon stats.
        """Menu #83 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.beacons_stats()  # Delegate the export.

    @staticmethod
    def wxrules_usage() -> None:  # Export WxRules usage.
        """Menu #84 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.wxrules_usage()  # Delegate the export.

    @staticmethod
    def assets_stats() -> None:  # Export asset stats.
        """Menu #85 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.assets_stats()  # Delegate the export.

    @staticmethod
    def current_channel_planning() -> None:  # Export channel planning.
        """Menu #86 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.current_channel_planning()  # Delegate the export.

    @staticmethod
    def zone_config_analysis() -> None:  # Export zone analysis.
        """Menu #6 delegated entrypoint."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils.zone_config_analysis()  # Delegate the export.

    @staticmethod
    def _classify_device_platform(device_model: str) -> str:  # Classify a device platform.
        """Delegate device platform classification helper."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils._classify_device_platform(device_model)  # Delegate the call.

    @staticmethod
    def _metric_supported_on_platform(metric_name: str, device_platform: str) -> bool:  # Check metric platform support.
        """Delegate metric/platform support check to the extracted SiteExportUtils impl."""
        module = SiteExportUtils._configure_module()  # resolve wired src module
        return module.SiteExportUtils._metric_compatible_with_platform(metric_name, device_platform)  # call src impl

    @staticmethod
    def _normalize_device_mac_or_none(device_mac: str) -> str | None:  # Normalize a device MAC.
        """Delegate device MAC normalization helper."""
        module = SiteExportUtils._configure_module()  # Configure the module.
        return module.SiteExportUtils._normalize_device_mac_or_none(device_mac)  # Delegate the call.


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


# ============================================================================
# INSIGHT METRICS UTILITIES CLASS
# ============================================================================
class InsightMetricsUtils:  # Insight-metrics helpers.
    """
    Utilities for working with Mist insight metrics.

    Provides functionality to export, filter, and normalize insight metrics data
    from the Mist API. All methods are static to avoid unnecessary instantiation.
    """

    @staticmethod
    def export_const_insight_metrics() -> None:  # Export const insight metrics.
        """
        Export available const insight metrics via the ConstDefinitionsExporter.

        Refreshes data/ConstInsightMetrics.csv so scope-filtering helpers can read it.
        """
        print("Export Available Insight Metrics:")  # User-facing banner for the const insight metrics export
        print("! Note: This function now uses the dynamic comprehensive const export system")  # Tell the user.
        print("! For best results, consider using Menu 82: Export All Const Definitions")  # Tell the user.
        logging.info("Legacy const insight metrics export called - using ConstDefinitionsExporter class")

        exporter = ConstDefinitionsExporter(apisession)  # type: ignore[no-untyped-call]
        exporter.export_all()  # Run the dynamic export.

        insight_metrics_file = os.path.join("data", "ConstInsightMetrics.csv")  # Expected output file.
        if os.path.exists(insight_metrics_file):  # File present.
            print("! ConstInsightMetrics.csv is available in the dynamic export results")  # Tell the user.
        else:
            print("! Warning: ConstInsightMetrics.csv was not created during dynamic export")

    @staticmethod
    def _should_skip_row(metric_name: str, scopes: str) -> bool:
        """Return True when a row is incomplete or uses a template-placeholder name."""
        if not metric_name or not scopes:  # Incomplete row — missing required fields
            return True
        return "{" in metric_name or "}" in metric_name  # Template placeholders are skip candidates

    @staticmethod
    def _row_matches_scope(row, normalized_target_scope: str) -> str | None:  # type: ignore[no-untyped-def]
        """Return ``metric_name`` when the row supports the target scope, else None to signal skip."""
        scopes = row.get("scopes", "")  # Scope string for this metric
        metric_name = row.get("metric_name", "")  # Display name
        if InsightMetricsUtils._should_skip_row(metric_name, scopes):  # Delegate skip-checks
            return None
        parsed_scopes = InsightMetricsUtils._parse_scopes(scopes)  # Tokenize scopes
        return metric_name if normalized_target_scope in parsed_scopes else None  # Match check

    @staticmethod
    def _collect_metrics_for_scope(reader, normalized_target_scope: str) -> list[str]:
        """Walk CSV rows and return metric names supporting the given scope."""
        matches = (InsightMetricsUtils._row_matches_scope(row, normalized_target_scope) for row in reader)  # Per-row
        return [name for name in matches if name]  # Drop None skips

    @staticmethod
    def get_by_scope(target_scope: str) -> list[str]:  # List metrics for a scope.
        """Read ConstInsightMetrics.csv and return metrics supporting ``target_scope``."""
        csv_path = os.path.join("data", "ConstInsightMetrics.csv")  # CSV path.
        normalized_target_scope = (target_scope or "").strip().lower()  # Normalize the target scope.
        try:
            if not os.path.exists(csv_path):  # File missing.
                logging.warning("ConstInsightMetrics.csv not found at %s", csv_path)  # Warn it is missing.
                return []  # Return empty.
            with open(csv_path, encoding="utf-8") as csvfile:  # Open the CSV.
                reader = csv.DictReader(csvfile)  # Parse rows.
                metrics_for_scope = InsightMetricsUtils._collect_metrics_for_scope(reader, normalized_target_scope)
            logging.debug(  # Trace the count.
                "Found %s metrics for scope '%s': %s", len(metrics_for_scope), target_scope, metrics_for_scope
            )
            return metrics_for_scope  # Return the metrics.
        except Exception as exception:  # Read failed.
            logging.error("Error reading ConstInsightMetrics.csv: %s", exception)  # Log the error.
            return []  # Return empty.

    @staticmethod
    def _parse_scopes(scopes_text: str) -> set[str]:  # Parse a scopes string.
        """Parse scope strings from CSV into normalized tokens."""
        if not scopes_text:  # Empty input.
            return set()  # Empty set.
        normalized = scopes_text.strip().lower()  # Lowercase it.
        normalized = normalized.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
        normalized = normalized.replace(";", ",")  # Normalize separators.
        tokens = [token.strip() for token in normalized.split(",") if token.strip()]  # Split into tokens.
        return set(tokens)  # Return the token set.

    @staticmethod
    def _log_normalization_summary(metric_type: str, normalized_data: dict[str, list]) -> None:  # type: ignore[type-arg]
        """Emit debug trace of normalized metric counts per bucket."""
        logging.debug(  # Trace the parse.
            "Normalized metric %s: %s summary, %s time series, %s results, %s sites",
            metric_type,  # Metric type label.
            len(normalized_data["summary"]),  # Summary row count.
            len(normalized_data["time_series"]),  # Time series row count.
            len(normalized_data["results"]),  # Results row count.
            len(normalized_data["sites_data"]),  # Sites row count.
        )

    @staticmethod
    def parse_to_normalized_data(metric_data: dict, org_id: str) -> dict[str, list]:  # type: ignore[type-arg]
        """Parse one insight metric into 'summary'/'time_series'/'results'/'sites_data' lists."""
        normalized_data: dict[str, list] = {"summary": [], "time_series": [], "results": [], "sites_data": []}  # type: ignore[type-arg]
        try:
            metric_type = metric_data.get("metric_type", "unknown")  # Read the metric type.
            normalized_data["summary"].append(  # Add summary record.
                InsightMetricsUtils._extract_summary(metric_data, org_id, metric_type)
            )
            normalized_data["time_series"].extend(  # Add time series rows.
                InsightMetricsUtils._extract_time_series(metric_data, org_id, metric_type)
            )
            normalized_data["results"] = InsightMetricsUtils._extract_results(metric_data, org_id, metric_type)
            normalized_data["sites_data"] = InsightMetricsUtils._extract_sites_data(metric_data, org_id, metric_type)
            InsightMetricsUtils._log_normalization_summary(metric_type, normalized_data)  # Trace counts.
        except Exception as exception:  # Parse failed.
            logging.error("Error parsing insight metric data: %s", exception)  # Log the error.
            logging.debug("Failed metric data structure: %s", metric_data)  # Trace the structure.
        return normalized_data  # Return normalized data.

    SUMMARY_SCALAR_FIELDS = (  # Scalar fields copied verbatim from the raw metric payload.
        "ap-health",
        "ap-redundancy",
        "capacity",
        "coverage",
        "num_active_wan_tunnels",
        "num_aps",
        "num_auth",
        "num_auth_failure",
        "num_auth_total",
        "num_client",
        "num_clients",
        "num_gateways",
        "num_mdm_client",
        "num_mxedges",
        "num_mxtunnels",
        "num_nac_clients",
        "num_switches",
        "num_wan_clients",
        "num_wired_clients",
        "successful-connect",
        "throughput",
        "time-to-connect",
    )

    @staticmethod
    def _build_summary_base(metric_data: dict, org_id: str, metric_type: str) -> dict:  # type: ignore[type-arg]
        """Build the fixed-key portion of the summary record (org/metric metadata)."""
        return {  # Header fields common to every metric type.
            "org_id": org_id,  # Tenant org id.
            "metric_type": metric_type,  # Logical metric name.
            "data_source": metric_data.get("data_source", ""),  # API data source.
            "start_time": metric_data.get("start", ""),  # Window start epoch.
            "end_time": metric_data.get("end", ""),  # Window end epoch.
            "interval_seconds": metric_data.get("interval", ""),  # Bucket interval.
            "limit": metric_data.get("limit", ""),  # Page limit echoed back.
            "total_sites": metric_data.get("total_sites", ""),  # Total sites count.
            "page": metric_data.get("page", ""),  # Current page index.
            "sle_category": metric_data.get("sle_category", ""),  # SLE category, if any.
            "original_metric": metric_data.get("original_metric", ""),  # Original metric key.
            "roaming": metric_data.get("roaming", ""),  # Roaming subtotal.
            "total": metric_data.get("total", ""),  # Total counter.
            "totalTunnelCount": metric_data.get("totalTunnelCount", ""),  # Tunnel count.
        }

    @staticmethod
    def _extract_summary(metric_data: dict, org_id: str, metric_type: str) -> dict:  # type: ignore[type-arg]
        """Extract summary data from metric."""
        summary_data = InsightMetricsUtils._build_summary_base(metric_data, org_id, metric_type)  # Header.
        for field_name in InsightMetricsUtils.SUMMARY_SCALAR_FIELDS:  # Append present scalars.
            if field_name in metric_data:  # Field present.
                summary_data[field_name] = metric_data[field_name]  # Copy the value.
        return summary_data  # Return the summary.

    @staticmethod
    def _extract_time_series(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract time series data from metric."""
        time_series_records = []  # type: ignore[var-annotated]

        rt_field = metric_data.get("rt", "")  # Read the rt field.
        if not InsightMetricsUtils._is_csv_string(rt_field):  # Not a CSV series.
            return time_series_records  # No time-series.

        timestamps = rt_field.split(",")  # Split the timestamps.
        time_series_fields = ["num_clients", "num_aps", "num_gateways", "num_switches", "num_mxedges", "num_mxtunnels"]

        for field_name in time_series_fields:  # Walk each field.
            field_data = metric_data.get(field_name, "")  # Read the field.
            time_series_records.extend(  # Append this field's time-series points (empty when not a CSV series)
                InsightMetricsUtils._field_time_series_points(field_name, field_data, timestamps, org_id, metric_type)
            )

        return time_series_records  # Return the series.

    @staticmethod
    def _is_csv_string(value: Any) -> bool:  # Detect a non-empty comma-separated string
        """Return True when value is a non-empty string containing at least one comma (a CSV series)."""
        return bool(value and isinstance(value, str) and "," in value)  # Truthy + str + contains a comma

    @staticmethod
    def _field_time_series_points(
        field_name: str,
        field_data: Any,
        timestamps: list[str],
        org_id: str,
        metric_type: str,
    ) -> list[dict]:  # type: ignore[type-arg]
        """Pair one CSV field's values with the timestamps into time-series point records (skipping empties)."""
        if not InsightMetricsUtils._is_csv_string(field_data):  # Not a CSV series.
            return []  # No points for this field.
        values = field_data.split(",")  # Split the values.
        points = []  # Collect this field's points.
        for index, (timestamp, value) in enumerate(zip(timestamps, values, strict=False)):  # Pair timestamp+value
            if value and value != "None":  # Skip empty/placeholder values.
                points.append(  # Collect the point.
                    {
                        "org_id": org_id,
                        "metric_type": metric_type,
                        "timestamp": timestamp.strip(),
                        "value": value.strip(),
                        "value_type": field_name,
                        "sequence_order": index,
                    }
                )
        return points  # Time-series points for this field.

    @staticmethod
    def _parse_results_key(key: str) -> tuple[str, str] | None:
        """Split a 'results_<index>_<field>' key into (index, field); return None if pattern fails."""
        if not (key.startswith("results_") and "_" in key):  # Only results_* keys are valid here.
            return None  # Reject non-matching keys.
        parts = key.split("_", 2)  # Split into at most 3 parts: ['results', index, field].
        if len(parts) < 3:  # Too few parts -- no field component.
            return None  # Reject malformed keys.
        return parts[1], parts[2]  # (index, field).

    @staticmethod
    def _ensure_result_row(
        results_data: list[dict],  # type: ignore[type-arg]
        result_index,  # type: ignore[no-untyped-def]
        org_id: str,
        metric_type: str,
    ) -> dict:
        """Return the existing row matching ``result_index`` from ``results_data`` or append+return a new one."""
        existing = next((r for r in results_data if r["result_index"] == result_index), None)  # Lookup
        if existing is not None:  # Reuse existing row
            return existing
        new_row = {  # New row with normalized index
            "org_id": org_id,
            "metric_type": metric_type,
            "result_index": int(result_index) if result_index.isdigit() else result_index,
        }
        results_data.append(new_row)  # Append into caller-owned list
        return new_row

    @staticmethod
    def _extract_results(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract results array data from metric."""
        results_data: list[dict] = []  # Accumulator
        for key, value in metric_data.items():  # Walk metric fields
            parsed = InsightMetricsUtils._parse_results_key(key)  # Parse the key shape
            if parsed is None:  # Not a results_* field
                continue
            result_index, result_field = parsed  # Unpack
            row = InsightMetricsUtils._ensure_result_row(results_data, result_index, org_id, metric_type)
            row[result_field] = value  # Set the field on the row
        return results_data

    @staticmethod
    def _extract_sites_data(metric_data: dict, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Extract sites data from metric."""
        sites_data = metric_data.get("sites_data", [])  # Read sites data.
        sites_records = InsightMetricsUtils._extract_sites_list(sites_data, org_id, metric_type)  # List-payload rows
        InsightMetricsUtils._merge_keyed_sites(metric_data, org_id, metric_type, sites_records)  # Merge sites_data_*
        return sites_records  # Return the sites.

    @staticmethod
    def _extract_sites_list(sites_data: Any, org_id: str, metric_type: str) -> list[dict]:  # type: ignore[type-arg]
        """Build site rows from a list-payload sites_data, tagging each dict site with org_id/metric_type."""
        sites_records = []  # Collect site rows.
        if isinstance(sites_data, list):  # List payload.
            for site_data in sites_data:  # Walk sites.
                if isinstance(site_data, dict):  # Dict site.
                    site_record = {"org_id": org_id, "metric_type": metric_type}  # Tag the site.
                    site_record.update(site_data)  # Merge the data.
                    sites_records.append(site_record)  # Collect the row.
        return sites_records  # Site rows from the list payload.

    @staticmethod
    def _merge_keyed_sites(
        metric_data: dict,  # type: ignore[type-arg]
        org_id: str,
        metric_type: str,
        sites_records: list[dict],  # type: ignore[type-arg]
    ) -> None:
        """Merge flattened sites_data_* keys into sites_records (find-or-create each site by index)."""
        for key, value in metric_data.items():  # Walk metric fields.
            parsed = InsightMetricsUtils._parse_keyed_site_field(key)  # (site_index, site_field) or None to skip
            if parsed is None:  # Not a sites_data_* field.
                continue  # Skip it.
            site_index, site_field = parsed  # Unpack the parsed index/field.
            site = InsightMetricsUtils._find_or_create_site(sites_records, site_index, org_id, metric_type)  # Find row
            site[site_field] = value  # Set the field.

    @staticmethod
    def _parse_keyed_site_field(key: str) -> tuple[str, str] | None:  # Parse a sites_data_* flattened key
        """Return (site_index, site_field) for a sites_data_* key, or None when the key is not a valid site field."""
        if not (key.startswith("sites_data_") and "_" in key):  # Only sites_data_* keys.
            return None  # Not a site field.
        parts = key.split("_", 2)  # Split the key.
        if len(parts) < 3:  # Too few parts.
            return None  # Skip it.
        site_index = parts[2]  # Site index.
        site_field = parts[3] if len(parts) > 3 else "value"  # Site field (defaults to 'value').
        return site_index, site_field  # Parsed index and field.

    @staticmethod
    def _find_or_create_site(
        sites_records: list[dict],  # type: ignore[type-arg]
        site_index: str,
        org_id: str,
        metric_type: str,
    ) -> dict:  # type: ignore[type-arg]
        """Return the existing site row matching site_index+metric_type, or create, append, and return a new one."""
        existing_site = next(  # Find existing site.
            (s for s in sites_records if s.get("site_index") == site_index and s.get("metric_type") == metric_type),
            None,
        )
        if existing_site is not None:  # Found a matching row.
            return existing_site  # Reuse it.
        new_site = {"org_id": org_id, "metric_type": metric_type, "site_index": site_index}  # Start a new site.
        sites_records.append(new_site)  # Collect it.
        return new_site  # The newly created row.


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


class GatewayStatsExporter:  # Gateway stats delegators.
    """Delegation wrapper for extracted gateway stats exporter implementation."""

    @staticmethod
    def _configure_module():  # Configure the module.
        """Configure extracted gateway modules and return stats module handle."""
        from src.gateway import gateway_stats_exporter as stats_module  # noqa: PLC0415,I001

        GatewayExportUtils._configure_module()  # Wire dependencies.
        return stats_module  # Return the module.

    @staticmethod
    def device_stats(fast=False):  # Export gateway device stats.
        """Delegated gateway device stats export entrypoint."""
        module = GatewayStatsExporter._configure_module()  # Configure the module.
        return module.GatewayStatsExporter.device_stats(fast=fast)  # Delegate the export.

    @staticmethod
    def device_stats_with_freshness(fast: bool = False) -> None:  # Export with freshness.
        """Delegated freshness-aware gateway device stats export entrypoint."""
        module = GatewayStatsExporter._configure_module()  # Configure the module.
        return module.GatewayStatsExporter.device_stats_with_freshness(fast=fast)  # Delegate the export.

    @staticmethod
    def wan_port_conflicts():  # Export WAN port conflicts.
        """Delegated WAN port conflict analysis entrypoint."""
        module = GatewayStatsExporter._configure_module()  # Configure the module.
        return module.GatewayStatsExporter.wan_port_conflicts()  # Delegate the export.


class GatewayExportUtils:  # Gateway export delegators.
    """Delegation wrapper for extracted gateway export utility implementation."""

    @staticmethod
    @staticmethod
    def _gateway_export_dependency_kwargs() -> dict:
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
            execute_fn=ConnectionPoolExecutor.execute,  # Pool executor (1012 SC-003; renamed from connection_pool_fn).
            validation_utils=ValidationUtils,  # Input validation.
            rate_limiting_utils=RateLimitingUtils,  # Adaptive delay.
            mist_wan_target_ports=MistWanTargetPorts.VALUE,  # Port list from extracted class attribute.
            mist_site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,  # Site filter prefix.
            fast_mode_max_retries=FAST_MODE_MAX_RETRIES,  # Retry cap.
            fast_mode_retry_delay=FAST_MODE_RETRY_DELAY,  # Delay between retries.
            api_usage_cache=_api_usage_cache,  # Shared API usage cache.
            tqdm_module=tqdm,  # Progress bar dependency.
        )

    @staticmethod
    def _configure_module():  # Configure the module.
        """Configure extracted gateway modules and return gateway export module handle."""
        from src.gateway import gateway_export_utils as gateway_export_module  # noqa: PLC0415,I001

        configure_gateway_export_utils_dependencies(**GatewayExportUtils._gateway_export_dependency_kwargs())
        return gateway_export_module  # Return the module.

    @staticmethod
    def _with_site_info():  # Attach site info.
        """Delegated gateways-with-site-info export entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils._with_site_info()  # Delegate the call.

    @staticmethod
    def management_ips(fast: bool = False) -> None:  # Export management IPs.
        """Delegated gateway management IPs export entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils.management_ips(fast=fast)  # Delegate the export.

    @staticmethod
    def device_configs(debug: bool = False, fast: bool = False) -> None:  # Export device configs.
        """Delegated gateway device configs export entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils.device_configs(debug=debug, fast=fast)  # Delegate the export.

    @staticmethod
    def templates():  # Export gateway templates.
        """Delegated gateway template export entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils.templates()  # Delegate the export.

    @staticmethod
    def with_wan_overrides(fast: bool = False) -> None:  # Export with WAN overrides.
        """Delegated gateway WAN override analysis entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils.with_wan_overrides(fast=fast)  # Delegate the export.

    @staticmethod
    def _get_devices_with_sites(org_id: str, fast: bool = False) -> list[tuple[str, str, str, str]]:
        """Delegated gateway device+site inventory helper entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils._get_devices_with_sites(org_id, fast=fast)  # Delegate the call.

    @staticmethod
    def _get_devices_from_cache() -> list[tuple[str, str, str, str]]:  # List gateways from cache.
        """Delegated cached gateway inventory helper entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils._get_devices_from_cache()  # Delegate the call.

    @staticmethod
    def _get_devices_from_api(org_id: str) -> list[tuple[str, str, str, str]]:  # List gateways from API.
        """Delegated API-based gateway inventory helper entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils._get_devices_from_api(org_id)  # Delegate the call.

    @staticmethod
    def _get_site_ids_with_devices(org_id: str) -> list[str]:  # List sites with devices.
        """Delegated site-ID-with-gateway helper entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils._get_site_ids_with_devices(org_id)  # Delegate the call.

    @staticmethod
    def wan2_variable_migration(fast: bool = False, dry_run: bool = False) -> None:  # Migrate WAN2 variables.
        """Delegated WAN2 variable migration entrypoint."""
        module = GatewayExportUtils._configure_module()  # Configure the module.
        return module.GatewayExportUtils.wan2_variable_migration(fast=fast, dry_run=dry_run)  # Delegate the migration.


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
# SSH RUNNER MANAGER CLASS
# ============================================================================
class SSHRunnerManager:  # SSH runner delegators.
    """Delegation wrapper for extracted SSH runner manager implementation."""

    @staticmethod
    def _build_deps() -> SSHRunnerManagerDeps:  # Build the deps bundle.
        """Build dependency container for extracted SSH runner logic."""
        cli_args = globals().get("args") if "args" in globals() else None  # Read parsed CLI args.
        return SSHRunnerManagerDeps(  # Assemble the deps.
            args=cli_args,
            progress_emitter=PROGRESS_EMITTER,
            enhanced_ssh_runner=EnhancedSSHRunner,
            input_utils=InputUtils,
            cache_utils=CacheUtils,
            gateway_export_utils=GatewayExportUtils,
            file_path_utils=FilePathUtils,
        )

    @staticmethod
    def interactive():  # Run interactive SSH.
        """Delegated interactive SSH runner entrypoint."""
        return ExtractedSSHRunnerManager.interactive(SSHRunnerManager._build_deps())  # Delegate to the impl.

    @staticmethod
    def _load_gateway_data():  # Load gateway data.
        """Delegated helper to load gateway management data."""
        return ExtractedSSHRunnerManager._load_gateway_data(SSHRunnerManager._build_deps())  # Delegate to the impl.


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
class VirtualChassisManager:  # Virtual chassis manager.
    """Virtual chassis to virtual MAC conversion operations (Menus 92-94).

    Implementation extracted to src/device/virtual_chassis.py.
    This stub delegates to the extracted module while providing
    access to MistHelper globals (apisession, utility classes).
    """

    @staticmethod
    def convert_single(dry_run: bool = False) -> None:  # Convert a single VC.
        """Convert a single VC switch to virtual MAC (Menu 92)."""
        from src.device.virtual_chassis import (  # Import the impl.
            VCIODeps,
        )
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        io_deps = VCIODeps(  # Bundle IO/cache dependencies to satisfy the 5-param limit.
            get_csv_path_fn=FilePathUtils.get_csv_path,  # Resolve cache paths.
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,  # Refresh cached CSV.
            inventory_generator=OrgInventoryExporter.inventory,  # Rebuild OrgInventory.csv.
            sites_generator=OrgSiteExporter.sites,  # Rebuild SiteList.csv (unused here).
        )
        _VC.convert_single(  # Delegate the conversion.
            apisession=apisession,
            io_deps=io_deps,
            safe_input_fn=InputUtils.safe_input,
            select_site_fn=PromptUtils.select_site,
            dry_run=dry_run,
        )

    @staticmethod
    def convert_by_site_list() -> None:  # Convert by site list.
        """Bulk convert VC switches from site list CSV (Menu 93)."""
        from src.device.virtual_chassis import (  # Import the impl.
            VCIODeps,
        )
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        io_deps = VCIODeps(  # Bundle IO/cache dependencies for the bulk path.
            get_csv_path_fn=FilePathUtils.get_csv_path,  # Cache path resolver.
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,  # Refresh cached CSV.
            inventory_generator=OrgInventoryExporter.inventory,  # Rebuild OrgInventory.csv.
            sites_generator=OrgSiteExporter.sites,  # Rebuild SiteList.csv.
            create_csv_template_fn=FilePathUtils.create_csv_template,  # Write empty VCConvert.CSV.
        )
        _VC.convert_by_site_list(  # Delegate the conversion.
            apisession=apisession,
            io_deps=io_deps,
            safe_input_fn=InputUtils.safe_input,
        )

    @staticmethod
    def check_status() -> None:  # Check VC status.
        """Check conversion status of all VC switches (Menu 94)."""
        from src.device.virtual_chassis import (  # Import the impl.
            VCExportDeps,
            VCIODeps,
        )
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        io_deps = VCIODeps(  # Bundle IO/cache dependencies.
            get_csv_path_fn=FilePathUtils.get_csv_path,  # Cache path resolver.
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,  # Refresh cached CSV.
            inventory_generator=OrgInventoryExporter.inventory,  # Rebuild OrgInventory.csv.
            sites_generator=OrgSiteExporter.sites,  # Rebuild SiteList.csv.
        )
        export_deps = VCExportDeps(  # Bundle export dependencies.
            flatten_fields_fn=DataProcessingUtils.flatten_nested_fields,  # Flatten nested rows.
            escape_multiline_fn=DataProcessingUtils.escape_multiline,  # Escape multiline content.
            save_data_fn=DataExporter.write_with_format_selection,  # Physical writer.
        )
        _VC.check_status(io_deps=io_deps, export_deps=export_deps)  # Delegate the check.


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


menu_actions = {
    # ==============================
    # SYSTEM OPERATIONS
    # ==============================
    "0": (lambda: sys.exit(0), "Exit MistHelper"),
    # ==============================
    # SITE ADDRESS AUDIT (read-only)
    # ==============================
    "195": (
        lambda: AddressAuditEngine().run(apisession, ConfigUtils.get_cached_or_prompted_org_id()),  # type: ignore[misc]
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
        lambda fast=False: GatewayExportUtils.management_ips(fast=fast),  # type: ignore[misc]
        "Export gateway management overlay IPs grouped by template association",
    ),
    # > WebSocket Device Commands
    "102": (
        lambda: MacTableCommand.execute(_ws_cmd_deps()),  # type: ignore[misc]
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
        lambda: PacketCaptureManager(  # type: ignore[no-untyped-call]
            apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).start_site_packet_capture(),
        "Start Site Packet Capture - Wireless/Wired/Gateway/Scan captures with WebSocket streaming",
    ),
    "135": (
        lambda: PacketCaptureManager(  # type: ignore[no-untyped-call]
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
        lambda: (OrgSiteExporter.current_guests(), OrgSiteExporter.historical_guests()),  # type: ignore[no-untyped-call]
        "Export all current guest users and last 7 days of historical guests to CSV",
    ),
    "17": (OrgDeviceStatsExporter.switch_vc_stats, "Export all switch virtual chassis (VC/stacking) stats to CSV"),
    "12": (
        OrgInventoryExporter.combined_inventory_with_site_info,
        "Export combined inventory with site and address info by calendar week",
    ),
    "32": (GatewayExportUtils.templates, "Export gateway templates from the organization"),
    "3": (
        OrgSiteExporter.sites_list_api,
        "Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present)",
    ),
    "35": (
        lambda fast=False: GatewayExportUtils.with_wan_overrides(fast=fast),  # type: ignore[misc]
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
    "73": (SiteExportUtils.insights, "Export SLE (Service Level Experience) metrics insights for a selected site"),
    # ==============================
    # GATEWAY TEMPLATE VARIABLE OPERATIONS
    # ==============================
    "149": (
        lambda: WAN2MigrationLauncher().launch(),  # type: ignore[no-untyped-call]
        "Set WAN2 Interface Site Variable - Configure 'wan2_interface' site variable for template-based WAN migration (Reports sites with ge-0/0/1 overrides)",  # noqa: E501
    ),
    "163": (
        lambda fast=False, dry_run=False: GatewayExportUtils.wan2_variable_migration(fast=fast, dry_run=dry_run),  # type: ignore[misc]
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
        lambda: SwitchToInteractiveLoginManager().run(),  # type: ignore[no-untyped-call]
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
        lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: InventoryCSVComparator(  # type: ignore[misc]
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
        GatewayExportUtils.device_configs,
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
        lambda dry_run=False: VirtualChassisManager.convert_single(dry_run=dry_run),  # type: ignore[misc]
        " DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive, supports --dry-run)",
    ),
    "162": (
        VirtualChassisManager.convert_by_site_list,
        " DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation)",
    ),
    "14": (
        VirtualChassisManager.check_status,
        "Check virtual chassis to virtual MAC conversion status for all switches",
    ),
    "18": (
        lambda fast=False: GatewayStatsExporter.device_stats_with_freshness(fast=fast),  # type: ignore[misc]
        "Export detailed device statistics for all gateways (with freshness check)",
    ),
    "36": (
        GatewayStatsExporter.wan_port_conflicts,
        "Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2)",
    ),
    "175": (
        SSHRunnerManager.interactive,
        "Enhanced SSH Command Runner - Execute commands on remote network devices via SSH",
    ),
    "176": (
        # Wire menu directly to extracted SSH runner impl (facade wrapper removed).
        lambda: ExtractedSSHRunnerManager.by_gateway_template(SSHRunnerManager._build_deps()),
        "SSH Runner - Target gateways by template name (online gateways with management IPs only)",
    ),
    # ==============================
    # INSIGHTS API OPERATIONS - Organization & Site Analytics
    # ==============================
    "51": (OrgExportUtils.sle_metrics, "Export Organization SLE Metrics (Service Level Experience)"),
    "52": (OrgExportUtils.sites_sle_summary, "Export SLE summary metrics for all sites in the organization"),
    "74": (SiteExportUtils.insight_metrics, "Export general insight metrics for a selected site"),
    "75": (SiteClientExporter.client_insights, "Export client-specific insight metrics for a selected site"),
    "76": (SiteExportUtils.device_insights, "Export device-specific insight metrics for a selected site"),
    "54": (
        lambda: ConstDefinitionsExporter(apisession).export_all(),  # type: ignore[no-untyped-call]
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
        lambda: PingDeviceExecutor().execute(_ws_cmd_deps()),  # type: ignore[misc]
        "WebSocket Device Ping - Execute ping command on device via WebSocket stream (real-time output)",
    ),
    "119": (
        lambda: ArpDeviceExecutor().execute(_ws_cmd_deps()),  # type: ignore[misc]
        "WebSocket Device ARP - Execute ARP command on device via WebSocket stream (real-time output)",
    ),
    "120": (
        lambda: ServicePingLauncher().launch(),  # type: ignore[misc]
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
        lambda: TUILauncher().launch(),  # type: ignore[no-untyped-call]
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
        lambda dry_run=False: WANProbeConfigManager.configure(dry_run=dry_run),  # type: ignore[misc]
        " DESTRUCTIVE: Configure WAN Probe Override on Gateway Templates - Set ICMP probe IPs and profile for all WAN interfaces (Requires uppercase 'APPLY' confirmation, supports --dry-run)",  # noqa: E501
    ),
    "167": (
        lambda dry_run=False: WANProbeDeviceOverrideManager.configure(dry_run=dry_run),  # type: ignore[misc]
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
        SiteExportUtils.zone_config_analysis,
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
        lambda dry_run=False: BulkRadiusWLANConfigManager().manage(dry_run=dry_run),  # type: ignore[misc]
        "Bulk RADIUS WLAN Configuration - Configure auth_servers_timeout, auth_servers_retries, fast_dot1x_timers for org-level RADIUS WLANs",  # noqa: E501
    ),
    # ==============================
    # MAPS MANAGER (External Module)
    # ==============================
    "142": (
        lambda: MapsManagerLauncher().launch(),  # type: ignore[no-untyped-call]
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
    "70": (SiteExportUtils.ospf_stats, "Export OSPF adjacency statistics for a selected site"),
    "71": (SiteExportUtils.mxedge_upgrade_status, "Export MxEdge upgrade status for a selected site"),
    "72": (SiteExportUtils.auto_map_assignment_status, "Export auto-map assignment status for a selected site"),
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
    "80": (SiteExportUtils.site_stats, "Export site aggregate health & capacity statistics"),
    "81": (SiteExportUtils.gateway_metrics, "Export site gateway performance metrics summary"),
    "82": (SiteExportUtils.switches_metrics, "Export site switch performance metrics summary"),
    "83": (SiteExportUtils.beacons_stats, "Export site BLE beacon statistics"),
    "84": (SiteExportUtils.wxrules_usage, "Export site WxLAN rule usage statistics"),
    "85": (SiteExportUtils.assets_stats, "Export site asset statistics"),
    "86": (SiteExportUtils.current_channel_planning, "Export current RRM channel & power plan per AP radio"),
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
        sig = inspect.signature(func)  # type: ignore[arg-type]  # Detect optional 'fast' parameter
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
        func(**invoke_kwargs)  # type: ignore[operator, no-untyped-call]  # Call menu action
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


def _launch_web_portal(args):
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
    logging.debug("_establish_mist_session: starting session initialization")  # Log entry
    if args.login:  # Interactive login requested via --login flag
        logging.info("Interactive login mode requested via --login flag")  # Log before interactive login
        if not MistSessionInteractiveInitializer.initialize():  # Attempt email/password login
            logging.error("Failed to initialize Mist API session via interactive login")  # Log auth failure
            print(" Failed to initialize Mist API session. Check your credentials.")  # Inform user
            sys.exit(1)  # Exit -- cannot proceed without authenticated session
    else:  # Default path: use API token from .env or environment variables
        if not MistSessionInitializer.initialize():  # Attempt token-based session init
            logging.error("Failed to initialize Mist API session")  # Log token auth failure
            print(" Failed to initialize Mist API session. Check your credentials.")  # Inform user
            sys.exit(1)  # Exit -- cannot proceed without authenticated session
        detect_msp_privileges()  # type: ignore[no-untyped-call]  # Check if token has MSP-level scope
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

        tui = MistHelperTUI(debug_mode=args.debug)  # type: ignore[no-untyped-call]  # Create TUI with debug flag
        tui.apisession = apisession  # Pass global API session so TUI can execute live API calls
        if args.debug:  # Debug: record that TUI was launched with debug enabled
            logging.debug("TUI_MODE: Debug mode is ACTIVE - enhanced logging enabled")  # Log debug state
        tui.run()  # type: ignore[no-untyped-call]  # Launch TUI event loop (blocks until user exits)
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
        return args.org  # Return the CLI org ID.
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
    return device_id  # Return the resolved device_id.


def _dispatch_cli_menu_action(args: argparse.Namespace, site_id: str | None, device_id: str | None) -> None:
    """Look up args.menu in menu_actions, build kwargs, call the target. Exits 0/1 -- never returns on success."""
    if args.menu not in menu_actions:  # Invalid menu number -- abort with error.
        logging.error("! Invalid menu option: %s", args.menu)  # Log invalid menu selection.
        print(f"! Invalid menu option: {args.menu}")  # Inform user of bad menu number.
        sys.exit(1)  # Exit with error code on invalid menu option.
    func, _ = menu_actions[args.menu]  # Extract callable from menu_actions dispatch table.
    logging.info("Executing menu action '%s'.", args.menu)  # Log before function dispatch.
    func_args = _build_cli_func_kwargs(args, site_id, device_id)  # Build the full candidate kwargs dict.
    sig = inspect.signature(func)  # type: ignore[arg-type]  # Introspect signature to keep only valid kwargs.
    accepted_args = {
        k: v for k, v in func_args.items() if k in sig.parameters and v is not None
    }  # Filter to accepted params.
    func(**accepted_args)  # type: ignore[operator, no-untyped-call]  # Call menu function with filtered args.
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
        func()  # type: ignore[operator, no-untyped-call]  # Execute the selected menu function.
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
    _launch_web_portal(args)  # type: ignore[no-untyped-call]  # Blocks until shutdown
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
