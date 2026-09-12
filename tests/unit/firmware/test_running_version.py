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


# ---------------------------------------------------------------------------
# Tests for issue #2040: stale reading must not produce a silent upgrade verdict
# ---------------------------------------------------------------------------


def test_classify_returns_stale_when_both_endpoints_miss_device(monkeypatch: Any) -> None:
    """A device absent from both running-version endpoints must get a 'stale' verdict.

    Why:
        Commit 5ebbb30a fixed the main path but left a gap: when both
        listSiteDevicesStats and getOrgInventory have no row for a device,
        the inventory entry carries only the device-listing value and
        version_is_stale=True. _classify_ssr_device_for_upgrade must refuse
        to return 'upgrade' in that case.
    """
    manager = _make_manager()
    # Build an inventory entry that _apply_running_version would create for
    # a device absent from both running-version endpoints.
    inventory = {
        "dev-1": {
            "model": "SSR120",
            "type": "gateway",
            "version": STALE_VERSION,  # WHY: the stale device-listing value
            "version_is_stale": True,  # WHY: both running-version endpoints missed this device
        }
    }
    verdict = manager._classify_ssr_device_for_upgrade("dev-1", inventory, "23.4R2-S5.5")
    assert verdict == "stale", (
        f"Expected 'stale' but got {verdict!r}. "
        "A device absent from both running-version endpoints must not receive a silent upgrade verdict."
    )


def test_classify_returns_upgrade_when_org_inventory_holds_running_version() -> None:
    """A device present in the org inventory must still reach an upgrade verdict.

    Why:
        The org inventory reports the running version. A device with an org
        inventory entry must not be blocked by the stale check. version_is_stale
        must be absent from the entry in that case.
    """
    manager = _make_manager()
    # Build an inventory entry for a device whose org inventory version is running state.
    inventory = {
        "dev-2": {
            "model": "SSR120",
            "type": "gateway",
            "version": STALE_VERSION,  # WHY: older running version that needs an upgrade
            # WHY: version_is_stale is absent here because the org inventory had a value
        }
    }
    verdict = manager._classify_ssr_device_for_upgrade("dev-2", inventory, "23.4R2-S5.5")
    assert verdict == "upgrade", (
        f"Expected 'upgrade' but got {verdict!r}. "
        "A device with a running version from the org inventory must reach the upgrade verdict."
    )


def test_apply_running_version_does_not_mark_stale_when_org_inventory_held_version() -> None:
    """version_is_stale must be absent when the org inventory supplied a version.

    Why:
        Before issue #2040 the code set version_is_stale=True on every entry
        that had no stats row, including those whose org inventory version is
        running state. That false alarm would mislead any reader of the flag.
    """
    manager = _make_manager()
    # Simulate a device present in the org inventory (version is running state).
    merged: dict[str, Any] = {"dev-3": {"model": "SSR120", "type": "gateway", "version": RUNNING_VERSION}}
    row = {"id": "dev-3", "model": "SSR120", "type": "gateway", "version": STALE_VERSION}
    # No stats row: the resolver will mark the reading as not running.
    resolver = RunningFirmwareVersionResolver(apisession=object())
    manager._apply_running_version(merged, row, {}, resolver)
    assert (
        "version_is_stale" not in merged["dev-3"]
    ), "version_is_stale must not appear when the org inventory already held a running version."
    # The org inventory version must be preserved by setdefault.
    assert (
        merged["dev-3"]["version"] == RUNNING_VERSION
    ), "The org inventory version must be preserved when it already existed."


def test_apply_running_version_marks_stale_only_when_both_endpoints_miss() -> None:
    """version_is_stale must be True only when both running-version endpoints had no row.

    Why:
        A device absent from both listSiteDevicesStats and getOrgInventory has
        no running version at all. The inventory entry must carry the stale flag
        so _classify_ssr_device_for_upgrade can refuse to produce an upgrade verdict.
    """
    manager = _make_manager()
    # Simulate a device absent from the org inventory and from the stats endpoint.
    merged: dict[str, Any] = {}
    row = {"id": "dev-4", "model": "SSR120", "type": "gateway", "version": STALE_VERSION}
    resolver = RunningFirmwareVersionResolver(apisession=object())
    manager._apply_running_version(merged, row, {}, resolver)
    assert (
        merged["dev-4"].get("version_is_stale") is True
    ), "version_is_stale must be True when both running-version endpoints had no row."
    assert (
        merged["dev-4"]["version"] == STALE_VERSION
    ), "The listing value must be stored so the operator can see which version was rejected."


def test_validate_ssr_devices_skips_stale_devices() -> None:
    """_validate_ssr_devices_for_version must not include a stale device in the validated list.

    Why:
        The validator calls _classify_ssr_device_for_upgrade and must treat the
        'stale' verdict the same way it treats 'missing', 'current', and 'downgrade':
        place the device in the skipped list, not the validated list.
    """
    manager = _make_manager()
    inventory = {
        "dev-5": {
            "model": "SSR120",
            "type": "gateway",
            "version": STALE_VERSION,
            "version_is_stale": True,  # WHY: both running-version endpoints missed this device
        }
    }
    validated, skipped = manager._validate_ssr_devices_for_version(["dev-5"], inventory, "23.4R2-S5.5")
    assert "dev-5" not in validated, "A stale device must not appear in the validated list."
    assert "dev-5" in skipped, "A stale device must appear in the skipped list."
