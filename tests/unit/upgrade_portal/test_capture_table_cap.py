"""Unit tests for the row cap of the capture page tables.

Why:
    A capture of a large site holds thousands of client rows. One page that
    painted every row would render slowly, and the browser would then sort that
    whole table on every header press. Issue #2075 asks each table to carry a
    cap.

    A silent cut is worse than no cut. An operator who read a cut table as the
    whole site would count devices that the page never showed, and would then
    plan an upgrade against the wrong number.
"""

from __future__ import annotations

from typing import Any

from src.upgrade_portal.capture import tables


def device_document(count: int) -> dict[str, Any]:
    """Return one capture document that holds a chosen count of devices.

    Args:
        count: How many device records the document holds.

    Returns:
        The document, in the stored shape.
    """
    return {
        "devices": [
            {
                "mac": f"{index:012x}",
                "name": f"switch-{index}",
                "type": "switch",
                "model": "EX4100-F-12P",
                "version": "25.4R1-S2.3",
            }
            for index in range(count)
        ]
    }


def client_document(count: int) -> dict[str, Any]:
    """Return one capture document that holds a chosen count of wired clients.

    Args:
        count: How many client records the document holds.

    Returns:
        The document, in the stored shape.
    """
    return {"clients": {"wired": [{"mac": f"{index:012x}", "ip": "192.168.1.2"} for index in range(count)]}}


def test_a_small_table_reaches_the_page_whole() -> None:
    """The common site fits inside the cap, so the page states nothing extra."""
    result = tables.page_tables(device_document(8))
    assert len(result["device_rows"]) == 8  # Every device reaches the page.
    assert result["device_rows_held"] == 8  # The held count equals the row count, so no note appears.


def test_a_large_device_table_is_cut_at_the_cap() -> None:
    """A site above the cap paints the cap and never every row."""
    held = tables.TABLE_ROW_CAP + 25  # A site that passes the cap.
    result = tables.page_tables(device_document(held))
    assert len(result["device_rows"]) == tables.TABLE_ROW_CAP  # The page paints the cap alone.
    assert result["device_rows_held"] == held  # The page still states the whole count.


def test_a_large_client_table_is_cut_at_the_cap() -> None:
    """The client tables carry the same cap as the device table."""
    held = tables.TABLE_ROW_CAP + 1  # One row above the cap.
    result = tables.page_tables(client_document(held))
    assert len(result["wired_rows"]) == tables.TABLE_ROW_CAP
    assert result["wired_rows_held"] == held


def test_the_cut_keeps_the_first_rows_in_order() -> None:
    """A cut must remove the end of the table, never the middle of it."""
    result = tables.page_tables(device_document(tables.TABLE_ROW_CAP + 10))
    assert result["device_rows"][0]["name"] == "switch-0"  # The first row stays first.
    assert result["device_rows"][-1]["name"] == f"switch-{tables.TABLE_ROW_CAP - 1}"  # The cut ends at the cap.


def test_an_empty_capture_holds_no_row_and_no_count() -> None:
    """A running capture paints three empty tables and raises nothing."""
    result = tables.page_tables({})
    assert result["device_rows"] == []
    assert result["device_rows_held"] == 0  # No note appears, because nothing was cut.


def test_the_page_reads_the_cap_by_name() -> None:
    """The template states the cap, so the number lives in one module only."""
    assert tables.page_tables({})["table_row_cap"] == tables.TABLE_ROW_CAP


def test_the_page_builds_guest_and_every_tier_three_table() -> None:
    """A Tier 3 capture exposes the guest group and all six extra sections."""
    capture = {
        "tier": 3,
        "clients": {"guest": [{"mac": "aabbccddeeff", "username": "visitor"}]},
        "extras": {
            "switch_ports": [{"port_id": "ge-0/0/1", "up": True}],
            "poe": [{"port_id": "ge-0/0/1", "power": 4.2}],
            "radios": [{"band": "5", "channel": 36}],
            "tunnels": [],
            "bgp_peers": [],
            "alarms": [{"id": "alarm-1", "type": "switch_down"}],
        },
    }
    result = tables.page_tables(capture)
    views = {view["key"]: view for view in result["additional_tables"]}
    assert result["tier3_requested"] is True
    assert set(views) == {
        "clients-guest",
        "switch-ports",
        "poe",
        "radios",
        "tunnels",
        "bgp-peers",
        "alarms",
    }
    assert views["clients-guest"]["rows"][0]["username"] == "visitor"
    assert views["switch-ports"]["rows"][0]["up"] == "True"
    assert views["tunnels"]["rows"] == []


def test_a_tier_two_capture_names_that_tier_three_was_not_requested() -> None:
    """A Tier 2 result must not make absent Tier 3 rows look like empty reads."""
    result = tables.page_tables({"tier": 2, "clients": {"guest": []}})
    assert result["tier3_requested"] is False
    assert [view["key"] for view in result["additional_tables"]] == ["clients-guest"]


def test_a_large_tier_three_table_uses_the_shared_cap() -> None:
    """The new tables obey the same page limit as the original tables."""
    held = tables.TABLE_ROW_CAP + 3
    result = tables.page_tables({"tier": 3, "extras": {"alarms": [{"id": f"alarm-{index}"} for index in range(held)]}})
    alarms = next(view for view in result["additional_tables"] if view["key"] == "alarms")
    assert len(alarms["rows"]) == tables.TABLE_ROW_CAP
    assert alarms["held"] == held


def test_nested_values_are_safe_json_and_nested_credentials_leave() -> None:
    """A structured Tier 3 cell stays readable and does not expose a secret."""
    capture = {
        "tier": 3,
        "extras": {"alarms": [{"id": "alarm-1", "detail": {"password": "drop", "safe": "kept"}}]},
    }
    result = tables.page_tables(capture)
    alarms = next(view for view in result["additional_tables"] if view["key"] == "alarms")
    assert alarms["rows"][0]["detail"] == '{"safe":"kept"}'
