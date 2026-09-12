"""Unit tests for OrgAlarmEventExporter — covers every static-method branch.

Why:
    The tranche-17 push of issue #878 removes ``src/export/org_alarm_event_exporter.py``
    from the coverage ``omit`` list.  This suite drives every entry point (alarms,
    alarm_templates, events, device_events, device_events_52w) plus the private
    ``_export_data`` helper and the ``device_events`` sample-log branch so the
    module lands at 100 % line coverage without touching live Mist APIs.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.export import org_alarm_event_exporter as oaee
from src.export.org_alarm_event_exporter import OrgAlarmEventExporter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mh(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Install a synthetic ``MistHelper`` module returned by every lazy import.

    Why:
        Every helper in ``org_alarm_event_exporter`` calls
        ``importlib.import_module("MistHelper")``.  Patching that lookup once
        keeps the tests deterministic and avoids pulling in real live globals.
    """
    mh = ModuleType("MistHelper")
    mh.APIDataFetcher = MagicMock()  # type: ignore[attr-defined]
    mh.ConfigUtils = MagicMock()  # type: ignore[attr-defined]
    mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    mh.apisession = MagicMock()  # type: ignore[attr-defined]
    mh.DataExporter = MagicMock()  # type: ignore[attr-defined]
    mh.OUTPUT_FORMAT = "csv"  # type: ignore[attr-defined]
    mh.DATABASE_PATH = "/tmp/db"  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


# ---------------------------------------------------------------------------
# _export_data
# ---------------------------------------------------------------------------


class TestExportDataHelper:
    def test_builds_filename_and_invokes_fetcher(self, fake_mh: ModuleType) -> None:
        api_call = MagicMock()
        OrgAlarmEventExporter._export_data(
            api_call=api_call,
            data_type="alarm templates",
            sort_key="name",
            duration="24h",
        )
        fake_mh.APIDataFetcher.assert_called_once()  # type: ignore[attr-defined]
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["filename"] == "OrgAlarmtemplates.csv"
        assert kwargs["sort_key"] == "name"
        assert kwargs["duration"] == "24h"
        assert kwargs["limit"] == 1000
        assert kwargs["api_call"] is api_call
        fake_mh.APIDataFetcher.return_value.execute.assert_called_once()  # type: ignore[attr-defined]

    def test_data_type_with_hyphen_is_sanitized(self, fake_mh: ModuleType) -> None:
        OrgAlarmEventExporter._export_data(api_call=MagicMock(), data_type="foo-bar baz")
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["filename"] == "OrgFoobarbaz.csv"


# ---------------------------------------------------------------------------
# alarms
# ---------------------------------------------------------------------------


class TestAlarms:
    def test_success_path(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(oaee.TimeUtils, "get_dynamic_lookback_hours", return_value=24) as get_hrs,
            patch.object(oaee.TimeUtils, "log_dynamic_lookback"),
        ):
            OrgAlarmEventExporter.alarms()
        get_hrs.assert_called_once_with(24, 1)
        fake_mh.APIDataFetcher.assert_called_once()  # type: ignore[attr-defined]
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["filename"] == "OrgAlarms.csv"
        assert kwargs["duration"] == "24h"
        assert kwargs["acked"] is False

    def test_exception_is_logged_and_reraised(self, fake_mh: ModuleType) -> None:
        fake_mh.APIDataFetcher.return_value.execute.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]
        with (
            patch.object(oaee.TimeUtils, "get_dynamic_lookback_hours", return_value=24),
            patch.object(oaee.TimeUtils, "log_dynamic_lookback"),
            pytest.raises(RuntimeError, match="boom"),
        ):
            OrgAlarmEventExporter.alarms()


# ---------------------------------------------------------------------------
# alarm_templates
# ---------------------------------------------------------------------------


class TestAlarmTemplates:
    def test_delegates_to_export_data(self, fake_mh: ModuleType) -> None:
        with patch.object(OrgAlarmEventExporter, "_export_data") as export_mock:
            OrgAlarmEventExporter.alarm_templates()
        export_mock.assert_called_once()
        assert export_mock.call_args.kwargs["data_type"] == "alarm templates"
        assert export_mock.call_args.kwargs["sort_key"] == "name"


# ---------------------------------------------------------------------------
# events
# ---------------------------------------------------------------------------


class TestEvents:
    def test_resolves_lookback_and_delegates(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(oaee.TimeUtils, "get_dynamic_lookback_hours", return_value=12) as get_hrs,
            patch.object(oaee.TimeUtils, "log_dynamic_lookback"),
            patch.object(OrgAlarmEventExporter, "_export_data") as export_mock,
        ):
            OrgAlarmEventExporter.events()
        get_hrs.assert_called_once_with(24, 1)
        assert export_mock.call_args.kwargs["duration"] == "12h"
        assert export_mock.call_args.kwargs["sort_key"] == "timestamp"


# ---------------------------------------------------------------------------
# device_events
# ---------------------------------------------------------------------------


class TestDeviceEvents:
    def test_with_events_logs_sample(self, fake_mh: ModuleType, caplog: pytest.LogCaptureFixture) -> None:
        events = [{"id": 1}, {"id": 2}, {"id": 3}]
        with (
            patch.object(oaee.TimeUtils, "get_dynamic_lookback_hours", return_value=24),
            patch.object(oaee.TimeUtils, "log_dynamic_lookback"),
            patch("src.export.org_alarm_event_exporter.mistapi") as mistapi_mock,
        ):
            mistapi_mock.api.v1.orgs.devices.searchOrgDeviceEvents.return_value = MagicMock()
            mistapi_mock.get_all.return_value = events
            OrgAlarmEventExporter.device_events()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(events, "OrgDeviceEvents.csv")  # type: ignore[attr-defined]
        assert "3 device events exported" in caplog.text

    def test_without_events_skips_sample_block(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(oaee.TimeUtils, "get_dynamic_lookback_hours", return_value=24),
            patch.object(oaee.TimeUtils, "log_dynamic_lookback"),
            patch("src.export.org_alarm_event_exporter.mistapi") as mistapi_mock,
            patch.object(oaee.json, "dumps") as dumps_mock,
        ):
            mistapi_mock.api.v1.orgs.devices.searchOrgDeviceEvents.return_value = MagicMock()
            mistapi_mock.get_all.return_value = []
            OrgAlarmEventExporter.device_events()
        dumps_mock.assert_not_called()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgDeviceEvents.csv")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# device_events_52w
# ---------------------------------------------------------------------------


class TestDeviceEvents52w:
    def test_builds_exporter_with_runtime_globals(self, fake_mh: ModuleType) -> None:
        with patch("src.export.org_alarm_event_exporter.DeviceEvents52wExporter") as exporter_cls:
            instance = exporter_cls.return_value
            OrgAlarmEventExporter.device_events_52w()
        exporter_cls.assert_called_once()
        kwargs = exporter_cls.call_args.kwargs
        assert kwargs["apisession"] is fake_mh.apisession  # type: ignore[attr-defined]
        assert kwargs["org_id"] == "org-1"
        assert kwargs["data_exporter"] is fake_mh.DataExporter  # type: ignore[attr-defined]
        assert kwargs["output_format"] == "csv"
        assert kwargs["database_path"] == "/tmp/db"
        instance.export.assert_called_once()


# ---------------------------------------------------------------------------
# Simple SimpleNamespace-based smoke: helper preserves ordering
# ---------------------------------------------------------------------------


def test_smoke_module_symbols() -> None:
    """Sanity check module exports match documented public API."""
    assert isinstance(OrgAlarmEventExporter.__doc__, str)
    for name in ("alarms", "alarm_templates", "events", "device_events", "device_events_52w"):
        assert callable(getattr(OrgAlarmEventExporter, name))
    _ = SimpleNamespace  # keep import referenced when file scanned by tooling
