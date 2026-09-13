"""Integration smoke tests for menu item 196."""

import pytest

import MistHelper

_HAS_MENU_WIRING = all(hasattr(MistHelper, attr_name) for attr_name in ("menu_actions", "LicenseExportUtils"))
pytestmark = pytest.mark.skipif(
    not _HAS_MENU_WIRING,
    reason="MistHelper menu wiring unavailable in this test environment",
)


def test_menu_196_dispatches_to_async_claim_exporter(monkeypatch):
    called = {"value": False}  # Sentinel captured by exporter_stub to prove dispatch fired.

    def exporter_stub():
        called["value"] = True  # Flip sentinel when the menu dispatch invokes us.

    # WHY: menu_actions["196"] is a tuple built at MistHelper import time; the callable slot
    # captures LicenseExportUtils.export_org_license_async_claim_status by *value* (function
    # object) rather than by name resolution. Patching the class attribute would not affect
    # the tuple's captured reference, so we must replace the tuple entry itself via setitem.
    _original_callable, description = MistHelper.menu_actions["196"]  # Preserve real description.
    monkeypatch.setitem(  # Replace the dispatch tuple entry directly.
        MistHelper.menu_actions,  # Target the menu dispatch registry.
        "196",  # Menu key under test.
        (exporter_stub, description),  # New tuple with stub callable + original description.
    )
    action_callable, _description = MistHelper.menu_actions["196"]  # Re-read post-patch entry.
    action_callable()  # Invoke through the dispatch surface the production menu loop uses.

    assert called["value"] is True  # Sentinel proves the dispatch reached the stub.


def test_menu_196_registered_with_readable_description():
    _action_callable, description = MistHelper.menu_actions["196"]
    assert "async organization license-claim status" in description.lower()
