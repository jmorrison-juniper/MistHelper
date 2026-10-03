"""Offline harness for the upgrade option number readers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.interfaces.portals.upgrade_portal.upgrade import options

FIXED_NOW = 1_780_000_000


def fixed_clock() -> int:
    """Return the stable clock used by schedule tests."""
    return FIXED_NOW


def read_options(field: str, value: Any, now: Callable[[], int] | None = fixed_clock) -> Any:
    """Read one option value through the production mapper."""
    return options.build_options({field: value}, now=now)
