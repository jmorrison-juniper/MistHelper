"""Shared AP scorecard test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def ap_stats_payload() -> list[dict[str, object]]:
    """Return AP statistics rows that cover detail, site, and summary cases."""
    return [
        {
            "site_id": "site-a",
            "site_name": "Alpha",
            "name": "AP-1",
            "mac": "aabbcc000001",
            "model": "AP43",
            "version": "1.0.0",
            "status": "connected",
            "inactive_wired_vlans": [],
            "switch_redundancy": 2,
            "power_constrained": False,
            "power_opmode": "802.3at",
            "power_budget": 25500,
            "lldp_stat": {"power_allocated": 25500, "power_needed": 25000},
            "config_reverted": False,
            "last_trouble": {},
            "expiring_certs": {},
            "uptime": 172800,
        },
        {
            "site_id": "site-a",
            "site_name": "Alpha",
            "name": "AP-2",
            "mac": "aabbcc000002",
            "model": "AP43",
            "version": "1.0.0",
            "status": "connected",
            "inactive_wired_vlans": [],
            "switch_redundancy": 3,
            "power_constrained": False,
            "power_opmode": "802.3at",
            "power_budget": 25500,
            "config_reverted": False,
            "last_trouble": {},
            "expiring_certs": {"serial": 1728000000},
            "uptime": 86400,
        },
        {
            "site_id": "site-b",
            "site_name": "Beta",
            "name": "AP-3",
            "mac": "aabbcc000003",
            "model": "AP43",
            "version": "0.9.0",
            "status": "disconnected",
            "offline_reason": "switch_down",
            "inactive_wired_vlans": [20, 30],
            "switch_redundancy": 1,
            "power_constrained": True,
            "power_opmode": "low",
            "power_budget": 15000,
            "lldp_stat": {"power_allocated": 15000, "power_requested": 25500},
            "config_reverted": True,
            "last_trouble": {"code": "07"},
            "expiring_certs": {},
            "uptime": 43200,
        },
    ]
