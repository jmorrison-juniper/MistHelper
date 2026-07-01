"""Integration smoke tests for the async org license-claim status menu entry."""  # Document integration scope for new menu wiring.

import MistHelper  # Import runtime module to exercise real menu_actions dispatch wiring.
import pytest  # Use pytest skip markers when optional dependencies block full module import.

_HAS_MENU_WIRING = all(  # Detect whether menu wiring symbols loaded during MistHelper import.
    hasattr(MistHelper, attr_name)  # Probe each required attribute on possibly partial module object.
    for attr_name in ("menu_actions", "LicenseExportUtils")  # Require menu registry and target exporter class.
)
pytestmark = pytest.mark.skipif(  # Skip integration smoke tests when menu wiring is not loaded.
    not _HAS_MENU_WIRING,  # Trigger skip when import ended before menu wiring definitions.
    reason="MistHelper menu wiring unavailable in this test environment",  # Explain skip root cause.
)


def test_menu_196_dispatches_to_async_claim_exporter(monkeypatch):  # Verify menu option 196 points to and executes the intended exporter.
    called = {"value": False}  # Track whether exporter function was invoked through menu dispatch.

    def exporter_stub():  # Stub exporter to avoid network/file side effects while validating menu routing.
        called["value"] = True  # Mark invocation so assertion can confirm dispatch behavior.

    monkeypatch.setattr(MistHelper.LicenseExportUtils, "export_org_license_async_claim_status", exporter_stub)  # Replace exporter target with deterministic stub.
    action_callable, _description = MistHelper.menu_actions["196"]  # Resolve menu callable from registry under test.
    action_callable()  # Execute menu action exactly as --menu path would invoke it.

    assert called["value"] is True  # Confirm menu action executed the async-claim exporter function.


def test_menu_196_registered_with_readable_description():  # Verify menu metadata remains discoverable for operators and docs.
    _action_callable, description = MistHelper.menu_actions["196"]  # Retrieve menu tuple for new operation.
    assert "async organization license-claim status" in description.lower()  # Confirm description explains endpoint intent in operator-facing text.
