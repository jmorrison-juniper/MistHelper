"""Operation handler for the organization access point scorecard."""

from __future__ import annotations  # WHY: keep annotations import-safe during MistHelper bootstrap.

import logging  # WHY: log each API, transform, and export action.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: use the shared session, org helper, and exporter.
)
from src.mist.intelligence.reports.ap_scorecard.client import ApScorecardClient
from src.mist.intelligence.reports.ap_scorecard.model import (
    AP_SCORECARD_COLUMNS,
    ORG_SUMMARY_FIELDS,
    SITE_SCORECARD_COLUMNS,
    OrganizationSummary,
    ap_rows_as_dicts,
    build_ap_rows,
    build_organization_summary,
    build_site_rows,
    site_rows_as_dicts,
)
from src.mist.intelligence.reports.switch_scorecard.site_lookup import (
    SiteNameLookup,
)  # WHY: live AP stats include site_id only.

logger = logging.getLogger(__name__)  # WHY: let operators filter AP scorecard operation messages.

AP_SCORECARD_FILENAME = "ApScorecard.csv"  # WHY: contract file name for AP detail rows.
SITE_SCORECARD_FILENAME = "ApScorecardBySite.csv"  # WHY: contract file name for site summary rows.
AP_SCORECARD_API_NAME = "ap_scorecard"  # WHY: deferred primary key strategy name.
SITE_SCORECARD_API_NAME = "ap_scorecard_by_site"  # WHY: deferred primary key strategy name.


class ApScorecard:
    """Run the organization access point scorecard export."""

    @staticmethod
    def run() -> None:
        """Fetch AP statistics, export scorecards, and log the organization summary."""
        logger.info("Menu #278: Starting the organization access point scorecard")  # WHY: name the menu row.
        org_id = str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id())  # WHY: shared helper.
        client = ApScorecardClient(SourceDependencyResolver.apisession, org_id)  # WHY: one API client for the run.
        logger.info("Fetching organization AP statistics for scorecard")  # WHY: log before the API read.
        source_rows = client.list_ap_stats()  # WHY: use the client and SDK pagination seam.
        logger.debug("Fetched organization AP statistics rows=%d", len(source_rows))  # WHY: summarize fetch.
        if not source_rows:  # WHY: no AP rows means every percentage would be misleading.
            logger.info("No access point statistics were found. No AP scorecard files were written.")  # WHY: clear.
            return  # WHY: stop before exports and summary.
        site_names = SiteNameLookup.fetch(org_id)  # WHY: enrich site names after proving AP rows exist.
        logger.info("Building AP scorecard detail rows")  # WHY: log before transformation.
        ap_rows = build_ap_rows(source_rows, org_id=org_id, site_names=site_names)  # WHY: include site names.
        logger.debug("Built AP scorecard detail rows=%d", len(ap_rows))  # WHY: summarize transformation.
        logger.info("Building AP scorecard site summary rows")  # WHY: log before transformation.
        site_rows = build_site_rows(ap_rows)  # WHY: model aggregates rows by site.
        logger.debug("Built AP scorecard site summary rows=%d", len(site_rows))  # WHY: summarize transformation.
        ApScorecard._export_detail(ap_rows_as_dicts(ap_rows))  # WHY: static run has no class parameter.
        ApScorecard._export_sites(site_rows_as_dicts(site_rows))  # WHY: static run has no class parameter.
        logger.info("Building AP scorecard organization summary")  # WHY: log before transformation.
        summary = build_organization_summary(ap_rows)  # WHY: model aggregates the org-wide percentages.
        logger.debug("Built AP scorecard organization summary ap_count=%d", summary.ap_count)  # WHY: count result.
        ApScorecard._log_summary(summary)  # WHY: static run has no class parameter.

    @staticmethod
    def _export_detail(rows: list[dict[str, object]]) -> None:
        """Export the AP detail rows."""
        logger.info("Writing %d AP scorecard rows to %s", len(rows), AP_SCORECARD_FILENAME)  # WHY: before export.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # WHY: shared backend path.
            rows,
            AP_SCORECARD_FILENAME,
            api_function_name=AP_SCORECARD_API_NAME,
            fieldnames=AP_SCORECARD_COLUMNS,
        )
        logger.debug("AP scorecard detail export returned written=%s", written)  # WHY: summarize export result.
        if not written:  # WHY: failed export must be visible to the operator.
            logger.error("MistHelper could not write %s. Read the export error above.", AP_SCORECARD_FILENAME)

    @staticmethod
    def _export_sites(rows: list[dict[str, object]]) -> None:
        """Export the AP site summary rows."""
        logger.info("Writing %d AP site scorecard rows to %s", len(rows), SITE_SCORECARD_FILENAME)  # WHY: before.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # WHY: shared backend path.
            rows,
            SITE_SCORECARD_FILENAME,
            api_function_name=SITE_SCORECARD_API_NAME,
            fieldnames=SITE_SCORECARD_COLUMNS,
        )
        logger.debug("AP site scorecard export returned written=%s", written)  # WHY: summarize export result.
        if not written:  # WHY: failed export must be visible to the operator.
            logger.error("MistHelper could not write %s. Read the export error above.", SITE_SCORECARD_FILENAME)

    @staticmethod
    def _log_summary(summary: OrganizationSummary) -> None:
        """Log the organization-wide summary for the operator."""
        logger.info("AP scorecard organization summary: AP count %d", summary.ap_count)  # WHY: show denominator.
        logger.info("%s: %.2f%%", ORG_SUMMARY_FIELDS[0], summary.connection_status_percent)  # WHY: tile output.
        logger.info("%s: %.2f%%", ORG_SUMMARY_FIELDS[1], summary.vlans_percent)  # WHY: tile output.
        logger.info("%s: %.2f%%", ORG_SUMMARY_FIELDS[2], summary.version_compliance_percent)  # WHY: tile output.
        logger.info("%s: %.2f%%", ORG_SUMMARY_FIELDS[3], summary.switch_redundancy_percent)  # WHY: tile output.
        logger.info("%s: %.2f%%", ORG_SUMMARY_FIELDS[4], summary.potential_anomalies_percent)  # WHY: tile output.
