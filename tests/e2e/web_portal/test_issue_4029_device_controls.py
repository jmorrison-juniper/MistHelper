"""E2E contracts for the device controls of menus 94, 95, and 96."""

from __future__ import annotations

import pytest


def _parameters(client, menu: str) -> list[dict]:
    """Return the parameter contract that the portal sends to the browser."""
    response = client.get(f"/api/operations/parameters/{menu}")  # Use the real Flask route that serves the form.
    payload = response.get_json()  # Decode the same JSON that the Operations page reads.
    return payload["parameters"]  # Return the ordered answers that the run queue consumes.


def test_menu_94_requires_site_and_all_device_controls(client) -> None:
    """Menu 94 must offer one site and one device from the full site inventory."""
    assert _parameters(client, "94") == [
        {"label": "Site", "name": "site_id", "param_type": "site", "required": True},
        {
            "depends_on": "site_id",
            "device_filter": "all",
            "label": "Device",
            "name": "device_id",
            "param_type": "device",
            "required": True,
        },
    ]


def test_menu_95_requires_site_and_gateway_device_controls(client) -> None:
    """Menu 95 must limit its device selector to gateways."""
    assert _parameters(client, "95") == [
        {"label": "Site", "name": "site_id", "param_type": "site", "required": True},
        {
            "depends_on": "site_id",
            "device_filter": "gateway",
            "label": "Device",
            "name": "device_id",
            "param_type": "device",
            "required": True,
        },
    ]


def test_menu_96_requires_site_and_all_device_controls(client) -> None:
    """Menu 96 must offer one site and one device from the full site inventory."""
    assert _parameters(client, "96") == [
        {"label": "Site", "name": "site_id", "param_type": "site", "required": True},
        {
            "depends_on": "site_id",
            "device_filter": "all",
            "label": "Device",
            "name": "device_id",
            "param_type": "device",
            "required": True,
        },
    ]


@pytest.mark.parametrize("menu", ["91", "195"])
def test_follow_up_menus_remain_unchanged(client, menu: str) -> None:
    """Menus 91 and 195 stay outside this repair until their control designs are complete."""
    assert _parameters(client, menu) == []
