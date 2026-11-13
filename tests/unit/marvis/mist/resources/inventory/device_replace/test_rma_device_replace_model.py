"""Unit tests for RMA device replacement models."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

import pytest  # WHY: assert validation failures in pure model tests.

from src.mist.resources.inventory.device_replace.models import (
    DeviceReplaceValidator,
    InventoryDevice,
)  # WHY: test pure behavior.


def _device(**overrides: str) -> InventoryDevice:
    """Return one inventory device for model tests."""
    row = {
        "id": "device-id",
        "mac": "AA:BB:CC:00:00:01",
        "serial": "serial-1",
        "model": "AP45",
        "type": "ap",
        "site_id": "site-1",
        "name": "Old AP",
    }
    row.update(overrides)  # WHY: each test changes only the relevant fields.
    return InventoryDevice.from_row(row)  # WHY: exercise normalization from Mist rows.


def test_request_body_matches_openapi_shape() -> None:
    """The replacement body uses the OpenAPI field names."""
    old_device = _device()  # WHY: source device supplies site and old MAC.
    new_device = _device(id="new-id", mac="AA-BB-CC-00-00-02", site_id="", name="New AP")  # WHY: valid target.
    request = DeviceReplaceValidator.build_request(old_device, new_device)  # WHY: build after validation.
    assert request.as_body() == {
        "site_id": "site-1",
        "mac": "aabbcc000001",
        "inventory_mac": "aabbcc000002",
        "discard": [],
    }


def test_type_mismatch_states_both_types() -> None:
    """A replacement type mismatch reports old and new types."""
    old_device = _device(type="ap")  # WHY: source type.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", type="switch")  # WHY: mismatched target.
    with pytest.raises(ValueError, match="old device type ap, new device type switch"):
        DeviceReplaceValidator.validate_pair(old_device, new_device)  # WHY: destructive flow must stop here.


def test_replacement_choices_include_only_unassigned_same_type() -> None:
    """Replacement choices exclude assigned and wrong-type devices."""
    old_device = _device(mac="aabbcc000001", type="ap")  # WHY: source type selects candidates.
    valid = _device(id="new-id", mac="aabbcc000002", site_id="", type="ap", name="new")  # WHY: valid target.
    assigned = _device(id="assigned-id", mac="aabbcc000003", site_id="site-2", type="ap")  # WHY: assigned target.
    wrong = _device(id="wrong-id", mac="aabbcc000004", site_id="", type="switch")  # WHY: wrong type target.
    assert DeviceReplaceValidator.replacement_choices([old_device, valid, assigned, wrong], old_device) == [valid]


def test_find_old_device_by_mac_and_name() -> None:
    """Old device lookup supports MAC addresses and names."""
    old_device = _device(name="Lobby AP")  # WHY: named source device.
    assert DeviceReplaceValidator.find_old_device([old_device], "aa-bb-cc-00-00-01") == old_device
    assert DeviceReplaceValidator.find_old_device([old_device], "lobby ap") == old_device
