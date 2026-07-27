"""TroubleshootUtils -- Marvis troubleshooting delegation wrapper.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 39).
Thin facade over ``ExtractedMarvisTroubleshootUtils`` that builds a
``MarvisTroubleshootDeps`` bundle from live-global collaborators and forwards
to the implementation module, plus the interactive menu dispatcher for
Marvis (VNA) troubleshooting.

Direct imports cover stdlib only (importlib, logging). Every live-global
read (``apisession``, ``mistapi``, ``ConfigUtils``, ``PromptClientUtils``,
``PromptUtils``, ``DataExporter``, ``MarvisDataUtilsFactory``,
``DataProcessingUtils``, ``MarvisTroubleshootDeps``,
``ExtractedMarvisTroubleshootUtils``, ``InputUtils``) is resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside the methods that need
them. Callers continue to reach the class through the
``MistHelper.TroubleshootUtils`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for menu-dispatch lifecycle events.
from typing import Any  # WHY: MarvisTroubleshootDeps is resolved lazily. Annotate as Any.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class TroubleshootUtils:  # Marvis troubleshoot delegators.
    """Delegation wrapper for extracted Marvis troubleshooting implementation."""

    @staticmethod
    def _build_deps() -> Any:  # Build the deps bundle.
        """Build dependency container for extracted troubleshooting logic."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of all deps + MarvisTroubleshootDeps class.
        return mh.MarvisTroubleshootDeps(  # Assemble the deps.
            apisession=mh.apisession,
            mistapi=mh.mistapi,
            config_utils=mh.ConfigUtils,
            prompt_client_utils=mh.PromptClientUtils,
            prompt_utils=mh.PromptUtils,
            data_exporter=mh.DataExporter,
            marvis_data_utils=mh.MarvisDataUtilsFactory.instance(),
            data_processing_utils=DataProcessingUtils,
        )

    @staticmethod
    def client_connectivity() -> None:  # Troubleshoot client connectivity.
        """Delegated client connectivity troubleshooting implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ExtractedMarvisTroubleshootUtils.
        mh.ExtractedMarvisTroubleshootUtils.client_connectivity(
            TroubleshootUtils._build_deps()
        )  # Delegate to the impl.

    @staticmethod
    def device_performance() -> None:  # Diagnose device performance.
        """Delegated device performance troubleshooting implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ExtractedMarvisTroubleshootUtils.
        mh.ExtractedMarvisTroubleshootUtils.device_performance(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def network_connectivity() -> None:  # Analyze network connectivity.
        """Delegated network connectivity troubleshooting implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ExtractedMarvisTroubleshootUtils.
        mh.ExtractedMarvisTroubleshootUtils.network_connectivity(
            TroubleshootUtils._build_deps()
        )  # Delegate to the impl.

    @staticmethod
    def _print_marvis_menu() -> None:
        """Emit the interactive Marvis troubleshooting header banner.

        Why:
            #886 slice 17/N migrates ``print()`` to ``logging.warning`` so that
            ruff T20 can stay armed globally. Header + divider are consolidated
            into a single warning record so the banner arrives atomically in
            handlers that buffer per-record (for example remote log shippers).
        """
        logging.warning(
            " Starting Marvis (VNA - Virtual Network Assistant) Troubleshooting\n%s\n",
            "=" * 65,
        )

    @staticmethod
    def _print_marvis_options() -> None:
        """Emit the 5 numbered Marvis troubleshooting choices to the user.

        Why:
            #886 slice 17/N. Merged into a single ``logging.warning`` so the
            menu prints atomically and cannot be interleaved with other log
            records under concurrent producers.
        """
        logging.warning(
            " Marvis AI Troubleshooting Options:\n"
            "1. Troubleshoot client connectivity issues (guided client selection)\n"
            "2. Diagnose device performance problems (guided device selection)\n"
            "3. Analyze network connectivity issues (site-level analysis)\n"
            "4. View organization Marvis insights and capabilities\n"
            "5. Exit\n"
        )

    @staticmethod
    def _handle_marvis_invalid_choice(choice: str) -> None:
        """Handle an out-of-range Marvis menu selection (warn + log).

        Why:
            #886 slice 17/N replaces the user-facing ``print()`` with
            ``logging.warning`` so all three log lines (visible notice + audit
            trail + debug trace) travel through the same sink.
        """
        logging.warning(" Invalid option selected.")  # User-visible notice
        logging.warning("MARVIS DEBUG: Invalid troubleshooting option selected: %s", choice)  # Audit trail
        logging.debug("MARVIS DEBUG: Exiting launch_interactive() due to invalid choice")  # Trace exit reason

    @staticmethod
    def _handle_marvis_exit() -> None:
        """Handle the Marvis exit menu pick.

        Why:
            #886 slice 17/N. The exit notice is promoted to ``logging.warning``
            because the caller expects it to be captured at the default pytest
            log level and displayed by every stream handler configuration.
        """
        logging.debug("MARVIS DEBUG: User chose to exit")  # Trace the exit
        logging.warning("Exiting Marvis troubleshooting.")  # Tell the user

    @staticmethod
    def _invoke_marvis_client_connectivity() -> None:
        """Run the client-connectivity troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.client_connectivity()")  # Trace the call
        TroubleshootUtils.client_connectivity()

    @staticmethod
    def _invoke_marvis_device_performance() -> None:
        """Run the device-performance troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.device_performance()")  # Trace the call
        TroubleshootUtils.device_performance()

    @staticmethod
    def _invoke_marvis_network_connectivity() -> None:
        """Run the network-connectivity troubleshooter."""
        logging.debug("MARVIS DEBUG: Calling TroubleshootUtils.network_connectivity()")  # Trace the call
        TroubleshootUtils.network_connectivity()

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
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + apisession + InputUtils.
        logging.info("Entering TroubleshootUtils.launch_interactive")  # Entry envelope for logging compliance
        logging.debug("MARVIS DEBUG: Entering launch_interactive() method")  # Trace the entry.
        TroubleshootUtils._print_marvis_menu()  # Header + divider.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        logging.debug("MARVIS DEBUG: Using org_id: %s for Marvis troubleshooting", org_id)  # %s not f-string
        logging.debug("MARVIS DEBUG: Session state - authenticated: %s", mh.apisession is not None)  # %s not f-string
        TroubleshootUtils._print_marvis_options()  # Show numbered choices.
        choice = mh.InputUtils.safe_input("Select an option (1-5): ", context="marvis_launch_menu").strip()
        logging.debug("MARVIS DEBUG: User selected option: %s", choice)  # %s not f-string
        TroubleshootUtils._dispatch_marvis_choice(choice)  # Route to handler.
        logging.info("Exiting TroubleshootUtils.launch_interactive with choice: %s", choice)  # Exit envelope

    @staticmethod
    def view_insights() -> None:  # View Marvis insights.
        """Delegated Marvis insights and capabilities view implementation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ExtractedMarvisTroubleshootUtils.
        mh.ExtractedMarvisTroubleshootUtils.view_insights(TroubleshootUtils._build_deps())  # Delegate to the impl.

    @staticmethod
    def _display_usage_guide() -> None:  # Show the usage guide.
        """Delegated helper for usage guide display."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ExtractedMarvisTroubleshootUtils.
        mh.ExtractedMarvisTroubleshootUtils._display_usage_guide()  # Delegate to the impl.
