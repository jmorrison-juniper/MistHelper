"""Operation orchestration for the PSK hygiene report."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any, ClassVar, Protocol

from src.config.source_dependency_resolver import SourceDependencyResolver
from src.reports.psk_hygiene.client import PskHygieneClient
from src.reports.psk_hygiene.model import (
    HygieneSummary,
    PskHygieneRow,
    build_hygiene_rows,
    psk_inputs_from_records,
    wlan_references_from_records,
)
from src.utils.console import echo

logger = logging.getLogger(__name__)  # Keep operation logs tied to this module.


class PskHygieneClientProtocol(Protocol):
    """Define the client methods that the operation needs."""

    def fetch_psks(self) -> list[dict[str, Any]]:
        """Fetch organization PSK records."""

    def fetch_wlans(self) -> list[dict[str, Any]]:
        """Fetch organization WLAN records."""

    def fetch_templates(self) -> list[dict[str, Any]] | None:
        """Fetch organization template records."""


class PskHygieneReport:
    """Run the PSK hygiene report without prompts."""

    API_NAME = "psk_hygiene_report"  # Give DataExporter a stable report source name.
    FILENAME = "PskHygiene.csv"  # Keep the output file name aligned with the contract.
    CLIENT_CLASS: ClassVar[Any] = PskHygieneClient  # Allow tests to replace the client without changing run().
    DEPENDENCY_RESOLVER: ClassVar[Any] = SourceDependencyResolver  # Allow tests to replace shared runtime services.
    OUTPUT: ClassVar[Callable[[str], None]] = echo  # Allow tests to capture console summary lines.

    @classmethod
    def run(cls) -> bool:
        """Run the PSK hygiene report and return success."""
        logger.info("Resolving PSK hygiene report dependencies")  # Log before reading runtime dependencies.
        apisession = cls.DEPENDENCY_RESOLVER.apisession  # Reuse the authenticated Mist session from the app context.
        org_id = cls._resolve_org_id(cls.DEPENDENCY_RESOLVER)  # Resolve org id without any interactive prompt.
        if not org_id:  # Stop before any API call when non-interactive org resolution fails.
            return False  # Signal failure to menu test handling without prompting.
        report_client = cls.CLIENT_CLASS(apisession, org_id)  # Build the read-only client through the testable seam.
        logger.debug("Resolved PSK hygiene dependencies for one organization")  # Avoid logging the organization ID.
        rows, summary = cls._build_report(report_client)  # Fetch, sanitize, and score report data.
        cls._write_summary(summary, cls.OUTPUT)  # Print and log sanitized summary counts.
        cls._export_rows(cls.DEPENDENCY_RESOLVER, rows)  # Export sanitized rows through the configured backend.
        return True  # Signal success to menu test handling.

    @staticmethod
    def _resolve_org_id(resolver: Any) -> str | None:
        """Return a configured organization ID without a prompt."""
        cached_org_id = resolver.ConfigUtils.get_cached_org_id()  # Read the context or cache without prompting.
        org_id = cached_org_id or os.environ.get("org_id") or os.environ.get("ORG_ID")  # Use safe env fallback.
        if org_id:  # A configured organization lets the report run non-interactively.
            logger.debug("Resolved PSK hygiene organization without a prompt")  # Log source success without ID value.
            return str(org_id)  # Normalize the value for the SDK client.
        logger.error("PSK hygiene report needs org_id or ORG_ID before it can run without a prompt")  # Explain failure.
        return None  # Preserve the no-prompt contract.

    @staticmethod
    def _build_report(client: PskHygieneClientProtocol) -> tuple[list[dict[str, str | int | bool]], HygieneSummary]:
        """Fetch inputs and build sanitized report rows."""
        logger.info("Fetching PSK hygiene report inputs")  # Log before read-only input collection.
        raw_psks = client.fetch_psks()  # Read PSK records through the client boundary.
        raw_wlans = PskHygieneReport._fetch_wlan_scope(client)  # Read WLAN records, or mark the scope unknown.
        raw_templates = PskHygieneReport._fetch_template_scope(client)  # Read templates, or omit them safely.
        logger.debug(
            "Fetched PSK hygiene input counts: psks=%d, wlans=%d, templates=%d",
            len(raw_psks),
            -1 if raw_wlans is None else len(raw_wlans),
            -1 if raw_templates is None else len(raw_templates),
        )  # Log only safe counts.
        logger.info("Scoring sanitized PSK hygiene rows")  # Log before model transformations.
        psks = psk_inputs_from_records(raw_psks)  # Strip secrets before scoring.
        wlan_references = None if raw_wlans is None else wlan_references_from_records(raw_wlans, raw_templates or [])
        hygiene_rows = build_hygiene_rows(psks, wlan_references)  # Score each sanitized PSK.
        output_rows = [row.as_output_row() for row in hygiene_rows]  # Convert rows to exporter dictionaries.
        summary = HygieneSummary.from_rows(hygiene_rows)  # Build summary counts from the finding labels.
        logger.debug("Scored %d sanitized PSK hygiene rows", len(output_rows))  # Log only safe row count.
        return output_rows, summary  # Return sanitized rows and summary.

    @staticmethod
    def _fetch_wlan_scope(client: PskHygieneClientProtocol) -> list[dict[str, Any]] | None:
        """Fetch organization WLAN scope, or return None when unavailable."""
        try:
            return client.fetch_wlans()  # Use direct WLAN data when the endpoint succeeds.
        except Exception:
            logger.exception("PSK hygiene could not read organization WLANs; orphan SSID findings are unknown")
            return None  # Unknown scope must not create false orphan findings.

    @staticmethod
    def _fetch_template_scope(client: PskHygieneClientProtocol) -> list[dict[str, Any]] | None:
        """Fetch organization template scope, or return None when unavailable."""
        try:
            return client.fetch_templates()  # Use template data when the endpoint succeeds.
        except Exception:
            logger.exception("PSK hygiene could not read organization templates; template SSID matches are omitted")
            return None  # Missing template data must not stop the core PSK report.

    @staticmethod
    def _write_summary(summary: HygieneSummary, output: Callable[[str], None]) -> None:
        """Write the sanitized console and log summary."""
        logger.info("Writing PSK hygiene summary")  # Log before console output.
        for line in summary.to_lines():  # Print each summary line without secret values.
            output(line)  # Send summary text to the configured console function.
        logger.debug(
            "PSK hygiene summary counts: total=%d expired=%d expires_soon=%d uncapped_multi_use=%d "
            "rotation_pending=%d orphan_ssid=%d",
            summary.total_psks,
            summary.expired,
            summary.expires_soon,
            summary.uncapped_multi_use,
            summary.rotation_pending,
            summary.orphan_ssid,
        )  # Log only counts.

    @staticmethod
    def _export_rows(resolver: Any, rows: list[dict[str, str | int | bool]]) -> None:
        """Export sanitized rows through DataExporter."""
        logger.info("Exporting PSK hygiene rows")  # Log before the export write.
        resolver.DataExporter.write_with_format_selection(
            rows,
            PskHygieneReport.FILENAME,
            api_function_name=PskHygieneReport.API_NAME,
            fieldnames=PskHygieneRow.column_names(),
        )  # Write only sanitized rows through the configured backend.
        logger.debug("Exported %d PSK hygiene rows", len(rows))  # Log only the safe exported row count.
