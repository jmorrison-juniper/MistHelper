"""WAN2MigrationLauncher extracted from MistHelper.

Launches the canonical WAN2 migration flow (Menu 149) by wiring
MistHelper-owned runtime dependencies into
``src.gateway.wan2_migration_manager.WAN2MigrationManager`` and invoking
``set_site_variable()``.

Runtime dependencies (``apisession`` global, ``mistapi`` module, the
utility classes ``ConfigUtils``/``CacheUtils``/``OrgSiteExporter``/
``GatewayExportUtils``/``FilePathUtils``/``InputUtils``/``DataExporter``)
are still owned by MistHelper.py. They are resolved lazily via
``importlib.import_module`` so the extracted module import-graph stays
flat and monkeypatched attributes are honoured in tests.

The ``MIST_SITE_EXCLUDE_PREFIX`` constant is imported directly from
``src.refactors.mist_site_exclude_prefix`` (initiative 1015 T-15) --
it is a static string captured at env-init time, so no lazy rebind is
needed.

This module replaces the previous ``WAN2MigrationManager`` delegator
shim (mirror-and-forward pattern) with a proper launcher whose only
public surface is ``launch()``.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes and external manager instance

from src.refactors.mist_site_exclude_prefix import (  # 1015 T-15: canonical constant import.
    MIST_SITE_EXCLUDE_PREFIX,
)


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info("Resolving WAN2MigrationLauncher runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug("WAN2MigrationLauncher runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so global lookups honour monkeypatch in tests
    )


class WAN2MigrationLauncher:
    """Launch WAN2 migration from external wan2_migration_manager module.

    The external module contains the full WAN2 migration implementation
    including site enumeration, WAN2 variable configuration, and
    result reporting. This launcher owns only the numbered-menu
    ceremony: wire runtime dependencies into the canonical class,
    instantiate it, and invoke ``set_site_variable()`` with fatal-error
    surfacing.

    SECURITY: Site variable configuration for WAN2 migration (read/write)

    Usage:
        WAN2MigrationLauncher().launch()
    """

    def __init__(self) -> None:
        """Initialize launcher with late-bound MistHelper handles."""
        logging.info("WAN2MigrationLauncher init: starting new launcher instance")  # Log construction start
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("WAN2MigrationLauncher init complete")  # Log after construction

    def _misthelper(self) -> Any:
        """Return the current MistHelper module so monkeypatched attributes are honoured."""
        return self._deps.misthelper_module  # Resolve at call-time so tests can substitute values

    def launch(self) -> None:
        """Main entry point - wire dependencies and run WAN2 migration."""
        logging.info("Menu #149: Starting WAN2 Migration")  # User-visible launch marker
        try:  # Wrap the full flow so any runtime error is funneled through the fatal-error handler
            self._wire_dependencies()  # Publish MistHelper globals into the canonical manager module
            manager = self._build_manager()  # Instantiate the canonical WAN2MigrationManager
            manager.set_site_variable()  # Run the WAN2 site-variable flow (blocks until user exits)
            logging.debug("Menu #149: WAN2 migration session returned cleanly")  # Log clean session close
        except Exception as error:  # noqa: BLE001 - runtime errors must never crash the numbered menu
            self._handle_fatal_error(error)  # Log traceback and surface user-visible error

    def _wire_dependencies(self) -> None:
        """Configure the canonical wan2_migration_manager module with MistHelper runtime globals."""
        logging.info("WAN2MigrationLauncher: wiring runtime dependencies into wan2_migration_manager")  # Log wire start
        misthelper = self._misthelper()  # Cache module handle for the ten attribute lookups below
        from src.gateway import (
            wan2_migration_manager as wan2_module,  # noqa: PLC0415 - lazy import keeps startup path light
        )

        wan2_module.configure_wan2_migration_dependencies(  # Publish MistHelper-owned deps as frozen dataclass
            wan2_module.WAN2MigrationDependencies(
                apisession=getattr(misthelper, "apisession", None),  # Current apisession honours monkeypatch
                config_utils=misthelper.ConfigUtils,  # Config helper class for org resolution
                cache_utils=misthelper.CacheUtils,  # Cache helper class for site prefix filtering
                org_site_exporter=misthelper.OrgSiteExporter,  # Site exporter used for listing candidate sites
                gateway_export_utils=misthelper.GatewayExportUtils,  # Gateway export utility for device lookup
                file_path_utils=misthelper.FilePathUtils,  # Path helper for CSV inputs and export targets
                input_utils=misthelper.InputUtils,  # Input helper class for user confirmation prompts
                data_exporter=misthelper.DataExporter,  # DataExporter for CSV audit output
                mistapi=misthelper.mistapi,  # Bound mistapi module (attribute access on MistHelper)
                site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,  # 1015 T-15: canonical import.
            )
        )
        logging.debug("WAN2MigrationLauncher: runtime dependencies wired successfully")  # Log wire completion

    def _build_manager(self) -> Any:
        """Instantiate the canonical WAN2MigrationManager with dependencies already wired."""
        logging.info("WAN2MigrationLauncher: instantiating canonical WAN2MigrationManager")  # Log build start
        from src.gateway.wan2_migration_manager import (
            WAN2MigrationManager,  # noqa: PLC0415 - lazy import mirrors _wire_dependencies
        )

        manager = WAN2MigrationManager()  # Canonical class. Constructor pulls wired module globals
        logging.debug("WAN2MigrationLauncher: WAN2MigrationManager instantiated successfully")  # Log build finish
        return manager  # Return the ready-to-run manager to launch()

    def _handle_fatal_error(self, error: Exception) -> None:
        """Log and display fatal error message."""
        logging.error("Error running WAN2 Migration: %s", error, exc_info=True)  # Log with traceback for postmortem
        # WHY: operator-visible error surface (replaces prior print()).
        logging.warning("ERROR: %s", error)
