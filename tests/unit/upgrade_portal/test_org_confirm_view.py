"""Unit tests for safe confirmation details of a multi-site plan."""

from src.upgrade_portal.upgrade.org_confirm_view import OrgConfirmView  # Test the view without Flask.


def test_confirmation_view_names_the_full_durable_plan() -> None:
    """The view converts storage words into the complete operator plan."""
    rows = [  # Keep the selected order that the route receives.
        {"site_id": "site-a", "name": "Alpha", "device_count": 2},  # The first selected site.
        {"site_id": "site-b", "name": "Bravo", "device_count": 1},  # The second selected site.
    ]
    options = {  # Model every base choice that the confirmation must show.
        "selected_types": ["ap", "switch"],  # Keep the options-page family order.
        "version_ap": "0.15.1",  # The AP target version.
        "version_switch": "23.4R1.9",  # The switch target version.
        "strategy": "canary",  # The storage word must not reach the page.
        "canary_phases": "10,50,100",  # The page must state each percentage.
        "max_failure_percentage": 10,  # The page must state the failure unit.
        "reboot": False,  # The page must state the negative choice.
        "junos_file_action": True,  # The page must state the positive choice.
        "force": True,  # The page must state the destructive override.
    }
    operation = {  # Model the two child routes of one mixed-family plan.
        "children": [
            {  # The organization child covers both selected sites.
                "route": "upgradeOrgDevices",
                "site_name": "Alpha, Bravo",
                "device_family": "ap",
                "target_ids": ["ap-a", "ap-b"],
            },
            {  # The site child covers the switch at one site.
                "route": "upgradeSiteDevices",
                "site_name": "Alpha",
                "device_family": "switch",
                "target_ids": ["switch-a"],
            },
        ]
    }

    view = OrgConfirmView.build(rows, options, operation, ["ap", "switch"])  # Build the operator details.

    assert [site["name"] for site in view["sites"]] == ["Alpha", "Bravo"]  # Name every selected site.
    assert view["families"] == [  # Name each family and its exact target build.
        {"label": "AP", "version": "0.15.1"},
        {"label": "switch", "version": "23.4R1.9"},
    ]
    assert {"label": "Strategy", "text": "Canary"} in view["options"]  # Use the plain strategy label.
    assert {"label": "Canary phases", "text": "10%, 50%, 100%"} in view["options"]  # State each unit.
    assert {"label": "Maximum failure percentage", "text": "10%"} in view["options"]  # State the limit.
    assert {"label": "Reboot after the firmware write", "text": "No"} in view["options"]  # State reboot.
    assert {"label": "Complete the Junos file action", "text": "Yes"} in view["options"]  # State Junos action.
    assert {"label": "Force the firmware write", "text": "Yes"} in view["options"]  # State force.
    assert [child["route"] for child in view["children"]] == [  # Name both child routes in plan order.
        "Organization AP upgrade",
        "Site device upgrade",
    ]


def test_confirmation_view_uses_accessible_fallbacks_for_an_older_plan() -> None:
    """An older plan keeps a named site and shows no invented child job."""
    rows = [{"site_id": "site-a", "name": "", "device_count": 0}]  # Use the identifier when the name is absent.
    options = {"selected_types": ["ap"], "version_ap": "0.15.1", "strategy": "big_bang"}  # Legacy values.

    view = OrgConfirmView.build(rows, options, None, [])  # Build a page with no durable child list.

    assert view["sites"] == [{"name": "site-a", "device_count": 0}]  # Never show a blank site label.
    assert view["families"] == [{"label": "AP", "version": "0.15.1"}]  # Keep the exact AP target.
    assert view["children"] == []  # Do not invent a route that the record does not hold.
    assert {"label": "Strategy", "text": "Big bang"} in view["options"]  # Replace the storage word.
