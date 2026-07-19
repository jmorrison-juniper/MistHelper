"""Mist cloud endpoint catalog and interactive cloud picker."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from collections.abc import Callable  # Typing for the injected safe_input dependency

MIST_CLOUDS: dict[str, tuple[str, str]] = {  # Selectable Mist clouds keyed by menu number
    "1": ("Global 01", "api.mist.com"),  # Default global cloud
    "2": ("Global 02", "api.gc1.mist.com"),  # Secondary global cluster
    "3": ("Global 03", "api.ac2.mist.com"),  # Tertiary global cluster
    "4": ("Global 04", "api.gc2.mist.com"),  # Fourth global cluster
    "5": ("Global 05", "api.gc4.mist.com"),  # Fifth global cluster
    "6": ("EMEA 01", "api.eu.mist.com"),  # Primary EMEA cluster
    "7": ("EMEA 02", "api.gc3.mist.com"),  # Secondary EMEA cluster
    "8": ("EMEA 03", "api.ac6.mist.com"),  # Tertiary EMEA cluster
    "9": ("EMEA 04", "api.gc6.mist.com"),  # Fourth EMEA cluster
    "10": ("APAC 01", "api.ac5.mist.com"),  # Primary APAC cluster
    "11": ("APAC 03", "api.gc7.mist.com"),  # Secondary APAC cluster
}


class CloudSelector:
    """Prompt the user to choose one of the Mist cloud endpoints."""

    def __init__(self, safe_input: Callable[..., str]) -> None:
        """Store the EOF-safe input function used for the interactive prompt."""
        self.safe_input = safe_input  # Injected EOF-safe input wrapper

    @staticmethod
    def catalog() -> dict[str, tuple[str, str]]:
        """Return the cloud catalog mapping menu key -> (label, host)."""
        return MIST_CLOUDS  # Single source of truth for the cloud menu

    def prompt(self) -> tuple[str, str] | None:
        """Render the cloud menu and return the chosen (cloud_name, host) tuple.

        Returns None when the user aborts via EOF (SystemExit).
        """
        logging.info("Prompting user to choose Mist cloud endpoint")  # Trace prompt start
        self._render_menu()  # Print the numbered cloud menu verbatim
        try:
            cloud_choice = self.safe_input(  # Read EOF-safely so SSH disconnects bail out cleanly
                "  Select cloud (1-11, or press Enter for Global 01): ",
                context="interactive_login",
            ).strip()
        except SystemExit:  # safe_input raises SystemExit on EOF
            logging.info("Cloud selection aborted via EOF")  # Trace abort path
            return None  # Signal caller to cancel the login flow
        if cloud_choice == "" or cloud_choice not in MIST_CLOUDS:  # Default to Global 01
            cloud_choice = "1"  # Preserve legacy default behaviour
        cloud_name, host = MIST_CLOUDS[cloud_choice]  # Resolve label + host from catalog
        logging.warning("  Using cloud: %s (%s)", cloud_name, host)  # Legacy console echo routed via logger
        logging.warning("")  # Blank spacer matches the original output exactly
        logging.debug("Cloud selected: %s (%s)", cloud_name, host)  # Trace selection result
        return (cloud_name, host)  # Hand off to the login orchestrator

    @staticmethod
    def _render_menu() -> None:
        """Print the interactive cloud menu using the legacy formatting."""
        logging.warning("")  # Leading blank line matches the original banner spacing
        logging.warning("=" * 60)  # Top divider routed via logger
        logging.warning("  INTERACTIVE MIST API LOGIN")  # Banner heading routed via logger
        logging.warning("=" * 60)  # Bottom divider routed via logger
        logging.warning("")  # Blank spacer matches original output
        logging.warning(
            "  This authentication method uses session/cookie-based login,"
        )  # Legacy explainer routed via logger
        logging.warning(
            "  which can access MSP-level APIs (unlike org-scoped API tokens)."
        )  # Legacy explainer routed via logger
        logging.warning("")  # Blank spacer matches original output
        logging.warning("  Available Mist Clouds:")  # Legacy header routed via logger
        for key, (name, host) in MIST_CLOUDS.items():  # Iterate catalog in insertion order
            logging.warning("    %2s. %-12s (%s)", key, name, host)  # Legacy format string preserved exactly
        logging.warning("")  # Blank spacer matches original output
