"""Tests for the running firmware version resolver and the SSR overlay.

Why:
    Three cloud endpoints report a firmware version for one device, and
    ``listSiteDevices`` disagrees with the other two. It reports the
    configured version, not the running version. A firmware decision
    that reads the wrong value turns a one-step upgrade into a
    multi-release jump, and an operator plans the wrong change. These
    tests pin the rule that a firmware decision reads the running
    version, or marks the value as stale.
"""

from __future__ import annotations

from typing import Any

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig
from src.firmware.running_version import (
    DEVICE_LISTING_ENDPOINT,
    ORG_INVENTORY_ENDPOINT,
    SITE_STATS_ENDPOINT,
    RunningFirmwareVersionResolver,
)

STALE_VERSION = "20.4R3-S2.6"
RUNNING_VERSION = "23.4R2-S5.5"


class _FakeResponse:
    """Minimal mistapi response stand-in that carries a status and a payload."""

    def __init__(self, status_code: int = 200, data: Any = None) -> None:
        """Store the two fields every caller reads."""
        self.status_code = status_code
        self.data = data


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a FirmwareManager with the minimum valid config."""
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-test"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


def test_device_listing_is_not_a_running_version_source() -> None:
    """The resolver must reject the device listing as a running-version source."""
    assert RunningFirmwareVersionResolver.reports_running_version(SITE_STATS_ENDPOINT) is True
    assert RunningFirmwareVersionResolver.reports_running_version(ORG_INVENTORY_ENDPOINT) is True
    assert RunningFirmwareVersionResolver.reports_running_version(DEVICE_LISTING_ENDPOINT) is False


def test_read_prefers_the_running_version_over_the_listing_value() -> None:
    """A stats hit must win over the stale value carried by the device listing."""
    resolver = RunningFirmwareVersionResolver(apisession=object())
    device_row = {"id": "dev-1", "mac": "aabbccddeeff", "version": STALE_VERSION}
    running_by_key = {"dev-1": RUNNING_VERSION}
    reading = resolver.read(device_row, running_by_key)
    assert reading.value == RUNNING_VERSION
    assert reading.source == SITE_STATS_ENDPOINT
    assert reading.is_running is True


def test_read_marks_a_listing_only_value_as_stale() -> None:
    """With no stats row the reading must carry the stale flag, not a silent value."""
    resolver = RunningFirmwareVersionResolver(apisession=object())
    device_row = {"id": "dev-1", "version": STALE_VERSION}
    reading = resolver.read(device_row, {})
    assert reading.source == DEVICE_LISTING_ENDPOINT
    assert reading.is_running is False


def test_fetch_site_running_versions_requests_every_device_type() -> None:
    """The stats call must pass type=all so switches and gateways are included."""
    captured: dict[str, Any] = {}

    def _fake_stats(session: Any, site_id: str, **kwargs: Any) -> _FakeResponse:
        """Record the keyword arguments the resolver sent to the stats endpoint."""
        captured.update(kwargs)
        captured["site_id"] = site_id
        return _FakeResponse(data=[{"id": "dev-1", "mac": "aabbccddeeff", "version": RUNNING_VERSION}])

    resolver = RunningFirmwareVersionResolver(apisession=object(), stats_fn=_fake_stats)
    running = resolver.fetch_site_running_versions("site-1")
    assert captured["type"] == "all"
    assert captured["site_id"] == "site-1"
    assert running["dev-1"] == RUNNING_VERSION
    assert running["aabbccddeeff"] == RUNNING_VERSION


def test_ssr_flow_classifies_on_the_running_version_not_the_stale_one(monkeypatch: Any) -> None:
    """The SSR upgrade flow must not decide from the stale device-listing version."""
    manager = _make_manager()
    site = {"id": "site-1", "name": "Morrison House"}
    stale_row = {"id": "dev-1", "type": "gateway", "model": "SSR120", "version": STALE_VERSION}
    monkeypatch.setattr(manager, "_discover_site_ssr_devices", lambda *_a, **_k: [stale_row])
    monkeypatch.setattr(
        manager,
        "_fetch_site_running_versions",
        lambda *_a, **_k: {"dev-1": RUNNING_VERSION},
    )
    seen: dict[str, Any] = {}

    def _capture(device_ids: list[str], inventory: dict[str, Any], target: str) -> tuple[list[str], list[str]]:
        """Record the inventory the flow handed to the validator."""
        seen["inventory"] = inventory
        return [], []

    monkeypatch.setattr(manager, "_validate_ssr_devices_for_version", _capture)
    upgrade_config: dict[str, Any] = {
        "inventory": {"dev-1": {"model": "SSR120", "type": "gateway", "version": STALE_VERSION, "site_id": "site-1"}},
        "version": RUNNING_VERSION,
        "ssr_models": ["SSR", "128T"],
    }
    site_result: dict[str, Any] = {"site_name": "Morrison House"}
    results: dict[str, Any] = {"ssrs_upgraded": 0, "errors": []}
    manager._run_ssr_site_upgrade_flow(site, site_result, upgrade_config, results)
    assert seen["inventory"]["dev-1"]["version"] == RUNNING_VERSION


def test_ssr_flow_keeps_a_device_missing_from_the_org_inventory(monkeypatch: Any) -> None:
    """A device the org inventory misses must still reach the validator with its running version."""
    manager = _make_manager()
    site = {"id": "site-1", "name": "Morrison House"}
    stale_row = {"id": "dev-2", "type": "gateway", "model": "SSR120", "version": STALE_VERSION}
    monkeypatch.setattr(manager, "_discover_site_ssr_devices", lambda *_a, **_k: [stale_row])
    monkeypatch.setattr(
        manager,
        "_fetch_site_running_versions",
        lambda *_a, **_k: {"dev-2": RUNNING_VERSION},
    )
    seen: dict[str, Any] = {}

    def _capture(device_ids: list[str], inventory: dict[str, Any], target: str) -> tuple[list[str], list[str]]:
        """Record the inventory the flow handed to the validator."""
        seen["inventory"] = inventory
        return [], []

    monkeypatch.setattr(manager, "_validate_ssr_devices_for_version", _capture)
    upgrade_config: dict[str, Any] = {"inventory": {}, "version": "24.1R1", "ssr_models": ["SSR", "128T"]}
    site_result: dict[str, Any] = {"site_name": "Morrison House"}
    results: dict[str, Any] = {"ssrs_upgraded": 0, "errors": []}
    manager._run_ssr_site_upgrade_flow(site, site_result, upgrade_config, results)
    assert seen["inventory"]["dev-2"]["version"] == RUNNING_VERSION


def test_firmware_manager_module_exposes_the_resolver() -> None:
    """The firmware manager must import the shared resolver rather than re-implement it."""
    assert fm_mod.RunningFirmwareVersionResolver is RunningFirmwareVersionResolver
