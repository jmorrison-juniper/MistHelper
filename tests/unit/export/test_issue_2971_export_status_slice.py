"""Regression tests for issue #2971, export status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for the pytest process.

import logging  # WHY: caplog assertions need numeric severity checks.
from collections.abc import Iterator  # WHY: helper contexts use precise callable and iterator types.
from contextlib import contextmanager  # WHY: group related monkeypatches for the shared fetcher path.
from typing import Any  # WHY: fake Mist payloads use loose SDK-shaped values.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: caplog and monkeypatch fixtures drive the real product functions.

from src.api import api_data_fetcher as fetcher_module  # WHY: patch the shared fetcher dependencies directly.
from src.api.api_data_fetcher import APIDataFetcher  # WHY: route product functions through the real fetcher.
from src.export import org_admin_exporter as admin_module  # WHY: patch module globals in the real admin exporter.
from src.export import org_alarm_event_exporter as alarm_module  # WHY: patch module globals in the real alarm exporter.
from src.export import org_client_security_exporter as security_module  # WHY: patch the real rogue helper.
from src.export import org_device_stats_exporter as stats_module  # WHY: patch the real port-stats helper.
from src.export import org_export_utils as export_utils_module  # WHY: patch the real audit-log helper.
from src.export import (
    org_inventory_exporter as inventory_module,  # WHY: patch module globals in the real inventory exporter.
)
from src.export.org_admin_exporter import OrgAdminExporter  # WHY: import the real product class under test.
from src.export.org_alarm_event_exporter import OrgAlarmEventExporter  # WHY: import the real product class under test.
from src.export.org_client_security_exporter import OrgClientSecurityExporter  # WHY: import the real product class.
from src.export.org_device_stats_exporter import OrgDeviceStatsExporter  # WHY: import the real product class.
from src.export.org_export_utils import OrgExportUtils  # WHY: import the real product class under test.
from src.export.org_inventory_exporter import OrgInventoryExporter  # WHY: import the real product class under test.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: list[Any] = []  # WHY: simulate the empty SDK payload that previously looked normal.


def _failed_api_call(_session: Any, _org_id: str, **_kwargs: Any) -> _FailedResponse:
    """Return a 503 response for APIDataFetcher-driven exporters."""
    return _FailedResponse()  # WHY: drive the real fetcher through the outage branch.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: the operator acts on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect structured records instead of formatted text.
    )


def _fake_resolver(writer: MagicMock) -> MagicMock:
    """Build a resolver double that keeps tests inside the real product path."""
    resolver = MagicMock()  # WHY: isolate product functions from live application state.
    resolver.apisession = MagicMock()  # WHY: satisfy SDK call signatures without live credentials.
    resolver.APIDataFetcher = APIDataFetcher  # WHY: keep the shared fetcher under test real.
    resolver.DataExporter.write_with_format_selection = writer  # WHY: detect unsafe empty exports.
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fix the target org.
    resolver.RateLimitingUtils.get_rate_limited_delay.return_value = (None, 0)  # WHY: keep tests fast.
    resolver.mistapi = MagicMock()  # WHY: support exporters that read the SDK through the resolver.
    resolver.mistapi.get_all.return_value = []  # WHY: reproduce the empty SDK payload after a 503.
    return resolver  # WHY: callers patch each module with the same controlled dependencies.


@contextmanager
def _api_fetcher_context(
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
    writer: MagicMock,
) -> Iterator[None]:
    """Patch one APIDataFetcher caller and the shared fetcher dependency resolver."""
    resolver = _fake_resolver(writer)  # WHY: build a resolver that blocks live cloud and file writes.
    monkeypatch.setattr(fetcher_module.runtime_settings, "API_REQUEST_MAX_RETRIES", 0)  # WHY: fail fast.
    monkeypatch.setattr(fetcher_module.runtime_settings, "API_REQUEST_RETRY_DELAY", 0)  # WHY: fail fast.
    with patch(f"{module_name}.SourceDependencyResolver", resolver):  # WHY: control the exporter dependencies.
        with patch.object(fetcher_module, "SourceDependencyResolver", resolver):  # WHY: control the fetcher deps.
            yield  # WHY: let the real product function run under controlled dependencies.


def _patch_api_function(path: str) -> Any:
    """Patch a Mist SDK function with a callable that preserves __name__."""
    return patch(path, _failed_api_call)  # WHY: APIDataFetcher reads __name__ from the callable.


def _freeze_lookback(monkeypatch: pytest.MonkeyPatch, module: Any) -> None:
    """Freeze dynamic lookback helpers so tests stay deterministic."""
    monkeypatch.setattr(module.TimeUtils, "get_dynamic_lookback_hours", lambda *_args: 24)  # WHY: fix time.
    monkeypatch.setattr(module.TimeUtils, "log_dynamic_lookback", lambda *_args: None)  # WHY: quiet time log.


def test_usage_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A license-usage 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    with _api_fetcher_context(admin_module.__name__, monkeypatch, writer):  # WHY: patch shared dependencies.
        with _patch_api_function("src.export.org_admin_exporter.mistapi.api.v1.orgs.licenses.getOrgLicensesBySite"):
            with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                result = OrgAdminExporter.usage()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "License usage data exported to OrgUsage" not in caplog.text  # WHY: this success line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_alarms_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An alarm 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    with _api_fetcher_context(alarm_module.__name__, monkeypatch, writer):  # WHY: patch shared dependencies.
        _freeze_lookback(monkeypatch, alarm_module)  # WHY: keep the duration parameter deterministic.
        with _patch_api_function("src.export.org_alarm_event_exporter.mistapi.api.v1.orgs.alarms.searchOrgAlarms"):
            with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                result = OrgAlarmEventExporter.alarms()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Completed org alarms export and wrote results to OrgAlarms.csv." not in caplog.text  # WHY: false success.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_device_events_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A device-events 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    resolver = _fake_resolver(writer)  # WHY: control the direct exporter dependencies.
    _freeze_lookback(monkeypatch, alarm_module)  # WHY: keep the duration parameter deterministic.
    with patch.object(alarm_module, "SourceDependencyResolver", resolver):  # WHY: avoid live org resolution.
        with patch.object(alarm_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch(
                "src.export.org_alarm_event_exporter.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents",
                return_value=_FailedResponse(),
            ):
                with caplog.at_level(logging.INFO, logger=alarm_module.logger.name):  # WHY: capture module logs.
                    result = OrgAlarmEventExporter.device_events()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Fetched 0 device events from the past 24 hours" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_fetch_rogues_for_one_site_503_returns_empty_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A rogue fetch 503 must not report a successful zero-rogue site fetch."""
    writer = MagicMock()  # WHY: prove this helper does not write on a failed site fetch.
    fetch_callable = MagicMock(return_value=_FailedResponse())  # WHY: simulate one failed site request.
    resolver = _fake_resolver(writer)  # WHY: block live application state.
    with patch.object(security_module, "SourceDependencyResolver", resolver):  # WHY: provide a safe session.
        with patch.object(security_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with caplog.at_level(logging.INFO, logger=security_module.logger.name):  # WHY: capture module logs.
                result = OrgClientSecurityExporter._fetch_rogues_for_one_site(
                    fetch_callable, "site-1", "Alpha", "168h", "rogue clients"
                )  # WHY: drive the real product helper.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "! Fetched 0 rogue clients from site: Alpha" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: this per-site helper must not write an export.


def test_load_port_stats_sites_from_api_503_returns_empty_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A port-stats site-list 503 must not report a successful zero-site fetch."""
    writer = MagicMock()  # WHY: prove the failing lookup writes no export.
    resolver = _fake_resolver(writer)  # WHY: control resolver-based SDK access.
    resolver.mistapi.api.v1.orgs.sites.listOrgSites.return_value = _FailedResponse()  # WHY: feed 503.
    with patch.object(stats_module, "SourceDependencyResolver", resolver):  # WHY: avoid live org state.
        with caplog.at_level(logging.INFO, logger=stats_module.logger.name):  # WHY: capture module logs.
            result = OrgDeviceStatsExporter._load_port_stats_sites_from_api("org-1")  # WHY: drive the real helper.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "* Fetched 0 sites from API" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_audit_logs_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An audit-log 503 must not continue as a normal empty audit-log export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    resolver = _fake_resolver(writer)  # WHY: control the direct exporter dependencies.
    _freeze_lookback(monkeypatch, export_utils_module)  # WHY: keep the duration parameter deterministic.
    with patch.object(export_utils_module, "SourceDependencyResolver", resolver):  # WHY: avoid live org resolution.
        with patch.object(export_utils_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch(
                "src.export.org_export_utils.mistapi.api.v1.orgs.logs.listOrgAuditLogs",
                return_value=_FailedResponse(),
            ):
                with caplog.at_level(logging.INFO, logger=export_utils_module.logger.name):  # WHY: capture logs.
                    result = OrgExportUtils.audit_logs()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "audit logs exported to OrgAuditLogs.csv" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_inventory_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An inventory 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    with _api_fetcher_context(inventory_module.__name__, monkeypatch, writer):  # WHY: patch shared dependencies.
        with _patch_api_function("src.export.org_inventory_exporter.mistapi.api.v1.orgs.inventory.getOrgInventory"):
            with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                result = OrgInventoryExporter.inventory()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    success_message = "Completed organization inventory export and wrote results to OrgInventory.csv."  # WHY: name it.
    assert success_message not in caplog.text  # WHY: this success line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_devices_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An org-devices 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: the failing path must not write a valid empty export.
    with _api_fetcher_context(inventory_module.__name__, monkeypatch, writer):  # WHY: patch shared dependencies.
        with _patch_api_function("src.export.org_inventory_exporter.mistapi.api.v1.orgs.devices.listOrgDevices"):
            with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                result = OrgInventoryExporter.devices()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    success_message = "Completed organization devices export and wrote results to OrgDevices.csv."  # WHY: name it.
    assert success_message not in caplog.text  # WHY: this success line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.
