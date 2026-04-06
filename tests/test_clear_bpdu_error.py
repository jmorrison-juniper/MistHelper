"""
Unit test scaffolding for DeviceUtilityCommands.clear_bpdu_error (Menu #151)

These tests focus on verifying the port-normalization and body-format behavior.
Marked xfail until normalization is implemented.
"""

from unittest.mock import MagicMock

import pytest

import MistHelper


@pytest.mark.xfail(reason="Port normalization helper not yet implemented")
def test_clear_bpdu_uses_normalized_port_identifier(monkeypatch):
    # Arrange selection
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev1", "Switch1"),
    )

    # Simulate optional port selection returning 'ge-0/0/0'
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands, "_select_port_optional", lambda site_id, device_id: "ge-0/0/0"
    )

    captured = {}

    def fake_clear_bpdu(session, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.devices, "clearBpduErrorsFromPortsOnSwitch", fake_clear_bpdu
    )

    # Act
    MistHelper.DeviceUtilityCommands.clear_bpdu_error()

    # Assert: expected normalized body key (implementation TBD)
    assert "port_id" in captured.get("body", {}) or "port" in captured.get("body", {})
