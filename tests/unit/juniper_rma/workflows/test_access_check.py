"""Tests for menu 301: the access check, the menu guard, and one opt-in read-only live check."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import logging  # WHY: caplog levels for the action log checks.
import os  # WHY: read the opt-in and the environment for the live check.
import re  # WHY: find e-mail addresses in free text before a live line is logged.
import sys  # WHY: the menu guard reads the command line.
from datetime import UTC, date, datetime, timedelta  # WHY: the last calendar month for the live list.
from pathlib import Path  # WHY: the .env path check.

import pytest  # WHY: fixtures, skip markers, and the live marker.
import requests  # WHY: the connection errors that the real gateway retries.
from dotenv import dotenv_values  # WHY: read the local .env file for the live check, without printing values.

from src.operations.exporting.juniper_rma.api.gateway import JuniperGatewayClient  # WHY: the real gateway under test.
from src.operations.exporting.juniper_rma.api.messages import (
    ResponseStatusReader,  # WHY: the plain-text reason for a failed reply.
)
from src.operations.exporting.juniper_rma.model.export_rows import (
    PersonalDataMasker,  # WHY: ASCII-only text for the live display.
)
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: parses cases, details, and items.
    RmaItem,
    ServiceRequest,
)
from src.operations.exporting.juniper_rma.settings import (  # WHY: types.
    JuniperServiceSession,
    JuniperSettings,
    JuniperSettingsLoader,
)
from src.operations.exporting.juniper_rma.workflows.access_check import (
    AccessCheckWorkflow,  # WHY: the workflow under test.
)
from tests.unit.juniper_rma.fixtures.fake_gateway import (  # WHY: the fakes for the gateway and the workflow.
    TEST_TOKEN,
    FakeClock,
    FakeGateway,
    FakeHttpSession,
    FakeResponse,
    build_session,
    json_bytes,
    make_settings,
)

LIST_OK = {"querySRListResponse": {"statusCode": "200", "cases": []}}  # WHY: a usable reply.
FAULT_735 = {  # WHY: a fault reply for the wrong application identifier.
    "querySRListResponse": {"statusCode": "400", "fault": [{"errorCode": "735", "errorMessage": "bad"}]}
}


TOKEN_REPLY = FakeResponse(  # WHY: the token exchange that every run makes before the API call.
    200, json_bytes({"access_token": TEST_TOKEN, "token_type": "Bearer", "expires_in": 3600})
)


def _no_pause(seconds: float) -> None:
    """Accept the requested pause and return at once, so each retry runs without a wait."""
    del seconds  # WHY: the pause value is not needed, because the fake clock does not wait.


def _real_gateway(replies: list[FakeResponse | BaseException]) -> JuniperGatewayClient:
    """Return the real gateway over a fake HTTP session that replays the token and then the replies."""
    http = FakeHttpSession([TOKEN_REPLY, *replies])  # WHY: the token exchange comes before the API call.
    return JuniperGatewayClient(  # WHY: the real transport, with no network and no waits.
        make_settings(),
        session=http,
        clock=FakeClock(),
        sleeper=_no_pause,
    )


def test_access_check_passes_when_juniper_accepts_the_request(caplog: pytest.LogCaptureFixture) -> None:
    """A usable reply to the one-day list request is a pass."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    gateway = FakeGateway(bodies={"querysrlist": [LIST_OK]})  # WHY: one usable reply.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is True  # WHY: the pass.
    assert "PASS" in caplog.text  # WHY: the operator sees the result.


def test_access_check_fails_with_the_fault_meaning_and_the_next_step(caplog: pytest.LogCaptureFixture) -> None:
    """Fault 735 is a fail, and the message names the meaning and the setting to check."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    gateway = FakeGateway(bodies={"querysrlist": [FAULT_735]})  # WHY: the fault reply.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is False  # WHY: the fail.
    assert "appId is not valid" in caplog.text  # WHY: the meaning.
    assert "JUNIPER_APP_ID" in caplog.text  # WHY: the next step.


def test_menu_refuses_live_calls_in_test_mode(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Under --test with no opt-in, the menu returns no session and names the opt-in."""
    caplog.set_level(logging.WARNING)  # WHY: the refusal is a warning.
    monkeypatch.setattr(sys, "argv", ["MistHelper.py", "--test"])  # WHY: the automated mode.
    monkeypatch.delenv("JUNIPER_LIVE_TESTS", raising=False)  # WHY: no opt-in.
    assert JuniperServiceSession.open_for_menu() is None  # WHY: no session in a refused run.
    assert "JUNIPER_LIVE_TESTS=1" in caplog.text  # WHY: the operator learns how to opt in.


def test_menu_names_the_missing_settings_and_stops(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With no Juniper settings in the environment, the menu stops and lists the names."""
    caplog.set_level(logging.ERROR)  # WHY: the missing settings are an error.
    monkeypatch.setattr(sys, "argv", ["MistHelper.py"])  # WHY: an operator run, so the guard does not refuse.
    for name in list(os.environ):  # WHY: clear every Juniper name for this test only.
        if name.startswith("JUNIPER_"):  # WHY: only the Juniper names.
            monkeypatch.delenv(name, raising=False)  # WHY: restored after the test.
    assert JuniperServiceSession.open_for_menu() is None  # WHY: no session without settings.
    assert "JUNIPER_APP_ID" in caplog.text  # WHY: the operator sees the missing name.


def test_access_check_reports_a_connection_error_as_a_failure(caplog: pytest.LogCaptureFixture) -> None:
    """A connection error that outlasts the retries is a fail, and the log names the cause."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    gateway = _real_gateway([requests.ConnectionError("network down") for _ in range(3)])  # WHY: all attempts fail.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is False  # WHY: the fail.
    assert "failed after 3 attempts (ConnectionError)" in caplog.text  # WHY: the operator sees the retries ran out.


def test_access_check_reports_a_connection_timeout_as_a_failure(caplog: pytest.LogCaptureFixture) -> None:
    """A connection timeout that outlasts the retries is a fail, and the log names the timeout."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    gateway = _real_gateway([requests.Timeout("read timed out") for _ in range(3)])  # WHY: all attempts time out.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is False  # WHY: the fail.
    assert "failed after 3 attempts (Timeout)" in caplog.text  # WHY: the operator sees the timeout.


def test_access_check_reports_an_http_4xx_reply_as_a_failure(caplog: pytest.LogCaptureFixture) -> None:
    """A 400 reply is an HTTP 4xx failure that is not retried, and the log names the status."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    fault = {"errorCode": "906", "errorMessage": "customerSourceID is missing"}  # WHY: the client-error fault.
    body = json_bytes({"querySRListResponse": {"statusCode": "400", "fault": [fault]}})  # WHY: the reply body.
    gateway = _real_gateway([FakeResponse(status_code=400, body=body)])  # WHY: one reply, not retried.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is False  # WHY: the fail.
    assert "customerSourceID is missing" in caplog.text  # WHY: the operator sees the meaning of the fault.
    assert "JUNIPER_CUSTOMER_SOURCE_ID" in caplog.text  # WHY: the next step names the setting.
    assert "http_status=400" in caplog.text  # WHY: the log records the HTTP status of the reply.


def test_access_check_reports_an_http_5xx_after_retries_as_a_failure(caplog: pytest.LogCaptureFixture) -> None:
    """A 503 that repeats through every retry is an HTTP 5xx failure, and the log names the status."""
    caplog.set_level(logging.INFO)  # WHY: capture the result line.
    gateway = _real_gateway([FakeResponse(status_code=503) for _ in range(3)])  # WHY: every attempt gets a 503.
    assert AccessCheckWorkflow(build_session(gateway, make_settings())).execute() is False  # WHY: the fail.
    assert "failed after 3 attempts (http_503)" in caplog.text  # WHY: the operator sees the server status.


def _load_live_settings() -> JuniperSettings:
    """Merge the local .env file and the environment, then validate them the same way the menu does."""
    env_file = Path(os.environ.get("MISTHELPER_ENV_FILE", ".env"))  # WHY: the local file may sit elsewhere.
    values: dict[str, str] = {}  # WHY: merge the file and the environment, without printing either.
    if env_file.is_file():  # WHY: the file is optional when the environment holds the values.
        values.update(  # WHY: merge the file values, skipping empty ones.
            {name: value for name, value in dotenv_values(env_file).items() if value is not None}
        )
    values.update({name: value for name, value in os.environ.items() if name.startswith("JUNIPER_")})  # WHY: env wins.
    return JuniperSettingsLoader(values).load()  # WHY: the same checks as the menu.


def _last_calendar_month(today: date) -> tuple[date, date]:
    """Return the first and the last day of the calendar month before the given day."""
    last_day = today.replace(day=1) - timedelta(days=1)  # WHY: the day before this month starts ends last month.
    return last_day.replace(day=1), last_day  # WHY: the first and the last day of that month.


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the one read-only live access check.",
)
def test_live_access_check_is_read_only() -> None:
    """Send one one-day list request to Juniper with the local settings. No write operation is used."""
    settings = _load_live_settings()  # WHY: the same checks as the menu.
    assert AccessCheckWorkflow(JuniperServiceSession(settings)).execute() is True  # WHY: one read, then the verdict.


def _parse_case_rows(rows: object) -> list[ServiceRequest]:
    """Return one parsed request for each dictionary row. A value that is not a list gives no requests."""
    if not isinstance(rows, list):  # WHY: a missing or wrong-shaped case list reads as no cases.
        return []  # WHY: nothing to parse.
    return [ServiceRequest.from_list_row(row) for row in rows if isinstance(row, dict)]  # WHY: skip non-object rows.


def _live_session() -> JuniperServiceSession:
    """Return a live session built from the local settings, with the same checks as the menu."""
    return JuniperServiceSession(_load_live_settings())  # WHY: one session for one read-only check.


def _live_cases_last_month() -> list[ServiceRequest]:
    """Read the cases of the last calendar month with one list call and return the parsed requests."""
    from_day, to_day = _last_calendar_month(datetime.now(UTC).date())  # WHY: last calendar month, in UTC.
    logging.getLogger(__name__).info("Reading the case list %s to %s", from_day, to_day)  # WHY: action log.
    outcome = _live_session().case.list_requests(from_day=from_day, to_day=to_day)  # WHY: one read-only call.
    assert outcome.is_usable is True, ResponseStatusReader.explain(outcome)  # WHY: the reason names the fault.
    cases = _parse_case_rows(outcome.result.get("cases"))  # WHY: parsed records for the display and next reads.
    logging.getLogger(__name__).debug("Parsed %d case record(s)", len(cases))  # WHY: count only, never content.
    return cases  # WHY: the caller shows or reuses the records.


EMAIL_TEXT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")  # WHY: find e-mail addresses.


def _mask_emails(text: str) -> str:
    """Replace each e-mail address in the text with the masked form from PersonalDataMasker."""
    return EMAIL_TEXT.sub(lambda match: PersonalDataMasker.email(match.group(0)), text)  # WHY: R-14 masks it.


def _case_line(request: ServiceRequest) -> str:
    """Return one ASCII line that summarizes a case. The line holds no contact detail."""
    synopsis = PersonalDataMasker.ascii_text(_mask_emails(request.synopsis))[:60]  # WHY: mask, ASCII, then shorten.
    columns = (  # WHY: a fixed column order makes each run easy to compare.
        request.request_number,
        request.case_number,
        request.status,
        request.priority,
        request.product_id,
        request.serial_number,
        request.last_modified,
        synopsis,
    )
    return PersonalDataMasker.ascii_text(" | ".join(columns))  # WHY: one ASCII line for the console and the log.


def _distinct_serials(cases: list[ServiceRequest]) -> list[str]:
    """Return the distinct serial numbers in the order that the case list gives them."""
    seen: dict[str, None] = {}  # WHY: a dictionary keeps the first-seen order and drops repeats.
    for case in cases:  # WHY: one pass over the parsed cases.
        if case.serial_number:  # WHY: an empty serial cannot be read.
            seen.setdefault(case.serial_number, None)  # WHY: keep the first occurrence only.
    return list(seen)  # WHY: the distinct serials in order.


def _asset_line(asset: dict[str, object]) -> str:
    """Return one ASCII line that summarizes an asset record."""
    columns = (  # WHY: the fields that identify an asset and its support state.
        str(asset.get("serialNumber", "")),
        str(asset.get("assetStatus", "")),
        str(asset.get("productSKU", "")),
        str(asset.get("productSKUEosDate", "")),
        str(asset.get("serviceEligible", "")),
    )
    return PersonalDataMasker.ascii_text(" | ".join(columns))  # WHY: ASCII only for the console and the log.


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the one read-only live case list for last month.",
)
def test_live_case_list_last_month_is_read_only(caplog: pytest.LogCaptureFixture) -> None:
    """List the cases of the last calendar month and log one masked line for each. No write is used."""
    caplog.set_level(logging.INFO)  # WHY: each case line must reach the live log.
    cases = _live_cases_last_month()  # WHY: one list call, parsed into requests.
    logging.getLogger(__name__).info("Live case list: %d case(s) in the last calendar month", len(cases))  # WHY: count.
    assert all(case.request_number for case in cases), "A case row has no request number"  # WHY: each row keys one.
    for case in cases:  # WHY: one masked line for each case.
        logging.getLogger(__name__).info("Live case: %s", _case_line(case))  # WHY: the operator sees the case.


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the one read-only live case detail read.",
)
def test_live_case_detail_is_read_only(caplog: pytest.LogCaptureFixture) -> None:
    """Read the detail of the first numbered case of the last calendar month. No write is used."""
    caplog.set_level(logging.INFO)  # WHY: the detail line must reach the live log.
    numbered = [case for case in _live_cases_last_month() if case.request_number]  # WHY: detail needs a number.
    if not numbered:  # WHY: an empty month cannot test the detail call.
        pytest.skip("No case with a request number in the last calendar month")  # WHY: the skip names the reason.
    first = numbered[0]  # WHY: one detail read keeps the live call count low.
    outcome = _live_session().case.get_request(request_number=first.request_number)  # WHY: one read-only call.
    assert outcome.is_usable is True, ResponseStatusReader.explain(outcome)  # WHY: the reason names the fault.
    detail = ServiceRequest.from_detail(outcome.result)  # WHY: the parsed detail, with the RMA numbers.
    logging.getLogger(__name__).info("Live case detail: %s", _case_line(detail))  # WHY: the masked summary.
    logging.getLogger(__name__).info("Live case detail RMA numbers: %d", len(detail.rma_numbers))  # WHY: count.


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the one read-only live asset read.",
)
def test_live_asset_read_is_read_only(caplog: pytest.LogCaptureFixture) -> None:
    """Read the asset details of up to five serial numbers from the last calendar month. No write is used."""
    caplog.set_level(logging.INFO)  # WHY: each asset line must reach the live log.
    serials = _distinct_serials(_live_cases_last_month())[:5]  # WHY: five serials keep the live call small.
    if not serials:  # WHY: an empty month cannot test the asset call.
        pytest.skip("No serial number in the last calendar month")  # WHY: the skip names the reason.
    result = _live_session().asset.query_all(serials)  # WHY: the product path, one batch for these serials.
    summary = (  # WHY: name each gap in the failure message.
        f"problems={result.problems} failed={len(result.failed_serials)} " f"not_processed={len(result.not_processed)}"
    )
    assert result.is_complete is True, summary  # WHY: the message names the gap when the read is incomplete.
    logging.getLogger(__name__).info(  # WHY: the operator sees the counts for this read.
        "Live asset read: %d record(s) for %d serial(s), %d not found",
        len(result.assets),
        len(serials),
        len(result.not_found),
    )
    for asset in result.assets:  # WHY: one masked line for each asset record.
        logging.getLogger(__name__).info("Live asset: %s", _asset_line(asset))  # WHY: the operator sees the asset.


def _rma_item_line(item: RmaItem) -> str:
    """Return one ASCII line that summarizes an RMA item. Personal fields never appear."""
    columns = (  # WHY: business fields only; the contact and the telephone fields stay out of the line.
        item.rma_number,
        item.item_type,
        item.item_number,
        item.product_id,
        item.serial_number,
        item.status,
        item.tracking_number,
    )
    return PersonalDataMasker.ascii_text(" | ".join(columns))  # WHY: ASCII only for the console and the log.


def _detail_with_rma(cases: list[ServiceRequest], attempts: int) -> ServiceRequest | None:
    """Return the first case detail that lists an RMA. Cases with a serial number are read first."""
    numbered = (case for case in cases if case.request_number)  # WHY: only cases with a request number can be read.
    ordered = sorted(numbered, key=lambda case: not case.serial_number)  # WHY: cases with a serial come first.
    session = _live_session()  # WHY: one session for the bounded detail reads.
    for case in ordered[:attempts]:  # WHY: a fixed upper bound on live reads.
        outcome = session.case.get_request(request_number=case.request_number)  # WHY: one read-only call.
        assert outcome.is_usable is True, ResponseStatusReader.explain(outcome)  # WHY: the reason names the fault.
        detail = ServiceRequest.from_detail(outcome.result)  # WHY: parsed detail with the RMA numbers.
        if detail.rma_numbers:  # WHY: the first case with an RMA is enough for this check.
            return detail  # WHY: the RMA numbers come from this detail.
    return None  # WHY: no case in the bounded set lists an RMA.


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the one read-only live RMA read.",
)
def test_live_rma_read_is_read_only(caplog: pytest.LogCaptureFixture) -> None:
    """Read the RMA of the first case with an RMA among five detail reads. No write operation is used."""
    caplog.set_level(logging.INFO)  # WHY: the RMA lines must reach the live log.
    detail = _detail_with_rma(_live_cases_last_month(), attempts=5)  # WHY: a bounded search for an RMA case.
    if detail is None:  # WHY: no RMA in the bounded set means no RMA read.
        pytest.skip("No case with an RMA among the first five detail reads of the last calendar month")  # WHY: reason.
    rma_number = detail.rma_numbers[0]  # WHY: one RMA read keeps the live call count low.
    outcome = _live_session().case.get_rma(rma_number, detail.request_number, detail.case_number)  # WHY: one read.
    assert outcome.is_usable is True, ResponseStatusReader.explain(outcome)  # WHY: the reason names the fault.
    items = RmaItem.parse_all(rma_number, outcome.result)  # WHY: the items of this RMA.
    logging.getLogger(__name__).info("Live RMA read: %d item(s) for one RMA", len(items))  # WHY: count only.
    for item in items:  # WHY: one masked line for each item.
        logging.getLogger(__name__).info("Live RMA item: %s", _rma_item_line(item))  # WHY: business fields only.
