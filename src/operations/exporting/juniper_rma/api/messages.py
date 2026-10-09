"""Request envelopes and response readers for the Juniper Service Case and Asset APIs.

The envelope rules follow contracts/juniper-case-api.md and
contracts/juniper-asset-api.md. The body status decides the outcome (R-07).
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import json  # WHY: response bodies are JSON documents.
import logging  # WHY: action log for each envelope and each reply.
import uuid  # WHY: a new 32-character identifier for each attempt (R-03).
from dataclasses import dataclass, field  # WHY: immutable records for replies and outcomes.
from datetime import UTC, datetime  # WHY: UTC timestamps with milliseconds (R-04).
from typing import TYPE_CHECKING, Any  # WHY: the settings type is needed only for annotations.

if TYPE_CHECKING:  # WHY: avoid a runtime import cycle with the settings module.
    from src.operations.exporting.juniper_rma.settings import JuniperSettings  # WHY: annotations only.

logger = logging.getLogger(__name__)  # WHY: module logger for envelope and reply events.


@dataclass(frozen=True)
class JuniperTransportReply:
    """One completed exchange with a Juniper endpoint. The body stays out of repr output."""

    endpoint: str  # WHY: the operation name, used in logs and reports.
    http_status: int  # WHY: the transport outcome, separate from the body status.
    body: dict[str, Any] = field(repr=False)  # WHY: the parsed JSON body, hidden from repr output.
    transaction_id: str  # WHY: the identifier of the attempt that produced this reply.
    attempts: int  # WHY: the number of attempts that the call used.

    @staticmethod
    def parse_object(raw: bytes) -> dict[str, Any]:
        """Return the JSON object in the raw bytes, or an empty dict when the bytes hold no object."""
        if not raw:  # WHY: an empty body has nothing to parse.
            return {}  # WHY: callers read a missing body as no result.
        try:  # WHY: a malformed body is a reply problem, not a crash.
            parsed = json.loads(raw.decode("utf-8"))  # WHY: the API replies with UTF-8 JSON.
        except (UnicodeDecodeError, json.JSONDecodeError):  # WHY: both errors mean the body is not JSON.
            logger.warning("juniper.body_not_json")  # WHY: log the fact, never the body.
            return {}  # WHY: no result for this reply.
        if isinstance(parsed, list):  # WHY: a top-level list (the list-of-values reply) keeps its items.
            return {"items": parsed}  # WHY: the items stay available under one named key.
        return parsed if isinstance(parsed, dict) else {}  # WHY: only a JSON object carries named fields.


@dataclass(frozen=True)
class ResponseOutcome:
    """The body status, the fault codes, and the result of one reply (R-07)."""

    endpoint: str  # WHY: the operation name.
    status_code: str  # WHY: the body statusCode text: 200, 300, 400, or empty when missing.
    result: dict[str, Any] = field(repr=False)  # WHY: the result fields, hidden from repr output.
    fault_codes: tuple[str, ...] = ()  # WHY: fault codes that drive the decision logic.
    fault_messages: tuple[str, ...] = ()  # WHY: raw messages for fault codes that the table does not list.

    @property
    def is_usable(self) -> bool:  # WHY: codes 200 and 300 both carry a result (R-07).
        """Return True when the body status carries a result."""
        return self.status_code in ("200", "300")  # WHY: 300 is a warning, and it keeps its result.

    def has_fault(self, code: str) -> bool:  # WHY: decision logic checks one code at a time.
        """Return True when the reply lists the fault code."""
        return code in self.fault_codes  # WHY: codes are compared as text.


class RequestMessageBuilder:
    """Build the request envelopes from the identifiers in settings."""

    def __init__(self, settings: JuniperSettings) -> None:
        """Keep the settings that every envelope uses."""
        self._settings = settings  # WHY: identifiers come from the validated settings.

    @staticmethod
    def new_transaction_id() -> str:
        """Return a new 32-character lowercase hexadecimal identifier."""
        return uuid.uuid4().hex  # WHY: letters and digits only satisfy the alphanumeric rule (R-03).

    @staticmethod
    def request_date_time() -> str:
        """Return the current UTC time as YYYY-MM-DDTHH:mm:ss.SSSZ."""
        moment = datetime.now(UTC)  # WHY: the API requires UTC.
        milliseconds = moment.microsecond // 1000  # WHY: the format carries three digits of milliseconds.
        return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{milliseconds:03d}Z"  # WHY: fault 903 rejects other formats.

    def build_list(self, from_date: str, to_date: str, transaction_id: str) -> dict[str, Any]:
        """Build the querySRListRequest envelope. The identifiers sit inside caseInformation (O-10)."""
        request = {  # WHY: the list operation keeps its identifiers beside the window.
            "requestDateTime": self.request_date_time(),  # WHY: a fresh UTC timestamp for this attempt.
            "appId": self._settings.app_id,  # WHY: application identifier from settings.
            "userId": self._settings.user_id,  # WHY: registered portal user from settings.
            "caseInformation": {  # WHY: the window and the identifiers share one block (O-10).
                "fromDate": from_date,  # WHY: start of the requested window (R-06).
                "toDate": to_date,  # WHY: end of the requested window (R-06).
                "customerSourceID": self._settings.customer_source_id,  # WHY: source identifier from settings.
                "customerUniqueTransactionID": transaction_id,  # WHY: identifier of this attempt.
            },  # WHY: close the window block.
        }
        logger.debug("Built querySRListRequest envelope")  # WHY: debug log after the build, no values.
        return {"querySRListRequest": request}  # WHY: the wrapper key that the operation expects.

    def build_detail(self, case_number: str, request_number: str, transaction_id: str) -> dict[str, Any]:
        """Build the querySRRequest envelope. The identifiers sit inside caseInformation (O-10)."""
        logger.debug("Built querySRRequest envelope")  # WHY: debug log after the build, no values.
        return {"querySRRequest": self._case_block(case_number, request_number, transaction_id)}  # WHY: shared block.

    def build_rma(
        self,
        rma_number: str,
        request_number: str,
        case_number: str,
        transaction_id: str,
    ) -> dict[str, Any]:
        """Build the queryRMARequest envelope. It adds the RMA number beside the shared blocks (O-5)."""
        block = self._case_block(case_number, request_number, transaction_id)  # WHY: same blocks as the detail.
        block["rmaNumber"] = rma_number  # WHY: the RMA to read, inside the wrapper.
        logger.debug("Built queryRMARequest envelope")  # WHY: debug log after the build, no values.
        return {"queryRMARequest": block}  # WHY: the wrapper key from the contract (O-5 pattern default).

    def build_note(
        self,
        note_id: str,
        request_number: str,
        case_number: str,
        transaction_id: str,
    ) -> dict[str, Any]:
        """Build the querySRNoteRequest envelope. It adds the note identifier beside the shared blocks."""
        block = self._case_block(case_number, request_number, transaction_id)  # WHY: same blocks as the detail.
        block["noteId"] = note_id  # WHY: the note to read, inside the wrapper.
        logger.debug("Built querySRNoteRequest envelope")  # WHY: debug log after the build, no values.
        return {"querySRNoteRequest": block}  # WHY: the wrapper key from the Case API example.

    def build_bulk(self, from_date: str, to_date: str, transaction_id: str) -> dict[str, Any]:
        """Build the assetsBulkDataRequest envelope for one date window of snapshots."""
        request = {  # WHY: the bulk operation keeps its identifiers at the top level.
            "appId": self._settings.app_id,  # WHY: application identifier from settings.
            "requestDateTime": self.request_date_time(),  # WHY: a fresh UTC timestamp for this attempt.
            "customerUniqueTransactionID": transaction_id,  # WHY: alphanumeric identifier for this attempt.
            "customerSourceID": self._settings.customer_source_id,  # WHY: source identifier from settings.
            "snapshotFromDate": from_date,  # WHY: start of the snapshot window, YYYY-MM-DD.
            "snapshotToDate": to_date,  # WHY: end of the snapshot window, YYYY-MM-DD.
        }
        logger.debug("Built assetsBulkDataRequest envelope")  # WHY: debug log after the build, no values.
        return {"assetsBulkDataRequest": request}  # WHY: the wrapper key from the Asset API example.

    def build_assets(self, serials: list[str], transaction_id: str) -> dict[str, Any]:
        """Build the queryAssetsDetailsRequest envelope for one batch of serial numbers."""
        request = {  # WHY: the Asset API keeps its identifiers at the top level.
            "appId": self._settings.app_id,  # WHY: application identifier from settings.
            "requestDateTime": self.request_date_time(),  # WHY: a fresh UTC timestamp for this attempt.
            "customerUniqueTransactionID": transaction_id,  # WHY: alphanumeric identifier (fault 986).
            "customerSourceID": self._settings.customer_source_id,  # WHY: source identifier from settings.
            "serialNumbersOrSSRNs": list(serials),  # WHY: the batch, 300 or fewer (fault 991).
        }
        logger.debug(
            "Built queryAssetsDetailsRequest envelope with %d serial numbers", len(serials)
        )  # WHY: count only.
        return {"queryAssetsDetailsRequest": request}  # WHY: the wrapper key from the export example.

    def _case_block(self, case_number: str, request_number: str, transaction_id: str) -> dict[str, Any]:
        """Return the fields that the detail and RMA envelopes share (O-10 placement)."""
        return {  # WHY: one block serves the detail and the RMA operations.
            "appId": self._settings.app_id,  # WHY: application identifier from settings.
            "userId": self._settings.user_id,  # WHY: registered portal user from settings.
            "requestDateTime": self.request_date_time(),  # WHY: a fresh UTC timestamp for this attempt.
            "caseInformation": {  # WHY: the detail operation keeps its identifiers here.
                "customerCaseNumber": case_number,  # WHY: empty string when the lookup uses a request number.
                "serviceRequestNumber": request_number,  # WHY: empty string when the lookup uses a case number.
                "customerSourceID": self._settings.customer_source_id,  # WHY: source identifier from settings.
                "customerUniqueTransactionID": transaction_id,  # WHY: identifier of this attempt.
            },
            "contact": {  # WHY: the contact block links the account to the request.
                "accountID": self._settings.account_id,  # WHY: account identifier from settings.
                "contactEmail": self._settings.contact_email,  # WHY: contact e-mail from settings.
            },
        }


class ResponseStatusReader:
    """Read the body status, the fault codes, and the result of a Juniper reply."""

    FAULT_MEANINGS: dict[str, str] = {  # WHY: plain-text meanings from the two contracts (R-08).
        "707": "appId and customerSourceID combination is not valid",
        "735": "appId is not valid",
        "750": "More than one contact record for contactEmail",
        "751": "accountID is not valid",
        "752": "customerSourceID and accountID combination is not valid",
        "753": "contactEmail is not a registered user",
        "754": "contactEmail is not linked to accountID",
        "755": "userId is not linked to accountID",
        "756": "customerCaseNumber is not linked to the account",
        "757": "serviceRequestNumber is not valid",
        "763": "customerCaseNumber has more than one request with the same value",
        "765": "rmaNumber is not valid",
        "768": "Serial number or SSRN is not valid",
        "769": "More than one contact record for userId",
        "771": "userId is not a registered user",
        "775": "rmaNumber does not belong to serviceRequestNumber",
        "778": "serviceRequestNumber is not linked to the account",
        "900": "appId is missing",
        "901": "userId is missing",
        "902": "requestDateTime is missing",
        "903": "requestDateTime format is wrong",
        "906": "customerSourceID is missing",
        "907": "appId and customerSourceID combination is not valid",
        "908": "customerUniqueTransactionID is missing",
        "931": "serviceRequestNumber is missing",
        "932": "appId and userId combination is not valid",
        "935": "appId is invalid",
        "937": "Invalid authentication method",
        "938": "User not authenticated with a valid certificate",
        "944": "rmaNumber is missing",
        "955": "Duplicate customerUniqueTransactionID. Retry with a new identifier.",
        "956": "Neither serviceRequestNumber nor customerCaseNumber is given",
        "973": "System error while preparing the response. Retry later.",
        "985": "Account identifier validation failed",
        "986": "customerUniqueTransactionID is invalid. Use only alphanumeric characters.",
        "991": "More than 300 serial numbers in one request",
        "992": "serialNumbersOrSSRNs is invalid",
        "999": "A key exceeds its maximum length",
    }
    FAULT_ACTIONS: dict[str, str] = {  # WHY: the next step for the operator, for common codes.
        "707": "Check JUNIPER_APP_ID and JUNIPER_CUSTOMER_SOURCE_ID.",
        "735": "Check JUNIPER_APP_ID.",
        "751": "Check JUNIPER_ACCOUNT_ID.",
        "752": "Check JUNIPER_CUSTOMER_SOURCE_ID and JUNIPER_ACCOUNT_ID.",
        "753": "Check JUNIPER_CONTACT_EMAIL.",
        "754": "Check JUNIPER_CONTACT_EMAIL and JUNIPER_ACCOUNT_ID.",
        "755": "Check JUNIPER_USER_ID and JUNIPER_ACCOUNT_ID.",
        "756": "Record the ticket as unmatched.",
        "757": "Check the request number.",
        "763": "Use the request number to choose one request.",
        "771": "Check JUNIPER_USER_ID.",
        "900": "Set JUNIPER_APP_ID.",
        "901": "Set JUNIPER_USER_ID.",
        "906": "Set JUNIPER_CUSTOMER_SOURCE_ID.",
        "907": "Check JUNIPER_APP_ID and JUNIPER_CUSTOMER_SOURCE_ID.",
        "932": "Check JUNIPER_APP_ID and JUNIPER_USER_ID.",
        "937": "Confirm the OAuth 2.0 setup with Juniper.",
        "938": "Confirm the credential type with Juniper.",
        "955": "The client sends a new identifier on the next attempt.",
        "956": "Give a request number or a customer case number.",
        "973": "Retry later. Report the code if it repeats.",
    }
    GATEWAY_MEANINGS: dict[int, str] = {  # WHY: gateway statuses that carry no body status, with the next step.
        401: (
            "Juniper gateway rejected the request with HTTP 401 after a token refresh. "
            "The application may not be enabled for this API. Ask Juniper to confirm the API access."
        ),
    }

    @classmethod
    def gateway_rejection(cls, endpoint: str, http_status: int) -> ResponseOutcome:
        """Return the outcome of a gateway rejection. The status is the reason, because no body status exists."""
        fallback = f"Juniper gateway replied with HTTP {http_status}."  # WHY: a status without a listed meaning.
        meaning = cls.GATEWAY_MEANINGS.get(http_status, fallback)  # WHY: the listed text, or the fallback.
        logger.info("juniper.gateway_rejection endpoint=%s http_status=%d", endpoint, http_status)  # WHY: status only.
        return ResponseOutcome(  # WHY: a typed outcome that the services and the workflows already handle.
            endpoint=endpoint,
            status_code=str(http_status),  # WHY: a status that is not 200 or 300 is not usable (R-07).
            result={},  # WHY: a rejection carries no result.
            fault_messages=(meaning,),  # WHY: explain() shows this plain-text meaning.
        )

    @classmethod
    def from_reply(cls, endpoint: str, reply: JuniperTransportReply) -> ResponseOutcome:
        """Return the outcome of a POST reply. A non-200 reply with no body status is a gateway rejection."""
        has_status = "statusCode" in reply.body or "fault" in reply.body  # WHY: a body status or fault is a reply.
        if reply.http_status != 200 and not has_status:  # WHY: the gateway refused the call without a body.
            return cls.gateway_rejection(endpoint, reply.http_status)  # WHY: name the rejection.
        return cls.read_checked(endpoint, reply)  # WHY: the body status decides, but an error status never passes.

    @classmethod
    def plain(cls, endpoint: str, reply: JuniperTransportReply) -> ResponseOutcome:
        """Return the outcome of a GET reply. A list-of-values reply may carry no body status."""
        has_status = "statusCode" in reply.body or "fault" in reply.body  # WHY: a body status is read as usual.
        if has_status:  # WHY: a body with a status or a fault follows the usual rules.
            return cls.read_checked(endpoint, reply)  # WHY: the body status decides, but an error status never passes.
        if reply.http_status == 200:  # WHY: HTTP 200 with no body status is a usable plain reply.
            logger.info("juniper.response endpoint=%s plain_reply http_status=200", endpoint)  # WHY: status only.
            return ResponseOutcome(endpoint=endpoint, status_code="200", result=dict(reply.body))  # WHY: keep it.
        return cls.gateway_rejection(endpoint, reply.http_status)  # WHY: name the rejection.

    @classmethod
    def read_checked(cls, endpoint: str, reply: JuniperTransportReply) -> ResponseOutcome:
        """Return the body outcome, unless an HTTP error status contradicts a success body status."""
        outcome = cls.read(endpoint, reply.body)  # WHY: the body status and the faults, read as usual.
        if reply.http_status >= 400 and outcome.is_usable:  # WHY: a 4xx or 5xx status never carries a usable result.
            return cls.gateway_rejection(endpoint, reply.http_status)  # WHY: name the rejection, not the body.
        return outcome  # WHY: a fault or a non-usable body keeps its reading.

    @classmethod
    def read(cls, endpoint: str, body: dict[str, Any]) -> ResponseOutcome:
        """Return the outcome of one reply. The body status decides the outcome (R-07)."""
        envelope = cls._unwrap(body)  # WHY: the wrapper key may or may not be present (R-09).
        status = str(envelope.get("statusCode", "")).strip()  # WHY: the body status is text.
        codes, messages = cls._read_faults(envelope.get("fault"))  # WHY: faults explain a failure.
        logger.info(  # WHY: action log after the read, with codes and counts only.
            "juniper.response endpoint=%s body_status=%s fault_count=%d fault_codes=%s",
            endpoint,
            status or "missing",
            len(codes),
            ",".join(codes) or "none",
        )
        return ResponseOutcome(  # WHY: the typed outcome for the caller.
            endpoint=endpoint,
            status_code=status,
            result=envelope,
            fault_codes=codes,
            fault_messages=messages,
        )

    @classmethod
    def describe(cls, code: str, message: str = "") -> str:
        """Return the plain-text meaning of a fault code, or the raw text when the code is not listed."""
        meaning = cls.FAULT_MEANINGS.get(code)  # WHY: the documented meaning, when the table lists the code.
        if meaning is None:  # WHY: an unlisted code shows the raw text so the operator can still act.
            return f"Fault {code or 'unknown'}: {cls._ascii_text(message) or 'no message'}"  # WHY: ASCII console text.
        return f"Fault {code}: {meaning}"  # WHY: the plain-text meaning from the contracts.

    @classmethod
    def action_for(cls, code: str) -> str:
        """Return the next step for the operator. Unknown codes go to Juniper support."""
        return cls.FAULT_ACTIONS.get(code, "Report the code to Juniper support.")  # WHY: a safe default step.

    @classmethod
    def explain(cls, outcome: ResponseOutcome) -> str:
        """Return one sentence that says why a reply is not usable."""
        if outcome.fault_codes:  # WHY: a fault gives the most specific reason.
            first_message = (
                outcome.fault_messages[0] if outcome.fault_messages else ""
            )  # WHY: raw text for unlisted codes.
            code = outcome.fault_codes[0]  # WHY: the first fault drives the operator message.
            return f"{cls.describe(code, first_message)}. {cls.action_for(code)}"  # WHY: meaning, then the next step.
        if outcome.fault_messages:  # WHY: a gateway rejection gives its meaning as text, with no fault code.
            return outcome.fault_messages[0]  # WHY: the plain-text meaning from the gateway table.
        return (
            f"Juniper returned body status {outcome.status_code or 'missing'} without a fault."  # WHY: no fault given.
        )

    @staticmethod
    def _unwrap(body: dict[str, Any]) -> dict[str, Any]:
        """Return the envelope inside a *Response wrapper, or the body when no wrapper exists."""
        for key, value in body.items():  # WHY: accept any operation wrapper.
            if key.endswith("Response") and isinstance(value, dict):  # WHY: the wrapper holds the envelope.
                return value  # WHY: fields live inside the wrapper.
        return body  # WHY: a flat reply has no wrapper.

    @staticmethod
    def _read_faults(raw: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Return the fault codes and the raw messages from the fault list."""
        if isinstance(raw, str) and raw.strip():  # WHY: some replies document a fault as plain text.
            return (), (raw.strip(),)  # WHY: keep the text so the operator sees the reason.
        items = [raw] if isinstance(raw, dict) else raw  # WHY: a single fault may arrive as an object.
        if not isinstance(items, list):  # WHY: no usable fault list.
            return (), ()  # WHY: nothing to report.
        faults = [item for item in items if isinstance(item, dict)]  # WHY: keep only fault objects.
        codes = tuple(str(item.get("errorCode", "")).strip() for item in faults)  # WHY: codes as text.
        messages = tuple(str(item.get("errorMessage", "")).strip() for item in faults)  # WHY: raw messages.
        return codes, messages  # WHY: the codes and their raw texts.

    @staticmethod
    def _ascii_text(value: str) -> str:
        """Return the text with non-ASCII characters escaped, so the console and the log stay ASCII."""
        return value.encode("ascii", "backslashreplace").decode("ascii")  # WHY: ASCII-only output (Principle V).
