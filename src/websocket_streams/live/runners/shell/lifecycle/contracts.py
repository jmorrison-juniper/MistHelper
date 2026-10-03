"""Immutable contracts for terminal runner coordination."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Callable  # The coordinator receives one checked trigger callback.
from dataclasses import dataclass  # The configuration is a small immutable value.

from src.websocket_streams.live.runners.shell.modes.behavior import TerminalBehavior  # Modes own terminal actions.
from src.websocket_streams.live.runners.utility.triggers.models import UtilityRequest  # Triggers use one record type.


@dataclass(frozen=True, slots=True)
class TerminalConfiguration:
    """Hold one terminal mode configuration."""

    opened_note: str  # The session records this text after the connection opens.
    closed_reason: str  # The session records this text after a normal device close.
    trigger: Callable[[], UtilityRequest]  # The mode builds its checked REST trigger.
    behavior: TerminalBehavior  # The mode handles first output, limits, and special outcomes.
