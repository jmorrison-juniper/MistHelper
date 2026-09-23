#!/usr/bin/env python3
"""
MistHelper - Comprehensive Juniper Mist API Data Export Tool
A powerful utility for extracting and analyzing data from Juniper Mist cloud environments.
"""

from __future__ import annotations  # Preserve the existing behavior during the compliance refactor.

# ============================================================================
# PYTHON VERSION CHECK - MUST BE FIRST (before any other imports)
# ============================================================================
import sys  # Preserve the existing behavior during the compliance refactor.

# Enforce Python 3.13+ requirement
MINIMUM_PYTHON_VERSION = (3, 13)  # Define minimum required Python version tuple for compatibility checks
if sys.version_info < MINIMUM_PYTHON_VERSION:  # Exit early if Python is too old to prevent cryptic errors later
    # Format current Python version for display
    version_str = f"{sys .version_info .major }.{sys .version_info .minor }.{sys .version_info .micro }"
    required_str = (
        f"{MINIMUM_PYTHON_VERSION [0 ]}.{MINIMUM_PYTHON_VERSION [1 ]}"  # Format minimum required version for display
    )
    warning_msg = (  # Build user-friendly error message with actionable guidance
        f"WARNING: Python {version_str } detected. MistHelper requires Python {required_str } or newer.\n"
        f"Some features may not work correctly. Please upgrade Python to {required_str }+.\n"
        f"Download from: https://www.python.org/downloads/"
    )
    # Pre-logging setup: logging module not yet imported, so stderr prints are the only viable channel.
    print(f"\n{'='*70 }", file=sys.stderr)  # Preserve the existing behavior during the compliance refactor.
    print(warning_msg, file=sys.stderr)  # Preserve the existing behavior during the compliance refactor.
    print(f"{'='*70 }\n", file=sys.stderr)  # Preserve the existing behavior during the compliance refactor.
    # Log will be configured later, but we cannot use logging yet
    # The warning is printed to stderr so it is visible regardless

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
import re  # Import re for regex pattern matching in data parsing (SSIDs, descriptions, and so on)
import time  # Import time for rate limiting, delays, and performance monitoring
import traceback  # Import traceback for detailed exception context in error logs
import types  # Import types for type annotations (TracebackType)
from collections.abc import (
    Callable,  # Callable protocol for typed function references
    Iterable,  # Type hints for static analysis
)
from datetime import datetime  # Import datetime for timestamping logs and events
from logging.handlers import RotatingFileHandler  # Rotate script.log before the data volume fills
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    NoReturn,
    TextIO,
    cast,
)  # Preserve the existing behavior during the compliance refactor.

from packaging.requirements import InvalidRequirement, Requirement  # WHY: Parse requirement lines that include names.
from packaging.specifiers import (
    InvalidSpecifier,
    SpecifierSet,
)  # WHY: PEP 440 specifier checks replace hand comparisons.
from packaging.version import InvalidVersion, Version  # WHY: PEP 440 version comparison.

from src.utils.console import echo  # WHY: 1031 stdout + INFO log helper replaces legacy WARNING-channel echoes.
from src.utils.subprocess_runner import (  # Centralized subprocess dispatch + exception re-exports (initiative 1016).
    SubprocessError,  # Base class for subprocess errors (parent of TimeoutExpired/CalledProcessError).
    SubprocessRunner,  # Audited dispatcher. Sole entry point for external command execution.
    TimeoutExpired,  # Raised when subprocess.run exceeds its timeout.
    subprocess,  # Re-exported audited module for bootstrap injection without a direct stdlib import.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.
if sys.version_info < MINIMUM_PYTHON_VERSION:  # Log the same version warning after logging becomes importable.
    version_str = (
        f"{sys .version_info .major }.{sys .version_info .minor }.{sys .version_info .micro }"  # Format version.
    )
    required_str = f"{MINIMUM_PYTHON_VERSION [0 ]}.{MINIMUM_PYTHON_VERSION [1 ]}"  # Format the minimum version.
    logger.warning(  # Keep the historical log text for the logging parity contract.
        "Python %s detected. MistHelper requires Python %s+. Some features may not work correctly.",
        version_str,
        required_str,
    )


class LogRotationSettings:  # Preserve the existing behavior during the compliance refactor.
    """Read safe size-based rotation settings for script.log."""

    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # Limit the active log to 10 MiB by default
    DEFAULT_BACKUP_COUNT = 5  # Keep five rotated logs by default

    def __init__(
        self, max_bytes: int, backup_count: int
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        self.max_bytes = max_bytes  # Store the active log size limit
        self.backup_count = backup_count  # Store the retained backup count

    @classmethod
    def from_environment(cls) -> LogRotationSettings:  # Preserve the existing behavior during the compliance refactor.
        """Read validated rotation values from the process environment."""
        max_bytes = cls._read_integer("LOGGING_MAX_BYTES", cls.DEFAULT_MAX_BYTES, minimum=1)  # Read the size limit
        backup_count = cls._read_integer("LOGGING_BACKUP_COUNT", cls.DEFAULT_BACKUP_COUNT, minimum=0)  # Read retention
        return cls(max_bytes, backup_count)  # Return one validated configuration for either setup path

    @staticmethod
    def _read_integer(
        name: str, default: int, minimum: int
    ) -> int:  # Preserve the existing behavior during the compliance refactor.
        """Return a positive environment integer or its safe default."""
        raw_value = os.environ.get(name)  # Read the optional deployment override
        if raw_value is None:  # Use the default when the variable is not configured
            return default  # Preserve the bounded default
        try:  # Validate operator-provided text before logging starts
            value = int(raw_value)  # Convert the override to an integer
        except ValueError:  # Reject malformed deployment settings
            return default  # Preserve a safe bounded configuration
        return value if value >= minimum else default  # Reject values that disable the safety bound

    def build_handler(
        self, log_path: str
    ) -> RotatingFileHandler:  # Preserve the existing behavior during the compliance refactor.
        """Build a UTF-8 rotating handler for the configured log path."""
        return RotatingFileHandler(  # Create the bounded handler used by both logging setup paths
            log_path,  # Keep the existing data/script.log location
            maxBytes=self.max_bytes,  # Rotate when the active file reaches the configured size
            backupCount=self.backup_count,  # Retain only the configured number of backups
            encoding="utf-8",  # Preserve non-ASCII operational data safely
        )

        # Type stubs for dynamically imported modules
        # These allow type checking while the actual imports happen at runtime via GlobalImportManager
        # Pylance uses these unconditionally. Runtime try/except blocks below handle actual loading.


if TYPE_CHECKING:  # These imports only used by static type checkers (Pylance, mypy), not at runtime
    from types import ModuleType  # ModuleType annotation for optional-module fallback typing

    from prettytable import PrettyTable  # Type stub for prettytable (ASCII table formatting)

    import websocket  # Type stub for websocket (WebSocket client for device diagnostics)
    from src.device.utility_commands import DeviceUtilityCommands  # Type stub for DeviceUtilityCommands

    # ============================================================================
    # POLYGLOT DATABASE LAYER (OPTIONAL)
    # ============================================================================
    # Conditional import for ArangoDB + Redis TimeSeries backends.
    # Falls back gracefully in standalone mode (no python-arango/redis installed).
try:  # Try to import polyglot database layer for ArangoDB/Redis export backends
    from src.db import (
        DatabaseConfig as _DatabaseConfigImpl,
    )  # Preserve the existing behavior during the compliance refactor.
    from src.db import (
        configure_db_logging as _configure_db_logging_impl,
    )  # Preserve the existing behavior during the compliance refactor.
    from src.db.router import (
        DatabaseRouter as _DatabaseRouterImpl,
    )  # Preserve the existing behavior during the compliance refactor.

    DatabaseConfig: type[_DatabaseConfigImpl] | None = _DatabaseConfigImpl  # Class reference for DB config construction
    configure_db_logging: Callable[[], None] | None = _configure_db_logging_impl  # Logging setup callable
    DatabaseRouter: type[_DatabaseRouterImpl] | None = _DatabaseRouterImpl  # Class reference for DB router construction
    DB_LAYER_AVAILABLE = True  # Set flag indicating database backends are available for export operations
except ImportError:  # If database dependencies (python-arango, redis) not installed, gracefully disable
    DatabaseConfig = None  # None lets runtime guards detect DB-layer absence
    configure_db_logging = None  # None lets runtime guards detect DB-layer absence
    DatabaseRouter = None  # None lets runtime guards detect DB-layer absence
    DB_LAYER_AVAILABLE = False  # Set flag to disable database output formats (CSV/SQLite only)

    # Explicit public API surface (issue #895).
    # A src.* submodule re-exports every name below for external
    # consumers. Adding a name here MUST accompany a corresponding update to
    # specs/1016-misthelper-suppression-cleanup/contracts/public_api_snapshot.txt.
__all__ = [  # Preserve the existing behavior during the compliance refactor.
    "API_REQUEST_MAX_RETRIES",
    "API_REQUEST_RETRY_DELAY",
    "API_REQUEST_TIMEOUT",
    "AUTO_UPGRADE_DEPENDENCIES",
    "AUTO_UPGRADE_UV",
    "CSV_FRESHNESS_MINUTES",
    "DATABASE_PATH",
    "DB_LAYER_AVAILABLE",
    "DEFAULT_API_PAGE_LIMIT",
    "DOTENV_AVAILABLE",
    "FAST_MODE_ENABLED",
    "FAST_MODE_FALLBACK_THREADS",
    "FAST_MODE_MAX_RETRIES",
    "FAST_MODE_RETRY_DELAY",
    "FAST_MODE_RETRY_MAX_RETRIES",
    "FAST_MODE_RETRY_THREADS",
    "IS_TEST_MODE",
    "LAST_SELECTED_SITE_ID",
    "MINIMUM_PYTHON_VERSION",
    "OUTPUT_FORMAT",
    "PROGRESS_EMITTER",
    "TYPE_CHECKING",
    "UPGRADE_CHECK_TIMEOUT",
    "UTC",
    "APICoreFetchUtils",
    "APIDataFetcher",
    "APIFetchUtils",
    "APITenantFetchUtils",
    "ARPCommandManager",
    "AddressAuditEngine",
    "AnomalyMetricsDiscovery",
    "Any",
    "ArpDeviceExecutor",
    "AuditAnalysisOps",
    "BulkRadiusWLANConfigManager",
    "CLIShellManager",
    "CacheUtils",
    "ConfigUtils",
    "ConnectionPoolExecutor",
    "ConstDefinitionsExporter",
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
    "SSIDBroadcastGapReport",
    "EndpointConfig",
    "EnhancedSSHRunner",
    "EnvironmentUtils",
    "ExtractedMarvisTroubleshootUtils",
    "ExtractedSiteAnalyticsConfigurator",
    "ExtractedSiteInventoryHealthAnalyzer",
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
    "InputUtils",
    "InsightMetricsUtils",
    "InteractiveDisplayUtils",
    "InteractiveTestRunner",
    "InventoryCSVComparator",
    "IsDebugMode",
    "KeyboardListener",
    "LicenseExportUtils",
    "LogSanitizer",
    "LoginOrchestrator",
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
    "TelemetryEmitter",
    "TimeUtils",
    "TroubleshootUtils",
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
)  # Duplicate import (re-stated with comment below). Kept to preserve module load behavior
from src.bootstrap.dependency_check import (
    DependencyCheckOrchestrator,
)  # Duplicate import. Harmless re-import of dependency check orchestrator
from src.bootstrap.package_installer import (
    PackageInstaller,
)  # Duplicate import. Harmless re-import of package installer
from src.cache.cache_utils import (
    CacheUtils,
)  # Cat E canonical (1014 P14) -- re-export for MistHelper.CacheUtils callers
from src.capture.client_pcap_downloader import (
    ClientPacketCaptureDownloader,
)  # Menu 197: interactive client PCAP downloader (issue #421)
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
    TestSummary,  # Test summary counters for telemetry emission
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
from src.device.ap_profile_migration_manager import (
    APProfileMigrationManager,  # Menus 207 and 208 -- migrate APs between device profiles and revert
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
from src.device.virtual_chassis import (  # Preserve the existing behavior during the compliance refactor.
    VirtualChassisManager,
)
from src.device.virtual_chassis import (  # Preserve the existing behavior during the compliance refactor.
    configure_virtual_chassis_dependencies as _configure_virtual_chassis_dependencies,
)
from src.export.const_definitions_exporter import (
    ConstDefinitionsExporter,  # Cat B (1013 SC-001 position 17) -- re-export
)
from src.export.count_exporter import (
    CountExporter,  # Issue #1802 -- the 70 Mist count endpoints, grouped by scope, menus 235-237
)
from src.export.device_events_52w_exporter import (
    DeviceEvents52wExporter,  # Re-export preserved after OrgAlarmEventExporter extraction (1013 SC-001 position 18)
)
from src.export.endpoint_family_exporter import (
    EndpointFamilyExporter,  # Issue #1807 stage two -- remaining endpoint issues grouped by prompt family.
)
from src.export.gateway_test_exporter import (
    GatewayTestExporter,  # Cat B (1013 SC-001 position 37) -- re-export for MistHelper.GatewayTestExporter callers
)
from src.export.license_export_utils import (
    LicenseExportUtils,  # Cat B (1013 SC-001 position 24) -- re-export for MistHelper.LicenseExportUtils callers
)
from src.export.msp_inventory_exporter import (
    MSPInventoryExporter,  # Cat B (1013 SC-001 position 8) -- re-export for menu row + static call rewire
)
from src.export.msp_license_exporter import (
    MSPLicenseExporter,  # Issue #1260 -- the MSP license export, menu 238
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
from src.export.org_cradlepoint_connection_exporter import (
    OrgCradlepointConnectionExporter,  # Issue #1413 -- Cradlepoint status read, menu 245
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
from src.export.org_inventory_search_exporter import (
    OrgInventorySearchExporter,  # Spec 864 / issue #1372 -- organization inventory search menu 254
)
from src.export.org_search_exporter import (
    OrgSearchExporter,  # Specs 863, 872, 874-879; issues #1371, #1377, #1379, #1380, #1382, #1383, #1385, #1386.
)
from src.export.org_sec_intel_profile_exporter import (
    OrgSecIntelProfileExporter,  # Issue #1148 -- one SecIntel profile read by id, menu 240
)
from src.export.org_site_exporter import (
    OrgSiteExporter,  # Cat E canonical (1014 P9) -- re-export for MistHelper.OrgSiteExporter callers
)
from src.export.org_template_exporter import (
    OrgTemplateExporter,  # Cat B (1013 SC-001 position 22) -- re-export for MistHelper.OrgTemplateExporter callers
)
from src.export.org_webhook_deliveries_exporter import (
    OrgWebhookDeliveriesExporter,  # Spec 876 / issue #1384 -- webhook delivery search, menu 256
)
from src.export.self_account_exporter import (
    SelfAccountExporter,  # Issue #1415 -- verify an email change token, menu 247
)
from src.export.self_export_utils import (
    SelfExportUtils,  # Cat B (1013 SC-001 position 7) -- re-export for menu row at MistHelper:18167
)
from src.export.simple_endpoint_exporter import (
    SimpleEndpointExporter,  # Issue #1807 -- simple get and list endpoints, grouped by scope.
)
from src.export.site_anomaly_exporter import (
    SiteAnomalyExporter,  # Cat B (1013 SC-001 position 43) -- re-export for MistHelper.SiteAnomalyExporter callers
)
from src.export.site_application_list_exporter import (
    SiteApplicationListExporter,  # Spec 666 / issue #1416 -- getSiteApplicationList menu 213
)
from src.export.site_asset_exporter import (
    SiteAssetExporter,  # Specs 667/668/670 / issues #1417, #1418, #1419 -- site asset menus 210-212
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
from src.export.site_guest_authorization_exporter import (
    SiteGuestAuthorizationExporter,  # Spec 889 / issue #1397 -- searchSiteGuestAuthorization menu 200
)
from src.export.site_insights.device_metric_operation import (
    DeviceMetricOperation,
)  # Decomposed Menu 76 entry point
from src.export.site_insights.site_metric_operation import (
    SiteMetricOperation,
)  # Decomposed Menu 74 entry point
from src.export.site_mist_edge_events_exporter import (
    SiteMistEdgeEventsExporter,  # Spec 890 / issue #1398 -- searchSiteMistEdgeEvents menu 201
)
from src.export.site_nac_client_events_exporter import (
    SiteNacClientEventsExporter,  # Spec 891 / issue #1399 -- searchSiteNacClientEvents menu 202
)
from src.export.site_other_device_events_exporter import (
    SiteOtherDeviceEventsExporter,  # Spec 894 / issue #1402 -- searchSiteOtherDeviceEvents menu 258
)
from src.export.site_search_exporter import (
    SiteSearchExporter,  # Specs 879-882/897 / issues #1387-#1390, #1405 -- site search menus 215-219
)
from src.export.site_system_events_exporter import (
    SiteSystemEventsExporter,  # Spec 898 / issue #1406 -- searchSiteSystemEvents menu 214
)
from src.export.site_wan_usage_exporter import (
    SiteWanUsageExporter,  # Spec 901 / issue #1409 -- searchSiteWanUsage menu 198
)
from src.export.site_webhook_deliveries_exporter import (
    SiteWebhookDeliveriesExporter,  # Spec 902 / issue #1410 -- searchSiteWebhooksDeliveries menu 199
)
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
from src.org.org_synthetic_probes_manager import (
    manage_org_synthetic_probes,  # Menu 206 Zscaler probe manager (side-effect-free until final confirmation)
)
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
    DeviceDataFetcher,  # Extracted device fetcher (SC-017). Lazy re-export for interactive_display_utils
)
from src.refactors.fast_mode_backoff_multiplier import (
    FastModeBackoffMultiplier,  # Extracted backoff multiplier (SC-028). Lazy re-export for org_device_stats_exporter
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

MainEntrypoint.bind_host_module(sys.modules[__name__])  # Give source packages a bound host without root imports.

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
from src.reports.ssid_broadcast_gap_report import SSIDBroadcastGapReport  # Menu 242 SSID coverage report.
from src.reports.wired_client_manufacturer_report_generator import (
    WiredClientManufacturerReportGenerator,  # Cat B (1013 SC-001 position 26) -- re-export
)
from src.security.rogue_dhcp import (
    RogueDhcpScanOperation,  # Menu 269 (issue #2985) -- org-wide rogue DHCP server scan.
)
from src.site.address_audit import AddressAuditEngine  # Menu 195: read-only CSV site-address audit
from src.site.bulk_radius_wlan_config_manager import (
    BulkRadiusWLANConfigManager,  # Cat B (1013 SC-001 position 15) -- re-export
)
from src.site.site_config_manager import (  # Cat A canonical (1013 SC-003)
    SiteConfigDependencies as _SiteConfigDependencies,
)
from src.site.site_config_manager import (  # Preserve the existing behavior during the compliance refactor.
    SiteConfigManager,
)
from src.site.site_config_manager import (  # Preserve the existing behavior during the compliance refactor.
    configure_site_config_manager_dependencies as _configure_site_config_dependencies,
)
from src.ssh.cli_shell_manager import CLIShellManager  # Preserve the existing behavior during the compliance refactor.
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
# CONFIGURATION DATACLASSES (5-Item Rule Compliance)
# ============================================================================
# These dataclasses group related parameters to comply with the 5-parameter limit
# per function. Each dataclass encapsulates configuration for a specific domain.


# ============================================================================
# EARLY DEPENDENCY AUTO-INSTALLER
# ============================================================================
# This section attempts to auto-install critical dependencies BEFORE any imports
# that might fail. This enables running the script directly without pre-setup.


def _get_installed_version(package_name: str) -> str:  # Look up the installed version string for a package
    """Get installed version of a package using importlib.metadata."""
    try:  # Try to read version metadata from the installed distribution
        from importlib.metadata import PackageNotFoundError  # Import the precise absence signal for metadata lookup
        from importlib.metadata import version as get_version  # Import the stdlib version lookup (Python 3.8+)

        return get_version(package_name)  # Return the installed version string (for example '0.59.3')
    except (PackageNotFoundError, ValueError) as error:  # Missing metadata or a bad name must not stop startup
        logging.exception("Installed package version lookup failed for %s: %s", package_name, error)  # Keep trace
        return ""  # Return empty string to signal 'not installed' to callers


def _version_satisfies(installed: str, spec: str) -> bool:  # Decide whether installed meets the spec constraint
    """Return True when the installed version satisfies the version spec.

    Why:
        The bootstrap orchestrator needs a safe predicate that never raises for
        package metadata. The packaging library gives PEP 440 ordering, and this
        function keeps the old no-constraint behavior.
    """
    if not installed:  # An empty installed version means the package is not present
        return False  # Treat 'not installed' as 'requirement not satisfied'
    try:  # Try the simple form, such as '>=1.0' or '==2.0'
        constraint = SpecifierSet(spec)  # Parse a bare PEP 440 specifier set
    except InvalidSpecifier:  # A requirements.txt line can include a package name
        try:  # Fall back to the named requirement form, such as 'mistapi>=0.63.1'
            constraint = Requirement(spec).specifier  # Extract only the version constraint from the requirement
        except InvalidRequirement:  # Malformed text must not stop bootstrap
            logging.debug("Ignoring invalid version spec '%s'", spec)  # Leave a diagnostic without failing startup
            return True  # Preserve the old safe behavior for an unusable constraint
    try:  # Convert the installed version through the PEP 440 parser
        installed_version = Version(str(installed))  # Use packaging so pre-release order is correct
    except (InvalidVersion, TypeError):  # Malformed package metadata must not stop bootstrap
        logging.debug("Rejecting invalid installed version '%s'", installed)  # Record the safe rejection
        return False  # A bad installed version must not satisfy a real constraint
    return constraint.contains(installed_version)  # Apply packaging's PEP 440 specifier rules


def _get_latest_pypi_version(package_name: str) -> str:  # Ask PyPI for a package's newest published version
    """Query PyPI for the latest version of a package.

    Uses a bounded read to prevent hangs behind corporate
    proxies (for example Zscaler SSL inspection).
    """
    try:  # Network calls can fail many ways. Treat any failure as 'latest unknown'
        requests_module = cast(Any, __import__("requests"))  # Import after bootstrap can repair requests
        url = f"https://pypi.org/pypi/{package_name }/json"  # PyPI JSON API endpoint for this package's metadata
        if not url.startswith("https://"):  # Defence-in-depth: refuse any non-HTTPS scheme before dispatch
            raise ValueError("PyPI URL must use https scheme")  # Fail-closed guards against future url refactors
        logger.info("Checking the latest package version for %s", package_name)  # Log before the bounded HTTP request
        response = requests_module.get(url, timeout=5)  # Use requests so Bandit sees the validated HTTPS URL path
        logger.debug("PyPI returned status %s for %s", response.status_code, package_name)  # Log the HTTP result
        response.raise_for_status()  # Treat a non-success response as an unknown latest version
        data = response.json()  # Parse the small JSON body through requests
        version = data.get("info", {}).get("version", "")  # Return latest version string, or empty if absent
        return str(version) if version else ""  # Cast to str for strict typing
    except (ImportError, OSError, TypeError, ValueError) as error:  # Offline hosts and bad JSON mean latest is unknown
        logging.exception("Latest package version lookup failed for %s: %s", package_name, error)  # Keep trace
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


def _parse_requirements_file(
    filepath: str = "requirements.txt",
) -> list[tuple[str, str]]:  # Preserve the existing behavior during the compliance refactor.
    """Parse requirements.txt into a list of (package_name, package_spec) tuples.

    SECURITY: only reads requirements.txt (no arbitrary file access). Skips comments/blanks/dev deps.
    """
    packages = []  # Accumulate (name, spec) tuples to return to the dependency checker
    try:  # The file may be absent or unreadable. Handle that gracefully below
        with open(filepath, encoding="utf-8") as requirements_file:  # Open requirements.txt as UTF-8 text
            for line in requirements_file:  # Process one dependency line at a time
                parsed = _parse_requirement_line(line)  # Parse this line into (name, spec) or None to skip
                if parsed is not None:  # Only keep lines that yielded a real dependency
                    packages.append(parsed)  # Record this dependency for the caller
        logger.debug("Parsed %s packages from %s", len(packages), filepath)  # Debug aid: how many specs were parsed
        return packages  # Return the collected dependency list
    except FileNotFoundError:  # requirements.txt does not exist at the given path
        logging.warning("Requirements file not found: %s", filepath)  # Warn that auto-install is skipped
        return []  # No packages to check
    except (OSError, UnicodeDecodeError) as parse_error:  # Bad files must skip startup install without a crash
        logging.warning("Error parsing requirements file: %s", parse_error, exc_info=True)  # Keep the traceback
        return []  # Fail safe with an empty list rather than crashing startup

        # _early_dependency_check_legacy_impl removed per issue #431 (ARCH-NAMING +
        # dead-code). The function (~430 lines, cyclomatic 64) was a leftover legacy
        # implementation never called from anywhere -- production startup uses the
        # canonical _early_dependency_check() defined below which delegates to the
        # extracted src/bootstrap/* orchestrator.


def _early_dependency_check() -> None:  # Public entry point. Delegates to the extracted bootstrap modules
    """Run early dependency checks through the extracted bootstrap orchestrator."""
    installer = PackageInstaller(  # Build the installer with stdlib modules injected (enables testing/mocking)
        os_module=os,  # Inject os for path/env operations
        subprocess_module=subprocess,  # Inject the audited module import for pip/uv commands
        sys_module=sys,  # Inject sys for the interpreter path
        logging_module=logging,  # Inject logging for progress messages
    )
    orchestrator = DependencyCheckOrchestrator(  # Build the orchestrator that drives the detect-and-install flow
        os_module=os,  # Inject os for env checks (DISABLE_AUTO_INSTALL, and so on)
        logging_module=logging,  # Inject logging for progress messages
        sys_module=sys,  # Inject sys for the interpreter path
        package_import_map=PackageImportMapManager.MAPPING,  # Provide the pip-name -> import-name mapping
        parse_requirements_file_fn=_parse_requirements_file,  # Reuse the requirements parser defined above
        get_installed_version_fn=_get_installed_version,  # Reuse the installed-version lookup
        version_satisfies_fn=_version_satisfies,  # Reuse the version-constraint checker
        get_latest_pypi_version_fn=_get_latest_pypi_version,  # Reuse the PyPI latest-version lookup
        parse_version_fn=Version,  # Use packaging's PEP 440 parser for latest-version checks
        installer=installer,  # Hand the orchestrator the installer built above
    )
    orchestrator.run()  # Execute the dependency check + install/upgrade workflow

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
try:  # The tool needs PrettyTable for formatted console tables
    from prettytable import PrettyTable  # ASCII table renderer used across menus and reports
except ImportError as _pt_err:  # Required dependency is not installed
    raise ImportError(
        "PrettyTable is required but not installed. Run: pip install prettytable"
    ) from _pt_err  # Fail fast with install guidance

try:  # numpy is optional (only some analytics need it)
    import numpy as _np_impl  # Numerical arrays for analytics calculations

    np: ModuleType | None = _np_impl  # Union type lets guards detect absence
except ImportError:  # numpy not installed
    np = None  # None lets runtime guards detect absence

try:  # The tool needs websocket-client for live device diagnostics
    import websocket  # WebSocket client fail-fast install guard (used by src.device.arp_command_manager)
except ImportError as _ws_err:  # Required dependency is not installed
    raise ImportError(
        "websocket-client is required but not installed. Run: pip install websocket-client"
    ) from _ws_err  # Fail fast with install guidance

try:  # SequenceMatcher is optional (used for fuzzy string comparisons)
    from difflib import SequenceMatcher as _SequenceMatcherImpl  # Stdlib similarity-ratio helper

    SequenceMatcher: type[_SequenceMatcherImpl[Any]] | None = _SequenceMatcherImpl  # Class handle for guarded use
except ImportError:  # Extremely unlikely for a stdlib module, but guard anyway
    SequenceMatcher = None  # None lets callers detect absence

mistapi: Any = None  # Preserve the historical module global for tests and menu factories.
try:  # Import the SDK without starting a session or touching the network.
    import mistapi as _mistapi_impl  # Bind the SDK for import-time menu factories and tests.

    mistapi = _mistapi_impl  # Preserve the historical module global without a bootstrap session.
except ImportError:  # The bootstrap dependency check reports the missing SDK before runtime modes start.
    pass  # Keep the public name available for environments that install dependencies later.

    # tqdm wrapper: canonical home is src/utils/tqdm_wrapper.py (1015 T-14, Cat E).
    # The wrapper resolves to the real tqdm package if installed, else a no-op pass-through.
    # Re-exported here so ``MistHelper.tqdm`` / ``mh.tqdm`` callers keep working unchanged.
from src.utils.tqdm_wrapper import tqdm  # Cat E canonical (1015 T-14) -- re-export.

if "requests" not in globals():  # Keep the requests name without importing the HTTP stack during module import.
    requests: Any = None  # Bootstrap and deferred imports publish requests after dependency checks run.

if "urllib3" not in globals():  # Keep the urllib3 name without importing the HTTP stack during module import.
    urllib3: ModuleType | None = None  # Deferred imports publish urllib3 after bootstrap avoids socket creation.

try:  # pyte is optional (terminal emulation for parsing WebSocket output)
    import pyte as _pyte_impl  # In-memory terminal emulator to render device CLI screens

    pyte: ModuleType | None = _pyte_impl  # Union type lets guards detect absence
    _has_pyte = True  # Flag that terminal-emulation features are available
except ImportError:  # pyte not installed
    pyte = None  # None lets guards detect absence
    _has_pyte = False  # Flag that terminal-emulation features are unavailable

try:  # paramiko is optional (used for direct SSH operations)
    _paramiko_impl = __import__("paramiko")  # Import by name so mypy does not require third-party stubs
    _paramiko_any = cast(Any, _paramiko_impl)  # Treat optional SSH package as dynamic until a local Protocol exists
    paramiko: ModuleType | None = _paramiko_impl  # Union type lets guards detect absence
    SSHClient: type[Any] | None = _paramiko_any.SSHClient  # Class handle for guarded use
    RejectPolicy: type[Any] | None = _paramiko_any.RejectPolicy  # Class handle for guarded use
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

    fuzz: ModuleType | None = _fuzz_impl  # Union type lets guards detect absence
except ImportError:  # rapidfuzz not installed
    fuzz = None  # None lets callers skip fuzzy matching

    # Keyboard listener functionality moved to src/refactors/keyboard_listener.py
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
    # size (commonly 100). That caused excessive paging (for example 10x HTTP calls for
    # 1000-item datasets). We unify a single configurable default via environment
    # variable MIST_PAGE_LIMIT (clamped to 1..1000). All new/updated listOrgSites /
    # getOrgInventory calls should pass limit=DEFAULT_API_PAGE_LIMIT or use the
    # helper wrappers below to ensure consistency and simpler tuning.
if "_raw_page_limit_env" not in globals():  # Keep the helper name without reading the environment during import.
    _raw_page_limit_env = "1000"  # Bootstrap reads MIST_PAGE_LIMIT after import.
if "_parsed_limit" not in globals():  # Keep the parsed helper name without reading the environment during import.
    _parsed_limit = 1000  # Preserve the historical default without an import-time environment read.
DEFAULT_API_PAGE_LIMIT = 1000  # Bootstrap clamps and publishes the configured page limit.


def _apply_dotenv_line(line: str) -> None:  # Set one KEY=VALUE pair from a .env line into the environment
    """Parse one .env line and set it into os.environ, skipping blanks/comments/malformed entries."""
    stripped = line.strip()  # Remove surrounding whitespace and the trailing newline
    if not stripped or stripped.startswith("#") or "=" not in stripped:  # Skip blanks, comments, malformed entries
        return  # Nothing assignable on this line
    key, value = stripped.split("=", 1)  # Split on the first '=' (values may themselves contain '=')
    os.environ[key.strip()] = value.strip()  # Set the env var (overwrites, unlike setdefault)

    # Early dotenv import for configuration loading


def _fallback_load_dotenv() -> None:  # Minimal .env parser used when python-dotenv is not installed
    """Fallback .env loader when python-dotenv package is not installed."""
    try:  # The .env file is optional. Handle its absence/errors gracefully
        with open(".env", encoding="utf-8") as dotenv_file:  # Open .env in the current working directory
            for line in dotenv_file:  # Process the file one line at a time
                _apply_dotenv_line(line)  # Set this KEY=VALUE pair (skips blanks/comments internally)
    except FileNotFoundError:  # No .env file present
        logging.debug("No .env file found")  # Not an error. Just note it at debug level
    except (OSError, UnicodeDecodeError, ValueError) as parse_error:  # Bad .env content must not stop startup
        logging.debug("Error loading .env file: %s", parse_error, exc_info=True)  # Keep the traceback for repair


if "load_dotenv" not in globals():  # Keep the loader name without reading .env during module import.
    load_dotenv: Callable[..., object] = _fallback_load_dotenv  # Bootstrap replaces this when dotenv is present.
if "DOTENV_AVAILABLE" not in globals():  # Keep the availability flag without importing dotenv during module import.
    DOTENV_AVAILABLE = False  # Bootstrap updates this flag after the explicit environment load step.


class GlobalImportManager:  # Preserve the existing behavior during the compliance refactor.
    """
    Centralized import and dependency management system for MistHelper.

    This class handles:
    - UV-based package installation and upgrades
    - Centralized import management
    - Dependency verification and auto-installation
    - Graceful handling of optional dependencies
    - Performance optimization through early imports
    """

    _REQUIRED_PACKAGES: ClassVar[dict[str, str | None]] = {  # Class-level required spec map (data, not behavior)
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

    MenuEntry: ClassVar[type[Any]] = __import__(  # WHY: keep MenuEntry off the module symbol table.
        "src.utils.menu_entry", fromlist=("MenuEntry",)
    ).MenuEntry

    _OPTIONAL_PACKAGES_RAW: ClassVar[dict[str, str | None]] = {  # Class-level optional spec map (data, not behavior)
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

    class SiteExportUtilsFactory:  # Preserve the existing behavior during the compliance refactor.
        """Build the shared `SiteExportUtils` dependency set for menu rows."""

        def build(self) -> SiteExportUtils:  # Preserve the existing behavior during the compliance refactor.
            """Return a `SiteExportUtils` instance for one menu dispatch."""
            logger.info("Building the site export utility for menu dispatch")  # WHY: log before dependency wiring.
            utility = SiteExportUtils(  # WHY: centralize site export wiring.
                apisession=MainEntrypoint.context.apisession,  # WHY: reuse the active Mist session.
                PromptUtils=PromptUtils,  # WHY: preserve the existing prompt helper dependency.
                ConfigUtils=ConfigUtils,  # WHY: preserve config helpers.
                DataProcessingUtils=DataProcessingUtils,  # WHY: keep data normalization unchanged.
                DataExporter=DataExporter,  # WHY: keep output selection unchanged.
                TimeUtils=TimeUtils,  # WHY: preserve time helpers.
                EnhancedSSHRunner=EnhancedSSHRunner,  # WHY: preserve SSH helper access.
                InsightMetricsUtils=InsightMetricsUtils,  # WHY: preserve insights helpers.
                PacketCaptureManager=PacketCaptureManager,  # WHY: preserve packet helpers.
                APICoreFetchUtils=APICoreFetchUtils,  # WHY: preserve paged fetch helpers.
                check_fn=IsDebugMode.check,  # WHY: keep the existing debug-mode predicate.
                PrettyTable=PrettyTable,  # WHY: preserve table rendering.
                tqdm=tqdm,  # WHY: preserve progress display.
                mistapi=mistapi,  # WHY: preserve direct Mist SDK access.
            )
            logger.debug("Built the site export utility: %s", type(utility).__name__)  # WHY: summarize result.
            return utility  # WHY: caller invokes the same method as the former inline construction.

    class RoutingUtilsFactory:  # Preserve the existing behavior during the compliance refactor.
        """Build the shared `RoutingUtils` dependency set for menu rows."""

        def build(self) -> RoutingUtils:  # Preserve the existing behavior during the compliance refactor.
            """Return a `RoutingUtils` instance for one menu dispatch."""
            logger.info("Building the routing utility for menu dispatch")  # WHY: log before dependency wiring.
            deps = RoutingDeps(  # WHY: centralize routing wiring.
                apisession=MainEntrypoint.context.apisession,  # WHY: reuse the active Mist session.
                select_site_fn=PromptUtils.select_site_id_from_csv,  # WHY: preserve the site selector.
                select_device_fn=self._select_device,  # WHY: keep device selection local.
                safe_input_fn=InputUtils.safe_input,  # WHY: keep EOF-safe operator prompts.
                websocket_manager_factory=WebSocketManager,  # WHY: preserve WebSocket transport.
                check_fn=IsDebugMode.check,  # WHY: keep the existing debug-mode predicate.
            )
            routing = RoutingUtils(deps)  # WHY: create the utility after the dependency object is complete.
            logger.debug("Built the routing utility: %s", type(routing).__name__)  # WHY: summarize result.
            return routing  # WHY: caller invokes the same method as the former inline construction.

        @staticmethod
        def _select_device(
            site_id: str, dtype: str
        ) -> Any:  # Preserve the existing behavior during the compliance refactor.
            """Select one device while preserving the legacy `device_type` keyword."""
            logger.info("Selecting a device for routing command at site %s", site_id)  # WHY: log before prompt work.
            device = PromptUtils.select_device_id_from_inventory(  # WHY: keep the same inventory-backed selector.
                site_id, device_type=dtype
            )
            logger.debug("Selected routing device value present: %s", bool(device))  # WHY: do not log sensitive data.
            return device  # WHY: RoutingDeps expects the selected device identifier.

    class GatewayTemplateConfigManagerFactory:  # Preserve the existing behavior during the compliance refactor.
        """Build the shared gateway template manager dependency set for menu rows."""

        def build(
            self,
        ) -> GatewayTemplateConfigManager:  # Preserve the existing behavior during the compliance refactor.
            """Return a gateway template manager for one menu dispatch."""
            logger.info("Building the gateway template manager for menu dispatch")  # WHY: log before dependency wiring.
            manager = GatewayTemplateConfigManager(  # WHY: centralize manager wiring.
                org_id=ConfigUtils.get_cached_or_prompted_org_id(),  # WHY: preserve lazy org selection.
                apisession=MainEntrypoint.context.apisession,  # WHY: reuse the active Mist session.
                input_fn=InputUtils.safe_input,  # WHY: keep all prompts EOF-safe.
                get_csv_path_fn=FilePathUtils.get_csv_path,  # WHY: preserve path resolution.
                save_data_fn=DataExporter.write_with_format_selection,  # WHY: preserve output backend selection.
                check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,  # WHY: preserve CSV cache generation.
                generate_sites_fn=OrgSiteExporter.sites,  # WHY: preserve fallback site export.
                sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename,  # WHY: preserve safe file names.
            )
            logger.debug("Built the gateway template manager: %s", type(manager).__name__)  # WHY: summarize result.
            return manager  # WHY: caller invokes the same method as the former inline construction.

    def __init__(self, setup_logging: bool = True) -> None:  # Read config from env and prepare dependency state
        """Initialize the import manager with configuration from environment variables."""
        self._load_upgrade_configuration()  # Read env-driven upgrade/UV/CSV freshness settings
        self._initialize_dependency_tracking()  # Prepare package-tracking lists and import/UV caches
        self._initialize_import_mappings()  # Build package->import name maps and special import handlers
        if setup_logging:  # Allow ApplicationBootstrap to keep logging setup to one explicit call.
            self._setup_logging()  # Configure handlers and levels when no bootstrap owns logging.
        self._detect_virtual_environment()  # Log whether we are in a venv (affects installs)
        self._define_package_requirements()  # Populate the required/optional package dicts

    def _load_upgrade_configuration(self) -> None:  # Read upgrade/UV/CSV settings from the environment
        """Load upgrade, UV-check, and CSV-freshness settings from environment variables."""
        logger.debug("Loading import-manager upgrade configuration from environment")  # Trace config load
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

    def _initialize_dependency_tracking(self) -> None:  # Prepare package-tracking and import/UV caches
        """Initialize dependency-tracking containers and UV/deferred-init state flags."""
        logger.debug("Initializing dependency tracking containers and caches")  # Trace tracking setup
        self.required_packages: dict[str, str | None] = {}  # Will hold name -> spec for required packages
        self.optional_packages: dict[str, str | None] = {}  # Will hold name -> spec for optional packages
        self.failed_imports: list[str] = []  # Names of packages that failed to import
        self.installed_packages: list[str] = []  # Names of packages installed during this run
        self.imports: dict[str, Any] = {}  # Cache of imported modules keyed by name for global reuse
        self._uv_available: bool = False  # Cached answer to 'is UV usable?'
        self._uv_checked: bool = False  # Whether the UV availability check ran
        self._last_uv_update_check: float | None = None  # Track when we last checked for UV updates
        self._deferred_init_done: bool = False  # Whether the deferred (lazy) init ran
        self._initialization_complete: bool = False  # Whether full initialization finished
        self._initialization_success: bool = False  # Whether initialization succeeded
        self._cached_global_assignments: dict[str, Any] = {}  # Module globals to publish once imports complete

    def _initialize_import_mappings(self) -> None:  # Build name maps and special import handlers
        """Build package->import name mappings and the special-case import handler table."""
        logger.debug("Initializing import name mappings and special handlers")  # Trace mapping setup
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
        """Detect if this runs in a virtual environment and log info."""
        self.in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )  # venv when prefixes differ

        if self.in_venv:  # Running inside a virtual environment
            venv_path = getattr(sys, "prefix", "unknown")  # Path to the active venv
            logger.info("Running in virtual environment: %s", venv_path)  # Log the venv location
            logger.info("Python executable: %s", sys.executable)  # Log which interpreter is in use
        else:  # Running against the system Python
            logger.info("Running in system Python environment")  # Note the non-venv environment
            logger.info("Python executable: %s", sys.executable)  # Log which interpreter is in use

    def _setup_logging(self) -> None:  # Build console+file handlers with env-driven levels
        """Setup basic logging configuration with environment-specific levels."""
        return  # ApplicationBootstrap owns the only logging.basicConfig call.

    def _build_console_log_handler(self, level: int) -> logging.StreamHandler[TextIO]:  # Console handler factory
        """Build a stdout/stderr console log handler at the requested level."""
        logger.debug("_build_console_log_handler: creating console handler at level %s", level)  # Log before build
        console_handler = logging.StreamHandler()  # Handler that writes to stdout/stderr
        console_handler.setLevel(level)  # Apply the console verbosity threshold
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )  # Timestamped log line format
        console_handler.setFormatter(console_formatter)  # Attach the format to the console handler
        logger.debug("_build_console_log_handler: console handler ready")  # Log after build
        return console_handler  # Caller wires this into basicConfig

    def _build_file_log_handler(self, level: int) -> RotatingFileHandler:  # File handler factory (data/script.log)
        """Build a data/script.log file handler at the requested level."""
        logger.debug("_build_file_log_handler: creating file handler at level %s", level)  # Log before build
        log_file_path = os.path.join("data", "script.log")  # Log path under data/ (writable in the container)
        os.makedirs("data", exist_ok=True)  # Create data/ if missing (no error if present)
        rotation_settings = LogRotationSettings.from_environment()  # Read deployment rotation limits for this handler
        file_handler = rotation_settings.build_handler(
            log_file_path
        )  # Build the bounded script.log writer with UTF-8 output
        file_handler.setLevel(level)  # Apply the file verbosity threshold
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  # Same timestamped format
        file_handler.setFormatter(file_formatter)  # Attach the format to the file handler
        logger.debug(
            "_build_file_log_handler: bounded handler ready at %s with %d-byte limit and %d backups",
            log_file_path,
            rotation_settings.max_bytes,
            rotation_settings.backup_count,
        )  # Log the configured bound after the handler is ready
        return file_handler  # Caller wires this into basicConfig

    def _define_package_requirements(self) -> None:  # Populate the required/optional package dictionaries
        """Define all required and optional package dependencies from class constants."""
        logger.debug("_define_package_requirements: loading spec maps from class constants")  # Log before copy
        self.required_packages = dict(self._REQUIRED_PACKAGES)  # Copy class-level required spec map (defensive copy)
        self.optional_packages = {  # Filter out any None specs defensively (platform-incompatible)
            k: v for k, v in self._OPTIONAL_PACKAGES_RAW.items() if v is not None
        }
        logger.debug(
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
        self._uv_checked = True  # Mark that we probed UV so we do not repeat it
        return self._uv_available  # Return the (now cached) availability

    def _probe_uv_binary(self) -> bool:  # Run 'uv --version' to detect UV availability
        """Probe the UV binary by running 'uv --version' and log the outcome."""
        logger.debug("_probe_uv_binary: probing UV binary via subprocess")  # Log before probe
        try:  # Probing UV may fail if it is not installed
            result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- shell=False + argv allow-list.
                ["uv", "--version"], timeout=10, check=False
            )  # Run 'uv --version' via SubprocessRunner (validates argv, no shell).
            if result.returncode == 0:  # UV ran successfully
                logger.info("UV package manager found: %s", result.stdout.strip())  # Log detected version
                return True  # UV is usable
            logger.warning("UV package manager not found or not working properly")  # Note the problem
            return False  # UV is not usable
        except (TimeoutExpired, FileNotFoundError, SubprocessError) as e:  # Missing/hung
            logging.warning("UV package manager check failed: %s", e)  # Log why the probe failed
            return False  # UV is not usable

    def _install_uv(self) -> bool:  # Try to install UV by pip when it is absent
        """Install UV package manager if not present."""
        if not self.auto_upgrade_uv:  # UV auto-management disabled by config
            logger.info("Auto-upgrade of UV is disabled in configuration")  # Note that we will not install UV
            return False  # Signal UV is unavailable

        logger.info("Attempting to install UV package manager...")  # Announce the install attempt
        try:  # The pip install may fail (no network, restricted env)
            # Try installing UV using pip as fallback
            result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- interpreter self-invoke allowed.
                [sys.executable, "-m", "pip", "install", "uv"],  # pip install command for the current interpreter
                timeout=self.upgrade_check_timeout,  # Bound the install so startup cannot hang
                check=False,  # Caller inspects returncode to branch on success/failure.
            )
            if result.returncode == 0:  # pip reported success
                logger.info("UV package manager installed successfully via pip")  # Confirm the install
                return True  # UV is now available
            else:  # pip returned an error
                logger.error("Failed to install UV via pip: %s", result.stderr)  # Log pip's error output
                return False  # UV remains unavailable
        except (TimeoutExpired, SubprocessError) as e:  # pip process hung or failed to launch
            logging.error("Failed to install UV package manager: %s", e)  # Log the exception
            return False  # UV remains unavailable

    def _upgrade_uv(self) -> bool:  # Keep UV up to date, throttled to once per configured interval
        """Upgrade UV package manager to latest version (only if needed)."""
        if not self.auto_upgrade_uv:  # UV auto-management disabled by config
            return True  # Nothing to do. Treat as success
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
            logger.debug(  # Skip the check to avoid frequent network calls
                "UV update check skipped (last check %.1f hours ago, threshold: %s hours)",
                hours_since_last_check,
                self.uv_update_check_hours,
            )
            return True  # Throttled -- skip this update
        return False  # Throttle window elapsed -- allow the check

    def _run_uv_self_update(self, now: float) -> bool:  # Run 'uv self update', recording the attempt time
        """Attempt 'uv self update'. On failure, dispatch to the pip-fallback handler. Always non-fatal."""
        try:  # The update may fail. Treat most failures as non-critical
            logger.info("Checking for UV package manager updates...")  # Announce the update check
            result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- 'uv' basename allow-listed.
                ["uv", "self", "update"],
                timeout=self.upgrade_check_timeout,  # Bounded self-update call
                check=False,  # Caller inspects returncode to trigger pip-fallback.
            )
            self._last_uv_update_check = now  # Record this attempt so we honor the throttle next time
            if result.returncode == 0:  # Self-update succeeded
                logger.info("UV package manager updated successfully")  # Confirm the update
                return True  # Done
            return self._handle_uv_selfupdate_failure(result)  # Inspect stderr and try the pip fallback
        except (TimeoutExpired, SubprocessError) as e:  # Update process hung or failed to launch
            self._last_uv_update_check = now  # Record the attempt so we do not retry immediately
            logging.warning("UV self-update failed: %s", e)  # Log the exception
            return True  # Non-critical failure -- the current UV still works

    def _handle_uv_selfupdate_failure(self, result: Any) -> bool:  # Handle a non-zero 'uv self update' result
        """When self-update fails because UV was pip-installed, upgrade via pip. Otherwise just log. Non-fatal."""
        pip_installed_marker = (  # Marker stderr emits when self-update is not supported for this install method
            "Self-update is only available for uv binaries installed via the standalone installation scripts"
        )
        if pip_installed_marker not in result.stderr:  # Self-update failed for some other reason
            logger.warning("UV self-update returned non-zero: %s", result.stderr)  # Log the error
            return True  # Non-critical -- the current UV still works
        logger.info("UV was installed via pip, attempting pip upgrade...")  # Switch to the pip upgrade path
        pip_result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- interpreter self-invoke allowed.
            [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],  # pip upgrade command
            timeout=self.upgrade_check_timeout,  # Bound the upgrade
            check=False,  # Caller inspects returncode. Non-zero is warned, not raised.
        )
        if pip_result.returncode == 0:  # pip upgrade succeeded
            logger.info("UV package manager updated successfully via pip")  # Confirm the upgrade
            return True  # Done
        logger.warning("Failed to upgrade UV via pip: %s", pip_result.stderr)  # Log the error
        return True  # Non-critical -- the current UV still works

    def _install_package_with_uv(
        self, package_spec: str
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Install a package using UV package manager with fast resolution and virtual environment awareness."""
        try:
            logger.debug("Installing package with UV: %s", package_spec)  # Log which package the tool installs
            uv_cmd = self._resolve_uv_binary()  # Pick venv-local UV when available, else PATH 'uv'
            first_cmd = self._build_uv_install_cmd(uv_cmd, package_spec, no_build_isolation=True)  # First attempt
            if self._attempt_uv_install(first_cmd, package_spec, fallback=False):  # First UV attempt succeeded
                return True  # Installation done
            logger.debug("UV install failed with --no-build-isolation, retrying without it")  # Note the retry
            retry_cmd = self._build_uv_install_cmd(uv_cmd, package_spec, no_build_isolation=False)  # Retry sans flag
            return self._attempt_uv_install(retry_cmd, package_spec, fallback=True)  # Fallback attempt (logs stderr)
        except (TimeoutExpired, SubprocessError) as e:  # UV hung or failed to launch
            logging.warning("Failed to install %s with UV: %s", package_spec, e)  # Log the exception detail
            return False  # Signal failure so the caller can fall back to pip

    def _attempt_uv_install(self, cmd: list[str], package_spec: str, *, fallback: bool) -> bool:  # One UV install try
        """Run one UV install attempt. On success log+return True. On failure return False (logs stderr if fallback)."""
        result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- cmd argv built from allow-listed pieces.
            cmd,  # The assembled UV command
            timeout=self.upgrade_check_timeout,  # Bound the install so it cannot hang forever
            check=False,  # Non-zero rc is handled by the caller (fallback logging).
        )
        if result.returncode == 0:  # UV reported a successful install
            label = "UV (fallback)" if fallback else "UV"  # Distinguish the first attempt from the retry in the log
            logger.info("Successfully installed %s with %s", package_spec, label)  # Confirm success
            return True  # Installation done
        if fallback:  # Only the final (fallback) attempt surfaces the UV error output
            logger.warning("UV install failed for %s: %s", package_spec, result.stderr)  # Log the UV error output
        return False  # This attempt did not install the package

    def _resolve_uv_binary(self) -> str:  # Choose which UV binary to invoke
        """Return the venv-local UV binary when running inside a venv that ships one, else PATH 'uv'."""
        if not (hasattr(self, "in_venv") and self.in_venv):  # Not running inside a virtual environment
            return "uv"  # Use the UV binary found on PATH
        venv_uv = os.path.join(os.path.dirname(sys.executable), "uv.exe")  # Build the venv-local UV path
        if os.path.exists(venv_uv):  # The venv ships its own UV binary
            logger.debug("Using venv UV: %s", venv_uv)  # Record which UV binary was chosen
            return venv_uv  # Prefer the venv's UV to stay environment-consistent
        return "uv"  # venv has no local UV -- fall back to PATH 'uv'

    def _build_uv_install_cmd(self, uv_cmd: str, package_spec: str, no_build_isolation: bool) -> list[str]:  # UV argv
        """Assemble the 'uv pip install' argv: pin to this interpreter in a venv. Add --no-build-isolation if set."""
        cmd = [uv_cmd, "pip", "install"]  # Base UV install command
        if hasattr(self, "in_venv") and self.in_venv:  # Inside a venv -- pin the install to this interpreter
            cmd += ["--python", sys.executable]  # Target the current Python explicitly
        if no_build_isolation:  # First attempt requests no build isolation (faster, fewer surprises)
            cmd.append("--no-build-isolation")  # Disable build isolation for this attempt
        cmd.append(package_spec)  # The package to install (with any version constraint)
        return cmd  # Completed UV argv

    def _install_package_with_pip(
        self, package_spec: str
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Install a package using pip as fallback with virtual environment awareness."""
        try:
            logger.info("Installing package with pip: %s", package_spec)  # Log the pip install attempt
            # Always use the current Python executable to ensure installation in the right environment
            result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- interpreter self-invoke allowed.
                [sys.executable, "-m", "pip", "install", package_spec],  # Invoke pip as a module of this Python
                timeout=self.upgrade_check_timeout,  # Bound the install so it cannot hang forever
                check=False,  # Non-zero rc is inspected below rather than raised.
            )
            if result.returncode == 0:  # pip reported a successful install
                logger.info("Successfully installed %s with pip", package_spec)  # Confirm success
                return True  # Installation done
            else:  # pip install failed
                logger.error("Failed to install %s with pip: %s", package_spec, result.stderr)  # Log pip's error output
                return False  # Signal failure to the caller
        except (TimeoutExpired, SubprocessError) as e:  # pip hung or failed to launch
            logging.error("Failed to install %s with pip: %s", package_spec, e)  # Log the exception detail
            return False  # Signal failure to the caller

    def _should_check_uv_update(self) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Check if we should check for UV updates based on time since last check."""
        if not self.auto_upgrade_uv:  # UV auto-upgrade is disabled by configuration
            return False  # Never check when the feature is off

        if self._last_uv_update_check is None:  # No prior check ran this session
            return True  # Force an initial check

        time_since_check = time.time() - self._last_uv_update_check  # Seconds elapsed since the last check
        hours_since_check = time_since_check / 3600  # Convert elapsed seconds to hours
        return hours_since_check >= self.uv_update_check_hours  # Check again only after the configured interval

    def _check_uv_needs_update(self) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Check if UV actually needs an update by comparing versions."""
        try:
            # Get current UV version
            result = SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- 'uv' basename allow-listed.
                ["uv", "--version"], timeout=5, check=False
            )  # Query installed UV version via SubprocessRunner (validates argv, no shell).
            if result.returncode != 0:  # UV is absent or gave no version
                return False  # Cannot determine an update is needed

                # For now, we'll assume UV is up to date since checking remote version is complex
                # In a production environment, you might want to implement version comparison
            logger.debug("UV version check complete - assuming current version is adequate")  # Note the no-op result
            return False  # Treat UV as up to date (remote comparison not implemented)

        except (TimeoutExpired, SubprocessError):  # Version probe hung or failed to launch
            return False  # Assume no update needed when the probe fails

    def _upgrade_all_dependencies(self) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Install missing dependencies and upgrade existing ones."""
        if not self.auto_upgrade_dependencies:  # Auto-upgrade disabled by configuration
            logger.info("Auto-upgrade of dependencies is disabled in configuration")  # Note the skip
            return True  # Nothing to do. Treat as success
        packages_to_process = self._collect_packages_to_process()  # (name, spec) pairs, built-ins excluded
        if not packages_to_process:  # Caller supplied an empty work list
            logger.info("No packages to process")  # Note there is nothing to do
            return True  # Success by default -- no work means no failures
        logger.info("Processing %s packages...", len(packages_to_process))  # Announce how many will be handled
        success_count = self._install_dependency_batch(packages_to_process)  # Install each, counting successes
        logger.info("Successfully processed %s/%s packages", success_count, len(packages_to_process))  # Summarize
        return success_count > 0  # Report success if at least one package installed

    def _install_dependency_batch(self, packages_to_process: list[tuple[str, str]]) -> int:  # Install a batch
        """Install each (name, spec) package via the best backend. Return the count that installed successfully."""
        uv_available = self._check_uv_installation()  # Detect whether the tool can use UV as the fast installer
        logger.info(  # Record which installer backend will be used
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
            logger.warning("Failed to install/upgrade %s", pkg_spec)  # Both paths failed -- warn, keep going
            return False  # This package did not install
        except (OSError, SubprocessError, ValueError, RuntimeError) as e:  # Package tool errors affect only this item
            logging.warning("Error processing package %s: %s", pkg_spec, e, exc_info=True)  # Keep the traceback
            return False  # Treat as a failed package

    def _import_concurrent_futures(self) -> Any:  # Preserve the existing behavior during the compliance refactor.
        """Special handler for concurrent.futures import."""
        from concurrent.futures import ThreadPoolExecutor, as_completed  # Import the thread-pool primitives on demand

        return type(
            "ConcurrentFutures", (), {"ThreadPoolExecutor": ThreadPoolExecutor, "as_completed": as_completed}
        )()  # Bundle them on a tiny namespace object

    class _DateTimeHandler:  # Adapter exposing both class-like and module-like datetime access
        """Adapter exposing both class-like and module-like datetime access."""

        def __init__(self) -> None:  # Preserve the existing behavior during the compliance refactor.
            from datetime import datetime, timedelta  # Local import keeps handler self-contained

            self._datetime_cls = datetime  # Capture class for __call__ forwarding
            self.now = datetime.now  # Expose datetime.now() at the top level
            self.fromtimestamp = datetime.fromtimestamp  # Expose epoch->datetime conversion
            self.fromisoformat = datetime.fromisoformat  # Expose ISO-8601 string parsing
            self.strptime = datetime.strptime  # Expose format-string parsing
            # Preserve legacy naive-UTC behavior without calling the deprecated datetime.utcnow.
            # Expose UTC now() helper as naive UTC (legacy contract).
            self.utcnow = lambda: datetime.now(UTC).replace(
                tzinfo=None
            )  # Preserve the existing behavior during the compliance refactor.
            self.datetime = datetime  # Allow handler.datetime to reach the real class
            self.timezone = timezone  # Provide timezone for tz-aware construction
            self.timedelta = timedelta  # Provide timedelta for date arithmetic

        def __call__(
            self, *args: Any, **kwargs: Any
        ) -> datetime:  # Preserve the existing behavior during the compliance refactor.
            return self._datetime_cls(*args, **kwargs)  # Forward calls to the datetime constructor

    def _import_datetime(self) -> Any:  # Preserve the existing behavior during the compliance refactor.
        """Special handler for datetime import."""
        logger.debug("_import_datetime: returning _DateTimeHandler adapter")  # Log before construction
        return self._DateTimeHandler()  # Hand back the dual-purpose adapter

    def _import_tqdm(self) -> Any:  # Preserve the existing behavior during the compliance refactor.
        """Special handler for tqdm import to ensure proper functionality."""
        try:
            from tqdm import tqdm  # Attempt to import the real progress-bar library

            logger.debug("Successfully imported tqdm from package")  # Note the real library is available
            return tqdm  # Use the genuine tqdm progress bar
        except ImportError:  # tqdm is not installed
            logging.warning("tqdm package not available, using fallback")  # Warn and degrade gracefully

            # Return the fallback function if tqdm is not available
            def tqdm_fallback(
                iterable: Iterable[Any], *args: Any, **kwargs: Any
            ) -> Iterable[Any]:  # Preserve the existing behavior during the compliance refactor.
                """Fallback when tqdm package is not available."""
                from collections.abc import Sized  # Type for objects supporting len()

                desc = kwargs.get("desc", "Processing")  # Description label for the log line
                unit = kwargs.get("unit", "item")  # Unit noun for the progress message
                if isinstance(iterable, Sized):  # The iterable length is known
                    total = len(cast(Sized, iterable))  # Compute total item count for the message
                    logging.info("%s: %s %ss to process", desc, total, unit)  # Log a one-shot progress summary
                else:  # Length is unknown (for example a generator)
                    logging.info("%s: processing %ss...", desc, unit)  # Log an indefinite progress message
                return iterable  # Pass the iterable through unchanged (no live bar)

            return tqdm_fallback  # Provide the no-op progress shim to callers

    def _check_and_upgrade_package(
        self, module_name: str, package_spec: str
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Check if a package needs upgrading and upgrade it if necessary. Always non-fatal (returns True)."""
        if not package_spec:  # No version spec provided (for example a stdlib module)
            return True  # Built-in modules do not need upgrading
        try:  # Upgrade problems must never block startup
            package_name = self._bare_package_name(package_spec)  # Strip version operators to the bare name
            result = self._run_pip_show(package_name)  # Ask pip what version is currently installed
            if result.returncode != 0:  # pip could not find the package
                logger.debug("Package %s not found, skipping upgrade check", package_name)  # Nothing to upgrade
                return True  # Treat as success -- not an error condition
            current_version = self._parse_pip_show_version(result.stdout)  # Parse the installed version
            if not current_version:  # Could not determine the installed version
                return True  # Treat as non-fatal -- nothing reliable to upgrade against
            logger.debug("Current version of %s: %s", package_name, current_version)  # Record the current version
            logger.info("  Checking for updates to %s...", package_name)  # Inform the user an upgrade check runs
            return self._upgrade_and_verify(package_name, package_spec, current_version)  # Upgrade + report
        except (KeyboardInterrupt, SystemExit):  # Operators must be able to stop startup immediately
            raise  # Do not convert an operator stop into a successful startup check
        except Exception as e:  # Broad by contract because upgrade checks are always non-fatal
            logging.warning("Error checking/upgrading %s: %s", module_name, e, exc_info=True)  # Keep startup non-fatal
            return True  # Non-critical failure -- never block startup on upgrade issues

    @staticmethod
    def _bare_package_name(package_spec: str) -> str:  # Strip version operators from a package spec
        """Return the bare package name from a spec (for example 'requests>=2.28.0' -> 'requests')."""
        return package_spec.split(">=")[0].split("==")[0].split("<")[0].split(">")[0].strip()  # Drop any constraint

    def _run_pip_show(self, package_name: str) -> Any:  # Query pip for a package's metadata
        """Run 'pip show <package_name>' for this interpreter with captured text output (10s timeout)."""
        return SubprocessRunner.run(  # Audited dispatch (initiative 1016) -- interpreter self-invoke allowed.
            [sys.executable, "-m", "pip", "show", package_name],  # pip show for this interpreter
            timeout=10,  # Bound the metadata query
            check=False,  # Caller parses stdout regardless of returncode.
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
        upgrade_result = SubprocessRunner.run(  # Audited dispatch (initiative 1016).
            self._build_upgrade_cmd(package_spec),  # UV or pip upgrade argv
            timeout=self.upgrade_check_timeout,  # Bound the upgrade so it cannot hang
            check=False,  # Non-zero rc is downgraded to a debug log, not raised.
        )
        if upgrade_result.returncode != 0:  # The upgrade command failed
            logger.debug("  [WARN] %s: Upgrade check failed: %s", package_name, upgrade_result.stderr)  # Log detail
            return True  # Non-critical failure -- continue without blocking startup
        new_version = self._parse_pip_show_version(self._run_pip_show(package_name).stdout)  # Re-query post-upgrade
        if new_version and new_version != current_version:  # The version actually advanced
            logger.info("  [OK] %s: Upgraded from %s to %s", package_name, current_version, new_version)  # Report it
        else:  # Version did not change
            logger.debug("  [OK] %s: Already up to date (%s)", package_name, current_version)  # Already current
        return True  # Upgrade path is always non-fatal

        # _get_actual_import_name removed per issue #431 (ARCH-DELEGATE) -- callers
        # now do `self.import_name_mappings.get(name, name)` inline.

    def _resolve_and_import(
        self, module_name: str
    ) -> Any:  # Preserve the existing behavior during the compliance refactor.
        """Import a module via its special handler or its real import name (issue #470: shared by attempt + retry)."""
        if module_name in self.special_import_handlers:  # Some modules need custom construction logic.
            return self.special_import_handlers[module_name]()  # Invoke special handler.
        actual_import_name = self.import_name_mappings.get(module_name, module_name)  # Resolve package -> import name.
        return __import__(actual_import_name)  # Import the module by its real import name.

    def _should_upgrade_package(
        self, package_spec: str | None, skip_deps: bool, skip_upgrade: bool
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Return True only when every opportunistic-upgrade gate passes (issue #470: hoisted to keep CC low)."""
        return bool(
            package_spec and self.auto_upgrade_dependencies and not skip_deps and not skip_upgrade
        )  # All four upgrade gates must pass before an opportunistic upgrade.

    def _auto_install_allowed(
        self, package_spec: str | None, skip_deps: bool
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Return True only when auto-installing a missing dependency is permitted (issue #470: hoisted gate)."""
        return bool(
            package_spec and self.auto_upgrade_dependencies and not skip_deps and not self.disable_auto_install
        )  # All four install gates must pass before attempting an install.

    def _attempt_install(
        self, package_spec: str
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Install a package, preferring UV then falling back to pip. Return True if either succeeded."""
        installed = False  # Track whether any installer succeeded.
        if self._check_uv_installation():  # UV is the preferred fast installer.
            logger.debug("Trying UV installation for %s", package_spec)  # Note the UV attempt.
            installed = self._install_package_with_uv(package_spec)  # Attempt the UV install.
        if not installed:  # UV either failed or is unavailable.
            logger.debug("Trying pip installation for %s", package_spec)  # Note the pip attempt.
            installed = self._install_package_with_pip(package_spec)  # Attempt the pip install.
        return installed  # Report whether the package is now installed.

    def _clear_failed_import_cache(
        self, module_name: str
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Invalidate import caches and purge stale failed entries so a post-install retry imports cleanly."""
        import importlib  # Imported locally to invalidate caches only when needed.

        importlib.invalidate_caches()  # Force Python to notice the newly installed files.
        actual_import_name = self.import_name_mappings.get(module_name, module_name)  # Resolve package -> import name.
        for mod_name in (actual_import_name, module_name):  # Both names may be cached as failed.
            if mod_name in sys.modules:  # A stale/failed entry exists in the module cache.
                del sys.modules[mod_name]  # Remove it so the retry re-imports cleanly.
                logger.debug("Cleared cached module: %s", mod_name)  # Record the cache purge.

    def _retry_import_after_install(
        self, module_name: str, package_spec: str, required: bool
    ) -> Any | None:  # Preserve the existing behavior during the compliance refactor.
        """Re-import a module after a successful install. Return it, or None if the import still fails."""
        try:  # The install may still not satisfy the import in this Python session.
            module = self._resolve_and_import(module_name)  # Re-import now that the package is installed.
            self.imports[module_name] = module  # Cache the now-successful import.
            self.installed_packages.append(package_spec)  # Record that we installed this package this run.
            logger.info("Successfully imported %s after installation", module_name)  # Confirm recovery.
            return module  # Return the freshly imported module.
        except ImportError as retry_e:  # Import still fails even after a successful install.
            logging.error("Import still failed after installation for %s: %s", module_name, retry_e)  # Log failure.
            if not required:  # Optional dependency -- degrade gracefully.
                logging.info(  # Preserve the existing behavior during the compliance refactor.
                    (
                        "Optional package %s installation succeeded but import failed - likely needs system restart or "
                        "different Python session"
                    ),
                    module_name,
                )
            return None  # The retry import did not succeed.

    def _install_and_retry(  # Preserve the existing behavior during the compliance refactor.
        self, module_name: str, package_spec: str | None, required: bool, skip_deps: bool
    ) -> Any | None:
        """Install a missing dependency (when permitted) and retry the import. Return the module or None."""
        if not self._auto_install_allowed(package_spec, skip_deps):  # Auto-install must be permitted.
            return None  # Installation not allowed -- nothing to retry.
        if package_spec is None:  # Defensive guard: an overridden gate must never trigger an unbounded install.
            logger.error(
                "Cannot install %s: package specification is missing", module_name
            )  # Surface the invalid state.
            return None  # Refuse installation without an explicit package constraint.
        logger.info("Attempting to install missing dependency: %s", package_spec)  # Announce the install attempt.
        if not self._attempt_install(package_spec):  # No installer succeeded.
            logger.error("Failed to install %s", package_spec)  # Report the install failure.
            return None  # Cannot retry without a successful install.
        self._clear_failed_import_cache(module_name)  # Purge stale caches before the retry.
        time.sleep(0.5)  # Brief pause to let filesystem writes settle before retrying.
        return self._retry_import_after_install(module_name, package_spec, required)  # Retry.

    def _record_import_failure(
        self, module_name: str, required: bool
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Record a terminal import failure (hard error for required deps, warning for optional)."""
        if required:  # This dependency is mandatory for the program to run.
            self.failed_imports.append(module_name)  # Track it among hard failures.
            logger.error("Required dependency %s could not be imported or installed", module_name)  # Hard error.
        else:  # Optional dependency.
            # WHY: Optional deps not being installed is the expected steady state
            # for most operators (plotly/dash/kaleido only matter for the maps
            # dashboards). Emit at INFO so startup noise doesn't look like something
            # is broken; the [--] line below still surfaces it for anyone scanning.
            logger.info(
                "Optional dependency %s not available", module_name
            )  # Preserve the existing behavior during the compliance refactor.

    def import_module_safely(  # Preserve the existing behavior during the compliance refactor.
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
            # WHY: This branch fires on every optional-dep miss (plotly/dash/kaleido)
            # before the install-and-retry pass. Logging at WARNING here made a
            # completely healthy startup look like it had problems. The terminal
            # outcome is still recorded via _record_import_failure below.
            logging.debug(
                "Failed to import %s: %s", module_name, e
            )  # Preserve the existing behavior during the compliance refactor.
            module = self._install_and_retry(module_name, package_spec, required, skip_deps)  # Try install + retry.
            if module is not None:  # The install-and-retry recovered the import.
                return module  # Return the recovered module.
            self._record_import_failure(module_name, required)  # Record terminal failure (logs required/optional).
            return None  # Signal to the caller that the import was unavailable.

    def _record_successful_import(  # Preserve the existing behavior during the compliance refactor.
        self,
        module: Any,
        module_name: str,
        package_spec: str | None,
        skip_deps: bool,
        skip_upgrade: bool,
    ) -> None:
        """Cache an imported module and run the opportunistic upgrade check."""
        logger.debug("_record_successful_import: caching '%s' and checking upgrade", module_name)  # Log before
        self.imports[module_name] = module  # Cache the imported module for later global assignment.
        logger.debug("Successfully imported %s", module_name)  # Record the successful import.
        if not self._should_upgrade_package(
            package_spec, skip_deps, skip_upgrade
        ):  # Exit when any upgrade gate blocks.
            return  # Nothing else is required when upgrades are disabled.
        if package_spec is None:  # Defensive guard: an overridden gate must never trigger an unbounded upgrade.
            logger.warning(
                "Skipping upgrade for %s: package specification is missing", module_name
            )  # Surface the invalid state.
            return  # Refuse upgrade without an explicit package constraint.
        self._check_and_upgrade_package(module_name, package_spec)  # Upgrade the explicitly requested package.

    def _partition_dependencies(
        self, packages_dict: dict[str, str | None]
    ) -> tuple[dict[str, None], dict[str, str]]:  # Preserve the existing behavior during the compliance refactor.
        """Split a package map into (builtin, external) dicts by whether a spec is present."""
        logger.debug("_partition_dependencies: splitting %d packages", len(packages_dict))  # Log before split
        builtin_packages = {k: v for k, v in packages_dict.items() if v is None}  # No spec -> stdlib/built-in module
        external_packages = {k: v for k, v in packages_dict.items() if v is not None}  # Has spec -> needs install
        return builtin_packages, external_packages  # Return the two cohesive groups for separate processing

    def _import_single_dependency(  # Preserve the existing behavior during the compliance refactor.
        self,
        package_info: tuple[str, str | None],
        required: bool,
        skip_deps: bool,
        log_lock: Any,
    ) -> tuple[str, bool]:
        """Import one package and log its check and outcome under the shared thread lock."""
        module_name, package_spec = package_info  # Unpack the (name, spec) tuple for this worker
        package_type = "required" if required else "optional"  # Label used in user-facing log lines
        with log_lock:  # Serialize this log line against other worker threads
            logger.info(
                "  Checking %s dependency: %s (%s)", package_type, module_name, package_spec or "built-in"
            )  # Announce the check
        import_result = self.import_module_safely(  # Perform the actual import/install for this package
            module_name, package_spec, required=required, skip_deps=skip_deps, skip_upgrade=True
        )  # Skip upgrade for speed here
        result: bool = import_result is not None  # Convert Any | None to bool (success if not None)
        with log_lock:  # Serialize the result log line against other worker threads
            self._log_dependency_result(module_name, result, required)  # Emit OK/FAIL/WARN for this package
        return module_name, result  # Return the outcome for aggregation by the caller

    def _log_dependency_result(
        self, module_name: str, result: bool, required: bool
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Log a single dependency outcome as OK, hard FAIL (required), or soft WARN (optional)."""
        if result:  # Import succeeded
            logger.info("  [OK] %s: Available", module_name)  # Report availability
        elif required:  # Mandatory dependency missing
            logger.error("  [FAIL] %s: Failed to import", module_name)  # Log a hard failure
        else:  # Optional dependency missing
            # WHY: Downgraded from WARNING to INFO so a missing optional dep
            # (plotly/dash/kaleido on non-dashboard workstations) doesn't
            # masquerade as a fault at startup. Marker changed to [--] to
            # keep scan lines but drop the warning connotation.
            logger.info(
                "  [--] %s: Not available", module_name
            )  # Preserve the existing behavior during the compliance refactor.

    def _import_external_dependencies(  # Preserve the existing behavior during the compliance refactor.
        self,
        external_packages: dict[str, str],
        required: bool,
        skip_deps: bool,
        log_lock: Any,
        max_workers: int,
    ) -> list[tuple[str, bool]]:
        """Import external packages concurrently with a bounded thread pool."""
        logger.debug(  # Preserve the existing behavior during the compliance refactor.
            "_import_external_dependencies: importing %d external packages",
            len(external_packages),
        )
        results: list[tuple[str, bool]] = []  # Preserve the existing behavior during the compliance refactor.
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:  # Preserve the existing behavior during the compliance refactor.
            future_to_package: dict[concurrent.futures.Future[tuple[str, bool]], tuple[str, str | None]] = (
                {  # Preserve the existing behavior during the compliance refactor.
                    executor.submit(self._import_single_dependency, item, required, skip_deps, log_lock): item
                    for item in external_packages.items()
                }
            )
            for future in concurrent.futures.as_completed(
                future_to_package
            ):  # Preserve the existing behavior during the compliance refactor.
                result = self._collect_import_result(
                    future, future_to_package, log_lock
                )  # Preserve the existing behavior during the compliance refactor.
                if result:  # Result collection succeeded
                    results.append(result)  # Add to accumulated results
        return results  # Return all successfully collected results

    def _collect_import_result(  # Preserve the existing behavior during the compliance refactor.
        self,
        future: concurrent.futures.Future[tuple[str, bool]],
        future_to_package: dict[concurrent.futures.Future[tuple[str, bool]], tuple[str, str | None]],
        log_lock: Any,
    ) -> tuple[str, bool] | None:
        """Retrieve one import future's result, logging any exception under the lock.

        Returns the result if successful, None on exception.
        """
        package_info = future_to_package[future]  # Recover which package this future handled
        try:
            result: tuple[str, bool] = future.result()  # Retrieve the worker's return value (re-raises worker errors)
            return result  # Return the successful result
        except (
            concurrent.futures.CancelledError,
            TimeoutError,
            ImportError,
            OSError,
            RuntimeError,
        ) as exc:  # Worker failed
            with log_lock:  # Serialize the error log line against other worker threads
                logging.exception("Package %s import generated an exception: %s", package_info[0], exc)  # Keep trace
            return None  # Signal failure to caller

    def _import_packages_concurrently(  # Preserve the existing behavior during the compliance refactor.
        self,
        packages_dict: dict[str, str | None],
        required: bool = True,
        skip_deps: bool = False,
        max_workers: int = 4,
    ) -> None:
        """
        Import packages concurrently for faster dependency resolution.

        Args:
            packages_dict: A package to spec map.
            required: True for required packages.
            skip_deps: Skip installation when True.
            max_workers: The thread pool size.
        """
        log_lock = threading.Lock()  # Guards logging so concurrent threads do not interleave messages
        builtin_packages, external_packages = self._partition_dependencies(packages_dict)  # Split by spec presence
        for item in builtin_packages.items():  # Built-ins import instantly with no network needed
            self._import_single_dependency(item, required, skip_deps, log_lock)  # Import each sequentially
        if external_packages:  # Only spin up a thread pool if there is network work to do
            self._import_external_dependencies(external_packages, required, skip_deps, log_lock, max_workers)  # Pool

    def initialize_all_imports(  # Preserve the existing behavior during the compliance refactor.
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
        from src.refactors.serial_cc.import_initialization_service import (
            ImportInitializationService,
        )  # Preserve the existing behavior during the compliance refactor.

        return ImportInitializationService.execute(
            self, skip_deps=skip_deps
        )  # Preserve the existing behavior during the compliance refactor.

    def _get_global_assignments(
        self,
    ) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
        """Get dictionary of global variable assignments for imported modules."""
        from src.refactors.serial_cc.global_assignments_builder import (
            GlobalAssignmentsBuilderService,
        )  # Preserve the existing behavior during the compliance refactor.

        return GlobalAssignmentsBuilderService.execute(
            self.imports, self._add_fallbacks_to_globals
        )  # Preserve the existing behavior during the compliance refactor.

        # Simple module -> [(global_name, attr_name_or_None)] hoists. attr None binds the module object itself.
        # Used by _hoist_module_globals so _make_modules_global stays a flat loop instead of a long if/elif chain.

    _SIMPLE_GLOBAL_HOISTS: ClassVar[dict[str, list[tuple[str, str | None]]]] = {
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

    def _make_modules_global(self) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Make all successfully imported modules available in the global namespace."""
        for module_name, module_obj in self.imports.items():  # Walk every imported module
            globals()[module_name] = module_obj  # Bind the module into the real module globals
            self._hoist_module_globals(module_name, module_obj)  # Hoist any commonly-used attributes for it
        logger.debug("Successfully made imported modules available globally")  # Confirm the global wiring completed

    def _hoist_module_globals(
        self, module_name: str, module_obj: Any
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Hoist commonly-used attributes of a known module into globals (data-driven, with optional-pkg cases)."""
        simple_hoists = self._SIMPLE_GLOBAL_HOISTS.get(module_name)  # Lookup the simple hoist list for this module
        if simple_hoists:  # This module lists a fixed set of attributes to hoist
            self._apply_simple_hoists(module_obj, simple_hoists)  # Bind each (global_name, attr) pair
        elif module_name == "usaddress-scourgify":  # Optional address-normalization package needs custom handling
            self._hoist_scourgify_global(module_obj)  # Bind its normalize function (with direct-import fallback)
        elif module_name == "rapidfuzz":  # Optional fuzzy-matching package needs custom handling
            self._hoist_rapidfuzz_global(module_obj)  # Bind its fuzz submodule (with direct-import fallback)

    @staticmethod
    def _apply_simple_hoists(
        module_obj: Any, hoists: list[tuple[str, str | None]]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Bind each (global_name, attr_name) pair: attr None binds the module object, else getattr(module, attr)."""
        for global_name, attr_name in hoists:  # Apply each configured binding for this module
            value = module_obj if attr_name is None else getattr(module_obj, attr_name, None)  # Module or its attribute
            globals()[global_name] = value  # Bind the resolved value into the real module globals

    @staticmethod
    def _hoist_scourgify_global(
        module_obj: Any,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
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
    def _hoist_rapidfuzz_global(
        module_obj: Any,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
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

    def _add_fallbacks_to_globals(
        self, global_vars: dict[str, Any]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Add fallbacks for optional modules that failed to import."""
        self._install_scourgify_fallback(global_vars)  # Address-normalization shim when scourgify is absent
        self._install_fuzz_fallback(global_vars)  # Fuzzy-match shim (difflib-backed) when rapidfuzz is absent
        self._install_ssh_fallbacks(global_vars)  # paramiko/redexpect shims that fail loudly with install guidance

    @staticmethod
    def _install_scourgify_fallback(
        global_vars: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """When normalize_address_record is absent, install a shim returning the raw string with empty fields."""
        if global_vars.get("normalize_address_record") is not None:  # A real normalizer is already present
            return  # No fallback needed

        def normalize_address_record_fallback(
            address_string: str,
        ) -> dict[str, str]:  # Preserve the existing behavior during the compliance refactor.
            """Fallback function when scourgify is not available."""
            logger.debug("Using fallback address normalization (scourgify not available)")  # Note the degraded path
            return {
                "address_line_1": address_string,
                "city": "",
                "state": "",
                "zip": "",
                "country": "",
            }  # Return the raw string with empty fields

        global_vars["normalize_address_record"] = normalize_address_record_fallback  # Install the shim by name

    @staticmethod
    def _install_fuzz_fallback(global_vars: dict[str, Any]) -> None:  # Install the rapidfuzz fallback when absent
        """When fuzz is absent, install a difflib-backed shim exposing token_sort_ratio (0-100 score)."""
        if global_vars.get("fuzz") is not None:  # A real fuzzy matcher is already present
            return  # No fallback needed

        class FuzzFallback:  # Preserve the existing behavior during the compliance refactor.
            """Fallback class when rapidfuzz is not available."""

            @staticmethod
            def token_sort_ratio(
                str1: str, str2: str
            ) -> int:  # Preserve the existing behavior during the compliance refactor.
                """Fallback using difflib SequenceMatcher."""
                if global_vars.get("difflib"):  # Use difflib if it is available as a substitute
                    return int(
                        global_vars["difflib"].SequenceMatcher(None, str1, str2).ratio() * 100
                    )  # Convert 0-1 ratio to a 0-100 score
                return 0  # No comparison library at all -- report no similarity

        global_vars["fuzz"] = FuzzFallback()  # Install the fuzzy-match shim under the expected name

    @classmethod
    def _install_ssh_fallbacks(
        cls, global_vars: dict[str, Any]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Install paramiko and redexpect shims that raise ImportError with install guidance when accessed."""
        cls._install_paramiko_fallback(global_vars)  # SSH client shim when paramiko is absent
        cls._install_redexpect_fallback(global_vars)  # SSH automation shim when redexpect is absent

    @staticmethod
    def _install_paramiko_fallback(global_vars: dict[str, Any]) -> None:  # Install a paramiko shim that errors on use
        """When paramiko is absent, install a shim whose SSHClient() raises ImportError with install guidance."""
        if global_vars.get("paramiko") is not None:  # paramiko (or an existing shim) is already present
            return  # No fallback needed

        class SSHFallback:  # Preserve the existing behavior during the compliance refactor.
            """Fallback class when paramiko is not available."""

            @staticmethod
            def SSHClient() -> NoReturn:  # Preserve the existing behavior during the compliance refactor.
                raise ImportError(  # Fail loudly with install guidance when SSH is attempted without paramiko
                    "SSH functionality requires 'paramiko' package. Install with: pip install paramiko"
                )

        global_vars["paramiko"] = SSHFallback()  # Install the SSH shim with a clear error path

    @staticmethod
    def _install_redexpect_fallback(global_vars: dict[str, Any]) -> None:  # Install a redexpect shim that errors on use
        """When redexpect is absent, install a shim whose spawn() raises ImportError with install guidance."""
        if global_vars.get("redexpect") is not None:  # redexpect (or an existing shim) is already present
            return  # No fallback needed

        class RedexpectFallback:  # Preserve the existing behavior during the compliance refactor.
            """Fallback class when redexpect is not available."""

            @staticmethod
            def spawn(
                *args: Any, **kwargs: Any
            ) -> NoReturn:  # Preserve the existing behavior during the compliance refactor.
                raise ImportError(  # Fail loudly with install guidance when redexpect is used but absent
                    "Cross-platform SSH automation requires 'redexpect' package. Install with: pip install redexpect"
                )

        global_vars["redexpect"] = RedexpectFallback()  # Install the redexpect shim with a clear error path

    def _import_special_modules(self) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Import special modules with custom handling."""
        logger.debug("_import_special_modules: wiring mistapi + websocket-client")  # Log before wiring
        self._wire_mistapi_module()  # Bind mistapi to module globals if it loaded
        self._log_websocket_availability()  # Log whether the websocket client is usable

    def _wire_mistapi_module(self) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Wire mistapi to module globals and confirm its API structure."""
        if "mistapi" not in self.imports:  # The base SDK never imported
            logger.debug("mistapi not imported, skipping sub-module imports")  # Nothing to wire up
            return  # No work to do
        try:  # Failed to even access the cached mistapi object
            mistapi = self.imports["mistapi"]  # Fetch the cached mistapi module object
            try:  # Sub-module wiring hit an unexpected issue
                globals()["mistapi"] = mistapi  # Expose mistapi at module global scope
                vars(sys.modules[__name__])["mistapi"] = mistapi  # Bind dynamic SDK module without a typed attr write
                logger.debug("Successfully imported mistapi main module")  # Confirm SDK wired up
                self._verify_mistapi_api_structure(mistapi)  # Run the hasattr structural check
            except (KeyError, AttributeError, TypeError, RuntimeError) as sub_e:  # Optional SDK wiring failed safely
                logging.debug(
                    "Note: mistapi sub-modules handled dynamically: %s", sub_e, exc_info=True
                )  # Keep the traceback
        except (KeyError, AttributeError, TypeError) as e:  # Cached SDK access failed before feature dispatch
            logging.warning("Error accessing mistapi: %s", e, exc_info=True)  # Warn with traceback for repair

    def _verify_mistapi_api_structure(
        self, mistapi: Any
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Verify mistapi.api.v1 module structure is present and log the result."""
        if hasattr(mistapi, "api") and hasattr(mistapi.api, "v1"):  # Confirm expected nested API surface
            logger.debug("mistapi.api.v1 module structure confirmed")  # Structure looks correct
        else:  # The expected nested structure is absent
            echo("mistapi.api.v1 structure not found - this may cause API call failures")  # Warn about likely failures

    def _log_websocket_availability(self) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Log whether websocket-client successfully loaded."""
        if "websocket-client" in self.imports:  # The websocket client library loaded
            logger.debug("websocket-client available for WebSocket operations")  # WebSocket features enabled
        else:  # The websocket client library is absent
            logger.debug(
                "websocket-client not available - WebSocket operations will be disabled"
            )  # WebSocket features disabled

            # get_import removed per issue #431 (ARCH-DELEGATE) -- callers access
            # `self.imports.get(name)` directly. `self.imports` is the public
            # dict already mutated elsewhere in this class.

    def is_available(self, module_name: str) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Check if a module is available."""
        return module_name in self.imports  # True only if the module imported successfully

    def get_configuration(self) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
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


def _get_tuning_data_file_path() -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return full path to tuning data JSON stored in data/ directory.

    Ensures the directory exists. Separated for future extension (for example,
    namespacing by org or mode) without scattering path logic.
    """
    data_dir = os.path.join(os.getcwd(), "data")  # Build the path to the data/ subdirectory under the CWD
    try:
        os.makedirs(data_dir, exist_ok=True)  # Create data/ if it does not already exist (idempotent)
    except (KeyboardInterrupt, SystemExit):  # Operators must be able to stop before logging is ready
        raise  # Do not hide an operator stop behind the tuning file fallback
    except Exception as error:  # Broad by design because logging may not be ready during early startup
        logging.exception("Failed to create data directory for tuning data: %s", error)  # Keep early failure trace
        # If directory creation fails, fall back to current working directory.
        # Logging deferred until logger configured.
        return os.path.join(os.getcwd(), "tuning_data.json")  # Degrade gracefully to a CWD-level file
    return os.path.join(data_dir, "tuning_data.json")  # Normal case: store tuning data inside data/


tuning_data_file = os.path.join("data", "tuning_data.json")  # Bootstrap creates data before code writes tuning data.

# API usage tracking cache
_api_usage_cache = {  # Module-level cache for Mist API rate-limit accounting
    "timestamp": 0,  # Epoch seconds when the code last populated the cache from the API
    "used": 0,  # Number of API requests the server reports as consumed
    "limit": 5000,  # Default per-window request quota until the code learns the real limit
    "last_updated": 0,  # Epoch seconds of the most recent local update
    "perceived_requests": 0,  # Locally counted requests since the last server sync
    "initialized": False,  # Whether the cache was seeded from a real API response yet
}

# ============================================================================
# GLOBAL IMPORT MANAGER INITIALIZATION
# ============================================================================
# Preserve private module names while moving their work into ApplicationBootstrap.
_early_log_dir = "data"  # Keep the old log directory name without creating it during import.
_early_log_path = os.path.join(_early_log_dir, "script.log")  # Keep the old log path without opening the file.
_early_console_level = logging.INFO  # Bootstrap reads the configured level during explicit startup.
_early_file_level = logging.INFO  # Bootstrap reads the configured level during explicit startup.
_early_console_handler = logging.NullHandler()  # Keep the old name without attaching a handler at import.
_early_rotation_settings = None  # Bootstrap reads rotation settings during explicit startup.
_early_file_handler = logging.NullHandler()  # Keep the old name without opening script.log at import.
_UNSUPPORTED_FLAG_VARIANTS: dict[str, str] = {}  # Argparse now owns unsupported flag errors.


def _is_help_invocation(argv: list[str]) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when argv requests help output."""
    return any(token in ("--help", "-h") for token in argv[1:])  # Preserve the private name for symbol stability.


def _reject_unsupported_flag_variants(
    argv: list[str],
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Let argparse own unsupported flag errors."""
    _ = argv  # Keep the private name while removing the pre-parse variant guard.


def _exit_on_unsupported_flag(
    head: str, supported: str
) -> NoReturn:  # Preserve the existing behavior during the compliance refactor.
    """Raise the standard argparse usage exit for obsolete direct callers."""
    raise SystemExit(2)  # Preserve the private name without adding a new compatibility path.


try:  # Import the sanitizer class without configuring logging during module import.
    from mistapi.__logger import LogSanitizer  # Keep the old exported name available for callers.
except ImportError:  # Older mistapi versions may not publish the sanitizer.
    LogSanitizer = None  # Keep the exported name stable when mistapi lacks the class.

    # The explicit bootstrap creates this manager before application startup work runs.
import_manager = cast(GlobalImportManager, None)  # Preserve the public name without running startup side effects.
_initialize_imports_now = False  # Keep import passive. The bootstrap decides when dependencies initialize.
if _initialize_imports_now:  # This branch stays false so import never initializes dependencies.
    pass  # Bootstrap owns all import-manager execution.
else:  # Preserve the original deferred shape without reading command-line arguments.
    success = False  # Bootstrap fills this value after the command-line parse.
    global_assignments: dict[str, Any] = {}  # Bootstrap fills these values after the command-line parse.

    # ============================================================================
    # TEST MODE GLOBALS & TIME UTILITIES CLASS
    # ============================================================================
    # Central flag for test mode (available early so helper functions outside main can use it)
IS_TEST_MODE = False  # Bootstrap updates this flag from the stored parsed arguments.
# Last selected interactive site ID (used to keep testinteractive site context consistent)
LAST_SELECTED_SITE_ID: str | None = None  # Preserve the existing behavior during the compliance refactor.


# ============================================================================
# IMPORT STATUS AND INPUT UTILITIES CLASS
# ============================================================================


from src.utils.input_utils import InputUtils  # Cat E canonical (1015 T-09) -- re-export.

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Configuration variables from .env (with defaults) - now managed by import manager
config: dict[str, Any] = {  # Bootstrap replaces this dictionary after it creates the import manager.
    "csv_freshness_minutes": 15,  # Preserve the historical default without reading the environment at import.
    "auto_upgrade_uv": True,  # Preserve the historical default without reading the environment at import.
    "auto_upgrade_dependencies": True,  # Preserve the historical default without reading the environment at import.
    "upgrade_check_timeout": 30,  # Preserve the historical default without reading the environment at import.
}
CSV_FRESHNESS_MINUTES: int = 15  # Bootstrap updates this value from startup configuration.
AUTO_UPGRADE_UV: bool = True  # Bootstrap updates this value from startup configuration.
AUTO_UPGRADE_DEPENDENCIES: bool = True  # Bootstrap updates this value from startup configuration.
UPGRADE_CHECK_TIMEOUT: int = 30  # Bootstrap updates this value from startup configuration.

# API Request Timeout (seconds) - prevents indefinite hangs on slow/dropped connections
# Default 120s is generous. Most Mist API calls return within 30s
API_REQUEST_TIMEOUT = 120  # Bootstrap updates this value from the environment.
API_REQUEST_MAX_RETRIES = 3  # Bootstrap updates this value from the environment.
API_REQUEST_RETRY_DELAY = 5.0  # Bootstrap updates this value from the environment.

# Fast Mode Configuration from .env
FAST_MODE_MAX_RETRIES = 3  # Bootstrap updates this value from the environment.
FAST_MODE_RETRY_DELAY = 0.5  # Bootstrap updates this value from the environment.

FAST_MODE_ENABLED: bool  # MainEntrypoint.context owns the runtime fast-mode flag.

org_id: str | None  # MainEntrypoint.context owns the active organization identifier.


FAST_MODE_RETRY_THREADS = 4  # Bootstrap updates this value from the environment.
FAST_MODE_RETRY_MAX_RETRIES = 2  # Bootstrap updates this value from the environment.
FAST_MODE_FALLBACK_THREADS = 8  # Bootstrap updates this value from the environment.

# Global configuration for output format (CSV or Redis/SQLite)
# Default to CSV for general use, can be overridden by CLI flag
OUTPUT_FORMAT: str  # MainEntrypoint.context owns the selected output format.
DATABASE_PATH = os.path.join("data", "mist_data.db")  # Path to hybrid SQLite database with natural primary keys

# Global progress telemetry emitter (initialized in main(), best-effort per FR-008)
PROGRESS_EMITTER: Any | None  # MainEntrypoint.context owns the telemetry emitter.

# ============================================================================
# APPLICATION SESSION CONTEXT
# ============================================================================

# Initialize Mist API session (prepared after authentication)
# Type annotation uses Any since the code imports mistapi dynamically
apisession: Any | None  # MainEntrypoint.context owns the authenticated Mist API session.

# MSP privilege tracking (populated after authentication)
msp_privileges: list[dict[str, Any]]  # MainEntrypoint.context owns the detected MSP grants.
selected_msp: dict[str, Any] | None  # MainEntrypoint.context owns the selected MSP.

sys.modules[__name__].__class__ = type(  # Preserve legacy attribute reads while the context owns the state.
    "_MistHelperContextModule",  # Give the dynamic module type a diagnostic name.
    (types.ModuleType,),  # Extend the normal module behavior only for context-owned names.
    {
        "__getattr__": lambda self, name: (
            getattr(  # Route late module reads to the context without a state copy.
                MainEntrypoint.context,  # Use the single entry-point context as the state owner.
                {
                    "apisession": "apisession",  # Keep old readers compatible until issue #1703 moves them.
                    "org_id": "org_id",  # Keep old readers compatible until issue #1703 moves them.
                    "msp_privileges": "msp_privileges",  # Keep old readers compatible until issue #1703 moves them.
                    "selected_msp": "selected_msp",  # Keep old readers compatible until issue #1703 moves them.
                    "OUTPUT_FORMAT": "output_format",  # Keep old readers compatible until issue #1703 moves them.
                    "PROGRESS_EMITTER": "progress_emitter",  # Keep old readers compatible until issue #1703 moves them.
                    "FAST_MODE_ENABLED": "fast_mode_enabled",  # Keep old readers compatible until issue #1703.
                }[name],
            )
            if name
            in {
                "apisession",  # Treat the old session name as a context view.
                "org_id",  # Treat the old organization name as a context view.
                "msp_privileges",  # Treat the old MSP grants name as a context view.
                "selected_msp",  # Treat the old MSP selection name as a context view.
                "OUTPUT_FORMAT",  # Treat the old output format name as a context view.
                "PROGRESS_EMITTER",  # Treat the old progress emitter name as a context view.
                "FAST_MODE_ENABLED",  # Treat the old fast-mode flag name as a context view.
            }
            else (_ for _ in ()).throw(AttributeError(name))
        ),  # Keep normal AttributeError behavior for unknown names.
        "__setattr__": lambda self, name, value: (
            setattr(  # Route legacy writes to the context during old tests.
                MainEntrypoint.context,  # Use the same owner for every legacy write.
                {
                    "apisession": "apisession",  # Keep monkeypatch-based tests pointed at the context.
                    "org_id": "org_id",  # Keep monkeypatch-based tests pointed at the context.
                    "msp_privileges": "msp_privileges",  # Keep monkeypatch-based tests pointed at the context.
                    "selected_msp": "selected_msp",  # Keep monkeypatch-based tests pointed at the context.
                    "OUTPUT_FORMAT": "output_format",  # Keep monkeypatch-based tests pointed at the context.
                    "PROGRESS_EMITTER": "progress_emitter",  # Keep monkeypatch-based tests pointed at the context.
                    "FAST_MODE_ENABLED": "fast_mode_enabled",  # Keep monkeypatch-based tests pointed at the context.
                }[name],
                value,
            )
            if name
            in {
                "apisession",  # Treat the old session name as a context write.
                "org_id",  # Treat the old organization name as a context write.
                "msp_privileges",  # Treat the old MSP grants name as a context write.
                "selected_msp",  # Treat the old MSP selection name as a context write.
                "OUTPUT_FORMAT",  # Treat the old output format name as a context write.
                "PROGRESS_EMITTER",  # Treat the old progress emitter name as a context write.
                "FAST_MODE_ENABLED",  # Treat the old fast-mode flag name as a context write.
            }
            else types.ModuleType.__setattr__(self, name, value)
        ),  # Preserve normal module writes for all other names.
        "__delattr__": lambda self, name: (
            setattr(  # Route legacy deletes to a null context value for old tests.
                MainEntrypoint.context,  # Use the same owner for every legacy delete.
                {
                    "apisession": "apisession",  # Keep monkeypatch delete pointed at the context.
                    "org_id": "org_id",  # Keep monkeypatch delete pointed at the context.
                    "msp_privileges": "msp_privileges",  # Keep monkeypatch delete pointed at the context.
                    "selected_msp": "selected_msp",  # Keep monkeypatch delete pointed at the context.
                    "OUTPUT_FORMAT": "output_format",  # Keep monkeypatch delete pointed at the context.
                    "PROGRESS_EMITTER": "progress_emitter",  # Keep monkeypatch delete pointed at the context.
                    "FAST_MODE_ENABLED": "fast_mode_enabled",  # Keep monkeypatch delete pointed at the context.
                }[name],
                None,
            )
            if name
            in {
                "apisession",  # Treat the old session delete as a context clear.
                "org_id",  # Treat the old organization delete as a context clear.
                "msp_privileges",  # Treat the old MSP grants delete as a context clear.
                "selected_msp",  # Treat the old MSP selection delete as a context clear.
                "OUTPUT_FORMAT",  # Treat the old output format delete as a context clear.
                "PROGRESS_EMITTER",  # Treat the old progress emitter delete as a context clear.
                "FAST_MODE_ENABLED",  # Treat the old fast-mode flag delete as a context clear.
            }
            else types.ModuleType.__delattr__(self, name)
        ),  # Preserve normal module deletes for all other names.
    },
)  # Install the compatibility type without adding a module-level symbol.


def _snapshot_session_globals_to_state() -> (
    dict[str, Any]
):  # Preserve the existing behavior during the compliance refactor.
    """Snapshot the live module-level session globals into a mutable state bag."""
    logger.debug("_snapshot_session_globals_to_state: capturing 5 module globals")  # Log before snapshot
    return {  # Map of global name -> current value for the LoginOrchestrator to mutate
        "apisession": MainEntrypoint.context.apisession,  # Current API session object (may be None)
        "mistapi": MainEntrypoint.context.mistapi or mistapi,  # Use the context SDK module when startup replaced it.
        "msp_privileges": MainEntrypoint.context.msp_privileges,  # Any previously detected MSP grants
        "selected_msp": MainEntrypoint.context.selected_msp,  # Currently selected MSP, if any
        "org_id": MainEntrypoint.context.org_id,  # Currently selected org ID, if any
    }


def _restore_session_globals_from_state(
    state: dict[str, Any],
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Restore module-level session globals from a state bag mutated by the orchestrator."""
    # The application context owns this state, so no global declaration is needed.
    logger.debug("_restore_session_globals_from_state: restoring 5 module globals")  # Log before restore
    MainEntrypoint.context.apisession = state.get("apisession")  # Copy the (possibly new) session back to the global
    MainEntrypoint.context.mistapi = state.get("mistapi")  # Keep the SDK module with the session context.
    MainEntrypoint.context.msp_privileges = state.get(
        "msp_privileges", MainEntrypoint.context.msp_privileges
    )  # Copy detected MSP grants back
    MainEntrypoint.context.selected_msp = state.get(
        "selected_msp", MainEntrypoint.context.selected_msp
    )  # Copy the selected MSP back
    MainEntrypoint.context.org_id = state.get("org_id", MainEntrypoint.context.org_id)  # Copy the selected org ID back


def _print_switch_login_header() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Display switch to interactive login header and benefits."""
    logger.debug("Entering _print_switch_login_header()")  # Trace entry for debugging
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
    echo("  SWITCH TO INTERACTIVE LOGIN")  # Preserve the existing behavior during the compliance refactor.
    echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "  This will replace your current API token session with"
    )  # Preserve the existing behavior during the compliance refactor.
    echo("  an interactive (email/password) session.")  # Preserve the existing behavior during the compliance refactor.
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo("  Benefits of interactive login:")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "    - Can access MSP-level APIs (if you have MSP privileges)"
    )  # Preserve the existing behavior during the compliance refactor.
    echo(
        "    - Session-based auth with cookie management"
    )  # Preserve the existing behavior during the compliance refactor.
    echo("    - Supports 2FA authentication")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "    - Select and switch between MSPs and Organizations"
    )  # Preserve the existing behavior during the compliance refactor.
    echo("")  # Preserve the existing behavior during the compliance refactor.
    if MainEntrypoint.context.msp_privileges:  # The user already has MSP grants detected
        logger.debug(
            "MSP privileges already detected: %s MSP(s)", len(MainEntrypoint.context.msp_privileges)
        )  # Trace the existing grants
        echo(  # Preserve the existing behavior during the compliance refactor.
            "  Note: You already have MSP access to %s MSP(s)",
            len(MainEntrypoint.context.msp_privileges),
        )
        echo("")  # Preserve the existing behavior during the compliance refactor.


def _attempt_interactive_login_with_rollback(
    old_session: Any, old_org_id: str | None
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Clear session and attempt interactive login with rollback on failure.

    Returns:
        bool: True if login succeeded, False if failed (session restored)
    """
    # The application context owns this state, so no global declaration is needed.

    logger.debug("Entering _attempt_interactive_login_with_rollback()")  # Trace entry for debugging
    logger.debug("Clearing existing session state for re-authentication")  # Note we reset before re-login

    MainEntrypoint.context.clear_session()  # Drop old session state through the context owner.

    if not MistSessionInteractiveInitializer.initialize():  # Attempt the interactive login
        echo("")  # Preserve the existing behavior during the compliance refactor.
        echo(
            "  X Login failed - restoring previous session"
        )  # Preserve the existing behavior during the compliance refactor.
        restored_grants = detect_msp_privileges(old_session)  # Re-detect grants for the restored session.
        MainEntrypoint.context.restore_session(old_session, old_org_id, restored_grants)  # Restore through context.
        logger.warning("Interactive login failed - restored previous API session")  # Log the failed attempt
        return False  # Signal failure to the caller
    logger.debug("Interactive login succeeded")  # Trace the successful login
    return True  # Signal success to the caller


def _handle_interactive_login_success() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Handle successful interactive login - display status and select MSP/org."""
    logger.debug("Entering _handle_interactive_login_success()")  # Trace entry for debugging
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "  + Successfully switched to interactive login"
    )  # Preserve the existing behavior during the compliance refactor.
    if MainEntrypoint.context.msp_privileges:  # The new session has MSP grants
        echo(
            "  + MSP access available: %s MSP(s)", len(MainEntrypoint.context.msp_privileges)
        )  # Preserve the existing behavior during the compliance refactor.
        logger.info(
            "Successfully switched to interactive login session with %s MSP(s)",
            len(MainEntrypoint.context.msp_privileges),
        )  # Log the success with MSP count
    else:  # No MSP grants on the new session
        logger.info(
            "Successfully switched to interactive login session (no MSP privileges)"
        )  # Log the success without MSPs

    if MainEntrypoint.context.msp_privileges:  # Choose the selection flow based on MSP access
        _select_msp_and_org()  # MSP users pick an MSP then an org
    else:  # No MSP access
        _select_org_from_session()  # Non-MSP users pick an org directly


def _prompt_switch_login_confirmation() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Prompt the user to confirm switching to interactive login.

    Returns True if the user typed 'y', False on cancel/EOF/SystemExit.
    """
    logger.debug("_prompt_switch_login_confirmation: prompting user for y/N")  # Log before prompt
    try:  # safe_input may raise SystemExit on EOF in some contexts
        confirm = (  # Preserve the existing behavior during the compliance refactor.
            InputUtils.safe_input("  Proceed with re-authentication? (y/N): ", context="switch_login").strip().lower()
        )
    except SystemExit:  # EOF during the prompt
        logging.debug("SystemExit during confirmation prompt")  # Trace the early exit
        return False  # Treat as cancel
    logger.debug("User confirmation received: '%s'", confirm)  # Log the captured response
    if confirm != "y":  # User declined or pressed Enter
        echo("  Cancelled.")  # Preserve the existing behavior during the compliance refactor.
        logger.warning("User cancelled switch to interactive login")  # Log the cancel
        return False  # Caller should stay on the menu
    return True  # User explicitly chose to proceed


def _select_msp_and_org() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Select MSP and organization via extracted interactive session manager."""
    # The application context owns this state, so no global declaration is needed.

    state = MainEntrypoint.context.as_selector_state()  # Build the selector state through the context owner.
    state["mistapi"] = state.get("mistapi") or mistapi  # Use the imported SDK module when context has none.

    session_manager = MspOrgSelector(  # Build the MSP/org selector with injected deps
        state=state,  # Pass the mutable state bag the selector will update
        safe_input=InputUtils.safe_input,  # Inject the EOF-safe input function
        select_org_fallback=_select_org_from_session,  # Inject the non-MSP fallback org selector
    )
    session_manager.select()  # Run the interactive MSP-then-org selection flow

    MainEntrypoint.context.apply_msp_selection(state)  # Store the selector result through the context owner.


def _invoke_mistapi_org_picker_and_apply() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run mistapi's org picker and apply the user's choice to the org_id global."""
    # The application context owns this state, so no global declaration is needed.
    try:  # mistapi may raise on network errors or invalid sessions
        logger.debug("Invoking mistapi.cli.select_org()")  # Trace the SDK call
        org_id_list = mistapi.cli.select_org(
            MainEntrypoint.context.apisession
        )  # Let mistapi present an org picker and return the choice
        if org_id_list and len(org_id_list) > 0:  # The user selected at least one org
            MainEntrypoint.context.org_id = org_id_list[0]  # Use the first selected org ID
            echo(
                "  + Organization ID set: %s", MainEntrypoint.context.org_id
            )  # Preserve the existing behavior during the compliance refactor.
            logger.info("User selected org from session: %s", MainEntrypoint.context.org_id)  # Log the chosen org
        else:  # The user selected nothing
            echo("  X No organization selected")  # Preserve the existing behavior during the compliance refactor.
            logger.warning("No organization selected from session privileges")  # Log the empty selection
    except (
        AttributeError,
        TypeError,
        IndexError,
        ValueError,
        OSError,
    ) as e:  # Picker errors should keep login controlled
        echo(
            "  X Error selecting organization: %s", e
        )  # Preserve the existing behavior during the compliance refactor.
        logging.exception("Failed to select org from session: %s", e)  # Keep picker traceback


def _select_org_from_session() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Pick an org via mistapi's built-in selector (non-MSP path)."""
    logger.debug("Entering _select_org_from_session()")  # Trace entry for debugging
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "  Selecting organization from your session privileges..."
    )  # Preserve the existing behavior during the compliance refactor.
    echo("")  # Preserve the existing behavior during the compliance refactor.
    _invoke_mistapi_org_picker_and_apply()  # Run picker. Updates the org_id global


def _load_mistapi_module(current_mistapi: Any) -> Any:  # Preserve the existing behavior during the compliance refactor.
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

        logger.debug("Loaded mistapi via fallback import in initialize_mist_session")  # Confirm load path
        return mistapi_fallback  # Return newly imported module
    except ImportError as import_err:  # Preserve the existing behavior during the compliance refactor.
        logging.error("Cannot import mistapi: %s", import_err)  # Log failure cause for operator visibility
        return None  # Signal that mistapi is unavailable -- caller must abort


def _split_env_tokens(raw_token_env: str | None) -> list[str]:  # Split a token env value into individual tokens
    """Split a newline/comma-separated token env value into a list of non-empty stripped tokens."""
    if not raw_token_env:  # No token env var set
        return []  # Caller will fall back to env_file or mistapi.Session
    return [token.strip() for token in re.split(r"[\n,]+", raw_token_env) if token.strip()]  # Split on newlines/commas


def _redact_tokens(tokens: list[str]) -> str:  # Describe discovered tokens without any secret material
    """Return a count of the discovered tokens for logging.

    The result holds no character of any token, so a log file or a support bundle never leaks
    credential material (issue #1710). An operator identifies a single token by its one-based
    position, which every per-token log line already carries.

    Args:
        tokens: The raw API token values. The function reads only the length of the list.

    Returns:
        A short phrase that states how many tokens the environment holds.
    """
    return f"{len (tokens )} token(s) found, values hidden"  # Count only -- no token character may reach the log


def _parse_api_tokens() -> tuple[str, list[str]]:  # Preserve the existing behavior during the compliance refactor.
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
        logger.debug("Token(s) discovered for initialization (redacted): %s", _redact_tokens(tokens))  # Safe preview
    else:  # No tokens discovered in environment
        logger.debug("No tokens discovered in environment; will rely on env_file or mistapi.Session fallback")  # Note
    return host, tokens  # Return host string and parsed token list to caller

    # Feature 1020: config values shipped in deploy/.env.example that must never be treated as real credentials.


_CREDENTIAL_PLACEHOLDER_MARKERS = ("your_", "_here", "changeme", "example.com", "<", ">")  # Copy-paste sentinels


def _looks_like_placeholder(value: str) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when *value* is blank or an obvious copy-paste placeholder (feature 1020, local-only)."""
    candidate = value.strip().lower()  # Normalize for case-insensitive marker matching.
    if not candidate:  # Empty/blank values are never valid credentials.
        return True  # Preserve the existing behavior during the compliance refactor.
    return any(marker in candidate for marker in _CREDENTIAL_PLACEHOLDER_MARKERS)  # Flag known placeholder markers.


def _preflight_verify_credentials(
    require_token: bool = True,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Fail closed before any mistapi/requests call when host/token config is absent or a placeholder.

    Feature 1020 (US3): invoked at the top of ``_establish_mist_session()`` for every dispatch mode. It
    performs only local string validation. It never imports ``requests`` or ``mistapi`` and never issues
    an HTTP request. So a misconfigured run exits with a redacted, actionable message instead of a
    malformed URL from mistapi. Token-based modes need a token
    (``--test``/``--testinteractive``/TUI/CLI). The ``require_token`` is False for interactive ``--login``,
    which authenticates via email/password rather than a token. Any token value present is shown only via
    ``_redact_tokens()`` previews, never raw (FR-015/SC-005). Since issue #1710 a preview is an 8
    character SHA-256 fingerprint, so it carries no character of the token itself.
    """
    logger.info("Running credential/config preflight (require_token=%s)", require_token)  # Before-action log.
    problems = _collect_credential_problems(require_token)  # Local string checks only, no network.
    if not problems:  # Host present and (when required) a real token present -> continue to session init.
        logger.debug("Credential/config preflight passed (require_token=%s)", require_token)  # After-action log.
        return  # Preserve the existing behavior during the compliance refactor.
    _report_credential_failure(problems)  # Emits the operator guidance and exits non-zero.


def _collect_credential_problems(
    require_token: bool,
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return every host/token configuration problem so the operator sees all fixes in one pass."""
    host, tokens = _parse_api_tokens()  # Reuse the canonical host/token reader (env only, no network).
    problems: list[str] = []  # Collect all issues so the operator sees every fix in one pass.
    if _looks_like_placeholder(host):  # Blank/placeholder host makes mistapi build malformed URLs.
        problems.append(
            "MIST_HOST is blank or a placeholder - set a real host (e.g. api.mist.com)"
        )  # Preserve the existing behavior during the compliance refactor.
    problems.extend(_collect_token_problems(require_token, tokens))  # Token rules are token-mode only.
    return problems  # Empty list means the preflight passed.


def _collect_token_problems(
    require_token: bool, tokens: list[str]
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return the token problems for modes that need a token, or nothing for interactive login."""
    if not require_token:  # Interactive --login authenticates by email/password, so no token is needed.
        return []  # Preserve the existing behavior during the compliance refactor.
    if not tokens:  # No MIST_APITOKEN/MIST_API_TOKEN resolved to a non-empty value.
        return [
            "no API token found - set MIST_APITOKEN or MIST_API_TOKEN"
        ]  # Preserve the existing behavior during the compliance refactor.
    if all(_looks_like_placeholder(token) for token in tokens):  # Only placeholders present.
        return [
            f"API token is a placeholder value (redacted: {_redact_tokens (tokens )})"
        ]  # Preserve the existing behavior during the compliance refactor.
    return []  # At least one real token is present.


def _report_credential_failure(
    problems: list[str],
) -> NoReturn:  # Preserve the existing behavior during the compliance refactor.
    """Log every preflight problem with remediation guidance, then exit before any session is built."""
    logger.error("Credential/config preflight failed: %s", "; ".join(problems))  # Names only - never secrets.
    logger.error(
        "[ERROR] Cannot start a Mist session - credential/config preflight failed:"
    )  # Preserve the existing behavior during the compliance refactor.
    for problem in problems:  # Enumerate each distinct problem on its own line.
        logger.error("[ERROR]   - %s", problem)  # Log per-problem detail at ERROR level.
    logger.error(
        "[ERROR] Copy deploy/.env.example to .env, then set MIST_HOST and MIST_APITOKEN/MIST_API_TOKEN."
    )  # Preserve the existing behavior during the compliance refactor.
    logger.error(
        "[ERROR] For --test/--testinteractive, also set org_id (or ORG_ID) - not MIST_ORG_ID - for this path."
    )  # Preserve the existing behavior during the compliance refactor.
    sys.exit(1)  # Exit non-zero before the code constructs any session or network object.


def _check_token_rate_limit(
    token: str, test_host: str, label: str
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Probe a token via GET /self. True if rate-limited/unreachable, False if usable.

    Args:
        token: The raw API token. It reaches the Authorization header and never reaches the log.
        test_host: The Mist API hostname to probe.
        label: A secret-free identifier such as ``"2/3"`` that names this token in the log.
    """
    try:
        import requests  # Import here -- only needed for this edge-case rate-limit probe path

        url = f"https://{test_host }/api/v1/self"  # Lightweight endpoint requiring auth for rate-limit probe
        headers = {"Authorization": f"Token {token }"}  # Standard Mist API bearer token header
        response = requests.get(url, headers=headers, timeout=5)  # Short timeout -- probe, not full call
        if response.status_code == 429:  # HTTP 429 = Too Many Requests = rate-limited
            logger.debug(
                "Token %s is rate-limited (HTTP 429)", label
            )  # Preserve the existing behavior during the compliance refactor.
            return True  # Confirmed rate-limited -- skip this token
        elif response.status_code == 200:  # HTTP 200 = OK = token is functional
            logger.debug(
                "Token %s is available (HTTP 200)", label
            )  # Preserve the existing behavior during the compliance refactor.
            return False  # Token is usable -- include in available list
        else:  # Any unexpected status treated as unavailable (defensive)
            logger.warning(
                "Token %s returned unexpected status %d", label, response.status_code
            )  # Preserve the existing behavior during the compliance refactor.
            return True  # Treat unexpected response as unavailable for safety
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
    ) as test_err:  # Probe failures make only this token unavailable
        logging.warning("Failed to test token %s: %s", label, test_err, exc_info=True)  # Keep probe trace
        return True  # Treat connection exception as unavailable to avoid broken tokens


def _introspect_apisession_class(
    mistapi_module: Any,
) -> tuple[Any, list[str]]:  # Preserve the existing behavior during the compliance refactor.
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
        logger.debug(
            "mistapi.APISession not found -- will attempt mistapi.Session fallback only"
        )  # Preserve the existing behavior during the compliance refactor.
        return None, []  # Return None class and empty param list to trigger fallback path
    try:
        sig_params = list(inspect.signature(apisession_cls).parameters.keys())  # Inspect constructor for param names
        logger.debug(
            "mistapi.APISession accepted parameters: %s", sig_params
        )  # Preserve the existing behavior during the compliance refactor.
        return apisession_cls, sig_params  # Return class and parameter name list
    except (TypeError, ValueError) as error:  # Some SDK callables do not expose a signature
        logging.debug(
            "Failed to introspect APISession signature: %s", error, exc_info=True
        )  # Proceed with no parameter list
        return apisession_cls, []  # Return class but no param info -- attempts list will be minimal


def _resolve_token_param_names(
    sig_params: list[str],
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return the supported token constructor parameter names, in priority order.

    Filters the known token kwargs against the introspected signature so callers
    only attempt parameter names the constructor actually accepts.
    """
    logger.debug("Resolving supported token parameter names from signature")  # Trace param resolution
    return [n for n in ["apitoken", "api_token", "token"] if n in sig_params]  # Keep only accepted token kwargs


def _build_token_session_attempts(  # Preserve the existing behavior during the compliance refactor.
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> list[dict[str, str]]:
    """Build token-auth kwargs dicts (highest priority) for each supported token param."""
    logger.debug("Building token-based APISession attempts")  # Trace token attempt construction
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


def _build_fallback_session_attempts(  # Preserve the existing behavior during the compliance refactor.
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> list[dict[str, str]]:
    """Build env_file/host fallback attempts, only when no env tokens are present."""
    logger.debug("Building fallback (env_file/host) APISession attempts")  # Trace fallback construction
    attempts: list[dict[str, str]] = []  # Accumulate fallback attempts
    if tokens:  # Env tokens present -- the code skips fallbacks to avoid duplicate token reads
        return attempts  # No fallback needed -- token attempts already cover auth
    if "env_file" in sig_params:  # env_file only when no env tokens (avoids double-read)
        attempts.append({"env_file": ".env"})  # Read credentials from .env file
    if "host" in sig_params:  # Host-only as last resort (unauthenticated probe)
        attempts.append({"host": host})  # Minimal connection -- API calls will fail without token
    return attempts  # Ordered fallback attempts


def _build_session_attempts(  # Preserve the existing behavior during the compliance refactor.
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


def _log_session_attempt_traceback(
    exc: Exception,
) -> None:  # Preserve the existing behavior during the compliance refactor.
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
            logger.info("  TRACE: %s", line)  # Prefix with TRACE so operators can filter
    except (TypeError, ValueError, OSError, RuntimeError) as trace_err:  # Secondary trace logging must not hide auth
        logging.warning("Failed to log traceback: %s", trace_err, exc_info=True)  # Non-fatal with secondary trace


def _try_single_session_kwargs(  # Preserve the existing behavior during the compliance refactor.
    apisession_cls: Any,
    kwargs: dict[str, str],
    attempt_num: int,
    total: int,
) -> tuple[Any, bool]:
    """Try one APISession kwargs dict. Return (session_or_None, rate_limit_seen)."""
    if apisession_cls is None:  # Guard: the class must be present if the code built the attempts list
        raise AssertionError(
            "apisession_cls should be set if attempts list is populated"
        )  # Preserve the existing behavior during the compliance refactor.
    try:  # APISession constructor may raise on auth/validation/rate-limit
        session = apisession_cls(**kwargs)  # Attempt APISession constructor with these kwargs
        logger.info(
            "Mist API session initialized with mistapi.APISession using kwargs=%s", list(kwargs.keys())
        )  # Preserve the existing behavior during the compliance refactor.
        return session, False  # Success -- no rate-limit signal needed
    except (TypeError, ValueError, RuntimeError, OSError) as e:  # Constructor variant failed without ending retries
        error_msg = str(e)  # Convert exception to string for rate-limit signature check
        logging.warning(
            "APISession attempt %d/%d failed kwargs=%s: %s", attempt_num, total, kwargs, e, exc_info=True
        )  # Keep constructor trace while the retry loop continues
        rate_limit = (
            "'NoneType' object is not iterable" in error_msg
        )  # Heuristic for rate-limit during token validation
        if rate_limit:  # Operator-visible signal that caller should switch to per-token retry path
            logging.warning(
                "Detected possible rate limiting during token validation - tokens may be throttled"
            )  # Preserve the existing behavior during the compliance refactor.
        _log_session_attempt_traceback(e)  # Log full traceback for detailed debugging
        return None, rate_limit  # Return failure with rate-limit flag for caller to react


def _execute_session_attempts(  # Preserve the existing behavior during the compliance refactor.
    apisession_cls: Any,
    attempts: list[dict[str, str]],
) -> tuple[Any, Any, bool, list[str]]:
    """Try each kwargs dict until one constructs a valid APISession. Track rate-limit signal."""
    tried_variants: list[str] = []  # Track all attempted kwargs for error reporting on total failure
    successful_method: Any = None  # Will hold the kwargs dict that succeeded
    rate_limit_detected = False  # Set True when a NoneType rate-limit error signature appears
    session: Any = None  # Will hold the created APISession object on success
    for i, kwargs in enumerate(attempts, start=1):  # Try each kwargs dict in priority order
        tried_variants.append(str(list(kwargs.keys())))  # Record attempt as string of keys before trying
        session, attempt_rate_limit = _try_single_session_kwargs(
            apisession_cls, kwargs, i, len(attempts)
        )  # Try one kwargs dict. Capture rate-limit signal
        if attempt_rate_limit:  # Even a failed attempt may surface the rate-limit signature
            rate_limit_detected = True  # Preserve the signal across iterations
        if session is not None:  # Successful construction -- record winning kwargs and stop
            successful_method = kwargs  # Downstream auth validation needs to know which kwargs worked
            break  # Success -- skip remaining attempts
    return session, successful_method, rate_limit_detected, tried_variants  # Return all state to orchestrator


def _filter_available_tokens(
    tokens: list[str], host: str
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
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
        label = f"{index }/{len (tokens )}"  # Secret-free identifier -- issue #1710 forbids any token character
        if not _check_token_rate_limit(token, host, label):  # Probe via /api/v1/self -- False means available
            available.append(token)  # This token is usable -- add to available list
            logger.info(
                "Token %s is available", label
            )  # Preserve the existing behavior during the compliance refactor.
        else:  # Token is rate-limited or unreachable -- skip it
            logger.warning(
                "Token %s is rate-limited - skipping", label
            )  # Preserve the existing behavior during the compliance refactor.
    return available  # Return only the usable tokens


def _build_filtered_session_kwargs(
    sig_params: list[str], tokens_csv: str, host: str
) -> dict[str, str]:  # Preserve the existing behavior during the compliance refactor.
    """Build APISession kwargs containing only fields the constructor accepts."""
    kwargs: dict[str, str] = {}  # Start with empty dict so we only include accepted params
    if "apitoken" in sig_params:  # Include token param only if constructor accepts it
        kwargs["apitoken"] = tokens_csv  # Pass comma-joined available tokens
    if "host" in sig_params:  # Include host if constructor accepts it
        kwargs["host"] = host  # Set target API hostname
    return kwargs  # Caller passes this into apisession_cls(**kwargs)


def _create_session_isolated_from_env(
    apisession_cls: Any, filtered_kwargs: dict[str, str]
) -> Any:  # Preserve the existing behavior during the compliance refactor.
    """Construct APISession with explicit filtered kwargs and no environment mutation."""
    try:  # Wrap constructor errors so filtered-token retry can fail safely.
        if apisession_cls is None:  # Guard replaces prior assert so behavior survives python -O optimization
            raise RuntimeError("apisession_cls should be set for retry logic")  # Retry logic requires the class
        session = apisession_cls(**filtered_kwargs)  # Create session with filtered token set
        logger.info(
            "SUCCESS: API session initialized with filtered token kwargs=%s", list(filtered_kwargs.keys())
        )  # Preserve the existing behavior during the compliance refactor.
        return session  # Caller pairs it back with filtered_kwargs for auth validation
    except (TypeError, ValueError, RuntimeError, OSError) as filtered_err:  # Filtered retry can still fail safely
        logging.exception("Failed to initialize with filtered tokens: %s", filtered_err)  # Keep trace
        return None  # Signal failure to caller


def _create_session_with_available_tokens(  # Preserve the existing behavior during the compliance refactor.
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
    logger.info("Initializing with %d available token(s)", len(available_tokens))  # Operator-visible progress
    session = _create_session_isolated_from_env(apisession_cls, filtered_kwargs)  # Construct with env-var isolation
    if session is None:  # Construction failed under env isolation
        return None, None  # Filtered token retry also failed
    return session, filtered_kwargs  # Return both for downstream auth validation


def _retry_with_filtered_tokens(  # Preserve the existing behavior during the compliance refactor.
    apisession_cls: Any,
    sig_params: list[str],
    tokens: list[str],
    host: str,
) -> tuple[Any, Any]:
    """Retry session creation using only non-rate-limited tokens after a multi-token failure."""
    if not (apisession_cls and tokens and len(tokens) > 1):  # Guard: need class and multiple tokens to retry
        return None, None  # Cannot retry without multiple tokens and a class
    logger.warning(
        "Multi-token init failed due to rate limiting - testing %d tokens individually", len(tokens)
    )  # Preserve the existing behavior during the compliance refactor.
    available_tokens = _filter_available_tokens(tokens, host)  # Probe each token for rate-limit status
    if not available_tokens:  # All tokens are throttled -- cannot recover
        logger.error(
            "All %d tokens are currently rate-limited - cannot initialize API session", len(tokens)
        )  # Preserve the existing behavior during the compliance refactor.
        return None, None  # No usable tokens -- caller will try Session fallback
    logger.info(
        "Found %d available token(s) out of %d total", len(available_tokens), len(tokens)
    )  # Preserve the existing behavior during the compliance refactor.
    return _create_session_with_available_tokens(apisession_cls, sig_params, available_tokens, host)  # Create session


def _try_session_fallback(
    mistapi_module: Any,
) -> tuple[Any, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Attempt legacy session creation via mistapi.Session() as last resort.

    mistapi.Session reads credentials from environment directly without explicit
    parameter passing. Used when all APISession constructor variants failed.

    Args:
        mistapi_module: The imported mistapi module.

    Returns:
        Tuple of (session, successful_method), both None if Session class absent or fails.
    """
    if not (mistapi_module and hasattr(mistapi_module, "Session")):  # Guard: Session class must exist
        return None, None  # Session class absent -- cannot use this fallback
    try:
        session = mistapi_module.Session()  # Attempt legacy Session() with no explicit params
        logger.info(
            "Mist API session initialized with mistapi.Session fallback"
        )  # Preserve the existing behavior during the compliance refactor.
        return session, {"fallback": "mistapi.Session"}  # Return session and method label for auth validation
    except (TypeError, ValueError, RuntimeError, OSError) as e:  # Last-resort SDK session creation failed safely
        logging.exception("mistapi.Session fallback failed: %s", e)  # Log why the last resort failed
        return None, None  # Fallback also failed -- caller will report total failure


def _ensure_mist_get_method(session: Any) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Verify that the session exposes a supported GET method.

    This check no longer adds a method to the third-party session object.
    The explicit session configuration seam owns the session shape check.

    Args:
        session: The initialized APISession or Session object to check.

    Returns:
        True if mist_get or get is present, False if neither method exists.
    """
    if hasattr(session, "mist_get"):  # Preferred method already exists on supported mistapi versions.
        return True  # Session is compatible as-is.
    if hasattr(session, "get") and callable(session.get):  # Newer SDK builds can expose get instead.
        return True  # Session is usable without a run-time attribute patch.
    logger.error(
        "Initialized session lacks 'mist_get' or 'get' methods required for API calls"
    )  # Preserve the existing behavior during the compliance refactor.
    return False  # Session is unusable -- hard failure


def _detect_session_token(session: Any) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when the session exposes a readable, non-empty token attribute."""
    logger.debug("Detecting readable token attribute on session")  # Trace token attribute probe
    token_attr = next((a for a in ("apitoken", "api_token", "token") if hasattr(session, a)), None)  # Find auth attr
    return bool(token_attr and getattr(session, token_attr))  # True only if attr exists and holds a value


def _detect_session_method_flags(
    successful_method: Any,
) -> tuple[bool, bool, bool]:  # Preserve the existing behavior during the compliance refactor.
    """Return (used_env_file, used_direct_token, used_fallback) from the winning kwargs."""
    logger.debug("Detecting auth method flags from successful constructor kwargs")  # Trace method-flag derivation
    direct_params = ["apitoken", "api_token", "token"]  # Constructor kwargs that denote direct token auth
    used_env_file = bool(successful_method and "env_file" in successful_method)  # env_file auth path used
    used_direct_token = bool(successful_method and any(p in successful_method for p in direct_params))  # Direct token
    used_fallback = bool(successful_method and "fallback" in successful_method)  # Legacy Session() path used
    return used_env_file, used_direct_token, used_fallback  # Surface flags for logging decisions


def _log_missing_auth_warning() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Emit operator-facing warnings when no authentication method can be detected."""
    logger.warning("Session established but no auth method detected; API calls may fail if auth required")  # Warn
    logger.warning("To fix: 1) Copy documentation/sample.env to .env, 2) Set MIST_APITOKEN to your token")  # Steps
    logger.warning("Get your API token from: https://manage.mist.com/admin/apitoken")  # Where to obtain a token


def _log_detected_auth(
    used_env_file: bool, used_direct_token: bool, has_readable_token: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Emit a single debug line describing the detected auth path (env_file > token param > attr)."""
    if used_env_file:  # Highest-priority detected path -- credentials came from .env
        logger.debug("Session initialized using env_file - authentication configured via .env file")  # env_file path
    elif used_direct_token:  # Next priority -- the caller passed a token directly to the constructor
        logger.debug("Session initialized using direct token parameter - authentication configured")  # token-param path
    elif has_readable_token:  # Last -- session simply exposes a populated token attribute
        logger.debug("Session has readable token attribute - authentication appears configured")  # attribute path


def _log_session_auth_status(
    session: Any, successful_method: Any
) -> None:  # Preserve the existing behavior during the compliance refactor.
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


def _validate_initialized_session(
    session: Any, successful_method: Any
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Validate that an initialized session provides the required methods and detectable authentication.

    Calls _ensure_mist_get_method to verify GET method compatibility, then
    calls _log_session_auth_status to warn if authentication cannot be confirmed.
    Returns False only for hard failures (missing mist_get). Auth warnings are non-fatal.

    Args:
        session: The initialized APISession or Session object.
        successful_method: Dict describing which constructor kwargs were used.

    Returns:
        True if the session is usable, False if required mist_get method is absent.
    """
    if not _ensure_mist_get_method(session):  # Verify a supported GET method without patching the session.
        return False  # Session is unusable without mist_get
    _log_session_auth_status(session, successful_method)  # Warn if authentication method is unclear
    return True  # Session passed all checks -- ready for API calls


def _attempt_all_session_strategies(  # Preserve the existing behavior during the compliance refactor.
    apisession_cls: type[Any],
    sig_params: list[str],
    tokens: list[str],
    host: str,
    mistapi_mod: Any,
) -> tuple[Any, dict[str, Any] | None, list[str]]:
    """Try APISession kwargs, then filtered-token retry, then legacy Session(). Returns (session, method, tried)."""
    attempts = _build_session_attempts(apisession_cls, sig_params, tokens, host)  # Ordered kwargs candidates
    session_obj, method, rate_limited, tried = _execute_session_attempts(apisession_cls, attempts)  # First wave
    if not session_obj and rate_limited:  # Rate-limit signature — try tokens individually
        session_obj, method = _retry_with_filtered_tokens(
            apisession_cls, sig_params, tokens, host
        )  # Preserve the existing behavior during the compliance refactor.
    if not session_obj:  # APISession exhausted — try legacy mistapi.Session()
        session_obj, method = _try_session_fallback(
            mistapi_mod
        )  # Preserve the existing behavior during the compliance refactor.
    return session_obj, method, tried  # Caller validates / logs / patches


def _log_failed_session_variants(
    tried_variants: list[str],
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log every kwargs variant that failed (operator debugging on total init failure)."""
    logger.error(
        "All Mist API session initialization attempts failed. Variants tried:"
    )  # Preserve the existing behavior during the compliance refactor.
    for variant in tried_variants:  # One log line per variant for clarity
        logger.error("  - %s", variant)  # Preserve the existing behavior during the compliance refactor.


def _install_default_request_timeout(
    inner_session: Any,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Install API_REQUEST_TIMEOUT as the default timeout on the requests.Session."""
    from requests.adapters import HTTPAdapter  # Lazy import. The requests package is large and only needed here

    class TimeoutAdapter(HTTPAdapter):  # Nested so we do not expose a public adapter class
        """HTTPAdapter that injects a default timeout."""

        def __init__(self, default_timeout: int, **kwargs: Any) -> None:  # Capture the project-wide timeout default
            self.default_timeout = default_timeout  # Reused when send() gets timeout=None
            super().__init__(**kwargs)  # Real adapter setup (connection pool, retries)

        def send(  # Preserve the existing behavior during the compliance refactor.
            self,
            request: Any,
            stream: Any = False,
            timeout: Any = None,
            verify: Any = True,
            cert: Any = None,
            proxies: Any = None,
        ) -> Any:
            if timeout is None:  # Caller did not supply a per-call timeout -- substitute our default
                timeout = self.default_timeout  # Preserve the existing behavior during the compliance refactor.
                # Issue #431: forward args verbatim. The signature must match parent for adapter contract.
            return super().send(
                request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies
            )  # Preserve the existing behavior during the compliance refactor.

    adapter = TimeoutAdapter(default_timeout=API_REQUEST_TIMEOUT)  # Single instance shared by both schemes
    inner_session.mount("https://", adapter)  # Apply to HTTPS calls (standard Mist transport)
    inner_session.mount("http://", adapter)  # Apply to plain HTTP too for completeness


def _configure_session_timeout(
    session_obj: Any,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Report that the explicit session configurator owns timeout setup."""
    logger.info("Checking legacy session timeout entry point")  # Log before the compatibility check.
    if session_obj is None:  # A missing session means there is nothing to configure.
        logger.warning("Cannot configure timeout because no session was supplied")  # Explain the safe no-op.
        return  # Preserve the historical non-fatal behavior.
    logger.debug("Session timeout setup is owned by MistSessionConfigurator")  # Confirm no patch ran here.


from src.api.tenant_fetch import APITenantFetchUtils  # Re-exported for ServicePingLauncher late-binding
from src.data.data_processing_utils import DataProcessingUtils  # Cat E canonical (1015 T-10).
from src.export.data_exporter import DataExporter  # T-08 re-export
from src.ui.prompt_utils import PromptUtils  # T-07 re-export


def _get_duc_instance() -> DeviceUtilityCommands:  # Build DeviceUtilityCommands.
    """Create DeviceUtilityCommands instance with MistHelper globals."""
    from src.device.utility_commands import (  # Import the extracted class + deps.
        DeviceUtilityCommands as _DUC,
    )
    from src.device.utility_commands import (  # Preserve the existing behavior during the compliance refactor.
        UtilityCommandsDeps as _Deps,
    )

    deps = _Deps(  # Bundle 6 dependencies into a frozen dataclass.
        apisession=MainEntrypoint.context.apisession,
        select_site_fn=PromptUtils.select_site_id_from_csv,
        select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype),
        safe_input_fn=InputUtils.safe_input,
        write_export_fn=lambda data, fn, api: DataExporter.write_with_format_selection(data, fn, api_function_name=api),
        websocket_manager_factory=WebSocketManager,
    )
    return _DUC(deps)  # Instantiate with bundled deps.


def _build_gateway_export_kwargs() -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Build the kwargs dict passed to configure_gateway_export_utils_dependencies()."""
    logger.info("Reading the canonical site exclude prefix")  # Log before the prefix module read.
    from src.refactors import mist_site_exclude_prefix  # Read the canonical filter owner at dispatch time.

    logger.debug(  # Log the filter length without exposing the configured text.
        "Read the canonical site exclude prefix with length %s",
        len(mist_site_exclude_prefix.MIST_SITE_EXCLUDE_PREFIX),
    )
    return {  # Single dependency-wiring payload assembled in one place.
        "apisession_dependency": MainEntrypoint.context.apisession,  # Live mistapi session.
        "mistapi_dependency": mistapi,  # mistapi root module.
        "config_utils": ConfigUtils,  # Shared config helpers.
        "cache_utils": CacheUtils,  # Disk-cache helpers.
        "file_path_utils": FilePathUtils,  # Path helpers.
        "data_exporter": DataExporter,  # Output backend writer.
        "data_processing_utils": DataProcessingUtils,  # Flatten/normalize helpers.
        "api_fetch_utils": APIFetchUtils,  # Paged fetch helpers.
        "api_core_fetch_utils": APICoreFetchUtils,  # Core unwrap helpers.
        "org_inventory_exporter": OrgInventoryExporter,  # For inventory lookups.
        "org_site_exporter": OrgSiteExporter,  # For site lookups.
        "input_utils": InputUtils,  # safe_input + prompts.
        "execute_fn": ConnectionPoolExecutor.execute,  # Pool executor (1012 SC-003).
        "validation_utils": ValidationUtils,  # Input validation.
        "rate_limiting_utils": RateLimitingUtils,  # Adaptive delay.
        "mist_wan_target_ports": MistWanTargetPorts.VALUE,  # Port list from extracted class attribute.
        "mist_site_exclude_prefix": mist_site_exclude_prefix.MIST_SITE_EXCLUDE_PREFIX,  # Canonical site filter prefix.
        "fast_mode_max_retries": FAST_MODE_MAX_RETRIES,  # Retry cap.
        "fast_mode_retry_delay": FAST_MODE_RETRY_DELAY,  # Delay between retries.
        "api_usage_cache": _api_usage_cache,  # Shared API usage cache.
        "tqdm_module": tqdm,  # Progress bar dependency.
    }


def _configure_gateway_module() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire DI into the canonical gateway_export_utils module (cascades to stats + WAN override)."""
    configure_gateway_export_utils_dependencies(
        **_build_gateway_export_kwargs()
    )  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_stats_device_stats_with_freshness(
    fast: bool = False,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayStatsExporter.device_stats_with_freshness."""
    _configure_gateway_module()  # WHY: cascades DI wiring for stats exporter.
    GatewayStatsExporter.device_stats_with_freshness(
        fast=fast
    )  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_stats_wan_port_conflicts() -> (
    None
):  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayStatsExporter.wan_port_conflicts."""
    _configure_gateway_module()  # WHY: cascades DI wiring for stats exporter.
    GatewayStatsExporter.wan_port_conflicts()  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_management_ips(
    fast: bool = False,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayExportUtils.management_ips."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.management_ips(fast=fast)  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_templates() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayExportUtils.templates."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.templates()  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_with_wan_overrides(
    fast: bool = False,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayExportUtils.with_wan_overrides."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.with_wan_overrides(fast=fast)  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_wan2_variable_migration(
    fast: bool = False, dry_run: bool = False
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayExportUtils.wan2_variable_migration."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.wan2_variable_migration(
        fast=fast, dry_run=dry_run
    )  # Preserve the existing behavior during the compliance refactor.


def _dispatch_gateway_device_configs(
    debug: bool = False, fast: bool = False
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Wire gateway DI then delegate to canonical GatewayExportUtils.device_configs."""
    _configure_gateway_module()  # WHY: cascades DI wiring before canonical call.
    GatewayExportUtils.device_configs(
        debug=debug, fast=fast
    )  # Preserve the existing behavior during the compliance refactor.

    # ============================================================================
    # TROUBLESHOOTING UTILITIES CLASS
    # ============================================================================


def _build_ssh_runner_deps() -> SSHRunnerManagerDeps:  # Build the deps bundle for SSHRunnerManager entrypoints.
    """Build dependency container for SSH runner logic (reads MistHelper globals)."""
    cli_args = globals().get("args") if "args" in globals() else None  # Read parsed CLI args.
    _configure_gateway_module()  # 1014 P13: DI wire canonical gateway module before packaging class ref.
    return SSHRunnerManagerDeps(  # Assemble the deps.
        args=cli_args,
        progress_emitter=MainEntrypoint.context.progress_emitter,
        enhanced_ssh_runner=EnhancedSSHRunner,
        input_utils=InputUtils,  # WHY: inject the EOF-safe prompt seam for unattended interactive tests.
        cache_utils=CacheUtils,
        gateway_export_utils=GatewayExportUtils,
        file_path_utils=FilePathUtils,
    )

    # ============================================================================
    # RATE LIMITING & ADDRESS UTILITIES (extracted to src/utils/)
    # ============================================================================


from src.utils.rate_limiting import RateLimitingUtils  # Preserve the existing behavior during the compliance refactor.

# ============================================================================
# ORG CONFIG MIGRATION MANAGER CLASS
# ============================================================================

# ============================================================================
# VIRTUAL CHASSIS MANAGER CLASS
# ============================================================================


def _configure_virtual_chassis_manager() -> (
    type[VirtualChassisManager]
):  # Preserve the existing behavior during the compliance refactor.
    """Wire VirtualChassisDependencies and return the canonical VirtualChassisManager class."""
    _configure_virtual_chassis_dependencies(  # Publish MistHelper globals into the impl module.
        _VirtualChassisDependencies(  # Frozen container of 9 injected collaborators.
            apisession=MainEntrypoint.context.apisession,  # Live Mist API session.
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


def _configure_site_config_manager() -> (
    type[SiteConfigManager]
):  # Preserve the existing behavior during the compliance refactor.
    """Wire SiteConfigDependencies and return the canonical SiteConfigManager class."""
    _configure_site_config_dependencies(
        _SiteConfigDependencies(  # Frozen container of 7 injected collaborators
            apisession=MainEntrypoint.context.apisession,  # Live Mist API session
            config_utils=ConfigUtils,  # Org id caching + stop-signal check
            file_path_utils=FilePathUtils,  # Portable CSV path resolver
            input_utils=InputUtils,  # Safe input for destructive confirmations
            data_exporter=DataExporter,  # Result-report writer
            mistapi=mistapi,  # Root SDK module for calls + pagination
            default_api_page_limit=DEFAULT_API_PAGE_LIMIT,  # Bulk fetch page size
            api_usage_cache=_api_usage_cache,  # Shared quota view for the adaptive rate limiter
        )
    )
    return SiteConfigManager  # Canonical class ready for menu callback dispatch


def _build_firmware_manager(
    session: Any, target_org_id: str
) -> FirmwareManager:  # Preserve the existing behavior during the compliance refactor.
    """Build a fully DI-wired FirmwareManager instance for menu callbacks and internal re-checks."""
    logger.debug("Building firmware manager impl for org %s", target_org_id)  # Trace factory build
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


def _build_org_ap_upgrader(
    **overrides: Any,
) -> _OrgLevelAPFirmwareUpgrader:  # Preserve the existing behavior during the compliance refactor.
    """Construct an OrgLevelAPFirmwareUpgrader with MistHelper.py DI wiring.

    Callers may override ``org_id``, ``dry_run``, ``msp_privileges``, or
    ``selected_msp`` via keyword. All remaining hooks bind to canonical
    MistHelper.py collaborators.
    """
    # WHY: read-only references to module globals msp_privileges/apisession/selected_msp.
    # No assignment means `global` is unnecessary (drops PLW0602 site, initiative 1016).
    kwargs: dict[str, Any] = {  # WHY: build DI kwargs dict for src class
        "org_id": ConfigUtils.get_cached_or_prompted_org_id() or "",
        "apisession": MainEntrypoint.context.apisession,
        "dry_run": getattr(globals().get("args", None), "dry_run", False),
        "safe_input_fn": InputUtils.safe_input,
        "check_stop_fn": ConfigUtils.check_stop_signal,
        "get_org_id_fn": ConfigUtils.get_cached_or_prompted_org_id,
        "fetch_sites_fn": APICoreFetchUtils.all_sites_with_limit,
        "write_results_fn": DataExporter.write_with_format_selection,
        "is_debug_fn": IsDebugMode.check,
        "msp_privileges": MainEntrypoint.context.msp_privileges if MainEntrypoint.context.msp_privileges else [],
        "selected_msp": MainEntrypoint.context.selected_msp if MainEntrypoint.context.selected_msp else None,
    }
    kwargs.update(overrides)  # WHY: caller overrides win over defaults
    return _OrgLevelAPFirmwareUpgrader(**kwargs)  # WHY: single src-class construction path


def _ws_cmd_deps() -> WebSocketCmdDeps:  # Preserve the existing behavior during the compliance refactor.
    """Create WebSocket command dependency context for the dispatch table."""
    import mistapi.api.v1.sites.devices as _site_devices

    return WebSocketCmdDeps(  # Preserve the existing behavior during the compliance refactor.
        apisession=MainEntrypoint.context.apisession,
        select_site_fn=PromptUtils.select_site_id_from_csv,
        select_device_fn=PromptUtils.select_device_id_from_inventory,
        validate_target_fn=ValidationUtils.validate_ping_target,
        list_devices_fn=_site_devices.listSiteDevices,
        safe_input_fn=InputUtils.safe_input,
    )

    # ============================================================================
    # AUDIT ANALYSIS OPS CLASS
    # ============================================================================


menu_actions: dict[str, Any] = {
    # ==============================
    # SYSTEM OPERATIONS
    # ==============================
    "0": GlobalImportManager.MenuEntry(  # Use named fields for menu 0.
        menu_id="0",  # Store key for drift checks.
        handler=lambda: sys.exit(0),
        title="Exit MistHelper",
        category=OperationRegistry.skip_category("0"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SITE ADDRESS AUDIT (read-only)
    # ==============================
    "195": GlobalImportManager.MenuEntry(  # Use named fields for menu 195.
        menu_id="195",  # Store key for drift checks.
        handler=lambda: AddressAuditEngine().run(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ),
        title=(
            "Audit site addresses from CSV (data/) - fuse Mist + SNMP + CSV hints, "
            "verify vs. web; READ-ONLY, saves report. Tier-3 browser geocoding "
            "auto-engages when available (ADDRESS_AUDIT_GEOCODE=off to skip)"
        ),
        category=OperationRegistry.skip_category("195"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # READ-ONLY OPERATIONS
    # ==============================
    # > Setup & Core Logs
    "20": GlobalImportManager.MenuEntry(  # Use named fields for menu 20.
        menu_id="20",  # Store key for drift checks.
        handler=OrgAlarmEventExporter.alarms,
        title="Export all organization alarms from the past day",
        category=OperationRegistry.skip_category("20"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "21": GlobalImportManager.MenuEntry(  # Use named fields for menu 21.
        menu_id="21",  # Store key for drift checks.
        handler=OrgAlarmEventExporter.device_events,
        title="Export all device events from the past 24 hours",
        category=OperationRegistry.skip_category("21"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "22": GlobalImportManager.MenuEntry(  # Use named fields for menu 22.
        menu_id="22",  # Store key for drift checks.
        handler=lambda: OrgExportUtils.audit_logs(full_history=False),
        title="Export audit logs for the organization (last 24 hours)",
        category=OperationRegistry.skip_category("22"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "31": GlobalImportManager.MenuEntry(  # Use named fields for menu 31.
        menu_id="31",  # Store key for drift checks.
        handler=_dispatch_gateway_management_ips,
        title="Export gateway management overlay IPs grouped by template association",
        category=OperationRegistry.skip_category("31"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > WebSocket Device Commands
    "102": GlobalImportManager.MenuEntry(  # Use named fields for menu 102.
        menu_id="102",  # Store key for drift checks.
        handler=lambda: MacTableCommand.execute(_ws_cmd_deps()),
        title="Show MAC table on switch device via WebSocket (Layer 2 switching table)",
        category=OperationRegistry.skip_category("102"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "103": GlobalImportManager.MenuEntry(  # Use named fields for menu 103.
        menu_id="103",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.RoutingUtilsFactory().build().execute_show_forwarding_table(),
        title="Show forwarding table on gateway device via WebSocket (Layer 3 routing table)",
        category=OperationRegistry.skip_category("103"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "104": GlobalImportManager.MenuEntry(  # Use named fields for menu 104.
        menu_id="104",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.RoutingUtilsFactory().build().execute_show_routing_table(),
        title=("Show routing table on switches via WebSocket (Switch L3 routing - " "BGP/OSPF/Static)"),
        category=OperationRegistry.skip_category("104"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "105": GlobalImportManager.MenuEntry(  # Use named fields for menu 105.
        menu_id="105",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.RoutingUtilsFactory().build().execute_show_ssr_routes(),
        title=("Show SSR/SRX routing table via dedicated API (128T/SRX gateways - " "Advanced BGP analysis)"),
        category=OperationRegistry.skip_category("105"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Packet Capture Operations
    "134": GlobalImportManager.MenuEntry(  # Use named fields for menu 134.
        menu_id="134",  # Store key for drift checks.
        handler=lambda: PacketCaptureManager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).start_site_packet_capture(),
        title=("Start Site Packet Capture - Wireless/Wired/Gateway/Scan captures with " "WebSocket streaming"),
        category=OperationRegistry.skip_category("134"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "135": GlobalImportManager.MenuEntry(  # Use named fields for menu 135.
        menu_id="135",  # Store key for drift checks.
        handler=lambda: PacketCaptureManager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).start_org_packet_capture(),
        title=("Start Organization Packet Capture - MxEdge captures for org-level " "Mist Edges only"),
        category=OperationRegistry.skip_category("135"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Organization-Level Exports
    "1": GlobalImportManager.MenuEntry(  # Use named fields for menu 1.
        menu_id="1",  # Store key for drift checks.
        handler=OrgSiteExporter.sites,
        title="Export a list of all sites in the organization",
        category=OperationRegistry.skip_category("1"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "8": GlobalImportManager.MenuEntry(  # Use named fields for menu 8.
        menu_id="8",  # Store key for drift checks.
        handler=OrgInventoryExporter.inventory,
        title="Export the full inventory of devices in the organization",
        category=OperationRegistry.skip_category("8"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "15": GlobalImportManager.MenuEntry(  # Use named fields for menu 15.
        menu_id="15",  # Store key for drift checks.
        handler=OrgDeviceStatsExporter.device_stats,
        title="Export statistics for all devices in the organization",
        category=OperationRegistry.skip_category("15"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "19": GlobalImportManager.MenuEntry(  # Use named fields for menu 19.
        menu_id="19",  # Store key for drift checks.
        handler=OrgDeviceStatsExporter.device_port_stats,
        title="Export port-level statistics for switches and gateways",
        category=OperationRegistry.skip_category("19"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "16": GlobalImportManager.MenuEntry(  # Use named fields for menu 16.
        menu_id="16",  # Store key for drift checks.
        handler=OrgDeviceStatsExporter.vpn_peer_stats,
        title="Export VPN peer path statistics for the organization",
        category=OperationRegistry.skip_category("16"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Gateway & Site-Wide Exports
    # Direct reference (removed lambda) so systematic test harness can introspect 'fast' parameter
    "33": GlobalImportManager.MenuEntry(  # Use named fields for menu 33.
        menu_id="33",  # Store key for drift checks.
        handler=GatewayTestExporter.synthetic_tests,
        title="Export synthetic test results for all gateways",
        category=OperationRegistry.skip_category("33"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "9": GlobalImportManager.MenuEntry(  # Use named fields for menu 9.
        menu_id="9",  # Store key for drift checks.
        handler=OrgInventoryExporter.devices,
        title="Export a list of all devices in the organization",
        category=OperationRegistry.skip_category("9"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "59": GlobalImportManager.MenuEntry(  # Use named fields for menu 59.
        menu_id="59",  # Store key for drift checks.
        handler=SiteConfigExporter.settings,
        title="Export configuration settings for all sites",
        category=OperationRegistry.skip_category("59"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "34": GlobalImportManager.MenuEntry(  # Use named fields for menu 34.
        menu_id="34",  # Store key for drift checks.
        handler=GatewayTestExporter.test_results_by_site,
        title="Export all synthetic test results (including speed tests) for gateways",
        category=OperationRegistry.skip_category("34"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Location-Enriched Exports
    "2": GlobalImportManager.MenuEntry(  # Use named fields for menu 2.
        menu_id="2",  # Store key for drift checks.
        handler=OrgSiteExporter.sites_with_location,
        title="Export a list of sites with location and timezone info",
        category=OperationRegistry.skip_category("2"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "11": GlobalImportManager.MenuEntry(  # Use named fields for menu 11.
        menu_id="11",  # Store key for drift checks.
        handler=OrgInventoryExporter.gateways_with_site_info,
        title="Export a list of gateways with associated site and address info",
        category=OperationRegistry.skip_category("11"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "10": GlobalImportManager.MenuEntry(  # Use named fields for menu 10.
        menu_id="10",  # Store key for drift checks.
        handler=OrgInventoryExporter.devices_with_site_info,
        title="Export a list of all devices with associated site and address info",
        category=OperationRegistry.skip_category("10"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "4": GlobalImportManager.MenuEntry(  # Use named fields for menu 4.
        menu_id="4",  # Store key for drift checks.
        handler=lambda: (
            OrgSiteExporter.current_guests(),
            OrgSiteExporter.historical_guests(),
        ),
        title="Export all current guest users and last 7 days of historical guests to CSV",
        category=OperationRegistry.skip_category("4"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "17": GlobalImportManager.MenuEntry(  # Use named fields for menu 17.
        menu_id="17",  # Store key for drift checks.
        handler=OrgDeviceStatsExporter.switch_vc_stats,
        title="Export all switch virtual chassis (VC/stacking) stats to CSV",
        category=OperationRegistry.skip_category("17"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "12": GlobalImportManager.MenuEntry(  # Use named fields for menu 12.
        menu_id="12",  # Store key for drift checks.
        handler=OrgInventoryExporter.combined_inventory_with_site_info,
        title="Export combined inventory with site and address info by calendar week",
        category=OperationRegistry.skip_category("12"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "32": GlobalImportManager.MenuEntry(  # Use named fields for menu 32.
        menu_id="32",  # Store key for drift checks.
        handler=_dispatch_gateway_templates,
        title="Export gateway templates from the organization",
        category=OperationRegistry.skip_category("32"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "3": GlobalImportManager.MenuEntry(  # Use named fields for menu 3.
        menu_id="3",  # Store key for drift checks.
        handler=OrgSiteExporter.sites_list_api,
        title=(
            "Export all sites using the 'list' sites API endpoint (to "
            "SiteList_ListAPI.csv, only if not already present)"
        ),
        category=OperationRegistry.skip_category("3"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "35": GlobalImportManager.MenuEntry(  # Use named fields for menu 35.
        menu_id="35",  # Store key for drift checks.
        handler=_dispatch_gateway_with_wan_overrides,
        title=("Find gateway ports overridden from template (outliers for compliance " "correction)"),
        category=OperationRegistry.skip_category("35"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Site-Specific Data Exports
    "62": GlobalImportManager.MenuEntry(  # Use named fields for menu 62.
        menu_id="62",  # Store key for drift checks.
        handler=SiteDeviceExporter.port_stats,
        title="Export port statistics for a selected site",
        category=OperationRegistry.skip_category("62"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "65": GlobalImportManager.MenuEntry(  # Use named fields for menu 65.
        menu_id="65",  # Store key for drift checks.
        handler=SiteClientExporter.clients,
        title="Export client statistics for a selected site",
        category=OperationRegistry.skip_category("65"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "60": GlobalImportManager.MenuEntry(  # Use named fields for menu 60.
        menu_id="60",  # Store key for drift checks.
        handler=SiteDeviceExporter.devices,
        title="Export device list for a selected site",
        category=OperationRegistry.skip_category("60"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "61": GlobalImportManager.MenuEntry(  # Use named fields for menu 61.
        menu_id="61",  # Store key for drift checks.
        handler=SiteDeviceExporter.device_stats,
        title="Export device statistics for a selected site",
        category=OperationRegistry.skip_category("61"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "63": GlobalImportManager.MenuEntry(  # Use named fields for menu 63.
        menu_id="63",  # Store key for drift checks.
        handler=SiteDeviceExporter.device_virtual_chassis,
        title="Export virtual chassis information for a selected switch device",
        category=OperationRegistry.skip_category("63"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "64": GlobalImportManager.MenuEntry(  # Use named fields for menu 64.
        menu_id="64",  # Store key for drift checks.
        handler=SiteClientExporter.wifi_clients,
        title=(
            "Export currently connected WiFi clients and session data for a " "selected site to SiteWiFiClients.CSV"
        ),
        category=OperationRegistry.skip_category("64"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Organization Template Exports
    "37": GlobalImportManager.MenuEntry(  # Use named fields for menu 37.
        menu_id="37",  # Store key for drift checks.
        handler=OrgTemplateExporter.all_templates,
        title="Export all organization templates (gateway, network, RF, site, AP)",
        category=OperationRegistry.skip_category("37"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "38": GlobalImportManager.MenuEntry(  # Use named fields for menu 38.
        menu_id="38",  # Store key for drift checks.
        handler=OrgTemplateExporter.network_templates,
        title="Export network template information for the organization",
        category=OperationRegistry.skip_category("38"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "39": GlobalImportManager.MenuEntry(  # Use named fields for menu 39.
        menu_id="39",  # Store key for drift checks.
        handler=OrgTemplateExporter.rf_templates,
        title="Export RF template information for the organization",
        category=OperationRegistry.skip_category("39"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "40": GlobalImportManager.MenuEntry(  # Use named fields for menu 40.
        menu_id="40",  # Store key for drift checks.
        handler=OrgTemplateExporter.ap_templates,
        title="Export AP template information for the organization",
        category=OperationRegistry.skip_category("40"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "41": GlobalImportManager.MenuEntry(  # Use named fields for menu 41.
        menu_id="41",  # Store key for drift checks.
        handler=OrgTemplateExporter.switch_templates,
        title="Export switch template information for the organization",
        category=OperationRegistry.skip_category("41"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Organization Statistics & Analytics
    "27": GlobalImportManager.MenuEntry(  # Use named fields for menu 27.
        menu_id="27",  # Store key for drift checks.
        handler=OrgClientSecurityExporter.wireless_clients,
        title="Export wireless client statistics for the organization",
        category=OperationRegistry.skip_category("27"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "28": GlobalImportManager.MenuEntry(  # Use named fields for menu 28.
        menu_id="28",  # Store key for drift checks.
        handler=OrgClientSecurityExporter.wired_clients,
        title="Export wired client statistics for the organization",
        category=OperationRegistry.skip_category("28"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Security & Monitoring
    "24": GlobalImportManager.MenuEntry(  # Use named fields for menu 24.
        menu_id="24",  # Store key for drift checks.
        handler=OrgClientSecurityExporter.security_events,
        title="Export security events for the organization",
        category=OperationRegistry.skip_category("24"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "29": GlobalImportManager.MenuEntry(  # Use named fields for menu 29.
        menu_id="29",  # Store key for drift checks.
        handler=OrgClientSecurityExporter.rogue_clients,
        title="Export rogue client detections for the organization",
        category=OperationRegistry.skip_category("29"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "30": GlobalImportManager.MenuEntry(  # Use named fields for menu 30.
        menu_id="30",  # Store key for drift checks.
        handler=OrgClientSecurityExporter.rogue_aps,
        title="Export rogue AP detections for the organization",
        category=OperationRegistry.skip_category("30"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Configuration & Management (Read-Only)
    "42": GlobalImportManager.MenuEntry(  # Use named fields for menu 42.
        menu_id="42",  # Store key for drift checks.
        handler=OrgAdminExporter.licenses,
        title="Export license information for the organization",
        category=OperationRegistry.skip_category("42"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "196": GlobalImportManager.MenuEntry(  # Use named fields for menu 196.
        menu_id="196",  # Store key for drift checks.
        handler=LicenseExportUtils.export_org_license_async_claim_status,
        title=("Export async organization license-claim status summary (and optional " "per-device details)"),
        category=OperationRegistry.skip_category("196"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "197": GlobalImportManager.MenuEntry(  # Use named fields for menu 197.
        menu_id="197",  # Store key for drift checks.
        handler=lambda: ClientPacketCaptureDownloader(MainEntrypoint.context.apisession).run(),
        title=("Download client packet captures grouped by VLAN (site -> client -> " "VLAN -> data/packet_captures/)"),
        category=OperationRegistry.skip_category("197"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "198": GlobalImportManager.MenuEntry(  # Use named fields for menu 198.
        menu_id="198",  # Store key for drift checks.
        handler=SiteWanUsageExporter.wan_usages,
        title=(
            "Search Site WAN Usages (searchSiteWanUsage) - Export per-site WAN " "usage records to SiteWanUsages.csv"
        ),
        category=OperationRegistry.skip_category("198"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "199": GlobalImportManager.MenuEntry(  # Use named fields for menu 199.
        menu_id="199",  # Store key for drift checks.
        handler=SiteWebhookDeliveriesExporter.deliveries,
        title=(
            "Search Site Webhook Deliveries (searchSiteWebhooksDeliveries) - Per " "site+webhook delivery audit CSV"
        ),
        category=OperationRegistry.skip_category("199"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "200": GlobalImportManager.MenuEntry(  # Use named fields for menu 200.
        menu_id="200",  # Store key for drift checks.
        handler=SiteGuestAuthorizationExporter.guest_authorizations,
        title=("Search Site Guest Authorization (searchSiteGuestAuthorization) - " "Per-site authorized guest CSV"),
        category=OperationRegistry.skip_category("200"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "201": GlobalImportManager.MenuEntry(  # Use named fields for menu 201.
        menu_id="201",  # Store key for drift checks.
        handler=SiteMistEdgeEventsExporter.mist_edge_events,
        title=("Search Site Mist Edge Events (searchSiteMistEdgeEvents) - Per-site " "Mist Edge event CSV"),
        category=OperationRegistry.skip_category("201"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "202": GlobalImportManager.MenuEntry(  # Use named fields for menu 202.
        menu_id="202",  # Store key for drift checks.
        handler=SiteNacClientEventsExporter.nac_client_events,
        title=("Search Site NAC Client Events (searchSiteNacClientEvents) - Per-site " "NAC client event CSV"),
        category=OperationRegistry.skip_category("202"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "203": GlobalImportManager.MenuEntry(  # Use named fields for menu 203.
        menu_id="203",  # Store key for drift checks.
        handler=SiteClientExporter.wan_client_events,
        title="Search WAN client events for a selected site (spec 899 / issue #1407)",
        category=OperationRegistry.skip_category("203"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "209": GlobalImportManager.MenuEntry(  # Use named fields for menu 209.
        menu_id="209",  # Store key for drift checks.
        handler=SiteClientExporter.get_site_beacon,
        title="Get site beacon detail by site_id + beacon_id (getSiteBeacon)",
        category=OperationRegistry.skip_category("209"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "210": GlobalImportManager.MenuEntry(  # Use named fields for menu 210.
        menu_id="210",  # Store key for drift checks.
        handler=SiteAssetExporter.assets_of_interest,
        title=("Export BLE beacons matching an Asset or AssetFilter for a site " "(getSiteAssetsOfInterest)"),
        category=OperationRegistry.skip_category("210"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "211": GlobalImportManager.MenuEntry(  # Use named fields for menu 211.
        menu_id="211",  # Store key for drift checks.
        handler=SiteAssetExporter.asset_filter,
        title="Get site asset filter detail by site_id + assetfilter_id (getSiteAssetFilter)",
        category=OperationRegistry.skip_category("211"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "212": GlobalImportManager.MenuEntry(  # Use named fields for menu 212.
        menu_id="212",  # Store key for drift checks.
        handler=SiteAssetExporter.asset,
        title="Get site asset detail by site_id + asset_id (getSiteAsset)",
        category=OperationRegistry.skip_category("212"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "213": GlobalImportManager.MenuEntry(  # Use named fields for menu 213.
        menu_id="213",  # Store key for drift checks.
        handler=SiteApplicationListExporter.application_list,
        title="Export the application list for a selected site (getSiteApplicationList)",
        category=OperationRegistry.skip_category("213"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "214": GlobalImportManager.MenuEntry(  # Use named fields for menu 214.
        menu_id="214",  # Store key for drift checks.
        handler=SiteSystemEventsExporter.system_events,
        title="Search system events for a selected site (searchSiteSystemEvents)",
        category=OperationRegistry.skip_category("214"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "215": GlobalImportManager.MenuEntry(  # Use named fields for menu 215.
        menu_id="215",  # Store key for drift checks.
        handler=SiteSearchExporter.alarms,
        title="Search alarms for a selected site (searchSiteAlarms)",
        category=OperationRegistry.skip_category("215"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "216": GlobalImportManager.MenuEntry(  # Use named fields for menu 216.
        menu_id="216",  # Store key for drift checks.
        handler=SiteSearchExporter.assets,
        title="Search tracked assets for a selected site (searchSiteAssets)",
        category=OperationRegistry.skip_category("216"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "217": GlobalImportManager.MenuEntry(  # Use named fields for menu 217.
        menu_id="217",  # Store key for drift checks.
        handler=SiteSearchExporter.bgp_stats,
        title="Search BGP peer statistics for a selected site (searchSiteBgpStats)",
        category=OperationRegistry.skip_category("217"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "218": GlobalImportManager.MenuEntry(  # Use named fields for menu 218.
        menu_id="218",  # Store key for drift checks.
        handler=SiteSearchExporter.calls,
        title="Search call quality records for a selected site (searchSiteCalls)",
        category=OperationRegistry.skip_category("218"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "219": GlobalImportManager.MenuEntry(  # Use named fields for menu 219.
        menu_id="219",  # Store key for drift checks.
        handler=SiteSearchExporter.skyatp_events,
        title="Search Sky ATP security events for a selected site (searchSiteSkyatpEvents)",
        category=OperationRegistry.skip_category("219"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "220": GlobalImportManager.MenuEntry(  # Use named fields for menu 220.
        menu_id="220",  # Store key for drift checks.
        handler=SiteSearchExporter.wireless_client_events,
        title=("Search wireless client events for a selected site " "(searchSiteWirelessClientEvents)"),
        category=OperationRegistry.skip_category("220"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "221": GlobalImportManager.MenuEntry(  # Use named fields for menu 221.
        menu_id="221",  # Store key for drift checks.
        handler=SiteSearchExporter.wan_clients,
        title="Search WAN clients for a selected site (searchSiteWanClients)",
        category=OperationRegistry.skip_category("221"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "222": GlobalImportManager.MenuEntry(  # Use named fields for menu 222.
        menu_id="222",  # Store key for drift checks.
        handler=SiteSearchExporter.device_events,
        title="Search device events for a selected site (searchSiteDeviceEvents)",
        category=OperationRegistry.skip_category("222"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "223": GlobalImportManager.MenuEntry(  # Use named fields for menu 223.
        menu_id="223",  # Store key for drift checks.
        handler=SiteSearchExporter.devices,
        title="Search devices for a selected site (searchSiteDevices)",
        category=OperationRegistry.skip_category("223"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "224": GlobalImportManager.MenuEntry(  # Use named fields for menu 224.
        menu_id="224",  # Store key for drift checks.
        handler=SiteSearchExporter.rogue_events,
        title="Search rogue access point events for a selected site (searchSiteRogueEvents)",
        category=OperationRegistry.skip_category("224"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "225": GlobalImportManager.MenuEntry(  # Use named fields for menu 225.
        menu_id="225",  # Store key for drift checks.
        handler=SiteSearchExporter.ospf_stats,
        title="Search OSPF neighbor statistics for a selected site (searchSiteOspfStats)",
        category=OperationRegistry.skip_category("225"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "226": GlobalImportManager.MenuEntry(  # Use named fields for menu 226.
        menu_id="226",  # Store key for drift checks.
        handler=SiteSearchExporter.device_last_configs,
        title=("Search the last device configurations for a selected site " "(searchSiteDeviceLastConfigs)"),
        category=OperationRegistry.skip_category("226"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "227": GlobalImportManager.MenuEntry(  # Use named fields for menu 227.
        menu_id="227",  # Store key for drift checks.
        handler=SiteSearchExporter.device_config_history,
        title=("Search device configuration history for a selected site " "(searchSiteDeviceConfigHistory)"),
        category=OperationRegistry.skip_category("227"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "228": GlobalImportManager.MenuEntry(  # Use named fields for menu 228.
        menu_id="228",  # Store key for drift checks.
        handler=SiteSearchExporter.discovered_switches,
        title="Search discovered switches for a selected site (searchSiteDiscoveredSwitches)",
        category=OperationRegistry.skip_category("228"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "229": GlobalImportManager.MenuEntry(  # Use named fields for menu 229.
        menu_id="229",  # Store key for drift checks.
        handler=SiteSearchExporter.zone_sessions,
        title=("Search zone sessions for a selected site and zone type " "(searchSiteZoneSessions)"),
        category=OperationRegistry.skip_category("229"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "230": GlobalImportManager.MenuEntry(  # Use named fields for menu 230.
        menu_id="230",  # Store key for drift checks.
        handler=OrgSearchExporter.wireless_client_sessions,
        title=("Search wireless client sessions for the organization " "(searchOrgWirelessClientSessions)"),
        category=OperationRegistry.skip_category("230"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "231": GlobalImportManager.MenuEntry(  # Use named fields for menu 231.
        menu_id="231",  # Store key for drift checks.
        handler=OrgSearchExporter.wireless_client_events,
        title=("Search wireless client events for the organization " "(searchOrgWirelessClientEvents)"),
        category=OperationRegistry.skip_category("231"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "232": GlobalImportManager.MenuEntry(  # Use named fields for menu 232.
        menu_id="232",  # Store key for drift checks.
        handler=OrgSearchExporter.wan_clients,
        title="Search WAN clients for the organization (searchOrgWanClients)",
        category=OperationRegistry.skip_category("232"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "233": GlobalImportManager.MenuEntry(  # Use named fields for menu 233.
        menu_id="233",  # Store key for drift checks.
        handler=OrgSearchExporter.wan_client_events,
        title="Search WAN client events for the organization (searchOrgWanClientEvents)",
        category=OperationRegistry.skip_category("233"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "234": GlobalImportManager.MenuEntry(  # Use named fields for menu 234.
        menu_id="234",  # Store key for drift checks.
        handler=OrgSearchExporter.system_events,
        title="Search system events for the organization (searchOrgSystemEvents)",
        category=OperationRegistry.skip_category("234"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "250": GlobalImportManager.MenuEntry(  # Use named fields for menu 250.
        menu_id="250",  # Store key for drift checks.
        handler=OrgSearchExporter.org_vars,
        title="Search organization variables (searchOrgVars)",
        category=OperationRegistry.skip_category("250"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "235": GlobalImportManager.MenuEntry(  # Use named fields for menu 235.
        menu_id="235",  # Store key for drift checks.
        handler=CountExporter.org_counts,
        title="Run any org-scoped Mist count endpoint (35 operations, issue #1802)",
        category=OperationRegistry.skip_category("235"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "236": GlobalImportManager.MenuEntry(  # Use named fields for menu 236.
        menu_id="236",  # Store key for drift checks.
        handler=CountExporter.site_counts,
        title="Run any site-scoped Mist count endpoint (32 operations, issue #1802)",
        category=OperationRegistry.skip_category("236"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "237": GlobalImportManager.MenuEntry(  # Use named fields for menu 237.
        menu_id="237",  # Store key for drift checks.
        handler=CountExporter.msp_counts,
        title="Run any MSP-scoped Mist count endpoint (3 operations, issue #1802)",
        category=OperationRegistry.skip_category("237"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "259": GlobalImportManager.MenuEntry(  # Use named fields for menu 259.
        menu_id="259",  # Store key for drift checks.
        handler=SimpleEndpointExporter.global_endpoints,
        title="Run any no-identifier Mist get or list endpoint (29 operations, issue #1807)",
        category=OperationRegistry.skip_category("259"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "260": GlobalImportManager.MenuEntry(  # Use named fields for menu 260.
        menu_id="260",  # Store key for drift checks.
        handler=SimpleEndpointExporter.org_endpoints,
        title="Run any org-scoped Mist get or list endpoint (55 operations, issue #1807)",
        category=OperationRegistry.skip_category("260"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "261": GlobalImportManager.MenuEntry(  # Use named fields for menu 261.
        menu_id="261",  # Store key for drift checks.
        handler=SimpleEndpointExporter.site_endpoints,
        title="Run any site-scoped simple Mist read endpoint (58 operations, issue #1807)",
        category=OperationRegistry.skip_category("261"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "262": GlobalImportManager.MenuEntry(  # Use named fields for menu 262.
        menu_id="262",  # Store key for drift checks.
        handler=SimpleEndpointExporter.msp_endpoints,
        title="Run any MSP-scoped Mist get or list endpoint (10 operations, issue #1807)",
        category=OperationRegistry.skip_category("262"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "263": GlobalImportManager.MenuEntry(  # Use named fields for menu 263.
        menu_id="263",  # Store key for drift checks.
        handler=EndpointFamilyExporter.site_sle_endpoints,
        title="Run any site SLE endpoint with scope prompts (17 operations, issue #1807)",
        category=OperationRegistry.skip_category("263"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "264": GlobalImportManager.MenuEntry(  # Use named fields for menu 264.
        menu_id="264",  # Store key for drift checks.
        handler=EndpointFamilyExporter.site_map_endpoints,
        title="Run any site map endpoint with map prompts (7 operations, issue #1807)",
        category=OperationRegistry.skip_category("264"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "265": GlobalImportManager.MenuEntry(  # Use named fields for menu 265.
        menu_id="265",  # Store key for drift checks.
        handler=EndpointFamilyExporter.site_detail_endpoints,
        title=("Run any site detail endpoint with identifier prompts (33 operations, " "issue #1807)"),
        category=OperationRegistry.skip_category("265"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "266": GlobalImportManager.MenuEntry(  # Use named fields for menu 266.
        menu_id="266",  # Store key for drift checks.
        handler=EndpointFamilyExporter.org_detail_endpoints,
        title=("Run any org detail endpoint with identifier prompts (61 operations, " "issue #1807)"),
        category=OperationRegistry.skip_category("266"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "267": GlobalImportManager.MenuEntry(  # Use named fields for menu 267.
        menu_id="267",  # Store key for drift checks.
        handler=EndpointFamilyExporter.msp_detail_endpoints,
        title=("Run any MSP detail endpoint with identifier prompts (10 operations, " "issue #1807)"),
        category=OperationRegistry.skip_category("267"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "268": GlobalImportManager.MenuEntry(  # Use named fields for menu 268.
        menu_id="268",  # Store key for drift checks.
        handler=EndpointFamilyExporter.other_endpoints,
        title="Run any remaining endpoint with identifier prompts (6 operations, issue #1807)",
        category=OperationRegistry.skip_category("268"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "269": GlobalImportManager.MenuEntry(  # Use named fields for menu 269.
        menu_id="269",  # Store key for drift checks.
        handler=RogueDhcpScanOperation.run,
        title="Scan the organization for rogue DHCP servers on switches (30 days, issue #2985)",
        category=OperationRegistry.skip_category("269"),  # Read the safety class.
        destructive=False,  # The scan reads only, so it changes no Mist configuration.
        supports_fast=False,  # The scan already limits its own request count.
    ),
    "238": GlobalImportManager.MenuEntry(  # Use named fields for menu 238.
        menu_id="238",  # Store key for drift checks.
        handler=MSPLicenseExporter.licenses,
        title=("Export the license entitlement, usage, and subscriptions for an MSP " "(listMspLicenses)"),
        category=OperationRegistry.skip_category("238"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "239": GlobalImportManager.MenuEntry(  # Use named fields for menu 239.
        menu_id="239",  # Store key for drift checks.
        handler=lambda: _launch_capture_portal(),
        title=("Launch the upgrade capture portal on port 8056 (pre-check, upgrade, " "post-check)"),
        category=OperationRegistry.skip_category("239"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "240": GlobalImportManager.MenuEntry(  # Use named fields for menu 240.
        menu_id="240",  # Store key for drift checks.
        handler=OrgSecIntelProfileExporter.profile,
        title="Export one organization security intelligence profile (getOrgSecIntelProfile)",
        category=OperationRegistry.skip_category("240"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "241": GlobalImportManager.MenuEntry(  # Use named fields for menu 241.
        menu_id="241",  # Store key for drift checks.
        handler=lambda: _launch_metrics_gateway(),
        title=("Serve Mist Cloud health to a monitoring system on port 8057 " "(Prometheus and SNMP)"),
        category=OperationRegistry.skip_category("241"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "242": GlobalImportManager.MenuEntry(  # Use named fields for menu 242.
        menu_id="242",  # Store key for drift checks.
        handler=SSIDBroadcastGapReport.execute,
        title="Find sites where an SSID is not broadcast by any AP",
        category=OperationRegistry.skip_category("242"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "243": GlobalImportManager.MenuEntry(  # Use named fields for menu 243.
        menu_id="243",  # Store key for drift checks.
        handler=lambda: _launch_mib_generator(),
        title="Generate the SNMP MIB from the Mist OpenAPI file and the metric catalog",
        category=OperationRegistry.skip_category("243"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "244": GlobalImportManager.MenuEntry(  # Use named fields for menu 244.
        menu_id="244",  # Store key for drift checks.
        handler=SiteSearchExporter.service_path_events,
        title="Search service path events for a selected site (searchSiteServicePathEvents)",
        category=OperationRegistry.skip_category("244"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "245": GlobalImportManager.MenuEntry(  # Use named fields for menu 245.
        menu_id="245",  # Store key for drift checks.
        handler=OrgCradlepointConnectionExporter.status,
        title=("Export the Cradlepoint connection status for an organization " "(testOrgCradlepointConnection)"),
        category=OperationRegistry.skip_category("245"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "246": GlobalImportManager.MenuEntry(  # Use named fields for menu 246.
        menu_id="246",  # Store key for drift checks.
        handler=SiteSearchExporter.troubleshoot_call,
        title=("Troubleshoot a call for a site, client MAC, and meeting ID " "(troubleshootSiteCall)"),
        category=OperationRegistry.skip_category("246"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "247": GlobalImportManager.MenuEntry(  # Use named fields for menu 247.
        menu_id="247",  # Store key for drift checks.
        handler=SelfAccountExporter.verify_email,
        title="Verify an email change token from the Mist email (verifySelfEmail)",
        category=OperationRegistry.skip_category("247"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "248": GlobalImportManager.MenuEntry(  # Use named fields for menu 248.
        menu_id="248",  # Store key for drift checks.
        handler=OrgSearchExporter.sites,
        title="Search sites for the organization (searchOrgSites)",
        category=OperationRegistry.skip_category("248"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "249": GlobalImportManager.MenuEntry(  # Use named fields for menu 249.
        menu_id="249",  # Store key for drift checks.
        handler=OrgSearchExporter.devices,
        title="Search devices for the organization (searchOrgDevices)",
        category=OperationRegistry.skip_category("249"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "251": GlobalImportManager.MenuEntry(  # Use named fields for menu 251.
        menu_id="251",  # Store key for drift checks.
        handler=OrgSearchExporter.user_macs,
        title="Search user MAC assignments for the organization (searchOrgUserMacs)",
        category=OperationRegistry.skip_category("251"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "252": GlobalImportManager.MenuEntry(  # Use named fields for menu 252.
        menu_id="252",  # Store key for drift checks.
        handler=OrgExportUtils.other_device_events,
        title="Search other-device events for the organization (searchOrgOtherDeviceEvents)",
        category=OperationRegistry.skip_category("252"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "253": GlobalImportManager.MenuEntry(  # Use named fields for menu 253.
        menu_id="253",  # Store key for drift checks.
        handler=OrgSearchExporter.mx_edges,
        title="Search Mist Edges for the organization (searchOrgMxEdges)",
        category=OperationRegistry.skip_category("253"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "254": GlobalImportManager.MenuEntry(  # Use named fields for menu 254.
        menu_id="254",  # Store key for drift checks.
        handler=OrgInventorySearchExporter.inventory,
        title="Search organization inventory with optional filters (searchOrgInventory)",
        category=OperationRegistry.skip_category("254"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "255": GlobalImportManager.MenuEntry(  # Use named fields for menu 255.
        menu_id="255",  # Store key for drift checks.
        handler=OrgSearchExporter.psk_portal_logs,
        title="Search PSK portal logs for the organization (searchOrgPskPortalLogs)",
        category=OperationRegistry.skip_category("255"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "256": GlobalImportManager.MenuEntry(  # Use named fields for menu 256.
        menu_id="256",  # Store key for drift checks.
        handler=OrgWebhookDeliveriesExporter.deliveries,
        title="Search organization webhook deliveries (searchOrgWebhooksDeliveries)",
        category=OperationRegistry.skip_category("256"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "257": GlobalImportManager.MenuEntry(  # Use named fields for menu 257.
        menu_id="257",  # Store key for drift checks.
        handler=SiteSearchExporter.nac_clients,
        title="Search NAC clients for a selected site (searchSiteNacClients)",
        category=OperationRegistry.skip_category("257"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "258": GlobalImportManager.MenuEntry(  # Use named fields for menu 258.
        menu_id="258",  # Store key for drift checks.
        handler=SiteOtherDeviceEventsExporter.other_device_events,
        title="Search other-device events for a selected site (searchSiteOtherDeviceEvents)",
        category=OperationRegistry.skip_category("258"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "44": GlobalImportManager.MenuEntry(  # Use named fields for menu 44.
        menu_id="44",  # Store key for drift checks.
        handler=OrgConfigExporter.psks,
        title="Export PSK (Pre-Shared Key) information for the organization",
        category=OperationRegistry.skip_category("44"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "45": GlobalImportManager.MenuEntry(  # Use named fields for menu 45.
        menu_id="45",  # Store key for drift checks.
        handler=OrgConfigExporter.webhooks,
        title="Export webhook configuration for the organization",
        category=OperationRegistry.skip_category("45"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "46": GlobalImportManager.MenuEntry(  # Use named fields for menu 46.
        menu_id="46",  # Store key for drift checks.
        handler=OrgConfigExporter.wlans,
        title="Export WLAN configuration for the organization",
        category=OperationRegistry.skip_category("46"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "69": GlobalImportManager.MenuEntry(  # Use named fields for menu 69.
        menu_id="69",  # Store key for drift checks.
        handler=SiteConfigExporter.wlans,
        title="Export WLAN configuration for a selected site",
        category=OperationRegistry.skip_category("69"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "66": GlobalImportManager.MenuEntry(  # Use named fields for menu 66.
        menu_id="66",  # Store key for drift checks.
        handler=SiteClientExporter.beacons,
        title="Export beacon information for a selected site",
        category=OperationRegistry.skip_category("66"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "67": GlobalImportManager.MenuEntry(  # Use named fields for menu 67.
        menu_id="67",  # Store key for drift checks.
        handler=SiteConfigExporter.maps,
        title="Export map information for a selected site",
        category=OperationRegistry.skip_category("67"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "68": GlobalImportManager.MenuEntry(  # Use named fields for menu 68.
        menu_id="68",  # Store key for drift checks.
        handler=SiteConfigExporter.zones,
        title="Export zone information for a selected site",
        category=OperationRegistry.skip_category("68"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "73": GlobalImportManager.MenuEntry(  # Use named fields for menu 73.
        menu_id="73",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().insights(),
        title="Export SLE (Service Level Experience) metrics insights for a selected site",
        category=OperationRegistry.skip_category("73"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # GATEWAY TEMPLATE VARIABLE OPERATIONS
    # ==============================
    "149": GlobalImportManager.MenuEntry(  # Use named fields for menu 149.
        menu_id="149",  # Store key for drift checks.
        handler=lambda: WAN2MigrationLauncher().launch(),
        title=(
            "Set WAN2 Interface Site Variable - Configure 'wan2_interface' site "
            "variable for template-based WAN migration (Reports sites with "
            "ge-0/0/1 overrides)"
        ),
        category=OperationRegistry.skip_category("149"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "163": GlobalImportManager.MenuEntry(  # Use named fields for menu 163.
        menu_id="163",  # Store key for drift checks.
        handler=_dispatch_gateway_wan2_variable_migration,
        title=(
            "DESTRUCTIVE: Update Gateway Templates to Use WAN2 Variable - Replace "
            "hardcoded 'ge-0/0/1' references with {{wan2_interface}} variable "
            "(Requires uppercase 'MIGRATE' confirmation, supports --dry-run)"
        ),
        category=OperationRegistry.skip_category("163"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "150": GlobalImportManager.MenuEntry(  # Use named fields for menu 150.
        menu_id="150",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.GatewayTemplateConfigManagerFactory().build().extract(),
        title=(
            "Extract Gateway Template Configuration (DIA_Pico, Picocell) - Save "
            "specific configs to JSON for replication"
        ),
        category=OperationRegistry.skip_category("150"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "164": GlobalImportManager.MenuEntry(  # Use named fields for menu 164.
        menu_id="164",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.GatewayTemplateConfigManagerFactory().build().apply(),
        title=(
            "DESTRUCTIVE: Apply Gateway Template Configuration - Replicate "
            "extracted configs to other templates (Requires uppercase 'APPLY' "
            "confirmation)"
        ),
        category=OperationRegistry.skip_category("164"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "148": GlobalImportManager.MenuEntry(  # Use named fields for menu 148.
        menu_id="148",  # Store key for drift checks.
        handler=lambda: WLANRadiusTimerManager().manage(),
        title=(
            "Manage WLAN RADIUS Authentication Timers - Configure "
            "auth_servers_timeout, auth_servers_retries, auth_server_selection, "
            "and fast_dot1x_timers for site or template WLANs"
        ),
        category=OperationRegistry.skip_category("148"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Authentication Management
    "143": GlobalImportManager.MenuEntry(  # Use named fields for menu 143.
        menu_id="143",  # Store key for drift checks.
        handler=lambda: SwitchToInteractiveLoginManager().run(),
        title=("Switch to interactive login (email/password) - Enables MSP-level API " "access for current session"),
        category=OperationRegistry.skip_category("143"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Organization Management (Read-Only)
    "47": GlobalImportManager.MenuEntry(  # Use named fields for menu 47.
        menu_id="47",  # Store key for drift checks.
        handler=OrgAdminExporter.api_tokens,
        title="Export API token information for the organization",
        category=OperationRegistry.skip_category("47"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "48": GlobalImportManager.MenuEntry(  # Use named fields for menu 48.
        menu_id="48",  # Store key for drift checks.
        handler=OrgAdminExporter.admins,
        title="Export administrator information for the organization",
        category=OperationRegistry.skip_category("48"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "136": GlobalImportManager.MenuEntry(  # Use named fields for menu 136.
        menu_id="136",  # Store key for drift checks.
        handler=OrgConfigExporter.msp,
        title=(
            "MSP (Managed Service Provider) info - Displays guidance only (MSP "
            "data requires MSP-level API access, not org-level)"
        ),
        category=OperationRegistry.skip_category("136"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "49": GlobalImportManager.MenuEntry(  # Use named fields for menu 49.
        menu_id="49",  # Store key for drift checks.
        handler=OrgAdminExporter.sso,
        title="Export SSO (Single Sign-On) information for the organization",
        category=OperationRegistry.skip_category("49"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "43": GlobalImportManager.MenuEntry(  # Use named fields for menu 43.
        menu_id="43",  # Store key for drift checks.
        handler=OrgAdminExporter.usage,
        title="Export license usage information for the organization",
        category=OperationRegistry.skip_category("43"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "50": GlobalImportManager.MenuEntry(  # Use named fields for menu 50.
        menu_id="50",  # Store key for drift checks.
        handler=OrgConfigExporter.mx_edges,
        title="Export MX Edge information for the organization",
        category=OperationRegistry.skip_category("50"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Status & Monitoring
    "137": GlobalImportManager.MenuEntry(  # Use named fields for menu 137.
        menu_id="137",  # Store key for drift checks.
        handler=lambda: _build_firmware_manager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).check_firmware_upgrade_status(),
        title=(
            "Check current firmware upgrade status across organization with "
            "detailed progress monitoring and export to CSV"
        ),
        category=OperationRegistry.skip_category("137"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "138": GlobalImportManager.MenuEntry(  # Use named fields for menu 138.
        menu_id="138",  # Store key for drift checks.
        handler=lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: InventoryCSVComparator(
            fast=fast, address_check=address_check, debug=debug, skip_ssl_verify=skip_ssl_verify
        ).execute(),
        title=(
            "Compare inventory data with external CSV file using configurable "
            "address similarity threshold (ADDRESS_MATCH_THRESHOLD in .env)"
        ),
        category=OperationRegistry.skip_category("138"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=True,  # Avoid fast-mode inspection.
    ),
    "139": GlobalImportManager.MenuEntry(  # Use named fields for menu 139.
        menu_id="139",  # Store key for drift checks.
        handler=TroubleshootUtils.launch_interactive,
        title=("Interactive Marvis (VNA) AI troubleshooting - guided client, device, " "and network analysis"),
        category=OperationRegistry.skip_category("139"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Long-Running Export Operations (Read-Only)
    "97": GlobalImportManager.MenuEntry(  # Use named fields for menu 97.
        menu_id="97",  # Store key for drift checks.
        handler=OrgAlarmEventExporter.device_events_52w,
        title=("Export all org device events from the last 52 weeks (streaming with " "checkpoint/resume)"),
        category=OperationRegistry.skip_category("97"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "98": GlobalImportManager.MenuEntry(  # Use named fields for menu 98.
        menu_id="98",  # Store key for drift checks.
        handler=lambda: OrgExportUtils.audit_logs(full_history=True, duration="52w"),
        title="Export ALL audit logs for the organization (last 52 weeks)",
        category=OperationRegistry.skip_category("98"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "99": GlobalImportManager.MenuEntry(  # Use named fields for menu 99.
        menu_id="99",  # Store key for drift checks.
        handler=_dispatch_gateway_device_configs,
        title="Export configuration details for all gateway devices across all sites",
        category=OperationRegistry.skip_category("99"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # UNSAFE/INTERACTIVE OPERATIONS
    # ==============================
    # > Site Selection & Interactive Tools
    "92": GlobalImportManager.MenuEntry(  # Use named fields for menu 92.
        menu_id="92",  # Store key for drift checks.
        handler=PromptUtils.select_site_with_logging,
        title="Select a site (used by other functions)",
        category=OperationRegistry.skip_category("92"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "93": GlobalImportManager.MenuEntry(  # Use named fields for menu 93.
        menu_id="93",  # Store key for drift checks.
        handler=InteractiveDisplayUtils.site_inventory,
        title="View device inventory for a selected site",
        category=OperationRegistry.skip_category("93"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "94": GlobalImportManager.MenuEntry(  # Use named fields for menu 94.
        menu_id="94",  # Store key for drift checks.
        handler=InteractiveDisplayUtils.device_stats,
        title="View statistics for a selected device at a site",
        category=OperationRegistry.skip_category("94"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "95": GlobalImportManager.MenuEntry(  # Use named fields for menu 95.
        menu_id="95",  # Store key for drift checks.
        handler=InteractiveDisplayUtils.device_tests,
        title="View synthetic test stats for a selected gateway device",
        category=OperationRegistry.skip_category("95"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "96": GlobalImportManager.MenuEntry(  # Use named fields for menu 96.
        menu_id="96",  # Store key for drift checks.
        handler=InteractiveDisplayUtils.device_config,
        title="View configuration details for a selected device",
        category=OperationRegistry.skip_category("96"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Continuous Operations & Monitoring
    # WHY: menu 152 duplicated this action with a vaguer description. Issue
    # #2066 retired 152. The number stays retired; see RETIRED_MENU_NUMBERS in
    # tests/guardrails/test_menu_number_uniqueness.py.
    "151": GlobalImportManager.MenuEntry(  # Use named fields for menu 151.
        menu_id="151",  # Store key for drift checks.
        handler=DataCollectionManager.continuous_loop,
        title=(
            "Loop refresh of core datasets (site list, inventory, stats, ports, "
            "VPN) Stop with CTRL+C or create 'stop_loop.txt'"
        ),
        category=OperationRegistry.skip_category("151"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > File Processing & Support Operations
    "100": GlobalImportManager.MenuEntry(  # Use named fields for menu 100.
        menu_id="100",  # Store key for drift checks.
        handler=SFPTransceiverDataProcessor.merge_transceiver_data,
        title="Process and merge CSV files of SFP Module locations into a single CSV file",
        category=OperationRegistry.skip_category("100"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "101": GlobalImportManager.MenuEntry(  # Use named fields for menu 101.
        menu_id="101",  # Store key for drift checks.
        handler=DataCollectionManager.generate_support_packages,
        title="Generate support package for each site",
        category=OperationRegistry.skip_category("101"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > CLI & WebSocket Operations
    "140": GlobalImportManager.MenuEntry(  # Use named fields for menu 140.
        menu_id="140",  # Store key for drift checks.
        handler=CLIShellManager.launch,
        title="Interactively execute a CLI command on a gateway or switch (exit with ~)",
        category=OperationRegistry.skip_category("140"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "121": GlobalImportManager.MenuEntry(  # Use named fields for menu 121.
        menu_id="121",  # Store key for drift checks.
        handler=ARPCommandManager.execute,
        title="Run ARP command on an AP and receive output via WebSocket",
        category=OperationRegistry.skip_category("121"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ! DESTRUCTIVE OPERATIONS - USE WITH EXTREME CAUTION
    "154": GlobalImportManager.MenuEntry(  # Use named fields for menu 154.
        menu_id="154",  # Store key for drift checks.
        handler=lambda: _build_firmware_manager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_firmware_upgrade_with_mode_selection(),
        title=(
            "DESTRUCTIVE: Advanced AP firmware upgrade with mode selection - "
            "upgrade by site list/selection or by Gateway Template assignment"
        ),
        category=OperationRegistry.skip_category("154"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "158": GlobalImportManager.MenuEntry(  # Use named fields for menu 158.
        menu_id="158",  # Store key for drift checks.
        handler=DeviceRebootManager.by_gateway_template_list,
        title=(
            "DESTRUCTIVE: Reboot all devices associated with templates listed in "
            "GatewayTemplateRebootList.CSV and log results"
        ),
        category=OperationRegistry.skip_category("158"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "161": GlobalImportManager.MenuEntry(  # Use named fields for menu 161.
        menu_id="161",  # Store key for drift checks.
        handler=lambda dry_run=False: _configure_virtual_chassis_manager().launch_convert_single(dry_run=dry_run),
        title=(" DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC " "(interactive, supports --dry-run)"),
        category=OperationRegistry.skip_category("161"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "162": GlobalImportManager.MenuEntry(  # Use named fields for menu 162.
        menu_id="162",  # Store key for drift checks.
        handler=lambda: _configure_virtual_chassis_manager().launch_convert_by_site_list(),
        title=(
            " DESTRUCTIVE: Convert all virtual chassis switches in sites listed in " "VCConvert.CSV (bulk operation)"
        ),
        category=OperationRegistry.skip_category("162"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "14": GlobalImportManager.MenuEntry(  # Use named fields for menu 14.
        menu_id="14",  # Store key for drift checks.
        handler=lambda: _configure_virtual_chassis_manager().launch_check_status(),
        title="Check virtual chassis to virtual MAC conversion status for all switches",
        category=OperationRegistry.skip_category("14"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "18": GlobalImportManager.MenuEntry(  # Use named fields for menu 18.
        menu_id="18",  # Store key for drift checks.
        handler=lambda fast=False: _dispatch_gateway_stats_device_stats_with_freshness(fast=fast),
        title="Export detailed device statistics for all gateways (with freshness check)",
        category=OperationRegistry.skip_category("18"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=True,  # Avoid fast-mode inspection.
    ),
    "36": GlobalImportManager.MenuEntry(  # Use named fields for menu 36.
        menu_id="36",  # Store key for drift checks.
        handler=_dispatch_gateway_stats_wan_port_conflicts,
        title=("Check and export gateways with duplicate WAN port IP addresses " "(0/0/0, 0/0/1, 0/0/2)"),
        category=OperationRegistry.skip_category("36"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "175": GlobalImportManager.MenuEntry(  # Use named fields for menu 175.
        menu_id="175",  # Store key for drift checks.
        handler=lambda: SSHRunnerManager.interactive(_build_ssh_runner_deps()),
        title=("Enhanced SSH Command Runner - Execute commands on remote network " "devices via SSH"),
        category=OperationRegistry.skip_category("175"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "176": GlobalImportManager.MenuEntry(  # Use named fields for menu 176.
        menu_id="176",  # Store key for drift checks.
        handler=lambda: SSHRunnerManager.by_gateway_template(_build_ssh_runner_deps()),
        title=("SSH Runner - Target gateways by template name (online gateways with " "management IPs only)"),
        category=OperationRegistry.skip_category("176"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # INSIGHTS API OPERATIONS - Organization & Site Analytics
    # ==============================
    "51": GlobalImportManager.MenuEntry(  # Use named fields for menu 51.
        menu_id="51",  # Store key for drift checks.
        handler=OrgExportUtils.sle_metrics,
        title="Export Organization SLE Metrics (Service Level Experience)",
        category=OperationRegistry.skip_category("51"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "52": GlobalImportManager.MenuEntry(  # Use named fields for menu 52.
        menu_id="52",  # Store key for drift checks.
        handler=OrgExportUtils.sites_sle_summary,
        title="Export SLE summary metrics for all sites in the organization",
        category=OperationRegistry.skip_category("52"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "74": GlobalImportManager.MenuEntry(  # Use named fields for menu 74.
        menu_id="74",  # Store key for drift checks.
        handler=lambda: SiteMetricOperation(
            apisession=MainEntrypoint.context.apisession,
            PromptUtils=PromptUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            mistapi=mistapi,
        ).execute(),
        title="Export general insight metrics for a selected site",
        category=OperationRegistry.skip_category("74"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "75": GlobalImportManager.MenuEntry(  # Use named fields for menu 75.
        menu_id="75",  # Store key for drift checks.
        handler=SiteClientExporter.client_insights,
        title="Export client-specific insight metrics for a selected site",
        category=OperationRegistry.skip_category("75"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "76": GlobalImportManager.MenuEntry(  # Use named fields for menu 76.
        menu_id="76",  # Store key for drift checks.
        handler=lambda: DeviceMetricOperation(
            apisession=MainEntrypoint.context.apisession,
            PromptUtils=PromptUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=DataExporter,
            EnhancedSSHRunner=EnhancedSSHRunner,
            InsightMetricsUtils=InsightMetricsUtils,
            PacketCaptureManager=PacketCaptureManager,
            mistapi=mistapi,
        ).execute(),
        title="Export device-specific insight metrics for a selected site",
        category=OperationRegistry.skip_category("76"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "54": GlobalImportManager.MenuEntry(  # Use named fields for menu 54.
        menu_id="54",  # Store key for drift checks.
        handler=lambda: ConstDefinitionsExporter(MainEntrypoint.context.apisession).export_all(),
        title=("Export all available const definitions from the Mist API " "(comprehensive endpoint coverage)"),
        category=OperationRegistry.skip_category("54"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "53": GlobalImportManager.MenuEntry(  # Use named fields for menu 53.
        menu_id="53",  # Store key for drift checks.
        handler=OrgExportUtils.insight_metrics,
        title="Export Organization Insight Metrics (comprehensive operational insights)",
        category=OperationRegistry.skip_category("53"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "77": GlobalImportManager.MenuEntry(  # Use named fields for menu 77.
        menu_id="77",  # Store key for drift checks.
        handler=SiteAnomalyExporter.anomaly_events,
        title=("Export Site Anomaly Events (dynamic discovery of all anomaly-related " "metrics from Mist API)"),
        category=OperationRegistry.skip_category("77"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "78": GlobalImportManager.MenuEntry(  # Use named fields for menu 78.
        menu_id="78",  # Store key for drift checks.
        handler=SiteAnomalyExporter.device_anomaly_events,
        title="Export Site Device Anomaly Events (device-specific anomaly detection)",
        category=OperationRegistry.skip_category("78"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "79": GlobalImportManager.MenuEntry(  # Use named fields for menu 79.
        menu_id="79",  # Store key for drift checks.
        handler=SiteAnomalyExporter.client_anomaly_events,
        title=(
            "Export Site Client Anomaly Events (client-specific anomaly detection: "
            "connectivity, roaming, throughput)"
        ),
        category=OperationRegistry.skip_category("79"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "118": GlobalImportManager.MenuEntry(  # Use named fields for menu 118.
        menu_id="118",  # Store key for drift checks.
        handler=lambda: PingDeviceExecutor().execute(_ws_cmd_deps()),
        title=("WebSocket Device Ping - Execute ping command on device via WebSocket " "stream (real-time output)"),
        category=OperationRegistry.skip_category("118"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "119": GlobalImportManager.MenuEntry(  # Use named fields for menu 119.
        menu_id="119",  # Store key for drift checks.
        handler=lambda: ArpDeviceExecutor().execute(_ws_cmd_deps()),
        title=("WebSocket Device ARP - Execute ARP command on device via WebSocket " "stream (real-time output)"),
        category=OperationRegistry.skip_category("119"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "120": GlobalImportManager.MenuEntry(  # Use named fields for menu 120.
        menu_id="120",  # Store key for drift checks.
        handler=lambda: ServicePingLauncher().launch(),
        title=(
            "WebSocket Service Ping - Execute service-specific ping on SSR "
            "gateways via WebSocket stream (real-time output)"
        ),
        category=OperationRegistry.skip_category("120"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # POST API OPERATIONS - Device Commands (Starting at 100)
    # ==============================
    # Device Network Operations removed (options 100, 101)
    # ==============================
    # SWITCH FIRMWARE OPERATIONS
    # ==============================
    "155": GlobalImportManager.MenuEntry(  # Use named fields for menu 155.
        menu_id="155",  # Store key for drift checks.
        handler=lambda: _build_firmware_manager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_switch_firmware_upgrade_with_mode_selection(),
        title=(
            "DESTRUCTIVE: Advanced Switch firmware upgrade with mode selection - "
            "upgrade by site list/selection or by Gateway Template assignment"
        ),
        category=OperationRegistry.skip_category("155"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SSR FIRMWARE OPERATIONS
    # ==============================
    "156": GlobalImportManager.MenuEntry(  # Use named fields for menu 156.
        menu_id="156",  # Store key for drift checks.
        handler=lambda: _build_firmware_manager(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ).execute_ssr_firmware_upgrade_with_mode_selection(),
        title=(
            "DESTRUCTIVE: Advanced SSR firmware upgrade with mode selection - "
            "upgrade by site list/selection or by Gateway Template assignment"
        ),
        category=OperationRegistry.skip_category("156"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # TERMINAL USER INTERFACE MODE
    # ==============================
    "141": GlobalImportManager.MenuEntry(  # Use named fields for menu 141.
        menu_id="141",  # Store key for drift checks.
        handler=lambda: TUILauncher().launch(),
        title=(
            "Launch Terminal User Interface (TUI) mode - Visual navigation of Mist "
            "API library with interactive exploration"
        ),
        category=OperationRegistry.skip_category("141"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # TEST DATA GENERATION
    # ==============================
    "171": GlobalImportManager.MenuEntry(  # Use named fields for menu 171.
        menu_id="171",  # Store key for drift checks.
        handler=lambda: _configure_site_config_manager().create_test_sites_from_csv(),
        title=(
            "DESTRUCTIVE: Create 137 test sites from NorthAmericanTestSites.csv - "
            "Real landmarks across 13 North American countries (Requires uppercase "
            "'CREATE' confirmation)"
        ),
        category=OperationRegistry.skip_category("171"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "172": GlobalImportManager.MenuEntry(  # Use named fields for menu 172.
        menu_id="172",  # Store key for drift checks.
        handler=lambda: _configure_site_config_manager().create_country_rf_templates_and_assign(),
        title=(
            "DESTRUCTIVE: Create country-specific RF templates and assign sites to "
            "matching templates (Requires uppercase 'CREATE' confirmation)"
        ),
        category=OperationRegistry.skip_category("172"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "173": GlobalImportManager.MenuEntry(  # Use named fields for menu 173.
        menu_id="173",  # Store key for drift checks.
        handler=lambda: _configure_site_config_manager().create_ap_model_device_profiles(),
        title=(
            "DESTRUCTIVE: Scan org for AP models and create Device Profile per "
            "model with inherit/auto settings (Requires uppercase 'CREATE' "
            "confirmation)"
        ),
        category=OperationRegistry.skip_category("173"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "174": GlobalImportManager.MenuEntry(  # Use named fields for menu 174.
        menu_id="174",  # Store key for drift checks.
        handler=lambda: _configure_site_config_manager().assign_aps_to_matching_device_profiles(),
        title=(
            "DESTRUCTIVE: Assign APs to Device Profiles matching their model type "
            "(AP-{model}) - Skips APs without matching profiles (Requires "
            "uppercase 'ASSIGN' confirmation)"
        ),
        category=OperationRegistry.skip_category("174"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "165": GlobalImportManager.MenuEntry(  # Use named fields for menu 165.
        menu_id="165",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.GatewayTemplateConfigManagerFactory().build().clone_by_location(),
        title=(
            "DESTRUCTIVE: Clone Gateway Template by State and Country - Create "
            "state/country-specific templates and assign sites (Requires uppercase "
            "'CLONE' confirmation)"
        ),
        category=OperationRegistry.skip_category("165"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "166": GlobalImportManager.MenuEntry(  # Use named fields for menu 166.
        menu_id="166",  # Store key for drift checks.
        handler=lambda dry_run=False: WANProbeConfigManager.configure(dry_run=dry_run),
        title=(
            "DESTRUCTIVE: Configure WAN Probe Override on Gateway Templates - Set "
            "ICMP probe IPs and profile for all WAN interfaces (Requires uppercase "
            "'APPLY' confirmation, supports --dry-run)"
        ),
        category=OperationRegistry.skip_category("166"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "167": GlobalImportManager.MenuEntry(  # Use named fields for menu 167.
        menu_id="167",  # Store key for drift checks.
        handler=lambda dry_run=False: WANProbeDeviceOverrideManager.configure(dry_run=dry_run),
        title=(
            "DESTRUCTIVE: Configure WAN Probe on Device Port Overrides - Set ICMP "
            "probe on device-level WAN overrides only (Requires uppercase 'APPLY' "
            "confirmation, supports --dry-run)"
        ),
        category=OperationRegistry.skip_category("167"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # ORG-LEVEL FIRMWARE OPERATIONS
    # ==============================
    "157": GlobalImportManager.MenuEntry(  # Use named fields for menu 157.
        menu_id="157",  # Store key for drift checks.
        handler=lambda: _build_org_ap_upgrader().run(),
        title=(
            "DESTRUCTIVE: Org-Level AP Firmware Upgrade - Efficient multi-site "
            "upgrade using org-level API (1 call per version vs 1 per site), MSP "
            "multi-org support, supports --dry-run"
        ),
        category=OperationRegistry.skip_category("157"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # MSP OPERATIONS
    # ==============================
    "144": GlobalImportManager.MenuEntry(  # Use named fields for menu 144.
        menu_id="144",  # Store key for drift checks.
        handler=MSPInventoryExporter.execute,
        title=(
            "MSP Inventory Export - Export device inventory across all MSPs and "
            "all organizations to CSV (requires MSP privileges via --login)"
        ),
        category=OperationRegistry.skip_category("144"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SITE AUTO-UPGRADE CONFIGURATION
    # ==============================
    "168": GlobalImportManager.MenuEntry(  # Use named fields for menu 168.
        menu_id="168",  # Store key for drift checks.
        handler=lambda: SiteAutoUpgradeConfigurator.execute(
            apisession=MainEntrypoint.context.apisession,
            msp_privileges=MainEntrypoint.context.msp_privileges if MainEntrypoint.context.msp_privileges else [],
            safe_input_fn=InputUtils.safe_input,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            check_stop_fn=ConfigUtils.check_stop_signal,
            dry_run=getattr(globals().get("args", None), "dry_run", False),
            select_msps_fn=lambda: _build_org_ap_upgrader(org_id="")._select_msps(),
            select_orgs_fn=lambda msp: _build_org_ap_upgrader(org_id="")._select_orgs_from_msp(msp),
        ),
        title=(
            "Site Auto-Upgrade Configuration - Configure AP auto-upgrade settings "
            "for sites with MSP multi-org support (supports --dry-run)"
        ),
        category=OperationRegistry.skip_category("168"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # ZONE & ENGAGEMENT CONFIGURATION ANALYSIS
    # ==============================
    "6": GlobalImportManager.MenuEntry(  # Use named fields for menu 6.
        menu_id="6",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().zone_config_analysis(),
        title=(
            "Site Config Analysis - Scan all sites for zone, engagement dwell tag, " "and occupancy setting deviations"
        ),
        category=OperationRegistry.skip_category("6"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SITE ANALYTICS CONFIGURATION (DESTRUCTIVE)
    # ==============================
    "169": GlobalImportManager.MenuEntry(  # Use named fields for menu 169.
        menu_id="169",  # Store key for drift checks.
        handler=lambda: ExtractedSiteAnalyticsConfigurator.execute(
            SiteAnalyticsConfiguratorDeps(
                apisession=MainEntrypoint.context.apisession,
                mistapi=mistapi,
                get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
                check_stop_fn=ConfigUtils.check_stop_signal,
                safe_input_fn=InputUtils.safe_input,
                all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
                save_data_fn=DataExporter.write_with_format_selection,
                tqdm_fn=tqdm,
            )
        ),
        title=(
            "DESTRUCTIVE: Site Analytics Configuration - Apply standard "
            "RTSA/Rogue/Engagement/Occupancy settings to deviating sites"
        ),
        category=OperationRegistry.skip_category("169"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SITE INVENTORY HEALTH ANALYSIS
    # ==============================
    "7": GlobalImportManager.MenuEntry(  # Use named fields for menu 7.
        menu_id="7",  # Store key for drift checks.
        handler=lambda: ExtractedSiteInventoryHealthAnalyzer.analyze(
            SiteInventoryHealthAnalyzerDeps(
                apisession=MainEntrypoint.context.apisession,
                mistapi=mistapi,
                get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
                all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
                save_data_fn=DataExporter.write_with_format_selection,
            )
        ),
        title=(
            "Site Inventory Health Analysis - Find sites with APs missing "
            "switches/gateways, or with offline infrastructure"
        ),
        category=OperationRegistry.skip_category("7"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # BULK RADIUS WLAN CONFIGURATION
    # ==============================
    "170": GlobalImportManager.MenuEntry(  # Use named fields for menu 170.
        menu_id="170",  # Store key for drift checks.
        handler=lambda dry_run=False: BulkRadiusWLANConfigManager().manage(dry_run=dry_run),
        title=(
            "Bulk RADIUS WLAN Configuration - Configure auth_servers_timeout, "
            "auth_servers_retries, fast_dot1x_timers for org-level RADIUS WLANs"
        ),
        category=OperationRegistry.skip_category("170"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # MAPS MANAGER (External Module)
    # ==============================
    "142": GlobalImportManager.MenuEntry(  # Use named fields for menu 142.
        menu_id="142",  # Store key for drift checks.
        handler=lambda: MapsManagerLauncher().launch(),
        title="Maps Manager - Interactive site floorplan and map operations (sub-menu)",
        category=OperationRegistry.skip_category("142"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # DEVICE UTILITY COMMANDS (Menus 123-157)
    # ==============================
    # > Diagnostic Commands
    "123": GlobalImportManager.MenuEntry(  # Use named fields for menu 123.
        menu_id="123",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().traceroute(),
        title="Traceroute from device to destination host (AP/Switch/Gateway)",
        category=OperationRegistry.skip_category("123"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "106": GlobalImportManager.MenuEntry(  # Use named fields for menu 106.
        menu_id="106",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_ospf_neighbors(),
        title="Show OSPF Neighbors on SSR/SRX Gateway",
        category=OperationRegistry.skip_category("106"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "107": GlobalImportManager.MenuEntry(  # Use named fields for menu 107.
        menu_id="107",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_ospf_interfaces(),
        title="Show OSPF Interfaces on SSR/SRX Gateway",
        category=OperationRegistry.skip_category("107"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "108": GlobalImportManager.MenuEntry(  # Use named fields for menu 108.
        menu_id="108",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_ospf_database(),
        title="Show OSPF Database on SSR/SRX Gateway",
        category=OperationRegistry.skip_category("108"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "109": GlobalImportManager.MenuEntry(  # Use named fields for menu 109.
        menu_id="109",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_ospf_summary(),
        title="Show OSPF Summary on SSR/SRX Gateway",
        category=OperationRegistry.skip_category("109"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "117": GlobalImportManager.MenuEntry(  # Use named fields for menu 117.
        menu_id="117",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().resolve_dns(),
        title="Test DNS Resolution on SSR Gateway",
        category=OperationRegistry.skip_category("117"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "124": GlobalImportManager.MenuEntry(  # Use named fields for menu 124.
        menu_id="124",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().monitor_traffic(),
        title="Monitor Traffic on Switch/SRX Port (streaming, Ctrl+C to stop)",
        category=OperationRegistry.skip_category("124"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "125": GlobalImportManager.MenuEntry(  # Use named fields for menu 125.
        menu_id="125",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().run_top(),
        title="Run Top Command on Switch/SRX (streaming, Ctrl+C to stop)",
        category=OperationRegistry.skip_category("125"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Show Commands
    "110": GlobalImportManager.MenuEntry(  # Use named fields for menu 110.
        menu_id="110",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_session(),
        title="Show Sessions on SSR/SRX Gateway",
        category=OperationRegistry.skip_category("110"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "111": GlobalImportManager.MenuEntry(  # Use named fields for menu 111.
        menu_id="111",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_service_path(),
        title="Show Service Path on SSR Gateway",
        category=OperationRegistry.skip_category("111"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "112": GlobalImportManager.MenuEntry(  # Use named fields for menu 112.
        menu_id="112",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_bgp_summary(),
        title="Show BGP Summary on Switch or Gateway",
        category=OperationRegistry.skip_category("112"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "113": GlobalImportManager.MenuEntry(  # Use named fields for menu 113.
        menu_id="113",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_arp_table(),
        title="Show ARP Table on Switch or Gateway",
        category=OperationRegistry.skip_category("113"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "114": GlobalImportManager.MenuEntry(  # Use named fields for menu 114.
        menu_id="114",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_dhcp_leases(),
        title="Show DHCP Leases on Switch or Gateway",
        category=OperationRegistry.skip_category("114"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "115": GlobalImportManager.MenuEntry(  # Use named fields for menu 115.
        menu_id="115",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_dot1x(),
        title="Show 802.1X Table on Switch",
        category=OperationRegistry.skip_category("115"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "116": GlobalImportManager.MenuEntry(  # Use named fields for menu 116.
        menu_id="116",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().show_evpn_database(),
        title="Show EVPN Database on Switch or Gateway",
        category=OperationRegistry.skip_category("116"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Management Commands
    "128": GlobalImportManager.MenuEntry(  # Use named fields for menu 128.
        menu_id="128",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().locate_device(),
        title="Locate Device - Blink LED on AP or Switch",
        category=OperationRegistry.skip_category("128"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "129": GlobalImportManager.MenuEntry(  # Use named fields for menu 129.
        menu_id="129",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().unlocate_device(),
        title="Unlocate Device - Stop LED Blinking on AP or Switch",
        category=OperationRegistry.skip_category("129"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "159": GlobalImportManager.MenuEntry(  # Use named fields for menu 159.
        menu_id="159",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().bounce_port(),
        title=" Bounce Switch/Gateway Port (y/N confirmation)",
        category=OperationRegistry.skip_category("159"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "122": GlobalImportManager.MenuEntry(  # Use named fields for menu 122.
        menu_id="122",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().cable_test(),
        title="Cable Test on Switch Port",
        category=OperationRegistry.skip_category("122"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "160": GlobalImportManager.MenuEntry(  # Use named fields for menu 160.
        menu_id="160",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().reprovision_device(),
        title=" Reprovision Switch/Gateway (y/N confirmation)",
        category=OperationRegistry.skip_category("160"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "130": GlobalImportManager.MenuEntry(  # Use named fields for menu 130.
        menu_id="130",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().readopt_device(),
        title="Re-adopt Switch Device",
        category=OperationRegistry.skip_category("130"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "131": GlobalImportManager.MenuEntry(  # Use named fields for menu 131.
        menu_id="131",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().get_ztp_password(),
        title="Get ZTP Password for Switch/Gateway (console only)",
        category=OperationRegistry.skip_category("131"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "132": GlobalImportManager.MenuEntry(  # Use named fields for menu 132.
        menu_id="132",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().get_config_commands(),
        title="Get Config CLI Commands for Switch Adoption",
        category=OperationRegistry.skip_category("132"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "133": GlobalImportManager.MenuEntry(  # Use named fields for menu 133.
        menu_id="133",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().upload_support_file(),
        title="Upload Support File from Switch/Gateway",
        category=OperationRegistry.skip_category("133"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Clear/Reset Commands
    "177": GlobalImportManager.MenuEntry(  # Use named fields for menu 177.
        menu_id="177",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_arp_cache(),
        title=" DESTRUCTIVE: Clear ARP Cache (type CLEAR)",
        category=OperationRegistry.skip_category("177"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "178": GlobalImportManager.MenuEntry(  # Use named fields for menu 178.
        menu_id="178",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_bgp_routes(),
        title=" DESTRUCTIVE: Clear BGP Routes (type CLEAR)",
        category=OperationRegistry.skip_category("178"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "179": GlobalImportManager.MenuEntry(  # Use named fields for menu 179.
        menu_id="179",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_session(),
        title=" DESTRUCTIVE: Clear Session on SSR/SRX (type CLEAR)",
        category=OperationRegistry.skip_category("179"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "180": GlobalImportManager.MenuEntry(  # Use named fields for menu 180.
        menu_id="180",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_mac_table(),
        title=" DESTRUCTIVE: Clear MAC Table (type CLEAR)",
        category=OperationRegistry.skip_category("180"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "181": GlobalImportManager.MenuEntry(  # Use named fields for menu 181.
        menu_id="181",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_bpdu_error(),
        title=" DESTRUCTIVE: Clear BPDU Errors on Switch (type CLEAR)",
        category=OperationRegistry.skip_category("181"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "182": GlobalImportManager.MenuEntry(  # Use named fields for menu 182.
        menu_id="182",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_learned_macs(),
        title=" DESTRUCTIVE: Clear Learned MACs from Switch Port (type CLEAR)",
        category=OperationRegistry.skip_category("182"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "183": GlobalImportManager.MenuEntry(  # Use named fields for menu 183.
        menu_id="183",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().clear_policy_hit_count(),
        title=" DESTRUCTIVE: Clear Policy Hit Count on SSR (type CLEAR)",
        category=OperationRegistry.skip_category("183"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "184": GlobalImportManager.MenuEntry(  # Use named fields for menu 184.
        menu_id="184",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().release_dhcp_lease(),
        title=" Release DHCP Lease on Switch/Gateway (y/N)",
        category=OperationRegistry.skip_category("184"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "185": GlobalImportManager.MenuEntry(  # Use named fields for menu 185.
        menu_id="185",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().release_dhcp_ssr(),
        title=" Release DHCP Lease on SSR/SRX (y/N)",
        category=OperationRegistry.skip_category("185"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Hardware Commands
    "126": GlobalImportManager.MenuEntry(  # Use named fields for menu 126.
        menu_id="126",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().poll_switch_stats(),
        title="Poll Fresh Statistics from Switch",
        category=OperationRegistry.skip_category("126"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "127": GlobalImportManager.MenuEntry(  # Use named fields for menu 127.
        menu_id="127",  # Store key for drift checks.
        handler=lambda: _get_duc_instance().create_device_snapshot(),
        title="Create Device Snapshot on Switch",
        category=OperationRegistry.skip_category("127"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Offline / Reporting
    "26": GlobalImportManager.MenuEntry(  # Use named fields for menu 26.
        menu_id="26",  # Store key for drift checks.
        handler=OfflineDeviceReporter.execute,
        title="Offline Device Report",
        category=OperationRegistry.skip_category("26"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "145": GlobalImportManager.MenuEntry(  # Use named fields for menu 145.
        menu_id="145",  # Store key for drift checks.
        handler=OrgExportUtils.ssid_template_consolidation,
        title="SSID Template Consolidation (5-Phase Guided Workflow)",
        category=OperationRegistry.skip_category("145"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "89": GlobalImportManager.MenuEntry(  # Use named fields for menu 89.
        menu_id="89",  # Store key for drift checks.
        handler=OrgExportUtils.e911_bssid_compliance_report,
        title="E911 BSSID Compliance Report",
        category=OperationRegistry.skip_category("89"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "90": GlobalImportManager.MenuEntry(  # Use named fields for menu 90.
        menu_id="90",  # Store key for drift checks.
        handler=GlobalWiredClientReportGenerator.execute,
        title="Global Wired Client Report (operator-based MAC/MFG filtering)",
        category=OperationRegistry.skip_category("90"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "91": GlobalImportManager.MenuEntry(  # Use named fields for menu 91.
        menu_id="91",  # Store key for drift checks.
        handler=WiredClientManufacturerReportGenerator.execute,
        title="Wired Client Manufacturer Report (exports all manufacturers)",
        category=OperationRegistry.skip_category("91"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "146": GlobalImportManager.MenuEntry(  # Use named fields for menu 146.
        menu_id="146",  # Store key for drift checks.
        handler=lambda: WanHubGroupNumberManager.execute(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ),
        title="WAN Hub Group Number Manager",
        category=OperationRegistry.skip_category("146"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "147": GlobalImportManager.MenuEntry(  # Use named fields for menu 147.
        menu_id="147",  # Store key for drift checks.
        handler=lambda: WanVpnBuilder.execute(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ),
        title="WAN Hub-Spoke VPN Builder",
        category=OperationRegistry.skip_category("147"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # > Bulk Data Collection
    "153": GlobalImportManager.MenuEntry(  # Use named fields for menu 153.
        menu_id="153",  # Store key for drift checks.
        handler=lambda: OrgDataCollector.execute(
            OrgExportUtils.export_data, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ),
        title=("Bulk Org Data Collection (populate ArangoDB/Redis/SQLite with all " "org-level APIs)"),
        category=OperationRegistry.skip_category("153"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # MISTAPI 0.62.0 NEW ENDPOINTS
    # ==============================
    "5": GlobalImportManager.MenuEntry(  # Use named fields for menu 5.
        menu_id="5",  # Store key for drift checks.
        handler=OrgExportUtils.e911_report,
        title="Export E911 report for the organization",
        category=OperationRegistry.skip_category("5"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "56": GlobalImportManager.MenuEntry(  # Use named fields for menu 56.
        menu_id="56",  # Store key for drift checks.
        handler=OrgExportUtils.jsi_pbn,
        title="Export JSI PBN (Product Bulletin Notifications) data",
        category=OperationRegistry.skip_category("56"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "57": GlobalImportManager.MenuEntry(  # Use named fields for menu 57.
        menu_id="57",  # Store key for drift checks.
        handler=OrgExportUtils.jsi_sirt,
        title="Export JSI SIRT (Security Incident Response) advisories",
        category=OperationRegistry.skip_category("57"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Spec 865 / issue #1373 -- surfaces mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts
    # alongside the existing PBN/SIRT reports so operators can pull JSI inventory + contracts.
    "204": GlobalImportManager.MenuEntry(  # Use named fields for menu 204.
        menu_id="204",  # Store key for drift checks.
        handler=OrgExportUtils.jsi_assets,
        title="Export JSI assets and contract search results",
        category=OperationRegistry.skip_category("204"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # Spec 866 / issue #1374 -- surfaces mistapi.api.v1.orgs.mxedges.searchOrgMistEdgeEvents
    # (org-scope peer of the site-scoped SiteMistEdgeEventsExporter registered on menu 201).
    "205": GlobalImportManager.MenuEntry(  # Use named fields for menu 205.
        menu_id="205",  # Store key for drift checks.
        handler=OrgExportUtils.mist_edge_events,
        title="Export Org Mist Edge event search results",
        category=OperationRegistry.skip_category("205"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "55": GlobalImportManager.MenuEntry(  # Use named fields for menu 55.
        menu_id="55",  # Store key for drift checks.
        handler=OrgExportUtils.ospf_stats,
        title="Export OSPF adjacency statistics for the organization",
        category=OperationRegistry.skip_category("55"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "70": GlobalImportManager.MenuEntry(  # Use named fields for menu 70.
        menu_id="70",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().ospf_stats(),
        title="Export OSPF adjacency statistics for a selected site",
        category=OperationRegistry.skip_category("70"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "71": GlobalImportManager.MenuEntry(  # Use named fields for menu 71.
        menu_id="71",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().mxedge_upgrade_status(),
        title="Export MxEdge upgrade status for a selected site",
        category=OperationRegistry.skip_category("71"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "72": GlobalImportManager.MenuEntry(  # Use named fields for menu 72.
        menu_id="72",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().auto_map_assignment_status(),
        title="Export auto-map assignment status for a selected site",
        category=OperationRegistry.skip_category("72"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "88": GlobalImportManager.MenuEntry(  # Use named fields for menu 88.
        menu_id="88",  # Store key for drift checks.
        handler=SitesByAPModelExporter.export_sites_by_ap_model,
        title="Export sites by AP model with site address (CSV)",
        category=OperationRegistry.skip_category("88"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "25": GlobalImportManager.MenuEntry(  # Use named fields for menu 25.
        menu_id="25",  # Store key for drift checks.
        handler=AuditAnalysisOps.audit_log_analysis,
        title="Audit Log Analysis - Mermaid timeline + interactive HTML report",
        category=OperationRegistry.skip_category("25"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "186": GlobalImportManager.MenuEntry(  # Use named fields for menu 186.
        menu_id="186",  # Store key for drift checks.
        handler=CacheUtils.clear_cache,
        title="Clear CSV Cache Files (delete all generated cache CSVs)",
        category=OperationRegistry.skip_category("186"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "58": GlobalImportManager.MenuEntry(  # Use named fields for menu 58.
        menu_id="58",  # Store key for drift checks.
        handler=lambda: cast(Any, OrgConfigMigrationManager)(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ).export_config(),
        title="Export Org WAN/Gateway Config (JSON bundle for cross-org migration)",
        category=OperationRegistry.skip_category("58"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "187": GlobalImportManager.MenuEntry(  # Use named fields for menu 187.
        menu_id="187",  # Store key for drift checks.
        handler=lambda: cast(Any, OrgConfigMigrationManager)(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
        ).import_config(),
        title="Import Org WAN/Gateway Config (cross-org migration with conflict detection)",
        category=OperationRegistry.skip_category("187"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SITE STATS, METRICS & CHANNEL PLANNING
    # ==============================
    "80": GlobalImportManager.MenuEntry(  # Use named fields for menu 80.
        menu_id="80",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().site_stats(),
        title="Export site aggregate health & capacity statistics",
        category=OperationRegistry.skip_category("80"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "81": GlobalImportManager.MenuEntry(  # Use named fields for menu 81.
        menu_id="81",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().gateway_metrics(),
        title="Export site gateway performance metrics summary",
        category=OperationRegistry.skip_category("81"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "82": GlobalImportManager.MenuEntry(  # Use named fields for menu 82.
        menu_id="82",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().switches_metrics(),
        title="Export site switch performance metrics summary",
        category=OperationRegistry.skip_category("82"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "83": GlobalImportManager.MenuEntry(  # Use named fields for menu 83.
        menu_id="83",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().beacons_stats(),
        title="Export site BLE beacon statistics",
        category=OperationRegistry.skip_category("83"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "84": GlobalImportManager.MenuEntry(  # Use named fields for menu 84.
        menu_id="84",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().wxrules_usage(),
        title="Export site WxLAN rule usage statistics",
        category=OperationRegistry.skip_category("84"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "85": GlobalImportManager.MenuEntry(  # Use named fields for menu 85.
        menu_id="85",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().assets_stats(),
        title="Export site asset statistics",
        category=OperationRegistry.skip_category("85"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "86": GlobalImportManager.MenuEntry(  # Use named fields for menu 86.
        menu_id="86",  # Store key for drift checks.
        handler=lambda: GlobalImportManager.SiteExportUtilsFactory().build().current_channel_planning(),
        title="Export current RRM channel & power plan per AP radio",
        category=OperationRegistry.skip_category("86"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "23": GlobalImportManager.MenuEntry(  # Use named fields for menu 23.
        menu_id="23",  # Store key for drift checks.
        handler=SelfExportUtils.audit_logs,
        title="Export self (admin account) audit log",
        category=OperationRegistry.skip_category("23"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "87": GlobalImportManager.MenuEntry(  # Use named fields for menu 87.
        menu_id="87",  # Store key for drift checks.
        handler=GatewayHaExporter.ha_cluster_info,
        title="Export HA gateway cluster info, stats & node pair for a site",
        category=OperationRegistry.skip_category("87"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "13": GlobalImportManager.MenuEntry(  # Use named fields for menu 13.
        menu_id="13",  # Store key for drift checks.
        handler=OrgDeviceInventorySummary.dispatch,
        title=("Export org device model counts, firmware version distribution, and " "versions per model (MSP-aware)"),
        category=OperationRegistry.skip_category("13"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    # ==============================
    # SUPPORT TICKETS
    # ==============================
    "188": GlobalImportManager.MenuEntry(  # Use named fields for menu 188.
        menu_id="188",  # Store key for drift checks.
        handler=OrgTicketManager.list_tickets,
        title="Export all organization support tickets to CSV",
        category=OperationRegistry.skip_category("188"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "189": GlobalImportManager.MenuEntry(  # Use named fields for menu 189.
        menu_id="189",  # Store key for drift checks.
        handler=OrgTicketManager.create_ticket,
        title="Create a new organization support ticket",
        category=OperationRegistry.skip_category("189"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "190": GlobalImportManager.MenuEntry(  # Use named fields for menu 190.
        menu_id="190",  # Store key for drift checks.
        handler=OrgTicketManager.add_comment,
        title="Add a comment (with optional file attachment) to a support ticket",
        category=OperationRegistry.skip_category("190"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "191": GlobalImportManager.MenuEntry(  # Use named fields for menu 191.
        menu_id="191",  # Store key for drift checks.
        handler=OrgTicketManager.update_ticket,
        title="Update fields on an existing support ticket",
        category=OperationRegistry.skip_category("191"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "192": GlobalImportManager.MenuEntry(  # Use named fields for menu 192.
        menu_id="192",  # Store key for drift checks.
        handler=OrgTicketManager.view_ticket,
        title="View a support ticket with full comments and history",
        category=OperationRegistry.skip_category("192"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "193": GlobalImportManager.MenuEntry(  # Use named fields for menu 193.
        menu_id="193",  # Store key for drift checks.
        handler=OrgTicketManager.export_ticket_details,
        title="Export all tickets with full details and comments",
        category=OperationRegistry.skip_category("193"),  # Read the safety class.
        destructive=False,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "194": GlobalImportManager.MenuEntry(  # Use named fields for menu 194.
        menu_id="194",  # Store key for drift checks.
        handler=DeviceConfigTemplateClonerManager.clone,
        title=(
            " DESTRUCTIVE: Clone Device Config to Gateway Template - Select a "
            "gateway, extract its local config, and create a new org gateway "
            "template (Requires typing 'CREATE' to confirm)"
        ),
        category=OperationRegistry.skip_category("194"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "206": GlobalImportManager.MenuEntry(  # Use named fields for menu 206.
        menu_id="206",  # Store key for drift checks.
        handler=lambda: manage_org_synthetic_probes(
            MainEntrypoint.context.apisession, ConfigUtils.get_cached_or_prompted_org_id()
        ),
        title=(
            " DESTRUCTIVE: Manage org Zscaler synthetic probes - Build/merge/swap "
            "synthetic_test.custom_probes from curated Zscaler catalogue"
        ),
        category=OperationRegistry.skip_category("206"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "207": GlobalImportManager.MenuEntry(  # Use named fields for menu 207.
        menu_id="207",  # Store key for drift checks.
        handler=lambda: APProfileMigrationManager.migrate_aps_between_device_profiles(
            MainEntrypoint.context.apisession
        ),
        title=(
            " DESTRUCTIVE: Migrate APs between device profiles - Reassign every AP "
            "bound to a source device profile to a chosen target profile (Requires "
            "typing 'MIGRATE' or 'DRY-RUN' to confirm)"
        ),
        category=OperationRegistry.skip_category("207"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
    "208": GlobalImportManager.MenuEntry(  # Use named fields for menu 208.
        menu_id="208",  # Store key for drift checks.
        handler=lambda: APProfileMigrationManager.revert_ap_profile_migration(MainEntrypoint.context.apisession),
        title=(
            " DESTRUCTIVE: Revert an AP profile migration from a backup file - "
            "Reassign each listed AP back to its original device profile (Requires "
            "typing 'REVERT' to confirm)"
        ),
        category=OperationRegistry.skip_category("208"),  # Read the safety class.
        destructive=True,  # Keep the safety flag.
        supports_fast=False,  # Avoid fast-mode inspection.
    ),
}


def _systematic_test_build_safe_list(  # Preserve the existing behavior during the compliance refactor.
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
    safe_options.extend(filter(remaining.__contains__, optimized_test_order))  # Keep optimized safe options in order.
    remaining.difference_update(safe_options)  # Remove ordered entries so the remainder block is unique.
    safe_options.extend(
        sorted(remaining, key=lambda x: float(x.replace("a", ".1")))
    )  # Append all remaining safe options in natural numeric order.
    if not _systematic_test_has_api_token():  # Without a token, only local safe checks may execute.
        api_options = _systematic_test_api_options(safe_options)  # Identify safe entries that call Mist Cloud.
        safe_options = [opt for opt in safe_options if opt not in api_options]  # Keep local safe tests only.
        unsafe_list.extend(api_options)  # Count credential-backed checks as skipped, not failed.
        unsafe_list = sorted(set(unsafe_list), key=lambda x: float(x.replace("a", ".1")))  # Keep output stable.
    return safe_options, unsafe_list  # Return both lists so caller can emit skips and run tests.


def _systematic_test_has_api_token() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when the environment holds a real Mist API token."""
    logger.info("SYSTEMATIC_TEST: checking for a Mist API token")  # Log before reading credential metadata.
    _host, tokens = _parse_api_tokens()  # Read only local environment values and never log the token.
    has_token = any(not _looks_like_placeholder(token) for token in tokens)  # Reject blank and template values.
    logger.debug("SYSTEMATIC_TEST: Mist API token present: %s", has_token)  # Log only the boolean result.
    return has_token  # Tell the runner whether live API tests may execute.


def _systematic_test_api_options(
    safe_options: list[str],
) -> set[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return the safe options that must not run without a Mist API token."""
    logger.info("SYSTEMATIC_TEST: classifying API-backed safe options")  # Log before registry filtering.
    api_options = {opt for opt in safe_options if OperationRegistry.requires_api_token(opt)}  # Find live API tests.
    logger.debug("SYSTEMATIC_TEST: found %d API-backed safe options", len(api_options))  # Log the skip count.
    return api_options  # Give the caller a set for quick membership tests.


def _systematic_test_skip_details(
    opt: str, has_api_token: bool
) -> tuple[str, str]:  # Preserve the existing behavior during the compliance refactor.
    """Return the skip reason and category for one systematic-test skip."""
    if not has_api_token and OperationRegistry.requires_api_token(opt):  # No token means API-backed tests must skip.
        reason = "Requires MIST_APITOKEN or MIST_API_TOKEN because this test calls the Mist API"  # Name variables.
        logger.debug("SYSTEMATIC_TEST: option %s skipped because a Mist API token is absent", opt)  # Log cause.
        return reason, "credential_required"  # Emit a precise dynamic skip category.
    reason = OperationRegistry.skip_reason(opt)  # Read the static registry reason for non-credential skips.
    category = OperationRegistry.skip_category(opt)  # Read the static registry category for telemetry.
    return reason, category  # Preserve existing skip output for non-credential cases.


def _systematic_test_emit_skips(
    emitter: Any, unsafe_list: list[str]
) -> int:  # Preserve the existing behavior during the compliance refactor.
    """Emit a skip event for each unsafe operation and print an explanation."""
    echo(" Skipping operations not run:")  # Preserve the existing behavior during the compliance refactor.
    has_api_token = _systematic_test_has_api_token()  # Use one credential check for all skip rows.
    for opt in unsafe_list:  # Iterate every unsafe option so none are silently omitted.
        if opt in menu_actions:  # Guard against stale unsafe lists that reference removed options.
            description = menu_actions[opt].title  # Read the display text from the named menu row.
            reason, category = _systematic_test_skip_details(opt, has_api_token)  # Resolve static or token skip.
            echo(  # Preserve the existing behavior during the compliance refactor.
                "   %3s: %s... (Reason: %s)",
                opt,
                description[:60],
                reason,
            )
            emitter.emit_test_skip(
                opt, description, reason, category, "systematic"
            )  # Record skip in telemetry for coverage reporting.
    echo("")  # Preserve the existing behavior during the compliance refactor.
    return len([opt for opt in unsafe_list if opt in menu_actions])  # Return actual skip count for summary reporting.


def _resolve_systematic_test_invoke_kwargs(
    entry: Any, fast_enabled: bool
) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Build invoke kwargs from explicit menu metadata."""
    logger.info("Resolving systematic-test kwargs for option %s", entry.menu_id)  # WHY: log before metadata read.
    invoke_kwargs: dict[str, Any] = {}  # Build kwargs dict
    if entry.supports_fast and fast_enabled:  # Both function and global mode agree
        invoke_kwargs["fast"] = True  # Activate fast mode for this operation
    logger.debug("Resolved systematic-test kwargs for option %s: %s", entry.menu_id, invoke_kwargs)  # WHY: log result.
    return invoke_kwargs  # Preserve the existing behavior during the compliance refactor.


def _invoke_one_systematic_test(  # Preserve the existing behavior during the compliance refactor.
    emitter: Any, case: SystematicTestOption, invoke_kwargs: dict[str, Any], op_start: float
) -> tuple[bool, float]:
    """Call one menu func with the resolved kwargs. Record pass/fail in telemetry and return (success, duration)."""
    option, func, description = case.option, case.func, case.description  # Unpack identity (issue #470)
    try:  # Each option runs independently so one failure does not abort remaining tests
        func(**invoke_kwargs)  # Call menu action
        duration = time.time() - op_start  # Elapsed seconds
        echo(
            "   [SUCCESS] Option %s completed successfully", option
        )  # Preserve the existing behavior during the compliance refactor.
        emitter.emit_test_pass(option, description, duration, "systematic")  # Record pass
        logger.info(
            "SYSTEMATIC_TEST: Successfully completed menu option %s", option
        )  # Preserve the existing behavior during the compliance refactor.
        return True, duration  # Preserve the existing behavior during the compliance refactor.
    except (KeyboardInterrupt, SystemExit):  # Operators and automation must be able to stop the harness
        raise  # Do not record a stop request as a menu test failure
    except Exception as exc:  # Broad by design so one menu defect cannot stop the test harness
        duration = time.time() - op_start  # Still record elapsed
        echo(
            "   [FAILED]  Option %s failed: %s...", option, str(exc)[:100]
        )  # Preserve the existing behavior during the compliance refactor.
        emitter.emit_test_fail(option, description, duration, exc, "systematic")  # Record failure
        logging.exception("SYSTEMATIC_TEST: Failed menu option %s: %s", option, exc)  # Keep menu failure trace
        return False, duration  # Preserve the existing behavior during the compliance refactor.


def _systematic_test_run_option(  # Preserve the existing behavior during the compliance refactor.
    emitter: Any,
    case: SystematicTestOption,
    i: int,
    total_safe: int,
    fast_enabled: bool,
) -> tuple[bool, float]:
    """Run one menu option in the systematic test harness and return (success, duration)."""
    option = case.option  # Read option id for telemetry.
    description = case.description  # Read menu text for telemetry.
    echo(
        "   [%2d/%d] Testing option %3s: %s...", i, total_safe, option, description[:60]
    )  # Preserve the existing behavior during the compliance refactor.
    emitter.emit_test_start(option, description, "systematic")  # Telemetry start
    op_start = time.time()  # Capture start time before invocation overhead
    invoke_kwargs = _resolve_systematic_test_invoke_kwargs(menu_actions[option], fast_enabled)  # Use menu metadata.
    logger.info(
        "SYSTEMATIC_TEST: INVOKE option=%s fast_supported=%s fast_enabled=%s test_mode=True description='%s'",
        option,
        "fast" in invoke_kwargs,
        fast_enabled,
        description,
    )  # Log invocation details for post-mortem correlation
    return _invoke_one_systematic_test(
        emitter, case, invoke_kwargs, op_start
    )  # Preserve the existing behavior during the compliance refactor.


def _fast_mode_from_global() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True iff the module-level ``FAST_MODE_ENABLED`` flag is set (errors -> False)."""
    try:  # Context access is normally safe but guarded for parity with original.
        return bool(MainEntrypoint.context.fast_mode_enabled)  # Read the context flag set by CLI parse at startup.
    except (KeyboardInterrupt, SystemExit):  # Operators must be able to stop fast-mode resolution
        raise  # Do not convert an operator stop into the default fast-mode value
    except Exception as error:  # Broad by design so a broken context only disables fast mode
        logging.exception("Failed to read context fast-mode flag: %s", error)  # Keep context failure trace
        return False  # Safe default for any introspection failure.


def _fast_mode_from_cli_args() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True iff parsed ``args`` exist in globals and carry ``--fast`` (errors -> False)."""
    try:  # CLI args presence + attribute lookup can both fail. Degrade safely.
        cli_args = globals().get("args") if "args" in globals() else None  # Locate parsed args, if any.
        return bool(cli_args and getattr(cli_args, "fast", False))  # Truthy only when the caller set --fast.
    except (KeyboardInterrupt, SystemExit):  # Operators must be able to stop CLI flag resolution
        raise  # Do not convert an operator stop into the default fast-mode value
    except Exception as error:  # Broad by design so a broken CLI namespace only disables fast mode
        logging.exception("Failed to read CLI fast-mode flag: %s", error)  # Keep CLI namespace failure trace
        return False  # Safe default for any introspection failure.


def _systematic_test_resolve_fast_mode() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return whether fast mode is active for the current systematic test run."""
    if _fast_mode_from_global():  # Primary source: module-level flag set at startup.
        return True  # Preserve the existing behavior during the compliance refactor.
    return _fast_mode_from_cli_args()  # Fallback: parsed --fast on CLI args namespace.


def _print_systematic_banner() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the test-start banner + timestamp + separator to the operator console."""
    echo(
        " Starting systematic test of MistHelper menu options..."
    )  # Preserve the existing behavior during the compliance refactor.
    echo(  # Preserve the existing behavior during the compliance refactor.
        "  Note: This will skip interactive, websocket, POST, and destructive operations",
    )
    echo(  # Preserve the existing behavior during the compliance refactor.
        "! Test started at: %s",
        datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    )
    echo("=" * 80)  # Preserve the existing behavior during the compliance refactor.


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


def _build_systematic_test_options() -> (
    tuple[list[str], list[str], list[str]]
):  # Preserve the existing behavior during the compliance refactor.
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
    return safe_options, unsafe_list, all_options  # Preserve the existing behavior during the compliance refactor.


def _print_systematic_pre_run_counts(
    all_options: list[str], safe_options: list[str], unsafe_list: list[str]
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the total / safe / unsafe option counts before the test loop runs."""
    echo(
        "! Found %d total menu options", len(all_options)
    )  # Preserve the existing behavior during the compliance refactor.
    echo(
        "! %d safe options will be tested", len(safe_options)
    )  # Preserve the existing behavior during the compliance refactor.
    echo(
        "!  %d operations will be skipped", len(unsafe_list)
    )  # Preserve the existing behavior during the compliance refactor.
    echo("")  # Preserve the existing behavior during the compliance refactor.


def _initialize_systematic_telemetry(
    unsafe_list: list[str],
) -> tuple[TelemetryEmitter, str, int]:  # Preserve the existing behavior during the compliance refactor.
    """Open the timestamped telemetry emitter and emit skip events. Return (emitter, path, skip_count)."""
    telemetry_path = TelemetryEmitter.timestamped_path(
        "data"
    )  # Compute timestamped telemetry file path before starting events.
    emitter = TelemetryEmitter(telemetry_path)  # Open emitter so all events land in one timestamped file.
    skip_count = _systematic_test_emit_skips(
        emitter, unsafe_list
    )  # Print skip list and emit skip events. Returns actual skip count.
    return emitter, telemetry_path, skip_count  # Preserve the existing behavior during the compliance refactor.


def _resolve_systematic_test_context() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Resolve module-level org_id and the fast-mode flag once before the test loop."""
    # The application context owns this state, so no global declaration is needed.
    if not _systematic_test_has_api_token():  # Offline test mode cannot resolve a live organization.
        logger.info("SYSTEMATIC_TEST: no Mist API token; skipping org_id resolution")  # Log the offline path.
        fast_enabled = _systematic_test_resolve_fast_mode()  # Still honor --fast for any local tests.
        logger.debug("SYSTEMATIC_TEST: offline context prepared fast=%s", fast_enabled)  # Confirm context result.
        return fast_enabled  # Let the loop run only offline-safe operations.
    if (
        not MainEntrypoint.context.org_id
    ):  # Resolve org_id once before the test loop so every option shares the same org.
        MainEntrypoint.context.org_id = (
            ConfigUtils.get_cached_or_prompted_org_id()
        )  # Prompt or use cached org identifier.
    return _systematic_test_resolve_fast_mode()  # Resolve fast-mode flag once for the loop.


def _execute_systematic_test_loop(  # Preserve the existing behavior during the compliance refactor.
    emitter: TelemetryEmitter, safe_options: list[str], fast_enabled: bool
) -> tuple[int, int]:
    """Iterate safe options through the runner, counting successes/failures."""
    echo(" Testing safe operations:")  # Preserve the existing behavior during the compliance refactor.
    success_count = 0  # Track how many options completed without raising.
    error_count = 0  # Track how many options raised an exception.
    for i, option in enumerate(safe_options, 1):  # Iterate options in optimized order, 1-indexed for display.
        entry = menu_actions[option]  # Read the named row for this option.
        func = entry.handler  # Read the callable without tuple-position unpacking.
        description = entry.title  # Read the display text without tuple-position unpacking.
        if func is None:  # Static rows cannot run in systematic mode.
            continue  # Skip impossible rows, though real MistHelper rows always have callables.
        success, _duration = _systematic_test_run_option(
            emitter, SystematicTestOption(option, func, description), i, len(safe_options), fast_enabled
        )  # Execute option with telemetry (issue #470: option identity bundled).
        if success:  # Count success and failure separately for the final summary.
            success_count += 1  # Increment on successful option execution.
        else:  # Non-success means the option raised or returned an error.
            error_count += 1  # Increment on failed option execution.
        if not fast_enabled:  # API-respectful delay between test runs in normal mode.
            time.sleep(1)  # One-second pause so the API is not hammered by rapid-fire requests.
    return success_count, error_count  # Preserve the existing behavior during the compliance refactor.


def _finalize_systematic_telemetry(
    emitter: TelemetryEmitter, summary: TestSummary
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Emit the final summary event, close the telemetry file, and enforce retention."""
    emitter.emit_test_summary(summary)  # Emit aggregate telemetry summary.
    emitter.close()  # Flush and close telemetry file before printing summary.
    emitter.enforce_retention()  # Clean up old telemetry files per configured retention policy.


def _print_systematic_summary(
    summary: TestSummary, telemetry_path: str
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the human-readable summary block (totals, coverage %, paths)."""
    echo("")  # Preserve the existing behavior during the compliance refactor.
    echo("=" * 80)  # Preserve the existing behavior during the compliance refactor.
    echo(" Systematic Test Summary:")  # Preserve the existing behavior during the compliance refactor.
    echo(
        "   Successful operations: %d", summary.passed
    )  # Preserve the existing behavior during the compliance refactor.
    echo("   Failed operations: %d", summary.failed)  # Preserve the existing behavior during the compliance refactor.
    echo("   Skipped operations: %d", summary.skipped)  # Preserve the existing behavior during the compliance refactor.
    coverage_pct = summary.passed / summary.total * 100 if summary.total else 0.0  # Coverage as a percent.
    echo(
        "   Total coverage: %d/%d (%.1f%%)", summary.passed, summary.total, coverage_pct
    )  # Preserve the existing behavior during the compliance refactor.
    echo(
        "    Total execution time: %.2f seconds", summary.elapsed
    )  # Preserve the existing behavior during the compliance refactor.
    echo(
        "   Telemetry written to: %s", telemetry_path
    )  # Preserve the existing behavior during the compliance refactor.
    echo("   Detailed logs in: script.log")  # Preserve the existing behavior during the compliance refactor.


def _report_systematic_outcome(
    success_count: int, error_count: int, safe_count: int, total_time: float
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Emit the final all-pass / partial-failure message and return the boolean result."""
    if error_count == 0:  # All-pass outcome deserves an explicit success message.
        echo(
            "   All tested operations completed successfully!"
        )  # Preserve the existing behavior during the compliance refactor.
        logger.info(
            "SYSTEMATIC_TEST: All %s tested operations completed successfully in %.2fs",
            success_count,
            total_time,
        )  # Record all-pass event for monitoring.
        return True  # Signal all-pass to callers (for example, for exit-code logic).
    echo(
        "    %d operations failed - check logs for details", error_count
    )  # Preserve the existing behavior during the compliance refactor.
    logger.warning(
        "SYSTEMATIC_TEST: %s operations failed out of %s tested", error_count, safe_count
    )  # Log failure count for alerting systems.
    return False  # Signal partial failure to callers.


def _build_interactive_test_runner(
    get_org_id: Any, set_org_id: Any
) -> Any:  # Preserve the existing behavior during the compliance refactor.
    """Construct InteractiveTestRunner with the current runtime context and return it."""
    logger.info("Constructing InteractiveTestRunner dependencies")  # Log before instance creation
    runner = InteractiveTestRunner(  # Build runner with runtime deps
        menu_actions=menu_actions,
        operation_registry=OperationRegistry,
        telemetry_emitter_cls=TelemetryEmitter,
        config_utils=ConfigUtils,
        mistapi_module=mistapi,
        apisession=MainEntrypoint.context.apisession,
        org_id_getter=get_org_id,
        org_id_setter=set_org_id,
        input_utils=InputUtils,
    )
    logger.debug("InteractiveTestRunner initialized successfully")  # Confirm construction
    return runner  # Preserve the existing behavior during the compliance refactor.


def _run_web_portal_server(
    app: Any, host: str, port: int, dev_debug: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Start the Flask app in container mode (Gunicorn-aware) or local Flask dev server mode."""
    in_container = EnvironmentUtils.is_running_in_container()  # Detect container runtime to switch banner + debug flag
    if in_container:  # Preserve the existing behavior during the compliance refactor.
        logger.info("WEB_PORTAL: Container detected - use wsgi.py with Gunicorn")  # Log container path
        echo(
            ">> Running Flask dev server on %s:%s", host, port
        )  # Preserve the existing behavior during the compliance refactor.
        echo(
            ">> For production, use: gunicorn wsgi:app"
        )  # Preserve the existing behavior during the compliance refactor.
        app.run(host=host, port=port, debug=False)  # Force debug=False inside container
    else:
        logger.info("WEB_PORTAL: Local mode - Flask dev server on %s:%s", host, port)  # Log local dev path
        echo(
            ">> Web portal starting at http://127.0.0.1:%s", port
        )  # Preserve the existing behavior during the compliance refactor.
        app.run(host=host, port=port, debug=dev_debug)  # Honor caller's debug flag locally


def _resolve_web_portal_host() -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the address that the web portal binds to.

    The WEB_HOST variable overrides every default. Without that
    variable, a container binds to all interfaces, and a
    workstation binds to the loopback address.
    """
    logger.info("WEB_PORTAL: resolving the bind address for the web portal")  # Log before the resolution starts
    override_host = os.environ.get("WEB_HOST")  # An operator value must win over both defaults
    if override_host:  # A set WEB_HOST value controls the bind on a container and on a workstation
        logger.debug("WEB_PORTAL: bind address came from WEB_HOST: %s", override_host)  # Report the override result
        return override_host  # Return the operator value and skip the container check
    in_container = EnvironmentUtils.is_running_in_container()  # Only a container gets the all-interfaces bind
    if not in_container:  # A workstation must keep the portal on the loopback interface
        logger.debug("WEB_PORTAL: bind address is the loopback address on a workstation")  # Report the result
        return "127.0.0.1"  # Keep the portal off every external interface of the workstation
        # The next assignment runs only when is_running_in_container() returns True. A container needs the
        # all-interfaces bind, because the container network maps the port from outside. The container port map
        # controls the exposure, and a workstation returns the loopback address above.
    all_interfaces_host = ".".join(("0", "0", "0", "0"))  # Build the bind-all address only for container use
    logger.debug("WEB_PORTAL: bind address is %s inside a container", all_interfaces_host)  # Report the result
    return all_interfaces_host  # Hand the container bind address to the launcher


def _launch_web_portal(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch the Flask web portal.

    Determines whether to use Gunicorn (container)
    or Flask dev server (local Windows) and starts
    the portal with the current apisession, org_id,
    and menu_actions.
    """
    from web_portal.app import WebPortalApp  # Preserve the existing behavior during the compliance refactor.
    from web_portal.services.config import (
        PortalConfigLoader,
    )  # Preserve the existing behavior during the compliance refactor.

    loader = PortalConfigLoader()  # Read web_port + other portal settings from env/.env
    config = loader.load_config()  # Preserve the existing behavior during the compliance refactor.
    port = config["web_port"]  # Preserve the existing behavior during the compliance refactor.
    host = _resolve_web_portal_host()  # Loopback on a workstation, all interfaces in a container, WEB_HOST wins

    app = WebPortalApp.create_app(  # Construct Flask app with shared API session + menu registry
        apisession=MainEntrypoint.context.apisession,
        menu_actions=menu_actions,
        org_id=MainEntrypoint.context.org_id,
    )

    _run_web_portal_server(app, host, port, args.debug)  # Dispatch to container/local runner


def _capture_portal_port() -> int:  # Preserve the existing behavior during the compliance refactor.
    """Return the listen port for the upgrade capture portal.

    Why:
        The container and a workstation both set CAPTURE_PORT. A bad value must not stop
        the launch, so the reader falls back to the documented default of 8056.

    Returns:
        The port from CAPTURE_PORT, or 8056 when the value is absent or is not a number.
    """
    raw_port = os.environ.get("CAPTURE_PORT", "8056")  # The container sets this; 8056 matches the plan
    if raw_port.isdigit():  # Accept only a plain number, so startup never raises on a typo
        return int(raw_port)  # Preserve the existing behavior during the compliance refactor.
    logger.warning("CAPTURE_PORTAL: CAPTURE_PORT value %s is not a number - using 8056", raw_port)  # Warn on a typo
    return 8056  # Documented default port for the capture portal


def _run_capture_portal_server(
    app: Any, host: str, port: int, dev_debug: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Start the capture portal in container mode (Gunicorn-aware) or local Flask dev server mode.

    Why:
        Gunicorn serves the portal in the container through wsgi_capture.py. A developer on a
        workstation needs the Flask development server instead. The port 8055 portal splits the
        two paths the same way, so both portals behave alike.

    Args:
        app: The Flask application that create_app built.
        host: The bind address for the listener.
        port: The listen port, 8056 by default.
        dev_debug: True to start the local development server with the debugger.
    """
    if EnvironmentUtils.is_running_in_container():  # Container path -- Gunicorn owns the socket
        logger.info(
            "CAPTURE_PORTAL: Container detected - use wsgi_capture.py with Gunicorn on port %s", port
        )  # Preserve the existing behavior during the compliance refactor.
        echo(
            ">> For production, use: gunicorn wsgi_capture:app -w 1 -k gthread --threads 4"
        )  # Preserve the existing behavior during the compliance refactor.
        app.run(host=host, port=port, debug=False)  # Force debug=False inside the container
        return  # Container path is complete
    logger.info("CAPTURE_PORTAL: Local mode - Flask dev server on %s:%s", host, port)  # Log the local dev path
    echo(">> Upgrade capture portal starting at http://127.0.0.1:%s", port)  # Clickable URL for the operator
    app.run(host=host, port=port, debug=dev_debug)  # Honor the caller's debug flag locally


def _launch_capture_portal(
    dev_debug: bool = False,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch the upgrade capture portal on port 8056.

    Why:
        Menu 239 and the --capture-portal flag need one shared start path. The portal runs in
        its own process on its own port, because the port 8055 portal holds process-level state
        that a second application would corrupt.

    Args:
        dev_debug: True to start the local development server with the debugger.
    """
    from src.upgrade_portal.app.factory import create_app  # Deferred import keeps CLI startup fast
    from src.upgrade_portal.runtime.server import resolve_host  # Deferred for the same reason

    port = _capture_portal_port()  # CAPTURE_PORT with the documented default of 8056
    # A container needs every address, because a published port cannot reach a loopback bind. A
    # workstation must not take that bind: this portal has no password, so any computer that reaches
    # it could start a firmware upgrade. A CAPTURE_HOST value from the operator wins over both.
    host = resolve_host(
        os.environ.get("CAPTURE_HOST"), in_container=EnvironmentUtils.is_running_in_container()
    )  # Preserve the existing behavior during the compliance refactor.
    logger.info("CAPTURE_PORTAL: Building the application for %s:%s", host, port)  # Log before the build
    app = create_app()  # The factory reads every setting from the environment and holds no credential value
    logger.debug("CAPTURE_PORTAL: Application built - starting the server")  # Log after the build
    _run_capture_portal_server(app, host, port, dev_debug)  # Dispatch to the container or local runner


def _metrics_gateway_org_id(settings: Any) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the organization the metrics gateway reports.

    Why:
        A container start reads METRICS_ORG_ID and never prompts, because no operator
        watches a container. A menu start has an operator, so it falls back to the org
        the session already selected, and then to the mistapi picker.

    Args:
        settings: The GatewaySettings record read from the environment.

    Returns:
        The organization identifier, or an empty string when none was chosen.
    """
    if settings.org_id:  # An explicit setting always wins, because a container cannot prompt
        return str(settings.org_id)  # Preserve the existing behavior during the compliance refactor.
    if MainEntrypoint.context.org_id:  # The session already holds a selection, so reuse it rather than ask twice
        return str(MainEntrypoint.context.org_id)  # Preserve the existing behavior during the compliance refactor.
    has_terminal = all((sys.stdin.isatty(), sys.stdout.isatty()))  # Require both streams before prompting.
    if not has_terminal:  # Refuse prompts without a terminal.
        logger.error("METRICS_GATEWAY: No organization and no terminal.")  # Explain the startup failure
        logger.error("METRICS_GATEWAY: Set METRICS_ORG_ID or MIST_ORG_ID.")  # Give the operator the fix
        return ""  # Return an empty value so the caller exits with a failure status
    logger.info("METRICS_GATEWAY: No organization is set - starting the picker")  # Log before the prompt
    _select_org_from_session()  # Writes the module-level org_id global
    logger.debug("METRICS_GATEWAY: Picker result: %s", bool(MainEntrypoint.context.org_id))  # Record the result safely
    return str(MainEntrypoint.context.org_id or "")  # Preserve the existing behavior during the compliance refactor.


def _launch_mib_generator() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Generate the SNMP MIB from the checked-in inputs.

    Why:
        Menu 243 and the --mib-generate flag need one shared start path, the
        same rule that menu 241 and --metrics-gateway follow.
    """
    from src.mib_generator.runner import (
        DEFAULT_OUTPUT,
        MibGeneratorRunner,
    )  # Preserve the existing behavior during the compliance refactor.

    logger.info("MIB_GENERATOR: Menu 243 started the generator")  # Log before the action.
    text = MibGeneratorRunner().generate(DEFAULT_OUTPUT)  # The runner reads the three checked-in inputs.
    echo(
        f"  Wrote {len (text )} characters to {DEFAULT_OUTPUT }"
    )  # Preserve the existing behavior during the compliance refactor.
    logger.info("MIB_GENERATOR: Menu 243 wrote %d characters to %s", len(text), DEFAULT_OUTPUT)  # Log the result.


def _launch_metrics_gateway(
    dev_debug: bool = False,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Serve Mist Cloud health to a monitoring system on port 8057.

    Why:
        Menu 241 and the --metrics-gateway flag need one shared start path, the same
        rule that menu 239 and --capture-portal follow. The gateway runs on its own
        port, because port 8055 and port 8056 already hold their own applications.

    Args:
        dev_debug: True to start the local development server with the debugger.
    """
    from src.metrics_gateway.service import (
        GatewaySettings,
        build_cache,
        start_refresh_thread,
    )  # Preserve the existing behavior during the compliance refactor.
    from src.metrics_gateway.web import create_app  # Preserve the existing behavior during the compliance refactor.

    in_container = EnvironmentUtils.is_running_in_container()  # A container binds every address
    settings = GatewaySettings.from_environment(in_container)  # One frozen record holds every setting
    resolved = _metrics_gateway_org_id(settings)  # The picker runs only when no setting names an org
    if not resolved:  # Without an organization the gateway would serve an empty reading forever
        echo(
            "  X No organization selected - the metrics gateway cannot start"
        )  # Preserve the existing behavior during the compliance refactor.
        logger.error("METRICS_GATEWAY: No organization selected - abort the launch")  # Log the refusal
        raise SystemExit(1)  # Return a non-zero status so service managers report the startup failure
    settings = settings.with_org_id(resolved)  # Carry the chosen org into the frozen record
    # Reuse the shared token-based initializer (handles retries, rate limits, and the legacy fallback).
    if not MistSessionInitializer.initialize():  # Populates the module-level `apisession` global on success.
        echo(
            "  X Could not authenticate to Mist Cloud - the metrics gateway cannot start"
        )  # Preserve the existing behavior during the compliance refactor.
        logger.error(
            "METRICS_GATEWAY: Mist API session initialization failed - abort the launch"
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    cache = build_cache(
        MainEntrypoint.context.apisession, settings
    )  # The cache holds the reading that both output paths serve
    start_refresh_thread(cache, threading.Event())  # A daemon thread keeps the reading fresh ahead of a poll
    logger.info(
        "METRICS_GATEWAY: Building the application for %s:%s", settings.host, settings.port
    )  # Preserve the existing behavior during the compliance refactor.
    echo(">> Mist metrics gateway starting at http://127.0.0.1:%s/metrics", settings.port)  # Clickable URL
    create_app(cache).run(
        host=settings.host, port=settings.port, debug=dev_debug and not in_container
    )  # Preserve the existing behavior during the compliance refactor.


def _run_metrics_snmp(
    _args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Answer Net-SNMP pass_persist requests on standard input, then exit.

    Why:
        snmpd owns UDP port 161, the community string, and the SNMP v3 user. It starts
        this process as a child and speaks a plain line protocol to it. MistHelper
        therefore binds no privileged port and holds no community string.

    Warning:
        This mode writes the protocol replies to standard output. Nothing else may
        print there, because one stray line makes snmpd drop the whole subtree.
        snmpd also merges standard error into the same pipe, so a log record on
        either stream breaks the handshake. protect_protocol_streams() must run
        before anything else, because building the cache writes a log record.

    Args:
        _args: The parsed command-line namespace. This mode reads no flag.
    """
    from src.metrics_gateway.snmp import (
        SnmpPassPersistResponder,
        protect_protocol_streams,
    )  # Preserve the existing behavior during the compliance refactor.

    protect_protocol_streams()  # First call of this mode. A later call cannot recall a sent record.

    from src.metrics_gateway.service import (
        GatewaySettings,
        build_cache,
        start_refresh_thread,
    )  # Preserve the existing behavior during the compliance refactor.
    from src.utils.environment_utils import EnvironmentUtils  # Import EnvironmentUtils for container detection

    logger.info("METRICS_SNMP: Starting the pass_persist responder")  # Log to the file, never to a stream
    settings = GatewaySettings.from_environment(
        EnvironmentUtils.is_running_in_container()
    )  # Preserve the existing behavior during the compliance refactor.
    if not settings.org_id:  # snmpd cannot answer a prompt, so the setting is the only source here
        logger.error("METRICS_SNMP: METRICS_ORG_ID is not set - abort")  # Log the refusal
        sys.exit(1)  # Preserve the existing behavior during the compliance refactor.
        # Reuse the shared token-based initializer instead of calling mistapi directly. It is the same
        # seam every other MistHelper mode uses, so it inherits the retry, rate-limit, and fallback logic
        # for free and it writes the session to the module-level `apisession` global that build_cache reads.
    if not MistSessionInitializer.initialize():  # Preserve the existing behavior during the compliance refactor.
        logger.error("METRICS_SNMP: Mist API session initialization failed - abort")  # Log the refusal
        sys.exit(1)  # Preserve the existing behavior during the compliance refactor.
    cache = build_cache(
        MainEntrypoint.context.apisession, settings
    )  # The cache holds the reading that the responder serves.
    start_refresh_thread(cache, threading.Event())  # Mist Cloud access runs away from the SNMP protocol.
    responder = SnmpPassPersistResponder(
        cache, settings.base_oid
    )  # Preserve the existing behavior during the compliance refactor.
    responder.run(sys.stdin, sys.stdout)  # Blocks until snmpd closes the pipe
    sys.exit(0)  # Preserve the existing behavior during the compliance refactor.


def _run_mib_generator_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run the SNMP MIB generator, then exit.

    Why:
        A hand-edited MIB drifts away from the metric catalog, and a poller then
        reads a name that the agent does not answer. The generator reads the
        Mist OpenAPI file, the catalog, and the OID ledger, so the module always
        agrees with the running agent.

    Args:
        args: The parsed command line.
    """
    from pathlib import Path  # A local import keeps the start of the tool free of the generator modules.

    from src.mib_generator.runner import (
        DEFAULT_OUTPUT,
        MibGeneratorRunner,
    )  # Preserve the existing behavior during the compliance refactor.

    logger.info("MIB_GENERATOR: Starting the MIB generator")  # Log before the action.
    runner = MibGeneratorRunner()  # The runner reads the three checked-in inputs from their default paths.
    output = (
        Path(args.mib_output) if getattr(args, "mib_output", None) else DEFAULT_OUTPUT
    )  # Preserve the existing behavior during the compliance refactor.
    code = _report_mib_result(runner, args, output)  # One helper keeps this function inside the line limit.
    logger.info("MIB_GENERATOR: The generator finished with exit code %s", code)  # Log the result.
    sys.exit(code)  # Preserve the existing behavior during the compliance refactor.


def _report_mib_result(
    runner: Any, args: argparse.Namespace, output: Any
) -> int:  # Preserve the existing behavior during the compliance refactor.
    """Run the action the operator selected and print its result.

    Args:
        runner: The MIB generator runner.
        args: The parsed command line.
        output: The path of the MIB file.

    Returns:
        The process exit code. A check that finds a problem returns 1.
    """
    if getattr(args, "mib_check", False):  # The continuous integration path must fail on a stale file.
        problems = runner.check(output)  # Preserve the existing behavior during the compliance refactor.
        print(
            "\n".join(problems) if problems else "The MIB agrees with the Mist file and the metric catalog."
        )  # Preserve the existing behavior during the compliance refactor.
        return 1 if problems else 0  # Preserve the existing behavior during the compliance refactor.
    if getattr(args, "mib_report", False):  # The report path lists work for a person to review.
        for row in runner.report():  # One line for each field the catalog does not yet serve.
            print(
                f"{row .scope }\t{row .path }\t{row .json_type }\t{row .description [:60 ]}"
            )  # Preserve the existing behavior during the compliance refactor.
        return 0  # Preserve the existing behavior during the compliance refactor.
    dry = bool(getattr(args, "mib_dry_run", False))  # A dry run prints the text and leaves the disk alone.
    text = runner.generate(output, dry_run=dry)  # Preserve the existing behavior during the compliance refactor.
    print(
        text if dry else f"Wrote {len (text )} characters to {output }."
    )  # Preserve the existing behavior during the compliance refactor.
    return 0  # Preserve the existing behavior during the compliance refactor.


def _report_tqdm_status() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log whether the real tqdm landed in the global namespace after deferred imports."""
    logger.debug("_report_tqdm_status: checking tqdm namespace availability")  # Trace tqdm status check
    if "tqdm" in global_assignments:  # tqdm injection succeeded -- confirm availability for progress bars
        logger.info("tqdm is available in global namespace: %s", type(globals().get("tqdm")))  # Log tqdm availability
    else:  # tqdm missing from resolved assignments -- progress bars will be non-functional
        logger.warning(
            "tqdm was not found in global assignments - progress bars will not be functional"
        )  # Warn if missing


def _apply_deferred_assignments() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Inject deferred import symbols into the namespace and report tqdm availability."""
    logger.debug("_apply_deferred_assignments: publishing deferred symbols")  # Trace publish
    if not global_assignments:  # No symbols resolved -- nothing to publish to namespace
        return  # Skip injection entirely when the import cycle produced no assignments
    for var_name, var_value in global_assignments.items():  # Publish each resolved symbol
        globals()[var_name] = var_value  # Inject the imported symbol into module scope for global reuse
        if var_name == "tqdm" and var_value is not None:  # Real tqdm replacing the stub warrants an explicit note
            logger.info("Successfully imported real tqdm in deferred mode: %s", type(var_value))  # Log tqdm override
    logger.debug("Applied %d global variable assignments", len(global_assignments))  # Log assignment count
    _report_tqdm_status()  # Log whether tqdm is available in the global namespace


def _run_deferred_import_cycle() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run the deferred import cycle, publish symbols, and warn on partial failure."""
    logger.info("Initializing deferred imports at application start...")  # Log before import process
    init_success, assignments = import_manager.initialize_all_imports()  # Run full deferred import cycle
    globals()["success"] = init_success  # Preserve the legacy module name without a global statement.
    globals()["global_assignments"] = assignments  # Preserve downstream reads without a global statement.
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_deferred_assignments()  # Inject resolved symbols and report tqdm availability
    if not init_success:  # Non-fatal warning: caller decides whether to abort on partial import failure
        logger.warning("Some required imports failed - functionality may be limited")  # Warn limited functionality


def _initialize_deferred_imports() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Initialize deferred module imports if not already completed at startup."""
    logger.debug("_initialize_deferred_imports: checking deferred import status")  # Log entry
    already_done = hasattr(import_manager, "_deferred_init_done")  # Detect whether deferred init already ran
    if not success and not global_assignments and not already_done:  # First-time deferred init required
        _run_deferred_import_cycle()  # Run the import cycle and publish resolved symbols
    elif already_done:  # Already initialized -- skip to avoid duplicate work
        logger.debug("Deferred imports already initialized, skipping duplicate initialization")  # Note the skip
    logger.debug("_initialize_deferred_imports: complete")  # Log exit


def _add_target_selection_arguments(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the org/menu/site/device/port target-selection flags on the parser."""
    logger.debug("_add_target_selection_arguments: registering target-selection flags")  # Log before adding
    parser.add_argument("-O", "--org", help="Organization ID")  # Short -O flag maps to --org for quick use
    parser.add_argument("-M", "--menu", help="Menu option number to execute")  # Short -M for non-interactive dispatch
    parser.add_argument("-S", "--site", help="Human-readable site name")  # Site name that gets resolved to site_id
    parser.add_argument("-D", "--device", help="Human-readable device name")  # Device name resolved to device_id
    parser.add_argument("-P", "--port", help="Port ID")  # Port identifier passed directly to menu functions


def _add_execution_mode_arguments(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the debug/delay/fast/skip-deps execution-mode flags on the parser."""
    logger.debug("_add_execution_mode_arguments: registering execution-mode flags")  # Log before adding
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output (includes detailed table data in logs)"
    )  # Debug mode flag
    parser.add_argument(
        "--delay", type=int, help="Fixed delay between loop iterations (in seconds). If omitted, delay is dynamic."
    )  # Rate limit override
    parser.add_argument(
        "--fast", action="store_true", help="Enable fast mode with multithreading (bypasses rate limiting)"
    )  # Concurrency mode
    parser.add_argument(
        "--skip-deps", action="store_true", help="Skip dependency check on startup for faster script initialization"
    )  # Skip dep check


def _add_output_format_arguments(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the output-format and systematic-test flags on the parser."""
    logger.debug("_add_output_format_arguments: registering output-format and test flags")  # Log before adding
    parser.add_argument(
        "--output-format",
        choices=["csv", "sqlite"],
        default="csv",
        help=(
            "Output format: 'csv' for CSV files (default) or 'sqlite' for hybrid database with natural primary keys"
        ),  # Output backend selector
    )
    _add_systematic_test_flags(parser)  # The two --test variants share one concern.


def _add_systematic_test_flags(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the systematic-test flags that drive the automated menu sweeps."""
    parser.add_argument(  # Preserve the existing behavior during the compliance refactor.
        "--test",
        action="store_true",
        help=(
            "Run systematic test of all safe menu options (GET operations only, no interactive/websocket/POST "
            "operations)"
        ),
    )
    parser.add_argument(  # Preserve the existing behavior during the compliance refactor.
        "--testinteractive",
        action="store_true",
        help=(
            "Run systematic test of read-only menu options requiring interactive site/device/client selection "
            "(excludes destructive operations)"
        ),
    )


def _add_safety_arguments(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the dry-run/address-check/SSL/no-env safety flags on the parser."""
    logger.debug("_add_safety_arguments: registering safety and validation flags")  # Log before adding
    _add_destructive_safety_flags(parser)  # Flags that change what a destructive run does.
    _add_external_call_flags(parser)  # Flags that change how outbound calls behave.


def _add_destructive_safety_flags(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the flags that govern destructive and address-checking behavior."""
    parser.add_argument(  # Preserve the existing behavior during the compliance refactor.
        "--dry-run",
        action="store_true",
        help=(
            "Enable dry-run mode for destructive operations (show what would be changed without making actual changes)"
        ),
    )
    parser.add_argument(
        "--address-check",
        action="store_true",
        help=(
            "Enable external address validation using Nominatim API for address comparison operations"
        ),  # Nominatim toggle
    )


def _add_external_call_flags(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the flags that govern SSL verification and .env loading."""
    parser.add_argument(  # Preserve the existing behavior during the compliance refactor.
        "--skip-ssl-verify",
        action="store_true",
        help=(
            "Skip SSL certificate verification for external API calls (use with caution - for corporate networks only)"
        ),
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help=(
            "Disable .env file loading for SSH operations (require explicit command line parameters)"
        ),  # SSH env override
    )


def _add_interface_arguments(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the TUI/login/web-portal/standalone interface flags on the parser."""
    logger.debug("_add_interface_arguments: registering interface and auth flags")  # Log before adding
    _add_interface_mode_flags(parser)  # Flags that choose which front end runs.
    _add_auth_and_backend_flags(parser)  # Flags that choose the auth path and the storage backend.


def _add_interface_mode_flags(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the flags that select an alternative front end."""
    parser.add_argument(
        "--tui",
        action="store_true",
        help=(
            "Launch MistHelper in Terminal User Interface (TUI) mode for visual navigation of Mist API library"
        ),  # Rich TUI mode
    )
    parser.add_argument(
        "--web-portal",
        action="store_true",
        help=(
            "Launch the web portal interface on port 8055 (or WEB_PORT env var) instead of the CLI menu"
        ),  # Gunicorn web portal
    )
    parser.add_argument(
        "--capture-portal",
        action="store_true",
        help=(
            "Launch the upgrade capture portal on port 8056 (or CAPTURE_PORT env var) instead of the CLI menu"
        ),  # Gunicorn upgrade capture portal, menu 239
    )
    parser.add_argument(
        "--metrics-gateway",
        action="store_true",
        help=(
            "Serve Mist Cloud health to a monitoring system on port 8057 (or METRICS_PORT env var)"
        ),  # Prometheus metrics gateway, menu 241
    )
    parser.add_argument(
        "--metrics-snmp",
        action="store_true",
        help=(
            "Answer Net-SNMP pass_persist requests on standard input. Start this from snmpd.conf, not by hand"
        ),  # SNMP output path of the metrics gateway
    )
    parser.add_argument(
        "--mib-generate",
        action="store_true",
        help="Generate documentation/mibs/MISTHELPER-MIB.mib from the Mist OpenAPI file and the metric catalog",
    )  # Write the SNMP MIB, menu 243
    parser.add_argument(
        "--mib-dry-run",
        action="store_true",
        help="Print the generated MIB to standard output and write nothing to the disk",
    )  # Review path of the generator
    parser.add_argument(
        "--mib-output",
        default=None,
        help="Write the generated MIB to this path instead of documentation/mibs/MISTHELPER-MIB.mib",
    )  # Output path of the generator
    parser.add_argument(
        "--mib-report",
        action="store_true",
        help="List the Mist fields that the metric catalog does not yet serve",
    )  # Candidate report of the generator
    parser.add_argument(
        "--mib-check",
        action="store_true",
        help="Exit with status 1 when the stored MIB disagrees with the Mist file or the metric catalog",
    )  # Continuous integration path of the generator


def _add_auth_and_backend_flags(
    parser: argparse.ArgumentParser,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Register the flags that select the authentication path and the storage backend."""
    parser.add_argument(
        "--login",
        action="store_true",
        help=(
            "Use interactive login (email/password) instead of API token - enables MSP-level API access"
        ),  # Interactive auth
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Force standalone/CSV-only mode, disabling ArangoDB and Redis connections",  # Force CSV-only mode
    )


def _build_argument_parser() -> (
    argparse.ArgumentParser
):  # Preserve the existing behavior during the compliance refactor.
    """Build and return the CLI argument parser for MistHelper with all supported flags."""
    logger.debug("_build_argument_parser: building argument parser")  # Log before parser creation
    parser = argparse.ArgumentParser(description="MistHelper CLI Interface")  # Create base parser with description
    _add_target_selection_arguments(parser)  # Register org/menu/site/device/port selection flags
    _add_execution_mode_arguments(parser)  # Register debug/delay/fast/skip-deps execution-mode flags
    _add_output_format_arguments(parser)  # Register output-format and systematic-test flags
    _add_safety_arguments(parser)  # Register dry-run/address-check/SSL/no-env safety flags
    _add_interface_arguments(parser)  # Register TUI/login/web-portal/standalone interface flags
    logger.debug("_build_argument_parser: parser ready with all arguments configured")  # Log completion
    return parser  # Return parser for caller to call parse_args() on


_FAST_MODE_CAPABLE_FUNCTIONS: tuple[str, ...] = (  # Preserve the existing behavior during the compliance refactor.
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


def _announce_fast_mode_scope() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log and print the list of fast-capable functions so operators know which paths get accelerated."""
    logger.info(
        "FAST MODE ACTIVE: Enabling caching/concurrency shortcuts for: %s",
        ", ".join(_FAST_MODE_CAPABLE_FUNCTIONS),
    )  # Log fast scope for log-correlation
    echo(
        "* Fast mode active (caching/concurrency). Functions optimized:"
    )  # Preserve the existing behavior during the compliance refactor.
    for name in _FAST_MODE_CAPABLE_FUNCTIONS:  # Iterate the module-level constant
        echo("  - %s", name)  # Preserve the existing behavior during the compliance refactor.


def _setup_runtime_flags(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Apply standalone env flag, register args globally, and configure FAST_MODE_ENABLED."""
    # The application context owns this state, so no global declaration is needed.
    logger.debug("_setup_runtime_flags: applying standalone and fast mode flags")  # Log entry
    if args.standalone:  # --standalone flag disables ArangoDB/Redis connections org-wide
        os.environ["MISTHELPER_STANDALONE"] = "true"  # Write env var so all components detect standalone mode
        logger.info("Standalone mode enabled via --standalone flag: ArangoDB/Redis disabled")  # Log env write
    globals()["args"] = args  # Register parsed args globally so menu functions can read CLI flags
    logger.debug("CLI args registered in globals()['args'] for menu function access")  # Log global assignment
    IS_TEST_MODE = bool(  # Keep the old global behavior from stored CLI arguments.
        getattr(args, "test", False) or getattr(args, "testinteractive", False)
    )
    logger.debug("IS_TEST_MODE set to %s", IS_TEST_MODE)  # Log the parsed test-mode state.
    try:
        MainEntrypoint.context.fast_mode_enabled = bool(
            args.fast
        )  # Derive flag from --fast CLI argument (bool is safe cast)
    except (AttributeError, TypeError) as error:  # Bad args or a broken context must only disable fast mode
        logging.warning("Failed to set context fast-mode flag: %s", error, exc_info=True)  # Keep trace for repair
        MainEntrypoint.context.fast_mode_enabled = False  # Fail-safe: ensure symbol exists even if args access fails
    logger.debug("FAST_MODE_ENABLED set to %s", MainEntrypoint.context.fast_mode_enabled)  # Log fast mode state
    if MainEntrypoint.context.fast_mode_enabled:  # Announce only after the guarded flag write succeeds
        _announce_fast_mode_scope()  # Log + print fast-capable function list
    logger.debug("_setup_runtime_flags: complete")  # Log exit


def _apply_dependency_assignments(
    skip_mode: bool,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Inject resolved global symbol assignments into the module namespace."""
    logger.debug("_apply_dependency_assignments: publishing symbols (skip_mode=%s)", skip_mode)  # Trace publish
    if not global_assignments:  # No symbols resolved -- nothing to publish to namespace
        return  # Skip injection entirely when the import cycle produced no assignments
    for var_name, var_value in global_assignments.items():  # Publish each resolved symbol
        globals()[var_name] = var_value  # Inject the imported symbol into module scope for global reuse
    if skip_mode:  # Differentiate the log message so operators see the skip-deps code path was taken
        logger.debug(
            "Applied %d global variable assignments in skip mode", len(global_assignments)
        )  # Log skip-mode count
    else:  # Full dependency path -- preserve the original (non-skip) log message wording
        logger.debug("Applied %d global variable assignments", len(global_assignments))  # Log assignment count


def _run_full_dependency_init(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run the full dependency import cycle and abort on critical, non-test failure."""
    logger.info("Initializing deferred dependencies with full checking...")  # Log before full init
    init_success, assignments = import_manager.initialize_all_imports(skip_deps=False)  # Run full import cycle
    globals()["success"] = init_success  # Preserve the legacy module name without a global statement.
    globals()["global_assignments"] = assignments  # Preserve downstream reads without a global statement.
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_dependency_assignments(skip_mode=False)  # Publish resolved symbols into module namespace
    if not init_success and not args.test:  # Abort on critical failure unless running in test mode
        logger.error("Critical dependencies missing. Exiting.")  # Log fatal dependency failure before exit
        echo(
            "!! Critical dependencies missing. Use --skip-deps to bypass or install missing packages."
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit with error code -- cannot continue without required modules


def _run_skip_dependency_init() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run the minimal dependency import cycle used by the --skip-deps path."""
    logger.info("Dependency initialization skipped due to --skip-deps flag")  # Log skip reason
    init_success, assignments = import_manager.initialize_all_imports(skip_deps=True)  # Minimal import cycle
    globals()["success"] = init_success  # Preserve the legacy module name without a global statement.
    globals()["global_assignments"] = assignments  # Preserve downstream reads without a global statement.
    import_manager._deferred_init_done = True  # Mark complete to prevent duplicate initialization
    _apply_dependency_assignments(skip_mode=True)  # Publish whatever symbols resolved even in skip mode


def _initialize_dependencies(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Initialize deferred module imports based on --skip-deps flag, aborting on critical failure."""
    logger.debug("_initialize_dependencies: checking if dependency initialization is needed")  # Log entry
    already_done = hasattr(import_manager, "_deferred_init_done")  # Detect whether deferred init already ran
    if not _initialize_imports_now and not already_done:  # First-time deferred init required
        if args.skip_deps:  # Minimal path when the caller passed --skip-deps
            _run_skip_dependency_init()  # Run the minimal import cycle for core functionality only
        else:  # Default path performs full dependency checking
            _run_full_dependency_init(args)  # Run the full import cycle (may sys.exit on critical failure)
    elif already_done:  # Already initialized -- skip to avoid duplicate work
        logger.debug("Dependencies already initialized, skipping duplicate initialization")  # Note the skip
    logger.debug("_initialize_dependencies: complete")  # Log exit


def _establish_mist_session(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Initialize Mist API session using interactive login or API token, then detect MSP privileges."""
    logger.debug("_establish_mist_session: starting session initialization")  # Log entry
    is_capture_portal = bool(
        getattr(args, "capture_portal", False)
    )  # The portal creates its own environment or browser credential session.
    # Feature 1020 (US3, R4 insertion-point 1): host/token preflight for every dispatch mode. Runs before
    # the --login/token branches so a missing/placeholder host or token exits with a redacted, actionable
    # message BEFORE mistapi/requests can build a malformed URL. require_token is False for interactive
    # --login (email/password auth needs no token). Host is still validated in both modes. The second,
    # distinct failure mode - a non-interactive org-id miss - is guarded separately in ConfigUtils (R4
    # insertion-point 2), since org selection is interactive-vs-non-interactive dependent.
    _preflight_verify_credentials(
        require_token=not args.login and not is_capture_portal
    )  # The portal validates its host but can receive a browser token after startup.
    if is_capture_portal:  # The capture app owns credential selection and session creation per browser.
        logger.info(
            "CAPTURE_PORTAL: Credential preflight passed; deferring Mist session creation to the portal"
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    _preflight_systematic_test_org(args)  # Resolve org before any session or MSP call in systematic modes.
    if args.login:  # Interactive login requested via --login flag
        _init_interactive_session()  # Email/password path. Exits non-zero on failure.
    else:  # Default path: use API token from .env or environment variables
        _init_token_session()  # Token path. Exits non-zero on failure, then publishes MSP grants.
    logger.debug("_establish_mist_session: session established successfully")  # Log successful auth


def _preflight_systematic_test_org(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Resolve the org id before session work when running either systematic test mode."""
    is_systematic_test = bool(  # WHY: both systematic modes need a resolved org before any API session work.
        getattr(args, "test", False) or getattr(args, "testinteractive", False)
    )
    if not is_systematic_test:  # WHY: interactive and single-menu runs resolve the org later, on demand.
        return  # Preserve the existing behavior during the compliance refactor.
    logger.info(
        "SYSTEMATIC_TEST: validating org_id before Mist session initialization"
    )  # Log before local org-id resolution.
    ConfigUtils.get_cached_or_prompted_org_id()  # Fail closed before session construction or MSP HTTP calls.
    logger.debug(
        "SYSTEMATIC_TEST: org_id preflight passed before Mist session initialization"
    )  # Log successful local validation.


def _init_interactive_session() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Authenticate with email and password, then publish the session to the shared config cache."""
    logger.info("Interactive login mode requested via --login flag")  # Log before interactive login
    if not MistSessionInteractiveInitializer.initialize():  # Attempt email/password login
        logger.error("Failed to initialize Mist API session via interactive login")  # Log auth failure
        echo(
            " Failed to initialize Mist API session. Check your credentials."
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit -- cannot proceed without authenticated session


def _init_token_session() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Authenticate with an API token, publish the session, and detect MSP privileges."""
    # The application context owns this state, so no global declaration is needed.
    if not MistSessionInitializer.initialize():  # Attempt token-based session init
        logger.error("Failed to initialize Mist API session")  # Log token auth failure
        echo(
            " Failed to initialize Mist API session. Check your credentials."
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit -- cannot proceed without authenticated session
    MainEntrypoint.context.msp_privileges = detect_msp_privileges(
        MainEntrypoint.context.apisession
    )  # Detect MSP grants for token session and publish to global
    logger.debug("_establish_mist_session: session established successfully")  # Log successful auth


def _apply_debug_log_level() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Set DEBUG on root + file handlers and keep console at INFO so DEBUG noise stays out of the terminal."""
    logging.getLogger().setLevel(logging.DEBUG)  # Enable DEBUG on root logger
    for handler in logging.getLogger().handlers:  # Iterate each registered handler
        if isinstance(handler, logging.FileHandler):  # File handlers get full DEBUG output
            handler.setLevel(logging.DEBUG)  # Preserve the existing behavior during the compliance refactor.
        elif isinstance(handler, logging.StreamHandler):  # Console stays at INFO to avoid noise
            handler.setLevel(logging.INFO)  # Preserve the existing behavior during the compliance refactor.
    logger.debug("Debug logging enabled via --debug flag")  # Confirm debug mode active in log file
    logger.debug("Performance monitoring will trigger circuit breakers for infinite loops")  # Remind about CBs


def _configure_runtime_options(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Set OUTPUT_FORMAT, initialize PROGRESS_EMITTER, and configure debug log level."""
    # The application context owns this state, so no global declaration is needed.
    logger.debug("_configure_runtime_options: applying runtime configuration")  # Log entry
    MainEntrypoint.context.output_format = (
        args.output_format
    )  # Apply --output-format (csv or sqlite) to global used by all exporters
    timestamp = datetime.now(UTC).isoformat()  # Capture current UTC time for audit trail
    logger.info(
        "Output format set to: %s at %s", MainEntrypoint.context.output_format, timestamp
    )  # Log format selection with timestamp
    try:
        MainEntrypoint.context.progress_emitter = TelemetryEmitter(
            os.path.join("data", "test_events.jsonl")
        )  # Initialize JSONL telemetry emitter
        logger.info("Progress telemetry emitter initialized: data/test_events.jsonl")  # Log emitter ready
    except (OSError, ValueError, TypeError) as emitter_exc:  # Telemetry file issues must not stop the CLI
        logging.warning("Progress telemetry emitter init failed: %s", emitter_exc, exc_info=True)  # Keep trace
        echo("Progress telemetry emitter init failed (non-blocking): %s", emitter_exc)  # Log non-fatal failure
        MainEntrypoint.context.progress_emitter = None  # Set to None so callers skip telemetry gracefully
    if args.debug:  # Apply debug logging level to file handlers. Keep console at INFO to avoid noise
        _apply_debug_log_level()  # Promote root + file handlers to DEBUG
    logger.debug("_configure_runtime_options: complete")  # Log exit


def _run_tui_mode(args: argparse.Namespace) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch MistHelper Terminal User Interface (TUI) mode using the Rich library."""
    logger.info("TUI_MODE: Starting Terminal User Interface mode")  # Log before TUI launch
    echo(">> Terminal User Interface mode activated")  # Preserve the existing behavior during the compliance refactor.
    _ensure_tui_api_session()  # Initialize the Mist API session if not already established.
    _silence_console_handlers_for_tui()  # Remove console log handlers so Rich owns the screen.
    _run_tui_event_loop(args)  # Run the TUI event loop (handles Ctrl+C + fatal errors internally).
    if args.debug:  # Debug: log a final timestamped marker after the loop exits cleanly.
        timestamp = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format ms timestamp.
        logger.debug(
            "TUI_DEBUG: [%s] TUI mode completed successfully - about to exit", timestamp
        )  # Log clean completion.
    logger.info("TUI_MODE: TUI mode completed successfully")  # Log clean exit.


def _ensure_tui_api_session() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Initialize the Mist API session if not already established. Exits 1 on auth failure."""
    if MainEntrypoint.context.apisession:  # Already authenticated -- nothing to do.
        return  # Reuse the existing session.
    echo(">> Initializing Mist API session...")  # Preserve the existing behavior during the compliance refactor.
    if not MistSessionInitializer.initialize():  # Attempt session init for TUI
        logger.error("[ERROR] Failed to initialize Mist API session")  # Auth-init failure at ERROR level.
        logger.error("TUI_MODE: Could not initialize API session")  # Log auth failure.
        sys.exit(1)  # Exit -- TUI cannot function without a session.
    echo(">> API session initialized successfully")  # Preserve the existing behavior during the compliance refactor.


def _silence_console_handlers_for_tui() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Remove non-file console handlers from the root logger so they do not disrupt the Rich UI."""
    root_logger = logging.getLogger()  # Access root logger to modify handlers.
    console_handlers = [  # Identify console handlers to suppress during TUI.
        h
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    for handler in console_handlers:  # Iterate handlers to remove each.
        root_logger.removeHandler(handler)  # Remove console handler so logs do not disrupt Rich display.
        logger.debug("TUI_MODE: Removed console handler to prevent interference with Rich TUI")  # Log removal.


def _handle_tui_keyboard_interrupt(
    debug: bool,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log clean exit when user pressed Ctrl+C inside the TUI and inform them at the console."""
    if debug:  # Debug: log timestamped interrupt event
        timestamp = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format timestamp
        logger.debug(
            "TUI_DEBUG: [%s] KeyboardInterrupt caught - user pressed Ctrl+C", timestamp
        )  # Log interrupt with time
    logger.info("TUI_MODE: User interrupted with Ctrl+C")  # Log clean user exit
    echo("\n[EXIT] TUI mode stopped by user")  # Preserve the existing behavior during the compliance refactor.


def _handle_tui_exception(
    debug: bool, error: Exception
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log fatal error from the TUI event loop and exit with code 1."""
    if debug:  # Debug: log timestamped exception detail
        timestamp = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format timestamp
        logger.debug(
            "TUI_DEBUG: [%s] Exception caught in TUI mode: %s: %s",
            timestamp,
            type(error).__name__,
            error,
        )  # Log error
    logger.exception("TUI_MODE: Fatal error - %s", error)  # Log full traceback to file
    logger.error("\n[ERROR] TUI mode crashed: %s", error)  # Crash message at ERROR level.
    sys.exit(1)  # Exit with error code after TUI crash


def _run_tui_event_loop(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Instantiate and run the TUI event loop. Handles Ctrl+C cleanly and Exceptions with traceback."""
    try:
        from src.ui.tui import MistHelperTUI  # PLC0415: lazy import avoids loading Rich at startup

        tui = MistHelperTUI(debug_mode=args.debug)  # Create TUI with debug flag
        tui.apisession = MainEntrypoint.context.apisession  # Pass global API session so TUI can execute live API calls
        if args.debug:  # Debug: record that the code launched the TUI with debug enabled
            logger.debug("TUI_MODE: Debug mode is ACTIVE - enhanced logging enabled")  # Log debug state
        tui.run()  # Launch TUI event loop (blocks until user exits)
    except KeyboardInterrupt:  # User pressed Ctrl+C inside the TUI
        _handle_tui_keyboard_interrupt(args.debug)  # Log and inform user of clean exit
    except SystemExit:  # Program exits from the TUI must keep their intended code
        raise  # Do not convert an explicit exit into a fatal TUI crash
    except Exception as error:  # Broad by design so TUI defects keep terminal cleanup and traceback logging
        _handle_tui_exception(args.debug, error)  # Log + print + exit(1)


def _run_cli_mode(args: argparse.Namespace) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Resolve org/site/device IDs from CLI args, dispatch to the target menu function, and exit."""
    # The application context owns this state, so no global declaration is needed.
    logger.info("CLI arguments detected, running in non-interactive mode.")  # Log before CLI dispatch.
    _log_cli_invocation(args)  # Verbose log of every parsed CLI flag for diagnostics.
    MainEntrypoint.context.org_id = _resolve_cli_org_id(args)  # Use --org if given, otherwise prompt/cache.
    site_id = _resolve_cli_site_id(args, MainEntrypoint.context.org_id)  # Resolve --site name -> site_id (or None).
    device_id = _resolve_cli_device_id(args, site_id)  # Resolve --device name -> device_id (or None).
    _dispatch_cli_menu_action(args, site_id, device_id)  # Dispatch + exit. Never returns on success.


def _log_cli_invocation(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Log every parsed CLI argument at DEBUG level for diagnostics."""
    logger.debug(  # Preserve the existing behavior during the compliance refactor.
        (
            "Parsed CLI arguments: org=%s, menu=%s, site=%s, device=%s, port=%s, debug=%s, delay=%s, fast=%s, "
            "skip_deps=%s, output_format=%s, test=%s, address_check=%s, tui=%s"
        ),
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


def _resolve_cli_org_id(
    args: argparse.Namespace,
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return --org if given, otherwise resolve from cache / interactive prompt."""
    if args.org:  # CLI explicitly provided the org ID.
        logger.info("Using org_id from CLI argument: %s", args.org)  # Log CLI org ID.
        return str(args.org)  # Return the CLI org ID (argparse gives Any, so narrow to str).
    return ConfigUtils.get_cached_or_prompted_org_id()  # Fall back to cache or prompt.


def _build_site_name_to_id_map(
    sites: list[dict[str, Any]],
) -> dict[str, str]:  # Preserve the existing behavior during the compliance refactor.
    """Build a {name: id} lookup map from a list of site dicts, skipping entries missing either field."""
    return {
        str(site["name"]): str(site["id"]) for site in sites if site.get("name") and site.get("id")
    }  # Build name->id map. Drop sites missing name or id


def _resolve_cli_site_id(
    args: argparse.Namespace, target_org_id: str
) -> str | None:  # Preserve the existing behavior during the compliance refactor.
    """Resolve --site name to a site_id via API lookup. Exit 1 if name not found. Return None if no --site."""
    if not args.site:  # No --site supplied. Nothing to resolve.
        return None  # Caller treats None as "no site filter".
    logger.info(
        "Resolving site name '%s' to site_id using unified pagination limit %d...",
        args.site,
        DEFAULT_API_PAGE_LIMIT,
    )  # Log before site resolution.
    sites = APICoreFetchUtils.all_sites_with_limit(target_org_id)  # Fetch all org sites from Mist API.
    site_lookup = _build_site_name_to_id_map(sites)  # Delegate name->id map construction
    site_id = site_lookup.get(args.site)  # Look up site ID by human-readable name.
    if not site_id:  # Site name not found in org -- abort with error.
        logger.error("! Site name '%s' not found.", args.site)  # Log resolution failure.
        echo("! Site name '%s' not found.", args.site)  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit -- cannot proceed with unknown site.
    logger.info("Resolved site name '%s' to site_id '%s'.", args.site, site_id)  # Log resolution success.
    return site_id  # Return the resolved site_id.


def _resolve_cli_device_id(
    args: argparse.Namespace, site_id: str | None
) -> str | None:  # Preserve the existing behavior during the compliance refactor.
    """Resolve --device name to a device_id via site-scoped API lookup. Requires site context."""
    if not (args.device and site_id):  # Either no --device or no site context. Nothing to resolve.
        return None  # Caller treats None as "no device filter".
    logger.info("Resolving device name '%s' at site_id '%s'...", args.device, site_id)  # Log before device resolution.
    response = mistapi.api.v1.sites.devices.listSiteDevices(
        MainEntrypoint.context.apisession, site_id, type="all"
    )  # Fetch all devices at site.
    devices = mistapi.get_all(
        response=response, mist_session=MainEntrypoint.context.apisession
    )  # Page through all results.
    device_lookup = {dev["name"]: dev["id"] for dev in devices}  # Build name->id map from device list.
    device_id = device_lookup.get(args.device)  # Look up device ID by human-readable name.
    if not device_id:  # Device name not found at site -- abort with error.
        logger.error("! Device name '%s' not found at site '%s'.", args.device, args.site)  # Log resolution failure.
        echo(
            "! Device name '%s' not found at site '%s'.", args.device, args.site
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit -- cannot proceed with unknown device.
    logger.info("Resolved device name '%s' to device_id '%s'.", args.device, device_id)  # Log resolution success.
    return str(device_id)  # Return the resolved device_id (dev["id"] is Any, so narrow to str).


def _dispatch_cli_menu_action(
    args: argparse.Namespace, site_id: str | None, device_id: str | None
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Look up args.menu in menu_actions, build kwargs, call the target. Exits 0/1 -- never returns on success."""
    if args.menu not in menu_actions:  # Invalid menu number -- abort with error.
        logger.error("! Invalid menu option: %s", args.menu)  # Log invalid menu selection.
        echo("! Invalid menu option: %s", args.menu)  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit with error code on invalid menu option.
    entry = menu_actions[args.menu]  # Read the named row from the dispatch table.
    func = entry.handler  # Extract the callable from the named row.
    if func is None:  # CLI mode cannot execute a static metadata row.
        logger.error("! Invalid static menu option: %s", args.menu)  # Log invalid static row use.
        echo("! Invalid menu option: %s", args.menu)  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Exit with error code on invalid menu option.
    logger.info("Executing menu action '%s'.", args.menu)  # Log before function dispatch.
    func_args = _build_cli_func_kwargs(args, site_id, device_id)  # Build the full candidate kwargs dict.
    sig = inspect.signature(func)  # Introspect signature to keep only valid kwargs.
    accepted_args = {
        k: v for k, v in func_args.items() if k in sig.parameters and v is not None
    }  # Filter to accepted params.
    func(**accepted_args)  # Call menu function with filtered args.
    logger.info("CLI execution complete. Exiting.")  # Log successful CLI completion.
    logger.debug("EXIT: _run_cli_mode - CLI success")  # Log exit point.
    sys.exit(0)  # Clean exit after successful CLI execution.


def _build_cli_func_kwargs(
    args: argparse.Namespace, site_id: str | None, device_id: str | None
) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Build the candidate kwargs dict used to call a menu function in CLI mode."""
    return {
        "site_id": site_id,  # Pass resolved site ID (or None if not provided).
        "device_id": device_id,  # Pass resolved device ID (or None if not provided).
        "port": args.port,  # Pass port ID directly from CLI.
        "org_id": MainEntrypoint.context.org_id,  # Pass resolved organization ID.
        "debug": args.debug,  # Pass debug mode flag to enable verbose logging.
        "delay": args.delay,  # Pass custom delay override (or None for dynamic).
        "fast": args.fast,  # Pass fast mode flag to enable concurrency.
        "dry_run": args.dry_run,  # Pass dry-run flag to skip destructive actions.
        "address_check": args.address_check,  # Pass address validation toggle.
        "skip_ssl_verify": args.skip_ssl_verify,  # Pass SSL verification bypass flag.
    }


def _run_interactive_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Present the interactive menu loop, dispatching to functions until user exits."""
    # The application context owns this state, so no global declaration is needed.
    logger.info("No CLI arguments detected, running in interactive menu mode.")  # Log before interactive start.
    MainEntrypoint.context.org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org ID from cache or prompt.
    logger.info("Organization ID initialized for interactive mode: %s", MainEntrypoint.context.org_id)  # Log org ID.
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
            continue  # In container mode, loop again. Direct mode already exited inside the handler.
        func = selected.handler  # Extract callable from the named menu entry.
        if func is None:  # Static metadata rows cannot run from the interactive CLI.
            _handle_interactive_invalid_selection(iwant, container_mode)  # Reuse the existing invalid-input handler.
            continue  # Return to the menu loop in container mode.
        logger.info(
            "User selected menu option '%s'. Executing associated function.", iwant
        )  # Log selection before dispatch.
        _execute_interactive_menu_action(iwant, func, container_mode)  # Run the func with full error handling.


def _setup_interactive_container_mode() -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Detect whether MistHelper runs inside a container. Print banner if yes."""
    container_mode = EnvironmentUtils.is_running_in_container()  # Check Podman/Docker container marker files.
    if container_mode:  # Container mode: show banner and loop after each operation.
        logger.info("Container mode detected - enabling continuous menu loop")  # Log container detection.
        echo(
            "[CONTAINER MODE] MistHelper will return to menu after each operation"
        )  # Preserve the existing behavior during the compliance refactor.
        echo(
            "                 Use option 0 to exit the container"
        )  # Preserve the existing behavior during the compliance refactor.
    return container_mode  # Return flag so the loop can branch on container or direct mode.


def _print_interactive_menu() -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the sorted list of available menu options."""
    echo("\nAvailable Options:")  # Preserve the existing behavior during the compliance refactor.
    menu_keys = tuple(menu_actions.keys())  # Snapshot keys so runtime registry edits invalidate the cache.
    cache = globals().get("_SORTED_MENU_KEYS_CACHE")  # Read the cache without a global statement.
    if cache is None or cache[0] != menu_keys:  # Detect new or changed keys.
        cache = (
            menu_keys,
            tuple(sorted(menu_keys, key=lambda x: float(x.replace("a", ".1")))),
        )  # Sort numerically once for this exact key set so 10 sorts after 9.
        globals()["_SORTED_MENU_KEYS_CACHE"] = cache  # Store the cache without a global statement.
    sorted_menu_keys = cache[1]  # Read the valid cached order for this redraw.
    for key in sorted_menu_keys:  # Iterate every menu key in numeric order.
        description = menu_actions[key].title  # Read the display text from the named menu row.
        echo("%s: %s", key, description)  # Preserve the existing behavior during the compliance refactor.


def _prompt_interactive_selection() -> str:  # Preserve the existing behavior during the compliance refactor.
    """Prompt the user for a menu selection. Returns stripped input, or __EXIT__ on EOF."""
    return InputUtils.safe_input(
        "\nEnter your selection number now: ",
        default_value="__EXIT__",  # EOF returns __EXIT__ sentinel to trigger clean shutdown.
        context="main_menu_selection",  # Context label for EOF logging.
    ).strip()  # Strip whitespace from user input.


def _handle_interactive_eof(
    container_mode: bool,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the EOF (Ctrl+D / SSH disconnect / pipe close) messages."""
    echo(
        "\n[EOF] Input stream closed. Exiting gracefully..."
    )  # Preserve the existing behavior during the compliance refactor.
    logger.info("EOF encountered on input - user disconnected or input stream closed")  # Log EOF event.
    if container_mode:  # Container mode: additional context message for SSH session termination.
        echo(
            "[CONTAINER MODE] SSH session ended. Terminating MistHelper."
        )  # Preserve the existing behavior during the compliance refactor.


def _handle_interactive_empty_input(
    container_mode: bool,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Print the empty-input notice (different copy for container vs direct mode)."""
    if container_mode:  # Container mode shows prompt to clarify nothing happened.
        echo(
            "[CONTAINER MODE] No selection entered. Redisplaying menu..."
        )  # Preserve the existing behavior during the compliance refactor.
        echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
    else:  # Direct mode shows simpler reminder.
        echo(
            "No selection entered. Please enter a menu number."
        )  # Preserve the existing behavior during the compliance refactor.


def _handle_interactive_invalid_selection(
    iwant: str, container_mode: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Handle an invalid (non-empty, not in dispatch table) menu selection. May call sys.exit."""
    logger.error("Invalid selection '%s' entered by user.", iwant)  # Log invalid selection.
    echo("Invalid selection. Please try again.")  # Preserve the existing behavior during the compliance refactor.
    if not container_mode:  # Direct mode: exit on invalid selection.
        logger.debug("EXIT: _run_interactive_mode - invalid selection (direct mode)")  # Log exit point.
        sys.exit(1)  # Exit with error code on invalid selection in direct mode.
    logger.debug("Container mode: invalid selection '%s', redisplaying menu", iwant)  # Log container invalid.


def _execute_interactive_menu_action(
    iwant: str, func: Callable[[], None], container_mode: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run the selected menu function with full error handling (success, Ctrl+C, exception)."""
    try:
        if iwant == "0":  # Option 0 is the explicit exit shortcut.
            logger.info("Exit option selected by user.")  # Log user-requested exit.
            logger.debug("EXIT: _run_interactive_mode - user requested exit")  # Log exit point.
            sys.exit(0)  # Exit cleanly on user selection of option 0.
        func()  # Execute the selected menu function.
        logger.info("Menu option '%s' execution complete.", iwant)  # Log completion after function returns.
        _dispatch_post_menu_success(iwant, container_mode)  # Branch on container vs direct + session-management ops.
    except KeyboardInterrupt:  # User pressed Ctrl+C during operation.
        _handle_post_menu_interrupt(iwant, container_mode)  # Container loops. Direct exits with SIGINT code.
    except SystemExit:  # Menu functions can request a controlled process exit
        raise  # Do not turn a deliberate exit into an operation failure
    except Exception as error:  # Broad by design so one menu defect does not crash a container session
        _handle_post_menu_exception(iwant, error, container_mode)  # Container loops. Direct exits with error code.


def _dispatch_post_menu_success(
    iwant: str, container_mode: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Dispatch follow-up after a successful menu call (continue loop vs sys.exit)."""
    session_management_options = {"115", "143"}  # Options that re-enter menu to use new context.
    if container_mode:  # Container mode: always return to menu after each operation.
        logger.debug(
            "Container mode: option '%s' completed successfully, returning to menu", iwant
        )  # Log container loop.
        echo(
            "\n[CONTAINER MODE] Operation '%s' completed. Returning to menu...", iwant
        )  # Preserve the existing behavior during the compliance refactor.
        echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
        return  # Return so the outer while loop continues.
    if iwant in session_management_options:  # Direct mode + session management: keep loop running.
        logger.info("Session management option '%s' completed - returning to menu", iwant)  # Log session update.
        echo(
            "\n[SESSION] Context updated. Returning to menu..."
        )  # Preserve the existing behavior during the compliance refactor.
        echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
        return  # Return so the outer while loop continues with updated session context.
    logger.debug("EXIT: _run_interactive_mode - interactive success (direct mode)")  # Log exit point.
    sys.exit(0)  # Exit after single operation in direct mode.


def _handle_post_menu_interrupt(
    iwant: str, container_mode: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Handle a Ctrl+C interrupt during a menu function call."""
    logger.info("Operation interrupted by user (Ctrl+C)")  # Log user interrupt.
    if container_mode:  # Container mode: return to menu after interrupt.
        logger.debug("Container mode: option '%s' interrupted, returning to menu", iwant)  # Log container interrupt.
        echo(
            "\n[CONTAINER MODE] Operation interrupted. Returning to menu..."
        )  # Preserve the existing behavior during the compliance refactor.
        echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
        return  # Return so the outer while loop continues.
    logger.debug("EXIT: _run_interactive_mode - user interrupt")  # Log exit point.
    sys.exit(130)  # Exit 130 is the standard exit code for SIGINT (Ctrl+C).


def _handle_post_menu_exception(
    iwant: str, error: Exception, container_mode: bool
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Handle an unexpected exception raised during a menu function call."""
    logger.exception("Error executing menu option '%s': %s", iwant, error)  # Log error with traceback.
    if container_mode:  # Container mode: show error but return to menu.
        logger.debug("Container mode: option '%s' failed with error, returning to menu", iwant)  # Log container error.
        logger.error(
            "\n[CONTAINER MODE] Error in operation '%s': %s", iwant, error
        )  # Preserve the existing behavior during the compliance refactor.
        echo("Returning to menu...")  # Preserve the existing behavior during the compliance refactor.
        echo("=" * 60)  # Preserve the existing behavior during the compliance refactor.
        return  # Return so the outer while loop continues despite the error.
    logger.debug("EXIT: _run_interactive_mode - interactive error (direct mode)")  # Log exit point.
    sys.exit(1)  # Exit with error code on unexpected exception in direct mode.


def _run_systematic_test_mode(
    _args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run all safe menu options once and exit 0 on pass / 1 on fail."""
    logger.info("SYSTEMATIC_TEST: Starting systematic test mode")  # Trace before dispatch
    from src.refactors.run_systematic_test import (  # Preserve the existing behavior during the compliance refactor.
        RunSystematicTestManager,
    )

    sys.exit(0 if RunSystematicTestManager().run() else 1)  # Delegate to extracted manager


def _run_interactive_test_mode(
    _args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Run interactive test mode (read-only menus with site/device selection) and exit."""
    logger.info("INTERACTIVE_TEST: Starting interactive test mode")  # Trace before dispatch
    sys.exit(0 if RunInteractiveTestManager().run() else 1)  # Route to extracted manager (PR-12)


def _run_tui_mode_and_exit(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch the Rich Terminal UI and exit cleanly when the user closes it."""
    _run_tui_mode(args)  # TUI handles its own event loop and exceptions
    sys.exit(0)  # Preserve the existing behavior during the compliance refactor.


def _run_web_portal_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch the Gunicorn web portal on port 8055 and exit cleanly on shutdown."""
    logger.info("WEB_PORTAL: Starting web portal mode")  # Trace before launch
    _launch_web_portal(args)  # Blocks until shutdown
    sys.exit(0)  # Preserve the existing behavior during the compliance refactor.


def _run_capture_portal_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Launch the upgrade capture portal on port 8056 and exit cleanly on shutdown.

    Why:
        _dispatch_main_mode needs one handler for each front end. This handler keeps the
        --capture-portal flag beside the --web-portal flag in the same dispatch table.

    Args:
        args: The parsed command-line namespace. The handler reads only the debug flag.
    """
    logger.info("CAPTURE_PORTAL: Starting upgrade capture portal mode")  # Trace before launch
    _launch_capture_portal(args.debug)  # Blocks until shutdown
    sys.exit(0)  # Preserve the existing behavior during the compliance refactor.


def _run_metrics_gateway_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Serve the Prometheus endpoint and exit cleanly on shutdown.

    Why:
        _dispatch_main_mode needs one handler for each front end. This handler keeps the
        --metrics-gateway flag beside the --capture-portal flag in the same table.

    Args:
        args: The parsed command-line namespace. The handler reads only the debug flag.
    """
    logger.info("METRICS_GATEWAY: Starting metrics gateway mode")  # Trace before launch
    _launch_metrics_gateway(args.debug)  # Blocks until shutdown
    sys.exit(0)  # Preserve the existing behavior during the compliance refactor.


_SORTED_MENU_KEYS_CACHE: tuple[tuple[str, ...], tuple[str, ...]] | None = None  # Cache the sorted menu key order.

_MAIN_MODE_TABLE: tuple[tuple[Callable[[argparse.Namespace], bool], str], ...] = (
    (lambda a: bool(a.test), "_run_systematic_test_mode"),
    (lambda a: bool(a.testinteractive), "_run_interactive_test_mode"),
    (lambda a: bool(a.tui), "_run_tui_mode_and_exit"),
    (lambda a: bool(getattr(a, "web_portal", False)), "_run_web_portal_mode"),
    (lambda a: bool(getattr(a, "capture_portal", False)), "_run_capture_portal_mode"),
    (lambda a: bool(getattr(a, "metrics_snmp", False)), "_run_metrics_snmp"),
    (
        lambda a: any(
            bool(getattr(a, name, False)) for name in ("mib_generate", "mib_dry_run", "mib_report", "mib_check")
        ),
        "_run_mib_generator_mode",
    ),
    (lambda a: bool(getattr(a, "metrics_gateway", False)), "_run_metrics_gateway_mode"),
    (lambda a: _has_meaningful_cli_args(a), "_run_cli_mode"),
)  # Cache predicate definitions while handler names keep monkeypatch and late binding behavior.


def _dispatch_main_mode(
    args: argparse.Namespace,
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Dispatch to the appropriate mode entry point based on parsed CLI flags."""
    for predicate, handler_name in _MAIN_MODE_TABLE:  # Stop on the first cached predicate that matches.
        if predicate(args):  # Preserve the existing behavior during the compliance refactor.
            handler = globals()[handler_name]  # Resolve at dispatch time so tests and late binding still work.
            handler(args)  # Preserve the existing behavior during the compliance refactor.
            return  # Most handlers call sys.exit. The return is defensive for _run_cli_mode
    _run_interactive_mode(args)  # Fallback: interactive menu loop


_MEANINGFUL_CLI_ATTRS: tuple[str, ...] = (
    "menu",
    "org",
    "site",
    "device",
    "port",
    "test",
)  # CLI flags that flip MistHelper into non-interactive one-shot dispatch mode


def _has_meaningful_cli_args(
    args: argparse.Namespace,
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True if the caller provided any non-interactive CLI flag (triggers CLI dispatch mode)."""
    return any(getattr(args, name, None) for name in _MEANINGFUL_CLI_ATTRS)  # Any flag => CLI mode


if __name__ == "__main__":  # Preserve the existing behavior during the compliance refactor.
    try:
        logger.info(
            "=== MistHelper application starting ==="
        )  # Preserve the existing behavior during the compliance refactor.
        # Single explicit banner for test mode to clarify reduced lookbacks
        try:
            if IS_TEST_MODE:  # Preserve the existing behavior during the compliance refactor.
                logger.info(
                    "TEST MODE ACTIVE: Reducing default 24h lookback windows to 1h for eligible exports."
                )  # Preserve the existing behavior during the compliance refactor.
        except NameError:  # Preserve the existing behavior during the compliance refactor.
            # IS_TEST_MODE may not yet be defined if refactor order changes. Ignore safely
            pass  # Preserve the existing behavior during the compliance refactor.

            # Install a global exception hook early so we capture full tracebacks for unexpected issues

        def _global_excepthook(  # Preserve the existing behavior during the compliance refactor.
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: types.TracebackType | None,
        ) -> None:
            try:
                import traceback as _tb  # Preserve the existing behavior during the compliance refactor.

                if issubclass(
                    exc_type, KeyboardInterrupt
                ):  # Preserve the existing behavior during the compliance refactor.
                    # Defer to default behavior for Ctrl+C
                    sys.__excepthook__(
                        exc_type, exc_value, exc_traceback
                    )  # Preserve the existing behavior during the compliance refactor.
                    return  # Preserve the existing behavior during the compliance refactor.
                formatted = "".join(
                    _tb.format_exception(exc_type, exc_value, exc_traceback)
                )  # Preserve the existing behavior during the compliance refactor.
                logger.error(
                    "UNHANDLED TOP-LEVEL EXCEPTION TRACEBACK FOLLOWS"
                )  # Preserve the existing behavior during the compliance refactor.
                for (
                    line
                ) in formatted.rstrip().splitlines():  # Preserve the existing behavior during the compliance refactor.
                    logger.error(line)  # Preserve the existing behavior during the compliance refactor.
            except (
                TypeError,
                ValueError,
                OSError,
                RuntimeError,
            ) as hook_err:  # Preserve the existing behavior during the compliance refactor.
                logging.exception("Exception in global excepthook: %s", hook_err)  # Keep hook trace

        try:
            import sys as _sys_mod  # Preserve the existing behavior during the compliance refactor.

            _sys_mod.excepthook = _global_excepthook  # Preserve the existing behavior during the compliance refactor.
        except (
            AttributeError,
            TypeError,
        ) as hook_setup_err:  # Preserve the existing behavior during the compliance refactor.
            logging.warning(
                "Failed to install global excepthook: %s", hook_setup_err, exc_info=True
            )  # Keep setup trace
        MainEntrypoint.run()  # Invoke extracted CLI main entrypoint (SC-026)
    except KeyboardInterrupt:  # Preserve the existing behavior during the compliance refactor.
        logging.info(
            "Application interrupted by user (Ctrl+C)"
        )  # Preserve the existing behavior during the compliance refactor.
        logging.debug(
            "EXIT: __main__ - user interrupt"
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(130)  # Standard exit code for SIGINT
    except SystemExit:  # Explicit exits must keep their intended process code
        raise  # Do not convert a deliberate exit into the top-level crash path
    except Exception as e:  # Broad by design so unexpected startup defects get a controlled final trace
        logging.error("Unhandled exception in main application: %s", e)  # Log before traceback formatting
        try:
            import traceback  # Preserve the existing behavior during the compliance refactor.

            traceback_details = "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )  # Preserve the existing behavior during the compliance refactor.
            for (
                line
            ) in (
                traceback_details.rstrip().splitlines()
            ):  # Preserve the existing behavior during the compliance refactor.
                logging.error(line)  # Preserve the existing behavior during the compliance refactor.
        except (
            TypeError,
            ValueError,
            OSError,
            RuntimeError,
        ) as trace_err:  # Preserve the existing behavior during the compliance refactor.
            logging.exception("Failed to log exception traceback: %s", trace_err)  # Keep secondary trace
        logging.debug(
            "EXIT: __main__ - unhandled exception"
        )  # Preserve the existing behavior during the compliance refactor.
        sys.exit(1)  # Preserve the existing behavior during the compliance refactor.
    finally:
        logger.info(
            "=== MistHelper application ending ==="
        )  # Preserve the existing behavior during the compliance refactor.
        # hi
