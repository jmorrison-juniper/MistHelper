"""Menu 303: look up one Juniper service request, optionally with one RMA, by request number or case number."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and the operator messages for the lookup.
from datetime import UTC, datetime  # WHY: the retrieval time for the export row.
from typing import Any  # WHY: the exporter is an injected object.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: the shared input helper.
)
from src.operations.exporting.export.data_exporter import (
    DataExporter,  # WHY: the export goes through the shared exporter.
)
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call is reported, not raised.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply reading.
    ResponseOutcome,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.export_rows import (
    ExportRowBuilder,  # WHY: the request and item row builders.
)
from src.operations.exporting.juniper_rma.model.service_request import (
    IdentifierRule,
    RmaItem,
    RmaRecord,
    ServiceRequest,
)  # WHY: parsing.
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for this menu.
)

logger = logging.getLogger(__name__)  # WHY: module logger for the lookup steps.


class LookupWorkflow:
    """Ask for a key, read one request, optionally read one RMA, and export the request row."""

    KIND_REQUEST = "1"  # WHY: the operator choice for a request number.
    KIND_CASE = "2"  # WHY: the operator choice for a customer case number.
    NOT_FOUND_CODES = ("756", "757", "778")  # WHY: codes that mean no such request for this account.

    def __init__(self, session: JuniperServiceSession, exporter: Any = DataExporter) -> None:
        """Store the checked session and the exporter."""
        self._session = session  # WHY: the Case API service and the settings.
        self._exporter = exporter  # WHY: the shared exporter (a test may inject a double).

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and run one lookup."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and settings checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to look up.
        LookupWorkflow(session).execute()  # WHY: the lookup itself.

    def execute(self) -> None:
        """Run the lookup. Stop before any call when an input fails its rule."""
        kind = self._ask_kind()  # WHY: the key type first.
        if kind is None:  # WHY: a cancelled or invalid choice stops the lookup.
            logger.info("Juniper lookup cancelled: no key type chosen")  # WHY: the operator sees the reason.
            return  # WHY: nothing to read.
        value = self._ask_value(kind)  # WHY: the request number or case number.
        if value is None:  # WHY: a blank or rejected value stops before any call.
            logger.info("Juniper lookup cancelled: the value is blank or breaks the rule")  # WHY: reason only.
            return  # WHY: nothing to read.
        rma_number = self._ask_rma()  # WHY: the RMA is optional.
        outcome = self._read_request(kind, value)  # WHY: one detail read.
        if outcome is None:  # WHY: the read failed or the request is not found.
            return  # WHY: the reason is already logged.
        request = ServiceRequest.from_detail(outcome.result)  # WHY: the parsed request.
        logger.info(  # WHY: the outcome, without personal values.
            "Juniper request %s found, status %s", request.request_number or "unknown", request.status or "unknown"
        )
        self._export_request(request)  # WHY: the request row.
        if rma_number:  # WHY: show the RMA only when the operator asked for it.
            self._show_rma(request, rma_number)  # WHY: one RMA read and its items.

    def _ask_kind(self) -> str | None:
        """Ask whether the key is a request number or a customer case number."""
        mh = SourceDependencyResolver  # WHY: the shared input helper.
        choice = mh.InputUtils.safe_input(  # WHY: the prompt uses the safe input helper.
            "Enter 1 for a request number or 2 for a customer case number (Enter to cancel): ",
            default_value="",
            allow_empty=True,
            context="juniper_lookup_kind",
        )
        return choice if choice in (self.KIND_REQUEST, self.KIND_CASE) else None  # WHY: only two choices exist.

    def _ask_value(self, kind: str) -> str | None:
        """Ask for the key value. Return None when it is blank or breaks the identifier rule."""
        mh = SourceDependencyResolver  # WHY: the shared input helper.
        label = "request number" if kind == self.KIND_REQUEST else "customer case number"  # WHY: the prompt label.
        raw: str = mh.InputUtils.safe_input(  # WHY: the prompt uses the safe input helper.
            f"Enter the {label} (1 to 40 letters, digits, or hyphens; Enter to cancel): ",
            default_value="",
            allow_empty=True,
            context="juniper_lookup_value",
        )
        if not raw:  # WHY: a blank value cancels the lookup.
            return None  # WHY: no call is made.
        if not IdentifierRule.is_valid(raw):  # WHY: reject the value before any call.
            logger.warning(  # WHY: the rule, not the value.
                "Input rejected: the lookup could not run, because the value breaks "  # The first half of the message.
                "the 1 to 40 character rule"  # The rule, not the value.
            )
            return None  # WHY: no call is made.
        return raw  # WHY: the checked value.

    def _ask_rma(self) -> str | None:
        """Ask for an optional RMA number. Return None when the operator skips it or it breaks the rule."""
        mh = SourceDependencyResolver  # WHY: the shared input helper.
        raw: str = mh.InputUtils.safe_input(  # WHY: the prompt uses the safe input helper.
            "Enter an RMA number, or press Enter to skip: ",
            default_value="",
            allow_empty=True,
            context="juniper_lookup_rma",
        )
        if not raw:  # WHY: the RMA is optional.
            return None  # WHY: nothing more to read.
        if not IdentifierRule.is_valid(raw):  # WHY: reject an invalid RMA before any call.
            logger.warning("RMA number rejected: use 1 to 40 letters, digits, or hyphens")  # WHY: the rule only.
            return None  # WHY: skip the RMA.
        return raw  # WHY: the checked RMA number.

    def _read_request(self, kind: str, value: str) -> ResponseOutcome | None:
        """Read one request. Return None when the request is not found or the read fails."""
        key_label = "request number" if kind == self.KIND_REQUEST else "case number"  # WHY: the key type only.
        logger.info("Juniper request lookup by %s", key_label)  # WHY: action log before the read.
        try:  # WHY: a transport failure is reported as a failed lookup.
            if kind == self.KIND_REQUEST:  # WHY: the request number is the key.
                outcome = self._session.case.get_request(request_number=value)  # WHY: one detail call.
            else:  # WHY: the customer case number is the key.
                outcome = self._session.case.get_request(case_number=value)  # WHY: one detail call.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            logger.error("Juniper lookup failed to complete: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: no detail.
        if outcome.is_usable:  # WHY: a usable reply carries the request.
            return outcome  # WHY: the caller parses it.
        if any(code in self.NOT_FOUND_CODES for code in outcome.fault_codes):  # WHY: not found is not a fault.
            logger.info("No Juniper request matches this value for the account")  # WHY: the operator sees the result.
            return None  # WHY: nothing to show.
        logger.error("Juniper lookup failed to complete: %s", ResponseStatusReader.explain(outcome))  # WHY: the reason.
        return None  # WHY: nothing to show.

    def _export_request(self, request: ServiceRequest) -> None:
        """Write the one-row lookup export through DataExporter."""
        retrieved = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: the time of this lookup.
        rows = [ExportRowBuilder.request_row(request, retrieved)]  # WHY: one row for the request.
        logger.info("Writing the lookup row to JuniperLookup.csv")  # WHY: action log before the write.
        self._exporter.write_with_format_selection(  # WHY: the shared export path.
            ExportRowBuilder.ascii_rows(rows),  # WHY: FR-029 ASCII-only output before the write.
            "JuniperLookup.csv",
            api_function_name="juniperQuerySrDetails",  # WHY: picks the key strategy.
            fieldnames=ExportRowBuilder.REQUEST_FIELDS,
        )

    def _export_rma_items(self, rma_number: str, request: ServiceRequest, result: dict[str, Any]) -> None:
        """Write every item of the RMA to JuniperLookupRmaItems.csv, with the personal fields in full."""
        retrieved = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: the time of this lookup, in UTC.
        rma = RmaRecord.from_result(result, request.request_number)  # WHY: the RMA context for each item row.
        items = RmaItem.parse_all(rma_number, result)  # WHY: every defective, replacement, and CE item.
        rows = [ExportRowBuilder.item_row(rma, item, retrieved) for item in items]  # WHY: the item rows.
        if not rows:  # WHY: the exporter rejects empty data.
            logger.info("The RMA has no items, so no lookup items file was written")  # WHY: the operator sees it.
            return  # WHY: nothing to write.
        logger.info("Writing %d RMA item row(s) to JuniperLookupRmaItems.csv", len(rows))  # WHY: action log.
        self._exporter.write_with_format_selection(  # WHY: the shared export path.
            ExportRowBuilder.ascii_rows(rows),  # WHY: FR-029 ASCII-only output before the write.
            "JuniperLookupRmaItems.csv",
            api_function_name="juniperQueryRmaDetails",  # WHY: picks the key strategy.
            fieldnames=ExportRowBuilder.RMA_ITEM_FIELDS,
        )

    def _show_rma(self, request: ServiceRequest, rma_number: str) -> None:
        """Read one RMA of the request and show its items. The personal fields are not printed."""
        logger.info("Reading the Juniper RMA detail for the lookup")  # WHY: action log before the call.
        try:  # WHY: a transport failure is reported, not raised.
            outcome = self._session.case.get_rma(rma_number, request.request_number, request.case_number)  # WHY.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error("Juniper RMA lookup failed: %s", error)  # WHY: the operator sees the reason.
            return  # WHY: no RMA to show.
        if not outcome.is_usable:  # WHY: a fault gives no RMA.
            logger.error("Juniper RMA lookup failed: %s", ResponseStatusReader.explain(outcome))  # WHY: the reason.
            return  # WHY: no RMA to show.
        items = RmaItem.parse_all(rma_number, outcome.result)  # WHY: the items of the RMA.
        logger.info("RMA %s has %d item(s)", rma_number, len(items))  # WHY: count only, no personal field.
        self._export_rma_items(rma_number, request, outcome.result)  # WHY: the same items are saved to a file.
        for item in items:  # WHY: one line for each item, without personal values.
            logger.info("  %s item %s status=%s", item.item_type, item.item_number, item.status or "unknown")  # WHY.
