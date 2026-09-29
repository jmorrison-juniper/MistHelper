"""Menu 282 operation for the rogue wireless PCI evidence pack."""

from __future__ import annotations  # Enable modern annotation syntax.

import logging  # Log every operation step for NOC traceability.
from pathlib import Path  # Write the Markdown summary with platform-safe paths.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Resolve shared MistHelper services.
from src.reports.rogue_pci_evidence.client import RoguePciEvidenceClient  # Read Mist rogue evidence data.
from src.reports.rogue_pci_evidence.model import (  # Build pure evidence rows and summary text.
    EVIDENCE_COLUMNS,
    SETTINGS_COLUMNS,
    RoguePciEvidenceModel,
)

logger = logging.getLogger(__name__)  # Name the logger for this module.

EVIDENCE_FILE = "RogueEvidence.csv"  # Name the classified detection output.
SETTINGS_FILE = "RogueSiteSettings.csv"  # Name the site settings output.
SUMMARY_FILE = "RogueEvidenceSummary.md"  # Name the Markdown evidence output.
EVIDENCE_API_NAME = "rogue_pci_evidence_pack"  # Name the deferred primary key strategy.
SETTINGS_API_NAME = "rogue_pci_site_settings"  # Name the deferred settings strategy.


class RoguePciEvidencePack:
    """Run menu 282 and write the rogue wireless PCI evidence pack."""

    @staticmethod
    def _write_rows(rows: list[dict[str, object]], filename: str, api_name: str, columns: list[str]) -> bool:
        """Write CSV rows through the shared exporter or create an empty template."""
        logger.info("Writing %d rows to %s", len(rows), filename)  # Log before the file write.
        if rows:  # Use the shared exporter when data exists.
            written = SourceDependencyResolver.DataExporter.write_with_format_selection(
                rows, filename, api_function_name=api_name, fieldnames=columns
            )  # Write through configured backends.
            logger.debug("Finished writing %s with result=%s", filename, written)  # Log after the file write.
            return bool(written)  # Return the exporter result.
        SourceDependencyResolver.FilePathUtils.create_csv_template(
            filename, columns
        )  # Create an empty CSV with headers.
        logger.debug("Created empty evidence template %s", filename)  # Log after the template write.
        return True  # Treat an empty template as a successful evidence write.

    @staticmethod
    def _write_summary(summary_text: str) -> Path:
        """Write the Markdown summary under the data directory."""
        logger.info("Writing rogue PCI summary to %s", SUMMARY_FILE)  # Log before the summary write.
        summary_path = Path(
            SourceDependencyResolver.FilePathUtils.get_csv_path(SUMMARY_FILE)
        )  # Reuse data path helper.
        summary_path.write_text(summary_text, encoding="utf-8")  # Write the Markdown evidence statement.
        logger.debug("Wrote rogue PCI summary bytes=%d", len(summary_text.encode("utf-8")))  # Log after the write.
        return summary_path  # Return the path for the closing log.

    @staticmethod
    def run() -> None:
        """Read Mist rogue data and write the PCI evidence pack."""
        logger.info("Menu #282: Starting the rogue and PCI evidence pack")  # Log operation start.
        org_id = str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id())  # Resolve the org.
        page_limit = int(SourceDependencyResolver.DEFAULT_API_PAGE_LIMIT)  # Read the shared page limit.
        client = RoguePciEvidenceClient(SourceDependencyResolver.apisession, org_id, page_limit)  # Build the client.
        wlans = client.list_org_wlans()  # Read WLANs for approved SSID matching.
        sites = client.list_org_sites()  # Read sites for coverage and per-site queries.
        raw_detections = client.list_site_rogue_aps(sites)  # Read the raw rogue AP detections.
        settings_by_site = client.list_site_settings(sites)  # Read one site setting per site with pacing.
        context = RoguePciEvidenceModel.build_context(org_id, wlans, sites, raw_detections)  # Build shared lookups.
        detection_rows = RoguePciEvidenceModel.detection_rows(raw_detections, context)  # Classify detection rows.
        setting_rows = RoguePciEvidenceModel.setting_rows(sites, settings_by_site, context)  # Build settings rows.
        summary_text = RoguePciEvidenceModel.summary_markdown(detection_rows, setting_rows, context)  # Build summary.
        RoguePciEvidencePack._write_rows(
            detection_rows, EVIDENCE_FILE, EVIDENCE_API_NAME, EVIDENCE_COLUMNS
        )  # Write detections.
        RoguePciEvidencePack._write_rows(
            setting_rows, SETTINGS_FILE, SETTINGS_API_NAME, SETTINGS_COLUMNS
        )  # Write settings.
        summary_path = RoguePciEvidencePack._write_summary(summary_text)  # Write summary file.
        logger.info("Completed the rogue and PCI evidence pack at %s", summary_path)  # Log operation completion.
