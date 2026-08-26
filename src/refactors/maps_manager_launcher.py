"""MapsManagerLauncher extracted from MistHelper.

Launches the external ``src.maps.maps_manager.MapsManager`` (a ~7,500 line
interactive Dash-based map viewer) from the numbered CLI menu. This module
only owns the thin launcher shell that handles import failure, org-id
prompt, and top-level error surfacing.

Runtime dependencies (``apisession`` global and the ``ConfigUtils`` class)
are still owned by MistHelper.py. They are resolved lazily via
``importlib.import_module`` so the extracted module import-graph stays
flat and monkeypatched attributes are honoured in tests.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes and external Dash object


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info("Resolving MapsManagerLauncher runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug("MapsManagerLauncher runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so apisession/ConfigUtils lookups honour monkeypatch
    )


class MapsManagerLauncher:
    """Launch MapsManager from external maps_manager.py module.

    The external module contains the full interactive map viewer implementation
    (~7,500 lines) supporting standalone execution and MistHelper integration.

    SECURITY: Read-only map viewing with interactive Dash web server

    Usage:
        MapsManagerLauncher().launch()
    """

    def __init__(self) -> None:
        """Initialize launcher with module reference placeholder."""
        logging.info("MapsManagerLauncher init: starting new launcher instance")  # Log construction start
        self.maps_manager: Any = None  # Populated after successful instantiation of external class
        self.org_id: str = ""  # Populated from cache/prompt via ConfigUtils
        self._external_class: Any = None  # Populated by _import_module on successful import
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("MapsManagerLauncher init complete")  # Log after construction

    def _apisession(self) -> Any:
        """Return the current MistHelper apisession so monkeypatched values are honoured."""
        return getattr(self._deps.misthelper_module, "apisession", None)  # Resolve at call-time, not import-time

    def _config_utils(self) -> Any:
        """Return the current MistHelper ConfigUtils class so monkeypatched values are honoured."""
        return self._deps.misthelper_module.ConfigUtils  # Attribute access still honours module monkeypatching

    def launch(self) -> None:
        """Main entry point - orchestrates module import and execution."""
        logging.info("Menu #142: Starting Maps Manager")  # User-visible launch marker preserved from original
        if not self._import_module():  # Bail out early if the external Maps module is unavailable
            return  # Import failure handled inside _import_module
        if not self._get_org_id():  # Bail out early if org id could not be determined
            return  # Org-id failure handled inside _get_org_id
        self._run_interactive_menu()  # Enter the Dash-based interactive menu (blocks until user exits)
        logging.info("Menu #142: Maps Manager session completed")  # Log clean session close

    def _import_module(self) -> bool:
        """Import MapsManager from external module with error handling."""
        logging.info("MapsManagerLauncher: importing MapsManager from src.maps.maps_manager")  # Log pre-import
        try:  # Wrap the lazy import so ImportError is turned into a user-visible message
            from src.maps.maps_manager import MapsManager as ExternalMapsManager  # PLC0415: lazy on purpose

            self._external_class = ExternalMapsManager  # Cache the imported class for later instantiation
            logging.debug("MapsManagerLauncher: MapsManager import succeeded")  # Log post-import success
            return True  # Signal caller that the external class is ready
        except ImportError as error:  # Missing module or bad install
            self._handle_import_error(error)  # Log and print actionable guidance
            return False  # Signal caller to abort the launch

    def _handle_import_error(self, error: ImportError) -> None:
        """Log and display import failure message."""
        logging.error("Failed to import MapsManager from src/maps/maps_manager.py: %s", error)  # Log the error
        # User-visible failure banner
        logging.info("\nERROR: Could not load Maps Manager module.")
        # Suggest the fix
        logging.info("Ensure src/maps/maps_manager.py exists")

    def _get_org_id(self) -> bool:
        """Get organization ID from cache or prompt."""
        logging.info("MapsManagerLauncher: resolving org id via ConfigUtils")  # Log before prompt/cache lookup
        try:  # Wrap prompt so any exception is funneled through the fatal-error handler
            self.org_id = self._config_utils().get_cached_or_prompted_org_id()  # Late-bound ConfigUtils
            logging.debug("MapsManagerLauncher: org id resolved (present=%s)", bool(self.org_id))  # Log resolution
            return bool(self.org_id)  # Empty string means the user aborted - abort launch
        except Exception as error:  # prompt errors must never crash the menu
            self._handle_fatal_error(error)  # Log traceback and surface user-visible error
            return False  # Signal caller to abort the launch

    def _run_interactive_menu(self) -> None:
        """Instantiate and run the Maps Manager interactive menu."""
        logging.info("MapsManagerLauncher: instantiating external MapsManager and entering menu")  # Log entry
        try:  # Wrap instantiation + run so any error is funneled through the fatal-error handler
            if self._external_class is None:  # Defensive - launch() calls _import_module first
                raise RuntimeError("MapsManagerLauncher._external_class not initialized")  # Explicit error
            self.maps_manager = self._external_class(self._apisession(), self.org_id)  # Late-bound apisession
            self.maps_manager.run_interactive_menu()  # Enter blocking interactive loop (Dash web server)
            logging.debug("MapsManagerLauncher: interactive menu returned cleanly")  # Log clean return
        except Exception as error:  # runtime errors must never crash the numbered menu
            self._handle_fatal_error(error)  # Log traceback and surface user-visible error

    def _handle_fatal_error(self, error: Exception) -> None:
        """Log and display fatal error message."""
        logging.error("Error running Maps Manager: %s", error, exc_info=True)  # Log with traceback for postmortem
        # Surface error to user without stack details
        logging.info("\nERROR: %s", error)
