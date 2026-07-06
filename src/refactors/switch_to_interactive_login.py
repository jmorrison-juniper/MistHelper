"""SwitchToInteractiveLoginManager extracted from MistHelper.

Launches the "switch to interactive login" flow (Menu 143). Owns the
top-level orchestration originally defined as
``switch_to_interactive_login()`` in MistHelper.py and delegates all
underlying work (header print, confirmation prompt, rollback-guarded
login, post-login MSP/org selection) to the four ``_*_switch_login_*``
/ ``_*_interactive_login_*`` helpers that remain in MistHelper.

Runtime dependencies (``apisession`` global, ``org_id`` global mutation,
and the four support helpers) are still owned by MistHelper.py. They are
resolved lazily via ``importlib.import_module`` so the extracted module
import-graph stays flat and monkeypatched attributes are honoured in
tests.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info(  # Log before importing MistHelper module for dependency resolution
        "Resolving SwitchToInteractiveLoginManager runtime dependencies from MistHelper"
    )
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug(  # Log after successful module import for observability
        "SwitchToInteractiveLoginManager runtime dependencies resolved successfully"
    )
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so global lookups honour monkeypatch in tests
    )


class SwitchToInteractiveLoginManager:
    """Switch the running session from API-token auth to interactive email/password login.

    Owns the top-level orchestration originally defined as
    ``switch_to_interactive_login()`` in MistHelper.py. Delegates the
    banner, confirmation, rollback-guarded login attempt, and post-login
    MSP/org selection to the corresponding ``_*_switch_login_*`` /
    ``_*_interactive_login_*`` helpers that remain in MistHelper.

    SECURITY: Prompts the user for credentials; on failure the previous
    ``apisession`` and ``org_id`` globals are rolled back inside the
    helper ``_attempt_interactive_login_with_rollback``.

    Usage:
        SwitchToInteractiveLoginManager().run()
    """

    def __init__(self) -> None:
        """Initialize manager with late-bound MistHelper handles."""
        logging.info(  # Log construction start for observability
            "SwitchToInteractiveLoginManager init: starting new manager instance"
        )
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("SwitchToInteractiveLoginManager init complete")  # Log after construction

    def _misthelper(self) -> Any:
        """Return the current MistHelper module so monkeypatched attributes are honoured."""
        return self._deps.misthelper_module  # Resolve at call-time so tests can substitute values

    def run(self) -> bool:
        """Run the switch-to-interactive-login flow and always return True so the menu loop continues.

        Returns:
            bool: Always ``True`` so the numbered-menu dispatcher keeps looping.
        """
        logging.info("User initiated switch to interactive login")  # Operator action note (kept from original)
        misthelper = self._misthelper()  # Cache module handle for the helper lookups below
        misthelper._print_switch_login_header()  # Show the explanatory banner
        if not misthelper._prompt_switch_login_confirmation():  # User cancelled or EOF'd the prompt
            logging.debug(  # Log cancel path for postmortem tracing
                "SwitchToInteractiveLoginManager: user declined confirmation; staying on menu"
            )
            return True  # Stay on the menu without changing session
        self._attempt_login_and_finalize(misthelper)  # Handle rollback-guarded login + post-login finalize
        return True  # Always return True so the menu loop continues

    def _attempt_login_and_finalize(self, misthelper: Any) -> None:
        """Attempt rollback-guarded interactive login and finalize MSP/org selection on success."""
        logging.info("SwitchToInteractiveLoginManager: attempting rollback-guarded login")  # Log attempt entry
        old_session = getattr(misthelper, "apisession", None)  # Preserve current session for rollback
        old_org_id = getattr(misthelper, "org_id", None)  # Preserve current org for rollback
        if not misthelper._attempt_interactive_login_with_rollback(  # Try login; restores on failure
            old_session, old_org_id
        ):
            logging.debug(  # Log rollback path for postmortem tracing
                "SwitchToInteractiveLoginManager: interactive login failed; rolled back and staying on menu"
            )
            return  # Login failed but old session was restored -- stay running
        misthelper._handle_interactive_login_success()  # Login succeeded -- show status and pick MSP/org
        logging.debug(  # Log success path so callers can trace successful session swap
            "SwitchToInteractiveLoginManager: interactive login succeeded; session updated"
        )
