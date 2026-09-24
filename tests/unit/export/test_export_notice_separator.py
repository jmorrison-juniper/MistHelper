"""Behavior tests for the export notices of menu 69 and menu 73 (issue #3251).

The container runs Linux, so each notice must name the data folder with the
separator of the platform. Each test replaces the ``os`` name of the module
under test with a small namespace that holds ``posixpath`` or ``ntpath``. The
global ``os`` module stays the same, so pytest and the logging framework see
no change.

The Windows cases pass on the old code on purpose. They prove that each
Windows notice stays the same byte for byte.

Two strict ``xfail`` tests state the correct notice for a cloud refusal. Issue
#3305 owns that repair. When the repair merges, remove the two markers.
"""

from __future__ import annotations  # Allow the modern annotations on Python 3.13.

import logging  # Read the log records that the two exporters emit.
import ntpath  # Simulate the path rules of Windows.
import posixpath  # Simulate the path rules of the Linux container.
import sys  # Install the fake host module that the dependency resolver reads.
from dataclasses import dataclass  # Hold one test case in one small object.
from types import ModuleType, SimpleNamespace  # Build the fake host and the fake platform.
from typing import Any  # Type the loose test doubles.
from unittest.mock import MagicMock  # Record each write call.

import pytest  # Parametrize the platform cases and read the log records.

from src.export.site_config_exporter import SiteConfigExporter  # The menu 69 exporter under test.
from src.export.site_export_utils import SiteExportUtils  # The menu 73 exporter under test.

_WLAN_MODULE = "src.export.site_config_exporter"  # The module path and the logger name of menu 69.
_INSIGHT_MODULE = "src.export.site_export_utils"  # The module path and the logger name of menu 73.
_WLAN_FILE = "SiteWlans_HQ.csv"  # The bare file name that menu 69 builds for the site "HQ".
_INSIGHT_FILE = "SiteSleMetricsInsights_HQ.csv"  # The bare file name that menu 73 builds for the site "HQ".
_WLAN_ROWS = [{"ssid": "B"}, {"ssid": "A"}]  # Two WLAN rows, so the notice shows a count of 2.
_INSIGHT_ROWS = [{"metric_name": "coverage"}]  # One insight row, so the notice shows a count of 1.
_INSIGHT_DEPENDENCIES = (  # The 13 constructor dependencies other than the writer.
    "apisession",
    "PromptUtils",
    "ConfigUtils",
    "DataProcessingUtils",
    "TimeUtils",
    "EnhancedSSHRunner",
    "InsightMetricsUtils",
    "PacketCaptureManager",
    "APICoreFetchUtils",
    "check_fn",
    "PrettyTable",
    "tqdm",
    "mistapi",
)


@dataclass(frozen=True)
class NoticeCase:
    """One platform, one input, and the exact notice that the operator must read."""

    path_module: ModuleType  # The path rules of the simulated platform.
    rows: list[dict[str, Any]]  # The rows that reach the exporter.
    expected_notice: str  # The full notice text, byte for byte.


_WLAN_CASES = [  # Each case of the menu 69 notice.
    pytest.param(NoticeCase(posixpath, [], "! 0 records exported to data/SiteWlans_HQ.csv"), id="linux-empty"),
    pytest.param(NoticeCase(posixpath, _WLAN_ROWS, "! 2 records exported to data/SiteWlans_HQ.csv"), id="linux-rows"),
    pytest.param(NoticeCase(ntpath, [], "! 0 records exported to data\\SiteWlans_HQ.csv"), id="windows-empty"),
    pytest.param(NoticeCase(ntpath, _WLAN_ROWS, "! 2 records exported to data\\SiteWlans_HQ.csv"), id="windows-rows"),
]

_INSIGHT_CASES = [  # Each case of the menu 73 notice.
    pytest.param(
        NoticeCase(posixpath, [], "! 0 records exported to data/SiteSleMetricsInsights_HQ.csv (no metrics available)"),
        id="linux-empty",
    ),
    pytest.param(
        NoticeCase(posixpath, _INSIGHT_ROWS, "! 1 records exported to data/SiteSleMetricsInsights_HQ.csv"),
        id="linux-rows",
    ),
    pytest.param(
        NoticeCase(ntpath, [], "! 0 records exported to data\\SiteSleMetricsInsights_HQ.csv (no metrics available)"),
        id="windows-empty",
    ),
    pytest.param(
        NoticeCase(ntpath, _INSIGHT_ROWS, "! 1 records exported to data\\SiteSleMetricsInsights_HQ.csv"),
        id="windows-rows",
    ),
]


@pytest.fixture
def fake_host(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Install a fake ``MistHelper`` module, so menu 69 writes to a mock ``DataExporter``."""
    host = ModuleType("MistHelper")  # The resolver reads this module from sys.modules.
    host.DataExporter = MagicMock()  # Record each write, and write no file.
    monkeypatch.setitem(sys.modules, "MistHelper", host)  # Replace the host for this test only.
    return host  # Give the test access to the write mock.


def _simulate_platform(monkeypatch: pytest.MonkeyPatch, module_path: str, path_module: ModuleType) -> None:
    """Replace the ``os`` name of one module with the path rules of one platform."""
    fake_os = SimpleNamespace(path=path_module, sep=path_module.sep)  # A small stand-in for the os module.
    monkeypatch.setattr(f"{module_path}.os", fake_os, raising=False)  # The old menu 69 module has no os name.


def _notices(caplog: pytest.LogCaptureFixture, logger_name: str) -> list[str]:
    """Return each operator notice, which starts with "! ", from one module logger."""
    messages = [record.getMessage() for record in caplog.records if record.name == logger_name]  # One module only.
    return [message for message in messages if message.startswith("! ")]  # Keep the operator notices only.


def _build_insight_exporter(write: MagicMock) -> SiteExportUtils:
    """Build a real menu 73 exporter whose writer is the given mock."""
    dependencies = {name: MagicMock() for name in _INSIGHT_DEPENDENCIES}  # Each one is a mock.
    data_exporter = SimpleNamespace(write_with_format_selection=write)  # Record each write, and write no file.
    return SiteExportUtils(DataExporter=data_exporter, **dependencies)  # Use the real constructor.


def _build_refused_insight_exporter(status_code: int, write: MagicMock) -> SiteExportUtils:
    """Build a menu 73 exporter whose cloud answers the SLE metrics request with one HTTP error."""
    exporter = _build_insight_exporter(write)  # Start from the exporter with mock dependencies.
    exporter.PromptUtils.select_site.return_value = "site-1"  # The operator selects the site "site-1".
    exporter.mistapi.get_all.return_value = [{"id": "site-1", "name": "HQ"}]  # The organization holds "HQ".
    refusal = SimpleNamespace(status_code=status_code, data={"detail": "refused"})  # The error answer.
    exporter.mistapi.api.v1.sites.sle.listSiteSlesMetrics.return_value = refusal  # Refuse the SLE request.
    return exporter  # Give the test an exporter that meets one cloud refusal.


def _snapshot_before_write(caplog: pytest.LogCaptureFixture, snapshot: list[str]) -> Any:
    """Return a write stand-in that copies each log message that exists when the write starts."""

    def _record(*_args: Any, **_kwargs: Any) -> None:
        snapshot.extend(record.getMessage() for record in caplog.records)  # Copy the log at the moment of the write.

    return _record  # The mock calls this function in place of the real write.


@pytest.mark.parametrize("case", _WLAN_CASES)
def test_the_wlan_notice_uses_the_platform_separator(
    fake_host: ModuleType, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, case: NoticeCase
) -> None:
    """FR-001 and FR-003: the menu 69 notice names data/<file> on Linux and data\\<file> on Windows."""
    caplog.set_level(logging.INFO)  # Capture the operator notices, which use the info level.
    _simulate_platform(monkeypatch, _WLAN_MODULE, case.path_module)  # Run the export on the simulated platform.
    SiteConfigExporter._persist_site_wlans_csv(list(case.rows), _WLAN_FILE, "HQ")  # Export the rows of this case.
    assert _notices(caplog, _WLAN_MODULE) == [case.expected_notice]  # One notice, with the exact text.


@pytest.mark.parametrize("case", _INSIGHT_CASES)
def test_the_insight_notice_uses_the_platform_separator(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, case: NoticeCase
) -> None:
    """FR-002 and FR-003: the menu 73 notice names data/<file> on Linux and data\\<file> on Windows."""
    caplog.set_level(logging.INFO)  # Capture the notices at the info level and the warning level.
    _simulate_platform(monkeypatch, _INSIGHT_MODULE, case.path_module)  # Run the export on the simulated platform.
    exporter = _build_insight_exporter(MagicMock())  # The writer records the call and writes no file.
    exporter._write_insight_rows(list(case.rows), _INSIGHT_FILE, "HQ")  # Export the rows of this case.
    assert _notices(caplog, _INSIGHT_MODULE) == [case.expected_notice]  # One notice, with the exact text.


@pytest.mark.parametrize("rows", [pytest.param([], id="empty"), pytest.param(_WLAN_ROWS, id="rows")])
def test_the_wlan_write_keeps_the_file_name_and_the_endpoint(
    fake_host: ModuleType, monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]
) -> None:
    """FR-004: menu 69 still writes the bare file name with the endpoint name of the WLAN list."""
    _simulate_platform(monkeypatch, _WLAN_MODULE, posixpath)  # Run the export as the Linux container does.
    SiteConfigExporter._persist_site_wlans_csv(list(rows), _WLAN_FILE, "HQ")  # Export the rows of this case.
    write = fake_host.DataExporter.write_with_format_selection  # The writer mock of the fake host.
    write.assert_called_once()  # One export writes one file.
    assert write.call_args.args[1] == _WLAN_FILE  # The writer receives the bare name, without a folder.
    assert write.call_args.kwargs == {"api_function_name": "listSiteWlans"}  # The endpoint name stays the same.


@pytest.mark.parametrize("rows", [pytest.param([], id="empty"), pytest.param(_INSIGHT_ROWS, id="rows")])
def test_the_insight_write_keeps_the_file_name_and_the_endpoint(
    monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]
) -> None:
    """FR-004: menu 73 still writes the bare file name with the endpoint name of the SLE metrics."""
    _simulate_platform(monkeypatch, _INSIGHT_MODULE, posixpath)  # Run the export as the Linux container does.
    write = MagicMock()  # Record the write call.
    _build_insight_exporter(write)._write_insight_rows(list(rows), _INSIGHT_FILE, "HQ")  # Export the rows.
    write.assert_called_once_with(  # One export writes one file with the same arguments as before.
        list(rows), _INSIGHT_FILE, api_function_name="listSiteSlesMetrics"
    )


def test_the_wlan_export_logs_before_the_write(fake_host: ModuleType, caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: menu 69 logs the WLAN count at the info level before it writes the file."""
    caplog.set_level(logging.DEBUG)  # Capture every level.
    seen_before_write: list[str] = []  # The log messages that exist when the write starts.
    write = fake_host.DataExporter.write_with_format_selection  # The writer mock of the fake host.
    write.side_effect = _snapshot_before_write(caplog, seen_before_write)  # Copy the log when the write starts.
    SiteConfigExporter._persist_site_wlans_csv(list(_WLAN_ROWS), _WLAN_FILE, "HQ")  # Export two rows.
    assert "Writing 2 WLAN records for site HQ" in seen_before_write  # The info line comes before the write.


def test_the_insight_export_logs_before_the_write(caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: menu 73 logs the record count at the info level before it writes the file."""
    caplog.set_level(logging.DEBUG)  # Capture every level.
    seen_before_write: list[str] = []  # The log messages that exist when the write starts.
    write = MagicMock(side_effect=_snapshot_before_write(caplog, seen_before_write))  # Copy the log at the write.
    _build_insight_exporter(write)._write_insight_rows(list(_INSIGHT_ROWS), _INSIGHT_FILE, "HQ")  # Export one row.
    assert "Writing 1 site SLE metric insight records" in seen_before_write  # The info line comes first.


def test_the_empty_insight_export_logs_after_the_write(caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: menu 73 logs a debug line after it writes the empty file."""
    caplog.set_level(logging.DEBUG)  # Capture the debug level.
    seen_before_write: list[str] = []  # The log messages that exist when the write starts.
    write = MagicMock(side_effect=_snapshot_before_write(caplog, seen_before_write))  # Copy the log at the write.
    _build_insight_exporter(write)._write_insight_rows([], _INSIGHT_FILE, "HQ")  # Export no rows.
    after_write = [record.getMessage() for record in caplog.records if record.levelno == logging.DEBUG]  # Debug.
    expected = "Wrote an empty SLE metric insight file for site HQ"  # The debug line that confirms the write.
    assert expected in after_write  # The debug line exists.
    assert expected not in seen_before_write  # The debug line comes after the write.


@pytest.mark.xfail(strict=True, reason="Issue #3305: menu 73 reports an HTTP error as an empty export.")
@pytest.mark.parametrize("status_code", [pytest.param(404, id="http-404"), pytest.param(503, id="http-503")])
def test_a_refused_insight_request_names_the_http_status(caplog: pytest.LogCaptureFixture, status_code: int) -> None:
    """Issue #3305: an HTTP error from the cloud must not read as "no metrics available"."""
    caplog.set_level(logging.INFO)  # Capture the notices and the error lines.
    _build_refused_insight_exporter(status_code, MagicMock()).insights()  # Run menu 73 against the refusal.
    messages = [record.getMessage() for record in caplog.records if record.name == _INSIGHT_MODULE]  # Menu 73 only.
    errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]  # Error lines.
    assert not any("no metrics available" in message for message in messages)  # A refusal is not an empty result.
    assert any(str(status_code) in message for message in errors)  # The operator reads the HTTP status.
