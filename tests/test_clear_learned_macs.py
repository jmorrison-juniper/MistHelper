"""
Unit test scaffolding for DeviceUtilityCommands.clear_learned_macs (Menu #152)

Marked xfail until port-name normalization and API-format adjustments are implemented.
"""

from unittest.mock import MagicMock

import mistapi
import pytest

from src.device.utility_commands import DeviceUtilityCommands


@pytest.mark.xfail(reason="Port normalization / API mapping not implemented")
def test_clear_learned_macs_accepts_junos_style_port_names(monkeypatch):
    monkeypatch.setattr(
        DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev1", "Switch1"),
    )

    monkeypatch.setattr(DeviceUtilityCommands, "_select_port_from_device", lambda site_id, device_id: "ge-0/0/0")

    captured = {}

    def fake_clear(session, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "clearAllLearnedMacsFromPortOnSwitch", fake_clear)

    DeviceUtilityCommands.clear_learned_macs()

    # Expectation: body contains normalized port identifier
    assert "port_id" in captured.get("body", {})
