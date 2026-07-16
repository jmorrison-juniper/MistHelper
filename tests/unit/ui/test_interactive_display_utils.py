"""Unit tests for src.ui.interactive_display_utils.

Wave 13 P2 coverage lift — InteractiveDisplayUtils is a thin static
class that lazily imports MistHelper to resolve prompt / exporter /
fetcher references. Cover every branch (site selected vs skipped,
device stats/tests/config) to close the 41% gap in one file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import sys  # WHY: patch.dict on sys.modules to inject a fake MistHelper module handle
from types import SimpleNamespace  # WHY: build lightweight stub for the MistHelper attribute surface
from unittest.mock import MagicMock, patch  # WHY: MagicMock for exporter/fetcher; patch for module swap

from src.ui.interactive_display_utils import InteractiveDisplayUtils  # WHY: subject under test


def _install_fake_misthelper(**attrs: object) -> MagicMock:
    """Return a MagicMock stand-in for the MistHelper module with the requested attrs."""
    fake_module = MagicMock()  # WHY: MagicMock accepts arbitrary attribute lookups without configuration
    for key, value in attrs.items():  # WHY: seed the attributes callers will access on MistHelper
        setattr(fake_module, key, value)  # WHY: attach each pre-built stub as a module attribute
    return fake_module  # WHY: caller patches sys.modules["MistHelper"] with this handle


def test_site_inventory_dispatches_when_site_selected(caplog) -> None:
    """site_inventory calls SiteDeviceExporter.device_inventory when a site is chosen."""
    prompt_utils = SimpleNamespace(select_site_id_from_csv=MagicMock(return_value="site-abc"))  # WHY: return real id
    exporter = SimpleNamespace(device_inventory=MagicMock())  # WHY: exporter stub tracks the invocation
    fake = _install_fake_misthelper(PromptUtils=prompt_utils, SiteDeviceExporter=exporter)  # WHY: attach both
    with patch.dict(sys.modules, {"MistHelper": fake}):  # WHY: force importlib.import_module to return our fake
        with caplog.at_level("INFO"):  # WHY: capture the info-level trace for assertion
            InteractiveDisplayUtils.site_inventory()  # WHY: execute the happy path
    exporter.device_inventory.assert_called_once_with("site-abc")  # WHY: exporter routed with selected site id
    assert any("selected site_id" in rec.message for rec in caplog.records)  # WHY: log trail preserved


def test_site_inventory_warns_when_no_site_selected(caplog) -> None:
    """site_inventory logs a warning when the user cancels site selection."""
    prompt_utils = SimpleNamespace(select_site_id_from_csv=MagicMock(return_value=None))  # WHY: user cancels
    exporter = SimpleNamespace(device_inventory=MagicMock())  # WHY: exporter must NOT be called
    fake = _install_fake_misthelper(PromptUtils=prompt_utils, SiteDeviceExporter=exporter)
    with patch.dict(sys.modules, {"MistHelper": fake}):
        with caplog.at_level("WARNING"):
            InteractiveDisplayUtils.site_inventory()
    exporter.device_inventory.assert_not_called()  # WHY: no site -> no exporter call
    assert any("No site selected" in rec.message for rec in caplog.records)  # WHY: warning path executed


def test_device_stats_uses_device_data_fetcher() -> None:
    """device_stats builds a DeviceFetchConfig and dispatches to DeviceDataFetcher.fetch()."""
    fetcher_instance = MagicMock()  # WHY: fetch() invocation observed on the fetcher instance
    device_data_fetcher = MagicMock(return_value=fetcher_instance)  # WHY: constructor returns our mock
    fake = _install_fake_misthelper(DeviceDataFetcher=device_data_fetcher)  # WHY: MistHelper.DeviceDataFetcher
    with patch.dict(sys.modules, {"MistHelper": fake}):
        InteractiveDisplayUtils.device_stats(site_id="site-x", device_id="dev-y")  # WHY: exercise stats path
    device_data_fetcher.assert_called_once()  # WHY: fetcher must be constructed exactly once
    fetcher_instance.fetch.assert_called_once_with()  # WHY: fetch() is dispatched on the built instance
    config_arg = device_data_fetcher.call_args.args[0]  # WHY: sole positional arg is the DeviceFetchConfig
    assert config_arg.site_id == "site-x"  # WHY: prompt args threaded into the config
    assert config_arg.device_id == "dev-y"  # WHY: device id threaded through
    assert config_arg.filename == "DeviceStats.csv"  # WHY: legacy filename preserved


def test_device_tests_targets_gateway_devices() -> None:
    """device_tests constructs a DeviceFetchConfig scoped to gateway devices."""
    fetcher_instance = MagicMock()
    device_data_fetcher = MagicMock(return_value=fetcher_instance)
    fake = _install_fake_misthelper(DeviceDataFetcher=device_data_fetcher)
    with patch.dict(sys.modules, {"MistHelper": fake}):
        InteractiveDisplayUtils.device_tests()  # WHY: exercise synthetic-test fetch
    fetcher_instance.fetch.assert_called_once_with()  # WHY: fetch() must be invoked
    config_arg = device_data_fetcher.call_args.args[0]
    assert config_arg.device_type == "gateway"  # WHY: only gateway devices support synthetic tests
    assert config_arg.filename == "DeviceTestResults.csv"  # WHY: legacy output filename


def test_device_config_dispatches_default_config_fetch() -> None:
    """device_config builds a DeviceFetchConfig with the default DeviceConfig.csv filename."""
    fetcher_instance = MagicMock()
    device_data_fetcher = MagicMock(return_value=fetcher_instance)
    fake = _install_fake_misthelper(DeviceDataFetcher=device_data_fetcher)
    with patch.dict(sys.modules, {"MistHelper": fake}):
        InteractiveDisplayUtils.device_config()  # WHY: exercise config fetch
    fetcher_instance.fetch.assert_called_once_with()
    config_arg = device_data_fetcher.call_args.args[0]
    assert config_arg.filename == "DeviceConfig.csv"  # WHY: legacy output filename preserved
