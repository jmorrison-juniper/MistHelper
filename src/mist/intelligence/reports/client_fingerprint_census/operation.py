"""Menu operation 289 -- export a site client fingerprint census."""

from __future__ import annotations  # WHY: allow modern type annotations in this operation.

import logging  # WHY: trace prompts, API reads, transforms, and exports.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: reach shared runtime services.
from src.mist.intelligence.reports.client_fingerprint_census.client import (
    ClientFingerprintCensusClient,
)  # WHY: isolate SDK calls.
from src.mist.intelligence.reports.client_fingerprint_census.model import (
    DISTINCT_FIELDS,
    EMPTY_CENSUS_MESSAGE,
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    FingerprintCensusModel,
    FingerprintCensusRow,
)

logger = logging.getLogger(__name__)  # WHY: name this operation in the shared log stream.


class ClientFingerprintCensus:
    """Run the client fingerprint census report for one Mist site."""

    @staticmethod
    def _resolve_site() -> tuple[str, str] | None:
        """Return the selected site identifier and name."""
        logger.info("Resolving site for client fingerprint census")  # WHY: action log before prompt.
        resolved = SourceDependencyResolver.SiteDeviceExporter._resolve_site_for_stats(  # WHY: reuse site prompt.
            "client fingerprint census"
        )
        logger.debug("Resolved client fingerprint census site=%s", resolved)  # WHY: result summary.
        return resolved  # WHY: caller stops when the operator cancels.

    @staticmethod
    def _prompt_distinct() -> str | None:
        """Ask the operator to choose one distinct fingerprint field."""
        logger.info("Offering client fingerprint distinct fields")  # WHY: action log before prompt.
        for index, field_name in enumerate(DISTINCT_FIELDS, start=1):  # WHY: show a numbered menu.
            logger.info("  [%d] %s", index, field_name)  # WHY: console prompt stays in the log stream.
        answer = str(  # WHY: safe_input returns a string-like value through the shared helper.
            SourceDependencyResolver.InputUtils.safe_input(
                f"Select a client fingerprint field (1-{len(DISTINCT_FIELDS)}): ",
                allow_empty=False,
                context="client_fingerprint_census.distinct",
            )
        ).strip()
        logger.debug("Client fingerprint distinct answer=%r", answer)  # WHY: trace non-secret input.
        if not answer.isdigit():  # WHY: non-numeric input cannot select the list.
            logger.info("No client fingerprint field selected. Returning to the menu.")  # WHY: user notice.
            return None  # WHY: caller stops without an API call.
        position = int(answer)  # WHY: convert after the digit guard.
        if not 1 <= position <= len(DISTINCT_FIELDS):  # WHY: avoid indexing outside the field list.
            logger.info("That client fingerprint field is not on the list. Returning to the menu.")  # WHY: notice.
            return None  # WHY: caller stops without an API call.
        distinct = DISTINCT_FIELDS[position - 1]  # WHY: menu choices are one-based.
        logger.debug("Selected client fingerprint distinct field=%s", distinct)  # WHY: result summary.
        return distinct  # WHY: caller passes this value to the API.

    @staticmethod
    def _print_report(rows: list[FingerprintCensusRow]) -> None:
        """Print the top census rows to the console."""
        logger.info("Printing client fingerprint census report")  # WHY: action log before console output.
        if not rows:  # WHY: empty reports need a clear statement, not a blank table.
            logger.info("%s", EMPTY_CENSUS_MESSAGE)  # WHY: acceptance criterion requires this message.
            return  # WHY: no table rows exist.
        logger.info("  %-24s %8s", "VALUE", "COUNT")  # WHY: aligned table header for the operator.
        for row in FingerprintCensusModel.top_rows(rows):  # WHY: cap the console table to the top 20 rows.
            logger.info("  %-24s %8d", row.value[:24], row.count)  # WHY: keep each row readable on a console.
        logger.debug("Printed client fingerprint census report rows=%d", min(len(rows), 20))  # WHY: summary.

    @staticmethod
    def _export(rows: list[FingerprintCensusRow]) -> bool:
        """Write the census rows through the shared exporter."""
        export_rows = [row.as_row() for row in rows]  # WHY: exporter consumes plain dictionaries.
        logger.info("Writing client fingerprint census rows=%d to %s", len(export_rows), EXPORT_FILENAME)
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # WHY: shared export path.
            export_rows,
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,
            fieldnames=FingerprintCensusRow.column_names(),
        )
        logger.debug("Client fingerprint census export finished written=%s", written)  # WHY: result summary.
        return bool(written)  # WHY: caller reports a failed write.

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the active organization identifier."""
        logger.info("Resolving organization for client fingerprint census")  # WHY: action log before context read.
        org_id = str(SourceDependencyResolver.org_id)  # WHY: direct menu execution already selected the org.
        logger.debug("Resolved client fingerprint census org_present=%s", bool(org_id))  # WHY: safe summary.
        return org_id  # WHY: the client needs the live organization path.

    @staticmethod
    def run() -> None:
        """Run the client fingerprint census operation."""
        logger.info("Menu #289: Starting the client fingerprint census")  # WHY: mark the selected menu row.
        resolved = ClientFingerprintCensus._resolve_site()  # WHY: the endpoint needs one site identifier.
        if resolved is None:  # WHY: no site means no safe API call.
            return  # WHY: resolver already logged the cancellation.
        distinct = ClientFingerprintCensus._prompt_distinct()  # WHY: the endpoint groups by one field.
        if distinct is None:  # WHY: no selected field means no safe API call.
            return  # WHY: prompt already logged the cancellation.
        site_id, site_name = resolved  # WHY: split identifiers for API and export rows.
        org_id = ClientFingerprintCensus._resolve_org_id()  # WHY: live fingerprint count path needs the org.
        client = ClientFingerprintCensusClient(SourceDependencyResolver.apisession, org_id)  # WHY: shared session.
        raw_rows = client.count(site_id, distinct)  # WHY: read the census from Mist.
        rows = FingerprintCensusModel.normalize_rows(raw_rows, site_id, site_name, distinct)  # WHY: export schema.
        ClientFingerprintCensus._print_report(rows)  # WHY: operator sees the result before the file path.
        if not ClientFingerprintCensus._export(rows):  # WHY: a failed export must reach the operator.
            logger.error("Client fingerprint census could not write %s", EXPORT_FILENAME)  # WHY: user warning.
