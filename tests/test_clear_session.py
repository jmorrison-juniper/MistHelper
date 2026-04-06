"""
Unit test scaffolding for DeviceUtilityCommands.clear_session (Menu #149)

Tests are marked xfail until the code is updated to accept session_ids or service_name.
"""

from unittest.mock import MagicMock

import pytest

import MistHelper


@pytest.mark.xfail(
    reason=(
        "Feature not implemented: currently uses 'session_id' key;"
        " desired behavior: accept service_name or session_ids list"
    )
)
def test_clear_session_accepts_service_name_or_session_ids(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev1", "Device1"),
    )

    # Simulate user entering comma-separated session IDs
    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if "session ID" in prompt:
            return "s1,s2"
        if "Node" in prompt:
            return ""
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)

    captured = {}

    def fake_clear(apisession, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear
    )

    # Act
    MistHelper.DeviceUtilityCommands.clear_session()

    # Assert: desired behavior is to set 'session_ids' or 'service_name'
    assert (
        "session_ids" in captured.get("body", {}) or "service_name" in captured.get("body", {})
    )
