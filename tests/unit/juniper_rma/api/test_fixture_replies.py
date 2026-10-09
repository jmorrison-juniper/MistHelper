"""Tests that the saved Case and Asset replies read through the real services."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import json  # WHY: the standard parser proves that a reply body is malformed.

import pytest  # WHY: the raises check for the standard parser.

from src.operations.exporting.juniper_rma.api.asset_service import (
    JuniperAssetService,  # WHY: the Asset service under test.
)
from src.operations.exporting.juniper_rma.api.case_service import (
    JuniperCaseService,  # WHY: the Case service under test.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: the body parser, the envelope builder, and the reader.  # noqa: E501
    JuniperTransportReply,
    RequestMessageBuilder,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: the parsers under test.
    RmaItem,
    ServiceRequest,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import (  # WHY: the fake gateway and the saved replies.
    ASSET_BASE_URL,
    CASE_BASE_URL,
    FakeGateway,
    load_fixture,
    make_settings,
)


def _case_service(gateway: FakeGateway) -> JuniperCaseService:
    """Return the real Case service wired to the fake gateway."""
    return JuniperCaseService(  # WHY: the real service, fed by the double.
        gateway,
        RequestMessageBuilder(make_settings()),
        ResponseStatusReader(),
        CASE_BASE_URL,
    )


def _asset_service(gateway: FakeGateway) -> JuniperAssetService:
    """Return the real Asset service wired to the fake gateway."""
    return JuniperAssetService(  # WHY: the real service, fed by the double.
        gateway,
        RequestMessageBuilder(make_settings()),
        ResponseStatusReader(),
        ASSET_BASE_URL,
    )


def test_saved_list_reply_yields_its_cases() -> None:
    """The saved list reply is usable and carries both cases in reply order."""
    reply = load_fixture("case", "querySRListResponse_success")  # WHY: the saved list reply.
    gateway = FakeGateway(bodies={"querysrlist": [reply]})  # WHY: one reply for the single read.
    outcome = _case_service(gateway).list_requests()  # WHY: the real list read.
    numbers = [row["customerCaseNumber"] for row in outcome.result["cases"]]  # WHY: the case numbers in order.
    assert outcome.is_usable is True  # WHY: a 200 list carries a result.
    assert numbers == ["CASE-TEST-100", "CASE-TEST-200"]  # WHY: both fixture cases, in order.


def test_saved_list_fault_is_not_usable_and_explains_the_setting() -> None:
    """The saved 735 fault is not usable, and the explanation names the setting to check."""
    reply = load_fixture("case", "querySRListResponse_fault_735")  # WHY: the saved 735 fault.
    gateway = FakeGateway(bodies={"querysrlist": [reply]})  # WHY: one reply for the single read.
    outcome = _case_service(gateway).list_requests()  # WHY: the real list read.
    explanation = ResponseStatusReader.explain(outcome)  # WHY: the text the operator sees.
    assert outcome.is_usable is False  # WHY: a 400 reply gives no result.
    assert outcome.has_fault("735")  # WHY: the fault code is listed.
    assert "JUNIPER_APP_ID" in explanation  # WHY: the next step names the setting.


def test_saved_detail_reply_yields_the_request_and_its_rma_numbers() -> None:
    """The saved detail reply yields the request number and its RMA list."""
    reply = load_fixture("case", "querySRResponse_success")  # WHY: the saved detail reply.
    gateway = FakeGateway(bodies={"querysrdetails": [reply]})  # WHY: one reply for the single read.
    outcome = _case_service(gateway).get_request(request_number="2026-0001-000001")  # WHY: the detail read.
    request = ServiceRequest.from_detail(outcome.result)  # WHY: the parser under test.
    assert request.request_number == "2026-0001-000001"  # WHY: the natural key.
    assert request.rma_numbers == ("RMA-TEST-1",)  # WHY: the RMA list from the detail.


def test_saved_fault_763_is_not_usable_and_carries_the_code() -> None:
    """The saved 763 fault gives no single request, so the caller can mark the case ambiguous."""
    reply = load_fixture("case", "querySRResponse_fault_763")  # WHY: the saved 763 fault.
    gateway = FakeGateway(bodies={"querysrdetails": [reply]})  # WHY: one reply for the single read.
    outcome = _case_service(gateway).get_request(case_number="CASE-TEST-100")  # WHY: the detail read by case.
    assert outcome.is_usable is False  # WHY: fault 763 gives no single request.
    assert outcome.has_fault("763")  # WHY: the caller marks the ticket ambiguous.


def test_saved_rma_reply_yields_its_item_with_the_tracking_number() -> None:
    """The saved RMA reply yields one defective item and keeps its tracking number."""
    reply = load_fixture("case", "queryRMAResponse_success")  # WHY: the saved RMA reply.
    gateway = FakeGateway(bodies={"queryrmadetails": [reply]})  # WHY: one reply for the single read.
    outcome = _case_service(gateway).get_rma("RMA-TEST-1", "2026-0001-000001", "")  # WHY: the RMA read.
    items = RmaItem.parse_all("RMA-TEST-1", outcome.result)  # WHY: the parser under test.
    assert [item.item_number for item in items] == ["ITEM-TEST-1"]  # WHY: one defective item.
    assert items[0].tracking_number == "TRACK-TEST-1"  # WHY: the tracking number is kept.


def test_saved_asset_reply_yields_the_asset_and_nothing_pending() -> None:
    """The saved asset reply keeps the asset and leaves no serial number pending."""
    reply = load_fixture("asset", "queryAssetsDetailsResponse_success")  # WHY: the saved asset reply.
    gateway = FakeGateway(bodies={"queryAssetsDetails": [reply]})  # WHY: one reply for the single pass.
    result = _asset_service(gateway).query_all(["SN-TEST-0001"])  # WHY: the batched read.
    assert [asset["serialNumber"] for asset in result.assets] == ["SN-TEST-0001"]  # WHY: the asset is kept.
    assert result.is_complete is True  # WHY: nothing is pending.


def test_saved_not_processed_reply_sends_only_the_pending_serial_again() -> None:
    """The not-processed serial goes out once more, and the other serials are not sent again."""
    gateway = FakeGateway(  # WHY: two replies, one for each pass.
        bodies={  # WHY: pass one is not processed, and pass two answers.
            "queryAssetsDetails": [
                load_fixture("asset", "queryAssetsDetailsResponse_not_processed"),
                load_fixture("asset", "queryAssetsDetailsResponse_success"),
            ]
        }
    )
    result = _asset_service(gateway).query_all(["SN-TEST-0001", "SN-TEST-0002", "SN-TEST-9999"])  # WHY: three serials.
    sent = [call.body["queryAssetsDetailsRequest"]["serialNumbersOrSSRNs"] for call in gateway.calls]  # WHY: each pass.
    assert sent == [["SN-TEST-0001", "SN-TEST-0002", "SN-TEST-9999"], ["SN-TEST-0002"]]  # WHY: only one number again.
    assert result.is_complete is True  # WHY: the second pass cleared the pending number.


def test_saved_fault_991_reply_is_not_usable() -> None:
    """The saved 991 fault gives no result for the batch, and the code is listed."""
    reply = load_fixture("asset", "queryAssetsDetailsResponse_fault_991")  # WHY: the saved 991 fault.
    gateway = FakeGateway(bodies={"queryAssetsDetails": [reply]})  # WHY: one reply for the single batch.
    outcome = _asset_service(gateway).query_batch(["SN-TEST-0001"])  # WHY: one batch read.
    assert outcome.is_usable is False  # WHY: fault 991 gives no result.
    assert outcome.has_fault("991")  # WHY: the batch limit fault is listed.


def test_empty_reply_body_is_not_usable() -> None:
    """An empty body carries no result, so the list read is not usable."""
    body = JuniperTransportReply.parse_object(b"")  # WHY: an empty reply parses to no body.
    gateway = FakeGateway(bodies={"querysrlist": [body]})  # WHY: the empty body reaches the service.
    outcome = _case_service(gateway).list_requests()  # WHY: the real list read.
    assert body == {}  # WHY: the empty reply carries no fields.
    assert outcome.is_usable is False  # WHY: an empty body is not an answer.


def test_truncated_reply_text_gives_no_result() -> None:
    """A reply cut off in transit parses to an empty body, so the list read is not usable."""
    truncated = b'{"querySRListResponse": {"statusCode": "200", "cases": ['  # WHY: a reply cut off mid-array.
    with pytest.raises(json.JSONDecodeError):  # WHY: prove that the standard parser rejects the text.
        json.loads(truncated.decode("utf-8"))  # WHY: the text is malformed JSON.
    body = JuniperTransportReply.parse_object(truncated)  # WHY: the parser that the gateway uses for every reply.
    gateway = FakeGateway(bodies={"querysrlist": [body]})  # WHY: the parsed body reaches the service.
    outcome = _case_service(gateway).list_requests()  # WHY: the real list read.
    assert body == {}  # WHY: the cut-off text is not a JSON object.
    assert outcome.is_usable is False  # WHY: no result means no usable answer.
