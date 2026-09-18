"""Menu operation 269 -- scan one organization for every rogue DHCP server.

Why:
    A NOC engineer needs one answer to one question: does any switch in this
    organization report a rogue DHCP server now, or did one report it in the
    last 30 days? This module is the entry point that the menu row, the command
    line, and the operations web dashboard all call.

Output:
    The operation prints one table, writes ``OrgRogueDhcpServers.csv`` under the
    data directory, and writes the same rows to the configured database backend.
    ``DataExporter.write_with_format_selection`` picks the backend and prompts
    for nothing, so the web dashboard path needs no special case.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the annotations in this module.

import logging  # WHY: log an action before each step and a summary after it.
from datetime import UTC, datetime  # WHY: print the window bounds as readable times.

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: reach the shared session, config helper, and exporter without the root module.
)
from src.security.rogue_dhcp.records import STATE_ACTIVE, RogueDhcpFinding
from src.security.rogue_dhcp.scanner import DEFAULT_WINDOW_DAYS, RogueDhcpScanner, RogueDhcpScanResult

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader filters by source.

EXPORT_FILENAME = "OrgRogueDhcpServers.csv"  # WHY: the data directory holds one file for this operation.
EXPORT_ENDPOINT_NAME = "scanOrgRogueDhcpServers"  # WHY: the primary key strategy registers under this name.

# WHY: the operator must read a clear result when the organization is clean, not an empty table.
NO_FINDING_MESSAGE = "No rogue DHCP server signal was found in this organization for the scan window."


class RogueDhcpScanOperation:
    """Run the rogue DHCP scan and report the result to the operator.

    Why:
        One class holds the organization resolution, the console report, and
        the export call, so the menu row points at one method.
    """

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the organization the scan covers.

        Returns:
            The organization identifier from the cache, the environment, or a prompt.
        """
        logger.info("Rogue DHCP scan resolves the organization")  # WHY: action log before the lookup.
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: the shared helper.
        logger.debug("Rogue DHCP scan resolved the organization org=%s", org_id)  # WHY: result summary.
        return str(org_id)  # WHY: every downstream column stores the identifier as text.

    @staticmethod
    def _resolve_session() -> object:
        """Return the live mistapi session.

        Returns:
            The session the shared resolver holds.
        """
        return SourceDependencyResolver.apisession  # WHY: one shared session serves every endpoint call.

    @staticmethod
    def _readable_time(epoch_seconds: float) -> str:
        """Return an epoch second value as a readable UTC string.

        Args:
            epoch_seconds: The time as epoch seconds.

        Returns:
            The time as an ISO 8601 string in UTC.
        """
        return datetime.fromtimestamp(epoch_seconds, tz=UTC).isoformat()  # WHY: UTC avoids a local offset.

    @staticmethod
    def _report_row(finding: RogueDhcpFinding) -> str:
        """Return one printable line for one finding.

        Args:
            finding: One merged finding.

        Returns:
            One aligned line that names the site, the switch, the port, and the state.
        """
        return (  # WHY: a fixed width keeps the console table readable on a narrow terminal.
            f"  {finding.site_name[:22]:<22} {finding.device_name[:18]:<18} "
            f"{finding.device_mac[:12]:<12} {finding.port_id[:12]:<12} "
            f"{finding.state:<10} {finding.last_seen[:19]:<19} {finding.source}"
        )

    @classmethod
    def _print_report(cls, result: RogueDhcpScanResult) -> None:
        """Print the whole result to the operator.

        Args:
            result: The merged findings and the run counts.
        """
        logger.info(  # WHY: name the window before the table, so the operator knows the span.
            "Rogue DHCP scan window %s to %s",
            cls._readable_time(result.window_start),
            cls._readable_time(result.window_end),
        )
        active = sum(1 for finding in result.findings if finding.state == STATE_ACTIVE)  # WHY: lead with the risk.
        logger.info("Rogue DHCP scan found rows=%d active=%d", result.finding_count, active)  # WHY: headline count.
        logger.info(  # WHY: name the header once, so every following line aligns under it.
            "  %-22s %-18s %-12s %-12s %-10s %-19s %s",
            "SITE",
            "SWITCH",
            "MAC",
            "PORT",
            "STATE",
            "LAST SEEN",
            "SOURCE",
        )
        for finding in result.findings:  # WHY: one line for each merged finding.
            logger.info("%s", cls._report_row(finding))  # WHY: pass the built line, so the format holds.
        for source, count in sorted(result.source_counts.items()):  # WHY: report the contribution of each search.
            logger.info("Rogue DHCP source %s returned records=%d", source, count)
        logger.info("Rogue DHCP scan queried sites=%d failed=%d", len(result.sites_queried), len(result.sites_failed))
        if result.sites_failed:  # WHY: a failed site means the result is incomplete, so name every one.
            logger.warning("Rogue DHCP scan could not read these sites: %s", ", ".join(result.sites_failed))
        logger.info("%s", result.marvis_scope_note)  # WHY: state the Marvis scope limit on every run.

    @staticmethod
    def _export(result: RogueDhcpScanResult) -> bool:
        """Write the findings to the configured backend.

        Args:
            result: The merged findings.

        Returns:
            True when the write succeeded, or False when it did not.
        """
        rows = [finding.as_row() for finding in result.findings]  # WHY: the writer takes flat dicts.
        logger.info("Rogue DHCP scan writes rows=%d to %s", len(rows), EXPORT_FILENAME)  # WHY: action log.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # WHY: the shared export path.
            rows,
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,
            fieldnames=RogueDhcpFinding.column_names(),
        )
        logger.debug("Rogue DHCP scan export finished written=%s", written)  # WHY: result summary after the write.
        return bool(written)  # WHY: the caller reports a failed write to the operator.

    @classmethod
    def run(cls, window_days: int = DEFAULT_WINDOW_DAYS) -> None:
        """Scan the organization, print the result, and write the export.

        Args:
            window_days: The lookback length in days. The default is 30.
        """
        logger.info("Menu #269: Starting the organization rogue DHCP server scan")  # WHY: name the menu row.
        org_id = cls._resolve_org_id()  # WHY: every query needs the organization identifier.
        scanner = RogueDhcpScanner(cls._resolve_session(), org_id, window_days=window_days)  # WHY: build the scan.
        result = scanner.scan()  # WHY: run the whole fan-out and merge.
        cls._print_report(result)  # WHY: the operator reads the table before any file exists.
        if not result.findings:  # WHY: an empty result writes nothing, per the specification.
            logger.info("%s", NO_FINDING_MESSAGE)  # WHY: a clear message beats an empty file.
            return  # WHY: leave the data directory untouched when the scan found nothing.
        if not cls._export(result):  # WHY: a failed write must reach the operator, not only the log file.
            logger.error(  # WHY: a failed write must reach the operator, not only the log file.
                "Rogue DHCP scan could not write %s, so the console table holds the only copy", EXPORT_FILENAME
            )
            return  # WHY: do not report success after a failed write.
        logger.info("Completed the rogue DHCP scan and wrote results to %s", EXPORT_FILENAME)  # WHY: closing report.
