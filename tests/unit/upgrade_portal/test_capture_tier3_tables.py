"""Unit tests for the guest client table and the six tier 3 tables.

Why:
    Issue #2443 records that a tier 3 capture stores six sections that
    `capture/tables.py` never read, so the page showed three tables no matter
    how many sections the capture stored. FR-003 also requires that a tier 2
    capture, an empty tier 3 section, and a failed tier 3 read each paint
    their own text, so an operator never mistakes one for another.

    Every test below feeds a plain dictionary. No test opens a socket or reads
    a real capture.
"""

from __future__ import annotations

from typing import Any

from src.upgrade_portal.capture import extras, tables


def _tier2_document() -> dict[str, Any]:
    """Return a document with no `extras` key, as a tier 2 capture stores it.

    Returns:
        The document, in the stored shape.
    """
    return {"clients": {"wired": [], "wireless": [], "guest": []}}


def _tier3_document(**extras_map: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a document that holds an `extras` map, as a tier 3 capture stores it.

    Args:
        extras_map: The six section names and their stored records. A section
            this call omits still joins the map, empty.

    Returns:
        The document, in the stored shape.
    """
    sections = dict.fromkeys(extras.SECTION_NAMES, [])
    sections.update(extras_map)
    return {"clients": {"wired": [], "wireless": [], "guest": []}, "extras": sections, "partial_reasons": []}


# --------------------------------------------------------------------------
# The guest client table.
# --------------------------------------------------------------------------


def test_the_guest_table_reads_the_guest_group() -> None:
    """The guest table reads `clients.guest`, the same way the other two client tables do."""
    document = {
        "clients": {
            "wired": [],
            "wireless": [],
            "guest": [{"mac": "aabbccddeeff", "hostname": "guest-01", "username": "visitor@example.invalid"}],
        }
    }
    rows = tables.page_tables(document)["guest_rows"]
    assert len(rows) == 1
    assert rows[0]["hostname"] == "guest-01"
    assert rows[0]["username"] == "visitor@example.invalid"


def test_the_guest_table_never_shows_an_ip_column() -> None:
    """Issue #2443 records that a guest authorization never carries an IP address."""
    assert "ip" not in tables.GUEST_COLUMNS


# --------------------------------------------------------------------------
# The four states of a tier 3 table.
# --------------------------------------------------------------------------


def test_a_tier2_document_reports_not_requested() -> None:
    """A tier 2 capture never ran a tier 3 read, so every section states that."""
    rows, held, state, message = tables.tier3_table(_tier2_document(), extras.SECTION_RADIOS, tables.RADIO_COLUMNS)
    assert rows == []
    assert held == 0
    assert state == tables.STATE_NOT_REQUESTED
    assert "not requested" in message.lower()


def test_a_tier3_section_with_a_row_reports_ok() -> None:
    """A tier 3 section that read one record shows the record and the ok state."""
    record = {"mac": "0011220000cc", "band": "5", "channel": 36}
    document = _tier3_document(radios=[record])
    rows, held, state, message = tables.tier3_table(document, extras.SECTION_RADIOS, tables.RADIO_COLUMNS)
    assert len(rows) == 1
    assert held == 1
    assert state == tables.STATE_OK
    assert message == ""
    assert rows[0]["mac"] == "0011220000cc"
    assert rows[0]["channel"] == "36"


def test_a_tier3_section_with_no_row_and_no_reason_reports_no_rows() -> None:
    """A tier 3 section that read zero records, with no stored refusal, is empty and not failed."""
    document = _tier3_document()
    rows, held, state, message = tables.tier3_table(document, extras.SECTION_TUNNELS, tables.TUNNEL_COLUMNS)
    assert rows == []
    assert held == 0
    assert state == tables.STATE_NO_ROWS
    assert "no row" in message.lower()


def test_a_tier3_section_with_a_stored_reason_reports_unavailable() -> None:
    """A failed cloud call must never read as an empty site."""
    document = _tier3_document()
    document["partial_reasons"] = [
        {"section": extras.SECTION_BGP_PEERS, "reason": extras.REASON_CALL_FAILED, "http_status": 0}
    ]
    rows, held, state, message = tables.tier3_table(document, extras.SECTION_BGP_PEERS, tables.BGP_PEER_COLUMNS)
    assert rows == []
    assert held == 0
    assert state == tables.STATE_UNAVAILABLE
    assert "failed" in message.lower()


def test_page_tables_wires_every_tier3_section() -> None:
    """`page_tables` must expose the rows, the held count, the state, and the message of each section."""
    document = _tier3_document(switch_ports=[{"mac": "0011220000aa", "port_id": "ge-0/0/1"}])
    context = tables.page_tables(document)
    assert context["switch_port_rows"][0]["port_id"] == "ge-0/0/1"
    assert context["switch_port_state"] == tables.STATE_OK
    assert context["poe_state"] == tables.STATE_NO_ROWS
    assert context["radio_state"] == tables.STATE_NO_ROWS
    assert context["tunnel_state"] == tables.STATE_NO_ROWS
    assert context["bgp_peer_state"] == tables.STATE_NO_ROWS
    assert context["alarm_state"] == tables.STATE_NO_ROWS


def test_a_credential_field_never_reaches_a_tier3_row() -> None:
    """The same credential filter that guards the device table guards a tier 3 table."""
    document = _tier3_document(radios=[{"mac": "0011220000cc", "band": "5", "api_token": "must-not-appear"}])
    rows, _held, _state, _message = tables.tier3_table(document, extras.SECTION_RADIOS, tables.RADIO_COLUMNS)
    assert "api_token" not in rows[0]
    assert "must-not-appear" not in rows[0].values()
