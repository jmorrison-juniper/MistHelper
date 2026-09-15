"""Define the named row shape for the MistHelper menu table."""

from __future__ import annotations  # WHY: allow modern annotations without run-time imports.

from collections.abc import Callable  # WHY: menu handlers are callables with different signatures.
from dataclasses import dataclass  # WHY: the menu row is immutable structured data.
from typing import Any  # WHY: menu handlers accept different keyword sets.


@dataclass(frozen=True, slots=True)
class MenuEntry:
    """Hold one menu row with named fields for dispatch and safety checks."""

    menu_id: str  # WHY: the row carries its dispatch key for drift checks.
    handler: Callable[..., Any] | None  # WHY: static portal rows can hold no callable.
    title: str  # WHY: the operator sees this menu text.
    category: str  # WHY: the registry safety class travels with the row.
    destructive: bool = False  # WHY: destructive operations need a direct safety flag.
    supports_fast: bool = False  # WHY: the systematic test runner must not inspect call signatures.
