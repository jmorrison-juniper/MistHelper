"""Shared test fixtures for MistHelper test suite."""

from tests.fixtures.device_inventory import (
    DEVICE_AP,
    DEVICE_MISSING_OPTIONAL,
    DEVICE_SWITCH,
    make_device_fixtures,
)

__all__ = [
    "DEVICE_AP",
    "DEVICE_MISSING_OPTIONAL",
    "DEVICE_SWITCH",
    "make_device_fixtures",
]
