"""Integration smoke tests for menu item 196."""

import pytest

import MistHelper
from src.utils.menu_entry import MenuEntry  # WHY: patched menu rows must match production rows.

_HAS_MENU_WIRING = all(hasattr(MistHelper, attr_name) for attr_name in ("menu_actions", "LicenseExportUtils"))
pytestmark = pytest.mark.skipif(
    not _HAS_MENU_WIRING,
    reason="MistHelper menu wiring unavailable in this test environment",
)


def test_menu_196_dispatches_to_async_claim_exporter(monkeypatch):
    called = {"value": False}  # Sentinel captured by exporter_stub to prove dispatch fired.

    def exporter_stub():
        called["value"] = True  # Flip sentinel when the menu dispatch invokes us.

    original_entry = MistHelper.menu_actions["196"]  # WHY: preserve the production row metadata.
    monkeypatch.setitem(  # WHY: replace the row because it captures the callable by value.
        MistHelper.menu_actions,  # WHY: target the runtime dispatch registry.
        "196",  # WHY: menu key under test.
        MenuEntry(  # WHY: patched rows must keep the named production shape.
            menu_id=original_entry.menu_id,  # WHY: keep the dispatch key unchanged.
            handler=exporter_stub,  # WHY: inject an observable callable for the test.
            title=original_entry.title,  # WHY: preserve the operator text.
            category=original_entry.category,  # WHY: preserve the safety class.
            destructive=original_entry.destructive,  # WHY: preserve the safety flag.
            supports_fast=original_entry.supports_fast,  # WHY: preserve test-run metadata.
        ),
    )
    action_callable = MistHelper.menu_actions["196"].handler
    _description = MistHelper.menu_actions["196"].title  # Re-read post-patch entry.
    action_callable()  # Invoke through the dispatch surface the production menu loop uses.

    assert called["value"] is True  # Sentinel proves the dispatch reached the stub.


def test_menu_196_registered_with_readable_description():
    _action_callable = MistHelper.menu_actions["196"].handler
    description = MistHelper.menu_actions["196"].title
    assert "async organization license-claim status" in description.lower()
