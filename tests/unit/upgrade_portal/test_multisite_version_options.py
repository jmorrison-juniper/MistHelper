"""Unit tests for multisite running-version option rendering."""

from __future__ import annotations

from typing import Any

from src.upgrade_portal.upgrade import options as module
from tests.unit.upgrade_portal.test_upgrade_options import SWITCH_ROW


def test_running_version_replaces_the_configured_inventory_version() -> None:
    """The multi-site table must show the version that the device runs."""
    rows: list[dict[str, Any]] = module.build_version_options(
        [SWITCH_ROW],
        {"EX4400-48P": ("24.2R1.17",)},
        running_by_key={SWITCH_ROW["mac"]: "24.2R1.17"},
    )

    assert rows[0]["version_before"] == "24.2R1.17"
    assert rows[0]["version_is_running"] is True
    assert rows[0]["version_note"] == ""
