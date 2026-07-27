"""Zone configuration analysis for Mist sites.

Analyzes location zone configurations and engagement/occupancy settings
across all sites to identify deviations from organizational norms.

Extracted from MistHelper.py for maintainability.
"""

from __future__ import annotations  # WHY: enable postponed annotation evaluation for cleaner type aliases

import logging  # WHY: module-level logger for action tracing
from collections.abc import Callable  # WHY: PEP 585 Callable type alias source
from datetime import datetime  # WHY: timestamp export filenames
from typing import Any, TypeGuard  # WHY: heterogeneous dict payloads + narrow bundle checks

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
GetOrgIdFn = Callable[[], str | None]  # WHY: dependency injection - resolve org id lazily
CheckStopFn = Callable[[], bool]  # WHY: dependency injection - cooperative cancellation
AllSitesFn = Callable[[str], list[dict[str, Any]]]  # WHY: dependency injection - site listing
SaveDataFn = Callable[..., None]  # WHY: dependency injection - CSV writer with named args

# ---------------------------------------------------------------------------
# Analysis constants (named to avoid magic numbers)
# ---------------------------------------------------------------------------
_COMMON_ZONE_PCT = 0.75  # WHY: zones present in >=75% of sites are considered "common"
_UNIQUE_ZONE_PCT = 0.10  # WHY: zones present in <=10% of sites are considered "unique"
_DEVIATION_MULT = 1.5  # WHY: zone count is a deviation if outside +/-1.5 std devs from mean
_DISPLAY_CAP = 10  # WHY: cap console listings so output stays readable
_BUSINESS_HOURS_CAP = 5  # WHY: only enumerate business-hours sites when the list is small
_WEEKDAYS = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")  # WHY: engagement.hours daily keys
_ANALYSIS_KEYS = ("zones", "engagement", "occupancy")  # WHY: canonical analysis bundle keys


class ZoneConfigurationAnalyzer:
    """Analyzes zone, engagement, and occupancy configurations across sites.

    Scans all sites in an organization and compares configurations to:
    - Identify sites with different zone counts than the norm
    - Find sites missing common zones present in most other sites
    - Detect unique zones that only appear in specific sites
    - Analyze engagement dwell tags and names for consistency
    - Compare occupancy settings across sites

    SECURITY: Read-only analysis, no configuration changes.
    """

    # Default engagement dwell tags (T-Mobile standard)
    DEFAULT_DWELL_TAGS = {  # WHY: baseline dwell tag ranges expected across the org
        "passerby": "1-300",  # WHY: 1s-5m dwell -> passing traffic
        "bounce": "301-14400",  # WHY: 5m-4h dwell -> brief visit
        "engaged": "14401-36000",  # WHY: 4h-10h dwell -> engaged visit
        "stationed": "36001-86400",  # WHY: 10h-24h dwell -> stationed / employee
    }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    @staticmethod
    def analyze(
        *,
        apisession: Any,
        get_org_id_fn: GetOrgIdFn,
        check_stop_fn: CheckStopFn,
        all_sites_fn: AllSitesFn,
        save_data_fn: SaveDataFn,
    ) -> None:
        """Run zone and engagement/occupancy configuration analysis across all sites."""
        _print_intro_banner()  # WHY: user-visible header for the analyzer
        logging.info("Starting zone and engagement configuration analysis across all sites...")  # WHY: audit trail
        current_org_id = get_org_id_fn()  # WHY: resolve active org id via injected callback
        if not _validate_org_id(current_org_id):  # WHY: cannot analyze without an org selection
            return  # WHY: precondition failed. Abort
        collected = _collect_all_data(  # WHY: gather zones + settings from every site
            apisession=apisession,
            org_id=current_org_id or "",
            all_sites_fn=all_sites_fn,
            check_stop_fn=check_stop_fn,
        )
        ZoneConfigurationAnalyzer._run_and_export(collected, save_data_fn)  # WHY: pattern analysis + CSV output
        logging.debug("analyze completed successfully")  # WHY: after-action trace for observability

    @staticmethod
    def _run_and_export(
        collected: tuple[dict[str, Any], dict[str, Any]],
        save_data_fn: SaveDataFn,
    ) -> None:
        """Run analyses, display, and export given the collected raw data."""
        site_zones, site_settings = collected  # WHY: unpack the two independent accumulators
        if not site_zones and not site_settings:  # WHY: bail if the API returned nothing usable
            print("! No data collected. Please verify sites exist.")  # WHY: guide the user
            logging.debug("analyze aborted: empty zone and settings collections")  # WHY: after-action trace
            return  # WHY: no data means nothing to analyze or export
        combined = _run_all_analyses(site_zones, site_settings)  # WHY: compute the three pattern analyses
        ZoneConfigurationAnalyzer._display_results(combined)  # WHY: render results to console
        ZoneConfigurationAnalyzer._export_results(  # WHY: persist rows to CSV via the injected writer
            combined,
            site_zones,
            site_settings,
            save_data_fn=save_data_fn,
        )

    # ------------------------------------------------------------------
    # Data collection helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_all_site_settings(
        *,
        apisession: Any,
        org_id: str,
        all_sites_fn: AllSitesFn,
        check_stop_fn: CheckStopFn,
    ) -> dict[str, Any]:
        """Collect engagement and occupancy settings from all sites."""
        import mistapi  # noqa: F811  # WHY: deferred import so tests can stub the module

        info_msg = "Fetching site settings for engagement/occupancy analysis..."  # WHY: banner literal reused below
        sites = _fetch_sites_or_warn(all_sites_fn, org_id, info_msg)  # WHY: shared warning path when empty
        if not sites:  # WHY: nothing to iterate when the org has no sites
            return {}  # WHY: empty result signals downstream callers to skip
        print(f"! Scanning engagement/occupancy settings for {len(sites)} sites...")  # WHY: progress banner
        site_settings = _scan_site_settings(apisession, mistapi, sites, check_stop_fn)  # WHY: loop extracted
        print(f"! Collected settings from {len(site_settings)} sites.")  # WHY: completion banner
        logging.debug("_collect_all_site_settings collected %d site records", len(site_settings))  # WHY: trace
        return site_settings  # WHY: hand collected settings back to caller

    @staticmethod
    def _collect_all_site_zones(
        *,
        apisession: Any,
        org_id: str,
        all_sites_fn: AllSitesFn,
        check_stop_fn: CheckStopFn,
    ) -> dict[str, Any]:
        """Collect zone configurations from all sites."""
        import mistapi  # noqa: F811  # WHY: deferred import so tests can stub the module

        sites = _fetch_sites_or_warn(all_sites_fn, org_id, "Fetching all sites in organization...")  # WHY: shared warn
        if not sites:  # WHY: nothing to iterate when the org has no sites
            return {}  # WHY: empty result signals downstream callers to skip
        print(f"! Found {len(sites)} sites. Scanning zone configurations...")  # WHY: progress banner
        counter = _ZoneCounter()  # WHY: track cumulative zone count for the summary print
        site_zones = _scan_site_zones(apisession, mistapi, sites, check_stop_fn, counter)  # WHY: loop extracted
        print(f"! Collected {counter.total} zones from {len(site_zones)} sites.")  # WHY: completion banner
        logging.debug("_collect_all_site_zones collected %d sites, %d zones", len(site_zones), counter.total)  # WHY
        return site_zones  # WHY: hand collected zones back to caller

    # ------------------------------------------------------------------
    # Pattern analysis helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _analyze_zone_patterns(
        site_zones: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze zone patterns to identify deviations from the norm."""
        logging.info("Analyzing zone patterns...")  # WHY: audit trail
        zone_frequency, all_zone_names, zone_counts = _accumulate_zone_frequency(site_zones)  # WHY: reduce inputs
        total_sites = len(site_zones)  # WHY: denominator for percent calculations
        sites_with_zones = sum(1 for c in zone_counts if c > 0)  # WHY: only count sites that reported any zone
        stats = _compute_zone_stats(zone_counts, total_sites, sites_with_zones)  # WHY: mean/median/stddev summary
        threshold = max(1, int(sites_with_zones * _COMMON_ZONE_PCT))  # WHY: >=75% cutoff for "common"
        common_zones = {n for n, c in zone_frequency.items() if c >= threshold}  # WHY: filter by frequency
        ctx = {  # WHY: single-dict input keeps helper under STRUCT-PARAMS budget
            "site_zones": site_zones,  # WHY: source zone map for lookups
            "zone_frequency": zone_frequency,  # WHY: pass through to result
            "all_zone_names": all_zone_names,  # WHY: pass through to result
            "common_zones": common_zones,  # WHY: pass through and used for missing lookup
            "stats": stats,  # WHY: mean/std_dev feed deviations
            "sites_with_zones": sites_with_zones,  # WHY: denominator for unique lookup
        }
        parts = _build_zone_pattern_parts(ctx)  # WHY: extracted deviations/missing/unique lookups keep this short
        logging.debug("_analyze_zone_patterns produced %d common", len(common_zones))  # WHY: trace pattern volume
        return _build_zone_analysis_result(parts)  # WHY: bundle parts into caller's expected result shape

    @staticmethod
    def _analyze_engagement_patterns(
        site_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze engagement dwell tag patterns to identify deviations."""
        logging.info("Analyzing engagement patterns...")  # WHY: audit trail
        accum = _EngagementAccumulator()  # WHY: encapsulate the four independent accumulator dicts

        for site_id, data in site_settings.items():  # WHY: single pass over each site's settings
            _process_engagement_site(site_id, data, accum)  # WHY: delegate per-site processing

        sorted_configs = sorted(accum.dwell_tag_configs.items(), key=lambda x: -len(x[1]))  # WHY: rank by count desc
        most_common = sorted_configs[0] if sorted_configs else (None, [])  # WHY: guard empty input
        dwell_deviations = _find_dwell_deviations(accum.dwell_tag_configs, most_common)  # WHY: sites off the norm

        logging.debug("_analyze_engagement_patterns produced %d configs", len(accum.dwell_tag_configs))  # WHY: trace
        return {  # WHY: bundled engagement analysis for downstream display/export
            "dwell_tag_configs": accum.dwell_tag_configs,  # WHY: config-key -> site list
            "most_common_config": most_common,  # WHY: (key, sites) of the dominant config
            "sites_with_dwell_deviations": dwell_deviations,  # WHY: sites diverging from the dominant config
            "dwell_tag_name_usage": accum.dwell_tag_name_usage,  # WHY: nested map of custom tag names
            "sites_with_custom_names": accum.sites_with_custom,  # WHY: sites that renamed any dwell tag
            "sites_with_business_hours": accum.sites_with_hours,  # WHY: sites that defined business hours
            "total_sites": len(site_settings),  # WHY: denominator for percentages downstream
        }

    @staticmethod
    def _analyze_occupancy_patterns(
        site_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze occupancy settings to identify deviations."""
        logging.info("Analyzing occupancy patterns...")  # WHY: audit trail
        accum = _OccupancyAccumulator()  # WHY: encapsulate the four accumulator fields

        for site_id, data in site_settings.items():  # WHY: single pass over each site's settings
            _process_occupancy_site(site_id, data, accum)  # WHY: delegate per-site processing

        sorted_configs = sorted(accum.occ_configs.items(), key=lambda x: -len(x[1]))  # WHY: rank by count desc
        most_common = sorted_configs[0] if sorted_configs else (None, [])  # WHY: guard empty input
        occ_deviations = _find_occupancy_deviations(accum.occ_configs, most_common)  # WHY: sites off the norm

        logging.debug("_analyze_occupancy_patterns produced %d configs", len(accum.occ_configs))  # WHY: trace
        return {  # WHY: bundled occupancy analysis for downstream display/export
            "occupancy_configs": accum.occ_configs,  # WHY: config-key -> site list
            "most_common_config": most_common,  # WHY: (key, sites) of the dominant config
            "sites_with_occupancy_deviations": occ_deviations,  # WHY: sites diverging from the dominant config
            "min_duration_values": accum.min_duration_values,  # WHY: histogram of min_duration values
            "analytic_enabled_count": accum.enabled_count,  # WHY: sites that enabled analytic
            "analytic_disabled_count": accum.disabled_count,  # WHY: sites that disabled analytic
            "total_sites": len(site_settings),  # WHY: denominator for percentages downstream
        }

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _display_results(combined: dict[str, Any]) -> None:
        """Display analysis results to console."""
        print("\n" + "=" * 60)  # WHY: visual separator before results
        print("ZONE & ENGAGEMENT CONFIGURATION ANALYSIS RESULTS")  # WHY: section header
        print("=" * 60)  # WHY: bottom of the header block

        ZoneConfigurationAnalyzer._display_zone_section(combined.get("zones", {}))  # WHY: render zone analysis
        ZoneConfigurationAnalyzer._display_engagement_section(combined.get("engagement", {}))  # WHY: render engagement
        ZoneConfigurationAnalyzer._display_occupancy_section(combined.get("occupancy", {}))  # WHY: render occupancy

        print("\n" + "=" * 60)  # WHY: closing separator to visually finish the section

    @staticmethod
    def _display_zone_section(zone_analysis: dict[str, Any]) -> None:
        """Display zone analysis section."""
        if not zone_analysis:  # WHY: nothing to render when zone analysis is missing/empty
            return  # WHY: leave the console untouched
        stats = zone_analysis.get("zone_count_stats", {})  # WHY: pull the summary stats for the header
        _print_zone_header(stats)  # WHY: emit the fixed-format zone summary lines
        _display_common_zones(zone_analysis, stats)  # WHY: list common zones and coverage
        _display_missing_zones(zone_analysis)  # WHY: list sites missing common zones
        _display_zone_deviations(zone_analysis)  # WHY: list sites with count deviations

    @staticmethod
    def _display_engagement_section(
        engagement_analysis: dict[str, Any],
    ) -> None:
        """Display engagement analysis section."""
        if not engagement_analysis:  # WHY: nothing to render when engagement analysis is missing/empty
            return  # WHY: leave the console untouched
        print(f"\n{'=' * 60}")  # WHY: separator before engagement section
        print("[ENGAGEMENT ANALYSIS]")  # WHY: engagement section header
        print(f"{'=' * 60}")  # WHY: separator after header
        _display_dwell_configs(engagement_analysis)  # WHY: summarize dwell tag configs
        _display_dwell_deviations(engagement_analysis)  # WHY: list sites diverging from dominant config
        _display_custom_names(engagement_analysis)  # WHY: list sites with custom dwell tag names
        _display_business_hours(engagement_analysis)  # WHY: list sites with business hours defined

    @staticmethod
    def _display_occupancy_section(
        occupancy_analysis: dict[str, Any],
    ) -> None:
        """Display occupancy analysis section."""
        if not occupancy_analysis:  # WHY: nothing to render when occupancy analysis is missing/empty
            return  # WHY: leave the console untouched
        print(f"\n{'=' * 60}")  # WHY: separator before occupancy section
        print("[OCCUPANCY ANALYSIS]")  # WHY: occupancy section header
        print(f"{'=' * 60}")  # WHY: separator after header
        _print_analytics_status(occupancy_analysis)  # WHY: emit enabled/disabled counts + percentages
        _display_occupancy_configs(occupancy_analysis)  # WHY: summarize occupancy configs
        _display_occupancy_deviations(occupancy_analysis)  # WHY: list sites diverging from dominant config

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _export_results(
        combined: dict[str, Any],
        site_zones: dict[str, Any],
        site_settings: dict[str, Any],
        *,
        save_data_fn: SaveDataFn,
    ) -> None:
        """Export analysis results to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005  # WHY: local wall-clock filename stamp
        analyses = {  # WHY: bundle the three analyses to keep helper param counts low
            "zones": combined.get("zones", {}),  # WHY: zone analysis dict
            "engagement": combined.get("engagement", {}),  # WHY: engagement analysis dict
            "occupancy": combined.get("occupancy", {}),  # WHY: occupancy analysis dict
        }
        _export_summary(site_zones, site_settings, analyses, timestamp, save_data_fn)  # WHY: combined summary CSV
        _export_all_zones(site_zones, timestamp, save_data_fn)  # WHY: all-zones CSV
        _export_zone_frequency(analyses["zones"], timestamp, save_data_fn)  # WHY: frequency CSV
        _export_dwell_configs(analyses["engagement"], timestamp, save_data_fn)  # WHY: dwell config CSV
        _export_occupancy_configs(analyses["occupancy"], timestamp, save_data_fn)  # WHY: occupancy config CSV
        logging.info(  # WHY: audit trail with the shared timestamp used across every CSV
            "Site configuration analysis complete. Exported CSV files with timestamp %s",
            timestamp,
        )


# ======================================================================
# Module-private helper functions (keep class body lean)
# ======================================================================


class _ZoneCounter:
    """Mutable counter for total zones observed across sites (avoids nonlocal)."""

    __slots__ = ("total",)  # WHY: tiny fixed attribute set, avoid __dict__ overhead

    def __init__(self) -> None:
        """Initialize the running zone total to zero."""
        self.total = 0  # WHY: baseline count before any sites have been scanned


class _EngagementAccumulator:
    """Accumulator bundle for engagement analysis to keep helper params <= 5."""

    __slots__ = (  # WHY: fixed attribute set for the accumulator
        "dwell_tag_configs",
        "dwell_tag_name_usage",
        "sites_with_custom",
        "sites_with_hours",
    )

    def __init__(self) -> None:
        """Initialize empty accumulator dictionaries for engagement analysis."""
        self.dwell_tag_configs: dict[str, list[dict[str, Any]]] = {}  # WHY: config-key -> site list
        self.dwell_tag_name_usage: dict[str, dict[str, list[dict[str, Any]]]] = {}  # WHY: nested custom name usage
        self.sites_with_custom: dict[str, dict[str, Any]] = {}  # WHY: sites that renamed dwell tags
        self.sites_with_hours: dict[str, dict[str, Any]] = {}  # WHY: sites with business hours defined


class _OccupancyAccumulator:
    """Accumulator bundle for occupancy analysis to keep helper params <= 5."""

    __slots__ = (  # WHY: fixed attribute set for the accumulator
        "occ_configs",
        "min_duration_values",
        "enabled_count",
        "disabled_count",
    )

    def __init__(self) -> None:
        """Initialize empty accumulator dictionaries for occupancy analysis."""
        self.occ_configs: dict[str, list[dict[str, Any]]] = {}  # WHY: config-key -> site list
        self.min_duration_values: dict[Any, int] = {}  # WHY: histogram of min_duration values
        self.enabled_count = 0  # WHY: running total of sites with analytic enabled
        self.disabled_count = 0  # WHY: running total of sites with analytic disabled


def _print_intro_banner() -> None:
    """Print the initial banner shown when the analyzer starts."""
    print("Zone & Engagement Configuration Analyzer:")  # WHY: title of the tool
    print("=" * 60)  # WHY: visual divider under the title


def _print_zone_header(stats: dict[str, Any]) -> None:
    """Print the fixed-format zone summary block."""
    print(f"\n{'=' * 60}")  # WHY: separator before zone section
    print("[ZONE ANALYSIS]")  # WHY: zone section header
    print(f"{'=' * 60}")  # WHY: separator after header
    print("\n[Zone Summary]")  # WHY: sub-header for the descriptive statistics
    print(f"  Total sites scanned: {stats.get('total_sites', 0)}")  # WHY: total denominator
    print(f"  Sites with zones: {stats.get('sites_with_zones', 0)}")  # WHY: sites with any zones
    print(f"  Average zones per site: {stats.get('mean', 0):.1f}")  # WHY: mean value
    print(f"  Median zones per site: {stats.get('median', 0)}")  # WHY: median value
    print(f"  Range: {stats.get('min', 0)} - {stats.get('max', 0)}")  # WHY: min-max spread
    print(f"  Standard deviation: {stats.get('std_dev', 0):.2f}")  # WHY: spread measure


def _print_analytics_status(occupancy_analysis: dict[str, Any]) -> None:
    """Print the analytics enabled/disabled counts and percentages."""
    total = occupancy_analysis.get("total_sites", 0)  # WHY: denominator for percent calculations
    enabled = occupancy_analysis.get("analytic_enabled_count", 0)  # WHY: enabled count
    disabled = occupancy_analysis.get("analytic_disabled_count", 0)  # WHY: disabled count
    pct_e = enabled / total * 100 if total else 0  # WHY: guard against division by zero
    pct_d = disabled / total * 100 if total else 0  # WHY: guard against division by zero
    print("\n[Analytics Status]")  # WHY: sub-header for analytics counts
    print(f"  Enabled: {enabled} sites ({pct_e:.1f}%)")  # WHY: user-facing enabled line
    print(f"  Disabled: {disabled} sites ({pct_d:.1f}%)")  # WHY: user-facing disabled line


def _validate_org_id(current_org_id: str | None) -> bool:
    """Return True when ``current_org_id`` is usable. Emit abort message otherwise."""
    if current_org_id:  # WHY: any truthy id lets the analyzer proceed
        return True  # WHY: precondition satisfied
    print("! No organization selected. Exiting.")  # WHY: user-friendly abort message
    logging.debug("analyze aborted: no org id available")  # WHY: after-action trace
    return False  # WHY: signal caller to abort


def _collect_all_data(
    *,
    apisession: Any,
    org_id: str,
    all_sites_fn: AllSitesFn,
    check_stop_fn: CheckStopFn,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Collect both zone and settings data for the org."""
    site_zones = ZoneConfigurationAnalyzer._collect_all_site_zones(  # WHY: fetch all zone records
        apisession=apisession,  # WHY: reuse session
        org_id=org_id,  # WHY: scope to active org
        all_sites_fn=all_sites_fn,  # WHY: inject site listing
        check_stop_fn=check_stop_fn,  # WHY: honor cancellation
    )
    site_settings = ZoneConfigurationAnalyzer._collect_all_site_settings(  # WHY: fetch all settings records
        apisession=apisession,  # WHY: reuse session
        org_id=org_id,  # WHY: scope to active org
        all_sites_fn=all_sites_fn,  # WHY: inject site listing
        check_stop_fn=check_stop_fn,  # WHY: honor cancellation
    )
    return site_zones, site_settings  # WHY: return both collections as a tuple


def _run_all_analyses(
    site_zones: dict[str, Any],
    site_settings: dict[str, Any],
) -> dict[str, Any]:
    """Run all three pattern analyses when data is available."""
    zone_analysis = ZoneConfigurationAnalyzer._analyze_zone_patterns(site_zones) if site_zones else {}  # WHY: guard
    engagement_analysis = (  # WHY: guard against missing settings
        ZoneConfigurationAnalyzer._analyze_engagement_patterns(site_settings) if site_settings else {}
    )
    occupancy_analysis = (  # WHY: guard against missing settings
        ZoneConfigurationAnalyzer._analyze_occupancy_patterns(site_settings) if site_settings else {}
    )
    return {  # WHY: canonical bundle expected by display/export helpers
        "zones": zone_analysis,  # WHY: zone analysis payload
        "engagement": engagement_analysis,  # WHY: engagement analysis payload
        "occupancy": occupancy_analysis,  # WHY: occupancy analysis payload
    }


def _collect_one_setting(
    apisession: Any,
    mistapi: Any,
    site: dict[str, Any],
    site_settings: dict[str, Any],
) -> None:
    """Fetch and store one site's settings, handling non-200 responses and errors."""
    site_id = site.get("id")  # WHY: unique site key
    site_name = site.get("name", "Unnamed Site")  # WHY: fall back to a placeholder
    try:  # WHY: isolate per-site failures so one bad site does not abort the loop
        response = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id=site_id)  # WHY: fetch settings
        if response.status_code == 200:  # WHY: only trust successful HTTP responses
            site_settings[site_id] = _build_settings_entry(site_name, response.data)  # WHY: store good entry
            logging.debug("Site %s: settings collected", site_name)  # WHY: after-action trace
            return  # WHY: successful path complete
        logging.warning("Failed to fetch settings for %s: HTTP %s", site_name, response.status_code)  # WHY: log fail
    except Exception as error:  # WHY: any exception must be captured so the batch continues
        logging.warning("Error fetching settings for %s: %s", site_name, error)  # WHY: log with context
    site_settings[site_id] = _empty_settings_entry(site_name)  # WHY: placeholder entry for failed site


def _build_settings_entry(site_name: str, raw: Any) -> dict[str, Any]:
    """Normalize the setting payload into the expected shape."""
    data = raw if isinstance(raw, dict) else {}  # WHY: defensive - API sometimes returns non-dict
    engagement = data.get("engagement", {})  # WHY: pull engagement sub-tree
    return {  # WHY: normalized entry with all expected keys always present
        "site_name": site_name,  # WHY: keep site name attached for downstream display
        "engagement": {  # WHY: subset of engagement fields the analyzer uses
            "dwell_tags": engagement.get("dwell_tags", {}),  # WHY: numeric dwell ranges
            "dwell_tag_names": engagement.get("dwell_tag_names", {}),  # WHY: custom tag names
            "hours": engagement.get("hours", {}),  # WHY: business hours per weekday
        },
        "occupancy": data.get("occupancy", {}),  # WHY: raw occupancy dict
        "analytic": data.get("analytic", {}),  # WHY: raw analytic dict
    }


def _empty_settings_entry(site_name: str) -> dict[str, Any]:
    """Return a placeholder settings entry with all keys initialized empty."""
    return {  # WHY: default-shaped entry so downstream .get lookups always succeed
        "site_name": site_name,  # WHY: keep site name attached
        "engagement": {"dwell_tags": {}, "dwell_tag_names": {}, "hours": {}},  # WHY: empty engagement
        "occupancy": {},  # WHY: empty occupancy dict
        "analytic": {},  # WHY: empty analytic dict
    }


def _collect_one_zone(
    apisession: Any,
    mistapi: Any,
    site: dict[str, Any],
    site_zones: dict[str, Any],
    counter: _ZoneCounter,
) -> None:
    """Fetch and store one site's zones, handling non-200 responses and errors."""
    site_id = site.get("id")  # WHY: unique site key
    site_name = site.get("name", "Unnamed Site")  # WHY: fall back to a placeholder
    try:  # WHY: isolate per-site failures so one bad site does not abort the loop
        response = mistapi.api.v1.sites.zones.listSiteZones(apisession, site_id=site_id)  # WHY: fetch zones
        if response.status_code == 200:  # WHY: only trust successful HTTP responses
            zones = response.data if isinstance(response.data, list) else []  # WHY: defensive default
            _store_zone_result(site_id, site_name, zones, site_zones, counter)  # WHY: normalize + accumulate
            logging.debug("Site %s: %d zones", site_name, len(zones))  # WHY: after-action trace
            return  # WHY: successful path complete
        logging.warning("Failed to fetch zones for %s: HTTP %s", site_name, response.status_code)  # WHY: log fail
    except Exception as error:  # WHY: any exception must be captured so the batch continues
        logging.warning("Error fetching zones for %s: %s", site_name, error)  # WHY: log with context
    site_zones[site_id] = _empty_zone_entry(site_name)  # WHY: placeholder entry for failed site


def _store_zone_result(
    site_id: str,
    site_name: str,
    zones: list[dict[str, Any]],
    site_zones: dict[str, Any],
    counter: _ZoneCounter,
) -> None:
    """Store a good zone-listing response for a site and bump the running total."""
    zone_names = {zone.get("name", "Unnamed") for zone in zones}  # WHY: dedupe zone names
    site_zones[site_id] = {  # WHY: normalized zone entry
        "site_name": site_name,  # WHY: attach site name for display
        "zones": zones,  # WHY: keep raw zones for downstream export
        "zone_names": zone_names,  # WHY: set-of-names for fast membership checks
        "zone_count": len(zones),  # WHY: precomputed count for stats
    }
    counter.total += len(zones)  # WHY: bump running total for the completion banner


def _empty_zone_entry(site_name: str) -> dict[str, Any]:
    """Return a zero-zone placeholder for a site."""
    return {  # WHY: default-shaped entry so downstream .get lookups always succeed
        "site_name": site_name,  # WHY: keep site name attached
        "zones": [],  # WHY: empty zone list
        "zone_names": set(),  # WHY: empty name set
        "zone_count": 0,  # WHY: zero count
    }


def _progress(items: list[Any], desc: str, unit: str) -> Any:
    """Wrap items with tqdm progress bar."""
    from tqdm import tqdm  # WHY: deferred import so tests can stub tqdm cheaply

    return tqdm(items, desc=desc, unit=unit)  # WHY: return progress-wrapped iterator


def _fetch_sites_or_warn(all_sites_fn: AllSitesFn, org_id: str, info_msg: str) -> list[dict[str, Any]]:
    """Log ``info_msg``, fetch sites, warn when empty, and return the site list."""
    logging.info(info_msg)  # WHY: audit trail before hitting the API
    sites = all_sites_fn(org_id)  # WHY: pull the site list via injected helper
    if not sites:  # WHY: empty org means no work downstream
        logging.warning("No sites found in organization.")  # WHY: surface the empty case
    return sites or []  # WHY: normalize to list for caller iteration


def _scan_site_settings(
    apisession: Any, mistapi_mod: Any, sites: list[dict[str, Any]], check_stop_fn: CheckStopFn
) -> dict[str, Any]:
    """Iterate sites collecting engagement/occupancy settings with cooperative cancel."""
    site_settings: dict[str, Any] = {}  # WHY: accumulator for per-site payloads
    for site in _progress(sites, "Fetching site settings", "site"):  # WHY: iterate with tqdm progress
        if check_stop_fn():  # WHY: honor cooperative cancellation between sites
            logging.debug("_scan_site_settings stopping on user request")  # WHY: after-action trace
            break  # WHY: skip remaining sites when stop was requested
        _collect_one_setting(apisession, mistapi_mod, site, site_settings)  # WHY: delegate per-site fetch
    return site_settings  # WHY: return accumulated settings map


def _scan_site_zones(
    apisession: Any,
    mistapi_mod: Any,
    sites: list[dict[str, Any]],
    check_stop_fn: CheckStopFn,
    counter: _ZoneCounter,
) -> dict[str, Any]:
    """Iterate sites collecting zone configurations with cooperative cancel."""
    site_zones: dict[str, Any] = {}  # WHY: accumulator for per-site zone payloads
    for site in _progress(sites, "Scanning sites", "site"):  # WHY: iterate with tqdm progress
        if check_stop_fn():  # WHY: honor cooperative cancellation between sites
            logging.debug("_scan_site_zones stopping on user request")  # WHY: after-action trace
            break  # WHY: skip remaining sites when stop was requested
        _collect_one_zone(apisession, mistapi_mod, site, site_zones, counter)  # WHY: delegate per-site fetch
    return site_zones  # WHY: return accumulated zone map


def _build_zone_pattern_parts(ctx: dict[str, Any]) -> dict[str, Any]:
    """Compute the missing/unique/deviations lookups and package parts for the result bundler."""
    site_zones = ctx["site_zones"]  # WHY: unpack for readability below
    zone_frequency = ctx["zone_frequency"]  # WHY: unpack for readability below
    common_zones = ctx["common_zones"]  # WHY: unpack for readability below
    stats = ctx["stats"]  # WHY: unpack for readability below
    missing = _find_sites_missing_common(site_zones, common_zones)  # WHY: sites missing common zones
    unique = _find_sites_with_unique(site_zones, zone_frequency, ctx["sites_with_zones"])  # WHY: unique zones
    deviations = _find_zone_count_deviations(site_zones, stats["mean"], stats["std_dev"])  # WHY: outliers
    return {  # WHY: parts dict consumed by _build_zone_analysis_result
        "zone_frequency": zone_frequency,  # WHY: raw frequency counts per zone name
        "common_zones": common_zones,  # WHY: set of zones surpassing common threshold
        "missing": missing,  # WHY: sites missing at least one common zone
        "unique": unique,  # WHY: sites owning rare/unique zones
        "stats": stats,  # WHY: descriptive statistics for zone counts
        "deviations": deviations,  # WHY: sites deviating from expected zone count
        "all_zone_names": ctx["all_zone_names"],  # WHY: union of all observed zone names
    }


def _build_zone_analysis_result(parts: dict[str, Any]) -> dict[str, Any]:
    """Bundle zone-pattern outputs into the single result dict callers expect."""
    return {  # WHY: bundled analysis result for downstream display/export
        "zone_frequency": parts["zone_frequency"],  # WHY: raw frequency counts per zone name
        "common_zones": parts["common_zones"],  # WHY: set of zones surpassing common threshold
        "sites_missing_common_zones": parts["missing"],  # WHY: sites missing at least one common zone
        "sites_with_unique_zones": parts["unique"],  # WHY: sites owning rare/unique zones
        "zone_count_stats": parts["stats"],  # WHY: descriptive statistics for zone counts
        "zone_count_deviations": parts["deviations"],  # WHY: sites deviating from expected zone count
        "all_zone_names": parts["all_zone_names"],  # WHY: union of all observed zone names
    }


def _accumulate_zone_frequency(
    site_zones: dict[str, Any],
) -> tuple[dict[str, int], set[str], list[int]]:
    """Fold per-site zone lists into frequency, name-set, and count-list aggregates."""
    zone_frequency: dict[str, int] = {}  # WHY: name -> count of sites carrying it
    all_zone_names: set[str] = set()  # WHY: union of every zone name seen
    zone_counts: list[int] = []  # WHY: sequence of per-site zone totals for stats
    for data in site_zones.values():  # WHY: iterate every site's payload
        zone_counts.append(data["zone_count"])  # WHY: accumulate the count list
        for zone_name in data["zone_names"]:  # WHY: fold each observed zone into freq map
            all_zone_names.add(zone_name)  # WHY: track the union of names
            zone_frequency[zone_name] = zone_frequency.get(zone_name, 0) + 1  # WHY: bump frequency
    return zone_frequency, all_zone_names, zone_counts  # WHY: return the three aggregates as a tuple


def _compute_zone_stats(
    zone_counts: list[int],
    total_sites: int,
    sites_with_zones: int,
) -> dict[str, Any]:
    """Compute summary statistics for zone counts."""
    if not zone_counts:  # WHY: no data path returns all zeros
        return _empty_zone_stats(total_sites, sites_with_zones)  # WHY: canonical empty stats
    mean = sum(zone_counts) / len(zone_counts)  # WHY: arithmetic mean
    sorted_c = sorted(zone_counts)  # WHY: sort once for median lookup
    median = sorted_c[len(sorted_c) // 2]  # WHY: middle index (biased-high for even n, matches legacy)
    std_dev = _std_dev(zone_counts, mean)  # WHY: population std-dev with legacy semantics
    return {  # WHY: canonical stats dict
        "mean": mean,  # WHY: arithmetic mean of zone counts
        "median": median,  # WHY: median zone count
        "min": min(zone_counts),  # WHY: smallest zone count
        "max": max(zone_counts),  # WHY: largest zone count
        "std_dev": std_dev,  # WHY: spread measure
        "total_sites": total_sites,  # WHY: total site count
        "sites_with_zones": sites_with_zones,  # WHY: sites reporting at least one zone
    }


def _empty_zone_stats(total_sites: int, sites_with_zones: int) -> dict[str, Any]:
    """Return a zeroed-out stats dict for the no-data case."""
    return {  # WHY: same shape as _compute_zone_stats to keep callers simple
        "mean": 0.0,  # WHY: no data means zero mean
        "median": 0,  # WHY: no data means zero median
        "min": 0,  # WHY: no data means zero minimum
        "max": 0,  # WHY: no data means zero maximum
        "std_dev": 0.0,  # WHY: no data means zero spread
        "total_sites": total_sites,  # WHY: pass-through
        "sites_with_zones": sites_with_zones,  # WHY: pass-through
    }


def _std_dev(zone_counts: list[int], mean: float) -> float:
    """Return population standard deviation (matches legacy variance formula)."""
    if len(zone_counts) <= 1:  # WHY: variance is undefined for n<=1. Legacy returns 0
        return 0.0  # WHY: preserve prior behavior
    variance = sum((c - mean) ** 2 for c in zone_counts) / len(zone_counts)  # WHY: population variance
    return variance**0.5  # WHY: sqrt of variance is std dev


def _find_sites_missing_common(
    site_zones: dict[str, Any],
    common_zones: set[str],
) -> dict[str, Any]:
    """Find sites missing common zones."""
    result: dict[str, Any] = {}  # WHY: accumulator for site-id -> missing info
    for site_id, data in site_zones.items():  # WHY: iterate each site
        if data["zone_count"] <= 0:  # WHY: skip sites with no zones (nothing to compare)
            continue  # WHY: guard clause
        missing = common_zones - data["zone_names"]  # WHY: set difference finds gaps
        if missing:  # WHY: only record sites that actually miss common zones
            result[site_id] = {  # WHY: store report entry
                "site_name": data["site_name"],  # WHY: for display
                "missing_zones": missing,  # WHY: list of missing zone names
                "has_zones": data["zone_names"],  # WHY: which zones the site does have
            }
    return result  # WHY: hand accumulator back


def _find_sites_with_unique(
    site_zones: dict[str, Any],
    zone_frequency: dict[str, int],
    sites_with_zones: int,
) -> dict[str, Any]:
    """Find sites with zones that only appear in < 10% of sites."""
    threshold = max(1, int(sites_with_zones * _UNIQUE_ZONE_PCT))  # WHY: <=10% cutoff for "unique"
    result: dict[str, Any] = {}  # WHY: accumulator for site-id -> unique-zone info
    for site_id, data in site_zones.items():  # WHY: iterate each site
        unique = {n for n in data["zone_names"] if zone_frequency.get(n, 0) <= threshold}  # WHY: rare names
        if unique:  # WHY: only record sites with at least one rare zone
            result[site_id] = {  # WHY: store report entry
                "site_name": data["site_name"],  # WHY: for display
                "unique_zones": unique,  # WHY: which zones qualified as unique
                "zone_count": data["zone_count"],  # WHY: keep total count for context
            }
    return result  # WHY: hand accumulator back


def _find_zone_count_deviations(
    site_zones: dict[str, Any],
    mean: float,
    std_dev: float,
) -> dict[str, Any]:
    """Identify sites with zone counts > 1.5 std-dev from mean."""
    if std_dev <= 0:  # WHY: cannot compute deviations without spread
        return {}  # WHY: return empty dict for consistency with populated result
    result: dict[str, Any] = {}  # WHY: accumulator for deviation entries
    for site_id, data in site_zones.items():  # WHY: iterate every site
        entry = _zone_deviation_entry(data, mean, std_dev)  # WHY: build entry if deviant
        if entry:  # WHY: only record actual deviations
            result[site_id] = entry  # WHY: store deviation for the site
    return result  # WHY: hand accumulator back


def _zone_deviation_entry(
    data: dict[str, Any],
    mean: float,
    std_dev: float,
) -> dict[str, Any] | None:
    """Return a deviation entry when the site's zone count is an outlier."""
    count = data["zone_count"]  # WHY: current site's zone count
    deviation = abs(count - mean) / std_dev  # WHY: number of std devs from mean
    is_outlier = deviation > _DEVIATION_MULT or (count == 0 and mean > 0)  # WHY: cutoff or empty-outlier
    if not is_outlier:  # WHY: skip non-deviating sites
        return None  # WHY: signal caller to skip
    low = max(0, mean - _DEVIATION_MULT * std_dev)  # WHY: expected lower bound
    high = mean + _DEVIATION_MULT * std_dev  # WHY: expected upper bound
    return {  # WHY: deviation report entry
        "site_name": data["site_name"],  # WHY: for display
        "zone_count": count,  # WHY: actual count
        "deviation_score": round(deviation, 2),  # WHY: how many std devs off, rounded
        "expected_range": f"{low:.1f} - {high:.1f}",  # WHY: user-facing expected band
    }


def _dwell_config_key(dwell_tags: dict[str, Any]) -> str:
    """Create a hashable config string for dwell tag comparison."""
    return "|".join(  # WHY: pipe-delimited canonical form used as dict key
        [
            f"passerby={dwell_tags.get('passerby', 'N/A')}",  # WHY: include passerby range
            f"bounce={dwell_tags.get('bounce', 'N/A')}",  # WHY: include bounce range
            f"engaged={dwell_tags.get('engaged', 'N/A')}",  # WHY: include engaged range
            f"stationed={dwell_tags.get('stationed', 'N/A')}",  # WHY: include stationed range
        ]
    )


def _occupancy_config_key(occupancy: dict[str, Any]) -> str:
    """Create a hashable config string for occupancy comparison."""
    return "|".join(  # WHY: pipe-delimited canonical form used as dict key
        [
            f"min_duration={occupancy.get('min_duration', 'N/A')}",  # WHY: include min_duration
            f"clients_enabled={occupancy.get('clients_enabled', 'N/A')}",  # WHY: include clients toggle
            f"sdkclients_enabled={occupancy.get('sdkclients_enabled', 'N/A')}",  # WHY: include SDK toggle
            f"assets_enabled={occupancy.get('assets_enabled', 'N/A')}",  # WHY: include assets toggle
            f"unconnected_clients_enabled={occupancy.get('unconnected_clients_enabled', 'N/A')}",  # WHY: unconn flag
        ]
    )


def _process_engagement_site(
    site_id: str,
    data: dict[str, Any],
    accum: _EngagementAccumulator,
) -> None:
    """Fold one site's engagement data into the shared accumulator."""
    site_name = data["site_name"]  # WHY: keep name attached for downstream display
    engagement = data.get("engagement", {})  # WHY: pull engagement sub-tree
    dwell_tags = engagement.get("dwell_tags", {})  # WHY: numeric ranges
    dwell_tag_names = engagement.get("dwell_tag_names", {})  # WHY: custom names
    hours = engagement.get("hours", {})  # WHY: business hours

    config_key = _dwell_config_key(dwell_tags)  # WHY: canonical key for grouping identical configs
    accum.dwell_tag_configs.setdefault(config_key, []).append(  # WHY: append site record under its config key
        {"site_id": site_id, "site_name": site_name, "dwell_tags": dwell_tags},  # WHY: site record shape
    )
    _track_custom_names(site_id, site_name, dwell_tag_names, accum.dwell_tag_name_usage, accum.sites_with_custom)
    if any(hours.get(day) for day in _WEEKDAYS):  # WHY: only track sites that actually configured hours
        accum.sites_with_hours[site_id] = {"site_name": site_name, "hours": hours}  # WHY: record hours entry


def _track_custom_names(
    site_id: str,
    site_name: str,
    dwell_tag_names: dict[str, str],
    usage: dict[str, dict[str, list[dict[str, Any]]]],
    sites_with_custom: dict[str, dict[str, Any]],
) -> None:
    """Track custom dwell tag names across sites."""
    custom_pairs = _extract_custom_pairs(dwell_tag_names)  # WHY: pre-filter to only non-empty entries
    if not custom_pairs:  # WHY: nothing to record when no custom names exist
        return  # WHY: leave accumulators untouched
    for tag_type, custom_name in custom_pairs:  # WHY: register each surviving pair
        usage.setdefault(tag_type, {}).setdefault(custom_name, []).append(  # WHY: nested map by tag then name
            {"site_id": site_id, "site_name": site_name},  # WHY: reference entry
        )
    sites_with_custom[site_id] = {  # WHY: record that this site has at least one custom name
        "site_name": site_name,  # WHY: for display
        "custom_names": dict(custom_pairs),  # WHY: rebuild filtered dict
    }


def _extract_custom_pairs(dwell_tag_names: dict[str, str]) -> list[tuple[str, str]]:
    """Return only (tag_type, custom_name) pairs where the name is meaningfully set."""
    return [  # WHY: filter list comprehension keeps the caller trivial
        (tag_type, custom_name)  # WHY: preserve tag type + non-empty name
        for tag_type, custom_name in dwell_tag_names.items()  # WHY: iterate raw names
        if custom_name and custom_name.strip()  # WHY: skip empty/whitespace-only names
    ]


def _find_dwell_deviations(
    configs: dict[str, list[dict[str, Any]]],
    most_common: tuple[str | None, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Identify sites deviating from the most common dwell config."""
    if not most_common[0]:  # WHY: no dominant config -> no deviations
        return {}  # WHY: empty result short-circuits downstream logic
    expected = most_common[1][0]["dwell_tags"] if most_common[1] else {}  # WHY: pick expected from sample
    return _collect_deviant_sites(configs, most_common[0], expected, "dwell_tags")  # WHY: shared collector


def _find_occupancy_deviations(
    configs: dict[str, list[dict[str, Any]]],
    most_common: tuple[str | None, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Identify sites deviating from the most common occupancy config."""
    if not most_common[0]:  # WHY: no dominant config -> no deviations
        return {}  # WHY: empty result short-circuits downstream logic
    expected = most_common[1][0]["occupancy"] if most_common[1] else {}  # WHY: pick expected from sample
    return _collect_deviant_sites(configs, most_common[0], expected, "occupancy")  # WHY: shared collector


def _collect_deviant_sites(
    configs: dict[str, list[dict[str, Any]]],
    common_key: str,
    expected: dict[str, Any],
    source_field: str,
) -> dict[str, Any]:
    """Return a mapping of site_id -> deviation entry for non-dominant configs."""
    result: dict[str, Any] = {}  # WHY: accumulator for deviation entries
    for key, sites in configs.items():  # WHY: iterate every distinct config bucket
        if key == common_key:  # WHY: dominant bucket has no deviations
            continue  # WHY: guard clause
        for site in sites:  # WHY: iterate every site in a non-dominant bucket
            result[site["site_id"]] = {  # WHY: register deviation entry
                "site_name": site["site_name"],  # WHY: for display
                "current_config": site[source_field],  # WHY: the site's actual config
                "expected_config": expected,  # WHY: the expected (dominant) config
            }
    return result  # WHY: hand accumulator back


def _process_occupancy_site(
    site_id: str,
    data: dict[str, Any],
    accum: _OccupancyAccumulator,
) -> None:
    """Fold one site's occupancy data into the shared accumulator."""
    site_name = data["site_name"]  # WHY: keep name attached for downstream display
    occupancy = data.get("occupancy", {})  # WHY: pull occupancy sub-tree
    analytic = data.get("analytic", {})  # WHY: pull analytic sub-tree

    if analytic.get("enabled", False):  # WHY: tally enabled vs disabled analytics
        accum.enabled_count += 1  # WHY: bump enabled tally
    else:
        accum.disabled_count += 1  # WHY: bump disabled tally

    config_key = _occupancy_config_key(occupancy)  # WHY: canonical key for grouping identical configs
    accum.occ_configs.setdefault(config_key, []).append(  # WHY: append site record under its config key
        {"site_id": site_id, "site_name": site_name, "occupancy": occupancy},  # WHY: site record shape
    )
    md = occupancy.get("min_duration", "N/A")  # WHY: min_duration histogram key
    accum.min_duration_values[md] = accum.min_duration_values.get(md, 0) + 1  # WHY: bump histogram bucket


# ======================================================================
# Display helper functions
# ======================================================================


def _display_common_zones(zone_analysis: dict[str, Any], stats: dict[str, Any]) -> None:
    """Display common zones section."""
    common_zones = zone_analysis.get("common_zones", set())  # WHY: pull the set of common zone names
    print("\n[Common Zones] (Present in 75%+ of sites with zones)")  # WHY: sub-section header
    if not common_zones:  # WHY: distinct message for the empty case
        print("  No common zones found (high variation across sites)")  # WHY: user hint
        return  # WHY: nothing else to render
    sites_with_zones = stats.get("sites_with_zones", 1) or 1  # WHY: guard against divide-by-zero
    for name in sorted(common_zones):  # WHY: alphabetical output for deterministic display
        freq = zone_analysis.get("zone_frequency", {}).get(name, 0)  # WHY: lookup count for this zone
        pct = freq / sites_with_zones * 100  # WHY: coverage percentage
        print(f"  - {name} ({freq} sites, {pct:.0f}%)")  # WHY: user-facing line


def _display_missing_zones(zone_analysis: dict[str, Any]) -> None:
    """Display sites missing common zones."""
    missing = zone_analysis.get("sites_missing_common_zones", {})  # WHY: pull the missing-common map
    print(f"\n[Sites Missing Common Zones] ({len(missing)} sites)")  # WHY: sub-section header + count
    if not missing:  # WHY: distinct message for the empty case
        print("  All sites have the common zones configured")  # WHY: reassure the user
        return  # WHY: nothing else to render
    for data in list(missing.values())[:_DISPLAY_CAP]:  # WHY: cap listed sites
        print(f"  - {data['site_name']}")  # WHY: site name line
        print(f"    Missing: {', '.join(sorted(data['missing_zones']))}")  # WHY: names of missing zones
    if len(missing) > _DISPLAY_CAP:  # WHY: mention overflow when truncated
        print(f"  ... and {len(missing) - _DISPLAY_CAP} more sites")  # WHY: overflow indicator


def _display_zone_deviations(zone_analysis: dict[str, Any]) -> None:
    """Display zone count deviations."""
    devs = zone_analysis.get("zone_count_deviations", {})  # WHY: pull the deviation map
    print(f"\n[Zone Count Deviations] ({len(devs)} sites)")  # WHY: sub-section header + count
    if not devs:  # WHY: distinct message for the empty case
        print("  All sites have zone counts within expected range")  # WHY: reassure the user
        return  # WHY: nothing else to render
    for data in list(devs.values())[:_DISPLAY_CAP]:  # WHY: cap listed sites
        print(f"  - {data['site_name']}: {data['zone_count']} zones")  # WHY: site name + count
        print(  # WHY: give reviewer the expected zone-count range and deviation magnitude
            f"    Expected range: {data['expected_range']}, Deviation: {data['deviation_score']}x std dev",
        )
    if len(devs) > _DISPLAY_CAP:  # WHY: mention overflow when truncated
        print(f"  ... and {len(devs) - _DISPLAY_CAP} more sites")  # WHY: overflow indicator


def _display_dwell_configs(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display dwell tag configuration summary."""
    most_common = engagement_analysis.get("most_common_config", (None, []))  # WHY: (key, sites) tuple
    configs = engagement_analysis.get("dwell_tag_configs", {})  # WHY: full config map
    print("\n[Dwell Tag Configurations]")  # WHY: sub-section header
    print(f"  Total unique configurations: {len(configs)}")  # WHY: how many distinct configs exist
    if not (most_common[0] and most_common[1]):  # WHY: skip detail when no dominant config
        return  # WHY: header-only when nothing dominant
    print(f"  Most common config ({len(most_common[1])} sites):")  # WHY: how big the dominant bucket is
    tags = most_common[1][0].get("dwell_tags", {})  # WHY: sample tags from dominant config
    print(f"    passerby: {tags.get('passerby', 'N/A')}")  # WHY: user-facing passerby range
    print(f"    bounce: {tags.get('bounce', 'N/A')}")  # WHY: user-facing bounce range
    print(f"    engaged: {tags.get('engaged', 'N/A')}")  # WHY: user-facing engaged range
    print(f"    stationed: {tags.get('stationed', 'N/A')}")  # WHY: user-facing stationed range


def _display_dwell_deviations(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with dwell tag deviations."""
    devs = engagement_analysis.get("sites_with_dwell_deviations", {})  # WHY: pull deviation map
    print(f"\n[Sites with Dwell Tag Deviations] ({len(devs)} sites)")  # WHY: sub-section header + count
    if not devs:  # WHY: distinct message for the empty case
        print("  All sites have matching dwell tag configurations")  # WHY: reassure the user
        return  # WHY: nothing else to render
    for data in list(devs.values())[:_DISPLAY_CAP]:  # WHY: cap listed sites
        print(f"  - {data['site_name']}")  # WHY: site name line
        cur = data.get("current_config", {})  # WHY: pull the site's actual config
        print(f"    Current: passerby={cur.get('passerby', 'N/A')}, bounce={cur.get('bounce', 'N/A')}")  # WHY: line 1
        print(  # WHY: second line of the current dwell values (engaged/stationed)
            f"             engaged={cur.get('engaged', 'N/A')}, stationed={cur.get('stationed', 'N/A')}",
        )
    if len(devs) > _DISPLAY_CAP:  # WHY: mention overflow when truncated
        print(f"  ... and {len(devs) - _DISPLAY_CAP} more sites")  # WHY: overflow indicator


def _display_custom_names(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with custom dwell tag names."""
    custom = engagement_analysis.get("sites_with_custom_names", {})  # WHY: pull custom-names map
    print(f"\n[Sites with Custom Dwell Tag Names] ({len(custom)} sites)")  # WHY: sub-section header + count
    if not custom:  # WHY: distinct message for the empty case
        print("  No sites have custom dwell tag names configured")  # WHY: reassure the user
        return  # WHY: nothing else to render
    for data in list(custom.values())[:_DISPLAY_CAP]:  # WHY: cap listed sites
        print(f"  - {data['site_name']}")  # WHY: site name line
        for tag_type, name in data.get("custom_names", {}).items():  # WHY: enumerate the custom name pairs
            print(f"    {tag_type}: '{name}'")  # WHY: user-facing tag/name line
    if len(custom) > _DISPLAY_CAP:  # WHY: mention overflow when truncated
        print(f"  ... and {len(custom) - _DISPLAY_CAP} more sites")  # WHY: overflow indicator


def _display_business_hours(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with business hours configured."""
    hours = engagement_analysis.get("sites_with_business_hours", {})  # WHY: pull hours map
    print(f"\n[Sites with Business Hours Configured] ({len(hours)} sites)")  # WHY: sub-section header + count
    if not hours:  # WHY: distinct message for the empty case
        print("  No sites have business hours configured")  # WHY: reassure the user
        return  # WHY: nothing else to render
    if len(hours) <= _BUSINESS_HOURS_CAP:  # WHY: enumerate only when the list is short
        for data in hours.values():  # WHY: list each site by name
            print(f"  - {data['site_name']}")  # WHY: site name line
        return  # WHY: enumeration complete
    print(f"  {len(hours)} sites have business hours configured")  # WHY: summary when list is long


def _display_occupancy_configs(
    occupancy_analysis: dict[str, Any],
) -> None:
    """Display occupancy configuration summary."""
    most_common = occupancy_analysis.get("most_common_config", (None, []))  # WHY: (key, sites) tuple
    configs = occupancy_analysis.get("occupancy_configs", {})  # WHY: full config map
    print("\n[Occupancy Configurations]")  # WHY: sub-section header
    print(f"  Total unique configurations: {len(configs)}")  # WHY: how many distinct configs exist
    if most_common[0] and most_common[1]:  # WHY: only detail when a dominant config exists
        _print_dominant_occupancy(most_common)  # WHY: emit dominant occupancy detail block
    md_vals = occupancy_analysis.get("min_duration_values", {})  # WHY: histogram of min_duration
    if len(md_vals) > 1:  # WHY: only show histogram when more than one distinct value
        _print_min_duration_dist(md_vals)  # WHY: emit histogram lines


def _print_dominant_occupancy(most_common: tuple[str | None, list[dict[str, Any]]]) -> None:
    """Print the dominant occupancy config detail block."""
    print(f"  Most common config ({len(most_common[1])} sites):")  # WHY: how big the dominant bucket is
    occ = most_common[1][0].get("occupancy", {})  # WHY: sample occupancy from dominant config
    print(f"    min_duration: {occ.get('min_duration', 'N/A')}")  # WHY: min_duration line
    print(f"    clients_enabled: {occ.get('clients_enabled', 'N/A')}")  # WHY: clients toggle line
    print(f"    sdkclients_enabled: {occ.get('sdkclients_enabled', 'N/A')}")  # WHY: sdk clients toggle line
    print(f"    assets_enabled: {occ.get('assets_enabled', 'N/A')}")  # WHY: assets toggle line
    print(f"    unconnected_clients_enabled: {occ.get('unconnected_clients_enabled', 'N/A')}")  # WHY: unconn. toggle


def _print_min_duration_dist(md_vals: dict[Any, int]) -> None:
    """Print the min_duration histogram."""
    print("\n[Min Duration Distribution]")  # WHY: sub-section header
    for dur, count in sorted(md_vals.items(), key=lambda x: -x[1]):  # WHY: sort by count descending
        print(f"  {dur}: {count} sites")  # WHY: histogram line


def _display_occupancy_deviations(
    occupancy_analysis: dict[str, Any],
) -> None:
    """Display sites with occupancy config deviations."""
    devs = occupancy_analysis.get("sites_with_occupancy_deviations", {})  # WHY: pull deviation map
    print(f"\n[Sites with Occupancy Config Deviations] ({len(devs)} sites)")  # WHY: sub-section header + count
    if not devs:  # WHY: distinct message for the empty case
        print("  All sites have matching occupancy configurations")  # WHY: reassure the user
        return  # WHY: nothing else to render
    for data in list(devs.values())[:_DISPLAY_CAP]:  # WHY: cap listed sites
        print(f"  - {data['site_name']}")  # WHY: site name line
        cur = data.get("current_config", {})  # WHY: pull the site's actual config
        print(  # WHY: single condensed detail line
            f"    min_duration={cur.get('min_duration', 'N/A')},"  # WHY: min duration
            f" clients={cur.get('clients_enabled', 'N/A')},"  # WHY: clients toggle
            f" unconnected={cur.get('unconnected_clients_enabled', 'N/A')}"  # WHY: unconnected toggle
        )
    if len(devs) > _DISPLAY_CAP:  # WHY: mention overflow when truncated
        print(f"  ... and {len(devs) - _DISPLAY_CAP} more sites")  # WHY: overflow indicator


# ======================================================================
# Export helper functions
# ======================================================================


def _export_summary(
    site_zones: dict[str, Any],
    site_settings: dict[str, Any],
    *args: Any,
) -> None:
    """Export combined summary by site.

    Accepts either the modern bundle form ``(analyses_bundle, timestamp, save_data_fn)``
    (3 varargs) or the legacy positional form ``(zone_analysis, engagement, occupancy,
    timestamp, save_data_fn)`` (5 varargs) for backward compatibility with existing tests.
    """
    analyses, timestamp, save_data_fn = _unpack_export_args(args)  # WHY: dispatch on varargs shape
    rows = _build_summary_rows(site_zones, site_settings, analyses)  # WHY: assemble per-site summary rows
    if not rows:  # WHY: nothing to write when there is no data
        return  # WHY: early return keeps the writer inert
    filename = f"SiteConfigAnalysis_Summary_{timestamp}.csv"  # WHY: canonical timestamped filename
    save_data_fn(rows, filename, api_function_name="site_config_analysis_summary")  # WHY: hand off to writer
    print(f"! Summary exported to {filename}")  # WHY: user-visible confirmation
    logging.debug("_export_summary wrote %d rows", len(rows))  # WHY: after-action trace


def _unpack_export_args(args: tuple[Any, ...]) -> tuple[dict[str, dict[str, Any]], str, SaveDataFn]:
    """Dispatch on the length of ``args`` to yield (analyses, timestamp, save_data_fn)."""
    if len(args) == 3:  # WHY: modern bundle form: (analyses, timestamp, save_fn)
        return _normalize_analyses(args[0], None, None), args[1], args[2]  # WHY: bundle path
    if len(args) == 5:  # WHY: legacy triple form: (zone, engagement, occupancy, timestamp, save_fn)
        return _normalize_analyses(args[0], args[1], args[2]), args[3], args[4]  # WHY: legacy path
    raise TypeError(f"_export_summary expected 3 or 5 trailing args, got {len(args)}")  # WHY: fail loud


def _build_summary_rows(
    site_zones: dict[str, Any],
    site_settings: dict[str, Any],
    analyses: dict[str, dict[str, Any]] | None = None,
    engagement_analysis: dict[str, Any] | None = None,
    occupancy_analysis: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build the combined summary rows sorted by deviation.

    Callers may supply either a bundled ``analyses`` dict (preferred) or the
    legacy positional triple (zone/engagement/occupancy) for compatibility with
    existing tests.
    """
    analyses = _normalize_analyses(analyses, engagement_analysis, occupancy_analysis)  # WHY: keep legacy signature
    all_site_ids = set(site_zones.keys()) | set(site_settings.keys())  # WHY: union of every seen site id
    rows: list[dict[str, Any]] = []  # WHY: accumulator for row dicts
    for site_id in all_site_ids:  # WHY: iterate every unique site id
        zd = site_zones.get(site_id, _default_zone_data())  # WHY: fall back when zones missing
        sd = site_settings.get(site_id, _default_settings_data())  # WHY: fall back when settings missing
        rows.append(_build_one_summary_row(site_id, zd, sd, analyses))  # WHY: assemble row for site
    rows.sort(key=_summary_sort_key)  # WHY: deviated sites first, then alphabetical by name
    return rows  # WHY: hand rows back to caller


def _normalize_analyses(
    analyses: dict[str, dict[str, Any]] | None,
    engagement_analysis: dict[str, Any] | None,
    occupancy_analysis: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Accept either the bundled ``analyses`` dict or the legacy positional triple.

    Legacy callers passed (zone_analysis, engagement_analysis, occupancy_analysis)
    as separate arguments. The analyses parameter takes precedence when supplied
    as a dict shaped like ``{"zones": {...}, "engagement": {...}, "occupancy": {...}}``.
    """
    if _looks_like_bundle(analyses):  # WHY: bundle path is the modern convention
        return analyses  # WHY: TypeGuard on _looks_like_bundle narrowed the return type
    zone_analysis = analyses if isinstance(analyses, dict) else {}  # WHY: legacy first positional = zone analysis
    return {  # WHY: reshape legacy triple into the bundle form
        "zones": zone_analysis,  # WHY: legacy zone analysis
        "engagement": engagement_analysis or {},  # WHY: default to empty when omitted
        "occupancy": occupancy_analysis or {},  # WHY: default to empty when omitted
    }


def _looks_like_bundle(candidate: dict[str, Any] | None) -> TypeGuard[dict[str, dict[str, Any]]]:
    """Return True when ``candidate`` matches the canonical analyses bundle shape."""
    if not isinstance(candidate, dict):  # WHY: non-dicts cannot be bundles
        return False  # WHY: reject early
    return all(key in candidate for key in _ANALYSIS_KEYS)  # WHY: requires all three canonical keys


def _default_zone_data() -> dict[str, Any]:
    """Return the default zone-data shape used when a site has no zone record."""
    return {"site_name": "Unknown", "zone_count": 0, "zone_names": set()}  # WHY: consistent fallback shape


def _default_settings_data() -> dict[str, Any]:
    """Return the default settings-data shape used when a site has no settings record."""
    return {  # WHY: consistent fallback shape mirroring _empty_settings_entry
        "site_name": "Unknown",  # WHY: placeholder name
        "engagement": {},  # WHY: empty engagement sub-tree
        "occupancy": {},  # WHY: empty occupancy sub-tree
        "analytic": {},  # WHY: empty analytic sub-tree
    }


def _summary_sort_key(row: dict[str, Any]) -> tuple[bool, bool, bool, bool, str]:
    """Return a tuple used to sort summary rows: deviations first, name last."""
    return (  # WHY: leading False sorts before True in tuple ordering
        row["zone_deviation"] != "Yes",  # WHY: sites flagged for zone deviation first
        row["dwell_deviation"] != "Yes",  # WHY: then sites flagged for dwell deviation
        row["occupancy_deviation"] != "Yes",  # WHY: then sites flagged for occupancy deviation
        not row["missing_common_zones"],  # WHY: then sites missing common zones
        row["site_name"],  # WHY: finally alphabetical by name
    )


def _build_one_summary_row(
    site_id: str,
    zone_data: dict[str, Any],
    settings_data: dict[str, Any],
    *args: Any,
) -> dict[str, Any]:
    """Build a single summary row for one site.

    Callers may supply either the bundled ``analyses`` dict (1 vararg) or the
    legacy positional triple ``(zone_analysis, engagement, occupancy)`` (3 varargs).
    """
    analyses = _unpack_row_args(args)  # WHY: dispatch on varargs shape
    flags = _derive_row_flags(site_id, analyses)  # WHY: consolidate zone/dwell/occupancy signals
    site_name = zone_data.get("site_name") or settings_data.get("site_name", "Unknown")  # WHY: prefer zone name
    row = _base_summary_row(site_id, site_name, zone_data, flags["missing_common"], flags["has_zone_dev"])
    row.update(_dwell_row_fields(settings_data.get("engagement", {}), flags["has_dwell_dev"]))  # WHY: dwell columns
    row.update(
        _occupancy_row_fields(
            settings_data.get("occupancy", {}),
            settings_data.get("analytic", {}),
            flags["has_occ_dev"],
        )
    )  # WHY: occupancy columns
    return row  # WHY: fully assembled row


def _derive_row_flags(site_id: str, analyses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Extract per-site zone/dwell/occupancy deviation flags from the analyses bundle."""
    zone_analysis = analyses["zones"]  # WHY: zone-pattern piece of the bundle
    engagement_analysis = analyses["engagement"]  # WHY: engagement-pattern piece of the bundle
    occupancy_analysis = analyses["occupancy"]  # WHY: occupancy-pattern piece of the bundle
    missing_common = zone_analysis.get("sites_missing_common_zones", {}).get(site_id, {}).get("missing_zones", set())
    zone_dev = zone_analysis.get("zone_count_deviations", {}).get(site_id)  # WHY: presence indicates deviation
    has_dwell_dev = site_id in engagement_analysis.get("sites_with_dwell_deviations", {})  # WHY: bool flag
    has_occ_dev = site_id in occupancy_analysis.get("sites_with_occupancy_deviations", {})  # WHY: bool flag
    return {  # WHY: consolidated bundle for the caller to consume
        "missing_common": missing_common,  # WHY: names of common zones this site lacks
        "has_zone_dev": bool(zone_dev),  # WHY: coerce presence to boolean flag
        "has_dwell_dev": has_dwell_dev,  # WHY: dwell deviation flag
        "has_occ_dev": has_occ_dev,  # WHY: occupancy deviation flag
    }


def _unpack_row_args(args: tuple[Any, ...]) -> dict[str, dict[str, Any]]:
    """Dispatch on ``args`` length to yield the normalized analyses bundle."""
    if len(args) == 1:  # WHY: modern bundle form: (analyses,)
        return _normalize_analyses(args[0], None, None)  # WHY: bundle path
    if len(args) == 3:  # WHY: legacy triple: (zone, engagement, occupancy)
        return _normalize_analyses(args[0], args[1], args[2])  # WHY: legacy path
    if not args:  # WHY: no analyses supplied -> use empty bundle
        return _normalize_analyses(None, None, None)  # WHY: empty defaults
    raise TypeError(f"_build_one_summary_row expected 0, 1, or 3 trailing args, got {len(args)}")  # WHY: fail loud


def _base_summary_row(
    site_id: str,
    site_name: str,
    zone_data: dict[str, Any],
    missing_common: set[str],
    has_zone_dev: bool,
) -> dict[str, Any]:
    """Return the zone-related columns of the summary row."""
    return {  # WHY: base columns before dwell/occupancy fields are merged in
        "site_id": site_id,  # WHY: primary key
        "site_name": site_name,  # WHY: display name
        "zone_count": zone_data.get("zone_count", 0),  # WHY: number of zones at this site
        "zone_names": ", ".join(sorted(zone_data.get("zone_names", set()))),  # WHY: CSV-friendly list
        "missing_common_zones": (", ".join(sorted(missing_common)) if missing_common else ""),  # WHY: missing list
        "zone_deviation": "Yes" if has_zone_dev else "No",  # WHY: user-facing boolean
    }


def _dwell_row_fields(engagement: dict[str, Any], has_dwell_dev: bool) -> dict[str, Any]:
    """Return the dwell-tag columns of the summary row."""
    dwell_tags = engagement.get("dwell_tags", {})  # WHY: numeric ranges
    dwell_names = engagement.get("dwell_tag_names", {})  # WHY: custom names
    return {  # WHY: dwell columns for CSV
        "dwell_passerby": dwell_tags.get("passerby", ""),  # WHY: passerby range
        "dwell_bounce": dwell_tags.get("bounce", ""),  # WHY: bounce range
        "dwell_engaged": dwell_tags.get("engaged", ""),  # WHY: engaged range
        "dwell_stationed": dwell_tags.get("stationed", ""),  # WHY: stationed range
        "dwell_name_passerby": dwell_names.get("passerby", ""),  # WHY: custom passerby name
        "dwell_name_bounce": dwell_names.get("bounce", ""),  # WHY: custom bounce name
        "dwell_name_engaged": dwell_names.get("engaged", ""),  # WHY: custom engaged name
        "dwell_name_stationed": dwell_names.get("stationed", ""),  # WHY: custom stationed name
        "dwell_deviation": "Yes" if has_dwell_dev else "No",  # WHY: user-facing boolean
    }


def _occupancy_row_fields(
    occupancy: dict[str, Any],
    analytic: dict[str, Any],
    has_occ_dev: bool,
) -> dict[str, Any]:
    """Return the occupancy-related columns of the summary row."""
    return {  # WHY: occupancy columns for CSV
        "analytic_enabled": analytic.get("enabled", ""),  # WHY: analytic toggle
        "occupancy_min_duration": occupancy.get("min_duration", ""),  # WHY: min duration
        "occupancy_clients_enabled": occupancy.get("clients_enabled", ""),  # WHY: clients toggle
        "occupancy_sdkclients_enabled": occupancy.get("sdkclients_enabled", ""),  # WHY: sdk clients toggle
        "occupancy_assets_enabled": occupancy.get("assets_enabled", ""),  # WHY: assets toggle
        "occupancy_unconnected_enabled": occupancy.get("unconnected_clients_enabled", ""),  # WHY: unconn. toggle
        "occupancy_deviation": "Yes" if has_occ_dev else "No",  # WHY: user-facing boolean
    }


def _export_all_zones(
    site_zones: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export all zones with site context."""
    if not site_zones:  # WHY: nothing to export when no sites collected
        return  # WHY: leave writer inert
    rows = _build_all_zone_rows(site_zones)  # WHY: flatten to per-zone rows
    if not rows:  # WHY: possible when sites exist but none report zones
        return  # WHY: leave writer inert
    filename = f"SiteConfigAnalysis_AllZones_{timestamp}.csv"  # WHY: canonical timestamped filename
    save_data_fn(rows, filename, api_function_name="site_config_all_zones")  # WHY: hand off to writer
    print(f"! All zones exported to {filename}")  # WHY: user-visible confirmation
    logging.debug("_export_all_zones wrote %d rows", len(rows))  # WHY: after-action trace


def _build_all_zone_rows(site_zones: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one row per zone for the AllZones CSV."""
    rows: list[dict[str, Any]] = []  # WHY: accumulator for zone rows
    for site_id, data in site_zones.items():  # WHY: iterate every site
        for zone in data.get("zones", []):  # WHY: iterate zones inside a site
            rows.append(_zone_row(site_id, data.get("site_name", ""), zone))  # WHY: append normalized row
    return rows  # WHY: hand rows back to caller


def _zone_row(site_id: str, site_name: str, zone: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized CSV row for a single zone."""
    return {  # WHY: canonical row shape for AllZones CSV
        "site_id": site_id,  # WHY: parent site id
        "site_name": site_name,  # WHY: parent site name
        "zone_id": zone.get("id", ""),  # WHY: zone identifier
        "zone_name": zone.get("name", ""),  # WHY: zone display name
        "map_id": zone.get("map_id", ""),  # WHY: floor plan id
        "vertex_count": len(zone.get("vertices", [])),  # WHY: number of polygon vertices
        "created_time": zone.get("created_time", ""),  # WHY: creation timestamp
        "modified_time": zone.get("modified_time", ""),  # WHY: last modified timestamp
    }


def _export_zone_frequency(
    zone_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export zone frequency report."""
    freq = zone_analysis.get("zone_frequency")  # WHY: pull the frequency map
    if not freq:  # WHY: nothing to export when no frequency data
        return  # WHY: leave writer inert
    stats = zone_analysis.get("zone_count_stats", {})  # WHY: pull denominator source
    sites_with_zones = stats.get("sites_with_zones", 1) or 1  # WHY: guard against divide-by-zero
    common = zone_analysis.get("common_zones", set())  # WHY: pull common set for flag column
    rows = _build_freq_rows(freq, sites_with_zones, common)  # WHY: assemble sorted rows

    filename = f"SiteConfigAnalysis_ZoneFrequency_{timestamp}.csv"  # WHY: canonical timestamped filename
    save_data_fn(rows, filename, api_function_name="site_config_zone_frequency")  # WHY: hand off to writer
    print(f"! Zone frequency exported to {filename}")  # WHY: user-visible confirmation
    logging.debug("_export_zone_frequency wrote %d rows", len(rows))  # WHY: after-action trace


def _build_freq_rows(
    freq: dict[str, int],
    sites_with_zones: int,
    common: set[str],
) -> list[dict[str, Any]]:
    """Return one CSV row per zone name sorted by descending count."""
    rows: list[dict[str, Any]] = []  # WHY: accumulator for frequency rows
    for name, count in sorted(freq.items(), key=lambda x: -x[1]):  # WHY: descending count order
        pct = count / sites_with_zones * 100  # WHY: coverage percentage
        rows.append(  # WHY: append normalized frequency row
            {
                "zone_name": name,  # WHY: zone name column
                "site_count": count,  # WHY: how many sites have this zone
                "percentage": f"{pct:.1f}%",  # WHY: formatted percentage
                "is_common": "Yes" if name in common else "No",  # WHY: common flag
            }
        )
    return rows  # WHY: hand rows back to caller


def _export_dwell_configs(
    engagement_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export dwell tag configuration distribution."""
    configs = engagement_analysis.get("dwell_tag_configs")  # WHY: pull configs map
    if not configs:  # WHY: nothing to export when no configs collected
        return  # WHY: leave writer inert
    rows = _build_dwell_config_rows(configs)  # WHY: assemble rows sorted by size
    filename = f"SiteConfigAnalysis_DwellConfigs_{timestamp}.csv"  # WHY: canonical timestamped filename
    save_data_fn(rows, filename, api_function_name="site_config_dwell_configs")  # WHY: hand off to writer
    print(f"! Dwell configurations exported to {filename}")  # WHY: user-visible confirmation
    logging.debug("_export_dwell_configs wrote %d rows", len(rows))  # WHY: after-action trace


def _build_dwell_config_rows(configs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Return one CSV row per distinct dwell config sorted by bucket size."""
    rows: list[dict[str, Any]] = []  # WHY: accumulator for dwell rows
    for key, sites in sorted(configs.items(), key=lambda x: -len(x[1])):  # WHY: biggest buckets first
        sample = sites[0] if sites else {}  # WHY: representative site for this bucket
        tags = sample.get("dwell_tags", {})  # WHY: dwell ranges from the sample
        rows.append(  # WHY: append normalized dwell row
            {
                "configuration": key,  # WHY: canonical config key
                "site_count": len(sites),  # WHY: how many sites share this config
                "passerby": tags.get("passerby", ""),  # WHY: passerby range
                "bounce": tags.get("bounce", ""),  # WHY: bounce range
                "engaged": tags.get("engaged", ""),  # WHY: engaged range
                "stationed": tags.get("stationed", ""),  # WHY: stationed range
                "sample_sites": ", ".join(s["site_name"] for s in sites[:_BUSINESS_HOURS_CAP]),  # WHY: 5 example names
            }
        )
    return rows  # WHY: hand rows back to caller


def _export_occupancy_configs(
    occupancy_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export occupancy configuration distribution."""
    configs = occupancy_analysis.get("occupancy_configs")  # WHY: pull configs map
    if not configs:  # WHY: nothing to export when no configs collected
        return  # WHY: leave writer inert
    rows = _build_occupancy_config_rows(configs)  # WHY: assemble rows sorted by size
    filename = f"SiteConfigAnalysis_OccupancyConfigs_{timestamp}.csv"  # WHY: canonical timestamped filename
    save_data_fn(rows, filename, api_function_name="site_config_occupancy_configs")  # WHY: hand off to writer
    print(f"! Occupancy configurations exported to {filename}")  # WHY: user-visible confirmation
    logging.debug("_export_occupancy_configs wrote %d rows", len(rows))  # WHY: after-action trace


def _build_occupancy_config_rows(configs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Return one CSV row per distinct occupancy config sorted by bucket size."""
    rows: list[dict[str, Any]] = []  # WHY: accumulator for occupancy rows
    for key, sites in sorted(configs.items(), key=lambda x: -len(x[1])):  # WHY: biggest buckets first
        sample = sites[0] if sites else {}  # WHY: representative site for this bucket
        occ = sample.get("occupancy", {})  # WHY: occupancy fields from the sample
        rows.append(  # WHY: append normalized occupancy row
            {
                "configuration": key,  # WHY: canonical config key
                "site_count": len(sites),  # WHY: how many sites share this config
                "min_duration": occ.get("min_duration", ""),  # WHY: min duration column
                "clients_enabled": occ.get("clients_enabled", ""),  # WHY: clients toggle column
                "sdkclients_enabled": occ.get("sdkclients_enabled", ""),  # WHY: sdk clients toggle column
                "assets_enabled": occ.get("assets_enabled", ""),  # WHY: assets toggle column
                "unconnected_clients_enabled": occ.get("unconnected_clients_enabled", ""),  # WHY: unconn. toggle column
                "sample_sites": ", ".join(s["site_name"] for s in sites[:_BUSINESS_HOURS_CAP]),  # WHY: 5 example names
            }
        )
    return rows  # WHY: hand rows back to caller
