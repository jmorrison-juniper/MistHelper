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
