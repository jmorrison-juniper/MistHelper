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
import functools  # Import functools for partial-binding apisession to connection-pool worker callables
import ipaddress  # Import ipaddress for parsing and validating IP addresses in device/client data
import logging  # Import logging for structured logging to script.log and console
import os  # Import os for file path operations, environment variables, and data/ directory setup
import re  # Import re for regex pattern matching in data parsing (SSIDs, descriptions, etc.)
import subprocess  # nosec B404  # Import subprocess for executing external commands (SSH, JSON parsing) with security review
import time  # Import time for rate limiting, delays, and performance monitoring
import traceback  # Import traceback for detailed exception context in error logs
from collections.abc import Callable  # Import Callable type hint for callback functions passed to API methods
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)  # Thread-pool primitives (FIRST_COMPLETED/wait migrated to ConnectionPoolExecutor per 1012 SC-003)
from dataclasses import dataclass, field  # Import dataclass decorators for configuration objects and entity classes
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
from src.api.api_data_fetcher import (  # pylint: disable=unused-import
    APIDataFetcher,  # noqa: F401  # Cat B (1013 SC-001 position 21) -- re-export for MistHelper.APIDataFetcher callers
)
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
from src.dataclasses.websocket_stream_target import (
    WebSocketStreamTarget,
)  # Issue #470: groups WS connection identity to keep _listen_for_output within the 5-Item Rule.
from src.device.device_utils import (  # pylint: disable=unused-import
    DeviceUtils,  # noqa: F401  # Cat B (1013 SC-001 position 6) -- re-export for dynamic _mh.DeviceUtils lookup
)
from src.export.const_definitions_exporter import (  # pylint: disable=unused-import
    ConstDefinitionsExporter,  # noqa: F401  # Cat B (1013 SC-001 position 17) -- re-export for MistHelper.ConstDefinitionsExporter callers
)
from src.export.device_events_52w_exporter import (  # pylint: disable=unused-import
    DeviceEvents52wExporter,  # noqa: F401  # Re-export preserved after OrgAlarmEventExporter extraction (1013 SC-001 position 18)
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
from src.export.org_template_exporter import (  # pylint: disable=unused-import
    OrgTemplateExporter,  # noqa: F401  # Cat B (1013 SC-001 position 22) -- re-export for MistHelper.OrgTemplateExporter callers
)
from src.export.self_export_utils import (  # pylint: disable=unused-import
    SelfExportUtils,  # noqa: F401  # Cat B (1013 SC-001 position 7) -- re-export for menu tuple at MistHelper:18167
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
from src.org.org_config_migration_manager import OrgConfigMigrationManager  # Cat B (1013 SC-001 position 5)
from src.org_data_collector import OrgDataCollector  # Import org-level data collection orchestrator
from src.refactors.anomaly_metrics_discovery import (
    AnomalyMetricsDiscovery,  # Extracted anomaly metrics discovery (SC-016)
)
from src.refactors.connection_pool_executor import ConnectionPoolExecutor  # Extracted pool executor (1012 SC-003)
from src.refactors.data_directory_checker import DataDirectoryChecker  # Early data-dir writable check (SC-005)
from src.refactors.device_config_template_cloner_manager import (
    DeviceConfigTemplateClonerManager,  # Extracted device config template cloner (SC-020)
)
from src.refactors.device_data_fetcher import (  # pylint: disable=unused-import
    DeviceDataFetcher,  # noqa: F401  # Extracted interactive device data fetcher (SC-017) -- re-export for src.ui.interactive_display_utils lazy access
)
from src.refactors.fast_mode_backoff_multiplier import (
    FastModeBackoffMultiplier,  # Extracted fast-mode backoff multiplier constant (SC-028)
)

# FastModeDevicesPerThread import removed: only referenced from within ConnectionPoolExecutor (1012 SC-003)
from src.refactors.fast_mode_sequential_max_retries import (
    FastModeSequentialMaxRetries,  # Extracted fast-mode sequential-fallback retry ceiling (SC-030)
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
from src.refactors.marvis_data_utils import (
    MarvisDataUtilsFactory,  # Extracted Marvis data-utils singleton factory (SC-027)
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
from src.reports.e911_bssid import E911BSSIDReportGenerator  # Module-level for tests
from src.reports.global_wired_client_report_generator import (  # pylint: disable=unused-import
    GlobalWiredClientReportGenerator,  # noqa: F401  # Cat B (1013 SC-001 position 36) -- re-export for MistHelper.GlobalWiredClientReportGenerator callers
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
from src.troubleshooting.interactive_test_runner import (
    InteractiveTestRunner,
)  # Import interactive diagnostic test runner
from src.troubleshooting.marvis_troubleshoot_utils import (
    MarvisTroubleshootDeps,
)  # Import Marvis troubleshooting dependency injection class
from src.troubleshooting.marvis_troubleshoot_utils import (
    MarvisTroubleshootUtils as ExtractedMarvisTroubleshootUtils,
)  # Import Marvis troubleshooting utils (renamed to avoid conflicts)
from src.ui.display_utils import (  # pylint: disable=unused-import
    DisplayUtils,  # noqa: F401  # Cat B (1013 SC-001 position 11) -- re-export for lazy _MH.DisplayUtils callers
)
from src.ui.interactive_display_utils import (  # pylint: disable=unused-import
    InteractiveDisplayUtils,  # noqa: F401  # Cat B (1013 SC-001 position 10) -- re-export for callers at 17392/17393/17394/17395
)
from src.utils.environment_utils import (  # pylint: disable=unused-import
    EnvironmentUtils,  # noqa: F401  # Cat B (1013 SC-001 position 33) -- re-export for MistHelper.EnvironmentUtils callers
)
from src.utils.operation_registry import (  # pylint: disable=unused-import
    OperationRegistry,  # noqa: F401  # Cat B (1013 SC-001 position 13) -- re-export for menu safety classification
)
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


@dataclass
class SSHConnectionConfig:
    """Configuration for SSH connections - groups connection parameters."""

    hostname: str  # Target device hostname or IP address to connect to
    username: str  # SSH login username for authentication
    password: str  # SSH login password (treated as a secret; never logged in plaintext)
    port: int = 22  # TCP port for SSH (default 22; override for non-standard device setups)
    timeout: int = 30  # Seconds to wait before giving up on a connection attempt
    use_shell: bool = True  # Whether to allocate an interactive shell vs exec a single command


@dataclass
class SSHExecutionConfig:
    """Configuration for SSH command execution - groups execution parameters."""

    commands: list[str] = field(
        default_factory=list
    )  # Commands to run; default_factory avoids a shared mutable default list
    max_threads: int = 5  # Cap on concurrent SSH sessions to avoid overloading devices/network
    use_shell: bool = True  # Whether commands run in an interactive shell context


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
    import websocket  # WebSocket client for streaming device CLI commands
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
    import requests  # HTTP library used by mistapi and direct API requests
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
        import threading  # Lock primitive to serialize log output across threads

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


class TimeUtils:
    """
    Centralized time-related utilities.
    Handles dynamic lookback windows, timestamp conversions, etc.
    """

    @staticmethod
    def get_dynamic_lookback_hours(default_hours: int = 24, test_hours: int = 1) -> int:
        """Return lookback hours adjusted for test mode (shrinks to test_hours under --test).

        Outside test mode the caller's default_hours window is honored. Both values are
        clamped to a 1-hour minimum so a misconfiguration never yields a sub-hour window.
        """
        try:
            chosen_hours = test_hours if IS_TEST_MODE else default_hours  # Pick the window for the active mode
            return max(1, chosen_hours)  # Never return less than 1 hour (clamp misconfigured values)
        except Exception as error:  # Never let lookback math crash a caller
            logging.debug("get_dynamic_lookback_hours fallback due to error: %s", error)  # Log the unexpected failure
            return test_hours if IS_TEST_MODE else default_hours  # Fall back to a sensible default per mode

    @staticmethod
    def log_dynamic_lookback(context: str, hours: int) -> None:
        """Helper to produce a consistent log line when dynamic lookback applies."""
        if IS_TEST_MODE:  # Surface the reduced window prominently during tests
            logging.info(
                "[TEST MODE] Using reduced lookback window of %sh for %s (normally 24h)", hours, context
            )  # Visible test-mode notice
        else:  # Production: keep the note at debug level
            logging.debug("Using standard lookback window of %sh for %s", hours, context)  # Quiet production notice


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
class ValidationUtils:  # Input validators for API identifiers.
    """
    Centralized validation utilities for input validation and sanitization.
    All validation functions should be static methods in this class.
    """

    @staticmethod
    def validate_site_id(site_id: str | None, function_name: str = "unknown") -> bool:  # Guard site_id before API use.
        """
        Validates that site_id is not None or empty before making API calls.

        Args:
            site_id: The site ID to validate
            function_name: Name of the calling function for logging

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValueError: If site_id is None or empty
        """
        if site_id is None:  # Reject a missing site_id.
            error_msg = f"! site_id is None in {function_name}. Cannot make API call."  # Build the failure message.
            logging.error(error_msg)  # Log before raising.
            raise ValueError(error_msg)  # Abort the call with context.

        if isinstance(site_id, str) and site_id.strip() == "":  # Reject empty/whitespace site_id.
            error_msg = f"! site_id is empty string in {function_name}. Cannot make API call."  # empty-string msg.
            logging.error(error_msg)  # Log before raising.
            raise ValueError(error_msg)  # Abort the call.

        return True  # site_id passed validation.

    @staticmethod
    def validate_device_id(device_id: str | None, function_name: str = "unknown") -> bool:  # Guard device_id.
        """
        Validates that device_id is not None or empty before making API calls.

        Args:
            device_id: The device ID to validate
            function_name: Name of the calling function for logging

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValueError: If device_id is None or empty
        """
        if device_id is None:  # Reject a missing device_id.
            error_msg = f"! device_id is None in {function_name}. Cannot make API call."  # Build the failure message.
            logging.error(error_msg)  # Log before raising.
            raise ValueError(error_msg)  # Abort the call with context.

        if isinstance(device_id, str) and device_id.strip() == "":  # Reject empty/whitespace device_id.
            error_msg = f"! device_id is empty string in {function_name}. Cannot make API call."  # empty-string msg.
            logging.error(error_msg)  # Log before raising.
            raise ValueError(error_msg)  # Abort the call.

        return True  # device_id passed validation.

    @staticmethod
    def validate_ping_target(target: str) -> bool:  # Validate a ping destination string.
        """
        Validate ping target hostname or IP address.

        Args:
            target: Target hostname or IP address

        Returns:
            bool: True if valid target, False otherwise
        """
        if not target or len(target.strip()) == 0:  # Reject empty targets.
            return False  # Invalid: no target given.

        target = target.strip()  # Normalize surrounding whitespace.

        try:  # A literal IP address is always a valid target.
            ipaddress.ip_address(target)  # Parse as a literal IP.
            return True  # Valid IP target.
        except ValueError:  # Not an IP; fall through to hostname validation.
            pass  # Hostname check happens below.

        return ValidationUtils._is_valid_hostname(target)  # Accept only well-formed hostnames

    @staticmethod
    def _is_valid_hostname(target: str) -> bool:  # Check a string is a syntactically valid hostname
        """Return True when target uses the hostname charset, is <= 253 chars, and has no edge dot/hyphen."""
        if not re.match(r"^[a-zA-Z0-9.-]+$", target) or len(target) > 253:  # Reject bad charset or over-length names
            return False  # Not a valid hostname
        return not target.startswith((".", "-")) and not target.endswith((".", "-"))  # Reject leading/trailing dot/dash


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
class APICoreFetchUtils:  # Low-level Mist API fetch helpers.
    """
    Core API Fetch Utilities

    Handles site and inventory fetching with pagination.
    Extracted from APIFetchUtils.
    """

    @staticmethod
    def all_sites_with_limit(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """
        Fetch all sites with unified pagination.

        Args:
            org_id: The organization ID

        Returns:
            List of site dictionaries

        SECURITY: Read-only; no sensitive data logged.
        """
        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)
        return mistapi.get_all(response=response, mist_session=apisession)  # type: ignore[no-any-return]

    @staticmethod
    def all_inventory_with_limit(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """
        Fetch full org inventory with unified pagination.

        Args:
            org_id: The organization ID

        Returns:
            List of inventory dictionaries (includes all VC physical members)

        SECURITY: Read-only; no secrets in inventory object fields.
        """
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(
            apisession, org_id, vc=True, limit=DEFAULT_API_PAGE_LIMIT
        )  # vc=True includes all physical VC member devices
        return mistapi.get_all(response=response, mist_session=apisession)  # type: ignore[no-any-return]

    @staticmethod
    def get_api_response_data(response: Any) -> Any:
        """Return a mistapi response's .data payload, or the response itself when .data is absent."""
        logging.debug("Unwrapping API response payload (type=%s)", type(response).__name__)  # Trace unwrap calls
        return getattr(response, "data", response)  # mistapi carries parsed JSON on .data; fall back to the raw object


# APITenantFetchUtils extracted to src/api/tenant_fetch.py (issue #331).
# Dependency injection is used so the module has no circular import with MistHelper.
# Instances are created at each call site using the runtime apisession and org ID resolver.
from src.api.tenant_fetch import APITenantFetchUtils  # noqa: F401  # Re-exported for ServicePingLauncher late-binding


class APIFetchUtils:  # Higher-level org/site fetchers.
    """
    Centralized API fetch utilities.
    Groups all data fetching functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def organization_services() -> list[dict[str, Any]]:  # Fetch and flatten org services.
        """Fetch all org-level services via the Mist API; return list of service dicts (empty on error).

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the target org.
            logging.info("Fetching organization services for org_id: %s", org_id)  # Log before the API call.

            # Call the Mist API to get organization services
            response = mistapi.api.v1.orgs.services.listOrgServices(apisession, org_id, limit=1000)  # List services.

            if hasattr(response, "data") and response.data:  # Only proceed with data.
                services_data = response.data  # Unwrap the payload.
                logging.info("Successfully retrieved %s organization services", len(services_data))  # Log the count.
                services_list = APIFetchUtils._normalize_org_services(services_data)  # Normalize to display rows.
                return services_list  # Return normalized services.

            logging.warning("No organization services found or response data is empty")  # Warn on empty response.
            return []  # No services to return.

        except Exception as error:  # Never crash on API failure.
            logging.error("Failed to fetch organization services: %s", error)  # Log the fetch failure.
            return []  # Degrade to empty list.

    @staticmethod
    def _normalize_org_services(services_data: list[Any]) -> list[dict[str, Any]]:  # Flatten raw services to rows
        """Normalize raw org service records into name/type/description rows (keeping the full config)."""
        services_list = []  # Accumulate normalized rows.
        for service in services_data:  # Walk each service.
            if isinstance(service, dict):  # Skip non-dict entries.
                services_list.append(
                    {
                        "name": service.get("name", "unnamed"),  # Default missing names.
                        "type": service.get("type", "custom"),  # Default missing type.
                        "description": service.get("description", ""),  # Default missing description.
                        "full_config": service,  # Keep full config for reference
                    }
                )  # Record the normalized service row
        return services_list  # Return normalized services.

    @staticmethod
    def _fetch_single_site_setting(apisession, site):
        """Fetch one site's settings; tag with id/name; return dict or None on failure."""
        site_id = site.get("id")  # Target site id
        site_name = site.get("name", "Unnamed Site")  # Friendly site label
        try:
            config = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id).data  # Fetch site settings
            config["site_id"] = site_id  # Tag with site id
            config["site_name"] = site_name  # Tag with site name
            logging.info("! Fetched config for site: %s (ID: %s)", site_name, site_id)
            return config
        except Exception as error:  # Skip sites that fail
            logging.warning("! Failed to fetch config for %s (ID: %s): %s", site_name, site_id, error)
            return None

    @staticmethod
    def all_site_settings(apisession, org_id, limit=1000):  # Fetch settings for every site.
        """Fetch per-site settings for every site in the org; limit param is unused (kept for back-compat)."""
        del limit  # Kept in signature for back-compat; explicitly discard so linters do not flag it.
        logging.info("Fetching all site settings...")  # Log before fetching sites
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # List all sites first
        all_configs = []  # Collect per-site settings
        for site in tqdm(sites, desc="Sites", unit="site"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():  # Honor a user stop request
                break  # Stop iterating sites
            config = APIFetchUtils._fetch_single_site_setting(apisession, site)  # One site at a time
            if config is not None:  # Skip failed fetches
                all_configs.append(config)
        logging.info("Fetched settings for %s sites.", len(all_configs))  # Log total fetched
        return all_configs  # Return all site settings

    @staticmethod
    def _gw_load_inventory(apisession, org_id):
        """Fetch the org inventory; return the device list, or None when the fetch fails."""
        logging.info("Fetching org inventory to find gateway devices...")  # Log before the inventory fetch.
        try:  # The inventory fetch is the one hard dependency; isolate its failure.
            response = mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)  # Fetch inventory.
            return mistapi.get_all(response=response, mist_session=apisession)  # Page through all devices.
        except Exception as error:  # Inventory fetch failed.
            logging.error("! Failed to fetch org inventory: %s", error)  # Log the failure.
            return None  # Signal failure so the caller degrades to an empty result.

    @staticmethod
    def _gw_load_site_names():
        """Load the site id -> name map from SiteList.csv; return an empty map when the file is unavailable."""
        try:  # The site-name CSV is optional enrichment; missing file is non-fatal.
            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # Locate the site list CSV.
            with open(site_list_path, encoding="utf-8") as file_handle:  # Read site names from CSV.
                reader = csv.DictReader(file_handle)  # Parse CSV rows.
                return {row.get("id"): row.get("name", "Unnamed Site") for row in reader}  # id->name map.
        except Exception as error:  # CSV missing or unreadable.
            logging.warning("! Failed to load SiteList.csv for site names: %s", error)  # Warn names may be unknown.
            return {}  # Degrade to an empty lookup.

    @staticmethod
    def _gw_build_work_items(inventory, site_name_lookup):
        """Build (site_id, device_id, site_name) work items for each gateway device in the inventory."""
        work_items = []  # Accumulate one tuple per gateway needing a config fetch.
        for device in inventory:  # Scan every inventory device.
            if device.get("type") != "gateway":  # Only gateways need configs; skip everything else.
                continue  # Move to the next device.
            site_id = device.get("site_id")  # Owning site id.
            device_id = device.get("id")  # Device id.
            if site_id and device_id:  # Require both ids before queueing a fetch.
                site_name = site_name_lookup.get(site_id, "Unknown")  # Resolve the site name for enrichment.
                work_items.append((site_id, device_id, site_name))  # Queue the fetch.
        return work_items  # Hand the gateway work list back to the caller.

    @staticmethod
    def _gw_fetch_one_config(apisession, work_item, connection_semaphore):
        """Fetch one gateway device's config (site-tagged); return the config dict, or None on empty/failure."""
        work_site_id, work_device_id, work_site_name = work_item  # Unpack the work item.
        with connection_semaphore:  # Limit concurrent connections via the pool semaphore.
            try:  # Isolate per-device failures so one bad device doesn't abort the batch.
                logging.debug("Fetching config for %s (%s)", work_device_id, work_site_name)  # Trace the fetch.
                config_response = mistapi.api.v1.sites.devices.getSiteDevice(  # Call the device API.
                    apisession, work_site_id, work_device_id
                )
                config = getattr(config_response, "data", {})  # Unwrap data safely.
                if config:  # Only keep non-empty configs.
                    config["site_name"] = work_site_name  # Tag with site name for enrichment.
                    config["site_id"] = work_site_id  # Tag with site id for enrichment.
                    logging.debug("! Config fetched for %s", work_device_id)  # Trace success.
                    return config  # Return the enriched config.
                logging.warning("! Empty config for device %s", work_device_id)  # Warn on empty config.
                return None  # Treat empty config as a miss.
            except Exception as inner_error:  # Per-device fetch failed.
                logging.error("! Failed to fetch config for device %s: %s", work_device_id, inner_error)  # Log error.
                return None  # Mark this device failed.

    @staticmethod
    def _gw_retry_one_item(apisession, failed_work_item, connection_semaphore, max_retries):
        """Retry one failed gateway config fetch up to max_retries with backoff; return the config or None."""
        _, failed_device_id, _ = failed_work_item  # Only the device id is needed here (for logging).
        for attempt in range(max_retries + 1):  # Bounded retry loop (initial try plus retries).
            result = APIFetchUtils._gw_fetch_one_config(apisession, failed_work_item, connection_semaphore)  # Try.
            if result is not None:  # Retry succeeded.
                return result  # Hand back the recovered config.
            if attempt < max_retries:  # More attempts remain.
                delay = 0.5 * (1.5**attempt)  # Exponential backoff delay.
                logging.debug(  # Trace the retry/backoff.
                    "Retrying device %s in %.2fs (attempt %s/%s)",
                    failed_device_id,
                    delay,
                    attempt + 2,
                    max_retries + 1,
                )
                time.sleep(delay)  # Back off before retrying.
        logging.warning(  # Warn after exhausting every attempt.
            "! Failed to fetch config for device %s after %s attempts", failed_device_id, max_retries + 1
        )
        return None  # Every attempt failed.

    @staticmethod
    def _gw_retry_configs(apisession, failed_items, connection_semaphore):
        """Retry failed gateway config fetches with bounded exponential backoff; return the recovered configs."""
        max_retries = FastModeSequentialMaxRetries.VALUE  # Configurable retry count from extracted class attribute.
        retry_results = []  # Collect configs recovered on retry.
        for failed_work_item in failed_items:  # Walk every failed item.
            result = APIFetchUtils._gw_retry_one_item(
                apisession, failed_work_item, connection_semaphore, max_retries
            )  # Retry this item with backoff.
            if result is not None:  # The item recovered on retry.
                retry_results.append(result)  # Keep the recovered config.
        return retry_results  # Return the configs recovered during retry.

    @staticmethod
    def _gw_collect_fast(apisession, work_items):
        """Fetch gateway configs concurrently through the connection pool with retry; return the successes."""
        successful_results, _ = ConnectionPoolExecutor.execute(  # Pooled concurrent fetch; discard failures.
            work_items=work_items,
            worker_function=functools.partial(APIFetchUtils._gw_fetch_one_config, apisession),  # Bind apisession.
            batch_description="gateway device configs",
            retry_function=functools.partial(APIFetchUtils._gw_retry_configs, apisession),  # Bind apisession.
        )
        return successful_results  # The pool already retried failures; return the successes.

    @staticmethod
    def _gw_collect_sequential(apisession, work_items):
        """Fetch each gateway config sequentially using a serializing semaphore; return the collected configs."""
        all_device_configs = []  # Accumulate sequential results.
        dummy_semaphore = threading.Semaphore(1)  # Serialize sequential fetches with a single permit.
        for work_item in tqdm(work_items, desc="Fetching Configs", unit="device"):  # type: ignore[no-untyped-call]
            result = APIFetchUtils._gw_fetch_one_config(apisession, work_item, dummy_semaphore)  # Fetch one config.
            if result is not None:  # Keep non-empty results.
                all_device_configs.append(result)  # Collect the config.
        return all_device_configs  # Return the sequentially fetched configs.

    @staticmethod
    def gateway_device_configs(apisession, org_id, fast=False, max_workers=None):
        """Fetch configuration details for all gateway devices in the org inventory.

        When ``fast`` is True the per-device fetches run concurrently through the
        connection pool (with retry); otherwise they run sequentially. Returns a list
        of site-tagged device configuration dicts (empty when the inventory fetch fails).
        ``max_workers`` is accepted for call-site compatibility.
        """
        del max_workers  # Kept in signature for call-site compatibility; explicitly discard so linters do not flag it.
        inventory = APIFetchUtils._gw_load_inventory(apisession, org_id)  # Fetch the org inventory (None on failure).
        if inventory is None:  # The inventory fetch failed outright.
            return []  # Degrade to an empty list.
        logging.info("Found %s total devices in org inventory.", len(inventory))  # Log the device count.
        site_name_lookup = APIFetchUtils._gw_load_site_names()  # Load site id->name enrichment map.
        work_items = APIFetchUtils._gw_build_work_items(inventory, site_name_lookup)  # Build the gateway work list.
        logging.info("Prepared %s gateway device config API calls.", len(work_items))  # Log planned API calls.
        if fast:  # Fast mode uses the connection pool with retry.
            all_device_configs = APIFetchUtils._gw_collect_fast(apisession, work_items)  # Pooled concurrent path.
        else:  # Sequential processing for non-fast mode.
            all_device_configs = APIFetchUtils._gw_collect_sequential(apisession, work_items)  # Serial fetch path.
        all_device_configs = [config for config in all_device_configs if config is not None]  # Drop any failures.
        logging.info("! Completed fetching %s gateway device configs.", len(all_device_configs))  # Log completion.
        return all_device_configs  # Return the gateway configs.


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


class DatabaseSchemaUtils:  # Build SQLite DDL from data.
    """
    Centralized database schema utilities for SQLite operations.
    Groups all schema-related functions per the 5-Item Rule class organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def determine_api_function_name_from_context() -> str:  # Infer API name from the call stack.
        """Walk the call stack and return the first frame whose name looks like a Mist API call; else 'unknown'."""
        frame = inspect.currentframe()  # Start at the current frame.
        try:
            while frame:  # Walk up the stack.
                function_name = frame.f_code.co_name  # Name of this frame's function.
                if any(  # Match known API call patterns.
                    pattern in function_name
                    for pattern in ["getOrg", "listOrg", "searchOrg", "getSite", "listSite", "searchSite"]
                ):
                    logging.debug("Detected API function name from stack: %s", function_name)  # Trace detected name.
                    return function_name  # Use the detected API name.
                frame = frame.f_back  # Step to the caller frame.
        except Exception as error:  # Stack inspection failed.
            logging.debug("Error determining API function name: %s", error)  # Trace the inspection error.
        finally:
            del frame  # Break the reference cycle.
        return "unknown"  # Fallback when undetected.

    @staticmethod
    def get_endpoint_strategy(api_function_name: str, data_fields: list[str]) -> dict[str, Any]:  # Pick PK strategy.
        """
        Determines the appropriate database schema strategy for an API endpoint.

        Args:
            api_function_name (str): Name of the API function being called
            data_fields (list): List of field names in the data

        Returns:
            dict: Strategy configuration including primary key, indexes, etc.
        """
        # First check if we have a specific strategy for this endpoint
        if api_function_name in ENDPOINT_PRIMARY_KEY_STRATEGIES:  # Use a configured strategy.
            strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_function_name].copy()  # Copy to avoid mutation.
            logging.debug("Using configured strategy for %s: %s", api_function_name, strategy["type"])  # Trace pick.
            return strategy  # Return configured strategy.

        return DatabaseSchemaUtils._build_default_strategy(api_function_name, data_fields)  # Derive from data shape

    @staticmethod
    def _build_default_strategy(api_function_name: str, data_fields: list[str]) -> dict[str, Any]:  # Field-derived PK
        """Build a default PK strategy enhanced by the data's available fields (id + common index columns)."""
        strategy: dict[str, Any] = ENDPOINT_PRIMARY_KEY_STRATEGIES["default"].copy()  # Start from the default template

        if "id" in data_fields:  # Data carries an 'id' -- use it as the unique key
            strategy["unique_constraints"] = ["id"]  # Enforce unique id.
            strategy["indexes"] = ["id"]  # Index id for lookups.
            logging.debug("Default strategy for %s: unique constraint on 'id'", api_function_name)  # Trace id keying

        common_index_fields = ["org_id", "site_id", "device_id", "timestamp", "mac", "serial"]  # Common index columns.
        for field_name in common_index_fields:  # Add indexes when present.
            if field_name in data_fields and field_name not in strategy["indexes"]:  # Avoid duplicate indexes.
                strategy["indexes"].append(field_name)  # type: ignore[attr-defined]  # Index this present field

        logging.debug("Using enhanced default strategy for %s: %s", api_function_name, strategy)  # Trace strategy.
        return strategy  # Return enhanced strategy.

    @staticmethod
    def _sanitize_table_name(name: str) -> str:
        """Sanitize a SQL table name; force a non-digit leading character to keep DDL valid."""
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)  # Replace any non-alphanum/underscore with '_'
        if not safe or safe[0].isdigit():  # Empty or digit-led identifier is not valid SQL
            safe = f"table_{safe}"  # Prefix to ensure a valid identifier
        return safe  # Return the sanitized name

    @staticmethod
    def _sanitize_column(field_name: Any) -> str:
        """Sanitize a column identifier for safe inclusion in SQL DDL."""
        return re.sub(r"[^a-zA-Z0-9_]", "_", str(field_name))  # Replace any non-alphanum/underscore with '_'

    @staticmethod
    def _pk_aware_column_defs(fields: list[str], pk_fields: list[str]) -> list[str]:
        """Return TEXT column-def strings; columns named in pk_fields are flagged NOT NULL."""
        defs: list[str] = []  # Collect column definitions in field order
        for field_name in fields:  # Walk each input field name
            safe = DatabaseSchemaUtils._sanitize_column(field_name)  # Sanitize column for SQL safety
            if field_name in pk_fields:  # Primary-key columns require NOT NULL
                defs.append(f"{safe} TEXT NOT NULL")  # Required PK column
            else:
                defs.append(f"{safe} TEXT")  # Optional column
        return defs  # Return the column-def list

    @staticmethod
    def _plain_column_defs(fields: list[str]) -> list[str]:
        """Return TEXT column-def strings for every field (no PK distinction)."""
        return [
            f"{DatabaseSchemaUtils._sanitize_column(field_name)} TEXT" for field_name in fields
        ]  # Plain TEXT columns

    @staticmethod
    def _metadata_column_defs() -> list[str]:
        """Return the standard audit timestamp column definitions appended to every table."""
        return [
            "misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP",  # Row-create timestamp
            "misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP",  # Row-update timestamp
        ]

    @staticmethod
    def _assemble_create_sql(safe_table_name: str, field_definitions: list[str], suffix: str) -> str:
        """Assemble the final CREATE TABLE statement from sanitized name, column defs, and suffix clauses."""
        sql_parts = [
            f"CREATE TABLE IF NOT EXISTS {safe_table_name} (",  # Begin the CREATE TABLE
            ", ".join(field_definitions),  # Join all column defs
            suffix,  # Strategy-specific suffix (PK or UNIQUE clauses)
            ")",  # Close the column list
        ]
        return "".join(sql_parts)  # Assemble the DDL string

    @staticmethod
    def _build_natural_pk_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for a natural-key endpoint (stable UUID column)."""
        pk_fields = strategy["primary_key"]  # Natural primary key columns
        field_defs = DatabaseSchemaUtils._pk_aware_column_defs(fields, pk_fields)  # PK-aware column defs
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        suffix = f", PRIMARY KEY ({', '.join(pk_fields)})"  # Compose the PK clause
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, suffix)  # Final DDL

    @staticmethod
    def _build_composite_pk_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for a composite-key endpoint (only present columns become PK)."""
        pk_fields = strategy["primary_key"]  # Composite key columns
        field_defs = DatabaseSchemaUtils._pk_aware_column_defs(fields, pk_fields)  # PK-aware column defs
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        available = [f for f in pk_fields if f in fields]  # Only key on present columns
        suffix = f", PRIMARY KEY ({', '.join(available)})" if available else ""  # Empty suffix when no key columns
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, suffix)  # Final DDL

    @staticmethod
    def _build_autoincrement_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for an auto-increment-with-unique endpoint (surrogate id + UNIQUE cols)."""
        field_defs = ["misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT"]  # Surrogate key column first
        field_defs.extend(DatabaseSchemaUtils._plain_column_defs(fields))  # Plain TEXT columns
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        unique_fields = [f for f in strategy["unique_constraints"] if f in fields]  # Constrain present columns only
        unique_suffix = "".join(
            f", UNIQUE({DatabaseSchemaUtils._sanitize_column(f)})" for f in unique_fields
        )  # Comma-separated UNIQUE clauses (empty when no unique fields)
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, unique_suffix)  # Final DDL

    @staticmethod
    def build_create_table_sql(
        table_name: str,
        fields: list[str],
        strategy: dict[str, Any],
    ) -> str:
        """Build the CREATE TABLE SQL for an endpoint, dispatching by strategy['type']."""
        datetime.now(UTC).isoformat()  # Preserve legacy timestamp-build side effect from prior implementation
        safe_table_name = DatabaseSchemaUtils._sanitize_table_name(table_name)  # Sanitize the table name
        builders = {
            "natural_pk": DatabaseSchemaUtils._build_natural_pk_sql,  # Stable-UUID branch builder
            "composite_pk": DatabaseSchemaUtils._build_composite_pk_sql,  # Time-series branch builder
        }
        builder = builders.get(strategy["type"], DatabaseSchemaUtils._build_autoincrement_sql)  # Auto-incr fallback
        create_sql = builder(safe_table_name, fields, strategy)  # Dispatch to the strategy-specific builder
        logging.debug("Generated CREATE TABLE SQL for %s: %s...", safe_table_name, create_sql[:100])  # Trace DDL
        return create_sql  # Return the CREATE TABLE

    @staticmethod
    def build_indexes_sql(table_name: str, fields: list[str], strategy: dict[str, Any]) -> list[str]:  # Build indexes.
        """Build CREATE INDEX IF NOT EXISTS statements for fields named in strategy['indexes'] that exist in fields."""
        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name)  # Sanitize the table name.
        if not safe_table_name or safe_table_name[0].isdigit():  # Names cannot start with a digit.
            safe_table_name = f"table_{safe_table_name}"  # Prefix to make it valid.
        index_sqls = []  # Collect index statements.
        for field_name in strategy.get("indexes", []):  # One index per configured field.
            if field_name in fields:  # Only index present columns.
                safe_field = re.sub(r"[^a-zA-Z0-9_]", "_", str(field_name))  # Sanitize the column name.
                index_name = f"idx_{safe_table_name}_{safe_field}"  # Deterministic index name.
                index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {safe_table_name} ({safe_field})"  # index DDL.
                index_sqls.append(index_sql)  # Collect the statement.
        return index_sqls  # Return all index DDL.


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


# ============================================================================
# ORGANIZATION TICKET MANAGER CLASS
# ============================================================================
class OrgTicketManager:  # Support ticket operations.
    """
    Full lifecycle management for Juniper Mist support tickets.

    Provides 6 public operations (list, create, add comment, update, view, export) that
    cover reading, creating, and modifying support tickets via the Mist API.
    Attachment support is integrated into add_comment via multipart upload.
    """

    TICKET_TYPES = ["question", "problem", "incident", "feature_request"]  # Valid Mist ticket type values

    # ------------------------------------------------------------------
    # Public entry points (6 operations -- cohesive ticket lifecycle)
    # ------------------------------------------------------------------

    @staticmethod
    def list_tickets() -> None:  # List org support tickets.
        """Menu 188: Export all organization support tickets to CSV/SQLite."""
        logging.info("Menu 188: Starting organization ticket list export")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.list_tickets()")  # Debug trace
        try:
            APIDataFetcher(  # Delegate to standard fetch-export pipeline
                title="Organization Support Tickets:",  # User-facing header
                api_call=mistapi.api.v1.orgs.tickets.listOrgTickets,  # SDK function for ticket listing
                filename="OrgTickets.csv",  # Output filename in data/ directory
                sort_key="created_at",  # Sort tickets by creation timestamp
                duration="365d",  # Look back 1 year (SDK defaults to 1d which misses older tickets)
            ).execute()  # Run the full fetch-flatten-export workflow
            logging.info("Completed org ticket list export")  # Log success
            logging.debug("EXIT: OrgTicketManager.list_tickets - success")  # Debug trace
        except Exception as error:  # Catch API or export failures
            logging.error("Failed to export org tickets: %s", error)  # Log error with context
            logging.debug("EXIT: OrgTicketManager.list_tickets - error")  # Debug trace
            raise  # Re-raise so caller sees the failure

    @staticmethod
    def create_ticket() -> None:  # Create a support ticket.
        """Menu 189: Create a new support ticket in the organization."""
        logging.info("Menu 189: Starting support ticket creation")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.create_ticket()")  # Debug trace
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        subject = OrgTicketManager._prompt_subject()  # Prompt user for ticket subject line
        if not subject:  # User left subject blank -- abort
            print("  Ticket creation cancelled -- subject is required.")  # Inform user
            logging.info("Ticket creation cancelled: blank subject")  # Log cancellation
            return  # Early exit
        ticket_type = OrgTicketManager._prompt_ticket_type()  # Prompt user to select ticket type
        comment = InputUtils.safe_input(  # Prompt for initial ticket description (optional)
            "  Enter initial comment/description: ",
            default_value="",
            allow_empty=True,
            context="create_ticket_comment",
        )
        body = {"subject": subject, "type": ticket_type}  # Build required API request fields
        if comment:  # Include comment only if user provided one
            body["comment"] = comment  # Add optional comment to request body
        OrgTicketManager._submit_create_ticket(org_id, body, subject, ticket_type)  # API + report

    @staticmethod
    def add_comment() -> None:  # Add a comment to a ticket.
        """Menu 190: Add a comment (with optional attachment) to an existing ticket."""
        logging.info("Menu 190: Starting add comment to ticket")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.add_comment()")  # Debug trace
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            print("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("Add comment cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit without adding comment
        comment_text, file_path = OrgTicketManager._prompt_comment_and_file()  # Gather inputs together
        if not comment_text and not file_path:  # Neither comment nor file provided -- abort
            print("  Operation cancelled -- provide a comment or file.")  # Inform user
            logging.info("Add comment cancelled: no comment or file provided")  # Log cancellation
            return  # Early exit
        OrgTicketManager._submit_comment(  # Submit comment to API
            org_id,
            ticket_id,
            comment_text,
            file_path,  # Pass all user-provided values
        )

    @staticmethod
    def update_ticket() -> None:  # Update a support ticket.
        """Menu 191: Update fields on an existing support ticket."""
        logging.info("Menu 191: Starting ticket update")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.update_ticket()")  # Debug trace
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            print("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("Ticket update cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit
        body = OrgTicketManager._build_update_body()  # Collect changed fields from user
        if not body:  # No fields were changed -- abort
            print("  No changes specified -- update cancelled.")  # Inform user
            logging.info("Ticket update cancelled: no fields changed")  # Log cancellation
            return  # Early exit
        OrgTicketManager._update_via_api(org_id, ticket_id, body)  # Send update + report results

    # ------------------------------------------------------------------
    # Private helpers (max 5 per group)
    # ------------------------------------------------------------------

    @staticmethod
    def _prompt_subject() -> str:  # Prompt for ticket subject.
        """Prompt user for ticket subject line."""
        return InputUtils.safe_input(  # Use EOF-safe input wrapper
            "  Enter ticket subject: ",  # Prompt text for ticket title
            default_value="",  # No default -- user must provide subject
            allow_empty=True,  # Allow blank to signal cancellation
            context="create_ticket_subject",  # Context label for EOF logging
        )

    @staticmethod
    def _prompt_ticket_type() -> str:  # Prompt for ticket type.
        """Prompt user to select a ticket type from valid options."""
        print("\n  Ticket types:")  # Section header for type selection
        for index, ticket_type in enumerate(OrgTicketManager.TICKET_TYPES, 1):  # Number each type for selection
            print(f"    {index}. {ticket_type}")  # Display numbered option
        choice = InputUtils.safe_input(  # Prompt user to pick a type number
            "  Select type [1]: ",  # Default to first option (question)
            default_value="1",  # Default selection is 'question'
            allow_empty=True,  # Allow enter for default
            context="create_ticket_type",  # Context label for EOF logging
        )
        try:
            index = int(choice) - 1  # Convert 1-based user input to 0-based index
            if 0 <= index < len(OrgTicketManager.TICKET_TYPES):  # Validate index is within bounds
                return OrgTicketManager.TICKET_TYPES[index]  # Return selected ticket type string
        except ValueError:  # User entered non-numeric input
            pass  # Fall through to default
        return OrgTicketManager.TICKET_TYPES[0]  # Default to 'question' for invalid input

    @staticmethod
    def _prompt_ticket_id() -> str:  # Prompt for ticket id.
        """Prompt user for ticket UUID."""
        return InputUtils.safe_input(  # Use EOF-safe input wrapper
            "  Enter ticket ID: ",  # Prompt text for ticket UUID
            default_value="",  # No default -- user must provide ID
            allow_empty=True,  # Allow blank to signal cancellation
            context="ticket_id_prompt",  # Context label for EOF logging
        )

    @staticmethod
    def _print_ticket_created_summary(ticket_data: dict, subject: str, ticket_type: str) -> None:
        """Print + log the newly created ticket summary."""
        ticket_id = ticket_data.get("id", "unknown")  # Get new ticket UUID from response
        logging.debug("Ticket created: id=%s, status=%s", ticket_id, ticket_data.get("status"))  # Log result
        print("\n  Ticket created successfully!")  # Confirm to user
        print(f"  ID:      {ticket_id}")  # Display ticket ID for reference
        print(f"  Subject: {subject}")  # Echo subject back to user
        print(f"  Type:    {ticket_type}")  # Echo type back to user
        print(f"  Status:  {ticket_data.get('status', 'open')}")  # Show initial status
        logging.info("Menu 189: Ticket creation complete, id=%s", ticket_id)  # Log success

    @staticmethod
    def _submit_create_ticket(org_id: str, body: dict, subject: str, ticket_type: str) -> None:
        """Send createOrgTicket API + print summary (or print + raise on error)."""
        logging.info("Creating ticket '%s' (type=%s) in org %s", subject, ticket_type, org_id)
        try:
            response = mistapi.api.v1.orgs.tickets.createOrgTicket(apisession, org_id, body)
            OrgTicketManager._print_ticket_created_summary(getattr(response, "data", {}), subject, ticket_type)
        except Exception as error:  # Catch API errors during ticket creation
            logging.error("Failed to create ticket: %s", error)  # Log error with context
            print(f"\n  Error creating ticket: {error}")  # Show error to user
            raise  # Re-raise for upstream error handling

    @staticmethod
    def _build_update_body() -> dict[str, str]:  # Build ticket update body.
        """Collect optional update fields (subject, status, type) from user prompts."""
        body: dict[str, str] = {}  # Accumulate changed fields in a dict
        fields = (  # (api_key, prompt_text, eof_context) tuples for each updatable field
            ("subject", "  New subject (leave blank to skip): ", "update_ticket_subject"),
            ("status", "  New status [open/closed] (leave blank to skip): ", "update_ticket_status"),
            (
                "type",
                "  New type [question/problem/incident/feature_request] (leave blank to skip): ",
                "update_ticket_type",
            ),
        )
        for api_key, prompt, ctx in fields:  # Prompt for each updatable field in turn
            value = InputUtils.safe_input(  # EOF-safe prompt for this field
                prompt,
                default_value="",
                allow_empty=True,
                context=ctx,
            )
            if value:  # Only include field if user provided a value
                body[api_key] = value  # Add user-supplied value to update body
        return body  # Return dict of fields to update (may be empty)

    @staticmethod
    def _update_via_api(org_id: str, ticket_id: str, body: dict[str, str]) -> None:
        """Send updateOrgTicket API call and print + log results."""
        logging.info("Updating ticket %s with fields: %s", ticket_id, list(body.keys()))  # Log before API call
        try:
            response = mistapi.api.v1.orgs.tickets.updateOrgTicket(  # Call Mist API to update ticket
                apisession,
                org_id,
                ticket_id,
                body,  # Pass session, org, ticket ID, body
            )
            logging.debug("Ticket updated: %s", getattr(response, "data", {}))  # Log full response
            print(f"\n  Ticket {ticket_id} updated successfully!")  # Confirm to user
            for field, value in body.items():  # Show each changed field to user
                print(f"  {field}: {value}")  # Display field name and new value
            logging.info("Menu 191: Ticket update complete for %s", ticket_id)  # Log success
        except Exception as error:  # Catch API errors during ticket update
            logging.error("Failed to update ticket %s: %s", ticket_id, error)  # Log error with context
            print(f"\n  Error updating ticket: {error}")  # Show error to user
            raise  # Re-raise for upstream error handling

    @staticmethod
    def _prompt_comment_and_file() -> tuple[str, str]:
        """Prompt for comment text and optional attachment path."""
        comment_text = InputUtils.safe_input(  # Prompt user for comment body text
            "  Enter comment text: ",
            default_value="",
            allow_empty=True,
            context="add_ticket_comment",
        )
        file_path = InputUtils.safe_input(  # Prompt for optional file attachment path
            "  Attach a file? Enter path (leave blank to skip): ",
            default_value="",
            allow_empty=True,
            context="add_ticket_attachment",
        )
        return comment_text, file_path  # Tuple of (text, file_path)

    @staticmethod
    def _submit_comment(org_id: str, ticket_id: str, comment_text: str, file_path: str) -> None:
        """Submit comment with optional file attachment to ticket."""
        has_file = bool(file_path and os.path.isfile(file_path))  # Check if valid file was specified

        if has_file:  # Use multipart upload API when file is attached
            logging.info("Adding comment with attachment to ticket %s", ticket_id)  # Log before API call
            mistapi.api.v1.orgs.tickets.addOrgTicketCommentFile(  # Multipart comment+file API
                apisession,
                org_id,
                ticket_id,  # Session, org, and ticket identifiers
                comment=comment_text or None,  # Comment text (None if empty)
                file=file_path,  # Path to file for upload
            )
            logging.debug("Comment with file submitted to ticket %s", ticket_id)  # Log after API call
            print(f"\n  Comment with attachment added to ticket {ticket_id}")  # Confirm to user
        elif file_path:  # User specified a path but file doesn't exist
            logging.warning(  # Warn about missing file path
                "File not found: %s -- adding comment without attachment", file_path
            )
            print(f"  Warning: File not found at '{file_path}' -- adding comment only.")  # Alert user
            OrgTicketManager._submit_text_comment(org_id, ticket_id, comment_text)  # Fall back to text-only
        else:  # No file specified -- text-only comment
            OrgTicketManager._submit_text_comment(org_id, ticket_id, comment_text)  # Submit text comment

    @staticmethod
    def _submit_text_comment(org_id: str, ticket_id: str, comment_text: str) -> None:  # Submit a text-only comment.
        """Submit a text-only comment to a ticket."""
        logging.info("Adding text comment to ticket %s", ticket_id)  # Log before API call
        body = {"comment": comment_text}  # Build comment request body
        mistapi.api.v1.orgs.tickets.addOrgTicketComment(  # Call Mist API to add comment
            apisession,
            org_id,
            ticket_id,
            body,  # Session, org, ticket ID, and comment body
        )
        logging.debug("Text comment submitted to ticket %s", ticket_id)  # Log after API call
        print(f"\n  Comment added to ticket {ticket_id}")  # Confirm to user

    # ------------------------------------------------------------------
    # Public entry points -- ticket viewing and export (Menu 192-193)
    # ------------------------------------------------------------------

    @staticmethod
    def view_ticket() -> None:  # View a single ticket.
        """Menu 192: View a single ticket with full comments and history."""
        logging.info("Menu 192: Starting ticket detail viewer")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.view_ticket()")  # Debug trace
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt

        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            print("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("View ticket cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit

        ticket_data = OrgTicketManager._fetch_ticket_detail(org_id, ticket_id)  # Fetch full ticket+comments
        if not ticket_data:  # API returned empty or failed
            print("  Could not retrieve ticket details.")  # Inform user of failure
            return  # Early exit

        OrgTicketManager._display_ticket_detail(ticket_data)  # Format and print to screen
        logging.info("Menu 192: Ticket detail view complete for %s", ticket_id)  # Log success

    @staticmethod
    def export_ticket_details() -> None:  # Export ticket details to file.
        """Menu 193: Export all tickets with full details and comments to CSV/SQLite."""
        logging.info("Menu 193: Starting full ticket detail export")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.export_ticket_details()")  # Debug trace
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        tickets = OrgTicketManager._fetch_all_ticket_summaries(org_id)  # API list summaries
        if not tickets:  # No tickets found in the org
            print("\n  No tickets found in this organization.")  # Inform user
            return  # Nothing to export
        all_details = OrgTicketManager._collect_ticket_details(org_id, tickets)  # Per-ticket detail fetch
        if all_details:  # Export if we have any ticket details
            logging.info("Exporting %d ticket details", len(all_details))  # Log before export
            DataExporter.write_with_format_selection(  # Write to CSV/SQLite via standard pipeline
                all_details,
                "OrgTicketDetails.csv",
                api_function_name="getOrgTicket",
            )
            logging.info("Menu 193: Full ticket detail export complete")  # Log success
        else:  # No details were retrieved
            print("\n  No ticket details could be retrieved.")  # Inform user

    # ------------------------------------------------------------------
    # Private helpers -- ticket selection and detail display
    # ------------------------------------------------------------------

    @staticmethod
    def _select_ticket(org_id: str) -> str:  # Prompt to select a ticket.
        """List tickets and let user pick by index, or enter ID manually."""
        tickets = OrgTicketManager._fetch_tickets_for_selection(org_id)  # Fetch + handle empty
        if not tickets:  # No tickets or fetch error
            return ""  # Signal cancellation to caller
        OrgTicketManager._render_ticket_list_table(tickets)  # Display numbered ticket table
        print(f"\n  Enter a number (1-{len(tickets)}) to select, or 'm' to enter ID manually.")
        choice = InputUtils.safe_input(  # Prompt user for selection input
            "  Selection: ",
            default_value="",
            allow_empty=True,
            context="select_ticket",
        )
        if not choice:  # Blank input -- cancel
            return ""  # Signal cancellation
        if choice.lower() == "m":  # Manual ID entry path
            return OrgTicketManager._prompt_ticket_id()  # Prompt for manual ticket UUID
        return OrgTicketManager._resolve_ticket_choice(choice, tickets)  # Parse + validate index

    @staticmethod
    def _fetch_tickets_for_selection(org_id: str) -> list:
        """Fetch ticket summaries for selection; print + return [] on error/empty."""
        logging.info("Fetching ticket list for selection (org %s)", org_id)  # Log before API call
        try:
            response = mistapi.api.v1.orgs.tickets.listOrgTickets(  # Fetch ticket summaries
                apisession,
                org_id,
                duration="365d",  # 1-year history window
            )
            tickets = getattr(response, "data", []) or []  # Extract ticket list
            logging.debug("Retrieved %d tickets for selection", len(tickets))  # Log count
        except Exception as error:  # Catch API failures
            logging.error("Failed to fetch tickets for selection: %s", error)  # Log error
            print(f"  Error fetching tickets: {error}")  # Show error to user
            return []  # Signal failure with empty list
        if not tickets:  # API returned no tickets
            print("\n  No tickets found in this organization.")  # Inform user
        return tickets  # Return list (possibly empty)

    @staticmethod
    def _render_ticket_list_table(tickets: list) -> None:
        """Print a numbered table of ticket #/status/type/subject for selection."""
        print("\n  Organization Support Tickets:")  # Section header
        print(f"  {'#':<4} {'Status':<10} {'Type':<18} {'Subject'}")  # Column headers
        print(f"  {'-' * 4} {'-' * 10} {'-' * 18} {'-' * 40}")  # Separator line
        for index, ticket in enumerate(tickets, 1):  # Display numbered rows
            status = ticket.get("status", "unknown")  # Ticket status field
            ttype = ticket.get("type", "unknown")  # Ticket type field
            subject = ticket.get("subject", "(no subject)")  # Ticket subject field
            print(f"  {index:<4} {status:<10} {ttype:<18} {subject}")  # Print formatted row

    @staticmethod
    def _resolve_ticket_choice(choice: str, tickets: list) -> str:
        """Parse numeric choice into ticket ID; print error + return '' on bad input."""
        try:
            idx = int(choice) - 1  # Convert 1-based to 0-based index
        except ValueError:  # Non-numeric input that wasn't 'm'
            print(f"  Invalid selection: {choice}")  # Inform user of bad input
            return ""  # Signal cancellation
        if not 0 <= idx < len(tickets):  # Index out of range
            print(f"  Invalid selection: {choice}")  # Inform user of bad input
            return ""  # Signal cancellation
        selected_id = tickets[idx].get("id", "")  # Extract ticket ID
        selected_subj = tickets[idx].get("subject", "(no subject)")  # Extract subject for confirmation
        print(f"  Selected: {selected_subj}")  # Confirm selection to user
        logging.info("User selected ticket %s (%s)", selected_id, selected_subj)  # Log selection
        return selected_id  # Return chosen ticket ID

    @staticmethod
    def _fetch_ticket_detail(org_id: str, ticket_id: str) -> dict:  # Fetch one ticket detail.
        """Fetch full ticket data including comments via getOrgTicket."""
        logging.info("Fetching detail for ticket %s", ticket_id)  # Log before API call
        try:
            response = mistapi.api.v1.orgs.tickets.getOrgTicket(  # Call SDK for full ticket detail
                apisession,
                org_id,
                ticket_id,
                duration="365d",  # Look back 1 year for comment history
            )
            ticket_data = getattr(response, "data", {}) or {}  # Extract response data dict
            logging.debug("Received ticket detail: %d fields", len(ticket_data))  # Log field count
            return ticket_data  # Return the full ticket dict with comments
        except Exception as error:  # Catch API failures
            logging.error("Failed to fetch ticket %s: %s", ticket_id, error)  # Log error
            print(f"  Error fetching ticket {ticket_id}: {error}")  # Show error to user
            return {}  # Return empty dict to signal failure

    @staticmethod
    def _fetch_all_ticket_summaries(org_id: str) -> list:
        """Fetch ticket-summary list via listOrgTickets, raise on failure."""
        logging.info("Fetching ticket list for org %s", org_id)  # Log before API call
        try:
            response = mistapi.api.v1.orgs.tickets.listOrgTickets(  # Fetch all ticket summaries
                apisession,
                org_id,
                duration="365d",  # 1-year window for ticket history
            )
            tickets = getattr(response, "data", []) or []  # Extract list from APIResponse
            logging.debug("Found %d tickets to export with details", len(tickets))  # Log count
            return tickets  # Return summary list to caller
        except Exception as error:  # Catch API failures on ticket list
            logging.error("Failed to fetch ticket list: %s", error)  # Log the failure
            print(f"\n  Error fetching tickets: {error}")  # Show error to user
            raise  # Re-raise for upstream handling

    @staticmethod
    def _collect_ticket_details(org_id: str, tickets: list) -> list:
        """For each summary in tickets, fetch + flatten its full detail. Returns list of flat dicts."""
        all_details = []  # Accumulate flattened ticket+comment records
        print(f"\n  Fetching details for {len(tickets)} tickets...")  # Progress indicator
        for index, ticket in enumerate(tickets, 1):  # Iterate each ticket summary
            tid = ticket.get("id", "")  # Extract ticket ID from summary
            if not tid:  # Skip tickets without valid IDs
                continue  # Move to next ticket
            logging.info("Fetching detail %d/%d: ticket %s", index, len(tickets), tid)  # Progress log
            detail = OrgTicketManager._fetch_ticket_detail(org_id, tid)  # Get full ticket data
            if detail:  # Only include tickets that returned data
                all_details.append(DataProcessingUtils.flatten_dict(detail))  # Flatten and add
            logging.debug("Fetched detail %d/%d", index, len(tickets))  # Progress debug log
        return all_details  # All flattened records (may be empty)

    @staticmethod
    def _display_ticket_detail(ticket_data: dict) -> None:  # Display ticket detail.
        """Format and display a ticket with its full comment history."""
        print("\n  " + "=" * 60)  # Top separator bar
        meta_fields = (  # (label, key, default) for the metadata block
            ("Ticket", "subject", "(no subject)"),
            ("ID    ", "id", "unknown"),
            ("Status", "status", "unknown"),
            ("Type  ", "type", "unknown"),
            ("Created", "created_at", "unknown"),
            ("Updated", "updated_at", "unknown"),
        )
        for label, key, default in meta_fields:  # Render header rows
            print(f"  {label}: {ticket_data.get(key, default)}")  # Display ticket metadata row
        print("  " + "-" * 60)  # Section separator
        OrgTicketManager._render_comments_block(ticket_data.get("comments", []))  # Render comments

    @staticmethod
    def _render_comments_block(comments: list) -> None:
        """Render the comments section: header + one block per comment + attachments."""
        if not comments:  # No comments on this ticket
            print("  No comments on this ticket.")  # Inform user
            return  # Nothing else to render
        print(f"  Comments ({len(comments)}):")  # Comment section header with count
        for idx, comment in enumerate(comments, 1):  # Iterate each comment
            author = comment.get("author", "unknown")  # Get comment author name
            created = comment.get("created_at", "unknown")  # Get comment timestamp
            text = comment.get("comment", "(no text)")  # Get comment body text
            print(f"\n  [{idx}] {author} -- {created}")  # Comment header with author+date
            print(f"      {text}")  # Comment body text indented
            for att in comment.get("attachments", []) or []:  # Iterate attachments (may be empty)
                print(f"      Attachment: {att.get('name', att.get('content_url', 'file'))}")

        print("  " + "=" * 60)  # Bottom separator bar


# OrgAlarmEventExporter moved to src/export/org_alarm_event_exporter.py (1013 SC-001 position 18)


# ============================================================================
# ORGANIZATION DATA EXPORT UTILITIES CLASS
# ============================================================================
class OrgSiteExporter:  # Org site exporters.
    """
    Organization Site Data Exporter

    Handles site listings, site locations, and guest data exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def sites():  # Export the org site list.
        """
        Fetches and exports the list of all sites in the organization.
        Output format determined by global OUTPUT_FORMAT setting.
        Uses APIDataFetcher to handle API call and output writing.
        """
        logging.info("Starting export of organization site list...")  # Log site export start.
        emitter = PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("11", "sites", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        APIDataFetcher(  # Fetch and write sites.
            title="Site List:",
            api_call=mistapi.api.v1.orgs.sites.listOrgSites,
            filename="SiteList",
            sort_key="name",
            limit=1000,
        ).execute()
        output_desc = "SQLite table" if OUTPUT_FORMAT == "sqlite" else "CSV file"  # Describe output backend.
        logging.info("Completed site list export and wrote results to %s.", output_desc)  # Log site export success.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(ProgressContext("11", "sites", 1), 1, False, time.time() - op_start)

    @staticmethod
    def sites_list_api():  # Export sites via list API.
        """Export all sites via 'list' endpoint to SiteList_ListAPI.csv (skip if cached file exists)."""
        output_file = "SiteList_ListAPI.csv"  # Define output filename.
        if os.path.exists(output_file):  # Branch: cached file exists.
            logging.info("! Using cached %s (already exists)", output_file)  # Log cache reuse.
            print(f"! Using cached {output_file} (already exists)")  # Inform operator of cache.
            return  # Skip re-fetch.
        logging.info("Fetching all sites using the 'list' sites API endpoint...")  # Log fetch start.
        print("Fetching all sites using the 'list' sites API endpoint...")  # Inform operator of fetch.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites.
        if not sites:  # Branch: no sites returned.
            logging.warning(" No sites returned from API.")  # Log empty result.
            print(" No sites returned from API.")  # Inform operator none returned.
            return  # Skip write.
        sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten nested site fields.
        # Normalize nested JSON structures into a flat row-per-record format for CSV/DB output
        sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten again post-merge.
        sites = DataProcessingUtils.escape_multiline(sites)  # type: ignore[no-untyped-call]
        # Write to the configured output backend (CSV or SQLite) via the DataExporter abstraction
        DataExporter.write_with_format_selection(sites, output_file)  # type: ignore[no-untyped-call]
        logging.info("! Sites exported to %s", output_file)  # Log the successful export
        print(f"! Sites exported to {output_file}")  # Inform the user on stdout

    @staticmethod
    def sites_with_location():  # Export sites with location.
        """
        Export a list of sites with all available fields to SitesWithLocations.csv.
        """
        print("Sites with Location and Timezone Info:")  # Inform operator of export.
        logging.info("Listing Sites with Full Info:")  # Log listing start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        logging.debug("Using org_id: %s for site location export.", org_id)  # Log org id used.
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites.
        logging.info("Fetched %s sites from the organization.", len(sites))  # Log fetched site count.
        flattened_sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten nested site fields.
        sanitized_sites = DataProcessingUtils.escape_multiline(flattened_sites)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(sanitized_sites, "SitesWithLocations.csv")  # type: ignore[no-untyped-call]
        print(f"! {len(sanitized_sites)} sites exported to SitesWithLocations.csv")  # Confirm export to operator.
        logging.info(" Full site data written to SitesWithLocations.csv")  # Log write success.

    @staticmethod
    def current_guests():  # Export current guest users.
        """
        Export all current guest users in the org to OrgCurrentGuests.csv
        """
        print("Current and Historical Guest Users:")  # Inform operator of export.
        logging.info("Exporting all current guest users in the org...")  # Log guest export start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        logging.debug("Using org_id: %s for current guest export.", org_id)  # Log org id used.
        response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(apisession, org_id, limit=1000)
        guests = mistapi.get_all(response=response, mist_session=apisession)  # Page through all guests.
        logging.info("Fetched %s current guest users from API.", len(guests))  # Log fetched guest count.
        guests = DataProcessingUtils.flatten_nested_fields(guests)  # Flatten nested guest fields.
        guests = DataProcessingUtils.escape_multiline(guests)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(guests, "OrgCurrentGuests.csv")  # type: ignore[no-untyped-call]
        print(f"! {len(guests)} current guest users exported to OrgCurrentGuests.csv")  # Confirm export to operator.
        logging.info(" Current guests exported to OrgCurrentGuests.csv")  # Log write success.

    @staticmethod
    def historical_guests():  # Export 7-day guest history.
        """
        Export all guest users from the last 7 days to OrgHistoricalGuests.csv
        """
        logging.info("Exporting all guest users from the last 7 days...")  # Log historical export start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        end_time = int(time.time())  # Capture end time as now.
        start_time = end_time - 7 * 24 * 3600  # Compute 7-day start time.
        logging.debug("Fetching guest authorizations from %s to %s (epoch seconds).", start_time, end_time)
        response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(  # Search guests in window.
            apisession, org_id, limit=1000, start=start_time, end=end_time
        )
        guests = mistapi.get_all(response=response, mist_session=apisession)  # Page through all guests.
        logging.info("Fetched %s historical guest users from API.", len(guests))  # Log fetched guest count.
        guests = DataProcessingUtils.flatten_nested_fields(guests)  # Flatten nested guest fields.
        guests = DataProcessingUtils.escape_multiline(guests)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(guests, "OrgHistoricalGuests.csv")  # type: ignore[no-untyped-call]
        print(f"! {len(guests)} historical guest users exported to OrgHistoricalGuests.csv")
        logging.info(" Historical guests exported to OrgHistoricalGuests.csv")  # Log write success.


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


class OrgDeviceStatsExporter:  # Org device-stats exporters.
    """
    Organization Device Statistics Exporter

    Handles device stats, port stats, VPN peer stats, and VC stats exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def _device_stats_cache_hit(output_file: str, fast: bool) -> bool:
        """Return True if fast-mode cache for OrgDeviceStats can be reused."""
        if not (fast and os.path.exists(output_file)):  # Cache reuse needs both flag + file
            return False  # No cache path available
        try:
            mtime = os.path.getmtime(output_file)  # Read file modified time
            age_minutes = (time.time() - mtime) / 60.0  # Compute file age in minutes
            if age_minutes < CSV_FRESHNESS_MINUTES:  # Cache still fresh
                logging.info(  # Log cache reuse
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    CSV_FRESHNESS_MINUTES,
                )
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # User notice
                return True  # Caller skips re-fetch
        except Exception as e:  # Freshness-check error
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, e)  # Log
        return False  # Cache stale or unreadable

    @staticmethod
    def device_stats(fast: bool = False):  # Export org device stats.
        """Export statistics for all devices in the organization to OrgDeviceStats.csv."""
        output_file = "OrgDeviceStats.csv"  # Output filename
        if OrgDeviceStatsExporter._device_stats_cache_hit(output_file, fast):  # Fast cache check
            return  # Skip re-fetch when cache fresh
        logging.info("Starting export of organization device statistics...")  # Log start
        emitter = PROGRESS_EMITTER  # Capture progress emitter
        if emitter:
            emitter.emit_progress_start("13", "device_stats", 1)  # Emit progress start
        op_start = time.time()  # Record operation start time
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Dynamic lookback hours
        TimeUtils.log_dynamic_lookback("org device statistics export", hours)  # Log lookback window
        APIDataFetcher(  # Fetch and write device stats
            title="Org Device Stats:",
            api_call=mistapi.api.v1.orgs.stats.listOrgDevicesStats,
            filename=output_file,
            sort_key="type",
            type="all",
            duration=f"{hours}h",
            limit=1000,
        ).execute()
        if emitter:
            emitter.emit_progress_complete(ProgressContext("13", "device_stats", 1), 1, False, time.time() - op_start)

    @staticmethod
    def _port_stats_cache_hit(output_file: str, fast: bool) -> bool:  # Check port-stats cache hit.
        """Return True when fast mode can safely reuse a fresh cached CSV."""
        if not (fast and os.path.exists(output_file)):  # Cache reuse needs flag + file
            return False  # No valid cache path
        try:  # Filesystem metadata lookup should never crash export path
            mtime = os.path.getmtime(output_file)  # Read last-modified time
            age_minutes = (time.time() - mtime) / 60.0  # Convert to minutes
            if age_minutes < CSV_FRESHNESS_MINUTES:  # Fresh cache means skip API
                logging.info(
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    CSV_FRESHNESS_MINUTES,
                )  # Record why no API calls were made
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # User notice
                return True  # Caller can return early
        except Exception as exception:  # Cache metadata problems degrade gracefully
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, exception)  # Log fallback
        return False  # Cache missing, stale, or unreadable

    @staticmethod
    def _load_port_stats_sites_from_api(org_id: str) -> list[tuple[str | None, str]]:
        """API fallback path for loading port-stats sites when cache fails."""
        site_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)  # API fallback
        site_data = mistapi.get_all(response=site_response, mist_session=apisession)  # Paginate
        sites = [
            (site.get("id"), site.get("name", "Unknown")) for site in site_data if site.get("id")
        ]  # Normalize into worker tuples
        logging.info("* Fetched %s sites from API", len(sites))  # API fallback count for cache-miss visibility
        logging.debug(
            "First site sample: %s, type: %s",
            sites[0] if sites else "No sites",
            type(sites[0]) if sites else "N/A",
        )  # One sample tuple for debug
        return sites  # Normalized site tuples for fast-mode worker pool

    @staticmethod
    def _log_first_site_sample(sites: list) -> None:
        """Emit a debug sample (first row + type) for cached-site lists, with empty-list fallback."""
        if sites:  # Non-empty: log the first row and its concrete type
            sample = sites[0]
            sample_type = type(sites[0])
        else:  # Empty: still emit placeholders so log lines stay parseable
            sample = "No sites"
            sample_type = "N/A"
        logging.debug("First site sample: %s, type: %s", sample, sample_type)  # Sample for malformed-row debug

    @staticmethod
    def _load_sites_from_cached_csv() -> list[tuple[str | None, str]] | None:
        """Read SiteList cache and return tuples, or ``None`` when the cache cannot be used."""
        try:  # Prefer cached site CSV to avoid extra API call
            CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # Ensure CSV exists
            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # Resolve path
            with open(site_list_path, encoding="utf-8") as file:  # Open cached CSV
                reader = csv.DictReader(file)  # Parse rows
                sites = [
                    (row.get("id"), row.get("name", "Unknown")) for row in reader if row.get("id")
                ]  # Build tuple list used by pool workers
        except Exception as exception:  # Cache read failure -> signal API fallback
            logging.warning("* Could not use cached sites, fetching from API: %s", exception)  # Explain fallback
            return None
        logging.info("* Loaded %s sites from cached data", len(sites))  # Confirm cached count
        OrgDeviceStatsExporter._log_first_site_sample(sites)  # Debug sample for malformed rows
        return sites

    @staticmethod
    def _load_port_stats_sites(org_id: str) -> list[tuple[str | None, str]]:  # Load sites for port stats.
        """Load site identifiers and names for fast-mode per-site port stats collection."""
        sites = OrgDeviceStatsExporter._load_sites_from_cached_csv()  # Cache-first path
        if sites is not None:  # Cache hit (possibly empty list)
            return sites
        return OrgDeviceStatsExporter._load_port_stats_sites_from_api(org_id)  # API fallback

    @staticmethod
    def _attempt_site_port_stats_fetch(site_id, site_name, connection_semaphore):
        """Single fetch attempt for one site's port stats; returns list or raises."""
        with connection_semaphore:  # Bound concurrent API calls
            response = mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts(apisession, site_id, limit=1000)
            port_stats = mistapi.get_all(response=response, mist_session=apisession)  # Paginate
        if not isinstance(port_stats, list):  # Defensive type check
            logging.error(
                "! API returned non-list type for site %s: type=%s, value=%s",
                site_name,
                type(port_stats),
                port_stats,
            )  # Log malformed payload
            return []  # Empty for malformed sites
        for stat in port_stats:  # Annotate each port row with site metadata
            stat["site_id"] = site_id  # Persist site identifier
            stat["site_name"] = site_name  # Persist site name
        return port_stats  # Annotated rows for caller

    @staticmethod
    def _handle_site_port_stats_retry(attempt, site_name, exception):
        """Backoff + log retry; return True if more attempts remain."""
        if attempt < FAST_MODE_MAX_RETRIES:  # More retries remain
            backoff_delay = FAST_MODE_RETRY_DELAY * (FastModeBackoffMultiplier.VALUE**attempt)  # Backoff curve
            logging.warning("! Attempt %s failed for site %s: %s", attempt + 1, site_name, exception)  # Log fail
            logging.info(
                "! Retrying in %.1fs (attempt %s/%s)",
                backoff_delay,
                attempt + 2,
                FAST_MODE_MAX_RETRIES + 1,
            )  # When next retry will occur
            time.sleep(backoff_delay)  # Pause before retry
            return True  # Continue loop
        logging.error("! Final attempt failed for site %s: %s", site_name, exception)  # Terminal failure
        return False  # No more retries

    @staticmethod
    def _fetch_site_port_stats(site_info, connection_semaphore):  # Fetch port stats for a site.
        """Fetch one site's switch/gateway port stats with bounded concurrency and retries."""
        site_id, site_name = site_info  # Unpack tuple
        for attempt in range(FAST_MODE_MAX_RETRIES + 1):  # Retry loop
            try:
                port_stats = OrgDeviceStatsExporter._attempt_site_port_stats_fetch(
                    site_id, site_name, connection_semaphore
                )
                if attempt > 0:  # Retries that later succeed get info-level log
                    logging.info(
                        "! Retry %s successful for site %s (%s records)",
                        attempt,
                        site_name,
                        len(port_stats),
                    )  # Successful retry outcome
                else:
                    logging.debug("! Collected %s port stats from site %s", len(port_stats), site_name)  # First-try
                return port_stats  # Annotated rows
            except Exception as exception:  # Retry on transient failure
                if not OrgDeviceStatsExporter._handle_site_port_stats_retry(attempt, site_name, exception):
                    return []  # Final failure path
        return []  # Defensive fallback

    @staticmethod
    def _process_retry_future(future, retry_futures, retry_results, still_failed):
        """Resolve one retried-site future; mutate retry_results + still_failed."""
        site_info = retry_futures[future]  # Recover original site tuple
        try:
            result = future.result()  # Resolve retried site rows
            if result:  # Site recovered
                retry_results.extend(result)  # Merge recovered rows
                logging.info(" FAST RETRY OK: %s", site_info[1])  # Record recovered site
            else:  # Site still failed logically
                still_failed.append(site_info)  # Keep for summary
                logging.warning(" FAST RETRY EMPTY: %s", site_info[1])  # Record unresolved
        except Exception as exception:  # Future itself raised unexpectedly
            still_failed.append(site_info)  # Preserve in failure list
            logging.error(" FAST RETRY EXC: %s -> %s", site_info[1], exception)  # Log

    @staticmethod
    def _dispatch_site_port_retries(failed_sites, connection_semaphore, retry_threads, retry_results, still_failed):
        """Run bounded retry pool and partition outcomes into retry_results / still_failed in place."""
        import concurrent.futures  # Local import keeps main module unchanged

        with ThreadPoolExecutor(max_workers=retry_threads) as executor:  # Bounded retry concurrency
            retry_futures = {
                executor.submit(OrgDeviceStatsExporter._fetch_site_port_stats, s, connection_semaphore): s
                for s in failed_sites
            }
            futures_list = list(retry_futures.keys())  # Materialize for tqdm total
            with tqdm(total=len(futures_list), desc="Retrying Failed Sites", unit="site") as pbar:  # type: ignore[call-arg, no-untyped-call]
                for future in concurrent.futures.as_completed(futures_list):  # Handle results as they complete
                    OrgDeviceStatsExporter._process_retry_future(future, retry_futures, retry_results, still_failed)
                    pbar.update(1)  # Advance progress

    @staticmethod
    def _retry_failed_site_port_stats(failed_sites, connection_semaphore):  # Retry failed site port stats.
        """Retry previously failed site fetches using a smaller worker pool."""
        retry_results: list = []  # Successful retry rows
        still_failed: list = []  # Sites remaining failed after retries
        retry_threads = min(
            FAST_MODE_RETRY_THREADS, len(failed_sites), max(1, FAST_MODE_MAX_CONCURRENT_CONNECTIONS - 2)
        )  # Smaller retry pool
        if retry_threads <= 0:  # Defensive guard
            logging.warning(" FAST MODE: No available threads for retry; skipping retries")  # Explain skip
            return [], failed_sites  # Preserve failed sites
        OrgDeviceStatsExporter._dispatch_site_port_retries(
            failed_sites, connection_semaphore, retry_threads, retry_results, still_failed
        )
        return retry_results, still_failed  # Return recovered rows + unresolved sites

    @staticmethod
    def _flatten_site_port_results(successful_results):  # Flatten site port results.
        """Flatten pooled worker results into one list of port-stat rows."""
        all_port_stats = []  # Accumulate all site-level rows into one export list.
        for index, result_list in enumerate(
            successful_results
        ):  # Inspect each worker result for defensive type handling.
            logging.debug(
                "Processing result %s: type=%s, is_list=%s", index, type(result_list), isinstance(result_list, list)
            )  # Log shape of each pooled result before flattening.
            if isinstance(result_list, list):  # Only list payloads are valid worker outputs.
                all_port_stats.extend(result_list)  # Merge valid site rows into the combined export list.
            else:  # Unexpected worker payloads should be visible but not fatal.
                logging.warning(
                    "Unexpected result type at index %s: %s, value: %s", index, type(result_list), result_list
                )  # Surface unexpected worker output for debugging.
        return all_port_stats  # Return flattened org-wide port-stat list for sorting and export.

    @staticmethod
    def _save_device_port_stats_output(all_port_stats, output_file: str) -> None:  # Save device port stats output.
        """Sort, sanitize, and persist collected port-stat rows."""
        if not all_port_stats:  # Empty dataset should skip file creation and clearly tell the operator why.
            logging.warning(" No port statistics collected. CSV not created.")  # Log absence of exportable data.
            print("! No port statistics collected. CSV not created.")  # Tell operator no file was written.
            return  # Nothing to sort or write.
        try:  # Sorting is best-effort because some rows may lack MACs.
            all_port_stats = sorted(
                all_port_stats, key=lambda row: row.get("mac", "")
            )  # Sort by MAC to produce deterministic CSV ordering.
        except Exception as exception:  # Sorting failures should not block export.
            logging.debug("Could not sort by MAC: %s", exception)  # Record sort failure while continuing unsorted.
        flattened = DataProcessingUtils.flatten_nested_fields(
            all_port_stats
        )  # Normalize nested API payloads into flat CSV-friendly records.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # type: ignore[no-untyped-call]  # Escape embedded newlines so CSV stays row-stable.
        DataExporter.write_with_format_selection(sanitized, output_file, api_function_name="searchSiteSwOrGwPorts")  # type: ignore[no-untyped-call]  # Persist to configured backend with endpoint metadata.
        print(
            f"! {len(all_port_stats)} port stat records exported to {output_file}"
        )  # Confirm output row count to the operator.
        logging.info(
            "! Port statistics saved to %s (%s records)", output_file, len(all_port_stats)
        )  # Record successful export count in logs.

    @staticmethod
    def _validate_fast_port_stats_start_time(start_time) -> None:
        """Defensive guard: fail loudly if start_time is not numeric (catches monkeypatch corruption)."""
        if isinstance(start_time, (int, float)):  # Normal numeric value -- nothing to do.
            return
        logging.error(
            "! CRITICAL: start_time is not a number! type=%s, value=%s", type(start_time), start_time
        )  # Surface impossible state.
        logging.error("! time module type: %s, time.time type: %s", type(time), type(time.time))  # Debugging context.
        raise TypeError(f"start_time must be a number, got {type(start_time)}")  # Elapsed calc would be invalid.

    @staticmethod
    def _log_fast_port_stats_summary(sites, failed_sites, all_port_stats, duration) -> None:
        """Emit operator-facing summary + structured log for fast-mode port stats run."""
        ok_count = len(sites) - len(failed_sites)  # Successful site count.
        fail_count = len(failed_sites)  # Failed site count.
        record_count = len(all_port_stats)  # Total port-stat rows collected.
        logging.info(
            " FAST MODE SUMMARY (port stats): sites_ok=%s sites_fail=%s records=%s elapsed=%.2fs",
            ok_count,
            fail_count,
            record_count,
            duration,
        )  # Structured run summary.
        print(
            f"* Fast mode: Collected {record_count} port stat records from {ok_count}/{len(sites)} sites in {duration:.1f}s"  # noqa: E501
        )  # Operator timing summary.

    @staticmethod
    def _run_fast_device_port_stats(output_file: str) -> None:  # Run fast device port stats.
        """Execute fast-mode site-parallel port stats collection and output."""
        logging.info(
            "* Fast mode: Parallelizing port stats retrieval across sites"
        )  # Announce fast-mode collection strategy.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org ID once before site discovery.
        sites = OrgDeviceStatsExporter._load_port_stats_sites(org_id)  # Load normalized site tuples from cache or API.
        start_time = time.time()  # Capture start time for performance summary.
        OrgDeviceStatsExporter._validate_fast_port_stats_start_time(start_time)  # Defensive numeric-type guard.
        successful_results, failed_sites = (
            ConnectionPoolExecutor.execute(  # Bounded-concurrency site collection with retry.
                work_items=sites,
                worker_function=OrgDeviceStatsExporter._fetch_site_port_stats,
                batch_description="sites",
                retry_function=OrgDeviceStatsExporter._retry_failed_site_port_stats,
            )
        )
        all_port_stats = OrgDeviceStatsExporter._flatten_site_port_results(
            successful_results
        )  # Collapse per-site results.
        duration = time.time() - start_time  # Elapsed seconds for operator summary.
        OrgDeviceStatsExporter._log_fast_port_stats_summary(
            sites, failed_sites, all_port_stats, duration
        )  # Emit summary log + print.
        OrgDeviceStatsExporter._save_device_port_stats_output(all_port_stats, output_file)  # Persist collected rows.

    @staticmethod
    def device_port_stats(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Export port-level statistics for switches and gateways to OrgDevicePortStats.csv.

        Fast mode caches recent CSV (CSV_FRESHNESS_MINUTES) and parallelizes site fetches with
        bounded concurrency. Non-fast mode issues one org-level paginated call. SECURITY: read-only.
        """
        output_file = "OrgDevicePortStats.csv"  # Stable filename for cache + downstream consumers.
        if OrgDeviceStatsExporter._port_stats_cache_hit(output_file, fast):  # Honor fast cache before API.
            return  # Fresh cache satisfied the request.
        logging.info("Starting export of organization device port statistics...")  # Log export start.
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve test-aware lookback window.
        TimeUtils.log_dynamic_lookback("org device port statistics export", hours)  # Record chosen window.
        if fast:  # Fast mode = site-parallel collection.
            OrgDeviceStatsExporter._run_fast_device_port_stats(output_file)  # Execute decomposed fast-mode workflow.
            return  # Fast-mode path owns the full export.
        APIDataFetcher(  # Non-fast mode = single org-level paginated fetch.
            title="Org Device Port Stats:",
            api_call=mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
            filename=output_file,
            sort_key="mac",
            limit=1000,
        ).execute()  # Execute pagination + export.

    @staticmethod
    def _vpn_peer_stats_cache_hit(output_file: str, fast: bool) -> bool:
        """Return True if fast-mode cache for VPN peer stats is fresh; emit cache-hit log + print."""
        if not (fast and os.path.exists(output_file)):  # Either non-fast or no file yet.
            return False
        try:
            mtime = os.path.getmtime(output_file)  # Disk mtime for freshness math.
            age_minutes = (time.time() - mtime) / 60.0  # Age in minutes.
            if age_minutes < CSV_FRESHNESS_MINUTES:  # Fresh enough to reuse.
                logging.info(
                    " Fast mode cache hit: %s is fresh (%.1fm < %sm); skipping fetch.",
                    output_file,
                    age_minutes,
                    CSV_FRESHNESS_MINUTES,
                )  # Structured log.
                print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # Operator-facing.
                return True
        except Exception as e:  # Freshness check failed -- fall through to fetch.
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, e)  # Debug-only.
        return False

    @staticmethod
    def vpn_peer_stats(fast: bool = False):  # Export VPN peer stats.
        """Export VPN peer path statistics to OrgVPNPeerStats.csv.

        Fast mode reuses recent CSV; normal mode does an org-level paginated fetch. SECURITY: read-only.
        """
        output_file = "OrgVPNPeerStats.csv"  # Output filename.
        if OrgDeviceStatsExporter._vpn_peer_stats_cache_hit(output_file, fast):  # Honor fast cache.
            return  # Cache satisfied.
        logging.info("Starting export of organization VPN peer path statistics...")  # Log start.
        emitter = PROGRESS_EMITTER  # Progress emitter (may be None).
        if emitter:  # Emitter present.
            emitter.emit_progress_start("15", "vpn_peer_stats", 1)  # Signal progress start.
        op_start = time.time()  # Start timer.
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Test-aware lookback.
        TimeUtils.log_dynamic_lookback("org vpn peer path statistics export", hours)  # Record lookback.
        APIDataFetcher(
            title="Org VPN Peer Stats:",
            api_call=mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
            filename=output_file,
            sort_key="mac",
            duration=f"{hours}h",
            limit=1000,
        ).execute()  # Run paginated org-level fetch + export.
        if emitter:  # Signal progress complete on the emitter.
            emitter.emit_progress_complete(ProgressContext("15", "vpn_peer_stats", 1), 1, False, time.time() - op_start)

    @staticmethod
    def switch_vc_stats():
        """
        Export virtual chassis stats (including stacking cable info) for all switches in the org.
        """
        from src.refactors.serial_cc.switch_vc_stats import SwitchVcStatsService

        SwitchVcStatsService.execute()


class OfflineDeviceReporter:
    """
    Offline Device Report (Menu 158)

    Scans org inventory via listOrgDevicesStats, filters devices offline
    beyond a user-configurable threshold (default 48h), displays summary
    and PrettyTable on screen, saves human-readable CSV to data/.

    Usage:
        OfflineDeviceReporter.execute()
    """

    MAX_DISPLAY_ROWS = 50
    DEFAULT_THRESHOLD_HOURS = 48
    MIN_THRESHOLD_HOURS = 1
    MAX_THRESHOLD_HOURS = 8760
    MAX_INPUT_RETRIES = 3

    @staticmethod
    def _parse_threshold_attempt(raw: str) -> int | None:
        """Parse one user attempt; return validated hours or None to retry."""
        try:
            hours = int(raw)  # Coerce to int.
            min_h = OfflineDeviceReporter.MIN_THRESHOLD_HOURS  # Local alias for line length.
            max_h = OfflineDeviceReporter.MAX_THRESHOLD_HOURS  # Local alias for line length.
            if min_h <= hours <= max_h:
                return hours  # Valid -- accept.
            print(f"! Threshold must be between {min_h} and {max_h} hours.")  # Out-of-range.
        except ValueError:
            print(f"! Invalid input '{raw}'. Please enter a number.")  # Bad type.
        return None

    @staticmethod
    def _prompt_threshold() -> int:
        """Prompt user for offline threshold in hours, with validation."""
        if IS_TEST_MODE:  # Test mode skips interactive prompt.
            logging.debug("Test mode: using default threshold 48 hours")  # Log shortcut.
            return OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS  # Default value.
        for attempt in range(OfflineDeviceReporter.MAX_INPUT_RETRIES):  # Bounded retry loop.
            raw = InputUtils.safe_input(
                f"Enter offline threshold in hours (default {OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS}): ",
                default_value=str(OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS),
                context="offline_threshold",
            )  # EOF-safe input.
            parsed = OfflineDeviceReporter._parse_threshold_attempt(raw)  # Validate this attempt.
            if parsed is not None:  # Valid value.
                return parsed
            remaining = OfflineDeviceReporter.MAX_INPUT_RETRIES - attempt - 1  # Attempts left.
            if remaining > 0:
                print(f"  ({remaining} attempt(s) remaining)")  # Tell user.
        logging.warning("Max retries exceeded for threshold input, using default 48 hours")  # Log fallback.
        print(f"  Using default threshold: {OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS} hours")  # Tell user.
        return OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS

    @staticmethod
    def _fetch_data(current_org_id: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
        """Fetch site lookup and device stats from Mist API."""
        logging.info("Fetching site information for offline device report...")
        print("  Fetching site information...")
        all_sites = APICoreFetchUtils.all_sites_with_limit(current_org_id)
        site_lookup: dict[str, str] = {}
        for site in all_sites:
            site_id = site.get("id")
            if site_id:
                site_lookup[site_id] = site.get("name", "Unknown Site")

        logging.info("Fetching device stats for offline device report...")
        print("  Fetching device statistics...")
        stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
            apisession, current_org_id, type="all", status="all", fields="*", limit=1000
        )
        all_devices: list[dict[str, Any]] = mistapi.get_all(response=stats_resp, mist_session=apisession)
        logging.info("Retrieved stats for %s devices", len(all_devices))
        print(f"  Retrieved {len(all_devices)} devices from API")
        return site_lookup, all_devices

    @staticmethod
    def _format_offline_timing(last_seen_epoch: float, offline_seconds: float) -> tuple[str, str, float]:
        """Return (last_seen_str, duration_str, sort_key) for one offline device."""
        if last_seen_epoch == 0.0:  # Device has never connected.
            return "Never Connected", "Never Connected", float("inf")
        last_seen_str = datetime.fromtimestamp(last_seen_epoch).strftime(
            "%Y-%m-%d %H:%M:%S"
        )  # Human-readable timestamp.
        total_hours = int(offline_seconds // 3600)  # Whole hours offline.
        days, hours = total_hours // 24, total_hours % 24  # Split into days and hours.
        duration_str = f"{days} days {hours} hours" if days > 0 else f"{hours} hours"  # Pick format.
        return last_seen_str, duration_str, offline_seconds

    @staticmethod
    def _compile_offline_record(
        device: dict, site_lookup: dict[str, str], last_seen_str: str, duration_str: str, sort_key: float
    ) -> dict:
        """Build the display/CSV record for one offline device."""
        device_type_raw = device.get("type", "unknown")  # Raw device type from API.
        type_display = {"ap": "AP", "switch": "Switch", "gateway": "Gateway"}.get(
            device_type_raw, device_type_raw.capitalize()
        )  # Friendly label.
        site_name = site_lookup.get(device.get("site_id", ""), "Unknown Site")  # Resolve site name.
        device_name = device.get("name") or "(unnamed)"  # Name fallback.
        return {
            "Device Name": device_name,
            "Device Type": type_display,
            "Site Name": site_name,
            "MAC Address": device.get("mac", ""),
            "Serial Number": device.get("serial", ""),
            "Model": device.get("model", ""),
            "Last Seen": last_seen_str,
            "Offline Duration": duration_str,
            "Status": device.get("status", "disconnected"),
            "_sort_key": str(sort_key),
        }

    @staticmethod
    def _parse_last_seen_epoch(device: dict) -> float:
        """Coerce a device's ``last_seen`` field to a float epoch (returns 0.0 when missing/blank)."""
        last_seen_raw = device.get("last_seen") or 0  # Treat None/blank/0 uniformly as 0
        if not last_seen_raw:  # Explicit guard so the float() cast can never see empty
            return 0.0
        return float(last_seen_raw)  # Numeric epoch ready for arithmetic

    @staticmethod
    def _maybe_build_offline_record(
        device: dict, site_lookup: dict[str, str], now: float, threshold_seconds: int
    ) -> dict | None:
        """Return offline record for device if it qualifies as offline; None to skip."""
        if device.get("status") == "connected":  # Skip currently-connected devices
            return None
        last_seen_epoch = OfflineDeviceReporter._parse_last_seen_epoch(device)  # Float epoch (0.0 = never seen)
        offline_seconds = now - last_seen_epoch  # Time since last contact
        if offline_seconds < threshold_seconds and last_seen_epoch > 0:  # Inside threshold + seen before
            return None
        last_seen_str, duration_str, sort_key = OfflineDeviceReporter._format_offline_timing(
            last_seen_epoch, offline_seconds
        )  # Format display values
        return OfflineDeviceReporter._compile_offline_record(device, site_lookup, last_seen_str, duration_str, sort_key)

    @staticmethod
    def _process_devices(
        all_devices: list[dict[str, Any]],
        site_lookup: dict[str, str],
        threshold_hours: int,
    ) -> list[dict[str, Any]]:
        """Filter offline devices beyond threshold, enrich with site names."""
        now = time.time()  # Current epoch.
        threshold_seconds = threshold_hours * 3600  # Convert threshold to seconds.
        offline_records: list[dict[str, Any]] = []  # Accumulator.
        for device in all_devices:  # Walk all devices once.
            record = OfflineDeviceReporter._maybe_build_offline_record(
                device, site_lookup, now, threshold_seconds
            )  # Build or skip.
            if record is not None:  # Device qualifies as offline.
                offline_records.append(record)
        offline_records.sort(key=lambda r: float(r["_sort_key"]), reverse=True)  # Sort by offline duration desc.
        return offline_records

    @staticmethod
    def _render_offline_breakdowns(type_counts: dict[str, int], site_counts: dict[str, int]) -> None:
        """Print 'By Type' and 'Top 5 Sites' breakdowns from precomputed counts."""
        print("\nBy Type:")  # Header for type breakdown.
        for device_type in ["AP", "Switch", "Gateway"]:  # Stable display order.
            count = type_counts.get(device_type, 0)  # Lookup count.
            if count > 0:  # Suppress zeros.
                print(f"  {device_type}s: {count}")
        sorted_sites = sorted(site_counts.items(), key=lambda item: item[1], reverse=True)[:5]  # Top 5 by count.
        if sorted_sites:
            print("\nTop 5 Sites:")  # Header for the leaderboard.
            for rank, (site_name, count) in enumerate(sorted_sites, 1):  # Rank each top site.
                print(f"  {rank}. {site_name}: {count} offline")  # Print rank and count.

    @staticmethod
    def _display_summary(
        total_device_count: int,
        offline_records: list[dict[str, str]],
        threshold_hours: int,
    ) -> None:
        """Display summary statistics before the detail table."""
        print("\n--- Summary ---")  # Section header.
        print(f"Total devices in org: {total_device_count:,}")  # Total count.
        print(f"Devices offline > {threshold_hours} hours: {len(offline_records)}")  # Offline count.
        type_counts: dict[str, int] = {}  # Per-type tally.
        site_counts: dict[str, int] = {}  # Per-site tally.
        for record in offline_records:  # Walk each offline record once.
            type_counts[record["Device Type"]] = type_counts.get(record["Device Type"], 0) + 1  # Bump type.
            site_counts[record["Site Name"]] = site_counts.get(record["Site Name"], 0) + 1  # Bump site.
        OfflineDeviceReporter._render_offline_breakdowns(type_counts, site_counts)  # Render breakdowns.

    _OFFLINE_DISPLAY_FIELDS: tuple[str, ...] = (
        "Device Name",
        "Device Type",
        "Site Name",
        "MAC Address",
        "Serial Number",
        "Model",
        "Last Seen",
        "Offline Duration",
        "Status",
    )

    @staticmethod
    def _save_offline_csv(offline_records: list[dict[str, str]], total_count: int) -> None:
        """Build CSV rows and persist via shared exporter; log + print result."""
        fields = OfflineDeviceReporter._OFFLINE_DISPLAY_FIELDS  # Column order.
        csv_records = [{f: record.get(f, "") for f in fields} for record in offline_records]  # Strip helper keys.
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")  # Timestamp for filename.
        filename = f"OfflineDeviceReport_{timestamp_str}.csv"  # Output filename.
        DataExporter.write_with_format_selection(
            data=csv_records, filename_or_table=filename, api_function_name="listOrgDevicesStats"
        )  # Persist.
        logging.info("CSV saved: data/%s (%s devices)", filename, total_count)  # Log save.
        print(f"\nCSV saved: data/{filename} ({total_count} devices)")  # Operator-facing.

    @staticmethod
    def _present_results(offline_records: list[dict[str, str]]) -> None:  # Render and save offline results.
        """Display PrettyTable and save CSV for offline devices."""
        fields = OfflineDeviceReporter._OFFLINE_DISPLAY_FIELDS  # Column order.
        total_count = len(offline_records)  # Total rows.
        show_count = min(total_count, OfflineDeviceReporter.MAX_DISPLAY_ROWS)  # Cap display.
        print(f"\n--- Offline Devices (showing {show_count} of {total_count}) ---")  # Header.
        table = PrettyTable()  # Build display table.
        table.field_names = list(fields)  # Set columns.
        for record in offline_records[:show_count]:  # Show capped rows.
            table.add_row([record.get(f, "") for f in fields])  # Add each row.
        print(table)  # Print table.
        OfflineDeviceReporter._save_offline_csv(offline_records, total_count)  # Persist CSV + log.

    @staticmethod
    def _gather_offline_inputs() -> tuple[str | None, int]:
        """Resolve org_id + threshold prompt; (None, _) signals early-abort."""
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        if not current_org_id:  # No org selected.
            print("! No organization selected. Exiting.")  # Tell the user.
            return None, 0  # Caller must abort.
        threshold_hours = OfflineDeviceReporter._prompt_threshold()  # Prompt threshold.
        print(f"Threshold: {threshold_hours} hours\n")  # Echo selection.
        return current_org_id, threshold_hours

    @staticmethod
    def _finalize_offline_report(
        total_count: int, offline_records: list[dict], threshold_hours: int, start_time: float
    ) -> None:
        """Display summary + present results + log elapsed for offline report."""
        OfflineDeviceReporter._display_summary(total_count, offline_records, threshold_hours)  # Summary section.
        OfflineDeviceReporter._present_results(offline_records)  # Detail table + CSV.
        elapsed = time.time() - start_time  # Elapsed wall time.
        logging.info("Offline device report completed in %.1f seconds", elapsed)  # Log duration.
        print(f"\nReport completed in {elapsed:.1f} seconds")  # Tell user.

    @staticmethod
    def execute() -> None:  # Run the offline report.
        """Main entry point for offline device report (Menu 158)."""
        print("\n=== Offline Device Report ===")  # Header.
        logging.info("Starting offline device report...")  # Log start.
        start_time = time.time()  # Start timer.
        current_org_id, threshold_hours = OfflineDeviceReporter._gather_offline_inputs()  # Org + threshold.
        if not current_org_id:  # Abort signaled.
            return
        try:
            site_lookup, all_devices = OfflineDeviceReporter._fetch_data(current_org_id)  # Fetch sites + devices.
        except Exception as error:  # Fetch failed.
            logging.error("Failed to fetch data from Mist API: %s", error)  # Log error.
            print("! Failed to fetch data. Please check your API credentials and network connection.")  # Tell user.
            return
        if not all_devices:  # No devices in org.
            logging.info("No devices found in organization")  # Log it.
            print("No devices found in this organization.")  # Tell user.
            return
        offline_records = OfflineDeviceReporter._process_devices(all_devices, site_lookup, threshold_hours)  # Filter.
        if not offline_records:  # Nothing offline.
            print(f"No devices found offline for more than {threshold_hours} hours. All clear!")  # All-clear.
            logging.info("No devices offline beyond %sh threshold", threshold_hours)  # Log all-clear.
            return
        OfflineDeviceReporter._finalize_offline_report(len(all_devices), offline_records, threshold_hours, start_time)


# --- OrgDeviceInventorySummary facade removed (1013 SC-001 Cat B pos 29) ---
# Canonical implementation lives in src/inventory/org_device_inventory_summary_facade.py; re-exported above.


# OrgTemplateExporter moved to src/export/org_template_exporter.py (1013 SC-001 position 22)


# OrgClientSecurityExporter body removed 1013 SC-001 P32 -- see src/export/org_client_security_exporter.py.


class FilterOperatorEngine:  # Filter operator evaluation engine.
    """Shared operator catalog, normalization, and evaluation for client search filtering."""

    OPERATOR_CATALOG: list[str] = [  # Supported operator names.
        "is",
        "is not",
        "contains",
        "doesn't contain",
        "starts with",
        "doesn't start with",
        "ends with",
        "doesn't end with",
        "is blank",
        "is not blank",
        "is null",
        "is not null",
    ]

    VALUE_REQUIRED_OPERATORS: frozenset[str] = frozenset(  # Operators needing a value.
        {
            "is",
            "is not",
            "contains",
            "doesn't contain",
            "starts with",
            "doesn't start with",
            "ends with",
            "doesn't end with",
        }
    )

    REMOTE_PREFILTER_OPERATORS: frozenset[str] = frozenset(  # Operators pushed to the API.
        {
            "is",
        }
    )

    @staticmethod
    def normalize_mac(mac_value: str) -> str:  # Normalize a MAC string.
        """Remove delimiters and lowercase for delimiter-insensitive comparison."""
        if not mac_value:  # Empty input.
            return ""  # Return empty.
        return re.sub(r"[:\-.]", "", mac_value).lower()  # Strip separators; lowercase.

    @staticmethod
    def normalize_text(text_value: str) -> str:  # Normalize free text.
        """Lowercase and strip for case-insensitive comparison."""
        if not text_value:  # Empty input.
            return ""  # Return empty.
        return text_value.strip().lower()  # Trim and lowercase.

    @staticmethod
    def evaluate_operator(field_value: str | None, operator: str, search_value: str, is_mac: bool = False) -> bool:
        """Evaluate a single operator against a field value. Returns True if record matches."""
        if operator in ("is null", "is not null", "is blank", "is not blank"):  # Null/blank operators.
            return FilterOperatorEngine._evaluate_null_blank(field_value, operator)  # Delegate null/blank check.
        if field_value is None or str(field_value).strip() == "":  # Empty field fails value ops.
            return False  # No match.
        normalized = FilterOperatorEngine._normalize_pair(str(field_value), search_value, is_mac)
        return FilterOperatorEngine._evaluate_value_operator(normalized[0], operator, normalized[1])

    @staticmethod
    def validate_operator_value(operator: str, value: str, field_name: str) -> bool:  # Validate operator+value pair.
        """Validate that value-required operators have non-empty normalized values."""
        if operator in FilterOperatorEngine.VALUE_REQUIRED_OPERATORS:  # Value-required operator?
            if not value or not value.strip():  # Missing value.
                logging.warning("Operator '%s' for %s requires a non-empty value", operator, field_name)
                print(f"\n  Operator '{operator}' requires a value for {field_name}. Please try again.")
                return False  # Invalid.
        return True  # Valid.

    # Null/blank operator -> predicate. Dict dispatch keeps _evaluate_null_blank flat (no if-chain/booleans).
    _NULL_BLANK_OPERATORS = {
        "is null": lambda field_value: field_value is None,  # True when the field is absent
        "is not null": lambda field_value: field_value is not None,  # True when the field is present
        "is blank": lambda field_value: (
            field_value is not None and str(field_value).strip() == ""
        ),  # Present but empty/whitespace
    }

    @staticmethod
    def _evaluate_null_blank(field_value: str | None, operator: str) -> bool:  # Evaluate null/blank operators.
        """Evaluate null/blank operators against a field value (default: 'is not blank')."""
        predicate = FilterOperatorEngine._NULL_BLANK_OPERATORS.get(operator)  # Look up the operator predicate
        if predicate:  # A null/null/blank operator matched
            return predicate(field_value)  # Apply its predicate
        return field_value is not None and str(field_value).strip() != ""  # Default: 'is not blank'

    @staticmethod
    def _normalize_pair(field_value: str, search_value: str, is_mac: bool) -> tuple[str, str]:
        """Normalize field and search values for comparison."""
        if is_mac:  # MAC comparison.
            return FilterOperatorEngine.normalize_mac(field_value), FilterOperatorEngine.normalize_mac(search_value)
        return FilterOperatorEngine.normalize_text(field_value), FilterOperatorEngine.normalize_text(search_value)

    @staticmethod
    def _evaluate_value_operator(field: str, operator: str, search: str) -> bool:  # Apply a value operator.
        """Evaluate value-based positional/equality operators."""
        operator_map: dict[str, Any] = {  # Operator -> comparator map.
            "is": lambda f, s: f == s,
            "is not": lambda f, s: f != s,
            "contains": lambda f, s: s in f,
            "doesn't contain": lambda f, s: s not in f,
            "starts with": lambda f, s: f.startswith(s),
            "doesn't start with": lambda f, s: not f.startswith(s),
            "ends with": lambda f, s: f.endswith(s),
            "doesn't end with": lambda f, s: not f.endswith(s),
        }
        evaluator = operator_map.get(operator)  # Look up the comparator.
        return evaluator(field, search) if evaluator else False  # Compare or default false.


# GlobalWiredClientReportGenerator moved to src/reports/global_wired_client_report_generator.py (1013 SC-001 position 36)  # noqa: E501


# WiredClientManufacturerReportGenerator moved to src/reports/wired_client_manufacturer_report_generator.py  # noqa: E501
# (1013 SC-001 position 26)


# OrgAdminExporter moved to src/export/org_admin_exporter.py (1013 SC-001 position 20)


# LicenseExportUtils moved to src/export/license_export_utils.py (1013 SC-001 position 24)


# NOTE: SelfExportUtils has been extracted to src/export/self_export_utils.py (issue #1013 SC-001 position 7)


# OrgConfigExporter moved to src/export/org_config_exporter.py (issue #1013 SC-001 position 31)


class OrgExportUtils:  # Generic org export helpers.
    """
    Centralized organization-level data export utilities.
    Groups all export_org_* functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    # Org-level switch/gateway insight metrics accept only byte-throughput choices. The count-type
    # choices in the constants ('total_*_count', 'num_used_*') are valid solely at site/switch scope
    # and return HTTP 400 "Bad Syntax" at org scope, so org expansion is restricted to this set.
    _ORG_VALID_METRIC_CHOICES = ("bytes", "rx_bytes", "tx_bytes")  # Org-scope-valid parameterized metric choices

    @staticmethod
    def export_data(api_call, data_type, sort_key="name", limit=1000, **api_kwargs):  # Export an org endpoint.
        """Generic org-data export: build Org<DataType>.csv from `api_call`, pass `limit`/extras as API kwargs."""
        logging.info("Starting export of organization %s...", data_type)  # Log start.

        # Create filename from data_type
        safe_data_type = data_type.replace(" ", "").replace("-", "").title()  # Sanitize for filename.
        filename = f"Org{safe_data_type}.csv"  # Build the CSV name.

        fetcher_kwargs = dict(api_kwargs)  # Copy extra kwargs.
        if limit is not None:  # Limit provided.
            fetcher_kwargs["limit"] = limit  # Set the page limit.

        APIDataFetcher(  # Fetch and write.
            title=f"Organization {data_type.title()}:",
            api_call=api_call,
            filename=filename,
            sort_key=sort_key,
            **fetcher_kwargs,
        ).execute()

    @staticmethod
    def _collect_one_sle_type(
        org_id: str,
        sle_type: str,
        all_sites_sle_data: list,
    ) -> None:
        """Fetch sites-SLE rows for one type and append (tagged) into the shared accumulator."""
        try:
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(  # Call the SLE API for this type.
                apisession, org_id, sle=sle_type, duration="7d", limit=1000
            )
            sites_sle_data = mistapi.get_all(response=response, mist_session=apisession) or []  # Page all rows.
            for site_data in sites_sle_data:  # Tag each row with its SLE type.
                site_data["sle_type"] = sle_type  # Record the SLE type on the row.
                all_sites_sle_data.append(site_data)  # Collect into accumulator.
            logging.debug("Retrieved SLE data for %s sites with SLE type: %s", len(sites_sle_data), sle_type)
        except Exception as exception:  # Fetch failed — skip this type but continue overall.
            logging.warning("Failed to get sites SLE data for type %s: %s", sle_type, exception)  # Warn and skip.

    @staticmethod
    def _persist_sites_sle_summary(all_sites_sle_data: list) -> None:
        """Persist aggregated sites-SLE rows to OrgSitesSLESummary.csv (or write empty + warn)."""
        if all_sites_sle_data:  # Have data — flatten + write + tell user.
            processed = DataProcessingUtils.flatten_nested_fields(all_sites_sle_data)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # CSV-safe.
            DataExporter.write_with_format_selection(processed, "OrgSitesSLESummary.csv")  # type: ignore[no-untyped-call]
            print(f"! {len(processed)} sites SLE summary exported to OrgSitesSLESummary.csv")  # Tell the user.
            logging.info("Exported %s sites SLE summary to OrgSitesSLESummary.csv", len(processed))  # Log count.
            return  # Done.
        print("! 0 sites SLE summary exported to OrgSitesSLESummary.csv (no data available)")  # Tell user zero.
        logging.warning("No sites SLE data available for organization")  # Warn no data.
        DataExporter.write_with_format_selection([], "OrgSitesSLESummary.csv")  # type: ignore[no-untyped-call]

    @staticmethod
    def _gather_all_sites_sle(org_id: str, sle_types: list, emitter: Any) -> tuple[list, int]:
        """Walk SLE types, accumulate rows, tick progress per type; return (rows, items_done)."""
        all_sites_sle_data: list = []  # Accumulator for SLE rows across types.
        items_done = 0  # Items processed counter.
        for sle_type in sle_types:  # Fetch each SLE type.
            OrgExportUtils._collect_one_sle_type(org_id, sle_type, all_sites_sle_data)  # Fetch + tag + accumulate.
            items_done += 1  # Count this item regardless of success/failure.
            if emitter:  # Emitter present — tick progress for UI.
                emitter.emit_progress_tick(
                    ProgressContext("67", "sites_sle_summary", len(sle_types)),
                    sle_type,
                    items_done,
                    len(sle_types) - items_done,
                )
        return all_sites_sle_data, items_done  # Caller persists + emits completion.

    @staticmethod
    def sites_sle_summary():  # Export sites SLE summary.
        """Export SLE summary metrics for all sites in the organization to OrgSitesSLESummary.csv."""
        print("Export Organization Sites SLE Summary:")  # Header.
        logging.info("Starting export of sites SLE summary...")  # Log start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        sle_types = ["wifi", "wired", "wan"]  # SLE types to fetch.
        emitter = PROGRESS_EMITTER  # Progress emitter handle.
        if emitter:  # Emitter present.
            emitter.emit_progress_start("67", "sites_sle_summary", len(sle_types))  # Signal progress start.
        op_start = time.time()  # Start the timer.
        all_sites_sle_data, items_done = OrgExportUtils._gather_all_sites_sle(  # Walk types + tick.
            org_id, sle_types, emitter
        )
        OrgExportUtils._persist_sites_sle_summary(all_sites_sle_data)  # Write CSV (or empty placeholder).
        if emitter:  # Emitter present.
            emitter.emit_progress_complete(  # Signal progress complete.
                ProgressContext("67", "sites_sle_summary", len(sle_types)),
                items_done,
                False,
                time.time() - op_start,
            )

    @staticmethod
    def _metric_choice_list(definition: Any) -> list[str]:  # Choices for one metric definition.
        """Return the 'metric' sub-parameter choices for one insight-metric definition, or []."""
        if not isinstance(definition, dict):  # Definition payload must be a mapping
            return []  # No choices to extract
        params = definition.get("params")  # Parameter specs block (may be absent)
        if not isinstance(params, dict):  # Params must be a mapping to hold a 'metric' spec
            return []  # No choices to extract
        metric_param = params.get("metric")  # The 'metric' sub-parameter spec, if any
        if not isinstance(metric_param, dict):  # Spec must be a mapping to hold choices
            return []  # No choices to extract
        choices = metric_param.get("choices")  # Allowed values the API enumerates for this metric
        return list(choices) if isinstance(choices, list) else []  # Normalize to a plain list

    @staticmethod
    def _org_valid_choices(choices: list[str]) -> list[str]:  # Keep org-scope-valid choices only.
        """Filter metric choices down to the byte-throughput set the org-scope endpoint accepts."""
        return [choice for choice in choices if choice in OrgExportUtils._ORG_VALID_METRIC_CHOICES]  # Drop count-type

    @staticmethod
    def _extract_metric_choices(definitions: Any) -> dict[str, list[str]]:  # Build the parameterized map.
        """Extract {metric_name: [choices]} from a listInsightMetrics definitions mapping."""
        parameterized: dict[str, list[str]] = {}  # Accumulates metrics that require a 'metric' choice
        if not isinstance(definitions, dict):  # Guard against unexpected payload shapes
            return parameterized  # Nothing to extract
        for metric_name, definition in definitions.items():  # Inspect every metric definition
            declared = OrgExportUtils._metric_choice_list(definition)  # All choices the metric declares
            choices = OrgExportUtils._org_valid_choices(declared)  # Restrict to org-scope-valid choices
            if choices:  # Only metrics with at least one org-valid choice are expandable here
                parameterized[metric_name] = choices  # Record the org-valid sub-metric choices
        return parameterized  # Completed metric -> choices mapping

    @staticmethod
    def _load_parameterized_metric_choices() -> dict[str, list[str]]:  # Discover parameterized metrics.
        """Return {metric_name: [choices]} for org insight metrics requiring a 'metric' sub-parameter.

        Some org insight metrics (e.g. switch-metrics, gateway-metrics) declare a 'metric'
        query parameter in their constants definition. getOrgSle cannot supply it, so a bare
        call returns HTTP 400 "Bad Syntax". Reading the live constants lets callers expand each
        such metric into one request per valid choice instead of failing.
        """
        logging.info("Loading parameterized insight-metric choices from Mist constants...")  # Trace the lookup
        try:  # The constants call may fail offline -> degrade to no expansion
            response = mistapi.api.v1.const.insight_metrics.listInsightMetrics(apisession)  # GET /const/insight_metrics
            definitions = getattr(response, "data", response) or {}  # Unwrap to the metric -> definition map
        except Exception as exception:  # Any failure simply disables expansion this run
            logging.error("Failed to load insight-metric constants for parameter expansion: %s", exception)  # Trace
            return {}  # No parameterized map available
        parameterized = OrgExportUtils._extract_metric_choices(definitions)  # Pull choices from the definitions
        logging.debug("Discovered %s parameterized org insight metrics", len(parameterized))  # Trace the count
        return parameterized  # Map of metric -> required choices

    @staticmethod
    def _fetch_single_metric_choice(
        org_id: str, metric: str, choice: str, duration: str
    ) -> dict[str, Any] | None:  # One (metric, choice) GET.
        """Issue the org-insight GET for one (metric, choice) pair; return a tagged record or None."""
        uri = f"/api/v1/orgs/{org_id}/insights/{metric}"  # Org insight endpoint for this parameterized metric
        query = {"metric": choice, "duration": duration}  # Required 'metric' choice plus the lookback window
        logging.debug("Fetching parameterized metric %s with metric=%s", metric, choice)  # Trace the attempt
        session = apisession  # Local handle so the Any | None global can be narrowed below
        if session is None:  # No authenticated session available (defensive guard)
            logging.error("No API session available to fetch parameterized metric %s", metric)  # Trace the gap
            return None  # Cannot fetch without a session
        try:  # Per-choice failures must not abort the whole export
            response = session.mist_get(uri=uri, query=query)  # Low-level GET (SDK cannot pass query 'metric')
            payload = getattr(response, "data", None)  # Unwrap the response data payload
        except Exception as exception:  # Network/HTTP failure for this specific choice
            logging.debug("Failed to fetch %s metric=%s: %s", metric, choice, exception)  # Trace the miss
            return None  # Signal failure to the caller
        if not payload:  # Empty payload means no data for this choice
            return None  # Signal empty to the caller
        record = dict(payload) if isinstance(payload, dict) else {"results": payload}  # Normalize to a dict row
        record["metric_type"] = f"{metric}:{choice}"  # Tag the composite metric type for the export
        record["org_id"] = org_id  # Tag the owning org
        record["metric_param"] = choice  # Tag which sub-metric this row represents
        return record  # Completed tagged record

    @staticmethod
    def _fetch_parameterized_org_metric(
        org_id: str, metric: str, choices: list[str], duration: str
    ) -> tuple[list[dict[str, Any]], int, int]:  # Expand a metric across its choices.
        """Fetch one parameterized org insight metric across each required 'metric' choice.

        getOrgSle cannot pass the required 'metric' query parameter, so this issues the GET
        directly for each choice. Returns (records, retrieved, failed).
        """
        records: list[dict[str, Any]] = []  # Collected per-choice time-series records
        retrieved = 0  # Successful choice fetches
        failed = 0  # Failed or empty choice fetches
        for choice in choices:  # Each valid sub-metric value (e.g. bytes, rx_bytes, total_port_count)
            record = OrgExportUtils._fetch_single_metric_choice(org_id, metric, choice, duration)  # One GET
            if record:  # Choice returned a usable payload
                records.append(record)  # Keep the tagged record
                retrieved += 1  # Count the success
            else:  # No data or the request failed
                failed += 1  # Count the miss
        logging.debug("Parameterized metric %s: %s retrieved, %s failed", metric, retrieved, failed)  # Trace totals
        return records, retrieved, failed  # Aggregate result for this metric

    @staticmethod
    def _insight_is_worst_sites_metric(metric: str) -> bool:
        """Return True when a metric needs site-level SLE analysis (issue #470: hoisted to keep dispatch CC low)."""
        return "worst-sites" in metric or metric in (
            "sites-sle",
            "sites-sle-filtered",
        )  # These metrics require getOrgSitesSle rather than the plain getOrgSle endpoint.

    @staticmethod
    def _insight_build_sites_result(
        org_id: str, metric: str, sle_category: str, sites_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build one aggregated site-SLE insight result row for a metric+category pair."""
        return {  # One aggregated record describing this metric/category combination.
            "metric_type": f"{metric}_{sle_category}",  # Composite metric+category identifier.
            "org_id": org_id,  # Tag the owning org.
            "sle_category": sle_category,  # Record which SLE category this row covers.
            "data_source": "sites_sle_analysis",  # Mark the provenance of this aggregated row.
            "total_sites": len(sites_data),  # How many sites contributed to this category.
            "sites_data": sites_data,  # The raw per-site SLE rows for downstream normalization.
            "original_metric": metric,  # Preserve the requesting metric name.
        }

    @staticmethod
    def _insight_fetch_one_sle_category(org_id: str, metric: str, sle_category: str) -> dict[str, Any] | None:
        """Fetch one SLE category's site data; return aggregated result row, or None when empty/failed."""
        try:  # Isolate this category so one failure doesn't abort the others.
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(  # Call the sites-SLE API for this category.
                apisession, org_id, sle=sle_category, duration="7d", limit=1000
            )
            sites_data = mistapi.get_all(response=response, mist_session=apisession) or []  # Page all site rows.
            if not sites_data:  # Category empty — log and return None.
                logging.debug("No sites data for insight metric: %s with SLE: %s", metric, sle_category)
                return None  # No data for this category.
            logging.debug(  # Trace the successful category fetch with its site count.
                "Got %s sites for insight metric: %s SLE: %s", len(sites_data), metric, sle_category
            )
            return OrgExportUtils._insight_build_sites_result(org_id, metric, sle_category, sites_data)
        except Exception as sites_error:  # Category fetch failed; log and report None without counting a failure.
            logging.debug("Failed to get sites data for metric '%s' SLE '%s': %s", metric, sle_category, sites_error)
            return None  # Treat the failed category as no data.

    @staticmethod
    def _insight_fetch_worst_sites_sle(org_id: str, metric: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch one site-SLE metric across wifi/wan/wired categories; return (records, retrieved, failed)."""
        records: list[dict[str, Any]] = []  # Aggregated per-category insight results for this metric.
        retrieved = 0  # Count of categories that returned usable site data.
        for sle_category in ("wifi", "wan", "wired"):  # The three SLE service categories to analyze.
            result = OrgExportUtils._insight_fetch_one_sle_category(org_id, metric, sle_category)  # One category fetch.
            if result is not None:  # The category returned usable data.
                records.append(result)  # Collect the aggregated category result.
                retrieved += 1  # Count this category as a successful retrieval.
        return records, retrieved, 0  # Failures are absorbed per-category, so the failed count stays zero here.

    @staticmethod
    def _insight_fetch_default_metric(org_id: str, metric: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch one ordinary metric via getOrgSle; return (records, retrieved, failed)."""
        response = mistapi.api.v1.orgs.insights.getOrgSle(apisession, org_id, metric, duration="7d")  # Direct SLE GET.
        insight_data = getattr(response, "data", response) or {}  # Unwrap the response payload; default to empty.
        if insight_data:  # The metric returned a usable payload.
            insight_data["metric_type"] = metric  # Tag the metric name onto the payload.
            insight_data["org_id"] = org_id  # Tag the owning org onto the payload.
            logging.debug("Successfully retrieved org insight data for metric: %s", metric)  # Trace the success.
            return [insight_data], 1, 0  # One retrieved record, no failures.
        logging.debug("No data available for org metric: %s", metric)  # Trace the empty payload.
        return [], 0, 1  # No data counts as a single failed metric (matches the original behavior).

    @staticmethod
    def _insight_fetch_one_metric(
        org_id: str, metric: str, parameterized_metrics: dict[str, list[str]]
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Dispatch one metric to the right fetch strategy; return (records, retrieved, failed)."""
        try:  # Any metric-level failure is caught here so the overall loop continues.
            logging.debug("Attempting to retrieve org insight metric: %s", metric)  # Trace the attempt.
            if metric in parameterized_metrics:  # Parameterized metric -> expand across its required 'metric' choices.
                records, ok, fail = OrgExportUtils._fetch_parameterized_org_metric(  # One GET per valid choice.
                    org_id, metric, parameterized_metrics[metric], "7d"
                )
                logging.debug("Expanded parameterized metric %s into %s records", metric, len(records))  # Trace expand.
                return records, ok, fail  # Hand back the per-choice aggregate.
            if OrgExportUtils._insight_is_worst_sites_metric(metric):  # Site-SLE metric -> per-category analysis.
                return OrgExportUtils._insight_fetch_worst_sites_sle(org_id, metric)  # Fetch across wifi/wan/wired.
            return OrgExportUtils._insight_fetch_default_metric(org_id, metric)  # Ordinary metric -> single getOrgSle.
        except Exception as metric_error:  # The metric failed entirely; count it and keep going.
            logging.debug("Failed to get org insight data for metric '%s': %s", metric, metric_error)  # Trace failure.
            return [], 0, 1  # No records, one failed metric.

    @staticmethod
    def _insight_fetch_sites_sle_summary(org_id: str) -> tuple[list[dict[str, Any]], int, int]:
        """Fetch the org-wide sites SLE summary; return (records, retrieved, failed)."""
        try:  # Isolate the summary fetch so its failure doesn't abort the export.
            logging.debug("Attempting to retrieve org sites SLE summary")  # Trace the attempt.
            response = mistapi.api.v1.orgs.insights.getOrgSitesSle(apisession, org_id, duration="7d", limit=100)  # GET.
            sites_data = mistapi.get_all(response=response, mist_session=apisession) or []  # Page all summary rows.
            if sites_data:  # The summary returned site rows.
                for item in sites_data:  # Tag each row with its metric type and org.
                    item["metric_type"] = "org_sites_sle_summary"  # Mark these as the sites SLE summary.
                    item["org_id"] = org_id  # Tag the owning org.
                logging.debug("Successfully retrieved org sites SLE data for %s sites", len(sites_data))  # Trace count.
                return list(sites_data), 1, 0  # All rows as records; counts as one successful retrieval.
            return [], 0, 0  # No summary data; neither retrieved nor failed (matches original).
        except Exception as sites_error:  # Summary fetch failed.
            logging.debug("Failed to get org sites SLE summary: %s", sites_error)  # Trace the failure.
            return [], 0, 1  # Count the summary as a single failure.

    @staticmethod
    def _insight_collect_all_metrics(
        org_id: str, org_metrics: list[str], parameterized_metrics: dict[str, list[str]]
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Retrieve every org-scope metric plus the sites SLE summary; return (all_records, retrieved, failed)."""
        all_insight_data: list[dict[str, Any]] = []  # Accumulate every metric's records.
        metrics_retrieved = 0  # Running count of successful retrievals.
        metrics_failed = 0  # Running count of failed or empty retrievals.
        for metric in org_metrics:  # Process each org-scoped metric independently.
            records, retrieved, failed = OrgExportUtils._insight_fetch_one_metric(  # Dispatch to the right strategy.
                org_id, metric, parameterized_metrics
            )
            all_insight_data.extend(records)  # Collect this metric's records.
            metrics_retrieved += retrieved  # Fold in its successful count.
            metrics_failed += failed  # Fold in its failed count.
        summary_records, summary_ok, summary_fail = OrgExportUtils._insight_fetch_sites_sle_summary(org_id)  # Summary.
        all_insight_data.extend(summary_records)  # Collect the summary rows.
        metrics_retrieved += summary_ok  # Fold in the summary success count.
        metrics_failed += summary_fail  # Fold in the summary failure count.
        return all_insight_data, metrics_retrieved, metrics_failed  # Hand the aggregate back to the orchestrator.

    @staticmethod
    def _insight_normalize_records(all_insight_data: list[dict[str, Any]], org_id: str) -> dict[str, list]:  # type: ignore[type-arg]
        """Normalize raw insight rows into the four output buckets (summary, time_series, results, sites_data)."""
        buckets: dict[str, list] = {  # type: ignore[type-arg]  # One list per normalized output file.
            "summary": [],  # Rows destined for OrgMetricsSummary.csv.
            "time_series": [],  # Rows destined for OrgMetricsTimeSeries.csv.
            "results": [],  # Rows destined for OrgMetricsResults.csv.
            "sites_data": [],  # Rows destined for OrgSitesData.csv.
        }
        for metric_data in all_insight_data:  # Normalize each raw metric record.
            normalized = InsightMetricsUtils.parse_to_normalized_data(metric_data, org_id)  # Split into the 4 buckets.
            for key in buckets:  # Fold each bucket's rows into the accumulator.
                buckets[key].extend(normalized[key])  # Collect this record's contribution to the bucket.
        return buckets  # Return the four populated buckets.

    @staticmethod
    def _insight_export_normalized(all_insight_data: list[dict[str, Any]], org_id: str, metrics_retrieved: int) -> None:
        """Normalize the insight rows and export them to the four normalized CSVs plus the legacy combined file."""
        print("! Parsing metrics into normalized data structures...")  # Tell the user normalization is starting.
        buckets = OrgExportUtils._insight_normalize_records(all_insight_data, org_id)  # Build the 4 output buckets.
        print("! Exporting to normalized CSV files...")  # Tell the user the writes are starting.
        outputs = [  # Drive the four normalized writes from one table to avoid repeated blocks.
            (buckets["summary"], "OrgMetricsSummary.csv", "summary"),  # Summary file + its label.
            (buckets["time_series"], "OrgMetricsTimeSeries.csv", "time series"),  # Time-series file + label.
            (buckets["results"], "OrgMetricsResults.csv", "results"),  # Results file + label.
            (buckets["sites_data"], "OrgSitesData.csv", "sites"),  # Sites file + label.
        ]
        for rows, filename, label in outputs:  # Write each normalized bucket to its CSV.
            processed = DataProcessingUtils.escape_multiline(rows)  # type: ignore[no-untyped-call]  # Escape newlines.
            DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]  # Write it.
            print(f"  !? {len(processed)} {label} records -> {filename}")  # Report this file's row count.
        print(
            f"\n! Successfully exported {metrics_retrieved} organization insight metrics to 4 normalized CSV files"  # noqa: E501
        )  # Summarize the export for the user.
        logging.info(  # Log the export totals for traceability.
            "Exported %s org insight data points from %s metrics to normalized CSV files",
            len(all_insight_data),
            metrics_retrieved,
        )
        OrgExportUtils._insight_write_combined(all_insight_data)  # Also write the combined compatibility file.

    @staticmethod
    def _insight_write_combined(all_insight_data: list[dict[str, Any]]) -> None:
        """Write the flattened combined insight file (OrgInsightMetrics_Legacy.csv) for backward compatibility."""
        processed_combined = DataProcessingUtils.flatten_nested_fields(all_insight_data)  # Flatten for combined.
        processed_combined = DataProcessingUtils.escape_multiline(processed_combined)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(processed_combined, "OrgInsightMetrics_Legacy.csv")  # type: ignore[no-untyped-call]
        print("  !? Legacy format maintained -> OrgInsightMetrics_Legacy.csv")  # Confirm the file write.

    @staticmethod
    def _insight_write_empty_outputs(include_legacy: bool = True) -> None:
        """Write empty normalized CSVs so downstream consumers always see the expected files."""
        files = [  # The four normalized output files are always written.
            "OrgMetricsSummary.csv",
            "OrgMetricsTimeSeries.csv",
            "OrgMetricsResults.csv",
            "OrgSitesData.csv",
        ]
        if include_legacy:  # The no-data and error paths also write the legacy combined file.
            files.append("OrgInsightMetrics_Legacy.csv")  # Include the legacy file when requested.
        for filename in files:  # Write an empty dataset to each output file.
            DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # Empty write.

    @staticmethod
    def _insight_setup_or_empty() -> list[str] | None:
        """Refresh and load org-scope metrics; write empty outputs and return None when none exist."""
        print("Export Organization Insight Metrics (Normalized):")  # Header for the operation.
        logging.info("Starting export of organization insight metrics with normalized structure...")  # Log start.
        print("! Refreshing available insight metrics from Mist API...")  # Tell the user about the refresh.
        InsightMetricsUtils.export_const_insight_metrics()  # Refresh ConstInsightMetrics.csv before scope filtering.
        org_metrics = InsightMetricsUtils.get_by_scope("org")  # Load the metrics that support org scope.
        if not org_metrics:  # No org-scope metrics are available.
            print("! No metrics found for org scope. Check ConstInsightMetrics.csv file.")  # Tell the user.
            logging.error("No org-scope metrics found in const insight metrics")  # Log the error condition.
            OrgExportUtils._insight_write_empty_outputs(include_legacy=False)  # Write the 4 empty normalized files.
            return None  # Signal the orchestrator to abort.
        return org_metrics  # Hand the org-scope metric list back to the orchestrator.

    @staticmethod
    def _insight_report_totals(metrics_retrieved: int, metrics_failed: int) -> None:
        """Print and log the retrieval totals for the insight-metrics run."""
        print(f"! Metric retrieval completed: {metrics_retrieved} successful, {metrics_failed} failed")  # Tell user.
        logging.info(
            "Org insight metrics: %s retrieved successfully, %s failed", metrics_retrieved, metrics_failed
        )  # Log the retrieval totals for traceability.

    @staticmethod
    def insight_metrics():
        """Export organization-wide insight metrics to normalized CSV files."""
        org_metrics = OrgExportUtils._insight_setup_or_empty()  # Refresh + load org metrics (None means abort early).
        if org_metrics is None:  # Setup wrote empty outputs and signaled there is nothing to export.
            return  # Abort the export.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org to query.
        print(f"! Retrieving {len(org_metrics)} different organization insight metrics...")  # Tell the user the count.
        print("! Processing each metric individually with proper error handling...")  # Explain the per-metric handling.
        parameterized_metrics = OrgExportUtils._load_parameterized_metric_choices()  # Metrics needing a 'metric' param.
        try:  # Guard the whole fetch-and-export so a failure still leaves consistent empty outputs.
            all_insight_data, metrics_retrieved, metrics_failed = OrgExportUtils._insight_collect_all_metrics(  # Fetch.
                org_id, org_metrics, parameterized_metrics
            )
            OrgExportUtils._insight_report_totals(metrics_retrieved, metrics_failed)  # Report + log the totals.
            if all_insight_data:  # At least one metric returned data.
                OrgExportUtils._insight_export_normalized(all_insight_data, org_id, metrics_retrieved)  # Write CSVs.
            else:  # Every metric failed or returned empty.
                print("! 0 organization insight metrics exported (no data available)")  # Tell the user zero.
                logging.warning("No org insight data available - all metrics failed or returned empty")  # Warn no data.
                OrgExportUtils._insight_write_empty_outputs(include_legacy=True)  # Write the 5 empty files.
        except Exception as exception:  # The export failed unexpectedly.
            print(f"! Error exporting organization insight metrics: {exception}")  # Tell the user about the error.
            logging.error("Failed to export org insight metrics: %s", exception)  # Log the failure with context.
            OrgExportUtils._insight_write_empty_outputs(include_legacy=True)  # Write the 5 empty files on error.

    @staticmethod
    def _nac_clients():  # Export NAC clients.
        """Export NAC clients to OrgNacClients.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClients, data_type="nac clients", sort_key="mac"
        )

    @staticmethod
    def _nac_tags():  # Export NAC tags.
        """Export NAC tags to OrgNacTags.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nactags.listOrgNacTags, data_type="nac tags", sort_key="name"
        )

    @staticmethod
    def _nac_portals():  # Export NAC portals.
        """Export NAC portals to OrgNacPortals.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nacportals.listOrgNacPortals, data_type="nac portals", sort_key="name"
        )

    @staticmethod
    def _nac_rules():  # Export NAC rules.
        """Export NAC rules to OrgNacRules.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nacrules.listOrgNacRules, data_type="nac rules", sort_key="name"
        )

    @staticmethod
    def _nac_events():  # Export NAC events.
        """Export NAC events to OrgNacEvents.csv."""
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve lookback hours.
        TimeUtils.log_dynamic_lookback("org NAC events export", hours)  # Log the window.
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.nac_clients.searchOrgNacClientEvents,
            data_type="nac events",
            sort_key="timestamp",
            duration=f"{hours}h",
        )

    @staticmethod
    def _assets():  # Export assets.
        """Export organization assets to OrgAssets.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgAssets, data_type="assets", sort_key="name"
        )

    @staticmethod
    def _bgp_peers():  # Export BGP peers.
        """Export BGP peer data to OrgBgpPeers.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgBgpStats, data_type="bgp peers", sort_key="peer_ip"
        )

    @staticmethod
    def _tunnel_stats():  # Export tunnel stats.
        """Export tunnel statistics to OrgTunnelStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgTunnelsStats, data_type="tunnel stats", sort_key="name"
        )

    @staticmethod
    def _site_stats():  # Export site stats.
        """Export site statistics to OrgSiteStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.listOrgSiteStats, data_type="site stats", sort_key="name"
        )

    @staticmethod
    def _mxedge_stats():  # Export Mist Edge stats.
        """Export MX Edge statistics to OrgMxedgeStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.listOrgMxEdgesStats, data_type="mx edge stats", sort_key="name"
        )

    @staticmethod
    def e911_report():  # Export E911 report.
        """Export E911 report for the organization to OrgE911Report.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.exports.getOrgE911Report,
            data_type="e911 report",
            sort_key="name",
            limit=None,  # pyright: ignore[reportArgumentType] - getOrgE911Report takes no limit param
        )

    @staticmethod
    def jsi_pbn():  # Export JSI PBN.
        """Export JSI PBN (Product Bulletin Notifications) data to OrgJsiPbn.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.jsi.searchOrgJsiPbn,
            data_type="jsi pbn",
            sort_key="id",
        )

    @staticmethod
    def jsi_sirt():  # Export JSI SIRT.
        """Export JSI SIRT (Security Incident Response Team) advisories to OrgJsiSirt.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.jsi.searchOrgJsiSirt,
            data_type="jsi sirt",
            sort_key="id",
        )

    @staticmethod
    def ospf_stats():  # Export OSPF stats.
        """Export OSPF adjacency statistics for the organization to OrgOspfStats.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.stats.searchOrgOspfStats,
            data_type="ospf stats",
            sort_key="mac",
        )

    @staticmethod
    def _security_intel_profiles():  # Export security intel profiles.
        """Export security intelligence profiles to OrgSecurityIntelProfiles.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles,
            data_type="security intel profiles",
            sort_key="name",
        )

    @staticmethod
    def _invites():  # Export invites.
        """Export organization invites to OrgInvites.csv."""
        OrgExportUtils.export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.orgs.invites.listOrgInvites, data_type="invites", sort_key="email"
        )

    @staticmethod
    def _build_audit_log_kwargs(full_history: bool, duration: str | None) -> dict[str, Any]:
        """Resolve API kwargs (limit + duration/start) for org audit-log listing based on caller flags."""
        kwargs: dict[str, Any] = {"limit": 1000}  # Base API params.
        if duration:  # Caller-supplied duration takes priority.
            kwargs["duration"] = duration  # Set explicit duration string.
            logging.info("Exporting audit logs for duration: %s", duration)  # Log the window.
            return kwargs  # Done.
        if not full_history:  # No duration, recent-only mode.
            hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve lookback hours.
            TimeUtils.log_dynamic_lookback("audit logs export", hours)  # Log the window.
            kwargs["duration"] = f"{hours}h"  # Set the duration.
            logging.info("Exporting only last %s hours of audit logs (duration=%sh).", hours, hours)
            return kwargs  # Done.
        kwargs["start"] = 0  # Full history from start.
        logging.info("Exporting full audit log history (start=0).")  # Log full history.
        return kwargs  # Done.

    @staticmethod
    def audit_logs(full_history: bool = False, duration: str | None = None) -> None:  # Export audit logs.
        """Export org audit logs (24h/explicit duration/full history) to OrgAuditLogs.csv."""
        logging.info("Menu #22: Starting audit logs export")  # Log start.
        logging.debug("ENTRY: OrgExportUtils.audit_logs(full_history=%s, duration=%s)", full_history, duration)
        try:
            org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
            kwargs = OrgExportUtils._build_audit_log_kwargs(full_history, duration)  # Resolve API kwargs.
            logging.debug("Making API call with parameters: %s", kwargs)  # Trace the params.
            response = mistapi.api.v1.orgs.logs.listOrgAuditLogs(apisession, org_id, **kwargs)  # List audit logs.
            rawdata = mistapi.get_all(response=response, mist_session=apisession)  # Page all rows.
            if not rawdata:  # No rows.
                logging.warning(" No audit logs returned from API.")  # Warn none returned.
                logging.debug("EXIT: OrgExportUtils.audit_logs - no data")  # Trace exit.
                return  # Abort.
            data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
            data = DataProcessingUtils.escape_multiline(data)  # type: ignore[no-untyped-call]
            DataExporter.write_with_format_selection(data, "OrgAuditLogs.csv")  # type: ignore[no-untyped-call]
            print(f"! {len(data)} audit logs exported to OrgAuditLogs.csv")  # Tell the user.
            logging.info("Completed audit logs export and wrote results to OrgAuditLogs.csv.")  # Log completion.
            logging.info("Menu #22: Audit logs export completed - %s records", len(data))  # Log the count.
            logging.debug("EXIT: OrgExportUtils.audit_logs - success")  # Trace success.
        except Exception as e:  # Export failed.
            logging.error("Failed to export audit logs: %s", e)  # Log the error.
            logging.debug("EXIT: OrgExportUtils.audit_logs - error")  # Trace exit.
            raise  # Re-raise to caller.

    @staticmethod
    def sle_metrics(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Export organization-wide SLE (Service Level Experience) metrics to OrgSLEMetrics.csv."""
        from src.refactors.serial_cc.sle_metrics import SLEMetricsService  # Import the SLE service.

        SLEMetricsService.execute(fast)  # Run the SLE export.

    @staticmethod
    def ssid_template_consolidation() -> None:  # Consolidate SSID templates.
        """SSID template consolidation workflow (Menu #145). Delegates to src.ssid_consolidation."""
        from src.ssid_consolidation.ssid_template_consolidation import (  # noqa: PLC0415
            SSIDTemplateConsolidationManager as _Impl,
        )

        _Impl.execute(  # Delegate to the impl.
            apisession=apisession,
            page_limit=DEFAULT_API_PAGE_LIMIT,
            safe_input_fn=InputUtils.safe_input,
            write_data_fn=DataExporter.write_with_format_selection,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
        )

    @staticmethod
    def e911_bssid_compliance_report() -> None:  # E911 BSSID compliance report.
        """E911 BSSID compliance report (Menu #89). Delegates to src.reports.e911_bssid."""
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        if not current_org_id:  # No org.
            print("! No organization selected. Exiting.")  # Tell the user.
            return  # Abort.
        E911BSSIDReportGenerator.execute(  # Run the report.
            apisession=apisession,
            page_limit=DEFAULT_API_PAGE_LIMIT,
            org_id=current_org_id,
            safe_input_fn=InputUtils.safe_input,
            write_data_fn=DataExporter.write_with_format_selection,
        )


# ============================================================================
# SITE DATA EXPORT UTILITIES CLASS
# ============================================================================


# SiteDeviceExporter moved to src/export/site_device_exporter.py (1013 SC-001 position 34)


# SiteClientExporter moved to src/export/site_client_exporter.py (1013 SC-001 position 14)


# SiteConfigExporter moved to src/export/site_config_exporter.py (1013 SC-001 position 19)


class SiteAnomalyExporter:  # Site anomaly exporters.
    """
    Site Anomaly and Event Exporter

    Handles site-level anomaly events and insight metrics exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def anomaly_events():
        """Export comprehensive anomaly events for a selected site to SiteAnomalyEvents_[SiteName].csv."""
        print("Export Site Anomaly Events:")  # User-visible header.
        logging.info("Starting export of site anomaly events...")  # Trace start of export.
        site_id = PromptUtils.select_site()  # Prompt the user for a site.
        if not site_id:  # No site chosen.
            print("! No site selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve display name for filename.
        filename = f"SiteAnomalyEvents_{EnhancedSSHRunner.sanitize_filename(site_name)}.csv"  # Build CSV name.
        metrics = SiteAnomalyExporter._discover_site_anomaly_metrics()  # Discover anomaly metric names.
        if not metrics:  # Nothing to fetch.
            return  # Abort the export.
        try:
            data, count = SiteAnomalyExporter._aggregate_site_anomaly_data(site_id, site_name, metrics)  # Fetch.
            SiteAnomalyExporter._export_anomaly_data(data, filename, "site anomaly event", count, site_name)  # CSV
        except Exception as exception:  # Broader export failure (flatten/write).
            print(f"! Error exporting site anomaly events: {exception}")  # Tell the user.
            logging.error("Failed to export site anomaly events for %s: %s", site_name, exception)  # Log it.

    @staticmethod
    def device_anomaly_events():
        """Export device anomaly events to SiteDeviceAnomalyEvents_[Site]_[Device].csv."""
        print("Export Site Device Anomaly Events:")  # User-visible header.
        logging.info("Starting export of site device anomaly events...")  # Trace start of export.
        site_id = PromptUtils.select_site()  # Prompt the user for a site.
        if not site_id:  # No site chosen.
            print("! No site selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve display name.
        selection = PromptUtils.select_device_id_from_inventory(site_id)  # Prompt for a device.
        if not selection:  # No device chosen.
            print("! No device selected. Exiting.")  # Tell the user.
            return  # Abort the export.
        device_mac, device_name = selection[0], selection[1]  # Unpack the MAC and display name.
        filename = SiteAnomalyExporter._build_device_filename(site_name, device_name)  # Build the CSV name.
        metrics = ["ap_availability", "throughput", "capacity"]  # Device anomaly metric names.
        try:
            data, count = SiteAnomalyExporter._aggregate_device_anomaly_data(
                site_id, site_name, device_mac, device_name, metrics
            )  # Loop + fetch each metric.
            SiteAnomalyExporter._export_anomaly_data(data, filename, "device anomaly event", count, device_name)  # CSV
        except Exception as exception:  # Broader export failure (flatten/write).
            print(f"! Error exporting device anomaly events: {exception}")  # Tell the user.
            logging.error("Failed to export device anomaly events for %s: %s", device_name, exception)  # Log it.

    @staticmethod
    def _build_device_filename(site_name: str, device_name: str) -> str:
        """Build the device anomaly CSV filename from sanitized site + device names."""
        sanitized_site = EnhancedSSHRunner.sanitize_filename(site_name)  # Sanitize the site name.
        sanitized_device = EnhancedSSHRunner.sanitize_filename(device_name)  # Sanitize the device name.
        return f"SiteDeviceAnomalyEvents_{sanitized_site}_{sanitized_device}.csv"  # Compose CSV name.

    @staticmethod
    def _discover_site_anomaly_metrics() -> list[str]:
        """Discover potential site anomaly metric names, announce them, return [] when none found."""
        print("! Discovering potential anomaly metrics from Mist API definitions...")  # Tell the user.
        potential = AnomalyMetricsDiscovery.discover()  # Pull discovery list from CSV.
        names = [info["metric_name"] for info in potential]  # Extract just the metric names.
        print(f"! Found {len(names)} potential anomaly metrics:")  # Tell the user the count.
        for info in potential:  # Show each metric to the user.
            print(f"  - {info['metric_name']}: {info['description'][:60]}...")  # Trim long descriptions.
        if not names:  # No metrics discovered at all.
            print("! No potential anomaly metrics found. Please check ConstInsightMetrics.csv availability.")
        return names  # Return the names (possibly empty).

    @staticmethod
    def _fetch_one_anomaly_metric(
        fetch_callable: Any, metric: str, tags: dict[str, str], scope: tuple[str, str]
    ) -> dict[str, Any] | None:
        """Invoke fetch_callable() for one metric, tag the result, return data dict or None on no-data/error."""
        display_label, data_type = scope  # Unpack the scope tuple for printing + tagging.
        try:
            response = fetch_callable()  # Issue the API call (callable is already bound via functools.partial).
            data = getattr(response, "data", response) or {}  # Unwrap data; default empty.
            if data:  # API returned actual data for this metric.
                data["metric_type"] = metric  # Tag the metric name.
                data["data_type"] = data_type  # Tag the data type for downstream consumers.
                for key, value in tags.items():  # Apply caller-supplied tags (site_id, site_name, ...).
                    data[key] = value  # Set each tag on the result row.
                print(f"!? Retrieved {metric} {display_label}")  # Tell the user.
                logging.debug("Successfully retrieved %s %s for %s", metric, display_label, tags)  # Trace success.
                return data  # Return the tagged row.
            print(f"! No {metric} {display_label} available")  # Tell the user the metric had no data.
            logging.info("No %s %s available for %s", metric, display_label, tags)  # Log the absence.
            return None  # Signal caller to skip.
        except Exception as metric_error:  # This metric's fetch failed.
            print(f"! Error retrieving {metric} {display_label}: {metric_error}")  # Tell the user.
            logging.warning("Error retrieving %s %s for %s: %s", metric, display_label, tags, metric_error)  # Warn.
            return None  # Signal caller to skip.

    @staticmethod
    def _run_anomaly_metric_loop(
        metrics: list[str],
        fetch_builder: Callable[[str], Callable],
        tags: dict[str, Any],
        scope: tuple[str, str],
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop metrics with mistapi loggers silenced; build fetch with fetch_builder(metric); collect tagged rows."""
        original_levels = SiteAnomalyExporter._anomaly_suppress_mistapi_loggers()  # Quiet mistapi internal loggers.
        rows: list[dict[str, Any]] = []  # Accumulator for successful rows.
        count = 0  # Number of metrics that returned data.
        try:
            for metric in metrics:  # Fetch each metric.
                fetch = fetch_builder(metric)  # Build per-metric fetch callable.
                row = SiteAnomalyExporter._fetch_one_anomaly_metric(fetch, metric, tags, scope)  # Fetch + tag.
                if row is not None:  # Metric returned data.
                    rows.append(row)  # Collect the row.
                    count += 1  # Bump the success counter.
        finally:
            SiteAnomalyExporter._anomaly_restore_loggers(original_levels)  # Always restore loggers.
        return rows, count  # Hand the aggregate back to the orchestrator.

    @staticmethod
    def _aggregate_site_anomaly_data(
        site_id: str, site_name: str, metrics: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop site anomaly metrics with mistapi loggers silenced; return (rows, success_count)."""
        tags = {"site_id": site_id, "site_name": site_name}  # Tags attached to every row.
        scope = ("anomaly events", "site_anomaly_events")  # Display label + data_type tag.
        print(f"! Retrieving {len(metrics)} different site anomaly events...")  # Tell the user.
        builder = lambda metric: functools.partial(  # noqa: E731 — bind site-anomaly fetch per metric.
            mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents, apisession, site_id, metric
        )
        return SiteAnomalyExporter._run_anomaly_metric_loop(metrics, builder, tags, scope)  # Shared loop.

    @staticmethod
    def _aggregate_device_anomaly_data(
        site_id: str, site_name: str, device_mac: str, device_name: str, metrics: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Loop device anomaly metrics with mistapi loggers silenced; return (rows, success_count)."""
        tags = {  # Tags attached to every row.
            "site_id": site_id,
            "site_name": site_name,
            "device_mac": device_mac,
            "device_name": device_name,
        }
        scope = ("device anomaly data", "device_anomaly_events")  # Display label + data_type tag.
        print(f"! Retrieving {len(metrics)} different device anomaly events for {device_name}...")  # Tell the user.
        builder = lambda metric: functools.partial(  # noqa: E731 — bind device-anomaly fetch per metric.
            mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForDevice, apisession, site_id, metric, device_mac
        )
        return SiteAnomalyExporter._run_anomaly_metric_loop(metrics, builder, tags, scope)  # Shared loop.

    @staticmethod
    def _export_anomaly_data(
        data_list: list[dict[str, Any]], filename: str, label: str, success_count: int, scope_name: str
    ) -> None:
        """Flatten + escape + write the aggregated anomaly rows, or write an empty CSV when there is no data."""
        if data_list:  # At least one metric returned data.
            processed = DataProcessingUtils.flatten_nested_fields(data_list)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
            DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
            print(f"! {success_count} {label} types exported to {filename}")  # Tell the user the count.
            logging.info("Exported %s %s types for %s to %s", success_count, label, scope_name, filename)  # Log.
        else:  # No data from any metric.
            print(f"! 0 {label}s exported to {filename} (no data available)")  # Tell the user zero.
            logging.warning("No %s available for %s", label, scope_name)  # Warn about the empty result.
            DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]

    _CLIENT_ANOMALY_METRICS = (  # Client-specific anomaly metrics (verified working) shared by the count + loop.
        "successful_connect",  # Note: uses underscore, not hyphen for the client endpoint.
        "roaming",  # Client roaming issues.
        "throughput",  # Client throughput anomalies.
    )

    @staticmethod
    def _anomaly_resolve_site_name(site_id: str) -> str:
        """Resolve the human-readable site name for a site_id, falling back to the id on lookup failure."""
        try:  # The site-name lookup is best-effort; the id is an acceptable fallback for the filename.
            response = mistapi.api.v1.sites.listSites(apisession, site_id)  # List the site.
            sites = mistapi.get_all(response=response, mist_session=apisession)  # Page all rows.
            return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # Resolve site name.
        except Exception:  # Lookup failed.
            return site_id  # Fall back to the id.

    @staticmethod
    def _anomaly_lookup_client_hostname(site_id: str, client_mac: str) -> str:
        """Look up a client's hostname from its wireless stats, falling back to the MAC on failure."""
        try:  # Hostname enrichment is best-effort; the MAC is an acceptable fallback.
            response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(  # List client stats.
                apisession, site_id, limit=100, duration="1d"
            )
            clients = getattr(response, "data", response) or []  # Unwrap data; default empty.
            for client in clients:  # Find the matching client.
                if client.get("mac") == client_mac:  # MAC matches.
                    return client.get("hostname", client.get("name", "Unknown"))  # Read the hostname.
            return "Unknown"  # No matching client found in the stats.
        except Exception as exception:  # Lookup failed.
            logging.warning("Could not retrieve client hostname for %s: %s", client_mac, exception)  # Warn the failure.
            return client_mac  # Fall back to the MAC address.

    @staticmethod
    def _anomaly_suppress_mistapi_loggers() -> dict:  # type: ignore[type-arg]
        """Raise mistapi logger levels to CRITICAL to keep the console clean; return their original levels."""
        mistapi_loggers = [
            "apirequest",
            "apiresponse",
            "mistapi",
            "mistapi.apirequest",
            "mistapi.apiresponse",
        ]  # Names.
        original_levels = {}  # Save original levels for later restoration.
        for logger_name in mistapi_loggers:  # Quiet each mistapi logger.
            logger_instance = logging.getLogger(logger_name)  # Get the logger.
            original_levels[logger_name] = logger_instance.level  # Remember its level.
            logger_instance.setLevel(logging.CRITICAL)  # Suppress ERROR logs temporarily.
        return original_levels  # Original levels keyed by logger name.

    @staticmethod
    def _anomaly_restore_loggers(original_levels: dict) -> None:  # type: ignore[type-arg]
        """Restore mistapi logger levels saved by _anomaly_suppress_mistapi_loggers."""
        for logger_name, original_level in original_levels.items():  # Restore each logger level.
            logging.getLogger(logger_name).setLevel(original_level)  # Restore the saved level.

    @staticmethod
    def _anomaly_fetch_one_metric(
        site_id: str, client_mac: str, site_name: str, client_hostname: str, metric: str
    ) -> dict | None:  # type: ignore[type-arg]
        """Fetch one client anomaly metric and tag it with site/client metadata; return the record, or None if empty."""
        response = mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForClient(  # Get client anomalies for this metric.
            apisession, site_id, client_mac, metric
        )
        client_anomaly_data = getattr(response, "data", response) or {}  # Unwrap data; default empty.
        if not client_anomaly_data:  # The metric returned no data.
            return None  # Signal an empty metric.
        client_anomaly_data["metric_type"] = metric  # Tag the metric.
        client_anomaly_data["site_id"] = site_id  # Tag the site.
        client_anomaly_data["site_name"] = site_name  # Tag the site name.
        client_anomaly_data["client_mac"] = client_mac  # Tag the client MAC.
        client_anomaly_data["client_hostname"] = client_hostname  # Tag the hostname.
        client_anomaly_data["data_type"] = "client_anomaly_events"  # Tag the data type.
        return client_anomaly_data  # The tagged anomaly record.

    @staticmethod
    def _anomaly_handle_metric_result(record: dict | None, metric: str, client_mac: str, all_data: list) -> int:  # type: ignore[type-arg]
        """Record one fetched metric: append + announce on data, announce 'none' otherwise; return 1 if kept else 0."""
        if record is not None:  # The metric returned data.
            all_data.append(record)  # Collect the row.
            print(f"!? Retrieved {metric} client anomaly data")  # Tell the user.
            logging.debug("Successfully retrieved %s client anomaly data for %s", metric, client_mac)  # Trace.
            return 1  # One successful metric.
        print(f"! No {metric} client anomaly data available")  # Tell the user none.
        logging.info("No %s client anomaly data available for %s", metric, client_mac)  # Log none.
        return 0  # No data for this metric.

    @staticmethod
    def _anomaly_collect_metrics(
        site_id: str, client_mac: str, site_name: str, client_hostname: str
    ) -> tuple[list, int]:  # type: ignore[type-arg]
        """Fetch all client anomaly metrics for one client; return (records, retrieved_count)."""
        print(
            f"! Retrieving {len(SiteAnomalyExporter._CLIENT_ANOMALY_METRICS)} different client anomaly events for {client_mac} ({client_hostname})..."  # noqa: E501
        )  # Tell the user how many metrics will be fetched.
        all_client_anomaly_data = []  # Accumulate anomaly rows.
        metrics_retrieved = 0  # Success count.
        for metric in SiteAnomalyExporter._CLIENT_ANOMALY_METRICS:  # Fetch each metric independently.
            try:  # Isolate per-metric failures so one bad metric doesn't abort the rest.
                record = SiteAnomalyExporter._anomaly_fetch_one_metric(  # Fetch + tag one metric.
                    site_id, client_mac, site_name, client_hostname, metric
                )
                metrics_retrieved += SiteAnomalyExporter._anomaly_handle_metric_result(  # Record + announce outcome.
                    record, metric, client_mac, all_client_anomaly_data
                )
            except Exception as metric_error:  # Metric fetch failed.
                print(f"! Error retrieving {metric} client anomaly data: {metric_error}")  # Tell the user.
                logging.warning(
                    "Error retrieving %s client anomaly data for %s: %s", metric, client_mac, metric_error
                )  # Warn the failure.
        return all_client_anomaly_data, metrics_retrieved  # Collected rows and the success count.

    @staticmethod
    def _anomaly_export(all_data: list, metrics_retrieved: int, client_mac: str, filename: str) -> None:  # type: ignore[type-arg]
        """Flatten and write the collected client anomaly rows to CSV (writes an empty file when there is no data)."""
        if all_data:  # At least one metric returned data.
            processed = DataProcessingUtils.flatten_nested_fields(all_data)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
            DataExporter.write_with_format_selection(processed, filename)  # type: ignore[no-untyped-call]
            print(f"! {metrics_retrieved} client anomaly event types exported to {filename}")  # Tell the user.
            logging.info(
                "Exported %s client anomaly event types for %s to %s", metrics_retrieved, client_mac, filename
            )  # Log the export.
        else:  # No metric returned data.
            print(f"! 0 client anomaly events exported to {filename} (no data available)")  # Tell the user zero.
            logging.warning("No client anomaly events available for %s", client_mac)  # Warn none.
            DataExporter.write_with_format_selection([], filename)  # type: ignore[no-untyped-call]  # Write empty file.

    @staticmethod
    def _anomaly_prepare() -> tuple | None:  # type: ignore[type-arg]
        """Prompt for a site and client, resolve names + hostname, and build the output filename.

        Returns (site_id, site_name, client_mac, client_hostname, filename), or None when the
        operator cancels at the site or client selection prompt.
        """
        site_id = PromptUtils.select_site()  # Select a site.
        if not site_id:  # No site selected.
            print("! No site selected. Exiting.")  # Tell the user.
            return None  # Abort.
        site_name = SiteAnomalyExporter._anomaly_resolve_site_name(site_id)  # Resolve site name for the filename.
        client_mac, _, _ = PromptClientUtils.select_client(site_id)  # Select a client (only MAC is used).
        if not client_mac:  # No client selected.
            print("! No client selected. Exiting.")  # Tell the user.
            return None  # Abort.
        client_hostname = SiteAnomalyExporter._anomaly_lookup_client_hostname(site_id, client_mac)  # Hostname lookup.
        sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name)  # Sanitize the site name.
        filename = f"SiteClientAnomalyEvents_{sanitized_site_name}_{client_mac.replace(':', '')}.csv"  # Output name.
        return site_id, site_name, client_mac, client_hostname, filename  # Resolved context for the export.

    @staticmethod
    def client_anomaly_events():
        """Export client-specific anomaly events for a selected client to a per-site/per-client CSV.

        Prompts for a site and client, fetches the successful_connect / roaming / throughput
        anomaly metrics, and writes SiteClientAnomalyEvents_[SiteName]_[ClientMAC].csv.
        """
        print("Export Site Client Anomaly Events:")  # Header.
        logging.info("Starting export of site client anomaly events...")  # Log start.
        prepared = SiteAnomalyExporter._anomaly_prepare()  # Prompt + resolve site/client/filename.
        if prepared is None:  # Operator cancelled at a selection prompt.
            return  # Abort.
        site_id, site_name, client_mac, client_hostname, filename = prepared  # Unpack the resolved context.
        original_levels = SiteAnomalyExporter._anomaly_suppress_mistapi_loggers()  # Quiet mistapi loggers.
        try:  # Guard the fetch/export so logger levels are always restored in finally.
            all_data, metrics_retrieved = SiteAnomalyExporter._anomaly_collect_metrics(  # Fetch all metrics.
                site_id, client_mac, site_name, client_hostname
            )
            SiteAnomalyExporter._anomaly_export(all_data, metrics_retrieved, client_mac, filename)  # Write the CSV.
        except Exception as exception:  # Export failed.
            print(f"! Error exporting client anomaly events: {exception}")  # Tell the user.
            logging.error("Failed to export client anomaly events for %s: %s", client_mac, exception)  # Log the error.
        finally:  # Always restore the mistapi logger levels.
            SiteAnomalyExporter._anomaly_restore_loggers(original_levels)  # Restore logger levels.


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


def _get_routing_utils_instance():  # Build a RoutingUtils.
    """Create RoutingUtils instance with MistHelper globals."""
    from src.network.routing_utils import RoutingDeps as _RD  # Deps dataclass wrapper.
    from src.network.routing_utils import RoutingUtils as _RU  # Import the extracted class.

    def _pick_device(site_id, dtype):  # Local wrapper for keyword-arg selector.
        return PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype)

    return _RU(  # Wire dependencies via RoutingDeps.
        _RD(
            apisession=apisession,
            select_site_fn=PromptUtils.select_site_id_from_csv,
            select_device_fn=_pick_device,
            safe_input_fn=InputUtils.safe_input,
            websocket_manager_factory=WebSocketManager,
            check_fn=IsDebugMode.check,
        )
    )


class RoutingUtils:  # Routing utils facade.
    """Routing utilities (Menus 6-8).

    Implementation extracted to src/network/routing_utils.py.
    This stub delegates to the extracted module while providing
    access to MistHelper globals (apisession, utility classes).
    """

    @staticmethod
    def execute_show_forwarding_table():  # Show the forwarding table.
        """Execute show forwarding table on a gateway/SSR device via WebSocket."""
        _get_routing_utils_instance().execute_show_forwarding_table()  # Delegate to the impl.

    @staticmethod
    def execute_show_routing_table():  # Show the routing table.
        """Execute show route command on switches via WebSocket."""
        _get_routing_utils_instance().execute_show_routing_table()  # Delegate to the impl.

    @staticmethod
    def execute_show_ssr_routes():  # Show SSR routes.
        """Execute SSR/SRX routing table via dedicated API."""
        _get_routing_utils_instance().execute_show_ssr_routes()  # Delegate to the impl.


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


# ============================================================================
# GATEWAY EXPORT UTILITIES CLASS
# ============================================================================
class GatewayTestExporter:  # Gateway synthetic test exporter.
    """
    Gateway Synthetic Test Exports

    Handles synthetic test result exports and site-level test aggregation for gateways.
    Extracted from GatewayExportUtils.
    """

    @staticmethod
    def synthetic_tests(fast=False):
        """Collect + export synthetic test stats for all gateways (optional fast/concurrent path)."""
        logging.debug("[DEBUG] GatewayTestExporter.synthetic_tests invoked with fast=%s", fast)  # Entry trace.
        logging.info("[INFO] Collecting synthetic test stats for all gateways in the org...")  # Log start.
        if fast:  # Fast mode.
            logging.info(" Fast mode enabled: Using cached data and concurrent processing (synthetic tests)")
        emitter = PROGRESS_EMITTER  # Progress emitter.
        if emitter:  # Emitter present.
            emitter.emit_progress_start("16", "synthetic_tests", 1)  # Signal progress start.
        op_start = time.time()  # Start the timer.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        gateway_devices = GatewayExportUtils._get_devices_with_sites(org_id, fast=fast)  # List gateways.
        if not gateway_devices:  # No gateways.
            logging.warning("[WARN] No gateway devices found. Exiting synthetic tests export.")  # Warn.
            return  # Abort.
        all_stats: list = []  # Accumulate stats.
        if fast:  # Concurrent path.
            GatewayTestExporter._run_synthetic_fast_path(gateway_devices, all_stats)  # Fast pool.
        else:
            GatewayTestExporter._run_synthetic_sequential_path(gateway_devices, all_stats)  # Sequential.
        GatewayTestExporter._export_synthetic_results(all_stats, gateway_devices)  # Write CSV + log.
        GatewayTestExporter._emit_synthetic_complete(emitter, op_start, gateway_devices, all_stats)  # Done.

    @staticmethod
    def _emit_synthetic_complete(emitter, op_start, gateway_devices, all_stats):
        """Emit final progress-complete signal if an emitter is configured."""
        if not emitter:  # No emitter — nothing to emit.
            return  # Skip silently.
        emitter.emit_progress_complete(  # Signal progress complete.
            ProgressContext("16", "synthetic_tests", len(gateway_devices)),
            len(all_stats),
            False,
            time.time() - op_start,
        )

    @staticmethod
    def _resolve_retry_defaults(max_retries, retry_delay):  # type: ignore[no-untyped-def]
        """Apply FAST_MODE defaults for unset retry budget / delay (returns the tuple)."""
        if max_retries is None:  # Default max retries.
            max_retries = FAST_MODE_MAX_RETRIES  # Fast-mode default.
        if retry_delay is None:  # Default retry delay.
            retry_delay = FAST_MODE_RETRY_DELAY  # Fast-mode default.
        return max_retries, retry_delay  # Tuple back to caller

    @staticmethod
    def fetch_synthetic_test_stats_with_retry(
        device_info, max_retries=None, retry_delay=None, connection_semaphore=None
    ):
        """Fetch synthetic test stats for one gateway with retry + optional connection pool gating."""
        max_retries, retry_delay = GatewayTestExporter._resolve_retry_defaults(
            max_retries, retry_delay
        )  # Defaults via helper
        site_id, device_id, _, _ = device_info  # Unpack for backoff/error logs only (names unused here).
        for attempt in range(max_retries + 1):  # Bounded retry loop.
            stats = GatewayTestExporter._try_synthetic_fetch_attempt(
                device_info, attempt, connection_semaphore
            )  # One attempt.
            if stats is not None:  # Success.
                return stats  # Return tagged stats.
            if attempt >= max_retries:  # Out of retries.
                logging.error("! Final attempt failed for device %s at site %s", device_id, site_id)  # Final failure.
                return None  # Give up.
            backoff_delay = retry_delay * (FastModeBackoffMultiplier.VALUE**attempt)  # Exponential backoff.
            logging.info(  # Log the retry.
                "! Fast retry in %.1fs (attempt %s/%s)", backoff_delay, attempt + 2, max_retries + 1
            )
            time.sleep(backoff_delay)  # Wait before retry.
        return None  # Defensive.

    @staticmethod
    def _try_synthetic_fetch_attempt(device_info, attempt, connection_semaphore):
        """Single attempt: validate inputs, call API, tag stats, log success. Return stats or None."""
        site_id, device_id, _, _ = device_info  # Unpack for the call + logging (names unused directly here).
        try:
            ValidationUtils.validate_site_id(site_id, "synthetic_tests")  # Validate the site id.
            ValidationUtils.validate_device_id(device_id, "synthetic_tests")  # Validate the device id.
            stats = GatewayTestExporter._call_synthetic_endpoint(site_id, device_id, connection_semaphore)  # Call API.
            GatewayTestExporter._tag_synthetic_stats(stats, device_info, attempt)  # Tag + log success.
            return stats  # Return tagged stats.
        except Exception as exception:  # Fetch failed this attempt.
            logging.warning(  # Warn and let caller handle backoff/retry.
                "! Attempt %s failed for device %s at site %s: %s",
                attempt + 1,
                device_id,
                site_id,
                exception,
            )
            return None  # Signal failure to caller.

    @staticmethod
    def _tag_synthetic_stats(stats, device_info, attempt):
        """Mutate ``stats`` with site/device tags and log first-try vs retry success."""
        site_id, device_id, device_name, site_name = device_info  # Unpack the fields.
        stats["site_id"] = site_id  # Tag the site.
        stats["site_name"] = site_name  # Tag the site name.
        stats["device_id"] = device_id  # Tag the device.
        stats["device_name"] = device_name  # Tag the device name.
        if attempt > 0:  # After a retry.
            logging.info("! Retry %s successful for device %s at site %s", attempt, device_name, site_name)
        else:
            logging.info("! Collected synthetic test stats for device %s at site %s", device_name, site_name)

    @staticmethod
    def _call_synthetic_endpoint(site_id, device_id, connection_semaphore):
        """Call ``getSiteDeviceSyntheticTest`` with optional semaphore-gated concurrency."""
        if connection_semaphore:  # Pool present.
            with connection_semaphore:  # Acquire a slot.
                return mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(apisession, site_id, device_id).data
        return mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest(
            apisession, site_id, device_id
        ).data  # Unsemaphored call.

    @staticmethod
    def _run_synthetic_fast_path(gateway_devices, all_stats):
        """Concurrent pool execution with retry on failures + summary instrumentation."""
        start_time = time.time()  # Start the timer.

        def fetch_device_stats(device_info, connection_semaphore):  # Pool worker.
            """Worker function that fetches synthetic test stats for a single device."""
            return GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                device_info, connection_semaphore=connection_semaphore
            )

        successful_results, failed_devices = ConnectionPoolExecutor.execute(  # Pool run.
            work_items=gateway_devices,
            worker_function=fetch_device_stats,
            batch_description="devices",
            retry_function=GatewayTestExporter._retry_failed_synthetic_devices,
        )
        duration = time.time() - start_time  # Compute the duration.
        all_stats.extend(successful_results)  # Collect the results.
        logging.info(  # Log the totals.
            " FAST MODE SUMMARY (synthetic tests): ok=%s fail=%s total=%s elapsed=%.2fs",
            len(successful_results),
            len(failed_devices),
            len(gateway_devices),
            duration,
        )

    @staticmethod
    def _retry_failed_synthetic_devices(failed_devices, connection_semaphore):
        """Retry failed devices through a small dedicated pool. Return (results, still_failed)."""
        retry_threads = min(  # Size the retry pool.
            FAST_MODE_RETRY_THREADS,
            len(failed_devices),
            max(1, FAST_MODE_MAX_CONCURRENT_CONNECTIONS - 2),
        )
        if retry_threads <= 0:  # No threads available.
            logging.warning(" FAST MODE: No available threads for retry; skipping retries")
            return [], failed_devices  # Return original failures.
        retry_results: list = []  # Collect retry results.
        still_failed: list = []  # Track still-failed devices.
        with ThreadPoolExecutor(max_workers=retry_threads) as executor:  # Run the retry pool.
            retry_futures = GatewayTestExporter._submit_synthetic_retries(
                executor, failed_devices, connection_semaphore
            )  # Build future map.
            for future in tqdm(  # type: ignore[no-untyped-call]
                as_completed(retry_futures),
                total=len(retry_futures),
                desc="Retrying Failed",
                unit="device",
            ):
                GatewayTestExporter._record_retry_outcome(future, retry_futures, retry_results, still_failed)
        return retry_results, still_failed  # Return results and failures.

    @staticmethod
    def _submit_synthetic_retries(executor, failed_devices, connection_semaphore):
        """Submit retry calls for every failed device and return the future->device map."""
        return {  # Map futures to devices.
            executor.submit(
                GatewayTestExporter.fetch_synthetic_test_stats_with_retry,
                device_info,
                max_retries=FAST_MODE_RETRY_MAX_RETRIES,
                connection_semaphore=connection_semaphore,
            ): device_info
            for device_info in failed_devices
        }

    @staticmethod
    def _record_retry_outcome(future, retry_futures, retry_results, still_failed):
        """Inspect one future's result, append to the matching bucket, log the outcome."""
        device_info = retry_futures[future]  # Resolve the device info.
        try:
            result = future.result()  # Read the result.
            if result:  # Have a result.
                retry_results.append(result)  # Collect it.
                logging.info(" FAST RETRY OK: %s", device_info[2])  # Log retry success.
            else:
                still_failed.append(device_info)  # Still failed.
                logging.error(" FAST RETRY FAIL: %s", device_info[2])  # Log retry failure.
        except Exception as exception:  # Retry raised.
            still_failed.append(device_info)  # Still failed.
            logging.error(" FAST RETRY EXC: %s -> %s", device_info[2], exception)  # Log exception.

    @staticmethod
    def _run_synthetic_sequential_path(gateway_devices, all_stats):
        """Sequential processing with adaptive rate limiting (original behavior)."""
        smoothed = None  # No smoothed delay yet.
        for device_info in tqdm(  # type: ignore[no-untyped-call]
            gateway_devices, desc="Gateway Devices", unit="device"
        ):
            result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                device_info, max_retries=FastModeSequentialMaxRetries.VALUE
            )
            if result:  # Have a result.
                all_stats.append(result)  # Collect it.
            smoothed, delay = RateLimitingUtils.get_rate_limited_delay(  # type: ignore[no-untyped-call]
                smoothed, apisession, _api_usage_cache
            )
            logging.info("[INFO] Sleeping for %.2fs.", delay)  # Log the sleep.
            time.sleep(delay)  # Pace the API.

    @staticmethod
    def _export_synthetic_results(all_stats, gateway_devices):
        """Write the aggregated stats to CSV + log totals (or warn when empty)."""
        if not all_stats:  # No results.
            logging.warning(" No synthetic test results found. CSV not created.")  # Warn.
            print("! No synthetic test results found. CSV not created.")  # Tell the user.
            return  # Nothing to write.
        filename = "AllGatewaySyntheticTests.csv"  # Build the CSV name.
        flattened = DataProcessingUtils.flatten_nested_fields(all_stats)  # Flatten nested fields.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # type: ignore[no-untyped-call]
        DataExporter.write_with_format_selection(sanitized, filename)  # type: ignore[no-untyped-call]
        print(f"! {len(all_stats)} gateway synthetic test results exported to {filename}")  # Tell user.
        logging.info("! Synthetic test results saved to %s (%s records).", filename, len(all_stats))
        logging.info(  # Log the optimization summary.
            "! API Optimization: Saved %s listSiteDevices calls by using cached inventory",
            len(gateway_devices),
        )

    @staticmethod
    def test_results_by_site(fast: bool = False) -> None:  # Export tests by site.
        """Delegator: all logic lives in src/refactors/serial_cc/test_results_by_site.py."""
        from src.refactors.serial_cc.test_results_by_site import GatewayTestResultsService  # noqa: PLC0415

        GatewayTestResultsService.execute(fast=fast)  # Delegate to extracted service; keeps CC at A(1)


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


class TroubleshootUtils:  # Marvis troubleshoot delegators.
    """Delegation wrapper for extracted Marvis troubleshooting implementation."""

    @staticmethod
    def _build_deps() -> MarvisTroubleshootDeps:  # Build the deps bundle.
        """Build dependency container for extracted troubleshooting logic."""
        return MarvisTroubleshootDeps(  # Assemble the deps.
            apisession=apisession,
            mistapi=mistapi,
            config_utils=ConfigUtils,
            prompt_client_utils=PromptClientUtils,
            prompt_utils=PromptUtils,
            data_exporter=DataExporter,
            marvis_data_utils=MarvisDataUtilsFactory.instance(),
            data_processing_utils=DataProcessingUtils,
        )

    @staticmethod
    def client_connectivity() -> None:  # Troubleshoot client connectivity.
        """Delegated client connectivity troubleshooting implementation."""
        ExtractedMarvisTroubleshootUtils.client_connectivity(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def device_performance() -> None:  # Diagnose device performance.
        """Delegated device performance troubleshooting implementation."""
        ExtractedMarvisTroubleshootUtils.device_performance(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def network_connectivity() -> None:  # Analyze network connectivity.
        """Delegated network connectivity troubleshooting implementation."""
        ExtractedMarvisTroubleshootUtils.network_connectivity(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def _print_marvis_menu() -> None:
        """Print the interactive Marvis troubleshooting menu header + numbered options."""
        print(" Starting Marvis (VNA - Virtual Network Assistant) Troubleshooting")  # Header.
        print("=" * 65)  # Divider.
        print()  # Spacer.

    @staticmethod
    def _print_marvis_options() -> None:
        """Print the 5 troubleshooting choices a user can pick."""
        print(" Marvis AI Troubleshooting Options:")  # Menu header.
        print("1. Troubleshoot client connectivity issues (guided client selection)")  # Option 1.
        print("2. Diagnose device performance problems (guided device selection)")  # Option 2.
        print("3. Analyze network connectivity issues (site-level analysis)")  # Option 3.
        print("4. View organization Marvis insights and capabilities")  # Option 4.
        print("5. Exit")  # Option 5.
        print()  # Spacer.

    @staticmethod
    def _handle_marvis_invalid_choice(choice: str) -> None:
        """Handle an out-of-range Marvis menu selection (warn + log)."""
        print(" Invalid option selected.")  # User-facing notice
        logging.warning("MARVIS DEBUG: Invalid troubleshooting option selected: %s", choice)  # Audit trail
        logging.debug("MARVIS DEBUG: Exiting launch_interactive() due to invalid choice")  # Trace exit reason

    @staticmethod
    def _handle_marvis_exit() -> None:
        """Handle the Marvis exit menu pick."""
        logging.debug("MARVIS DEBUG: User chose to exit")  # Trace the exit
        print("Exiting Marvis troubleshooting.")  # Tell the user

    @staticmethod
    def _invoke_marvis_client_connectivity() -> None:
        """Run the client-connectivity troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.client_connectivity()")  # Trace the call
        TroubleshootUtils.client_connectivity()  # type: ignore[no-untyped-call]

    @staticmethod
    def _invoke_marvis_device_performance() -> None:
        """Run the device-performance troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.device_performance()")  # Trace the call
        TroubleshootUtils.device_performance()  # type: ignore[no-untyped-call]

    @staticmethod
    def _invoke_marvis_network_connectivity() -> None:
        """Run the network-connectivity troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.network_connectivity()")  # Trace the call
        TroubleshootUtils.network_connectivity()  # type: ignore[no-untyped-call]

    @staticmethod
    def _invoke_marvis_view_insights() -> None:
        """Run the insights viewer."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.view_insights()")  # Trace the call
        TroubleshootUtils.view_insights()  # Show the insights

    @staticmethod
    def _dispatch_marvis_choice(choice: str) -> None:
        """Dispatch the user's menu pick to the matching TroubleshootUtils entrypoint."""
        handlers = {  # Map menu pick → handler (eliminates if/elif chain)
            "1": TroubleshootUtils._invoke_marvis_client_connectivity,  # Client connectivity
            "2": TroubleshootUtils._invoke_marvis_device_performance,  # Device performance
            "3": TroubleshootUtils._invoke_marvis_network_connectivity,  # Network connectivity
            "4": TroubleshootUtils._invoke_marvis_view_insights,  # View insights
            "5": TroubleshootUtils._handle_marvis_exit,  # Exit option
        }
        handler = handlers.get(choice)  # Lookup the picked handler
        if handler is None:  # Unknown pick = invalid path
            TroubleshootUtils._handle_marvis_invalid_choice(choice)  # Warn + log
            return  # Early return to keep depth flat
        handler()  # Invoke the matched handler

    @staticmethod
    def launch_interactive() -> None:  # Launch interactive Marvis.
        """Interactive Marvis (VNA) troubleshooting menu -- prompt + dispatch."""
        logging.info("Entering TroubleshootUtils.launch_interactive")  # Entry envelope for logging compliance
        logging.debug("MARVIS DEBUG: Entering launch_interactive() method")  # Trace the entry.
        TroubleshootUtils._print_marvis_menu()  # Header + divider.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        logging.debug("MARVIS DEBUG: Using org_id: %s for Marvis troubleshooting", org_id)  # %s not f-string
        logging.debug("MARVIS DEBUG: Session state - authenticated: %s", apisession is not None)  # %s not f-string
        TroubleshootUtils._print_marvis_options()  # Show numbered choices.
        choice = InputUtils.safe_input("Select an option (1-5): ", context="marvis_launch_menu").strip()
        logging.debug("MARVIS DEBUG: User selected option: %s", choice)  # %s not f-string
        TroubleshootUtils._dispatch_marvis_choice(choice)  # Route to handler.
        logging.info("Exiting TroubleshootUtils.launch_interactive with choice: %s", choice)  # Exit envelope

    @staticmethod
    def view_insights() -> None:  # View Marvis insights.
        """Delegated Marvis insights and capabilities view implementation."""
        ExtractedMarvisTroubleshootUtils.view_insights(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def _display_usage_guide() -> None:  # Show the usage guide.
        """Delegated helper for usage guide display."""
        ExtractedMarvisTroubleshootUtils._display_usage_guide()  # Delegate to the impl.


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


# ============================================================================
# ARP COMMAND MANAGER CLASS
# ============================================================================
class ARPCommandManager:  # ARP WebSocket command manager.
    """
    Manages ARP command execution via WebSocket for network devices.

    Consolidates all ARP-related functionality including command triggering,
    WebSocket message handling, and output processing/export.
    """

    @staticmethod
    def _resolve_arp_target_ids(site_id, device_id):
        """Resolve (site_id, device_id), prompting if either is missing. Returns tuple or (None, None) on abort."""
        if site_id and device_id:  # Already supplied — pass through
            return site_id, device_id
        site_id, device_id = PromptClientUtils.select_site_and_device_ids(site_id, device_id)  # type: ignore[no-untyped-call]
        return site_id, device_id  # Caller validates emptiness

    @staticmethod
    def _resolve_mist_ws_credentials():
        """Resolve (host, token) from session or environment. Returns (None, None) when either is missing."""
        mist_host = getattr(apisession, "host", None) or os.getenv("MIST_HOST")  # Session host > env
        mist_apitoken = getattr(apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")  # Session token > env
        if not mist_host or not mist_apitoken:  # Either missing — caller bails
            return None, None
        return mist_host, mist_apitoken  # Caller streams using these

    @staticmethod
    def execute(site_id=None, device_id=None):  # Run the ARP command.
        """Execute ARP command on a device and stream output via WebSocket (prompts for IDs when missing)."""
        site_id, device_id = ARPCommandManager._resolve_arp_target_ids(site_id, device_id)  # Resolve or prompt
        if not site_id or not device_id:  # Still missing — abort
            return
        mist_host, mist_apitoken = ARPCommandManager._resolve_mist_ws_credentials()  # Resolve creds
        if not mist_host or not mist_apitoken:  # Missing creds — abort
            print(" Mist host or API token not found in session or environment.")  # User-facing notice
            return
        print(" Subscribing to WebSocket stream...")  # User progress
        session_id = ARPCommandManager._trigger_command(mist_host, mist_apitoken, site_id, device_id)  # type: ignore[no-untyped-call]
        if not session_id:  # Trigger failed — nothing to listen for
            return
        ARPCommandManager._listen_for_output(  # type: ignore[no-untyped-call]
            WebSocketStreamTarget(  # Issue #470: bundle WS connection identity into one target.
                mist_host.replace("api.", "api-ws."), mist_apitoken, site_id, device_id, session_id
            )
        )

    @staticmethod
    def _trigger_command(mist_host, mist_apitoken, site_id, device_id):  # Trigger the ARP command.
        """Trigger ARP command on device via REST API."""
        url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"  # Build the URL.
        headers = {"Authorization": f"Token {mist_apitoken}"}  # Auth header.
        response = requests.post(url, headers=headers, json={}, timeout=30)  # POST the command.

        if response.status_code == 200:  # Success.
            session_id = response.json().get("session")  # Read the session id.
            print(f"! ARP command triggered. Session ID: {session_id}")  # Tell the user.
            return session_id  # Return the session.
        else:
            print(f"! Failed to trigger ARP command: {response.status_code}")  # Tell the user fail.
            print(response.text)  # Show the body.
            return None  # Return None.

    @staticmethod
    def _build_ws_subscribe(target: WebSocketStreamTarget) -> tuple[str, list[str], dict]:
        """Return (ws_url, auth headers, subscribe payload) for the bundled stream target."""
        ws_url = f"wss://{target.mist_host}/api-ws/v1/stream"  # Stream URL.
        headers = [f"Authorization: Token {target.mist_apitoken}"]  # Auth header.
        subscribe_msg = {  # Subscribe payload routed by site+device.
            "subscribe": f"/sites/{target.site_id}/devices/{target.device_id}/cmd"
        }
        return ws_url, headers, subscribe_msg  # Bundle for the caller.

    @staticmethod
    def _make_ws_callbacks(
        target: WebSocketStreamTarget,
        state: dict,
        output_lines: list[str],
        debug: bool,
        subscribe_msg: dict,
    ) -> dict:
        """Return on_message/on_close/on_error/on_open callbacks closed over a mutable state dict."""

        def on_message(ws, message):  # WebSocket message handler.
            del ws  # The websocket client passes itself; unused here but required by the callback signature.
            state["last_message_time"], state["buffer"] = ARPCommandManager._handle_message(  # type: ignore[no-untyped-call]
                message, target.session_id, state["buffer"], output_lines, debug
            )

        def on_close(ws, *args):  # WebSocket close handler.
            del ws, args  # Signature required by websocket-client; parameters unused here.
            ARPCommandManager._handle_close(output_lines, debug)  # type: ignore[no-untyped-call]

        def on_error(ws, error):  # WebSocket error handler.
            del ws  # Signature required by websocket-client; ws unused here.
            logging.error("! WebSocket error: %s", error)  # Log the error.

        def on_open(ws):  # WebSocket open handler.
            logging.info(" WebSocket opened. Subscribing...")  # Log the open.
            ws.send(json.dumps(subscribe_msg))  # Send the subscribe.

        return {"on_message": on_message, "on_close": on_close, "on_error": on_error, "on_open": on_open}

    @staticmethod
    def _poll_ws_idle(ws, state: dict, output_lines: list[str], timeout: int, idle_timeout: int) -> None:
        """Poll the running WebSocket until idle-timeout-after-output or hard timeout."""
        start_time = time.time()  # Start the timer.
        while time.time() - start_time < timeout:  # Poll until timeout.
            time.sleep(1)  # Pace the poll.
            if time.time() - state["last_message_time"] > idle_timeout and output_lines:  # Idle with output.
                logging.info(" Idle timeout reached. Closing WebSocket.")  # Log the idle close.
                ws.close()  # Close the socket.
                break  # Stop polling.
        if ws.keep_running:  # Still running -- hard timeout fired.
            logging.warning(" Timeout waiting for ARP output.")  # Warn the timeout.
            ws.close()  # Close the socket.

    @staticmethod
    def _listen_for_output(target: WebSocketStreamTarget, timeout=30, idle_timeout=3, debug=False):
        """Listen for WebSocket command output from a device (issue #470: connection identity in target)."""
        if debug:  # Debug mode.
            websocket.enableTrace(True)  # Trace the WebSocket.
        ws_url, headers, subscribe_msg = ARPCommandManager._build_ws_subscribe(target)  # Build endpoint.
        state: dict = {"last_message_time": time.time(), "buffer": ""}  # Shared callback state.
        output_lines: list[str] = []  # Collect output lines.
        callbacks = ARPCommandManager._make_ws_callbacks(target, state, output_lines, debug, subscribe_msg)
        ws = websocket.WebSocketApp(ws_url, header=headers, **callbacks)  # Build the WebSocket app.
        ws_thread = threading.Thread(target=ws.run_forever)  # Run it in a thread.
        ws_thread.start()  # Start the thread.
        ARPCommandManager._poll_ws_idle(ws, state, output_lines, timeout, idle_timeout)  # Wait for completion.

    @staticmethod
    def _drain_buffer_to_lines(buffer: str, output_lines: list[str]) -> str:
        """Split complete newline-terminated lines out of buffer, append them, and return the remainder."""
        while "\n" in buffer:  # Split on newlines.
            line, buffer = buffer.split("\n", 1)  # Pop one line.
            output_lines.append(line)  # Collect it.
        return buffer  # Return the remaining tail.

    @staticmethod
    @staticmethod
    def _parse_ws_arp_payload(message: str):
        """Parse a WebSocket frame into the inner ARP data dict (returns None when frame can't be unwrapped)."""
        msg = json.loads(message)  # Outer envelope
        data_str = msg.get("data", "{}")  # Outer data string
        data_obj = json.loads(data_str) if isinstance(data_str, str) else data_str  # Inner JSON or already-parsed
        inner_data = data_obj.get("data", {})  # Inner payload
        if isinstance(inner_data, str):  # Stringified inner — decode once more
            inner_data = json.loads(inner_data)
        return inner_data  # Caller checks session id

    @staticmethod
    def _safe_parse_ws_arp_payload(message):  # type: ignore[no-untyped-def]
        """Parse the nested ARP payload and log+swallow JSON/key errors; return inner dict or ``None`` on failure."""
        try:
            return ARPCommandManager._parse_ws_arp_payload(message)  # Nested JSON unwrap
        except json.JSONDecodeError as exception:  # Malformed JSON anywhere in the chain
            logging.error("WebSocket message JSON decode error: %s", exception)
            return None
        except KeyError as exception:  # Missing expected key in inner payload
            logging.warning("WebSocket message missing expected key: %s", exception)
            return None
        except Exception as exception:  # Defensive catch
            logging.error("Unexpected error parsing WebSocket message: %s", exception)
            return None

    @staticmethod
    def _handle_message(message, session_id, buffer, output_lines, debug=False):  # Parse one ARP message.
        """Handle incoming WebSocket message."""
        last_message_time = time.time()  # Arrival timestamp
        if debug:  # Optional raw-frame trace
            logging.debug("WebSocket raw message received: %s", message)
        inner_data = ARPCommandManager._safe_parse_ws_arp_payload(message)  # Parse + log-on-fail
        if inner_data is None:  # Parse failed -> caller continues
            return last_message_time, buffer
        if inner_data.get("session") != session_id:  # Not our session -> ignore
            return last_message_time, buffer
        raw_output = inner_data.get("raw", "")  # Append fragment
        buffer = ARPCommandManager._drain_buffer_to_lines(buffer + raw_output, output_lines)  # Flush full lines
        if debug:  # Size-trace after processing
            logging.debug("Processed WebSocket data: %s chars", len(raw_output))
        return last_message_time, buffer

    @staticmethod
    def _handle_close(output_lines, debug=False):  # Handle the close.
        """Handle WebSocket close and process output."""
        logging.info(" WebSocket closed.")  # Log the close.
        if not output_lines:  # No output captured during this session.
            print(" No ARP output received for this session.")  # Tell the user none.
            logging.warning(" No ARP output received for this session.")  # Warn none.
            return  # Nothing further to process.
        compiled_output = "\n".join(output_lines)  # Join the captured lines into one block.
        ARPCommandManager._save_output(compiled_output)  # type: ignore[no-untyped-call]
        ARPCommandManager._export_to_csv("arp_output_raw.txt")  # type: ignore[no-untyped-call]
        print("\n  ARP Output Received:\n")  # Tell the user output arrived.
        ARPCommandManager._render_arp_table(compiled_output, debug)  # type: ignore[no-untyped-call]

    @staticmethod
    def _render_arp_table(compiled_output, debug):  # Render the parsed ARP output.
        """Parse compiled ARP output and display it as a padded table."""
        logging.debug("Rendering ARP table from compiled output")  # Trace the render step.
        parsed_rows, max_cols = ARPCommandManager._parse_arp_rows(compiled_output)  # type: ignore[no-untyped-call]
        if not parsed_rows:  # No rows parsed -- nothing to tabulate.
            return  # Skip table construction entirely.
        table = PrettyTable()  # Build the table.
        table.field_names = [f"Col {col_num + 1}" for col_num in range(max_cols)]  # Number the columns.
        for row in parsed_rows:  # Add each parsed row.
            table.add_row(row)  # Add the row to the table.
        ARPCommandManager._emit_arp_table(table, len(parsed_rows), debug)  # type: ignore[no-untyped-call]

    @staticmethod
    def _parse_arp_rows(compiled_output):  # Parse compiled output into padded rows.
        """Split compiled output into tab-delimited rows padded to a uniform width."""
        logging.debug("Parsing ARP rows from compiled output")  # Trace the parse step.
        rows = compiled_output.split("\n")  # Split the block into individual rows.
        parsed_rows = [row.split("\t") for row in rows if row.strip()]  # Split each non-empty row on tabs.
        max_cols = max((len(row) for row in parsed_rows), default=0)  # Widest row determines column count.
        ARPCommandManager._pad_rows(parsed_rows, max_cols)  # type: ignore[no-untyped-call]
        return parsed_rows, max_cols  # Return the padded rows and the column width.

    @staticmethod
    def _pad_rows(parsed_rows, max_cols):  # Pad rows to a uniform width.
        """Pad each row with empty cells until it reaches max_cols columns."""
        logging.debug("Padding %d ARP rows to %d columns", len(parsed_rows), max_cols)  # Trace the pad step.
        for row in parsed_rows:  # Pad each row in place.
            while len(row) < max_cols:  # Keep padding until the row is full width.
                row.append("")  # Append an empty cell.

    @staticmethod
    def _emit_arp_table(table, row_count, debug):  # Print or log the rendered table.
        """Print the table in debug mode or report the row count otherwise."""
        if debug:  # Debug mode shows the full table.
            print(table)  # Print the table for the user.
            logging.debug("\n%s", table.get_string())  # Log the table contents.
        else:  # Non-debug mode reports only the row count.
            print(f"! ARP output received with {row_count} rows.")  # Tell the user the row count.

    @staticmethod
    def _save_output(compiled_output, filename="arp_output_raw.txt"):  # Save raw output.
        """Save compiled output to file."""
        try:
            file_path = FilePathUtils.get_csv_path(filename)  # Build the path.
            with open(file_path, "w", encoding="utf-8") as f:  # Open the file.
                f.write(compiled_output)  # Write the output.
            logging.info("! ARP output saved to %s", file_path)  # Log the save.
        except Exception as e:  # Save failed.
            logging.error("! Failed to save ARP output to file: %s", e)  # Log the error.

    @staticmethod
    def _extract_arp_columns(line: str) -> list[str]:
        """Tab-split a line and return non-empty stripped columns."""
        return [col.strip() for col in line.split("\t") if col.strip()]  # Split + strip + drop empties

    @staticmethod
    def _split_arp_text_into_datasets(raw_text: str) -> tuple[list[list[str]], list[list[str]]]:
        """Split raw ARP text into two tab-delimited datasets separated by a 'Total' marker line."""
        lines = raw_text.splitlines()  # Split into lines.
        dataset1: list[list[str]] = []  # First dataset.
        dataset2: list[list[str]] = []  # Second dataset.
        current_dataset = dataset1  # Start with the first.
        for line in lines:  # Walk lines.
            if "Total" in line:  # Total marker.
                current_dataset = dataset2  # Switch datasets.
                continue  # Marker isn't a row.
            columns = ARPCommandManager._extract_arp_columns(line)  # Delegate tab-split + strip
            if columns:  # Have columns.
                current_dataset.append(columns)  # Collect the row.
        return dataset1, dataset2  # Return both datasets.

    @staticmethod
    def _write_dataset_csv(path: str, rows: list[list[str]]) -> None:
        """Write a single dataset to a CSV file and announce the row count."""
        with open(path, "w", newline="", encoding="utf-8") as fout:  # Open the CSV.
            writer = csv.writer(fout)  # CSV writer.
            writer.writerows(rows)  # Write the rows.
        print(f"! Saved {len(rows)} rows to {path}")  # Tell the user.

    @staticmethod
    def _export_to_csv(txt_filename="arp_output_raw.txt", csv1="arp_dataset1.csv", csv2="arp_dataset2.csv"):
        """Export ARP output to CSV files."""
        try:
            txt_file_path = FilePathUtils.get_csv_path(txt_filename)  # Source path.
            csv1_path = FilePathUtils.get_csv_path(csv1)  # First CSV path.
            csv2_path = FilePathUtils.get_csv_path(csv2)  # Second CSV path.
            with open(txt_file_path, encoding="utf-8") as f:  # Open the source.
                raw_text = f.read()  # Read the text.
            dataset1, dataset2 = ARPCommandManager._split_arp_text_into_datasets(raw_text)  # Split.
            ARPCommandManager._write_dataset_csv(csv1_path, dataset1)  # Write first CSV.
            ARPCommandManager._write_dataset_csv(csv2_path, dataset2)  # Write second CSV.
        except Exception as e:  # Export failed.
            print(f"! Failed to export ARP output to CSV: {e}")  # Tell the user.


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


# ============================================================================
# DEVICE REBOOT MANAGER CLASS
# ============================================================================
class DeviceRebootManager:  # Device reboot manager.
    """
    Manages device reboot operations with comprehensive safety checks and audit logging.

    Supports reboot operations by:
    - Gateway template list (bulk operations)
    - Site list
    - Individual device selection

    All operations require explicit user confirmation and log results for auditing.
    """

    @staticmethod
    def by_gateway_template_list():  # Reboot by template list.
        """
        Reboots all devices associated with gateway templates in GatewayTemplateRebootList.CSV.
        Logs results to GatewayTemplateRebootResults.CSV.
        """
        logging.info("[Menu 91] Starting DeviceRebootManager.by_gateway_template_list")  # Log start.

        # Step 1: Validate reboot list file exists
        reboot_targets = DeviceRebootManager._load_and_validate_reboot_targets()  # Load reboot targets.
        if not reboot_targets:  # No targets.
            return  # Abort.

        # Step 2: Display confirmation and get user consent
        if not DeviceRebootManager._confirm_reboot_operation(reboot_targets):  # Confirm the reboot.
            return  # Abort.

        # Step 3: Execute reboots and collect results
        results = DeviceRebootManager._execute_reboots(reboot_targets)  # Execute the reboots.

        # Step 4: Export results to CSV
        DeviceRebootManager._export_reboot_results(results)  # Export the results.

    @staticmethod
    def _load_and_validate_reboot_targets() -> list[dict] | None:  # type: ignore[type-arg]
        """Load reboot list and return validated device targets."""
        reboot_list_path = FilePathUtils.get_csv_path("GatewayTemplateRebootList.CSV")  # Reboot list path.
        if not os.path.exists(reboot_list_path):  # File missing.
            DeviceRebootManager._handle_missing_reboot_file(reboot_list_path)  # Handle the missing file.
            return None  # Abort.
        DeviceRebootManager._ensure_fresh_csv_cache()  # Refresh the CSV cache.
        template_name_to_id = DeviceRebootManager._load_template_mappings()  # Load template mappings.
        if not template_name_to_id:  # No mappings.
            return None  # Abort.
        reboot_template_names = DeviceRebootManager._load_reboot_template_names()  # Load reboot template names.
        if not reboot_template_names:  # No names.
            return None  # Abort.
        reboot_template_ids = DeviceRebootManager._map_template_names_to_ids(reboot_template_names, template_name_to_id)
        if not reboot_template_ids:  # No ids.
            return None  # Abort.
        return DeviceRebootManager._find_reboot_target_devices(reboot_template_ids, template_name_to_id)

    @staticmethod
    def _handle_missing_reboot_file(reboot_list_path: str) -> None:  # Handle the missing file.
        """Handle missing reboot list file - offer to create template."""
        logging.error(" GatewayTemplateRebootList.CSV not found.")  # Log the missing file.
        print(" GatewayTemplateRebootList.CSV not found.")  # Tell the user.
        print(f"   Please create this file at: {reboot_list_path}")  # Show the path.
        print("   This file should contain template names to reboot, one per line.")  # Explain the format.

        user_input = (  # Prompt to create it.
            InputUtils.safe_input(
                "   Would you like to create an empty file? (y/n): ",
                context="gateway_reboot_create_template_file",
            )
            .strip()
            .lower()
        )
        if user_input in ["y", "yes"]:  # User said yes.
            try:
                template_path = FilePathUtils.create_csv_template("GatewayTemplateRebootList.CSV")
                print(f"! Empty file created at: {template_path}")  # Tell the user.
                print("   Edit the file to add template names and run again.")  # Tell the user.
            except Exception as error:  # Creation failed.
                print(f"! Failed to create file: {error}")  # Tell the user.

    @staticmethod
    def _ensure_fresh_csv_cache() -> None:  # Refresh the CSV cache.
        """Ensure required CSV files are fresh."""
        CacheUtils.check_and_generate_csv("OrgDevices.csv", OrgInventoryExporter.devices)  # Refresh devices CSV.
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # Refresh sites CSV.
        CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", GatewayExportUtils.templates)
        CacheUtils.check_and_generate_csv(  # Refresh gateway configs CSV.
            "AllSiteGatewayConfigs.csv",
            lambda: GatewayExportUtils.device_configs(fast=True),
        )

    @staticmethod
    def _load_template_mappings() -> dict[str, str] | None:  # Load template name->id.
        """Load template name to ID mapping from OrgGatewayTemplates.csv."""
        try:
            gateway_templates_path = FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")  # Templates path.
            template_name_to_id = DeviceRebootManager._read_template_name_id_csv(gateway_templates_path)  # Parse rows.
            logging.info("Loaded %s gateway templates", len(template_name_to_id))  # Log the count.
        except Exception as error:  # Load failed.
            logging.error("! Failed to load gateway templates: %s", error)  # Log the error.
            print(f"! Failed to load gateway templates: {error}")  # Tell the user.
            return None  # Abort.

        if not template_name_to_id:  # No templates.
            logging.warning(" No gateway templates found in OrgGatewayTemplates.csv")  # Warn none.
            print(" No gateway templates found in OrgGatewayTemplates.csv")  # Tell the user.
            return None  # Abort.

        return template_name_to_id  # Return the map.

    @staticmethod
    def _read_template_name_id_csv(csv_path: str) -> dict[str, str]:  # Read name/id rows into a map
        """Read a gateway-templates CSV into a {name: id} dict, skipping rows missing either field."""
        template_name_to_id: dict[str, str] = {}  # Name-to-id map.
        with open(csv_path, encoding="utf-8") as file:  # Open the CSV.
            reader = csv.DictReader(file)  # Parse rows.
            for row in reader:  # Walk rows.
                name = row.get("name", "").strip()  # Read the name.
                tid = row.get("id", "").strip()  # Read the id.
                if name and tid:  # Have both.
                    template_name_to_id[name] = tid  # Map name to id.
        return template_name_to_id  # The parsed name->id map

    @staticmethod
    def _load_reboot_template_names() -> set[str] | None:  # Load reboot template names.
        """Load template names from reboot list file."""
        try:
            reboot_list_path = FilePathUtils.get_csv_path("GatewayTemplateRebootList.CSV")  # Reboot list path.
            reboot_template_names = DeviceRebootManager._read_reboot_names_csv(reboot_list_path)  # Parse rows.
            logging.info("Loaded %s template names from reboot list", len(reboot_template_names))  # Log the count.
        except Exception as error:  # Load failed.
            logging.error("! Failed to load reboot template list: %s", error)  # Log the error.
            print(f"! Failed to load reboot template list: {error}")  # Tell the user.
            return None  # Abort.
        return reboot_template_names if reboot_template_names else None  # Return names or None.

    @staticmethod
    def _read_reboot_names_csv(csv_path: str) -> set[str]:  # Read first-column names into a set
        """Read a reboot-list CSV's first column into a set of names, skipping blank rows/values."""
        reboot_template_names: set[str] = set()  # Name set.
        with open(csv_path, encoding="utf-8") as file:  # Open the CSV.
            reader = csv.reader(file)  # Parse rows.
            for row in reader:  # Walk rows.
                if row and row[0].strip():  # Non-empty name.
                    reboot_template_names.add(row[0].strip())  # Collect it.
        return reboot_template_names  # The parsed name set

    @staticmethod
    def _map_template_names_to_ids(names: set[str], mapping: dict[str, str]) -> set[str] | None:  # Map names to ids.
        """Map template names to IDs, logging matches and mismatches."""
        reboot_template_ids = set()  # Id set.
        for name in names:  # Walk names.
            if name in mapping:  # Name found.
                reboot_template_ids.add(mapping[name])  # Collect the id.
                logging.info("! Found template '%s' with ID '%s'", name, mapping[name])  # Log the match.
            else:
                logging.warning("! Template '%s' not found in OrgGatewayTemplates.csv", name)  # Warn not found.
                print(f"! Template '{name}' not found in available templates")  # Tell the user.

        if not reboot_template_ids:  # No matches.
            logging.error(" No matching template IDs found for reboot")  # Log none.
            print(" No matching template IDs found for reboot")  # Tell the user.
            print("Available templates:")  # List available.
            for name, tid in mapping.items():  # Walk templates.
                print(f"  - {name} ({tid})")  # Print each.
            return None  # Abort.

        return reboot_template_ids  # Return the ids.

    @staticmethod
    def _build_gateway_reboot_target(row: dict, resolved: tuple) -> dict:  # type: ignore[type-arg]
        """Build one reboot-target dict from a CSV row + the (template_id, template_name, site_name) tuple."""
        template_id, template_name, site_name = resolved  # Unpack the resolved triple.
        return {
            "device_id": row.get("id", "").strip(),
            "device_name": row.get("name", "").strip(),
            "site_id": row.get("site_id", "").strip(),
            "site_name": site_name,
            "template_id": template_id,
            "template_name": template_name,
        }

    @staticmethod
    def _scan_csv_for_gateway_targets(  # type: ignore[type-arg]
        site_to_template: dict[str, tuple],
    ) -> list[dict] | None:
        """Scan AllSiteGatewayConfigs.csv and collect gateway-row targets whose site uses a tracked template."""
        reboot_targets: list[dict] = []  # Collect reboot targets.
        try:
            gateway_configs_path = FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv")  # Configs path.
            with open(gateway_configs_path, encoding="utf-8") as file:  # Open the CSV.
                for row in csv.DictReader(file):  # Walk rows.
                    device_site_id = row.get("site_id", "").strip()  # Read the site id.
                    if device_site_id not in site_to_template or row.get("type", "").strip() != "gateway":
                        continue  # Skip non-matching rows.
                    target = DeviceRebootManager._build_gateway_reboot_target(row, site_to_template[device_site_id])
                    reboot_targets.append(target)  # Collect the target.
                    logging.info("Found gateway '%s' at site '%s'", target["device_name"], target["site_name"])
        except Exception as error:  # Load failed.
            logging.error("! Failed to load gateway configs: %s", error)  # Log the error.
            print(f"! Failed to load gateway configs: {error}")  # Tell the user.
            return None  # Abort.
        return reboot_targets  # Return collected targets (possibly empty).

    @staticmethod
    def _find_reboot_target_devices(template_ids: set[str], mapping: dict[str, str]) -> list[dict] | None:  # type: ignore[type-arg]
        """Find gateway devices in sites using the target templates."""
        template_id_to_name = {tid: name for name, tid in mapping.items()}  # Invert the map.
        site_to_template = DeviceRebootManager._find_sites_using_templates(template_ids, template_id_to_name)
        if not site_to_template:  # No sites.
            logging.warning(" No sites found using the specified gateway templates")  # Warn none.
            print(" No sites found using the specified gateway templates")  # Tell the user.
            return None  # Abort.
        reboot_targets = DeviceRebootManager._scan_csv_for_gateway_targets(site_to_template)  # Collect targets.
        if reboot_targets is None:  # Hard error in CSV load.
            return None  # Propagate abort.
        if not reboot_targets:
            logging.warning(" No gateway devices found in sites using the specified templates")
            print(" No gateway devices found in sites using the specified templates")
            return None
        logging.info("Found %s gateway devices to reboot", len(reboot_targets))
        return reboot_targets

    @staticmethod
    def _find_sites_using_templates(template_ids: set[str], id_to_name: dict[str, str]) -> dict[str, tuple]:  # type: ignore[type-arg]
        """Find sites that use the target gateway templates."""
        site_to_template = {}  # Map of site_id -> (template_id, template_name, site_name) for matching sites
        try:
            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # Resolve the cached site list CSV path
            with open(site_list_path, encoding="utf-8") as file:  # Open the site list for reading
                reader = csv.DictReader(file)  # Parse each site row into a dictionary
                for row in reader:  # Examine every site
                    gateway_template_id = row.get(
                        "gatewaytemplate_id", ""
                    ).strip()  # The gateway template assigned to this site
                    if gateway_template_id in template_ids:  # This site uses one of the target templates
                        site_id = row.get("id", "").strip()  # The site's unique ID
                        site_name = row.get("name", "").strip()  # The site's display name
                        template_name = id_to_name.get(gateway_template_id, "Unknown")  # Resolve the template's name
                        site_to_template[site_id] = (gateway_template_id, template_name, site_name)  # Record the match
                        logging.info("Found site '%s' using template '%s'", site_name, template_name)  # Log the match
        except Exception as error:  # Reading or parsing the site list failed
            logging.error("! Failed to load site list: %s", error)  # Log the failure detail
            print(f"! Failed to load site list: {error}")  # Inform the user
        return site_to_template  # Return the site-to-template mapping

    @staticmethod
    def _group_targets_by_template(targets: list[dict]) -> dict[str, list[dict[str, Any]]]:  # type: ignore[type-arg]
        """Group reboot targets by their template_name into one list per template."""
        devices_by_template: dict[str, list[dict[str, Any]]] = {}
        for target in targets:  # Walk targets.
            template_name = target["template_name"]  # Read template name.
            devices_by_template.setdefault(template_name, []).append(target)  # Group in place.
        return devices_by_template

    @staticmethod
    def _print_reboot_target_summary(targets: list[dict], devices_by_template: dict[str, list[dict[str, Any]]]) -> None:  # type: ignore[type-arg]
        """Print the per-template device list followed by the totals summary."""
        for template_name, devices in devices_by_template.items():  # Per template.
            print(f"\n  Template: {template_name}")
            print(f"   {len(devices)} devices affected:")
            for device in devices:  # Per device.
                print(f"      !? {device['device_name']} (ID: {device['device_id']}) at '{device['site_name']}'")
        DeviceRebootManager._display_reboot_warnings()  # Inject the critical warnings.
        print("\n  Summary:")
        print(f"   !? Total devices to reboot: {len(targets)}")
        print(f"   !? Templates involved: {len(devices_by_template)}")
        print(f"   !? Sites affected: {len(set(t['site_name'] for t in targets))}")

    @staticmethod
    def _prompt_reboot_confirmation(target_count: int) -> bool:
        """Read the REBOOT confirmation phrase and log the accept/cancel decision."""
        print("\n  Type 'REBOOT' to confirm, or anything else to cancel:")
        print("   By typing 'REBOOT', you accept all risks and liability.")
        try:
            user_input = InputUtils.safe_input(">>> ", context="gateway_reboot_confirmation").strip()
            if user_input != "REBOOT":
                print(" Reboot operation cancelled.")
                logging.info("Gateway reboot cancelled by user")
                return False
            print(" User confirmed reboot operation. Proceeding...")
            logging.info("LIABILITY WAIVER ACCEPTED: User confirmed reboot for %s devices", target_count)
            return True
        except (KeyboardInterrupt, EOFError):
            print("\n Reboot operation cancelled.")
            logging.info("Gateway reboot cancelled by user interrupt")
            return False

    @staticmethod
    def _confirm_reboot_operation(targets: list[dict]) -> bool:  # type: ignore[type-arg]
        """Display targets and get user confirmation for reboot."""
        print("\n" + "=" * 100)
        print(" DEVICE REBOOT CONFIRMATION REQUIRED ")
        print("=" * 100)
        print(f"\n  The following {len(targets)} gateway devices will be REBOOTED:")
        print("-" * 100)
        devices_by_template = DeviceRebootManager._group_targets_by_template(targets)  # Group.
        DeviceRebootManager._print_reboot_target_summary(targets, devices_by_template)  # Display.
        return DeviceRebootManager._prompt_reboot_confirmation(len(targets))  # Read decision.

    @staticmethod
    def _display_reboot_warnings() -> None:
        """Display critical reboot warnings."""
        warnings = [
            " CRITICAL WARNING - READ CAREFULLY:",
            "!? This action will REBOOT network gateway devices",
            "!? Network connectivity will be TEMPORARILY LOST during reboot",
            "!? Users may experience service interruptions",
            "!? Remote sites may become inaccessible during reboot",
            "!? The script owner bears NO LIABILITY for any consequences",
        ]
        print("\n" + "??" * 50)
        for warning in warnings:
            print(warning)
        print("??" * 50)

    @staticmethod
    def _reboot_one_device(device: dict) -> str:  # type: ignore[type-arg]
        """Send one restartSiteDevice call and return the status string (or 'ERROR: ...')."""
        try:
            logging.info("Rebooting device '%s'", device["device_name"])  # Log before the call.
            print(f"! Rebooting {device['device_name']} at {device['site_name']}...")
            response = mistapi.api.v1.sites.devices.restartSiteDevice(  # Send the reboot.
                apisession,
                device["site_id"],
                device["device_id"],
                body={"timestamp": datetime.now(UTC).isoformat()},
            )
            status = DeviceRebootManager._parse_reboot_response(response)  # Parse the result.
            print("   Reboot command sent successfully")
            logging.info("! Reboot sent for '%s': %s", device["device_name"], status)  # Log after the call.
            return status  # Return the parsed status.
        except Exception as error:  # API failure.
            print(f"   Failed to send reboot: {error}")
            logging.error("! Failed to reboot '%s': %s", device["device_name"], error)
            return f"ERROR: {error}"  # Capture the error for the result row.

    @staticmethod
    def _build_reboot_result_row(device: dict, status: str) -> dict:  # type: ignore[type-arg]
        """Build a single reboot-result row (template/device/site identity plus status string)."""
        return {
            "Template ID": device["template_id"],
            "Template Name": device["template_name"],
            "Device ID": device["device_id"],
            "Device Name": device["device_name"],
            "Site ID": device["site_id"],
            "Site Name": device["site_name"],
            "Status": status,
        }

    @staticmethod
    def _execute_reboots(targets: list[dict]) -> list[dict]:  # type: ignore[type-arg]
        """Execute reboot commands for all target devices."""
        print("\n  Starting device reboot operations...")
        print("=" * 50)
        results: list[dict] = []
        for device in targets:  # Walk targets.
            status = DeviceRebootManager._reboot_one_device(device)  # Reboot + capture status.
            results.append(DeviceRebootManager._build_reboot_result_row(device, status))  # Record row.
        return results

    @staticmethod
    def _parse_reboot_response(response) -> str:
        """Parse reboot API response into status string."""
        if hasattr(response, "data") and response.data:
            if isinstance(response.data, dict):
                return response.data.get("status", f"SUCCESS - {response.data}")  # type: ignore[no-any-return]
            return f"SUCCESS - {response.data}"
        elif hasattr(response, "status_code"):
            return f"SUCCESS - HTTP {response.status_code}"
        return f"SUCCESS - {str(response)}"

    @staticmethod
    def _export_reboot_results(results: list[dict]) -> None:  # type: ignore[type-arg]
        """Export reboot results to CSV."""
        try:
            results_csv_path = FilePathUtils.get_csv_path("GatewayTemplateRebootResults.CSV")
            with open(results_csv_path, "w", newline="", encoding="utf-8") as file:
                fieldnames = [
                    "Template ID",
                    "Template Name",
                    "Device ID",
                    "Device Name",
                    "Site ID",
                    "Site Name",
                    "Status",
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            print("\n  Operation completed!")
            print(f"   Reboot commands sent to {len(results)} devices")
            print("   Results logged to GatewayTemplateRebootResults.CSV")
            logging.info("! Reboot results exported (%s entries)", len(results))
        except Exception as error:
            logging.error("! Failed to write results to CSV: %s", error)
            print(f"! Failed to write results to CSV: {error}")


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


class SiteAutoUpgradeConfigurator:
    """Thin wrapper that delegates to src.firmware.site_auto_upgrade."""

    @staticmethod
    def execute():
        """Static entry point - delegates to extracted module."""
        from src.firmware.site_auto_upgrade import SiteAutoUpgradeConfigurator as _Impl

        global msp_privileges

        dry_run = getattr(globals().get("args", None), "dry_run", False)
        _Impl.execute(
            apisession=apisession,
            msp_privileges=msp_privileges if msp_privileges else [],
            safe_input_fn=InputUtils.safe_input,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            check_stop_fn=ConfigUtils.check_stop_signal,
            dry_run=dry_run,
            select_msps_fn=OrgLevelAPFirmwareUpgrader._select_msps,
            select_orgs_fn=OrgLevelAPFirmwareUpgrader._select_orgs_from_msp,
        )


class OrgLevelAPFirmwareUpgrader:
    """Thin wrapper that delegates to src.firmware.org_ap_upgrader."""

    def __init__(self, org_id, dry_run=False):
        """Initialize the org-level AP firmware upgrader."""
        self.org_id = org_id
        self.dry_run = dry_run

    @staticmethod
    def run():
        """Static entry point - delegates to extracted module."""
        from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl

        global msp_privileges, apisession, selected_msp

        dry_run = getattr(globals().get("args", None), "dry_run", False)
        upgrader = _Impl(
            org_id=ConfigUtils.get_cached_or_prompted_org_id() or "",
            apisession=apisession,
            dry_run=dry_run,
            safe_input_fn=InputUtils.safe_input,
            check_stop_fn=ConfigUtils.check_stop_signal,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            write_results_fn=DataExporter.write_with_format_selection,
            is_debug_fn=IsDebugMode.check,
            msp_privileges=msp_privileges if msp_privileges else [],
            selected_msp=selected_msp if selected_msp else None,
        )
        upgrader.run()

    def execute(self):
        """Execute - delegates to extracted module."""
        from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl

        global apisession

        upgrader = _Impl(
            org_id=self.org_id,
            apisession=apisession,
            dry_run=self.dry_run,
            safe_input_fn=InputUtils.safe_input,
            check_stop_fn=ConfigUtils.check_stop_signal,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            write_results_fn=DataExporter.write_with_format_selection,
            is_debug_fn=IsDebugMode.check,
        )
        upgrader.execute()

    @staticmethod
    def _select_msps():
        """Delegate MSP selection to extracted module."""
        from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl

        global msp_privileges, apisession, selected_msp

        upgrader = _Impl(
            org_id="",
            apisession=apisession,
            safe_input_fn=InputUtils.safe_input,
            msp_privileges=msp_privileges if msp_privileges else [],
            selected_msp=selected_msp if selected_msp else None,
        )
        return upgrader._select_msps()

    @staticmethod
    def _select_orgs_from_msp(msp):
        """Delegate org selection to extracted module."""
        from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl

        global apisession

        upgrader = _Impl(
            org_id="",
            apisession=apisession,
            safe_input_fn=InputUtils.safe_input,
        )
        return upgrader._select_orgs_from_msp(msp)


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
        RoutingUtils.execute_show_forwarding_table,
        "Show forwarding table on gateway device via WebSocket (Layer 3 routing table)",
    ),
    "104": (
        RoutingUtils.execute_show_routing_table,
        "Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static)",
    ),
    "105": (
        RoutingUtils.execute_show_ssr_routes,
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
        OrgLevelAPFirmwareUpgrader.run,
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
        SiteAutoUpgradeConfigurator.execute,
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
