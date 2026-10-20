"""Shared stand-ins for the metrics gateway tests.

Why:
    Every test in this folder needs a Mist answer, and no test may reach the
    network. These fixtures hold one small organization, so a test reads a
    reading it can predict and a failure names one cause.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

ORG_ID = "org-1111"  # One organization for every test, so a label assertion stays short.
SITE_A = "site-aaaa"  # The first site. It sorts before the second one.
SITE_B = "site-bbbb"  # The second site. A site filter test excludes this one.


class StubResponse:
    """The shape that a `mistapi` endpoint returns."""

    def __init__(self, data: Any, status_code: int = 200) -> None:
        """Store the body and the status.

        Args:
            data: The response body.
            status_code: The HTTP status the call returned.
        """
        self.data = data
        self.status_code = status_code


def org_stats_payload() -> dict[str, Any]:
    """Build one answer for `getOrgStats`.

    Returns:
        An organization record with two service level expectations.
    """
    return {
        "name": "Test Org",
        "num_sites": 2,
        "num_devices": 3,
        "num_inventory": 4,
        "num_devices_connected": 2,
        "num_devices_disconnected": 1,
        "sle": [
            {"path": "coverage", "user_minutes": {"total": 1000, "ok": 970}},
            {"path": "capacity", "user_minutes": {"total": 500, "ok": 500}},
        ],
    }


def site_stats_payload() -> list[dict[str, Any]]:
    """Build one answer for `listOrgSiteStats`.

    Returns:
        One record for each of the two sites.
    """
    return [
        {
            "id": SITE_B,
            "name": "Branch B",
            "country_code": "GB",
            "num_ap": 1,
            "num_ap_connected": 0,
            "num_devices": 1,
            "num_devices_connected": 0,
            "num_clients": 0,
        },
        {
            "id": SITE_A,
            "name": 'Branch "A"',
            "country_code": "US",
            "num_ap": 2,
            "num_ap_connected": 2,
            "num_switch": 1,
            "num_switch_connected": 1,
            "num_devices": 3,
            "num_devices_connected": 3,
            "num_clients": 42,
        },
    ]


def device_stats_payload() -> list[dict[str, Any]]:
    """Build one answer for `listOrgDevicesStats`.

    Returns:
        One access point record, one switch record, and one disconnected record.
    """
    return [
        {
            "mac": "5c5b350e0001",
            "name": "AP-1",
            "type": "ap",
            "site_id": SITE_A,
            "status": "connected",
            "model": "AP45",
            "serial": "A11111111111",
            "version": "0.14.29587",
            "uptime": 86400,
            "last_seen": 1_700_000_000,
            "num_clients": 12,
            "cpu_util": 37,
            "mem_used_kb": 2048,
            "mem_total_kb": 8192,
            "rx_bytes": 5_000_000_000,
            "tx_bytes": 6_000_000_000,
            "power_budget": 30,
        },
        {
            "mac": "2c6bf5000002",
            "name": "SW-1",
            "type": "switch",
            "site_id": SITE_A,
            "status": "connected",
            "model": "EX4400-48P",
            "serial": "S22222222222",
            "version": "23.4R2-S3",
            "uptime": 172800,
            "cpu_stat": {"util": 12},
            "environment": {"cpu_temp": 45},
            "rx_bytes": 1_000,
            "tx_bytes": 2_000,
        },
        {
            "mac": "aabbcc000003",
            "name": "AP-Down",
            "type": "ap",
            "site_id": SITE_B,
            "status": "disconnected",
            "model": "AP12",
            "serial": "B33333333333",
            "version": "0.12.27139",
        },
    ]


def build_overrides(
    org: Mapping[str, Any] | None = None,
    sites: list[dict[str, Any]] | None = None,
    devices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the three endpoint stand-ins that `MistStatsReader` accepts.

    Args:
        org: The `getOrgStats` body. The shared organization is the default.
        sites: The `listOrgSiteStats` body. The shared sites are the default.
        devices: The `listOrgDevicesStats` body. The shared devices are the default.

    Returns:
        The endpoint callables, keyed by Mist endpoint name.
    """
    org_body = org_stats_payload() if org is None else org
    site_body = site_stats_payload() if sites is None else sites
    device_body = device_stats_payload() if devices is None else devices
    return {
        "getOrgStats": lambda _session, _org_id: StubResponse(org_body),
        "listOrgSiteStats": lambda _session, _org_id, **_kwargs: StubResponse(site_body),
        "listOrgDevicesStats": lambda _session, _org_id, **_kwargs: StubResponse(device_body),
    }


@pytest.fixture
def endpoint_overrides() -> dict[str, Any]:
    """Return the three endpoint stand-ins for the shared organization.

    Returns:
        The endpoint callables, keyed by Mist endpoint name.
    """
    return build_overrides()
