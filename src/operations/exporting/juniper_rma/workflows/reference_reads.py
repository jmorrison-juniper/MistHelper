"""Menus 298 to 300: the Juniper list-of-values, software version, and bulk asset read menus."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and operator messages for each read.
from datetime import UTC, date, datetime, timedelta  # WHY: the snapshot window and its defaults.

from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call is reported, not raised.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply reading.
    ResponseOutcome,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.reference_rows import (  # WHY: row builders.
    BulkLinkRows,
    LovRows,
    SoftwareVersionRows,
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for each menu.
)
from src.operations.exporting.juniper_rma.workflows.juniper_menu_support import (  # WHY: shared prompts, sink, and clock.  # noqa: E501
    JuniperExportSink,
    JuniperMenuInput,
    utc_now_text,
)

logger = logging.getLogger(__name__)  # WHY: module logger for each reference read.


class LovWorkflow:
    """Menu 298: read the Juniper list of values, and save every value with its full path."""

    FILENAME = "JuniperLovs.csv"  # WHY: one row for each value of each group.
    API_NAME = "juniperGetLov"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service and the settings.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. The list of values needs no contact, so the contact e-mail is not required."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=False)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        LovWorkflow(session).execute()  # WHY: the read itself.

    def execute(self) -> bool:
        """Read the list of values, print every value, and write the export."""
        outcome = self._read()  # WHY: one GET call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        rows = LovRows.rows(outcome.result, utc_now_text())  # WHY: one row for each scalar value.
        return self._sink.publish("Juniper list of values", self.FILENAME, self.API_NAME, LovRows.COLUMNS, rows)

    def _read(self) -> ResponseOutcome | None:
        """Read the list of values. Return None when the call fails or Juniper does not return it."""
        logger.info("Juniper list-of-values read started")  # WHY: action log before the call.
        try:  # WHY: a transport failure is reported as a failed read.
            outcome = self._session.case.get_lov(self._session.settings.app_id)  # WHY: one GET call.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error(  # WHY: the operator sees the reason.
                "Juniper list-of-values read failed to complete: %s", error  # The message keeps the cause.
            )
            return None  # WHY: no export.
        if outcome.is_usable:  # WHY: a usable reply carries the values.
            return outcome  # WHY: the caller builds the rows.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper list-of-values read failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: no export.


class SoftwareVersionWorkflow:
    """Menu 299: read the Juniper software versions by product series and platform, and save each release."""

    FILENAME = "JuniperSoftwareVersions.csv"  # WHY: one row for each release of each platform.
    API_NAME = "juniperGetSoftwareEosLov"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service and the settings.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. The software list needs no contact, so the contact e-mail is not required."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=False)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        SoftwareVersionWorkflow(session).execute()  # WHY: the read itself.

    def execute(self) -> bool:
        """Read the software versions, print every release, and write the export."""
        outcome = self._read()  # WHY: one GET call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        rows = SoftwareVersionRows.rows(outcome.result, utc_now_text())  # WHY: one row for each release.
        return self._sink.publish(
            "Juniper software versions",
            self.FILENAME,
            self.API_NAME,
            SoftwareVersionRows.COLUMNS,
            rows,
        )

    def _read(self) -> ResponseOutcome | None:
        """Read the software versions. Return None when the call fails or Juniper does not return them."""
        logger.info("Juniper software version read started")  # WHY: action log before the call.
        try:  # WHY: a transport failure is reported as a failed read.
            outcome = self._session.case.get_software_eos_lov(self._session.settings.app_id)  # WHY: one GET call.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error(  # WHY: the operator sees the reason.
                "Juniper software version read failed to complete: %s", error  # The message keeps the cause.
            )
            return None  # WHY: no export.
        if outcome.is_usable:  # WHY: a usable reply carries the versions.
            return outcome  # WHY: the caller builds the rows.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper software version read failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: no export.


class AssetBulkWorkflow:
    """Menu 300: list the bulk asset snapshot files for a date window, with each link masked."""

    MIN_AGE_DAYS = 1  # WHY: the newest snapshot is yesterday, because today is day zero (asset API note).
    MAX_AGE_DAYS = 7  # WHY: Juniper keeps each snapshot file for seven days.
    LINKS_FILE = "JuniperAssetBulkLinks.csv"  # WHY: one row for each file link, with its signature masked.
    LINKS_API = "juniperQueryAssetsBulkData"  # WHY: the operation name recorded with the export.
    NO_DATA_FILE = "JuniperAssetBulkNoData.csv"  # WHY: one row for each snapshot date that has no data.
    NO_DATA_API = "juniperQueryAssetsBulkNoData"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Asset service.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. The asset read needs no contact, so the contact e-mail is not required."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=False)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        AssetBulkWorkflow(session).execute()  # WHY: the read itself.

    def execute(self) -> bool:
        """Ask for the snapshot window, read the links, print every field, and write both exports."""
        today = datetime.now(UTC).date()  # WHY: the window is relative to today in UTC.
        start = JuniperMenuInput.day(  # WHY: the default start is the oldest retained day.
            "snapshot start date", today - timedelta(days=self.MAX_AGE_DAYS), "juniper_bulk_start"
        )
        end = JuniperMenuInput.day(  # WHY: the default end is the newest complete day.
            "snapshot end date", today - timedelta(days=self.MIN_AGE_DAYS), "juniper_bulk_end"
        )
        if start is None or end is None:  # WHY: a rejected date stops before any call.
            return False  # WHY: nothing was sent.
        if not self._window_is_valid(start, end, today):  # WHY: the window must follow the retention rule.
            return False  # WHY: nothing was sent.
        outcome = self._read(start, end)  # WHY: one bulk call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        retrieved = utc_now_text()  # WHY: one retrieval time for both exports.
        self._sink.publish(
            "Asset bulk links",
            self.LINKS_FILE,
            self.LINKS_API,
            BulkLinkRows.LINK_COLUMNS,
            BulkLinkRows.links(outcome.result, retrieved),
        )  # WHY: the links first.
        return self._sink.publish(  # WHY: the no-data export reports the result of the run.
            "Asset bulk no data",
            self.NO_DATA_FILE,
            self.NO_DATA_API,
            BulkLinkRows.NO_DATA_COLUMNS,
            BulkLinkRows.no_data(outcome.result, retrieved),
        )

    def _window_is_valid(self, start: date, end: date, today: date) -> bool:
        """Return True when both dates fall in the retained window and the start is not after the end."""
        start_age = (today - start).days  # WHY: days back from today for the start.
        end_age = (today - end).days  # WHY: days back from today for the end.
        in_window = all(self.MIN_AGE_DAYS <= age <= self.MAX_AGE_DAYS for age in (start_age, end_age))  # WHY.
        if start > end or not in_window:  # WHY: a window outside the retention rule is rejected before any call.
            logger.warning(
                "Input rejected: the snapshot could not be read, because the dates must be "
                "one to seven days old, with the start first"
            )
            return False  # WHY: no call is made.
        return True  # WHY: the window is valid.

    def _read(self, start: date, end: date) -> ResponseOutcome | None:
        """Read the bulk links. Return None when the call fails or Juniper does not accept the request."""
        logger.info("Juniper asset bulk read: window %s to %s", start.isoformat(), end.isoformat())  # WHY: action log.
        try:  # WHY: a transport failure is reported as a failed read.
            outcome = self._session.asset.query_bulk(start.isoformat(), end.isoformat())  # WHY: one bulk call.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error("Juniper asset bulk read failed to complete: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: no export.
        if outcome.is_usable:  # WHY: a usable reply carries the links or the no-data entries.
            return outcome  # WHY: the caller builds the rows.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper asset bulk read failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: no export.
