"""Menu operation 277 -- export the organization switch scorecard."""

from __future__ import annotations  # WHY: postpone annotations for Python 3.13 runtime clarity.

import logging  # WHY: log each operation step for NOC troubleshooting.
from typing import Any  # WHY: exporter dependency is dynamic in tests.

from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: reach the shared exporter.
from src.reports.switch_scorecard.client import SwitchScorecardClient  # WHY: isolate Mist API access.
from src.reports.switch_scorecard.model import (  # WHY: pure scorecard math and stable column order.
    DETAIL_COLUMNS,
    SITE_COLUMNS,
    ScorecardOutput,
    SwitchScorecardBuilder,
    SwitchScorecardSettings,
)

logger = logging.getLogger(__name__)  # WHY: name this module in operation logs.

DETAIL_FILENAME = "SwitchScorecard.csv"  # WHY: the brief requires this detail output name.
SITE_FILENAME = "SwitchScorecardBySite.csv"  # WHY: the brief requires this site output name.
DETAIL_ENDPOINT_NAME = "switch_scorecard"  # WHY: wiring.md registers this report output.
SITE_ENDPOINT_NAME = "switch_scorecard_by_site"  # WHY: wiring.md registers this summary output.


class SwitchScorecard:
    """Run the organization switch scorecard report."""

    @staticmethod
    def run() -> None:
        """Fetch switch stats, build scorecards, and write both outputs."""
        logger.info("Menu #277: Starting the organization switch scorecard")  # WHY: name the menu operation.
        client = SwitchScorecardClient()  # WHY: the operation owns the production client.
        rows = client.list_switch_stats()  # WHY: fetch raw switch runtime evidence.
        settings = SwitchScorecardSettings.from_environment()  # WHY: resolve the AP threshold once per run.
        output = SwitchScorecardBuilder.build(rows, settings)  # WHY: transform API rows into report rows.
        SwitchScorecard._write_outputs(output, SourceDependencyResolver.DataExporter)  # WHY: shared export backend.
        SwitchScorecard._print_summary(output, settings.fallback_note)  # WHY: console summary closes the run.
        logger.info("Menu #277: Finished the organization switch scorecard")  # WHY: log successful completion.

    @staticmethod
    def _write_outputs(output: ScorecardOutput, exporter: Any) -> None:
        """Write the detail and site summary outputs."""
        logger.info("Switch scorecard writes %s rows to %s", len(output.detail_rows), DETAIL_FILENAME)
        detail_written = exporter.write_with_format_selection(
            output.detail_rows,
            DETAIL_FILENAME,
            api_function_name=DETAIL_ENDPOINT_NAME,
            fieldnames=DETAIL_COLUMNS,
        )  # WHY: use the shared multi-backend export path.
        logger.debug("Switch scorecard detail export written=%s", detail_written)  # WHY: record export result.
        logger.info("Switch scorecard writes %s rows to %s", len(output.site_rows), SITE_FILENAME)
        site_written = exporter.write_with_format_selection(
            output.site_rows,
            SITE_FILENAME,
            api_function_name=SITE_ENDPOINT_NAME,
            fieldnames=SITE_COLUMNS,
        )  # WHY: use the same backend for the summary file.
        logger.debug("Switch scorecard site export written=%s", site_written)  # WHY: record export result.

    @staticmethod
    def _print_summary(output: ScorecardOutput, fallback_note: str) -> None:
        """Print the organization-wide tile summary."""
        summary = output.org_summary  # WHY: model and console must use the same counts.
        if fallback_note:  # WHY: invalid environment input must be visible to the operator.
            logger.warning("%s", fallback_note)  # WHY: route the notice through the configured logger.
        logger.info("Switch scorecard organization switch count: %s", summary.get("switch_count", 0))
        logger.info(
            "Switch scorecard org percentages: affinity=%s poe=%s version=%s uptime=%s config=%s anomalies=%s",
            summary.get("switch_ap_affinity_percent", 0.0),
            summary.get("poe_compliance_percent", 0.0),
            summary.get("version_compliance_percent", 0.0),
            summary.get("switch_uptime_percent", 0.0),
            summary.get("config_success_percent", 0.0),
            summary.get("potential_anomalies_percent", 0.0),
        )  # WHY: the operator requested an organization-wide console summary.
