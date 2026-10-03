"""RMA device replacement package for Mist inventory operations."""

from __future__ import annotations  # WHY: keep annotations import-safe for package consumers.

__all__ = ["DeviceReplaceOperation"]  # WHY: expose only the menu handler class from this package.

from src.mist.resources.inventory.device_replace.operation import (
    DeviceReplaceOperation,
)  # WHY: menu wiring imports the handler here.
