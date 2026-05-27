"""Unit tests for extracted service ping manager orchestration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import MistHelper
from src.websocket.service_ping_manager import ServicePingManager, configure_service_ping_manager_dependencies


class _FakeWebSocketManager:
    """Simple websocket manager fake used by manager tests."""

    def __init__(self, _session) -> None:
        self.connect = MagicMock(return_value=True)
        self.subscribe_to_channel = MagicMock(return_value=True)
        self.wait_for_subscription_confirmation = MagicMock(return_value=True)
        self.wait_for_command_result = MagicMock(return_value={"raw": "64 bytes from 8.8.8.8"})
        self.disconnect = MagicMock()


class _FakeTenantUtils:
    """Minimal tenant utility for manager initialization."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def organization_tenants(self) -> list[str]:
        return []

    def site_tenants(self, _site_id: str) -> list[str]:
        return []

    def service_policy_tenants(self, _site_id: str | None) -> list[str]:
        return []

    def gateway_template_tenants(self, _site_id: str | None) -> list[str]:
        return []


def _configure_manager() -> tuple[SimpleNamespace, SimpleNamespace]:
    """Configure extracted manager dependencies for unit tests."""
    prompt_utils = SimpleNamespace(
        select_site_id_from_csv=MagicMock(return_value="site-1"),
        select_device_id_from_inventory=MagicMock(return_value="device-1"),
    )
    mistapi_dependency = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(
                    devices=SimpleNamespace(
                        listSiteDevices=MagicMock(
                            return_value=SimpleNamespace(
                                data=[{"id": "device-1", "type": "gateway", "model": "SSR130", "name": "gw-1"}]
                            )
                        ),
                        servicePingFromSsr=MagicMock(
                            return_value=SimpleNamespace(status_code=200, data={"session": "session-123456"})
                        ),
                        getSiteDevice=MagicMock(return_value=SimpleNamespace(data={})),
                    ),
                    stats=SimpleNamespace(getSiteDeviceStats=MagicMock(return_value=SimpleNamespace(data={}))),
                )
            )
        )
    )
    input_utils = SimpleNamespace(safe_input=MagicMock(return_value=""))
    api_fetch_utils = SimpleNamespace(organization_services=MagicMock(return_value=[]))
    config_utils = SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1"))

    configure_service_ping_manager_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=mistapi_dependency,
        prompt_utils=prompt_utils,
        input_utils=input_utils,
        websocket_manager_class=_FakeWebSocketManager,
        is_debug_mode=MagicMock(return_value=False),
        api_tenant_fetch_utils=_FakeTenantUtils,
        config_utils=config_utils,
        api_fetch_utils=api_fetch_utils,
    )
    return prompt_utils, mistapi_dependency


def test_select_site_and_device_returns_false_when_no_site_selected() -> None:
    """Selection should stop immediately when the user skips site selection."""
    prompt_utils, _mistapi_dependency = _configure_manager()
    prompt_utils.select_site_id_from_csv.return_value = None
    manager = ServicePingManager()

    assert manager._select_site_and_device() is False


def test_fetch_device_info_accepts_gateway_device() -> None:
    """Gateway device lookup should validate cleanly for service ping execution."""
    _prompt_utils, _mistapi_dependency = _configure_manager()
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._fetch_device_info() is True
    assert manager.device_info is not None
    assert manager.device_info["name"] == "gw-1"


def test_execute_service_ping_returns_none_on_non_200_status() -> None:
    """Non-200 Mist API response should stop websocket result waiting."""
    _prompt_utils, mistapi_dependency = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.servicePingFromSsr.return_value = SimpleNamespace(
        status_code=500,
        data={"message": "boom"},
    )
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    result = manager._execute_service_ping({"host": "8.8.8.8", "service": "svc-a", "count": 4, "size": 56})

    assert result is None


def test_wait_for_results_uses_gateway_timeout_profile() -> None:
    """Gateway devices should use the extended websocket timeout profile."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway"}
    manager.websocket_manager = _FakeWebSocketManager(object())

    result = manager._wait_for_results("session-1")

    assert result == {"raw": "64 bytes from 8.8.8.8"}
    manager.websocket_manager.wait_for_command_result.assert_called_once_with(
        "session-1",
        timeout_seconds=45,
        activity_timeout_seconds=5,
    )


def test_execute_runs_end_to_end_until_display_results() -> None:
    """Full execute flow should orchestrate discovery, websocket setup, and result display."""
    _configure_manager()
    manager = ServicePingManager()
    manager._fetch_all_tenants = MagicMock()
    manager._fetch_all_services = MagicMock()
    manager._build_combined_tenants = MagicMock(return_value=["tenant-a"])
    manager._build_combined_services = MagicMock(return_value=["svc-a"])
    manager._prompt_for_tenant = MagicMock(return_value="tenant-a")
    manager._prompt_for_service = MagicMock(return_value="svc-a")
    manager._prompt_for_ping_parameters = MagicMock(
        return_value={"host": "8.8.8.8", "count": 4, "size": 56, "node": None}
    )
    manager._display_configuration = MagicMock()
    manager._setup_websocket = MagicMock(return_value=True)
    manager._execute_service_ping = MagicMock(return_value="session-abc")
    manager._wait_for_results = MagicMock(return_value={"raw": "pong"})
    manager._display_results = MagicMock()
    manager._cleanup = MagicMock()

    manager.execute()

    manager._fetch_all_tenants.assert_called_once()
    manager._fetch_all_services.assert_called_once()
    manager._setup_websocket.assert_called_once()
    manager._execute_service_ping.assert_called_once()
    manager._wait_for_results.assert_called_once_with("session-abc")
    manager._display_results.assert_called_once()
    manager._cleanup.assert_called_once()


def test_misthelper_wrapper_delegates_execute(monkeypatch) -> None:
    """MistHelper wrapper should preserve menu orchestration while delegating execution."""
    fake_delegate = SimpleNamespace(execute=MagicMock(), debug_mode=False)
    monkeypatch.setattr(MistHelper, "_get_service_ping_manager_instance", lambda: fake_delegate)

    wrapper = MistHelper.ServicePingManager()
    wrapper.execute()

    fake_delegate.execute.assert_called_once_with()


def test_menu_action_120_description_is_preserved() -> None:
    """Menu 120 should keep the documented service ping route and description text."""
    handler, description = MistHelper.menu_actions["120"]

    assert callable(handler)
    assert "WebSocket Service Ping" in description
    assert "SSR gateways" in description
