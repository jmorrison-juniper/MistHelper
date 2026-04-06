"""
Unit test for DeviceUtilityCommands.clear_session (Menu #149)

This test verifies that the code maps user input into either 'service_name' or 'session_ids' in the request body.
"""

from unittest.mock import MagicMock

import MistHelper


def test_clear_session_accepts_service_name_or_session_ids(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev1", "Device1"),
    )

    # Simulate user entering comma-separated session IDs via context-based safe_input
    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if context == "clear_session_ids":
            return "s1,s2"
        if context == "clear_session_node":
            return ""
        if context == "clear_session_service_name":
            return ""
        if context == "clear_session_confirm_all":
            return ""
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)

    # Ensure destructive confirmation passes
    monkeypatch.setattr(MistHelper.DeviceUtilityCommands, "_confirm_destructive", lambda *args, **kwargs: True)

    captured = {}

    def fake_clear(apisession, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear)

    # Act
    MistHelper.DeviceUtilityCommands.clear_session()

    # Assert
    assert ("session_ids" in captured.get("body", {}) and captured["body"]["session_ids"] == ["s1", "s2"]) or (
        "service_name" in captured.get("body", {})
    )
