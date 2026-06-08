"""Thin façade for the interactive Mist session login + MSP/org selection flow.

The real implementation lives under :mod:`src.auth.interactive` as a set of focused
collaborators. This module preserves the legacy public class and method signatures
so callers and tests continue to import ``InteractiveSessionManager`` from here.
"""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import getpass  # noqa: F401  Re-exported so tests can patch src.auth.interactive_session.getpass.getpass
import logging  # noqa: F401  Re-exported so tests/back-compat callers can patch the logger
from collections.abc import Callable  # Typing for the injected callbacks
from typing import Any  # Generic typing for the shared state bag

from src.auth.interactive import (  # Collaborators implementing the real workflow
    MIST_CLOUDS,
    LoginOrchestrator,
    MspOrgSelector,
)

__all__ = ["InteractiveSessionManager"]  # Explicit public surface for this façade module


class InteractiveSessionManager:
    """Manage interactive session login and MSP/org selection (thin façade)."""

    def __init__(
        self,
        state: dict[str, Any],
        safe_input: Callable[..., str],
        detect_msp_privileges: Callable[[], list[dict[str, Any]]],
        select_org_from_session: Callable[[], None],
    ) -> None:
        """Initialize the façade with shared mutable state and injected dependencies."""
        self.state = state  # Shared mutable state bag persisted across the workflow
        self.safe_input = safe_input  # Injected EOF-safe input wrapper
        self.detect_msp_privileges = detect_msp_privileges  # Post-login MSP detection callback
        self.select_org_from_session = select_org_from_session  # Direct-org-select fallback

    @staticmethod
    def _mist_clouds() -> dict[str, tuple[str, str]]:
        """Return the Mist cloud catalog (preserved for back-compat callers/tests)."""
        return MIST_CLOUDS  # Single source of truth lives in src.auth.interactive.clouds

    def initialize_mist_session_interactive(self) -> bool:
        """Run the interactive Mist API login workflow; True on success."""
        return LoginOrchestrator(  # Build a per-call orchestrator with the injected deps
            state=self.state,
            safe_input=self.safe_input,
            detect_msp_privileges=self.detect_msp_privileges,
        ).execute()  # Delegate to the orchestrator's execute() entry point

    def select_msp_and_org(self) -> None:
        """Run the MSP + organization selection workflow, mutating state in place."""
        MspOrgSelector(  # Build a per-call selector with the injected deps
            state=self.state,
            safe_input=self.safe_input,
            select_org_fallback=self.select_org_from_session,
        ).select()  # Delegate to the selector's select() entry point
