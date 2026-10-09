"""Tests for the Asset API service: batching, the not-processed passes, faults, and partial results."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import pytest  # WHY: the fixtures for the test doubles.

from src.operations.exporting.juniper_rma.api.asset_service import JuniperAssetService  # WHY: the service under test.
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: the transport error to replay.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: helpers.
    RequestMessageBuilder,
    ResponseStatusReader,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import ASSET_BASE_URL, FakeGateway, make_settings  # WHY: fixtures.


def _service(gateway: FakeGateway) -> JuniperAssetService:
    """Return the real Asset service wired to the fake gateway."""
    return JuniperAssetService(  # WHY: the real service, fed by the double.
        gateway,
        RequestMessageBuilder(make_settings()),
        ResponseStatusReader(),
        ASSET_BASE_URL,
    )


def _reply(assets: list[dict[str, str]], not_processed: list[str] | None = None, data: bool = False) -> dict:
    """Return an asset reply. The data flag nests the result the way the export example does (O-6)."""
    payload = {  # WHY: the result keys of the Asset API.
        "statusCode": "200",
        "assets": assets,
        "invalidSerialNumbersOrSSRNs": [],
        "notProcessedSerialNumbersOrSSRNs": [
            {"serialNumberOrSSRN": number, "message": "retry"} for number in (not_processed or [])
        ],
    }
    if data:  # WHY: the variant where the results sit under data.
        return {"queryAssetsDetailsResponse": {"statusCode": "200", "data": payload}}  # WHY: nested shape.
    return {"queryAssetsDetailsResponse": payload}  # WHY: the top-level shape.


def test_three_hundred_fifty_serials_go_in_two_batches() -> None:
    """A list of 350 numbers is sent as one batch of 300 and one batch of 50."""
    serials = [f"SN{number:04d}" for number in range(350)]  # WHY: 350 synthetic serials.
    gateway = FakeGateway(bodies={"queryAssetsDetails": [_reply([]), _reply([])]})  # WHY: two replies.
    result = _service(gateway).query_all(serials)  # WHY: the full batched read.
    sizes = [  # WHY: the batch sizes, in call order.
        len(call.body["queryAssetsDetailsRequest"]["serialNumbersOrSSRNs"]) for call in gateway.calls
    ]
    assert sizes == [300, 50]  # WHY: the batch limit of 300 (fault 991).
    assert result.is_complete is True  # WHY: every number received an answer.


def test_not_processed_numbers_are_sent_again_in_the_next_pass() -> None:
    """A not-processed number gets one more request, and its reply is merged into the result."""
    gateway = FakeGateway(  # WHY: pass one leaves SN2 pending, and pass two answers it.
        bodies={
            "queryAssetsDetails": [
                _reply([{"serialNumber": "SN1"}], not_processed=["SN2"]),  # WHY: pass one leaves SN2 pending.
                _reply([{"serialNumber": "SN2"}]),  # WHY: pass two answers SN2.
            ]
        }
    )
    result = _service(gateway).query_all(["SN1", "SN2"])  # WHY: two numbers.
    assert [asset["serialNumber"] for asset in result.assets] == ["SN1", "SN2"]  # WHY: both answered.
    assert len(gateway.calls) == 2  # WHY: exactly one extra request.
    assert result.is_complete is True  # WHY: nothing is left pending.


def test_pending_numbers_stop_after_three_passes() -> None:
    """A number that never gets an answer is listed as not processed after three passes."""
    replies = [_reply([], not_processed=["SN9"]) for _ in range(3)]  # WHY: SN9 is never answered.
    gateway = FakeGateway(bodies={"queryAssetsDetails": replies})  # WHY: three identical replies.
    result = _service(gateway).query_all(["SN9"])  # WHY: one number.
    assert len(gateway.calls) == 3  # WHY: the three-pass limit (contract).
    assert result.not_processed == ("SN9",)  # WHY: the number is listed for the operator.
    assert not result.is_complete  # WHY: the run is incomplete.


def test_faulted_batch_is_recorded_and_not_retried() -> None:
    """A batch that returns a fault gives no assets, is recorded, and is not sent again."""
    fault = {  # WHY: a batch fault reply.
        "queryAssetsDetailsResponse": {"statusCode": "400", "fault": [{"errorCode": "992", "errorMessage": "bad"}]}
    }
    gateway = FakeGateway(bodies={"queryAssetsDetails": [fault]})  # WHY: one faulted reply.
    result = _service(gateway).query_all(["BAD1"])  # WHY: one number in the faulted batch.
    assert result.failed_serials == ["BAD1"]  # WHY: the numbers are recorded as failed.
    assert len(gateway.calls) == 1  # WHY: a fault repeats on retry, so there is no second call.
    assert any("992" in problem for problem in result.problems)  # WHY: the fault meaning is kept.


def test_transport_failure_keeps_the_partial_results() -> None:
    """When the second batch fails in transport, the first batch's assets remain in the result."""
    serials = [f"SN{number:04d}" for number in range(301)]  # WHY: two batches (300 and 1).
    gateway = FakeGateway(  # WHY: the first batch answers, and the second batch fails in transport.
        bodies={"queryAssetsDetails": [_reply([{"serialNumber": "SN0000"}])]},  # WHY: the first batch answers.
        failures={"queryAssetsDetails": [JuniperTransportError("connection lost")]},  # WHY: the second fails.
    )
    result = _service(gateway).query_all(serials)  # WHY: the batched read with one failure.
    assert [asset["serialNumber"] for asset in result.assets] == ["SN0000"]  # WHY: partial results kept.
    assert not result.is_complete  # WHY: the run is incomplete.
    assert any("connection lost" in problem for problem in result.problems)  # WHY: the reason is recorded.


@pytest.mark.parametrize("data_wrapped", [True, False])
def test_both_response_shapes_are_accepted(data_wrapped: bool) -> None:
    """The results are read from the nested data object or from the top level (O-6)."""
    gateway = FakeGateway(  # WHY: one reply in the chosen shape.
        bodies={"queryAssetsDetails": [_reply([{"serialNumber": "SN7"}], data=data_wrapped)]}
    )
    result = _service(gateway).query_all(["SN7"])  # WHY: one number, two possible shapes.
    assert [asset["serialNumber"] for asset in result.assets] == ["SN7"]  # WHY: the asset is found either way.


def test_gateway_rejection_is_named_and_not_retried() -> None:
    """An HTTP 401 from the gateway is named as an access problem, and the batch is not sent again."""
    gateway = FakeGateway(statuses={"queryAssetsDetails": [401]})  # WHY: the gateway rejects the application.
    result = _service(gateway).query_all(["SN1"])  # WHY: one number in one batch.
    assert result.failed_serials == ["SN1"]  # WHY: the number is recorded as failed.
    assert len(gateway.calls) == 1  # WHY: the rejection repeats on a retry, so no second call is sent.
    assert any("HTTP 401" in problem for problem in result.problems)  # WHY: the operator sees the status.
    assert any("Ask Juniper" in problem for problem in result.problems)  # WHY: the next step is named.
