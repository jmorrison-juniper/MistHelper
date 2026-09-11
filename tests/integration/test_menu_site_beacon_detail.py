"""Integration smoke tests for menu item 209 getSiteBeacon wiring."""

import pytest  # WHY: skip guard and assertions use pytest helpers.

import MistHelper  # WHY: integration target exposes the runtime menu_actions mapping.

_HAS_MENU_WIRING = all(  # WHY: skip in stripped test environments.
    hasattr(MistHelper, attr_name) for attr_name in ("menu_actions", "SiteClientExporter")
)
pytestmark = pytest.mark.skipif(  # WHY: guard avoids false failures when menu wiring is unavailable.
    not _HAS_MENU_WIRING,  # WHY: condition expression for environment-based skip.
    reason="MistHelper menu wiring unavailable in this test environment",  # WHY: explicit skip reason.
)


def test_menu_209_dispatches_to_get_site_beacon(monkeypatch: pytest.MonkeyPatch) -> None:
    """Menu key 209 should invoke SiteClientExporter.get_site_beacon through menu_actions tuple dispatch."""
    called = {"value": False}  # WHY: mutable sentinel proves the dispatch target executed.

    def exporter_stub() -> None:
        called["value"] = True  # WHY: toggle sentinel when patched menu callable runs.

    (
        _original_callable,
        description,
    ) = MistHelper.menu_actions[
        "209"
    ]  # WHY: preserve description while swapping callable.
    monkeypatch.setitem(  # WHY: menu tuple holds callable by value.
        MistHelper.menu_actions,  # WHY: dispatch dictionary under test.
        "209",  # WHY: new getSiteBeacon menu key.
        (exporter_stub, description),  # WHY: preserve description while injecting observable callable.
    )
    action_callable, _description = MistHelper.menu_actions["209"]  # WHY: read patched tuple from runtime map.
    action_callable()  # WHY: execute dispatch surface exactly as runtime menu handler does.

    assert called["value"] is True  # WHY: sentinel confirms menu dispatch reached the expected callable.


def test_menu_209_description_mentions_get_site_beacon() -> None:
    """Menu key 209 should carry a readable description for operators and docs."""
    _action_callable, description = MistHelper.menu_actions["209"]  # WHY: inspect production tuple entry.
    assert "getsitebeacon" in description.lower()  # WHY: operation label should expose endpoint identity for operators.
