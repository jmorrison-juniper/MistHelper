"""ServicePingLauncher extracted from MistHelper.

Launches the canonical WebSocket Service Ping flow (Menu 120) by wiring
MistHelper-owned runtime dependencies into the extracted
``src.websocket.service_ping_manager.ServicePingManager`` and invoking its
``execute()`` entry point.

Runtime dependencies (``apisession`` global, ``mistapi`` module, the
utility classes ``PromptUtils``/``InputUtils``/``APITenantFetchUtils``/
``ConfigUtils``/``APIFetchUtils``, the ``WebSocketManager`` class, and the
``is_debug_mode`` closure) are still owned by MistHelper.py. They are
resolved lazily via ``importlib.import_module`` so the extracted module
import-graph stays flat and monkeypatched attributes are honoured in
tests.

This module replaces the previous ``ServicePingManager`` delegator shim
(mirror-and-forward pattern) with a proper launcher whose only public
surface is ``launch()``.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes and external manager instance

from src.refactors.is_debug_mode import IsDebugMode  # Debug-mode predicate now owned by extracted seam (1012 SC-002)


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info("Resolving ServicePingLauncher runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug("ServicePingLauncher runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so global lookups honour monkeypatch in tests
    )


class ServicePingLauncher:
    """Launch WebSocket Service Ping from external service_ping_manager module.

    The external module contains the full SSR service-ping implementation
    including tenant/service discovery, WebSocket transport, and result
    parsing. This launcher owns only the numbered-menu ceremony: wire
    runtime dependencies into the extracted class, instantiate it, and
    invoke ``execute()`` with fatal-error surfacing.

    SECURITY: WebSocket-driven service ping to SSR gateways (read-only)

    Usage:
        ServicePingLauncher().launch()
    """

    def __init__(self) -> None:
        """Initialize launcher with late-bound MistHelper handles."""
        logging.info("ServicePingLauncher init: starting new launcher instance")  # Log construction start
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("ServicePingLauncher init complete")  # Log after construction

    def _misthelper(self) -> Any:
        """Return the current MistHelper module so monkeypatched attributes are honoured."""
        return self._deps.misthelper_module  # Resolve at call-time so tests can substitute values

    def launch(self) -> None:
        """Main entry point - wire dependencies and run Service Ping."""
        logging.info("Menu #120: Starting WebSocket Service Ping")  # User-visible launch marker
        try:  # Wrap the full flow so any runtime error is funneled through the fatal-error handler
            self._wire_dependencies()  # Publish MistHelper globals into the extracted manager module
            manager = self._build_manager()  # Instantiate the canonical ServicePingManager
            manager.execute()  # Run the interactive ping flow (blocks until user exits)
            logging.debug("Menu #120: Service Ping session returned cleanly")  # Log clean session close
        except Exception as error:  # noqa: BLE001 - runtime errors must never crash the numbered menu
            self._handle_fatal_error(error)  # Log traceback and surface user-visible error

    def _wire_dependencies(self) -> None:
        """Configure the extracted service_ping_manager module with MistHelper runtime globals."""
        logging.info("ServicePingLauncher: wiring runtime dependencies into service_ping_manager")  # Log wire start
        misthelper = self._misthelper()  # Cache module handle for the nine attribute lookups below
        from src.websocket.service_ping_manager import (  # PLC0415: lazy import to keep startup path light
            configure_service_ping_manager_dependencies,
        )

        configure_service_ping_manager_dependencies(  # Publish MistHelper-owned deps into the extracted module
            apisession_dependency=getattr(misthelper, "apisession", None),  # Current apisession honours monkeypatch
            mistapi_dependency=misthelper.mistapi,  # Bound mistapi module (attribute access on MistHelper)
            prompt_utils=misthelper.PromptUtils,  # Prompt helper class for menu flow
            input_utils=misthelper.InputUtils,  # Input helper class for user confirmation
            websocket_manager_class=misthelper.WebSocketManager,  # WebSocket transport class
            is_debug_mode=IsDebugMode.check,  # Debug-mode probe closure (rewired to IsDebugMode.check per 1012 SC-002)
            api_tenant_fetch_utils=misthelper.APITenantFetchUtils,  # Tenant utility class
            config_utils=misthelper.ConfigUtils,  # Config utility helper class
            api_fetch_utils=misthelper.APIFetchUtils,  # API fetch utility class
        )
        logging.debug("ServicePingLauncher: runtime dependencies wired successfully")  # Log wire completion

    def _build_manager(self) -> Any:
        """Instantiate the canonical ServicePingManager with dependencies already wired."""
        logging.info("ServicePingLauncher: instantiating canonical ServicePingManager")  # Log build start
        from src.websocket.service_ping_manager import (  # PLC0415: lazy import mirrors _wire_dependencies pattern
            ServicePingManager as ExternalServicePingManager,
        )

        manager = ExternalServicePingManager()  # Canonical class; constructor pulls wired module globals
        logging.debug("ServicePingLauncher: ServicePingManager instantiated successfully")  # Log build finish
        return manager  # Return the ready-to-run manager to launch()

    def _handle_fatal_error(self, error: Exception) -> None:
        """Log and display fatal error message."""
        logging.error("Error running Service Ping: %s", error, exc_info=True)  # Log with traceback for postmortem
        # WHY: operator-visible error surface (replaces prior print()).
        logging.warning("ERROR: %s", error)
