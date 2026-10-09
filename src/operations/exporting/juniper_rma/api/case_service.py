"""Read operations of the Juniper Service Case API: request list, request detail, and RMA detail.

This class exposes no write operation. The Case API write operations are out of
scope for this integration (FR-006 and FR-007).
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log before each read.
from collections.abc import Callable  # WHY: the body builder receives the transaction identifier.
from datetime import UTC, date, datetime, timedelta  # WHY: the 90-day window and the one-day access window.
from typing import Any  # WHY: the body builder returns a loosely typed envelope.

from src.operations.exporting.juniper_rma.api.gateway import JuniperGatewayClient  # WHY: the one path to the network.
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: the envelope builder and the reply reader.
    RequestMessageBuilder,
    ResponseOutcome,
    ResponseStatusReader,
)

logger = logging.getLogger(__name__)  # WHY: module logger for each read.


class JuniperCaseService:
    """Run the three read operations of the Case API."""

    LIST_WINDOW_DAYS = 90  # WHY: the list operation covers the last 90 days (R-06).
    ACCESS_WINDOW_DAYS = 1  # WHY: the access check uses a one-day window.
    LIST_PATH = "querysrlist"  # WHY: operation path under the Case base address.
    DETAIL_PATH = "querysrdetails"  # WHY: operation path for one request.
    RMA_PATH = "queryrmadetails"  # WHY: operation path for one RMA.
    NOTE_PATH = "querysrnotedetails"  # WHY: operation path for the content of one note.
    LOV_PATH = "getlov"  # WHY: GET path for the list of values.
    EOS_PATH = "getSoftwareEosLov"  # WHY: GET path for the software versions by product series.

    def __init__(
        self,
        gateway: JuniperGatewayClient,
        builder: RequestMessageBuilder,
        reader: ResponseStatusReader,
        base_url: str,
    ) -> None:
        """Store the collaborators and the Case base address."""
        self._gateway = gateway  # WHY: every call goes through the gateway.
        self._builder = builder  # WHY: envelopes come from the builder.
        self._reader = reader  # WHY: replies are read by the status reader.
        self._base_url = base_url  # WHY: the checked Case base address.

    def check_access(self) -> ResponseOutcome:
        """Send one list request for a one-day window and return the outcome."""
        to_day = datetime.now(UTC).date()  # WHY: the window ends today in UTC.
        from_day = to_day - timedelta(days=self.ACCESS_WINDOW_DAYS)  # WHY: one day back.
        logger.info("Juniper access check: sending one list request for a one-day window")  # WHY: action log.
        return self.list_requests(from_day=from_day, to_day=to_day)  # WHY: the same operation as the list.

    def list_requests(self, from_day: date | None = None, to_day: date | None = None) -> ResponseOutcome:
        """Return the list outcome. The default window runs from 90 days before today to today."""
        end = to_day or datetime.now(UTC).date()  # WHY: the default end date is today in UTC.
        start = from_day or end - timedelta(days=self.LIST_WINDOW_DAYS)  # WHY: the default start is 90 days back.
        logger.info("Juniper request list: window %s to %s", start.isoformat(), end.isoformat())  # WHY: action log.
        return self._call(  # WHY: one list call through the gateway.
            self.LIST_PATH,
            lambda transaction_id: self._builder.build_list(start.isoformat(), end.isoformat(), transaction_id),
        )

    def get_request(self, case_number: str = "", request_number: str = "") -> ResponseOutcome:
        """Return the detail of one request, found by request number or by customer case number."""
        if not case_number and not request_number:  # WHY: the operation needs one of the two keys (fault 956).
            raise ValueError("A request number or a customer case number is required")  # WHY: a programming error.
        key_type = "request number" if request_number else "customer case number"  # WHY: name the key type only.
        logger.info("Juniper request detail by %s", key_type)  # WHY: action log before the call, no value.
        return self._call(  # WHY: one detail call through the gateway.
            self.DETAIL_PATH,
            lambda transaction_id: self._builder.build_detail(case_number, request_number, transaction_id),
        )

    def get_rma(self, rma_number: str, request_number: str, case_number: str) -> ResponseOutcome:
        """Return the detail of one RMA, with its shipping data and its items."""
        logger.info("Juniper RMA detail read")  # WHY: action log before the call, no value.
        return self._call(  # WHY: one RMA call through the gateway.
            self.RMA_PATH,
            lambda transaction_id: self._builder.build_rma(rma_number, request_number, case_number, transaction_id),
        )

    def get_note(self, note_id: str, request_number: str, case_number: str) -> ResponseOutcome:
        """Return the content of one note. The note identifier comes from the request detail."""
        logger.info("Juniper note read")  # WHY: action log before the call, no value.
        reply = self._gateway.post(  # WHY: one checked call with retries.
            self.NOTE_PATH,
            self._base_url,
            self.NOTE_PATH,
            lambda transaction_id: self._builder.build_note(note_id, request_number, case_number, transaction_id),
        )
        return ResponseStatusReader.from_reply(self.NOTE_PATH, reply)  # WHY: the body status decides the outcome.

    def get_lov(self, app_id: str) -> ResponseOutcome:
        """Return the list of values. The call is a GET. The live service needs the lowercase appid name."""
        logger.info("Juniper list-of-values read")  # WHY: action log before the call, no value.
        reply = self._gateway.get(self.LOV_PATH, self._base_url, self.LOV_PATH, {"appid": app_id})  # WHY: one GET.
        return ResponseStatusReader.plain(self.LOV_PATH, reply)  # WHY: a plain reply is usable with HTTP 200.

    def get_software_eos_lov(self, app_id: str) -> ResponseOutcome:
        """Return the software versions grouped by product series. The spec names this query parameter in lowercase."""
        logger.info("Juniper software version list read")  # WHY: action log before the call, no value.
        reply = self._gateway.get(self.EOS_PATH, self._base_url, self.EOS_PATH, {"appid": app_id})  # WHY: one GET.
        return ResponseStatusReader.plain(self.EOS_PATH, reply)  # WHY: a plain reply is usable with HTTP 200.

    def _call(self, path: str, build_body: Callable[[str], dict[str, Any]]) -> ResponseOutcome:
        """Send one checked call through the gateway and read the reply."""
        reply = self._gateway.post(path, self._base_url, path, build_body)  # WHY: one checked call with retries.
        if reply.http_status in ResponseStatusReader.GATEWAY_MEANINGS:  # WHY: a gateway rejection has no body status.
            return ResponseStatusReader.gateway_rejection(path, reply.http_status)  # WHY: name the rejection.
        return self._reader.read_checked(path, reply)  # WHY: the body status decides, but an error status never passes.
