"""Tests for the request envelopes and the response reader."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import json  # WHY: the standard parser proves that a reply body is malformed.
import re  # WHY: the timestamp and identifier formats are regular expressions.

import pytest  # WHY: the raises check for the standard parser.

from src.operations.exporting.juniper_rma.api.messages import (  # WHY: the envelope and reply helpers.
    JuniperTransportReply,
    RequestMessageBuilder,
    ResponseStatusReader,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import make_settings  # WHY: settings fixture.

TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")  # WHY: the documented format (R-04).


def _builder() -> RequestMessageBuilder:
    """Return a builder with synthetic settings."""
    return RequestMessageBuilder(make_settings())  # WHY: the envelope uses the test identifiers.


def test_transaction_identifier_is_32_lowercase_hex_characters() -> None:
    """Each identifier is 32 lowercase hexadecimal characters and never repeats."""
    first = RequestMessageBuilder.new_transaction_id()  # WHY: one identifier.
    second = RequestMessageBuilder.new_transaction_id()  # WHY: a second identifier.
    assert re.fullmatch(r"[0-9a-f]{32}", first)  # WHY: the alphanumeric rule of fault 986.
    assert first != second  # WHY: each attempt is new (R-03).


def test_request_timestamp_uses_utc_with_milliseconds() -> None:
    """The timestamp matches YYYY-MM-DDTHH:mm:ss.SSSZ."""
    assert TIMESTAMP_PATTERN.fullmatch(RequestMessageBuilder.request_date_time())  # WHY: fault 903 rule.


def test_list_envelope_places_identifiers_inside_case_information() -> None:
    """The list operation keeps the source and transaction identifiers inside caseInformation (O-10)."""
    envelope = _builder().build_list("2026-07-10", "2026-10-08", "a" * 32)  # WHY: one list envelope.
    request = envelope["querySRListRequest"]  # WHY: the wrapper key from the contract.
    assert request["caseInformation"] == {  # WHY: the window and the identifiers share one block.
        "fromDate": "2026-07-10",
        "toDate": "2026-10-08",
        "customerSourceID": "source-test-value",
        "customerUniqueTransactionID": "a" * 32,
    }
    assert "customerSourceID" not in request  # WHY: the top-level placement returned faults 906 and 908.
    assert "customerUniqueTransactionID" not in request  # WHY: the top-level placement returned faults 906 and 908.


def test_detail_envelope_places_identifiers_inside_case_information() -> None:
    """The detail operation keeps the identifiers in caseInformation, and empty keys stay present (O-10)."""
    envelope = _builder().build_detail("CASE-1", "", "b" * 32)  # WHY: a lookup by case number.
    info = envelope["querySRRequest"]["caseInformation"]  # WHY: the block that holds the identifiers.
    assert info["customerCaseNumber"] == "CASE-1"  # WHY: the lookup key.
    assert info["serviceRequestNumber"] == ""  # WHY: an unused key is an empty string.
    assert info["customerUniqueTransactionID"] == "b" * 32  # WHY: the attempt identifier sits here.
    assert envelope["querySRRequest"]["contact"] == {  # WHY: the contact block.
        "accountID": "0000000000",
        "contactEmail": "contact.test@example.com",
    }


def test_rma_envelope_adds_the_rma_number_inside_the_wrapper() -> None:
    """The RMA operation uses the shared blocks and adds the RMA number inside the wrapper (O-5)."""
    envelope = _builder().build_rma("RMA-9", "REQ-1", "CASE-1", "c" * 32)  # WHY: one RMA envelope.
    assert envelope["queryRMARequest"]["rmaNumber"] == "RMA-9"  # WHY: the RMA to read.
    assert envelope["queryRMARequest"]["caseInformation"]["serviceRequestNumber"] == "REQ-1"  # WHY: the parent.


def test_asset_envelope_uses_the_serial_batch_and_the_top_level_identifiers() -> None:
    """The asset envelope carries the serial numbers and an alphanumeric transaction identifier (fault 986)."""
    envelope = _builder().build_assets(["JN1", "JN2"], "d" * 32)  # WHY: one batch.
    request = envelope["queryAssetsDetailsRequest"]  # WHY: the wrapper from the export example.
    assert request["serialNumbersOrSSRNs"] == ["JN1", "JN2"]  # WHY: the batch in input order.
    assert request["customerUniqueTransactionID"] == "d" * 32  # WHY: alphanumeric only.


def test_reader_accepts_wrapped_and_flat_replies() -> None:
    """A reply with or without its wrapper key gives the same usable outcome."""
    wrapped = ResponseStatusReader.read(  # WHY: a wrapped reply.
        "querysrdetails", {"querySRResponse": {"statusCode": "200", "x": 1}}
    )
    flat = ResponseStatusReader.read("querysrdetails", {"statusCode": "200", "x": 1})  # WHY: the flat reply shape.
    assert wrapped.is_usable and flat.is_usable  # WHY: both forms carry a result.
    assert wrapped.result["x"] == flat.result["x"] == 1  # WHY: the fields come out the same.


def test_warning_status_keeps_the_result_and_fault_status_does_not() -> None:
    """Status 300 is usable with its result. Status 400 is not usable and lists its faults."""
    warning = ResponseStatusReader.read(  # WHY: a warning reply.
        "querysrlist", {"statusCode": "300", "cases": [], "fault": []}
    )
    assert warning.is_usable is True  # WHY: a warning keeps its result (R-07).
    fault = ResponseStatusReader.read(  # WHY: a fault reply.
        "querysrdetails",
        {"statusCode": "400", "fault": [{"errorCode": "763", "errorMessage": "more than one"}]},
    )
    assert not fault.is_usable  # WHY: a fault gives no result.
    assert fault.has_fault("763")  # WHY: the code is available to the decision logic.


def test_known_fault_shows_its_plain_text_meaning() -> None:
    """A listed fault code shows the meaning from the contract."""
    assert ResponseStatusReader.describe("763") == (  # WHY: the documented meaning.
        "Fault 763: customerCaseNumber has more than one request with the same value"
    )


def test_unknown_fault_shows_the_raw_text_in_ascii() -> None:
    """An unlisted code shows its raw message with non-ASCII characters escaped."""
    text = ResponseStatusReader.describe("4242", "boom \u2713")  # WHY: a non-ASCII message.
    assert text.startswith("Fault 4242: boom")  # WHY: the raw text is shown.
    assert all(ord(character) < 128 for character in text)  # WHY: the console and the log stay ASCII.


def test_explain_gives_the_meaning_and_the_next_step() -> None:
    """The explanation names the meaning and the operator action for a known fault."""
    outcome = ResponseStatusReader.read(  # WHY: a fault reply.
        "querysrlist", {"statusCode": "400", "fault": [{"errorCode": "735"}]}
    )
    text = ResponseStatusReader.explain(outcome)  # WHY: the one-sentence reason.
    assert "appId is not valid" in text  # WHY: the meaning.
    assert "JUNIPER_APP_ID" in text  # WHY: the operator's next step.


def test_truncated_json_reads_as_an_empty_body() -> None:
    """A reply cut off in transit is not valid JSON, so the parser returns no body and does not crash."""
    truncated = b'{"querySRListResponse": {"statusCode": "200", "cases": ['  # WHY: a reply cut off mid-array.
    with pytest.raises(json.JSONDecodeError):  # WHY: prove that the standard parser rejects the text.
        json.loads(truncated.decode("utf-8"))  # WHY: the text is malformed JSON.
    assert JuniperTransportReply.parse_object(truncated) == {}  # WHY: the body is treated as empty.


def test_parse_object_keeps_a_json_array_and_empties_other_bodies() -> None:
    """A top-level array keeps its items under one key. An empty body and invalid text give an empty dictionary."""
    assert JuniperTransportReply.parse_object(b"[1, 2]") == {"items": [1, 2]}  # WHY: the list-of-values array.
    assert JuniperTransportReply.parse_object(b"5") == {}  # WHY: a bare number has no named fields.
    assert JuniperTransportReply.parse_object(b"") == {}  # WHY: an empty body has nothing.
    assert JuniperTransportReply.parse_object(b"not json") == {}  # WHY: invalid text is not a crash.
