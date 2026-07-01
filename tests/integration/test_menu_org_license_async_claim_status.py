"""Integration smoke tests for menu item 196."""

import pytest

import MistHelper

_HAS_MENU_WIRING = all(hasattr(MistHelper, attr_name) for attr_name in ("menu_actions", "LicenseExportUtils"))
pytestmark = pytest.mark.skipif(
    not _HAS_MENU_WIRING,
    reason="MistHelper menu wiring unavailable in this test environment",
)


def test_menu_196_dispatches_to_async_claim_exporter(monkeypatch):
    called = {"value": False}

    def exporter_stub():
        called["value"] = True

    monkeypatch.setattr(
        MistHelper.LicenseExportUtils,
        "export_org_license_async_claim_status",
        exporter_stub,
    )
    action_callable, _description = MistHelper.menu_actions["196"]
    action_callable()

    assert called["value"] is True


def test_menu_196_registered_with_readable_description():
    _action_callable, description = MistHelper.menu_actions["196"]
    assert "async organization license-claim status" in description.lower()
