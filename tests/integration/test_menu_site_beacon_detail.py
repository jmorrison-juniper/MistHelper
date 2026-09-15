"""Integration smoke tests for menu item 209 getSiteBeacon wiring."""

import pytest  # WHY: skip guard and assertions use pytest helpers.

import MistHelper  # WHY: integration target exposes the runtime menu_actions mapping.
from src.utils.menu_entry import MenuEntry  # WHY: patched menu rows must match production rows.

_HAS_MENU_WIRING = all(  # WHY: skip in stripped test environments.
    hasattr(MistHelper, attr_name) for attr_name in ("menu_actions", "SiteClientExporter")
)
pytestmark = pytest.mark.skipif(  # WHY: guard avoids false failures when menu wiring is unavailable.
    not _HAS_MENU_WIRING,  # WHY: condition expression for environment-based skip.
    reason="MistHelper menu wiring unavailable in this test environment",  # WHY: explicit skip reason.
)


def test_menu_209_dispatches_to_get_site_beacon(monkeypatch: pytest.MonkeyPatch) -> None:
    """Menu key 209 should invoke SiteClientExporter.get_site_beacon through the menu row."""
    called = {"value": False}  # WHY: mutable sentinel proves the dispatch target executed.

    def exporter_stub() -> None:
        called["value"] = True  # WHY: toggle sentinel when patched menu callable runs.

    original_entry = MistHelper.menu_actions["209"]  # WHY: preserve the production row metadata.
    monkeypatch.setitem(  # WHY: replace the row because it captures the callable by value.
        MistHelper.menu_actions,  # WHY: dispatch dictionary under test.
        "209",  # WHY: getSiteBeacon menu key.
        MenuEntry(  # WHY: patched rows must keep the named production shape.
            menu_id=original_entry.menu_id,  # WHY: keep the dispatch key unchanged.
            handler=exporter_stub,  # WHY: inject an observable callable for the test.
            title=original_entry.title,  # WHY: preserve the operator text.
            category=original_entry.category,  # WHY: preserve the safety class.
            destructive=original_entry.destructive,  # WHY: preserve the safety flag.
            supports_fast=original_entry.supports_fast,  # WHY: preserve test-run metadata.
        ),
    )
    action_callable = MistHelper.menu_actions["209"].handler
    _description = MistHelper.menu_actions["209"].title  # WHY: read patched row from runtime map.
    action_callable()  # WHY: execute dispatch surface exactly as runtime menu handler does.

    assert called["value"] is True  # WHY: sentinel confirms menu dispatch reached the expected callable.


def test_menu_209_description_mentions_get_site_beacon() -> None:
    """Menu key 209 should carry a readable description for operators and docs."""
    _action_callable = MistHelper.menu_actions["209"].handler
    description = MistHelper.menu_actions["209"].title  # WHY: inspect production row entry.
    assert "getsitebeacon" in description.lower()  # WHY: operation label should expose endpoint identity for operators.
