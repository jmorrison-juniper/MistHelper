"""Menu 304: look up warranty, contract, and status data for Juniper serial numbers."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and the operator messages for the asset lookup.
import re  # WHY: split the operator input on commas and spaces.
from datetime import UTC, datetime  # WHY: the retrieval time for the export rows.
from typing import Any  # WHY: the exporter is an injected object.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: the shared input helper.
)
from src.operations.exporting.export.data_exporter import (
    DataExporter,  # WHY: every export goes through the shared exporter.
)
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call is reported, not raised.
)
from src.operations.exporting.juniper_rma.model.asset import (  # WHY: asset and coverage parsing.
    AssetCoverageRow,
    AssetRecord,
)
from src.operations.exporting.juniper_rma.model.export_rows import ExportRowBuilder  # WHY: the asset row builder.
from src.operations.exporting.juniper_rma.model.service_request import (
    IdentifierRule,  # WHY: the identifier rule for each serial.
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for this menu.
)

logger = logging.getLogger(__name__)  # WHY: module logger for the asset lookup.


class AssetLookupWorkflow:
    """Read the asset details of the entered serial numbers and export the asset and coverage rows."""

    SEPARATORS = r"[,\s]+"  # WHY: operators may separate serial numbers with commas or spaces.

    def __init__(self, session: JuniperServiceSession, exporter: Any = DataExporter) -> None:
        """Store the checked session and the exporter."""
        self._session = session  # WHY: the Asset API service.
        self._exporter = exporter  # WHY: the shared exporter (a test may inject a double).

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and run the asset lookup."""
        session = JuniperServiceSession.open_for_menu(
            needs_contact_email=False
        )  # WHY: the asset menu needs no contact.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to look up.
        AssetLookupWorkflow(session).execute()  # WHY: the asset lookup itself.

    @classmethod
    def parse_serials(cls, raw: str) -> tuple[list[str], list[str]]:
        """Split the input into valid serial numbers and rejected tokens. Duplicates are removed in order."""
        tokens = [token for token in re.split(cls.SEPARATORS, raw.strip()) if token]  # WHY: split and drop blanks.
        valid: list[str] = []  # WHY: the serial numbers that pass the rule, in input order.
        rejected: list[str] = []  # WHY: the tokens that break the rule.
        for token in tokens:  # WHY: check each token once.
            if not IdentifierRule.is_valid(token):  # WHY: a token that breaks the rule is rejected.
                rejected.append(token)  # WHY: keep it for the count, not for a call.
                continue  # WHY: move to the next token.
            if token not in valid:  # WHY: a repeated serial is queried once.
                valid.append(token)  # WHY: keep the first occurrence.
        return valid, rejected  # WHY: the checked serials and the rejects.

    def execute(self) -> None:
        """Ask for the serial numbers, query them in batches, and write the two exports."""
        mh = SourceDependencyResolver  # WHY: the shared input helper.
        raw = mh.InputUtils.safe_input(  # WHY: the prompt uses the safe input helper.
            "Enter serial numbers, separated by commas or spaces (Enter to cancel): ",
            default_value="",
            allow_empty=True,
            context="juniper_asset_input",
        )
        serials, rejected = self.parse_serials(raw)  # WHY: check the input before any call.
        if rejected:  # WHY: one bad token stops the run before any call.
            logger.warning(  # WHY: the count only, never the rejected values.
                "Input rejected: the lookup could not run, because %d token(s) break "  # The first half of the message.
                "the 1 to 40 character rule.",  # The rule, not the values.
                len(rejected),  # The count only, never the rejected values.
            )
            return  # WHY: nothing was sent.
        if not serials:  # WHY: a blank input cancels the run.
            logger.info("Juniper asset lookup cancelled: no serial numbers entered")  # WHY: the operator sees it.
            return  # WHY: nothing to query.
        self._run_query(serials)  # WHY: the batched read and the exports.

    def _run_query(self, serials: list[str]) -> None:
        """Query the serial numbers, write the exports, and report the counts."""
        logger.info("Juniper asset lookup for %d serial number(s)", len(serials))  # WHY: count only.
        try:  # WHY: a token or transport failure is reported, not raised.
            result = self._session.asset.query_all(serials)  # WHY: batched reads with partial results.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error("Juniper asset lookup failed to complete: %s", error)  # WHY: the operator sees the reason.
            return  # WHY: no exports.
        retrieved = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: one time for the rows.
        asset_rows = [ExportRowBuilder.asset_row(AssetRecord.from_api(raw), retrieved) for raw in result.assets]  # WHY.
        coverage_rows = [
            ExportRowBuilder.coverage_row(row, retrieved)  # WHY: one row for each warranty or contract line.
            for raw in result.assets
            for row in AssetCoverageRow.from_asset(raw)
        ]
        self._write(
            "JuniperAssets.csv", asset_rows, "juniperQueryAssetsDetails", ExportRowBuilder.ASSET_FIELDS
        )  # WHY: assets.
        self._write(  # WHY: coverage rows have their own key, so they get their own strategy.
            "JuniperAssetCoverage.csv", coverage_rows, "juniperQueryAssetCoverage", ExportRowBuilder.COVERAGE_FIELDS
        )
        self._report(result, len(serials))  # WHY: the summary and the problems.

    def _write(self, filename: str, rows: list[dict[str, Any]], api_name: str, fieldnames: list[str]) -> None:
        """Write one export through DataExporter. An empty output is logged, not written."""
        if not rows:  # WHY: DataExporter rejects empty data.
            logger.info("No rows for %s, so no file was written", filename)  # WHY: the operator sees the reason.
            return  # WHY: nothing to write.
        logger.info("Writing %d row(s) to %s", len(rows), filename)  # WHY: action log before the write.
        cleaned = ExportRowBuilder.ascii_rows(rows)  # WHY: FR-029 ASCII-only output before the write.
        self._exporter.write_with_format_selection(cleaned, filename, api_name, fieldnames=fieldnames)  # WHY: write.

    @staticmethod
    def _report(result: Any, requested: int) -> None:
        """Log the counts. Log at most five problems so the console stays readable."""
        logger.info(  # WHY: the summary line holds counts and the completeness flag only.
            "Juniper asset lookup: requested=%d found=%d not_found=%d not_processed=%d complete=%s",
            requested,
            len(result.assets),
            len(result.not_found),
            len(result.not_processed),
            result.is_complete,
        )
        for problem in result.problems[:5]:  # WHY: the first problems explain an incomplete run.
            logger.warning("%s", problem)  # WHY: the reason text only.
