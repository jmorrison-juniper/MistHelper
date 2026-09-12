"""Unit tests for switch VC stats serial_cc service extraction."""

from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.switch_vc_stats import SwitchVcStatsService


class DummyDeps:
    """Lightweight dependency bundle for SwitchVcStatsService unit tests."""

    def __init__(self):
        self.CacheUtils = MagicMock()  # Cache precheck collaborator
        self.OrgInventoryExporter = MagicMock()  # Org inventory exporter callback holder
        self.OrgInventoryExporter.inventory = MagicMock()  # Inventory callback attribute
        self.FilePathUtils = MagicMock()  # CSV path resolver
        self.ConfigUtils = MagicMock()  # Stop-signal helper
        self.DataProcessingUtils = MagicMock()  # Flatten/sanitize helpers
        self.DataExporter = MagicMock()  # Output writer
        self.mistapi = MagicMock()  # Mist SDK surface
        self.apisession = MagicMock()  # Active API session
        self.tqdm = lambda items=None, **_kwargs: items if items is not None else _TqdmContext()  # Progress wrapper
        self.FAST_MODE_ENABLED = False  # Default to sequential path in tests


class _TqdmContext:
    """Minimal tqdm context-manager stub used for fast-mode progress updates."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def update(self, _value):
        return None


@patch("src.refactors.serial_cc.switch_vc_stats._resolve_runtime_dependencies")
def test_switch_vc_stats_returns_when_no_switches(mock_resolve_runtime_dependencies):
    """Service exits early when OrgInventory.csv has no VC-capable switches."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve_runtime_dependencies.return_value = deps  # Inject synthetic dependencies
    deps.FilePathUtils.get_csv_path.return_value = "C:/tmp/OrgInventory.csv"  # Inventory CSV path used by loader
    deps.ConfigUtils.check_stop_signal.return_value = False  # No stop signal in this scenario
    with (
        patch("src.refactors.serial_cc.switch_vc_stats.open", MagicMock()),  # Avoid real file access
        patch("src.refactors.serial_cc.switch_vc_stats.csv.DictReader", return_value=[]),  # No inventory rows
    ):
        SwitchVcStatsService.execute()  # Execute service

    deps.DataExporter.write_with_format_selection.assert_not_called()  # No output should be written on empty inventory


@patch("src.refactors.serial_cc.switch_vc_stats._resolve_runtime_dependencies")
def test_switch_vc_stats_sequential_exports_records(mock_resolve_runtime_dependencies):
    """Sequential mode merges VC API payload and exports flattened CSV rows."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve_runtime_dependencies.return_value = deps  # Inject synthetic dependencies
    deps.FilePathUtils.get_csv_path.return_value = "C:/tmp/OrgInventory.csv"  # Inventory CSV path used by loader
    deps.ConfigUtils.check_stop_signal.return_value = False  # Keep loop running
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # Identity flatten for test
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # Identity sanitize for test
    deps.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis.return_value = MagicMock(data={"status": "up"})
    inventory_rows = [
        {
            "type": "switch",  # Included row
            "vc_mac": "aa:bb:cc",  # VC-capable marker
            "site_id": "site-1",  # Required API arg
            "id": "dev-1",  # Required API arg
            "name": "sw1",
            "mac": "11:22",
            "model": "EX4300",
            "serial": "ABC",
        }
    ]
    with (
        patch("src.refactors.serial_cc.switch_vc_stats.open", MagicMock()),  # Avoid real file access
        patch("src.refactors.serial_cc.switch_vc_stats.csv.DictReader", return_value=inventory_rows),  # One row
    ):
        SwitchVcStatsService.execute()  # Execute service

    deps.DataExporter.write_with_format_selection.assert_called_once()  # Export should be written exactly once
    args = deps.DataExporter.write_with_format_selection.call_args.args  # Extract positional call args for validation
    assert args[1] == "OrgSwitchVCStats.csv"  # Destination filename must match legacy contract
    assert args[0][0]["status"] == "up"  # VC API field should be present in merged export row


@patch("src.refactors.serial_cc.switch_vc_stats._resolve_runtime_dependencies")
def test_switch_vc_stats_fast_mode_uses_parallel_collection(mock_resolve_runtime_dependencies):
    """Fast mode executes concurrent worker path and still exports results."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    deps.FAST_MODE_ENABLED = True  # Force fast-mode branch
    mock_resolve_runtime_dependencies.return_value = deps  # Inject synthetic dependencies
    deps.FilePathUtils.get_csv_path.return_value = "C:/tmp/OrgInventory.csv"  # Inventory CSV path used by loader
    deps.ConfigUtils.check_stop_signal.return_value = False  # Keep loop running
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # Identity flatten for test
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # Identity sanitize for test
    deps.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis.return_value = MagicMock(data={"status": "ok"})
    inventory_rows = [
        {
            "type": "switch",  # Included row
            "vc_mac": "aa:bb:cc",  # VC-capable marker
            "site_id": "site-1",  # Required API arg
            "id": "dev-1",  # Required API arg
            "name": "sw1",
            "mac": "11:22",
            "model": "EX4300",
            "serial": "ABC",
        }
    ]

    class _DummyExecutor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, *submit_args):
            future = MagicMock()  # Synthetic future object
            future.result.return_value = fn(*submit_args)  # Execute immediately and store result
            return future

    with (
        patch("src.refactors.serial_cc.switch_vc_stats.open", MagicMock()),  # Avoid real file access
        patch("src.refactors.serial_cc.switch_vc_stats.csv.DictReader", return_value=inventory_rows),  # One row
        patch("src.refactors.serial_cc.switch_vc_stats.ThreadPoolExecutor", return_value=_DummyExecutor()),
        patch("src.refactors.serial_cc.switch_vc_stats.as_completed", side_effect=lambda futures: list(futures)),
    ):
        SwitchVcStatsService.execute()  # Execute service

    deps.DataExporter.write_with_format_selection.assert_called_once()  # Export should still be produced
