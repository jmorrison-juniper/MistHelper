"""Unit tests for extracted service ping manager orchestration.

Why:
    Comprehensive tests exercising every method and branch of
    ``src.websocket.service_ping_manager`` so the module can graduate out of
    the coverage omit list. Covers module-level helpers, dependency wiring,
    manager construction, discovery/preflight orchestration, websocket
    setup, dispatch, wait, display, cleanup, and the ``execute`` entry point.
"""

from __future__ import annotations

import importlib
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import MistHelper
from src.websocket import service_ping_manager as spm_module
from src.websocket.service_ping_manager import (
    ServicePingManager,
    _short_session_preview,
    configure_service_ping_manager_dependencies,
)


class _FakeWebSocketManager:
    """Simple websocket manager fake used by manager tests.

    Why:
        The manager only calls a small handful of transport methods; a
        MagicMock-backed fake keeps assertions readable without importing the
        real websocket stack in unit tests.
    """

    def __init__(self, _session) -> None:
        """Store MagicMock stubs for each websocket method used by the manager."""
        self.connect = MagicMock(return_value=True)
        self.subscribe_to_channel = MagicMock(return_value=True)
        self.wait_for_subscription_confirmation = MagicMock(return_value=True)
        self.wait_for_command_result = MagicMock(return_value={"raw": "64 bytes from 8.8.8.8"})
        self.disconnect = MagicMock()


class _FakeTenantUtils:
    """Minimal tenant utility for manager initialization.

    Why:
        The mixin only calls the tenant lookup helpers here; returning empty
        lists keeps the discovery cache initialisation deterministic.
    """

    def __init__(self, *_args, **_kwargs) -> None:
        """Accept and ignore any constructor arguments passed by the manager."""

    def organization_tenants(self) -> list[str]:
        """Return an empty tenant list for organization scope."""
        return []

    def site_tenants(self, _site_id: str) -> list[str]:
        """Return an empty tenant list for a given site."""
        return []

    def service_policy_tenants(self, _site_id: str | None) -> list[str]:
        """Return an empty tenant list for service-policy scope."""
        return []

    def gateway_template_tenants(self, _site_id: str | None) -> list[str]:
        """Return an empty tenant list for gateway-template scope."""
        return []


def _configure_manager(*, debug: bool = False) -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
    """Configure extracted manager dependencies for unit tests.

    Why:
        Every test in this module needs the module-level DI slots populated.
        Building the fakes in one place keeps tests focused on behaviour.

    Args:
        debug: whether ``is_debug_mode`` should return True at manager init.

    Returns:
        Tuple of ``(prompt_utils, mistapi_dependency, input_utils)`` so tests
        can mutate the stubs to drive individual branches.
    """
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
        is_debug_mode=MagicMock(return_value=debug),
        api_tenant_fetch_utils=_FakeTenantUtils,
        config_utils=config_utils,
        api_fetch_utils=api_fetch_utils,
    )
    return prompt_utils, mistapi_dependency, input_utils


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def test_short_session_preview_truncates_long_ids() -> None:
    """Long session ids get truncated to the preview budget with ellipsis."""
    assert _short_session_preview("abcdefghijklmno") == "abcdefgh..."


def test_short_session_preview_returns_short_ids_verbatim() -> None:
    """Short session ids are returned in full without truncation."""
    assert _short_session_preview("abcd") == "abcd"


def test_short_session_preview_boundary_is_not_truncated() -> None:
    """Session ids equal to the preview budget are returned in full."""
    assert _short_session_preview("abcdefgh") == "abcdefgh"


def test_configure_publishes_all_dependency_globals() -> None:
    """Configuration hook publishes every dependency global for downstream use."""
    _configure_manager()

    assert spm_module.apisession is not None
    assert spm_module.mistapi is not None
    assert spm_module.PromptUtils is not None
    assert spm_module.InputUtils is not None
    assert spm_module.WebSocketManager is _FakeWebSocketManager
    assert spm_module.check_fn is not None
    assert spm_module.APITenantFetchUtils is _FakeTenantUtils
    assert spm_module.ConfigUtils is not None
    assert spm_module.APIFetchUtils is not None


# ---------------------------------------------------------------------------
# __init__ and debug helpers
# ---------------------------------------------------------------------------


def test_init_defaults_debug_off_when_check_fn_returns_falsey() -> None:
    """When check_fn is falsy the manager latches debug_mode off."""
    _configure_manager(debug=False)
    manager = ServicePingManager()

    assert manager.debug_mode is False
    assert manager.site_id is None
    assert manager.device_id is None
    assert manager.device_info is None
    assert manager.websocket_manager is None
    assert manager.org_tenants == []
    assert manager.device_services == []


def test_init_latches_debug_true_when_check_fn_returns_true() -> None:
    """When check_fn returns True the manager records debug_mode=True at construction."""
    _configure_manager(debug=True)
    manager = ServicePingManager()

    assert manager.debug_mode is True


def test_init_uses_false_when_check_fn_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """When check_fn global is unset the manager still constructs with debug off."""
    _configure_manager()
    monkeypatch.setattr(spm_module, "check_fn", None)

    manager = ServicePingManager()

    assert manager.debug_mode is False


def test_debug_print_emits_only_when_debug_enabled(capsys: pytest.CaptureFixture[str]) -> None:
    """The debug helper suppresses output when debug is off and prints when on."""
    _configure_manager(debug=False)
    manager = ServicePingManager()

    manager._debug_print("hidden")
    assert capsys.readouterr().out == ""

    manager.debug_mode = True
    manager._debug_print("shown")
    assert "[DEBUG] shown" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _select_site_and_device
# ---------------------------------------------------------------------------


def test_select_site_and_device_returns_false_when_no_site_selected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Selection should stop immediately when the user skips site selection."""
    prompt_utils, _mistapi, _input_utils = _configure_manager()
    prompt_utils.select_site_id_from_csv.return_value = None
    manager = ServicePingManager()

    assert manager._select_site_and_device() is False
    assert "No site selected" in capsys.readouterr().out


def test_select_site_and_device_returns_false_when_no_gateway_selected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Selection should stop when the gateway inventory prompt yields no device."""
    prompt_utils, _mistapi, _input_utils = _configure_manager()
    prompt_utils.select_device_id_from_inventory.return_value = None
    manager = ServicePingManager()

    assert manager._select_site_and_device() is False
    assert "No gateway devices" in capsys.readouterr().out


def test_select_site_and_device_returns_true_when_both_selected() -> None:
    """Both selections successful should return True and populate ids."""
    _configure_manager(debug=True)
    manager = ServicePingManager()

    assert manager._select_site_and_device() is True
    assert manager.site_id == "site-1"
    assert manager.device_id == "device-1"


# ---------------------------------------------------------------------------
# _lookup_device_info / _fetch_device_info / _validate_device_type
# ---------------------------------------------------------------------------


def test_lookup_device_info_success_populates_device_info() -> None:
    """Successful lookup populates device_info from the API response."""
    _configure_manager()
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._lookup_device_info() is True
    assert manager.device_info is not None
    assert manager.device_info["name"] == "gw-1"


def test_lookup_device_info_returns_false_on_exception() -> None:
    """API exceptions are swallowed and cause lookup to return False."""
    _prompt, mistapi_dependency, _input_utils = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("boom")
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._lookup_device_info() is False


def test_fetch_device_info_accepts_gateway_device() -> None:
    """Gateway device lookup should validate cleanly for service ping execution."""
    _configure_manager()
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._fetch_device_info() is True
    assert manager.device_info is not None
    assert manager.device_info["name"] == "gw-1"


def test_fetch_device_info_falls_back_when_lookup_fails() -> None:
    """When lookup raises we drop into the unknown-device confirmation path."""
    _prompt, mistapi_dependency, input_utils = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("boom")
    input_utils.safe_input.return_value = "y"
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._fetch_device_info() is True


def test_fetch_device_info_falls_back_when_no_match_found() -> None:
    """Empty device match falls back to the unknown-device confirmation prompt."""
    _prompt, mistapi_dependency, input_utils = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.listSiteDevices.return_value = SimpleNamespace(data=[])
    input_utils.safe_input.return_value = "n"
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._fetch_device_info() is False


def test_validate_device_type_returns_false_when_info_none() -> None:
    """A None device_info in validate defers to the unknown-device path."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "n"
    manager = ServicePingManager()
    manager.device_info = None

    assert manager._validate_device_type() is False


def test_validate_device_type_accepts_gateway(capsys: pytest.CaptureFixture[str]) -> None:
    """Gateway devices short-circuit validation with a confirmation message."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "model": "SSR130"}

    assert manager._validate_device_type() is True
    out = capsys.readouterr().out
    assert "SSR Gateway detected" in out
    assert "SSR130" in out


def test_validate_device_type_warns_for_ap_and_asks_confirm(capsys: pytest.CaptureFixture[str]) -> None:
    """AP devices warn the user with the friendly label before confirming."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "y"
    manager = ServicePingManager()
    manager.device_info = {"type": "ap", "model": "AP41"}

    assert manager._validate_device_type() is True
    assert "Access Point detected" in capsys.readouterr().out


def test_validate_device_type_uses_unknown_label_for_unmapped_type(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Types absent from the label table fall through to 'Unknown device type'."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "n"
    manager = ServicePingManager()
    manager.device_info = {"type": "printer", "model": "LP-9000"}

    assert manager._validate_device_type() is False
    assert "Unknown device type" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _confirm_unknown_device / _confirm_proceed
# ---------------------------------------------------------------------------


def test_confirm_unknown_device_prints_and_delegates(capsys: pytest.CaptureFixture[str]) -> None:
    """Unknown-device prompt warns the operator before delegating to confirm."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "y"
    manager = ServicePingManager()

    assert manager._confirm_unknown_device() is True
    assert "Cannot determine device type" in capsys.readouterr().out


def test_confirm_proceed_yes_returns_true() -> None:
    """A 'y' input accepts continuation of the workflow."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "  Y  "
    manager = ServicePingManager()

    assert manager._confirm_proceed() is True


def test_confirm_proceed_non_y_returns_false(capsys: pytest.CaptureFixture[str]) -> None:
    """Any non-'y' answer cancels the workflow and prints acknowledgement."""
    _prompt, _mistapi, input_utils = _configure_manager()
    input_utils.safe_input.return_value = "n"
    manager = ServicePingManager()

    assert manager._confirm_proceed() is False
    assert "Operation cancelled." in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _wait_for_subscription / _setup_websocket
# ---------------------------------------------------------------------------


def test_wait_for_subscription_confirms_when_ack_returns_true(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A confirmed subscription prints the confirmation banner."""
    _configure_manager()
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())

    manager._wait_for_subscription("/channel")

    out = capsys.readouterr().out
    assert "Subscription confirmed" in out


def test_wait_for_subscription_warns_on_timeout(capsys: pytest.CaptureFixture[str]) -> None:
    """A missed ack prints both warning lines but does not raise."""
    _configure_manager()
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())
    manager.websocket_manager.wait_for_subscription_confirmation.return_value = False

    manager._wait_for_subscription("/channel")

    out = capsys.readouterr().out
    assert "Subscription confirmation not received" in out
    assert "may not be received" in out


def test_setup_websocket_returns_false_on_connect_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed connect aborts setup with a user-visible error."""

    class _FailingConnect(_FakeWebSocketManager):
        def __init__(self, session) -> None:
            super().__init__(session)
            self.connect = MagicMock(return_value=False)

    _configure_manager()
    spm_module.WebSocketManager = _FailingConnect
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._setup_websocket() is False
    assert "Failed to establish WebSocket connection" in capsys.readouterr().out


def test_setup_websocket_returns_false_on_subscribe_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed subscribe aborts setup with a user-visible error."""

    class _FailingSubscribe(_FakeWebSocketManager):
        def __init__(self, session) -> None:
            super().__init__(session)
            self.subscribe_to_channel = MagicMock(return_value=False)

    _configure_manager()
    spm_module.WebSocketManager = _FailingSubscribe
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._setup_websocket() is False
    assert "Failed to subscribe" in capsys.readouterr().out


def test_setup_websocket_success_confirms_and_waits(capsys: pytest.CaptureFixture[str]) -> None:
    """Successful setup confirms the handshake and calls the subscription wait."""
    _configure_manager()
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    assert manager._setup_websocket() is True
    out = capsys.readouterr().out
    assert "WebSocket connected and subscribed" in out
    assert "Subscription confirmed" in out


# ---------------------------------------------------------------------------
# _handle_ping_response / _execute_service_ping
# ---------------------------------------------------------------------------


def test_handle_ping_response_returns_none_on_non_200(capsys: pytest.CaptureFixture[str]) -> None:
    """A non-200 status is surfaced via print and returns None."""
    _configure_manager()
    manager = ServicePingManager()

    response = SimpleNamespace(status_code=500, data={"message": "boom"})
    assert manager._handle_ping_response(response) is None
    assert "Failed to issue Service Ping command" in capsys.readouterr().out


def test_handle_ping_response_returns_session_when_present(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A 200 with a session id emits the short-form banner and returns the id."""
    _configure_manager()
    manager = ServicePingManager()

    response = SimpleNamespace(status_code=200, data={"session": "session-999999"})
    assert manager._handle_ping_response(response) == "session-999999"
    assert "Service Ping command issued (session:" in capsys.readouterr().out


def test_handle_ping_response_notes_missing_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A 200 with no session id still confirms dispatch and returns None."""
    _configure_manager()
    manager = ServicePingManager()

    response = SimpleNamespace(status_code=200, data={"session": ""})
    assert manager._handle_ping_response(response) is None
    assert "no session ID returned" in capsys.readouterr().out


def test_execute_service_ping_returns_none_on_non_200_status() -> None:
    """Non-200 Mist API response should stop websocket result waiting."""
    _prompt, mistapi_dependency, _input_utils = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.servicePingFromSsr.return_value = SimpleNamespace(
        status_code=500,
        data={"message": "boom"},
    )
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    result = manager._execute_service_ping({"host": "8.8.8.8", "service": "svc-a", "count": 4, "size": 56})

    assert result is None


def test_execute_service_ping_returns_none_on_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """A mistapi exception should be reported and return None."""
    _prompt, mistapi_dependency, _input_utils = _configure_manager()
    mistapi_dependency.api.v1.sites.devices.servicePingFromSsr.side_effect = RuntimeError("blip")
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    result = manager._execute_service_ping({"host": "8.8.8.8", "service": "svc-a", "count": 4, "size": 56})

    assert result is None
    assert "Error issuing Service Ping command" in capsys.readouterr().out


def test_execute_service_ping_returns_session_on_success() -> None:
    """A successful dispatch returns the session id extracted from the response."""
    _configure_manager()
    manager = ServicePingManager()
    manager.site_id = "site-1"
    manager.device_id = "device-1"

    result = manager._execute_service_ping({"host": "8.8.8.8", "service": "svc-a", "count": 4, "size": 56})

    assert result == "session-123456"


# ---------------------------------------------------------------------------
# _select_timeout_profile / _wait_for_results
# ---------------------------------------------------------------------------


def test_select_timeout_profile_returns_gateway_profile(capsys: pytest.CaptureFixture[str]) -> None:
    """Gateway devices select the extended timeout profile with a banner."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway"}

    assert manager._select_timeout_profile() == (45, 5)
    assert "extended timeout" in capsys.readouterr().out


def test_select_timeout_profile_returns_default_when_not_gateway() -> None:
    """Non-gateway devices (or missing info) select the default timeout profile."""
    _configure_manager()
    manager = ServicePingManager()

    assert manager._select_timeout_profile() == (30, 3)

    manager.device_info = {"type": "switch"}
    assert manager._select_timeout_profile() == (30, 3)


def test_wait_for_results_returns_none_when_no_manager() -> None:
    """A missing websocket manager short-circuits the wait to None."""
    _configure_manager()
    manager = ServicePingManager()

    assert manager._wait_for_results("session") is None


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


def test_wait_for_results_traces_result_keys_in_debug(capsys: pytest.CaptureFixture[str]) -> None:
    """Debug mode should trace the keys of a non-empty result payload."""
    _configure_manager(debug=True)
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())

    manager._wait_for_results("session-9")

    out = capsys.readouterr().out
    assert "Result keys" in out


# ---------------------------------------------------------------------------
# _display_results and children
# ---------------------------------------------------------------------------


def test_display_results_dispatches_success_when_result_present() -> None:
    """Results present should route through the success display path."""
    _configure_manager()
    manager = ServicePingManager()
    manager._display_success_results = MagicMock()
    manager._display_timeout_results = MagicMock()

    manager._display_results({"raw": "ok"}, {"service": "svc", "host": "h"})

    manager._display_success_results.assert_called_once()
    manager._display_timeout_results.assert_not_called()


def test_display_results_dispatches_timeout_when_result_absent() -> None:
    """An empty result should route through the timeout display path."""
    _configure_manager()
    manager = ServicePingManager()
    manager._display_success_results = MagicMock()
    manager._display_timeout_results = MagicMock()

    manager._display_results(None, {"service": "svc", "host": "h"})

    manager._display_timeout_results.assert_called_once()
    manager._display_success_results.assert_not_called()


def test_print_ping_output_prints_both_when_parsed_differs(capsys: pytest.CaptureFixture[str]) -> None:
    """Raw and parsed sections are both printed when they differ."""
    _configure_manager()
    manager = ServicePingManager()

    manager._print_ping_output("raw", "parsed")

    out = capsys.readouterr().out
    assert "PING OUTPUT" in out
    assert "PARSED OUTPUT" in out


def test_print_ping_output_skips_parsed_when_equal(capsys: pytest.CaptureFixture[str]) -> None:
    """The parsed section is skipped when the parsed text matches raw output."""
    _configure_manager()
    manager = ServicePingManager()

    manager._print_ping_output("raw", "raw")

    out = capsys.readouterr().out
    assert "PING OUTPUT" in out
    assert "PARSED OUTPUT" not in out


def test_print_ping_output_prints_nothing_when_both_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """No output sections are emitted when both raw and parsed are empty."""
    _configure_manager()
    manager = ServicePingManager()

    manager._print_ping_output("", "")

    assert capsys.readouterr().out == ""


def test_handle_empty_output_prints_notice_and_hint_for_non_gateway(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-gateway devices with empty output receive the troubleshooting hint block."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "switch"}

    manager._handle_empty_output()

    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Troubleshooting for non-gateway" in out


def test_handle_empty_output_skips_hint_for_gateway(capsys: pytest.CaptureFixture[str]) -> None:
    """Gateway devices only see the empty-notice, no troubleshooting block."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway"}

    manager._handle_empty_output()

    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Troubleshooting" not in out


def test_handle_empty_output_when_device_info_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing device_info skips the troubleshooting hint block."""
    _configure_manager()
    manager = ServicePingManager()

    manager._handle_empty_output()

    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Troubleshooting" not in out


def test_display_success_results_prints_full_block(capsys: pytest.CaptureFixture[str]) -> None:
    """A populated result prints banner, device context, and output sections."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "model": "SSR130", "name": "gw-1"}

    manager._display_success_results(
        {"raw": "raw-line", "Output": "parsed-line"},
        {"service": "svc-a", "host": "8.8.8.8"},
    )

    out = capsys.readouterr().out
    assert "SERVICE PING RESULTS" in out
    assert "gw-1" in out
    assert "raw-line" in out
    assert "parsed-line" in out


def test_display_success_results_empty_output_reports_notice(capsys: pytest.CaptureFixture[str]) -> None:
    """When result contains no output the empty-output notice is printed."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "model": "SSR130", "name": "gw-1"}

    manager._display_success_results({}, {"service": "svc-a", "host": "8.8.8.8"})

    assert "No output data received" in capsys.readouterr().out


def test_display_success_results_skips_context_when_device_info_none(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing device_info skips the device-context call while still printing banners."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = None

    manager._display_success_results({"raw": "pong"}, {"service": "svc-a", "host": "8.8.8.8"})

    out = capsys.readouterr().out
    assert "SERVICE PING RESULTS" in out
    assert "pong" in out


def test_wait_for_results_skips_key_trace_when_result_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty results in debug mode skip the key-set trace branch."""
    _configure_manager(debug=True)
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())
    manager.websocket_manager.wait_for_command_result.return_value = None

    result = manager._wait_for_results("session-empty")

    assert result is None
    assert "Result keys" not in capsys.readouterr().out


def test_display_device_context_returns_when_info_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """No device_info means no device-context output is written."""
    _configure_manager()
    manager = ServicePingManager()

    manager._display_device_context({"service": "svc", "host": "h"})

    assert capsys.readouterr().out == ""


def test_display_device_context_notes_service_routing_for_gateway(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Gateway devices display the service-specific routing note."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "model": "SSR130", "name": "gw-1"}

    manager._display_device_context({"service": "svc-a", "host": "8.8.8.8"})

    out = capsys.readouterr().out
    assert "Service-specific routing path" in out
    assert "GATEWAY" in out


def test_display_device_context_warns_for_non_gateway(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-gateway devices display the fallback caution note."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "switch", "model": "EX4400", "name": "sw-1"}

    manager._display_device_context({"service": "svc-a", "host": "8.8.8.8"})

    assert "may not fully support" in capsys.readouterr().out


def test_display_non_gateway_troubleshooting_prints_hints(capsys: pytest.CaptureFixture[str]) -> None:
    """The non-gateway hint block prints all four help lines."""
    _configure_manager()
    manager = ServicePingManager()

    manager._display_non_gateway_troubleshooting()

    out = capsys.readouterr().out
    assert "Troubleshooting for non-gateway" in out
    assert "regular ping" in out
    assert "Verify device" in out


def test_log_success_includes_device_info_when_available(caplog: pytest.LogCaptureFixture) -> None:
    """The success log includes device name and type when metadata is present."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "name": "gw-1"}

    with caplog.at_level(logging.INFO, logger="root"):
        manager._log_success({"service": "svc", "host": "h"})

    assert any("gw-1" in rec.getMessage() for rec in caplog.records)


def test_log_success_falls_back_to_device_id(caplog: pytest.LogCaptureFixture) -> None:
    """Without device metadata the log falls back to the device id."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_id = "device-42"

    with caplog.at_level(logging.INFO, logger="root"):
        manager._log_success({"service": "svc", "host": "h"})

    assert any("device-42" in rec.getMessage() for rec in caplog.records)


def test_print_timeout_tips_gateway_prints_full_list(capsys: pytest.CaptureFixture[str]) -> None:
    """Gateway framing prints the dedicated header and every tip as an arrow."""
    _configure_manager()
    manager = ServicePingManager()

    manager._print_timeout_tips("gateway", ("first", "second"))

    out = capsys.readouterr().out
    assert "Troubleshooting for SSR gateways" in out
    assert "-> first" in out
    assert "-> second" in out


def test_print_timeout_tips_non_gateway_uses_note_framing(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-gateway framing elevates the first tip as a note and prints the rest."""
    _configure_manager()
    manager = ServicePingManager()

    manager._print_timeout_tips("ap", ("primary", "secondary"))

    out = capsys.readouterr().out
    assert "Note: primary" in out
    assert "-> secondary" in out


def test_display_timeout_results_bails_when_info_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing device_info drops out with a warning log and no formatted tips."""
    _configure_manager()
    manager = ServicePingManager()

    manager._display_timeout_results({"service": "svc", "host": "h"})

    out = capsys.readouterr().out
    assert "No Service Ping results" in out
    assert "Troubleshooting" not in out


def test_display_timeout_results_prints_gateway_tips(capsys: pytest.CaptureFixture[str]) -> None:
    """Gateway timeouts print the SSR gateway troubleshooting block."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "gateway", "name": "gw-1"}

    manager._display_timeout_results({"service": "svc", "host": "h"})

    out = capsys.readouterr().out
    assert "gw-1" in out
    assert "Troubleshooting for SSR gateways" in out


def test_display_timeout_results_uses_default_tips_for_unknown_type(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unmapped device types fall back to the DEFAULT tip table."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_info = {"type": "printer", "name": "unknown-1"}

    manager._display_timeout_results({"service": "svc", "host": "h"})

    out = capsys.readouterr().out
    assert "designed for SSR gateways" in out


# ---------------------------------------------------------------------------
# _cleanup
# ---------------------------------------------------------------------------


def test_cleanup_disconnects_when_manager_present(capsys: pytest.CaptureFixture[str]) -> None:
    """A live websocket manager is disconnected and cleanup message printed."""
    _configure_manager()
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())

    manager._cleanup()

    manager.websocket_manager.disconnect.assert_called_once()
    assert "WebSocket connection closed" in capsys.readouterr().out


def test_cleanup_noop_when_no_manager() -> None:
    """No websocket manager means cleanup is a no-op with no exception raised."""
    _configure_manager()
    manager = ServicePingManager()

    manager._cleanup()


def test_cleanup_swallows_exceptions(caplog: pytest.LogCaptureFixture) -> None:
    """Cleanup logs and swallows any exception raised during disconnect."""
    _configure_manager()
    manager = ServicePingManager()
    manager.websocket_manager = _FakeWebSocketManager(object())
    manager.websocket_manager.disconnect.side_effect = RuntimeError("bad")

    with caplog.at_level(logging.WARNING, logger="root"):
        manager._cleanup()

    assert any("cleanup error" in rec.getMessage() for rec in caplog.records)


# ---------------------------------------------------------------------------
# _preflight / _prepare_payload / _run_ping_flow / _run_workflow
# ---------------------------------------------------------------------------


def test_preflight_returns_false_when_selection_fails() -> None:
    """Site/device selection failure aborts the preflight."""
    _configure_manager()
    manager = ServicePingManager()
    manager._select_site_and_device = MagicMock(return_value=False)

    assert manager._preflight() is False


def test_preflight_returns_false_when_fetch_fails() -> None:
    """Device info fetch failure aborts the preflight."""
    _configure_manager()
    manager = ServicePingManager()
    manager._select_site_and_device = MagicMock(return_value=True)
    manager._fetch_device_info = MagicMock(return_value=False)

    assert manager._preflight() is False


def test_preflight_returns_true_when_both_succeed() -> None:
    """When both selection and fetch succeed preflight returns True."""
    _configure_manager()
    manager = ServicePingManager()
    manager._select_site_and_device = MagicMock(return_value=True)
    manager._fetch_device_info = MagicMock(return_value=True)

    assert manager._preflight() is True


def test_prepare_payload_calls_discovery_and_builders(capsys: pytest.CaptureFixture[str]) -> None:
    """Payload preparation drives the discovery mixin and payload builder."""
    _configure_manager()
    manager = ServicePingManager()
    manager._fetch_all_tenants = MagicMock()
    manager._fetch_all_services = MagicMock()
    manager._build_combined_tenants = MagicMock(return_value=["tenant-a"])
    manager._build_combined_services = MagicMock(return_value=["svc-a"])
    manager._prompt_for_tenant = MagicMock(return_value="tenant-a")
    manager._prompt_for_service = MagicMock(return_value="svc-a")
    manager._prompt_for_ping_parameters = MagicMock(
        return_value={"host": "1.1.1.1", "count": 2, "size": 100, "node": None}
    )
    manager._build_payload = MagicMock(return_value={"final": True})
    manager._display_configuration = MagicMock()

    payload = manager._prepare_payload()

    assert payload == {"final": True}
    manager._fetch_all_tenants.assert_called_once()
    manager._fetch_all_services.assert_called_once()
    manager._display_configuration.assert_called_once_with({"final": True})
    assert "SERVICE PING CONFIGURATION" in capsys.readouterr().out


def test_run_ping_flow_returns_when_setup_fails() -> None:
    """A failed websocket setup returns without dispatching the ping."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_id = "device-1"
    manager._setup_websocket = MagicMock(return_value=False)
    manager._execute_service_ping = MagicMock()

    manager._run_ping_flow({"host": "h", "service": "s"})

    manager._execute_service_ping.assert_not_called()


def test_run_ping_flow_returns_when_no_session(capsys: pytest.CaptureFixture[str]) -> None:
    """A missing session id aborts the wait/display phase with a message."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_id = "device-1"
    manager._setup_websocket = MagicMock(return_value=True)
    manager._execute_service_ping = MagicMock(return_value=None)
    manager._wait_for_results = MagicMock()

    manager._run_ping_flow({"host": "h", "service": "s"})

    manager._wait_for_results.assert_not_called()
    assert "No session ID" in capsys.readouterr().out


def test_run_ping_flow_dispatches_wait_and_display() -> None:
    """A successful setup+dispatch path waits for results and displays them."""
    _configure_manager()
    manager = ServicePingManager()
    manager.device_id = "device-1"
    manager._setup_websocket = MagicMock(return_value=True)
    manager._execute_service_ping = MagicMock(return_value="session-x")
    manager._wait_for_results = MagicMock(return_value={"raw": "ok"})
    manager._display_results = MagicMock()

    manager._run_ping_flow({"host": "h", "service": "s"})

    manager._wait_for_results.assert_called_once_with("session-x")
    manager._display_results.assert_called_once_with({"raw": "ok"}, {"host": "h", "service": "s"})


def test_run_workflow_returns_when_preflight_fails() -> None:
    """A failed preflight short-circuits the workflow before payload prep."""
    _configure_manager()
    manager = ServicePingManager()
    manager._preflight = MagicMock(return_value=False)
    manager._prepare_payload = MagicMock()

    manager._run_workflow()

    manager._prepare_payload.assert_not_called()


def test_run_workflow_runs_full_path_when_preflight_succeeds() -> None:
    """Preflight success drives payload prep and dispatch through run_ping_flow."""
    _configure_manager()
    manager = ServicePingManager()
    manager._preflight = MagicMock(return_value=True)
    manager._prepare_payload = MagicMock(return_value={"final": True})
    manager._run_ping_flow = MagicMock()

    manager._run_workflow()

    manager._run_ping_flow.assert_called_once_with({"final": True})


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------


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
    manager._preflight = MagicMock(return_value=True)

    manager.execute()

    manager._display_results.assert_called_once()
    manager._cleanup.assert_called_once()


def test_execute_prints_debug_banner_when_debug_on(capsys: pytest.CaptureFixture[str]) -> None:
    """Debug mode prints the startup banner before running the workflow."""
    _configure_manager(debug=True)
    manager = ServicePingManager()
    manager._run_workflow = MagicMock()
    manager._cleanup = MagicMock()

    manager.execute()

    out = capsys.readouterr().out
    assert "Starting Service Ping" in out
    assert "Command line args" in out


def test_execute_handles_keyboard_interrupt(capsys: pytest.CaptureFixture[str]) -> None:
    """Keyboard interrupts inside the workflow are caught and cleanup still runs."""
    _configure_manager()
    manager = ServicePingManager()
    manager._run_workflow = MagicMock(side_effect=KeyboardInterrupt())
    manager._cleanup = MagicMock()

    manager.execute()

    manager._cleanup.assert_called_once()
    assert "cancelled by user" in capsys.readouterr().out


def test_execute_handles_generic_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """Any workflow exception is caught, reported, and followed by cleanup."""
    _configure_manager()
    manager = ServicePingManager()
    manager._run_workflow = MagicMock(side_effect=RuntimeError("bad"))
    manager._cleanup = MagicMock()

    manager.execute()

    manager._cleanup.assert_called_once()
    assert "Error during Service Ping" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Menu integration
# ---------------------------------------------------------------------------


def test_misthelper_menu_120_launcher_delegates_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Menu 120 launcher should wire deps and delegate execute() to the canonical manager."""
    fake_manager = SimpleNamespace(execute=MagicMock())
    launcher_module = importlib.import_module("src.refactors.service_ping_launcher")
    monkeypatch.setattr(
        launcher_module.ServicePingLauncher,
        "_build_manager",
        lambda self: fake_manager,
    )
    monkeypatch.setattr(
        launcher_module.ServicePingLauncher,
        "_wire_dependencies",
        lambda self: None,
    )

    launcher_module.ServicePingLauncher().launch()

    fake_manager.execute.assert_called_once_with()


def test_menu_action_120_description_is_preserved() -> None:
    """Menu 120 should keep the documented service ping route and description text."""
    handler, description = MistHelper.menu_actions["120"]

    assert callable(handler)
    assert "WebSocket Service Ping" in description
    assert "SSR gateways" in description
