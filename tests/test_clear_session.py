"""
Expanded unit tests for DeviceUtilityCommands.clear_session (Menu #149)

These tests cover:
- service_name input
- comma-separated session_ids parsing and trimming
- CANCEL flow when neither provided
- CLEAR ALL confirmation flow
- 400 API error handling
"""

from unittest.mock import MagicMock

import MistHelper


def _stub_selection(monkeypatch):
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev1", "Device1"),
    )


def test_clear_session_with_service_name(monkeypatch):
    _stub_selection(monkeypatch)

    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if context == "clear_session_service_name":
            return "svc1"
        if context == "clear_session_ids":
            return ""
        if context == "clear_session_node":
            return ""
        if context == "clear_session_confirm_all":
            return ""
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)
    monkeypatch.setattr(MistHelper.DeviceUtilityCommands, "_confirm_destructive", lambda *args, **kwargs: True)

    captured = {}

    def fake_clear(apisession, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear)

    MistHelper.DeviceUtilityCommands.clear_session()

    assert captured.get("body") == {"service_name": "svc1"}


def test_clear_session_with_session_ids(monkeypatch):
    _stub_selection(monkeypatch)

    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if context == "clear_session_service_name":
            return ""
        if context == "clear_session_ids":
            return " s1, s2 ,s3 "
        if context == "clear_session_node":
            return ""
        if context == "clear_session_confirm_all":
            return ""
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)
    monkeypatch.setattr(MistHelper.DeviceUtilityCommands, "_confirm_destructive", lambda *args, **kwargs: True)

    captured = {}

    def fake_clear(apisession, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear)

    MistHelper.DeviceUtilityCommands.clear_session()

    assert captured.get("body") == {"session_ids": ["s1", "s2", "s3"]}


def test_clear_session_cancel_clear_all(monkeypatch, capsys):
    _stub_selection(monkeypatch)

    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        # No inputs provided, and confirmation left blank to cancel
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)

    called = {"api": False}

    def fake_clear(apisession, site_id, device_id, body):
        called["api"] = True
        return MagicMock()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear)

    MistHelper.DeviceUtilityCommands.clear_session()

    captured_out = capsys.readouterr().out
    assert "Cancelled: No service name or session IDs provided." in captured_out
    assert called["api"] is False


def test_clear_session_confirm_clear_all_proceeds(monkeypatch):
    _stub_selection(monkeypatch)

    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if context == "clear_session_confirm_all":
            return "CLEAR ALL"
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)
    monkeypatch.setattr(MistHelper.DeviceUtilityCommands, "_confirm_destructive", lambda *args, **kwargs: True)

    captured = {}

    def fake_clear(apisession, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear)

    MistHelper.DeviceUtilityCommands.clear_session()

    # No service_name or session_ids provided, and node skipped -> empty body
    assert captured.get("body") == {}


def test_clear_session_handles_400(monkeypatch, capsys):
    _stub_selection(monkeypatch)

    def fake_safe_input(prompt, context=None, allow_empty=True, **kwargs):
        if context == "clear_session_service_name":
            return "svc1"
        if context == "clear_session_ids":
            return ""
        if context == "clear_session_node":
            return ""
        if context == "clear_session_confirm_all":
            return ""
        return ""

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", fake_safe_input)
    monkeypatch.setattr(MistHelper.DeviceUtilityCommands, "_confirm_destructive", lambda *args, **kwargs: True)

    class FakeErr(Exception):
        def __init__(self):
            self.response = type("R", (), {"status_code": 400})

        def __str__(self):
            return "Bad Request"

    def fake_clear_raise(apisession, site_id, device_id, body):
        raise FakeErr()

    monkeypatch.setattr(MistHelper.mistapi.api.v1.sites.devices, "clearSiteDeviceSession", fake_clear_raise)

    MistHelper.DeviceUtilityCommands.clear_session()

    captured_out = capsys.readouterr().out
    assert "API returned 400" in captured_out
