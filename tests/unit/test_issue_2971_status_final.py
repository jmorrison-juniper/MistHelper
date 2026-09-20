"""Regression tests for issue #2971, final status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest imports.

import logging  # WHY: caplog assertions need severity checks.
from typing import Any  # WHY: response doubles use loose Mist SDK shapes.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: pytest fixtures drive the real product functions.

from src.ssh import cli_shell_manager as shell_module  # WHY: patch and drive the real CLI shell helper.
from src.ssh.cli_shell_manager import CLIShellManager  # WHY: import the real product class.
from src.ui import prompt_utils as prompt_module  # WHY: patch and drive the real prompt helpers.
from src.ui.prompt_utils import PromptUtils  # WHY: import the real prompt helper.
from src.upgrade_portal.api.run_controls import routes as run_routes  # WHY: patch the real evidence reader.
from src.upgrade_portal.api.run_controls.routes import SiteStatsFirmwareEvidenceReader  # WHY: real reader.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: operators act on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect structured records instead of formatted text.
    )


def _resolver() -> MagicMock:
    """Build a resolver double that blocks live cloud access."""
    resolver = MagicMock()  # WHY: isolate product functions from live application state.
    resolver.apisession = MagicMock()  # WHY: satisfy SDK call signatures without live credentials.
    return resolver  # WHY: callers patch product modules with this dependency set.


def _failed_api_call(*_args: Any, **_kwargs: Any) -> _FailedResponse:
    """Return a 503 response for generic helper tests."""
    return _FailedResponse()  # WHY: drive the real functions through the outage branch.


def _run_prompt_client_fetch(
    caplog: pytest.LogCaptureFixture,
    method_name: str,
    api_namespace: Any,
    api_name: str,
    target_id: str,
    success_message: str,
) -> None:
    """Drive one prompt client fetch helper through a 503 response."""
    with patch.object(prompt_module, "SourceDependencyResolver", _resolver()):  # WHY: avoid live app state.
        with patch.object(prompt_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(api_namespace, api_name, _failed_api_call):  # WHY: replace the cloud request.
                with caplog.at_level(logging.INFO, logger=prompt_module.logger.name):  # WHY: capture module logs.
                    result = getattr(PromptUtils, method_name)(target_id)  # WHY: drive the real product helper.
    assert result == []  # WHY: the existing failure contract for these helpers is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert success_message not in caplog.text  # WHY: this success line would be false.


def test_site_wired_clients_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A site wired-client 503 must not report a successful zero-client fetch."""
    _run_prompt_client_fetch(
        caplog,
        "_fetch_site_wired_clients",
        prompt_module.mistapi.api.v1.sites.wired_clients,
        "searchSiteWiredClients",
        "site-1",
        "Found 0 wired clients in site",
    )  # WHY: share the real prompt helper assertion flow.


def test_org_wireless_clients_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An organization wireless-client 503 must not report a successful zero-client fetch."""
    _run_prompt_client_fetch(
        caplog,
        "_fetch_org_wireless_clients",
        prompt_module.mistapi.api.v1.orgs.clients,
        "searchOrgWirelessClients",
        "org-1",
        "Found 0 wireless clients in organization",
    )  # WHY: share the real prompt helper assertion flow.


def test_org_wired_clients_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An organization wired-client 503 must not report a successful zero-client fetch."""
    _run_prompt_client_fetch(
        caplog,
        "_fetch_org_wired_clients",
        prompt_module.mistapi.api.v1.orgs.wired_clients,
        "searchOrgWiredClients",
        "org-1",
        "Found 0 wired clients in organization",
    )  # WHY: share the real prompt helper assertion flow.


def test_create_session_503_returns_none_and_suppresses_empty_url(caplog: pytest.LogCaptureFixture) -> None:
    """A CLI shell 503 must not collapse to a silent empty shell URL."""
    with patch.object(shell_module, "SourceDependencyResolver", _resolver()):  # WHY: avoid live app state.
        with patch.object(
            shell_module.mistapi.api.v1.sites.devices,  # WHY: patch the exact namespace used by product code.
            "createSiteDeviceShellSession",  # WHY: replace the shell-session API function.
            _failed_api_call,  # WHY: feed a 503 response with an empty payload.
        ):
            with caplog.at_level(logging.DEBUG, logger=shell_module.logger.name):  # WHY: capture debug success lines.
                result = CLIShellManager._create_session("site-1", "dev-1")  # WHY: drive the real product helper.
    assert result is None  # WHY: the existing failure contract for shell creation is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "CLI shell session URL present" not in caplog.text  # WHY: this success-state trace would be false.


def test_read_site_statistics_503_returns_none_and_suppresses_debug_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A site-statistics evidence 503 must not continue as a debug-only status."""
    reader = SiteStatsFirmwareEvidenceReader(MagicMock())  # WHY: use the real reader with a fake cloud session.
    with patch.object(
        run_routes.mistapi.api.v1.sites.stats,  # WHY: patch the exact namespace used by product code.
        "listSiteDevicesStats",  # WHY: replace the site statistics API function.
        _failed_api_call,  # WHY: feed a 503 response with an empty payload.
    ):
        with caplog.at_level(logging.DEBUG, logger=run_routes.logger.name):  # WHY: capture debug status lines.
            result = reader._read_site_statistics("site-1")  # WHY: drive the real product helper.
    assert result is None  # WHY: the existing failure contract for failed evidence read is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "listSiteDevicesStats returned status 503" not in caplog.text  # WHY: DEBUG alone hides the failure.


def test_read_site_statistics_404_returns_none_and_logs_warning_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A site-statistics evidence 404 must not continue as a normal empty read."""

    class ClientErrorResponse:
        """Response object for a 404 with an empty payload."""

        status_code = 404  # WHY: simulate a missing site or device response from the cloud.
        data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.

    reader = SiteStatsFirmwareEvidenceReader(MagicMock())  # WHY: use the real reader with a fake cloud session.
    with patch.object(
        run_routes.mistapi.api.v1.sites.stats,  # WHY: patch the exact namespace used by product code.
        "listSiteDevicesStats",  # WHY: replace the site statistics API function.
        return_value=ClientErrorResponse(),  # WHY: feed a 404 response with an empty payload.
    ):
        with caplog.at_level(logging.DEBUG, logger=run_routes.logger.name):  # WHY: capture all status logs.
            result = reader._read_site_statistics("site-1")  # WHY: drive the real product helper.
    assert result is None  # WHY: the existing failure contract for failed evidence read is None.
    assert any(  # WHY: require an operator-grade log for the exact status.
        record.levelno >= logging.WARNING and "404" in record.getMessage() for record in caplog.records
    )
