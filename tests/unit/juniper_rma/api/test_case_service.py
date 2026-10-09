"""Tests for the Case API service: the access window, the list window, the lookup keys, and the RMA envelope."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from datetime import date, timedelta  # WHY: the window arithmetic.

import pytest  # WHY: raised-error checks.

from src.operations.exporting.juniper_rma.api.case_service import JuniperCaseService  # WHY: the service under test.
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: helpers.
    RequestMessageBuilder,
    ResponseStatusReader,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import CASE_BASE_URL, FakeGateway, make_settings  # WHY: fixtures.

LIST_OK = {"querySRListResponse": {"statusCode": "200", "cases": []}}  # WHY: a usable empty list.


def _service(gateway: FakeGateway) -> JuniperCaseService:
    """Return the real Case service wired to the fake gateway."""
    settings = make_settings()  # WHY: synthetic settings.
    return JuniperCaseService(gateway, RequestMessageBuilder(settings), ResponseStatusReader(), CASE_BASE_URL)  # WHY.


def test_access_check_sends_a_one_day_window() -> None:
    """The access check reads a window of exactly one day."""
    gateway = FakeGateway(bodies={"querysrlist": [LIST_OK]})  # WHY: one usable reply.
    outcome = _service(gateway).check_access()  # WHY: the access check.
    body = gateway.calls[0].body["querySRListRequest"]  # WHY: the list envelope that was built.
    span = date.fromisoformat(body["caseInformation"]["toDate"]) - date.fromisoformat(  # WHY: window length.
        body["caseInformation"]["fromDate"]
    )
    assert span == timedelta(days=1)  # WHY: the access window is one day.
    assert outcome.is_usable is True  # WHY: the usable reply passes the check.


def test_default_list_window_covers_ninety_days() -> None:
    """The list operation covers the last 90 days by default (R-06)."""
    gateway = FakeGateway(bodies={"querysrlist": [LIST_OK]})  # WHY: one usable reply.
    _service(gateway).list_requests()  # WHY: the default window.
    info = gateway.calls[0].body["querySRListRequest"]["caseInformation"]  # WHY: the window that was sent.
    span = date.fromisoformat(info["toDate"]) - date.fromisoformat(info["fromDate"])  # WHY: window length.
    assert span == timedelta(days=90)  # WHY: the documented window.


def test_gateway_rejection_is_named_and_not_read_as_a_missing_status() -> None:
    """An HTTP 401 from the gateway is named as a rejection, not as a missing body status."""
    gateway = FakeGateway(statuses={"querysrlist": [401]})  # WHY: the gateway rejects the application.
    outcome = _service(gateway).list_requests()  # WHY: one list read through the rejection.
    assert outcome.is_usable is False  # WHY: a rejection is not a usable reply.
    assert "HTTP 401" in ResponseStatusReader.explain(outcome)  # WHY: the operator sees the status and the cause.


def test_detail_by_case_number_leaves_the_request_number_empty() -> None:
    """A lookup by case number sends an empty request number, not a missing key."""
    gateway = FakeGateway(bodies={"querysrdetails": [{"querySRResponse": {"statusCode": "200"}}]})  # WHY.
    _service(gateway).get_request(case_number="CASE-42")  # WHY: a lookup by case number.
    info = gateway.calls[0].body["querySRRequest"]["caseInformation"]  # WHY: the detail block.
    assert info["customerCaseNumber"] == "CASE-42"  # WHY: the lookup key.
    assert info["serviceRequestNumber"] == ""  # WHY: the unused key stays present and empty.


def test_detail_without_any_key_is_a_programming_error() -> None:
    """The detail operation refuses to run without a request number or a case number (fault 956)."""
    with pytest.raises(ValueError, match="required"):  # WHY: the rule is enforced before any call.
        _service(FakeGateway()).get_request()  # WHY: neither key is given.


def test_rma_envelope_carries_the_rma_number_and_both_parents() -> None:
    """The RMA read sends the RMA number with the parent request and case numbers."""
    gateway = FakeGateway(bodies={"queryrmadetails": [{"queryRMAResponse": {"statusCode": "200"}}]})  # WHY.
    _service(gateway).get_rma("RMA-7", "REQ-7", "CASE-7")  # WHY: one RMA read.
    body = gateway.calls[0].body["queryRMARequest"]  # WHY: the wrapper from the contract.
    assert body["rmaNumber"] == "RMA-7"  # WHY: the RMA to read.
    assert body["caseInformation"]["serviceRequestNumber"] == "REQ-7"  # WHY: the parent request.
    assert body["caseInformation"]["customerCaseNumber"] == "CASE-7"  # WHY: the parent case.


def test_fault_reply_is_not_usable_and_lists_its_code() -> None:
    """A status-400 reply is not usable, and its fault code is available to the caller."""
    fault = {"statusCode": "400", "fault": [{"errorCode": "756", "errorMessage": "not linked"}]}  # WHY.
    gateway = FakeGateway(bodies={"querysrdetails": [{"querySRResponse": fault}]})  # WHY: a fault reply.
    outcome = _service(gateway).get_request(case_number="CASE-99")  # WHY: the lookup.
    assert not outcome.is_usable  # WHY: a fault gives no result.
    assert outcome.has_fault("756")  # WHY: the caller can map the code to "not found" or "unmatched".


@pytest.mark.parametrize(
    ("code", "meaning"),
    [
        ("707", "appId and customerSourceID combination is not valid"),  # WHY: the application and source pair.
        ("735", "appId is not valid"),  # WHY: the application identifier.
        ("932", "appId and userId combination is not valid"),  # WHY: the application and user pair.
    ],
)
def test_access_faults_map_to_their_plain_meaning(code: str, meaning: str) -> None:
    """Each access fault from the Case API maps to its plain-text meaning for the operator."""
    fault = {"statusCode": "400", "fault": [{"errorCode": code, "errorMessage": "raw text"}]}  # WHY: a fault reply.
    gateway = FakeGateway(bodies={"querysrlist": [{"querySRListResponse": fault}]})  # WHY: list reply.
    outcome = _service(gateway).check_access()  # WHY: the access check reads the fault.
    assert outcome.has_fault(code)  # WHY: the code is listed on the reply.
    assert meaning in ResponseStatusReader.explain(outcome)  # WHY: the operator sees the plain-text meaning.
