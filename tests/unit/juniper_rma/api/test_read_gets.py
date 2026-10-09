"""Offline tests for the reference row builders and for the GET and envelope paths of the new Case and Asset reads."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import json  # WHY: the GET fixture reply is JSON bytes.

import pytest  # WHY: fixtures and the raised transport error.
import requests  # WHY: the transport type that the gateway wraps.

from src.operations.exporting.juniper_rma.api.gateway import (  # WHY: the real gateway.
    JuniperGatewayClient,
    JuniperTransportError,
)
from src.operations.exporting.juniper_rma.model.reference_rows import (  # WHY: row builders.
    BulkLinkRows,
    LovRows,
    SoftwareVersionRows,
)
from tests.unit.juniper_rma.fixtures import read_replies as replies  # WHY: synthetic replies in the live shape.
from tests.unit.juniper_rma.fixtures.fake_gateway import (  # WHY: the fakes for the transport and the services.
    ASSET_BASE_URL,
    CASE_BASE_URL,
    TEST_TOKEN,
    FakeClock,
    FakeGateway,
    FakeHttpSession,
    FakeResponse,
    build_session,
    json_bytes,
    make_settings,
)

RETRIEVED = "2026-09-07T10:00:00+00:00"  # WHY: one fixed retrieval time.
TOKEN_REPLY = FakeResponse(200, json_bytes({"access_token": TEST_TOKEN, "expires_in": 3600}))  # WHY: token exchange.


def _no_pause(seconds: float) -> None:
    """Accept the requested pause and return at once."""
    del seconds  # WHY: the fake clock does not wait, so the pause value is not used.


def _gateway(replies_after_token: list[FakeResponse | BaseException]) -> tuple[JuniperGatewayClient, FakeHttpSession]:
    """Return the real gateway over a fake HTTP session that replays the token and then the given replies."""
    http = FakeHttpSession([TOKEN_REPLY, *replies_after_token])  # WHY: the token comes before the API call.
    gateway = JuniperGatewayClient(make_settings(), session=http, clock=FakeClock(), sleeper=_no_pause)  # WHY.
    return gateway, http


def test_lov_rows_hold_every_scalar_value_with_its_full_path() -> None:
    """The list of values flattens to one row for each scalar, with the group, the path, and the type."""
    rows = LovRows.rows(replies.lov_reply(), RETRIEVED)  # WHY: every value of every group.
    paths = [row["lovPath"] for row in rows]  # WHY: the dotted and indexed paths.
    assert paths == [  # WHY: each scalar appears once, in reply order.
        "srStatus[0]",
        "srStatus[1]",
        "carrier[0].description",
        "carrier[0].code",
        "priority[0]",
        "priority[1]",
        "priority[2]",
    ]
    assert (rows[2]["lovGroup"], rows[2]["lovValue"], rows[2]["valueType"]) == ("carrier", "Example Carrier", "str")
    assert all(set(row) == set(LovRows.COLUMNS) for row in rows)  # WHY: the full column set on every row.


def test_software_rows_keep_each_release_and_an_empty_platform_once() -> None:
    """Each release is one row. A platform with no release keeps one row with an empty release."""
    rows = SoftwareVersionRows.rows(replies.eos_reply(), RETRIEVED)  # WHY: the flattened releases.
    pairs = [(row["platform"], row["versionRelease"]) for row in rows]  # WHY: the platform and release pairs.
    assert pairs == [("EX-PLATFORM", "1.0R1"), ("EX-PLATFORM", "1.0R2"), ("EX-EMPTY", "")]  # WHY: the expected rows.
    assert {row["productSeries"] for row in rows} == {"EXAMPLE SERIES"}  # WHY: the series name is on every row.


def test_bulk_links_mask_the_signature_and_keep_the_host_and_path() -> None:
    """A signed link keeps its scheme, host, and path. Its query, which holds the signature, is masked."""
    result = replies.bulk_reply()["assetsBulkDataResponse"]  # WHY: the wrapped bulk result.
    links = BulkLinkRows.links(result, RETRIEVED)  # WHY: one row for each link.
    assert links[0]["urlMasked"] == "https://files.example.invalid/snap/2026-09-04.json.gz?[masked]"  # WHY.
    assert "SECRET123" not in " ".join(links[0].values())  # WHY: the signature never reaches a row.
    assert set(links[0]) == set(BulkLinkRows.LINK_COLUMNS)  # WHY: the full column set.


def test_bulk_no_data_rows_carry_the_snapshot_date_and_the_message() -> None:
    """Each no-data date becomes one row with its snapshot date and the reason that Juniper gives."""
    result = replies.bulk_reply()["assetsBulkDataResponse"]  # WHY: the wrapped bulk result.
    no_data = BulkLinkRows.no_data(result, RETRIEVED)  # WHY: one row for each no-data object.
    assert (no_data[0]["snapshotDate"], no_data[0]["message"]) == ("2026-09-03", "noDataFound")  # WHY.
    assert set(no_data[0]) == set(BulkLinkRows.NO_DATA_COLUMNS)  # WHY: the full column set.


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://h.example.invalid/p", "https://h.example.invalid/p"),  # WHY: no query, nothing to mask.
        ("https://h.example.invalid/p?sig=1", "https://h.example.invalid/p?[masked]"),  # WHY: a query is masked.
        ("", ""),  # WHY: an empty link stays empty.
    ],
)
def test_mask_url_removes_only_the_query(raw: str, expected: str) -> None:
    """The mask keeps the scheme, host, and path, and replaces a query string with a fixed marker."""
    assert BulkLinkRows.mask_url(raw) == expected  # WHY: the rule for each shape.


def test_get_sends_the_parameter_and_no_body_with_the_bearer_token() -> None:
    """A GET carries its identifier as a query parameter and sends no JSON body, with the token header."""
    gateway, http = _gateway([FakeResponse(200, json_bytes(replies.lov_reply()))])  # WHY: one GET reply.
    reply = gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: one GET call.
    url, kwargs = http.calls[1]  # WHY: the call after the token exchange.
    assert url == f"{CASE_BASE_URL}/getlov"  # WHY: the checked path under the case base.
    assert kwargs["params"] == {"appid": "app-test-value"}  # WHY: the identifier is a query parameter.
    assert "json" not in kwargs  # WHY: a GET sends no envelope.
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_TOKEN}"  # WHY: the bearer token is sent.
    assert kwargs["allow_redirects"] is False  # WHY: redirects are refused.
    assert reply.http_status == 200  # WHY: the reply status is kept.


def test_get_retries_a_temporary_status_and_then_succeeds() -> None:
    """A 503 reply is retried, and a later 200 reply is returned."""
    gateway, http = _gateway([FakeResponse(503), FakeResponse(200, json_bytes(replies.lov_reply()))])  # WHY.
    reply = gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: one GET with a retry.
    assert reply.http_status == 200  # WHY: the second attempt succeeded.
    assert reply.attempts == 2  # WHY: the retry is counted.
    assert len(http.calls) == 3  # WHY: the token, the failed attempt, and the retry.


def test_get_refreshes_the_token_once_after_a_401_reply() -> None:
    """A 401 reply triggers one token refresh, and the retry uses the new token."""
    gateway, http = _gateway([FakeResponse(401), TOKEN_REPLY, FakeResponse(200, json_bytes(replies.lov_reply()))])
    reply = gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: one GET.
    assert reply.http_status == 200  # WHY: the retry succeeded with the new token.
    assert len(http.calls) == 4  # WHY: token, 401 call, token refresh, and the retry.


def test_get_refuses_a_redirect() -> None:
    """A redirect reply is never followed. The call raises a transport error that names the status."""
    gateway, _http = _gateway([FakeResponse(302)])  # WHY: one redirect reply.
    with pytest.raises(JuniperTransportError, match="302"):  # WHY: the status is named, the address is not.
        gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: the refused call.


def test_get_gives_up_after_the_retries_on_connection_errors() -> None:
    """Connection errors retry, and the final error names the number of attempts and the cause."""
    gateway, _http = _gateway([requests.ConnectionError("down") for _ in range(3)])  # WHY: every attempt fails.
    with pytest.raises(JuniperTransportError, match="failed after 3 attempts"):  # WHY: the bounded retry.
        gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: the failing call.


def test_lov_and_software_calls_use_the_lowercase_appid_parameter() -> None:
    """The live service needs appid in lowercase for both GET reads, so the services send that name."""
    gateway = FakeGateway(bodies={"getlov": [replies.lov_reply()], "getSoftwareEosLov": [replies.eos_reply()]})
    session = build_session(gateway, make_settings())  # WHY: the real services over the fake gateway.
    lov = session.case.get_lov("app-test-value")  # WHY: one list of values.
    eos = session.case.get_software_eos_lov("app-test-value")  # WHY: one software list.
    assert gateway.calls_for("getlov")[0].query == {"appid": "app-test-value"}  # WHY: the spelling that works.
    assert gateway.calls_for("getSoftwareEosLov")[0].query == {"appid": "app-test-value"}  # WHY: the same spelling.
    assert (lov.is_usable, eos.is_usable) == (True, True)  # WHY: a plain HTTP 200 is usable without a body status.


@pytest.mark.parametrize("status_code", [400, 404])  # WHY: a client error other than 401 is a final answer.
def test_get_returns_a_client_error_reply_without_a_retry(status_code: int) -> None:
    """A 400 or 404 reply comes back at once, and the gateway does not retry a client error."""
    gateway, http = _gateway([FakeResponse(status_code)])  # WHY: one client error reply.
    reply = gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: one GET call.
    assert reply.http_status == status_code  # WHY: the status is kept for the caller.
    assert reply.attempts == 1  # WHY: a client error is not retried.
    assert len(http.calls) == 2  # WHY: the token exchange and the one call.


@pytest.mark.parametrize("status_code", [502, 503])  # WHY: these statuses are temporary (R-11).
def test_get_gives_up_after_the_retries_on_a_temporary_server_error(status_code: int) -> None:
    """A temporary server error that never clears fails after three attempts, and the error names the status."""
    gateway, http = _gateway([FakeResponse(status_code) for _ in range(3)])  # WHY: every attempt fails.
    with pytest.raises(JuniperTransportError, match=f"failed after 3 attempts \\(http_{status_code}\\)"):  # WHY.
        gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: the failing call.
    assert len(http.calls) == 4  # WHY: the token exchange and the three attempts.


def test_get_gives_up_after_the_retries_on_a_timeout() -> None:
    """A timeout is retried, and the final error names the three attempts and the timeout."""
    gateway, _http = _gateway([requests.Timeout("slow") for _ in range(3)])  # WHY: every attempt times out.
    with pytest.raises(JuniperTransportError, match=r"failed after 3 attempts \(Timeout\)"):  # WHY: the retry bound.
        gateway.get("getlov", CASE_BASE_URL, "getlov", {"appid": "app-test-value"})  # WHY: the failing call.


def test_note_envelope_names_the_note_inside_the_wrapper() -> None:
    """The note envelope carries the note identifier inside the querySRNoteRequest wrapper."""
    gateway = FakeGateway(bodies={"querysrnotedetails": [replies.note_reply(replies.NOTE_ID_ONE)]})
    session = build_session(gateway, make_settings())  # WHY: the real case service.
    outcome = session.case.get_note(replies.NOTE_ID_ONE, replies.SR_NUMBER, "")  # WHY: one note read.
    envelope = gateway.calls_for("querysrnotedetails")[0].body["querySRNoteRequest"]  # WHY: the sent envelope.
    assert envelope["noteId"] == replies.NOTE_ID_ONE  # WHY: the identifier is in the wrapper.
    assert envelope["caseInformation"]["serviceRequestNumber"] == replies.SR_NUMBER  # WHY: the request key.
    assert set(envelope["contact"]) == {"accountID", "contactEmail"}  # WHY: the contact block for the account.
    assert outcome.is_usable is True  # WHY: a 200 note reply is usable.


def test_bulk_envelope_carries_the_snapshot_window_and_unwraps_the_reply() -> None:
    """The bulk envelope carries the two dates, and the reply wrapper is unwrapped to its data."""
    gateway = FakeGateway(bodies={"queryAssetsBulkData": [replies.bulk_reply()]})
    session = build_session(gateway, make_settings())  # WHY: the real asset service.
    outcome = session.asset.query_bulk("2026-09-01", "2026-09-04")  # WHY: one window.
    envelope = gateway.calls_for("queryAssetsBulkData")[0].body["assetsBulkDataRequest"]  # WHY: the envelope.
    assert (envelope["snapshotFromDate"], envelope["snapshotToDate"]) == ("2026-09-01", "2026-09-04")  # WHY.
    assert gateway.calls_for("queryAssetsBulkData")[0].base_url == ASSET_BASE_URL  # WHY: the asset base address.
    assert outcome.is_usable is True  # WHY: the body status is 200.
    assert "data" in outcome.result  # WHY: the data object stays in the result for the rows.


def test_bulk_gateway_401_is_explained_as_an_entitlement_problem() -> None:
    """A 401 from the asset gateway is not usable, and the explanation names the entitlement."""
    gateway = FakeGateway(bodies={"queryAssetsBulkData": [{}]}, statuses={"queryAssetsBulkData": [401]})
    session = build_session(gateway, make_settings())  # WHY: the real asset service over the fake gateway.
    outcome = session.asset.query_bulk("2026-09-01", "2026-09-04")  # WHY: the rejected call.
    assert outcome.is_usable is False  # WHY: a rejection is not a result.
    assert "HTTP 401" in outcome.fault_messages[0]  # WHY: the status is named.
    assert "enabled for this API" in outcome.fault_messages[0]  # WHY: the next step is named.


def test_plain_reply_with_a_non_200_status_and_no_body_is_a_rejection() -> None:
    """A GET reply that is not HTTP 200 and has no body status is a rejection, not an empty success."""
    gateway = FakeGateway(bodies={"getlov": [{}]}, statuses={"getlov": [500]})
    session = build_session(gateway, make_settings())  # WHY: the real case service.
    outcome = session.case.get_lov("app-test-value")  # WHY: the rejected GET.
    assert outcome.is_usable is False  # WHY: a 500 with no body is not usable.
    assert outcome.status_code == "500"  # WHY: the status is kept for the explanation.


def test_json_bytes_round_trip_is_the_fixture_shape() -> None:
    """The fixture helper encodes the reply as JSON bytes that the gateway can parse."""
    assert json.loads(json_bytes(replies.lov_reply()).decode("utf-8")) == replies.lov_reply()  # WHY: lossless.
