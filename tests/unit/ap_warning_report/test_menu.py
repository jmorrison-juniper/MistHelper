"""Verify that the final AP warning menu reaches the implemented report."""

import MistHelper
from src.foundation.support.utils.operation_registry import OperationRegistry
from src.operations.exporting.ap_warning_report.operation import ApWarningReport


def test_menu_307_uses_the_report_callable() -> None:
    """Keep the operator menu connected to the report rather than a duplicate."""
    entry = MistHelper.menu_actions["307"]
    assert entry.handler is ApWarningReport.run
    assert entry.title == "Export AP warning and error codes across all sites"
    assert entry.destructive is False
    assert entry.supports_fast is False


def test_menu_307_and_308_are_safe() -> None:
    """Permit unattended read-only reports without weakening destructive menus."""
    assert max(map(int, MistHelper.menu_actions)) == 308  # Menu 308 follows menu 307.
    assert OperationRegistry.skip_category("307") == "safe"  # AP warnings remain read-only.
    assert OperationRegistry.skip_category("308") == "safe"  # Cross-org subscriptions remain read-only.
    safe_options = OperationRegistry.safe_options(list(MistHelper.menu_actions))  # Build unattended menu options.
    assert "307" in safe_options  # Menu 307 stays available to the safe sweep.
    assert "308" in safe_options  # Menu 308 stays available to the safe sweep.
    assert "306" not in safe_options  # The destructive restore operation stays excluded.
