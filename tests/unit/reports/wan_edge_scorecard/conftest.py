"""Fixture builders for WAN edge scorecard tests."""

from __future__ import annotations  # Keep annotations import-safe in tests.

from typing import Any  # Allow compact fixture dictionaries with optional fields.

import pytest  # Provide pytest fixtures for scorecard tests.


@pytest.fixture
def gateway_stats_sample() -> list[dict[str, Any]]:
    """Return sample gateway statistics with DHCP, VPN, BGP, and site variance."""
    return [  # Provide deterministic rows for report tests.
        {
            "id": "gw-1",
            "site_id": "site-a",
            "site_name": "Alpha",
            "name": "Alpha-WAN-1",
            "model": "SRX320",
            "version": "22.4R1",
            "config_status": "success",
            "uptime": 172800,
            "dhcpd_stat": {
                "users": {"num_leased": 40, "num_ips": 100},
                "voice": {"num_leased": 85, "num_ips": 100},
            },
            "vpn_peers": [{"up": True}, {"up": False}],
            "bgp_peers": [{"state": "established"}, {"state": "active"}],
            "service_status": {"idp_status": "up"},
        },
        {
            "id": "gw-2",
            "site_id": "site-a",
            "site_name": "Alpha",
            "name": "Alpha-WAN-2",
            "model": "SRX320",
            "version": "22.4R1",
            "config_status": "synced",
            "uptime": 3600,
            "vpn_peers": [{"up": True}],
            "bgp_peers": [{"state": "established"}],
        },
        {
            "mac": "aabbccddeeff",
            "site_id": "site-b",
            "site_name": "Beta",
            "router_name": "Beta-WAN-1",
            "model": "SRX380",
            "version": "21.4R3",
            "config_status": "failed",
            "uptime": 86400,
            "dhcpd_stat": {"guest": {"num_leased": 10, "num_ips": 20}},
            "vpn_peers": [{"up": False}],
            "bgp_peers": [{"state": "idle"}],
            "last_trouble": "dhcp warning",
        },
    ]
