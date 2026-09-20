"""Tests for the device handler narrowing work from issue #2750."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.device._utility_commands_action import _UtilityCommandsAction
from src.device._utility_commands_selection import _UtilityCommandsSelection
from src.device.arp_command_manager import ARPCommandManager
from src.device.prompt_utils import PromptNetworkDeviceUtils


class TestNarrowedDeviceHandlerExceptions:
    """Prove narrowed device utility handlers expose unexpected faults."""

    def test_locate_unexpected_error_propagates(self) -> None:
        """A coding fault in locate must not look like a transport failure."""
        parent = SimpleNamespace(_apisession=MagicMock(), _print_api_result=MagicMock(return_value=True))
        action = _UtilityCommandsAction(parent)
        with patch("src.device._utility_commands_action.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.startSiteLocateDevice.side_effect = TypeError("bad locate wiring")
            with pytest.raises(TypeError, match="bad locate wiring"):
                action._invoke_locate("site-1", "dev-1", 5)

    def test_fetch_and_sort_unexpected_error_propagates(self) -> None:
        """A coding fault in device listing must not look like an empty device list."""
        utils = PromptNetworkDeviceUtils(MagicMock(), MagicMock(), MagicMock())
        with patch("src.device.prompt_utils.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.listSiteDevices.side_effect = TypeError("bad device list")
            with pytest.raises(TypeError, match="bad device list"):
                utils._fetch_and_sort_devices("site-1", "ap", "APs")

    def test_get_device_info_unexpected_error_propagates(self) -> None:
        """A coding fault in device stats must not look like missing stats."""
        parent = SimpleNamespace(_apisession=MagicMock())
        selection = _UtilityCommandsSelection(parent)
        with patch("src.device._utility_commands_selection.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.stats.getSiteDeviceStats.side_effect = TypeError("bad stats")
            with pytest.raises(TypeError, match="bad stats"):
                selection._get_device_info("site-1", "dev-1")

    def test_kept_broad_arp_parse_logs_exception_type(self, monkeypatch: pytest.MonkeyPatch, caplog) -> None:
        """The kept-broad WebSocket frame parser must log the exception type."""

        def raise_runtime_error(_message: str) -> object:
            raise RuntimeError("bad frame")

        monkeypatch.setattr(ARPCommandManager, "_parse_ws_arp_payload", staticmethod(raise_runtime_error))
        with caplog.at_level("ERROR"):
            result = ARPCommandManager._safe_parse_ws_arp_payload("{}")
        assert result is None
        assert "RuntimeError" in caplog.text

    @pytest.mark.parametrize(
        "exception",
        [
            requests.ConnectionError("offline"),
            requests.Timeout("slow"),
        ],
    )
    def test_locate_request_failures_return_message(self, exception: requests.RequestException, capsys) -> None:
        """Connection errors and timeouts must stay operator-visible for locate."""
        parent = SimpleNamespace(_apisession=MagicMock(), _print_api_result=MagicMock(return_value=True))
        action = _UtilityCommandsAction(parent)
        with patch("src.device._utility_commands_action.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.startSiteLocateDevice.side_effect = exception
            action._invoke_locate("site-1", "dev-1", 5)
        assert "Locate failed" in capsys.readouterr().out

    @pytest.mark.parametrize("status_code", [404, 503])
    def test_locate_http_error_reports_status(self, status_code: int, capsys) -> None:
        """HTTP 4xx and HTTP 5xx responses must stay visible to the operator."""
        parent = SimpleNamespace(_apisession=MagicMock())
        parent._print_api_result = MagicMock(
            side_effect=lambda _response, _ok, _fail: print(f"HTTP {status_code}") or False
        )
        action = _UtilityCommandsAction(parent)
        response = MagicMock(status_code=status_code, data={"detail": "bad"})
        with patch("src.device._utility_commands_action.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.startSiteLocateDevice.return_value = response
            action._invoke_locate("site-1", "dev-1", 5)
        assert f"HTTP {status_code}" in capsys.readouterr().out

    def test_arp_empty_body_parse_returns_none(self) -> None:
        """An empty WebSocket body must not produce a parsed ARP payload."""
        empty_body = ""
        response = MagicMock(content=b"", text=empty_body)
        result = ARPCommandManager._safe_parse_ws_arp_payload(response.text)
        assert result is None

    def test_arp_malformed_json_parse_returns_none(self) -> None:
        """Malformed WebSocket JSON must not produce a parsed ARP payload."""
        malformed_json = "{not-json"
        parse_error = json.JSONDecodeError("bad json", malformed_json, 1)
        with patch("src.device.arp_command_manager.json.loads", side_effect=parse_error):
            result = ARPCommandManager._safe_parse_ws_arp_payload(malformed_json)
        assert result is None
