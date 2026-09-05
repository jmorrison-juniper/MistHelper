"""Tests for the SSID broadcast gap report."""

from types import SimpleNamespace

import mistapi

from src.reports.ssid_broadcast_gap_report import SSIDBroadcastGapReport


def test_find_missing_sites_uses_exact_ssid_and_ignores_disabled_wlans(monkeypatch):
    """The report includes sites without an enabled exact SSID match."""
    responses = {
        "site-a": SimpleNamespace(data=[{"ssid": "Office", "enabled": True}]),
        "site-b": SimpleNamespace(data=[{"ssid": "office", "enabled": True}]),
        "site-c": SimpleNamespace(data=[{"ssid": "Office", "enabled": False}]),
    }

    def fetch(_session, site_id, resolve):
        assert resolve is True
        return responses[site_id]

    monkeypatch.setattr(mistapi.api.v1.sites.wlans, "listSiteWlansDerived", fetch)
    sites = [
        {"id": "site-a", "name": "Broadcast Site"},
        {"id": "site-b", "name": "Case Difference Site"},
        {"id": "site-c", "name": "Disabled Site"},
    ]

    result = SSIDBroadcastGapReport._find_missing_sites(object(), sites, "Office")

    assert [row["site_name"] for row in result] == ["Case Difference Site", "Disabled Site"]


def test_has_enabled_ssid_accepts_missing_enabled_field():
    """The report treats an effective WLAN without an enabled field as enabled."""
    assert SSIDBroadcastGapReport._has_enabled_ssid([{"ssid": "Office"}], "Office")
