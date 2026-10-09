"""Tests for the request parsers, the identifier rule, and the RMA item parsing."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: the parsers under test.
    FieldReader,
    IdentifierRule,
    RmaItem,
    RmaRecord,
    ServiceRequest,
)


def test_identifier_rule_accepts_one_to_forty_letters_digits_and_hyphens() -> None:
    """Valid identifiers pass, and spaces, symbols, and overlong values fail."""
    assert IdentifierRule.is_valid("2026-0918-934810")  # WHY: a request-number shape.
    assert IdentifierRule.is_valid("A" * 40)  # WHY: the 40-character ceiling.
    assert not IdentifierRule.is_valid("A" * 41)  # WHY: one character over the ceiling.
    assert not IdentifierRule.is_valid("bad value")  # WHY: a space breaks the rule.
    assert not IdentifierRule.is_valid("")  # WHY: an empty value breaks the rule.


def test_field_reader_accepts_one_object_or_a_list() -> None:
    """A single object and a list of objects both read as items (R-09)."""
    assert FieldReader.items({"rma": {"rmaNumber": "R1"}}, "rma") == [{"rmaNumber": "R1"}]  # WHY: single object.
    assert FieldReader.items({"rma": [{"rmaNumber": "R2"}, "junk"]}, "rma") == [{"rmaNumber": "R2"}]  # WHY: list.
    assert FieldReader.items({}, "rma") == []  # WHY: a missing field has no items.


def test_list_row_maps_the_summary_fields() -> None:
    """A list row becomes a request with its summary fields."""
    request = ServiceRequest.from_list_row(  # WHY: a list row from Juniper.
        {"serviceRequestNumber": "2026-0001-000001", "customerCaseNumber": " CASE-1 ", "srStatus": "Open"}
    )
    assert request.request_number == "2026-0001-000001"  # WHY: the natural key.
    assert request.case_number == "CASE-1"  # WHY: the join value is trimmed.
    assert request.rma_numbers == ()  # WHY: the list row has no RMA list.


def test_detail_collects_the_rma_numbers_in_reply_order() -> None:
    """The detail lists its RMA numbers and skips blank ones."""
    detail = {  # WHY: a detail reply.
        "serviceRequestNumber": "2026-0001-000001",
        "rma": [{"rmaNumber": "RMA-1"}, {"rmaNumber": ""}, {"rmaNumber": "RMA-2"}],
        "contact": {"accountName": "Test Account"},
    }
    request = ServiceRequest.from_detail(detail)  # WHY: parse the detail.
    assert request.rma_numbers == ("RMA-1", "RMA-2")  # WHY: blanks are dropped.
    assert request.account_name == "Test Account"  # WHY: the account name is read from the contact.


def test_rma_record_reads_a_nested_or_a_flat_address() -> None:
    """The address may sit under an address object or directly in the contact (R-09)."""
    nested = RmaRecord.from_result(  # WHY: the nested address shape.
        {"rmaNumber": "R1", "rmaContact": {"address": {"address1": "1 Way", "city": "Town"}}},
        "REQ-1",
    )
    flat = RmaRecord.from_result(  # WHY: the flat address shape.
        {"rmaNumber": "R2", "rmaContact": {"address1": "2 Way", "city": "Village"}}, "REQ-1"
    )
    assert (nested.address1, nested.city) == ("1 Way", "Town")  # WHY: the nested form.
    assert (flat.address1, flat.city) == ("2 Way", "Village")  # WHY: the flat form.


def test_malformed_dates_keep_their_raw_text() -> None:
    """A malformed timestamp is kept as received, not parsed or dropped (R-09)."""
    result = {  # WHY: an RMA with defective items.
        "replacementItems": [
            {"itemNumber": "R-1", "deliveredDate": "2017-09-05-T12:57:00.000Z", "replacementStatus": "Delivered"},
        ]
    }
    items = RmaItem.parse_all("RMA-1", result)  # WHY: parse the items.
    assert items[0].delivered_date == "2017-09-05-T12:57:00.000Z"  # WHY: the raw text is preserved.
    assert items[0].status == "Delivered"  # WHY: the status comes from its item-type key.


def test_items_of_every_type_get_unique_keys() -> None:
    """Defective, replacement, and CE items keep their type, and a CE item without a number still gets a key."""
    result = {  # WHY: an RMA with no items.
        "defectiveItems": [{"itemNumber": "D-1", "defectiveItemStatus": "Received"}],
        "replacementItems": [{"itemNumber": "R-1", "defectiveItemNumber": "D-1", "replacementStatus": "Shipped"}],
        "ceItems": [{"defectiveItemNumber": "D-1", "engineerStatus": "Scheduled", "vendorName": "Vendor"}],
    }
    items = RmaItem.parse_all("RMA-1", result)  # WHY: parse the items.
    assert [item.item_type for item in items] == ["defective", "replacement", "ce"]  # WHY: the three lists.
    assert items[2].item_number == "D-1"  # WHY: the CE item falls back to its parent item number.
    assert len({(item.item_type, item.item_number) for item in items}) == 3  # WHY: the keys do not collide.


def test_rma_with_no_items_gives_an_empty_list() -> None:
    """An RMA with no item lists yields no items."""
    assert RmaItem.parse_all("RMA-1", {"rmaNumber": "RMA-1"}) == []  # WHY: nothing to parse.
