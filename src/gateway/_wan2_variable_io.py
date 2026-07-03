"""IO cluster for :mod:`src.gateway.wan2_variable`.

Houses CSV/data loading, site filtering, template-assignment counting, and
the operation header printer. Split out from
:class:`GatewayWan2VariableMigrator` so the parent stays under the
STRUCT-LENGTH budget while each helper stays under CC/length limits.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import csv  # WHY: read Mist-exported CSV rows for templates and sites
import logging  # WHY: audit-log destructive Menu #104 flow

from ._wan2_variable_cluster import _ClusterBase  # WHY: parent-proxy pattern shared with peers


class _Wan2VariableIO(_ClusterBase):
    """CSV loading + site filtering helpers."""

    def _print_header(self) -> None:
        """Display operation header with mode-specific warnings."""
        print("\n  DESTRUCTIVE: Update Gateway Templates" " for WAN2 Variable Migration")  # WHY: banner line
        print("=" * 70)  # WHY: visual separator matches other menus
        if self._dry_run:  # WHY: dry-run mode gets safer copy
            self._print_dry_run_header()  # WHY: extracted helper keeps block count low
        else:  # WHY: live mode gets destructive warnings
            self._print_live_header()  # WHY: extracted helper keeps block count low
        print("=" * 70)  # WHY: closing separator

    @staticmethod
    def _print_dry_run_header() -> None:
        """Print the dry-run banner lines."""
        print("  >> DRY-RUN MODE: No changes will be made" " to templates or devices")  # WHY: mode indicator
        print("  >> This will show what WOULD be changed" " without modifying anything")  # WHY: expectations

    @staticmethod
    def _print_live_header() -> None:
        """Print the live-mode warning banner lines."""
        print("  !? WARNING: This operation modifies gateway templates")  # WHY: caution line
        print("  !? All sites using affected templates" " will inherit the change")  # WHY: scope warning
        print("  !? Ensure sites have 'wan2_interface'" " variable set (Menu #103)")  # WHY: prerequisite

    def _load_csv_data(
        self,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]] | None:
        """Load template and site CSV data, filter excluded sites."""
        print("\n  Loading gateway template data...")  # WHY: user progress feedback
        self._check_csv("OrgGatewayTemplates.csv", self._gen_templates)  # WHY: ensure freshness
        self._check_csv("SiteList.csv", self._gen_sites)  # WHY: ensure freshness
        template_rows = self._read_csv_rows("OrgGatewayTemplates.csv")  # WHY: helper handles read
        if not template_rows:  # WHY: empty file guard
            self._log_no_templates()  # WHY: helper logs the empty-result path
            return None  # WHY: signal empty result to caller
        all_sites = self._read_csv_rows("SiteList.csv")  # WHY: sites feed device migration
        sites = self._filter_excluded_sites(all_sites)  # WHY: apply SECURITY exclude prefix
        site_counts = self._count_template_assignments(sites)  # WHY: for template selection display
        return template_rows, sites, site_counts  # WHY: caller destructures triple

    def _read_csv_rows(self, filename: str) -> list[dict[str, str]]:
        """Read a CSV file from the export directory into a list of dicts."""
        path = self._get_csv_path(filename)  # WHY: resolves to configured export dir
        with open(path, encoding="utf-8") as csvfile:  # WHY: utf-8 covers exported site names
            return list(csv.DictReader(csvfile))  # WHY: caller iterates rows

    @staticmethod
    def _log_no_templates() -> None:
        """Emit the 'no templates' message and log line."""
        print(" No gateway templates found.")  # WHY: user-facing empty result
        logging.warning("No gateway templates available for modification")  # WHY: audit line

    def _filter_excluded_sites(self, all_sites: list[dict[str, str]]) -> list[dict[str, str]]:
        """Remove sites matching the exclusion prefix."""
        if not self._site_exclude_prefix:  # WHY: no prefix -> return unchanged list
            return all_sites  # WHY: fast path when no exclusion configured
        original_count = len(all_sites)  # WHY: track for log line
        filtered = [s for s in all_sites if not s.get("name", "").startswith(self._site_exclude_prefix)]
        excluded = original_count - len(filtered)  # WHY: how many sites got dropped
        if excluded > 0:  # WHY: only announce when exclusion actually applied
            self._announce_exclusion(excluded)  # WHY: extracted print/log helper
        return filtered  # WHY: caller consumes filtered list

    def _announce_exclusion(self, excluded: int) -> None:
        """Print SECURITY exclusion notice and matching audit log."""
        print(
            f"\n  !? SECURITY: Excluded {excluded}"
            f" '{self._site_exclude_prefix}*' sites"
            " from template impact analysis (early filter)"
        )  # WHY: user visibility on early filter
        logging.info(
            "Menu #104: Excluded %s sites matching prefix '%s' from WAN2 template operation",
            excluded,
            self._site_exclude_prefix,
        )  # WHY: audit trail entry

    @staticmethod
    def _count_template_assignments(
        sites: list[dict[str, str]],
    ) -> dict[str, int]:
        """Count how many sites are assigned to each template."""
        logging.info("Processing %s sites for template assignment counts", len(sites))  # WHY: log scope
        counts: dict[str, int] = {}  # WHY: template_id -> count map
        for site in sites:  # WHY: iterate every kept site
            tid = site.get("gatewaytemplate_id", "").strip()  # WHY: guard missing field
            if tid:  # WHY: skip unassigned sites
                counts[tid] = counts.get(tid, 0) + 1  # WHY: increment site count
        return counts  # WHY: consumed by selection cluster
