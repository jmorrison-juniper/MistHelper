"""Shared fixtures for top-5 decomposition compatibility tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def top5_target_names() -> list[str]:
    """Return canonical target names tracked by the spec."""
    return [
        "_early_dependency_check",
        "_execute_site_capture_loop",
        "start_org_packet_capture",
        "device_events_52w",
        "with_wan_overrides",
    ]
