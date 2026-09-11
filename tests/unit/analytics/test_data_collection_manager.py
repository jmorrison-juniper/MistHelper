"""Unit tests for DataCollectionManager (issue #878 tranche 7 -- un-omit).

Covers every static method on ``src.analytics.data_collection_manager``:
``_print_continuous_loop_banner`` (banner lines),
``continuous_loop`` (stop-signal / KeyboardInterrupt / Exception branches),
``_check_stop_signal`` (delegates to ConfigUtils),
``_collection_cycle_steps`` (5-tuple order and callables),
``_execute_collection_cycle`` (happy path + KeyboardInterrupt + Exception),
``generate_support_packages`` (orchestrates the three helpers),
``_refresh_support_data`` (7 filename/func pairs to CacheUtils),
``_load_support_data_sources`` (base sources + speedtest present/absent),
``_generate_site_packages`` (skip empty sites, write package otherwise).
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from src.analytics.data_collection_manager import DataCollectionManager
from tests.support.thread_scoped_sleep import ThreadScopedSleepSpy

# WHY: caplog must target the module logger so INFO/WARNING/ERROR records surface (issue #886).
_LOGGER_NAME = "src.analytics.data_collection_manager"


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "OrgSiteExporter": MagicMock(name="OrgSiteExporter"),
        "OrgDeviceStatsExporter": MagicMock(name="OrgDeviceStatsExporter"),
        "OrgAlarmEventExporter": MagicMock(name="OrgAlarmEventExporter"),
        "GatewayTestExporter": MagicMock(name="GatewayTestExporter"),
        "CacheUtils": MagicMock(name="CacheUtils"),
        "FilePathUtils": MagicMock(name="FilePathUtils"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- _print_continuous_loop_banner ----------


def test_print_continuous_loop_banner_emits_three_lines(caplog: pytest.LogCaptureFixture) -> None:
    """Banner logs the three-line startup message at INFO."""
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    DataCollectionManager._print_continuous_loop_banner()
    out = "\n".join(r.getMessage() for r in caplog.records)
    assert "Starting continuous data collection loop" in out
    assert "every 5 seconds" in out
    assert "stop_loop.txt" in out


# ---------- continuous_loop ----------


def test_continuous_loop_exits_when_stop_signal_set(caplog: pytest.LogCaptureFixture) -> None:
    """First stop-signal check returning True breaks the loop before any cycle runs."""
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    with (
        patch.object(DataCollectionManager, "_check_stop_signal", return_value=True),
        patch.object(DataCollectionManager, "_execute_collection_cycle") as cycle,
    ):
        DataCollectionManager.continuous_loop()
    cycle.assert_not_called()
    assert any("Continuous data collection loop ended" in r.getMessage() for r in caplog.records)


def test_continuous_loop_handles_keyboard_interrupt(caplog: pytest.LogCaptureFixture) -> None:
    """KeyboardInterrupt is caught and reported to the user."""
    caplog.set_level(logging.WARNING, logger=_LOGGER_NAME)
    with (
        patch.object(DataCollectionManager, "_check_stop_signal", return_value=False),
        patch.object(DataCollectionManager, "_execute_collection_cycle", side_effect=KeyboardInterrupt),
    ):
        DataCollectionManager.continuous_loop()
    out = "\n".join(r.getMessage() for r in caplog.records)
    assert "stopped by user" in out


def test_continuous_loop_handles_unexpected_exception(caplog: pytest.LogCaptureFixture) -> None:
    """A non-KeyboardInterrupt exception is logged + reported and loop ends."""
    caplog.set_level(logging.ERROR, logger=_LOGGER_NAME)
    with (
        patch.object(DataCollectionManager, "_check_stop_signal", return_value=False),
        patch.object(DataCollectionManager, "_execute_collection_cycle", side_effect=RuntimeError("boom")),
    ):
        DataCollectionManager.continuous_loop()
    out = "\n".join(r.getMessage() for r in caplog.records)
    assert "Fatal error in continuous loop" in out
    assert "boom" in out


# ---------- _check_stop_signal ----------


def test_check_stop_signal_delegates_to_config_utils() -> None:
    """Returns whatever ConfigUtils.check_stop_signal reports (coerced to bool)."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.check_stop_signal.return_value = True
    with patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh):
        assert DataCollectionManager._check_stop_signal() is True
    fake_mh.ConfigUtils.check_stop_signal.assert_called_once_with()


def test_check_stop_signal_false_path() -> None:
    """False result flows through."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.check_stop_signal.return_value = False
    with patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh):
        assert DataCollectionManager._check_stop_signal() is False


# ---------- _collection_cycle_steps ----------


def test_collection_cycle_steps_returns_five_labelled_callables() -> None:
    """Returns the five ordered (banner, callable) tuples."""
    fake_mh = _make_mh()
    with (
        patch("src.analytics.data_collection_manager.OrgInventoryExporter") as inv,
        patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh),
    ):
        steps = DataCollectionManager._collection_cycle_steps()
    assert len(steps) == 5
    labels = [banner for banner, _ in steps]
    assert "Collecting site list" in labels[0]
    assert "Collecting organization inventory" in labels[1]
    assert "Collecting organization device stats" in labels[2]
    assert "Collecting organization device port stats" in labels[3]
    assert "Collecting VPN peer path stats" in labels[4]
    # Direct-imported OrgInventoryExporter.inventory is used at index 1.
    assert steps[1][1] is inv.inventory
    # Facade callables come from the mh stubs.
    assert steps[0][1] is fake_mh.OrgSiteExporter.sites
    assert steps[2][1] is fake_mh.OrgDeviceStatsExporter.device_stats
    assert steps[3][1] is fake_mh.OrgDeviceStatsExporter.device_port_stats
    assert steps[4][1] is fake_mh.OrgDeviceStatsExporter.vpn_peer_stats


# ---------- _execute_collection_cycle ----------


def test_execute_collection_cycle_runs_all_steps_and_paces(caplog: pytest.LogCaptureFixture) -> None:
    """Happy path invokes every step and sleeps 0.75s between them."""
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    step_a, step_b = MagicMock(name="a"), MagicMock(name="b")
    steps = [("  step A", step_a), ("  step B", step_b)]
    sleep = ThreadScopedSleepSpy()  # Thread-scoped, so a leaked thread cannot shift this record.
    with (
        patch.object(DataCollectionManager, "_collection_cycle_steps", return_value=steps),
        patch("src.analytics.data_collection_manager.time.sleep", new=sleep),
    ):
        DataCollectionManager._execute_collection_cycle(loop_count=3)
    step_a.assert_called_once_with()
    step_b.assert_called_once_with()
    assert sleep.call_args_list == [call(0.75), call(0.75)]
    assert any("Loop 3 completed successfully" in r.getMessage() for r in caplog.records)


def test_execute_collection_cycle_propagates_keyboard_interrupt() -> None:
    """KeyboardInterrupt raised by a step re-raises to the outer handler."""
    step = MagicMock(side_effect=KeyboardInterrupt)
    steps = [("  boom", step)]
    with (
        patch.object(DataCollectionManager, "_collection_cycle_steps", return_value=steps),
        patch("src.analytics.data_collection_manager.time.sleep"),
    ):
        with pytest.raises(KeyboardInterrupt):
            DataCollectionManager._execute_collection_cycle(loop_count=1)


def test_execute_collection_cycle_logs_and_backs_off_on_exception(caplog: pytest.LogCaptureFixture) -> None:
    """A step exception is logged, user notified, and a 5s back-off runs."""
    caplog.set_level(logging.WARNING, logger=_LOGGER_NAME)
    step = MagicMock(side_effect=RuntimeError("nope"))
    steps = [("  step", step)]
    sleep = ThreadScopedSleepSpy()  # Thread-scoped, so a leaked thread cannot add a false back-off.
    with (
        patch.object(DataCollectionManager, "_collection_cycle_steps", return_value=steps),
        patch("src.analytics.data_collection_manager.time.sleep", new=sleep),
    ):
        DataCollectionManager._execute_collection_cycle(loop_count=7)
    out = "\n".join(r.getMessage() for r in caplog.records)
    assert "Error in loop 7" in out
    assert "Continuing to next iteration" in out
    # The 5-second back-off must have fired.
    assert call(5) in sleep.call_args_list


# ---------- generate_support_packages ----------


def test_generate_support_packages_orchestrates_helpers_in_order() -> None:
    """Refresh -> load sources -> generate packages, in that order."""
    order: list[str] = []
    fake_sources = {"marker": True}
    with (
        patch.object(DataCollectionManager, "_refresh_support_data", side_effect=lambda: order.append("refresh")),
        patch.object(
            DataCollectionManager,
            "_load_support_data_sources",
            side_effect=lambda: (order.append("load"), fake_sources)[1],
        ),
        patch.object(
            DataCollectionManager,
            "_generate_site_packages",
            side_effect=lambda ds: order.append(f"gen:{ds is fake_sources}"),
        ),
    ):
        DataCollectionManager.generate_support_packages()
    assert order == ["refresh", "load", "gen:True"]


# ---------- _refresh_support_data ----------


def test_refresh_support_data_invokes_check_and_generate_for_each_pair() -> None:
    """All seven filename/func pairs are refreshed via CacheUtils."""
    fake_mh = _make_mh()
    with (
        patch("src.analytics.data_collection_manager.OrgInventoryExporter") as inv,
        patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh),
    ):
        DataCollectionManager._refresh_support_data()
    call_args = fake_mh.CacheUtils.check_and_generate_csv.call_args_list
    assert len(call_args) == 7
    filenames = [c.args[0] for c in call_args]
    funcs = [c.args[1] for c in call_args]
    assert filenames == [
        "OrgAlarms.csv",
        "OrgDeviceEvents.csv",
        "SiteList.csv",
        "OrgDevices.csv",
        "OrgDeviceStats.csv",
        "OrgDevicePortStats.csv",
        "AllGatewayTestResults.csv",
    ]
    assert funcs[0] is fake_mh.OrgAlarmEventExporter.alarms
    assert funcs[1] is fake_mh.OrgAlarmEventExporter.device_events
    assert funcs[2] is fake_mh.OrgSiteExporter.sites
    assert funcs[3] is inv.devices
    assert funcs[4] is fake_mh.OrgDeviceStatsExporter.device_stats
    assert funcs[5] is fake_mh.OrgDeviceStatsExporter.device_port_stats
    assert funcs[6] is fake_mh.GatewayTestExporter.test_results_by_site


# ---------- _load_support_data_sources ----------


def test_load_support_data_sources_returns_all_six_groups_and_speedtest_when_present() -> None:
    """Speedtest CSV exists -> speedtest_data is populated from CacheUtils."""
    fake_mh = _make_mh()
    fake_mh.FilePathUtils.get_csv_path.return_value = "/data/AllGatewayTestResults.csv"
    grouped = {
        "SiteList.csv": {"s1": [{"id": "s1"}]},
        "OrgAlarms.csv": {"s1": [{"a": 1}]},
        "OrgDeviceEvents.csv": {"s1": [{"e": 1}]},
        "OrgDevices.csv": {"ap-1": [{"n": 1}]},
        "OrgDeviceStats.csv": {"s1": [{"ds": 1}]},
        "OrgDevicePortStats.csv": {"s1": [{"ps": 1}]},
        "AllGatewayTestResults.csv": {"s1": [{"st": 1}]},
    }

    def loader(name, _key):
        return grouped[name]

    fake_mh.CacheUtils.load_csv_grouped_by_key.side_effect = loader
    with (
        patch("src.analytics.data_collection_manager.os.path.exists", return_value=True),
        patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh),
    ):
        out = DataCollectionManager._load_support_data_sources()
    assert out["site_data"] == grouped["SiteList.csv"]
    assert out["alarms_data"] == grouped["OrgAlarms.csv"]
    assert out["events_data"] == grouped["OrgDeviceEvents.csv"]
    assert out["devices_data"] == grouped["OrgDevices.csv"]
    assert out["device_stats_data"] == grouped["OrgDeviceStats.csv"]
    assert out["port_stats_data"] == grouped["OrgDevicePortStats.csv"]
    assert out["speedtest_data"] == grouped["AllGatewayTestResults.csv"]


def test_load_support_data_sources_speedtest_empty_when_file_missing() -> None:
    """Speedtest CSV missing -> speedtest_data stays as an empty dict."""
    fake_mh = _make_mh()
    fake_mh.FilePathUtils.get_csv_path.return_value = "/data/AllGatewayTestResults.csv"
    fake_mh.CacheUtils.load_csv_grouped_by_key.return_value = {}
    with (
        patch("src.analytics.data_collection_manager.os.path.exists", return_value=False),
        patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh),
    ):
        out = DataCollectionManager._load_support_data_sources()
    assert out["speedtest_data"] == {}
    # The 6 base sources are always loaded; the speedtest one is skipped.
    assert fake_mh.CacheUtils.load_csv_grouped_by_key.call_count == 6


# ---------- _generate_site_packages ----------


def test_generate_site_packages_skips_sites_without_alarms_or_events() -> None:
    """Sites with neither alarms nor events are skipped -- no CSV is written."""
    fake_mh = _make_mh()
    data_sources = {
        "site_data": {"s-skip": [{"id": "s-skip"}]},
        "alarms_data": {},
        "events_data": {},
        "devices_data": {},
        "device_stats_data": {},
        "port_stats_data": {},
        "speedtest_data": {},
    }
    with patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh):
        DataCollectionManager._generate_site_packages(data_sources)
    fake_mh.CacheUtils.write_support_data_to_csv.assert_not_called()


def test_generate_site_packages_writes_package_for_site_with_alarms() -> None:
    """Site with alarms present -> support package CSV written with all six data keys."""
    fake_mh = _make_mh()
    data_sources = {
        "site_data": {"s1": [{"id": "s1"}]},
        "alarms_data": {"s1": [{"a": 1}]},
        "events_data": {},
        "devices_data": {"s1": [{"d": 1}]},
        "device_stats_data": {"s1": [{"ds": 1}]},
        "port_stats_data": {"s1": [{"ps": 1}]},
        "speedtest_data": {"s1": [{"st": 1}]},
    }
    with patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh):
        DataCollectionManager._generate_site_packages(data_sources)
    fake_mh.CacheUtils.write_support_data_to_csv.assert_called_once()
    written_data, filename = fake_mh.CacheUtils.write_support_data_to_csv.call_args[0]
    assert filename == "SupportPackage_s1.csv"
    assert written_data == {
        "alarms": [{"a": 1}],
        "events": [],
        "devices": [{"d": 1}],
        "device_stats": [{"ds": 1}],
        "port_stats": [{"ps": 1}],
        "speedtests": [{"st": 1}],
    }


def test_generate_site_packages_writes_package_for_site_with_events_only() -> None:
    """Site with events but no alarms is still packaged."""
    fake_mh = _make_mh()
    data_sources = {
        "site_data": {"s2": [{"id": "s2"}]},
        "alarms_data": {},
        "events_data": {"s2": [{"e": 1}]},
        "devices_data": {},
        "device_stats_data": {},
        "port_stats_data": {},
        "speedtest_data": {},
    }
    with patch("src.analytics.data_collection_manager.importlib.import_module", return_value=fake_mh):
        DataCollectionManager._generate_site_packages(data_sources)
    fake_mh.CacheUtils.write_support_data_to_csv.assert_called_once()
    _, filename = fake_mh.CacheUtils.write_support_data_to_csv.call_args[0]
    assert filename == "SupportPackage_s2.csv"
