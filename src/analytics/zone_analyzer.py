"""Zone configuration analysis for Mist sites.

Analyzes location zone configurations and engagement/occupancy settings
across all sites to identify deviations from organizational norms.

Extracted from MistHelper.py for maintainability.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases for injected dependencies
# ---------------------------------------------------------------------------
GetOrgIdFn = Callable[[], str | None]
CheckStopFn = Callable[[], bool]
AllSitesFn = Callable[[str], list[dict[str, Any]]]
SaveDataFn = Callable[..., None]


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
    DEFAULT_DWELL_TAGS = {
        "passerby": "1-300",
        "bounce": "301-14400",
        "engaged": "14401-36000",
        "stationed": "36001-86400",
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
        """Run zone and engagement/occupancy configuration analysis.

        Args:
            apisession: Authenticated Mist API session.
            get_org_id_fn: Returns the current org ID or None.
            check_stop_fn: Returns True when the user requests a stop.
            all_sites_fn: Fetches all sites for an org ID.
            save_data_fn: Persists row data to the configured output.
        """
        print("Zone & Engagement Configuration Analyzer:")
        print("=" * 60)
        logging.info("Starting zone and engagement configuration analysis" " across all sites...")

        current_org_id = get_org_id_fn()
        if not current_org_id:
            print("! No organization selected. Exiting.")
            return

        site_zones = ZoneConfigurationAnalyzer._collect_all_site_zones(
            apisession=apisession,
            org_id=current_org_id,
            all_sites_fn=all_sites_fn,
            check_stop_fn=check_stop_fn,
        )

        site_settings = ZoneConfigurationAnalyzer._collect_all_site_settings(
            apisession=apisession,
            org_id=current_org_id,
            all_sites_fn=all_sites_fn,
            check_stop_fn=check_stop_fn,
        )

        if not site_zones and not site_settings:
            print("! No data collected. Please verify sites exist.")
            return

        zone_analysis = ZoneConfigurationAnalyzer._analyze_zone_patterns(site_zones) if site_zones else {}
        engagement_analysis = (
            ZoneConfigurationAnalyzer._analyze_engagement_patterns(
                site_settings,
            )
            if site_settings
            else {}
        )
        occupancy_analysis = (
            ZoneConfigurationAnalyzer._analyze_occupancy_patterns(
                site_settings,
            )
            if site_settings
            else {}
        )

        combined = {
            "zones": zone_analysis,
            "engagement": engagement_analysis,
            "occupancy": occupancy_analysis,
        }

        ZoneConfigurationAnalyzer._display_results(combined)
        ZoneConfigurationAnalyzer._export_results(
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
        import mistapi

        logging.info("Fetching site settings for engagement/occupancy analysis...")
        sites = all_sites_fn(org_id)

        if not sites:
            logging.warning("No sites found in organization.")
            return {}

        print(f"! Scanning engagement/occupancy settings" f" for {len(sites)} sites...")

        site_settings: dict[str, Any] = {}
        empty_settings: dict[str, Any] = {
            "engagement": {
                "dwell_tags": {},
                "dwell_tag_names": {},
                "hours": {},
            },
            "occupancy": {},
            "analytic": {},
        }

        for site in _progress(sites, "Fetching site settings", "site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unnamed Site")
            if check_stop_fn():
                break

            try:
                response = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id=site_id)
                if response.status_code == 200:
                    data = response.data if isinstance(response.data, dict) else {}
                    engagement = data.get("engagement", {})
                    site_settings[site_id] = {
                        "site_name": site_name,
                        "engagement": {
                            "dwell_tags": engagement.get("dwell_tags", {}),
                            "dwell_tag_names": engagement.get("dwell_tag_names", {}),
                            "hours": engagement.get("hours", {}),
                        },
                        "occupancy": data.get("occupancy", {}),
                        "analytic": data.get("analytic", {}),
                    }
                    logging.debug("Site %s: settings collected", site_name)
                else:
                    logging.warning(
                        "Failed to fetch settings for %s: HTTP %s",
                        site_name,
                        response.status_code,
                    )
                    site_settings[site_id] = {
                        "site_name": site_name,
                        **empty_settings,
                    }
            except Exception as error:
                logging.warning(
                    "Error fetching settings for %s: %s",
                    site_name,
                    error,
                )
                site_settings[site_id] = {
                    "site_name": site_name,
                    **empty_settings,
                }

        print(f"! Collected settings from {len(site_settings)} sites.")
        return site_settings

    @staticmethod
    def _collect_all_site_zones(
        *,
        apisession: Any,
        org_id: str,
        all_sites_fn: AllSitesFn,
        check_stop_fn: CheckStopFn,
    ) -> dict[str, Any]:
        """Collect zone configurations from all sites."""
        import mistapi

        logging.info("Fetching all sites in organization...")
        sites = all_sites_fn(org_id)

        if not sites:
            logging.warning("No sites found in organization.")
            return {}

        print(f"! Found {len(sites)} sites." " Scanning zone configurations...")

        site_zones: dict[str, Any] = {}
        zones_collected = 0

        for site in _progress(sites, "Scanning sites", "site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unnamed Site")
            if check_stop_fn():
                break

            try:
                response = mistapi.api.v1.sites.zones.listSiteZones(apisession, site_id=site_id)
                if response.status_code == 200:
                    zones = response.data if isinstance(response.data, list) else []
                    zone_names = {zone.get("name", "Unnamed") for zone in zones}
                    site_zones[site_id] = {
                        "site_name": site_name,
                        "zones": zones,
                        "zone_names": zone_names,
                        "zone_count": len(zones),
                    }
                    zones_collected += len(zones)
                    logging.debug("Site %s: %d zones", site_name, len(zones))
                else:
                    logging.warning(
                        "Failed to fetch zones for %s: HTTP %s",
                        site_name,
                        response.status_code,
                    )
                    site_zones[site_id] = _empty_zone_entry(site_name)
            except Exception as error:
                logging.warning("Error fetching zones for %s: %s", site_name, error)
                site_zones[site_id] = _empty_zone_entry(site_name)

        print(f"! Collected {zones_collected} zones" f" from {len(site_zones)} sites.")
        return site_zones

    # ------------------------------------------------------------------
    # Pattern analysis helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _analyze_zone_patterns(
        site_zones: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze zone patterns to identify deviations from the norm."""
        logging.info("Analyzing zone patterns...")

        zone_frequency: dict[str, int] = {}
        all_zone_names: set[str] = set()
        zone_counts: list[int] = []

        for data in site_zones.values():
            zone_counts.append(data["zone_count"])
            for zone_name in data["zone_names"]:
                all_zone_names.add(zone_name)
                zone_frequency[zone_name] = zone_frequency.get(zone_name, 0) + 1

        total_sites = len(site_zones)
        sites_with_zones = sum(1 for c in zone_counts if c > 0)

        stats = _compute_zone_stats(zone_counts, total_sites, sites_with_zones)
        mean_count = stats["mean"]
        std_dev = stats["std_dev"]

        threshold = max(1, int(sites_with_zones * 0.75))
        common_zones = {n for n, c in zone_frequency.items() if c >= threshold}

        missing = _find_sites_missing_common(site_zones, common_zones)
        unique = _find_sites_with_unique(site_zones, zone_frequency, sites_with_zones)
        deviations = _find_zone_count_deviations(site_zones, mean_count, std_dev)

        return {
            "zone_frequency": zone_frequency,
            "common_zones": common_zones,
            "sites_missing_common_zones": missing,
            "sites_with_unique_zones": unique,
            "zone_count_stats": stats,
            "zone_count_deviations": deviations,
            "all_zone_names": all_zone_names,
        }

    @staticmethod
    def _analyze_engagement_patterns(
        site_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze engagement dwell tag patterns to identify deviations."""
        logging.info("Analyzing engagement patterns...")

        dwell_tag_configs: dict[str, list[dict[str, Any]]] = {}
        dwell_tag_name_usage: dict[str, dict[str, list[dict[str, Any]]]] = {}
        sites_with_custom: dict[str, dict[str, Any]] = {}
        sites_with_hours: dict[str, dict[str, Any]] = {}

        for site_id, data in site_settings.items():
            site_name = data["site_name"]
            engagement = data.get("engagement", {})
            dwell_tags = engagement.get("dwell_tags", {})
            dwell_tag_names = engagement.get("dwell_tag_names", {})
            hours = engagement.get("hours", {})

            config_key = _dwell_config_key(dwell_tags)
            dwell_tag_configs.setdefault(config_key, []).append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "dwell_tags": dwell_tags,
                }
            )

            _track_custom_names(
                site_id,
                site_name,
                dwell_tag_names,
                dwell_tag_name_usage,
                sites_with_custom,
            )

            has_hours = any(hours.get(day) for day in ["sun", "mon", "tue", "wed", "thu", "fri", "sat"])
            if has_hours:
                sites_with_hours[site_id] = {
                    "site_name": site_name,
                    "hours": hours,
                }

        sorted_configs = sorted(dwell_tag_configs.items(), key=lambda x: -len(x[1]))
        most_common = sorted_configs[0] if sorted_configs else (None, [])

        dwell_deviations = _find_dwell_deviations(dwell_tag_configs, most_common)

        return {
            "dwell_tag_configs": dwell_tag_configs,
            "most_common_config": most_common,
            "sites_with_dwell_deviations": dwell_deviations,
            "dwell_tag_name_usage": dwell_tag_name_usage,
            "sites_with_custom_names": sites_with_custom,
            "sites_with_business_hours": sites_with_hours,
            "total_sites": len(site_settings),
        }

    @staticmethod
    def _analyze_occupancy_patterns(
        site_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze occupancy settings to identify deviations."""
        logging.info("Analyzing occupancy patterns...")

        occ_configs: dict[str, list[dict[str, Any]]] = {}
        min_duration_values: dict[Any, int] = {}
        enabled_count = 0
        disabled_count = 0

        for site_id, data in site_settings.items():
            site_name = data["site_name"]
            occupancy = data.get("occupancy", {})
            analytic = data.get("analytic", {})

            if analytic.get("enabled", False):
                enabled_count += 1
            else:
                disabled_count += 1

            config_key = _occupancy_config_key(occupancy)
            occ_configs.setdefault(config_key, []).append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "occupancy": occupancy,
                }
            )

            md = occupancy.get("min_duration", "N/A")
            min_duration_values[md] = min_duration_values.get(md, 0) + 1

        sorted_configs = sorted(occ_configs.items(), key=lambda x: -len(x[1]))
        most_common = sorted_configs[0] if sorted_configs else (None, [])

        occ_deviations = _find_occupancy_deviations(occ_configs, most_common)

        return {
            "occupancy_configs": occ_configs,
            "most_common_config": most_common,
            "sites_with_occupancy_deviations": occ_deviations,
            "min_duration_values": min_duration_values,
            "analytic_enabled_count": enabled_count,
            "analytic_disabled_count": disabled_count,
            "total_sites": len(site_settings),
        }

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _display_results(combined: dict[str, Any]) -> None:
        """Display analysis results to console."""
        print("\n" + "=" * 60)
        print("ZONE & ENGAGEMENT CONFIGURATION ANALYSIS RESULTS")
        print("=" * 60)

        ZoneConfigurationAnalyzer._display_zone_section(combined.get("zones", {}))
        ZoneConfigurationAnalyzer._display_engagement_section(combined.get("engagement", {}))
        ZoneConfigurationAnalyzer._display_occupancy_section(combined.get("occupancy", {}))

        print("\n" + "=" * 60)

    @staticmethod
    def _display_zone_section(zone_analysis: dict[str, Any]) -> None:
        """Display zone analysis section."""
        if not zone_analysis:
            return
        stats = zone_analysis.get("zone_count_stats", {})
        print(f"\n{'=' * 60}")
        print("[ZONE ANALYSIS]")
        print(f"{'=' * 60}")
        print("\n[Zone Summary]")
        print(f"  Total sites scanned: {stats.get('total_sites', 0)}")
        print(f"  Sites with zones: {stats.get('sites_with_zones', 0)}")
        print(f"  Average zones per site: {stats.get('mean', 0):.1f}")
        print(f"  Median zones per site: {stats.get('median', 0)}")
        print(f"  Range: {stats.get('min', 0)} - {stats.get('max', 0)}")
        print(f"  Standard deviation: {stats.get('std_dev', 0):.2f}")

        _display_common_zones(zone_analysis, stats)
        _display_missing_zones(zone_analysis)
        _display_zone_deviations(zone_analysis)

    @staticmethod
    def _display_engagement_section(
        engagement_analysis: dict[str, Any],
    ) -> None:
        """Display engagement analysis section."""
        if not engagement_analysis:
            return
        print(f"\n{'=' * 60}")
        print("[ENGAGEMENT ANALYSIS]")
        print(f"{'=' * 60}")

        _display_dwell_configs(engagement_analysis)
        _display_dwell_deviations(engagement_analysis)
        _display_custom_names(engagement_analysis)
        _display_business_hours(engagement_analysis)

    @staticmethod
    def _display_occupancy_section(
        occupancy_analysis: dict[str, Any],
    ) -> None:
        """Display occupancy analysis section."""
        if not occupancy_analysis:
            return
        print(f"\n{'=' * 60}")
        print("[OCCUPANCY ANALYSIS]")
        print(f"{'=' * 60}")

        total = occupancy_analysis.get("total_sites", 0)
        enabled = occupancy_analysis.get("analytic_enabled_count", 0)
        disabled = occupancy_analysis.get("analytic_disabled_count", 0)

        print("\n[Analytics Status]")
        pct_e = enabled / total * 100 if total else 0
        pct_d = disabled / total * 100 if total else 0
        print(f"  Enabled: {enabled} sites ({pct_e:.1f}%)")
        print(f"  Disabled: {disabled} sites ({pct_d:.1f}%)")

        _display_occupancy_configs(occupancy_analysis)
        _display_occupancy_deviations(occupancy_analysis)

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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zone_analysis = combined.get("zones", {})
        engagement_analysis = combined.get("engagement", {})
        occupancy_analysis = combined.get("occupancy", {})

        _export_summary(
            site_zones,
            site_settings,
            zone_analysis,
            engagement_analysis,
            occupancy_analysis,
            timestamp,
            save_data_fn,
        )
        _export_all_zones(site_zones, timestamp, save_data_fn)
        _export_zone_frequency(zone_analysis, timestamp, save_data_fn)
        _export_dwell_configs(engagement_analysis, timestamp, save_data_fn)
        _export_occupancy_configs(occupancy_analysis, timestamp, save_data_fn)

        logging.info(
            "Site configuration analysis complete." " Exported CSV files with timestamp %s",
            timestamp,
        )


# ======================================================================
# Module-private helper functions (keep class body lean)
# ======================================================================


def _empty_zone_entry(site_name: str) -> dict[str, Any]:
    """Return a zero-zone placeholder for a site."""
    return {
        "site_name": site_name,
        "zones": [],
        "zone_names": set(),
        "zone_count": 0,
    }


def _progress(items: list[Any], desc: str, unit: str) -> Any:
    """Wrap items with tqdm progress bar."""
    from tqdm import tqdm

    return tqdm(items, desc=desc, unit=unit)


def _compute_zone_stats(
    zone_counts: list[int],
    total_sites: int,
    sites_with_zones: int,
) -> dict[str, Any]:
    """Compute summary statistics for zone counts."""
    mean: float
    median: int
    mn: int
    mx: int
    std_dev: float
    if zone_counts:
        mean = sum(zone_counts) / len(zone_counts)
        sorted_c = sorted(zone_counts)
        median = sorted_c[len(sorted_c) // 2]
        mn, mx = min(zone_counts), max(zone_counts)
        if len(zone_counts) > 1:
            variance = sum((c - mean) ** 2 for c in zone_counts) / len(zone_counts)
            std_dev = variance**0.5
        else:
            std_dev = 0.0
    else:
        mean = 0.0
        median = 0
        mn = 0
        mx = 0
        std_dev = 0.0

    return {
        "mean": mean,
        "median": median,
        "min": mn,
        "max": mx,
        "std_dev": std_dev,
        "total_sites": total_sites,
        "sites_with_zones": sites_with_zones,
    }


def _find_sites_missing_common(
    site_zones: dict[str, Any],
    common_zones: set[str],
) -> dict[str, Any]:
    """Find sites missing common zones."""
    result: dict[str, Any] = {}
    for site_id, data in site_zones.items():
        if data["zone_count"] > 0:
            missing = common_zones - data["zone_names"]
            if missing:
                result[site_id] = {
                    "site_name": data["site_name"],
                    "missing_zones": missing,
                    "has_zones": data["zone_names"],
                }
    return result


def _find_sites_with_unique(
    site_zones: dict[str, Any],
    zone_frequency: dict[str, int],
    sites_with_zones: int,
) -> dict[str, Any]:
    """Find sites with zones that only appear in < 10% of sites."""
    threshold = max(1, int(sites_with_zones * 0.1))
    result: dict[str, Any] = {}
    for site_id, data in site_zones.items():
        unique = {n for n in data["zone_names"] if zone_frequency.get(n, 0) <= threshold}
        if unique:
            result[site_id] = {
                "site_name": data["site_name"],
                "unique_zones": unique,
                "zone_count": data["zone_count"],
            }
    return result


def _find_zone_count_deviations(
    site_zones: dict[str, Any],
    mean: float,
    std_dev: float,
) -> dict[str, Any]:
    """Identify sites with zone counts > 1.5 std-dev from mean."""
    if std_dev <= 0:
        return {}
    result: dict[str, Any] = {}
    for site_id, data in site_zones.items():
        count = data["zone_count"]
        deviation = abs(count - mean) / std_dev
        if deviation > 1.5 or (count == 0 and mean > 0):
            result[site_id] = {
                "site_name": data["site_name"],
                "zone_count": count,
                "deviation_score": round(deviation, 2),
                "expected_range": (f"{max(0, mean - 1.5 * std_dev):.1f}" f" - {mean + 1.5 * std_dev:.1f}"),
            }
    return result


def _dwell_config_key(dwell_tags: dict[str, Any]) -> str:
    """Create a hashable config string for dwell tag comparison."""
    return "|".join(
        [
            f"passerby={dwell_tags.get('passerby', 'N/A')}",
            f"bounce={dwell_tags.get('bounce', 'N/A')}",
            f"engaged={dwell_tags.get('engaged', 'N/A')}",
            f"stationed={dwell_tags.get('stationed', 'N/A')}",
        ]
    )


def _occupancy_config_key(occupancy: dict[str, Any]) -> str:
    """Create a hashable config string for occupancy comparison."""
    return "|".join(
        [
            f"min_duration={occupancy.get('min_duration', 'N/A')}",
            f"clients_enabled={occupancy.get('clients_enabled', 'N/A')}",
            f"sdkclients_enabled=" f"{occupancy.get('sdkclients_enabled', 'N/A')}",
            f"assets_enabled={occupancy.get('assets_enabled', 'N/A')}",
            f"unconnected_clients_enabled=" f"{occupancy.get('unconnected_clients_enabled', 'N/A')}",
        ]
    )


def _track_custom_names(
    site_id: str,
    site_name: str,
    dwell_tag_names: dict[str, str],
    usage: dict[str, dict[str, list[dict[str, Any]]]],
    sites_with_custom: dict[str, dict[str, Any]],
) -> None:
    """Track custom dwell tag names across sites."""
    has_custom = False
    for tag_type, custom_name in dwell_tag_names.items():
        if custom_name and custom_name.strip():
            has_custom = True
            usage.setdefault(tag_type, {}).setdefault(custom_name, []).append(
                {"site_id": site_id, "site_name": site_name}
            )
    if has_custom:
        sites_with_custom[site_id] = {
            "site_name": site_name,
            "custom_names": {k: v for k, v in dwell_tag_names.items() if v and v.strip()},
        }


def _find_dwell_deviations(
    configs: dict[str, list[dict[str, Any]]],
    most_common: tuple[str | None, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Identify sites deviating from the most common dwell config."""
    result: dict[str, Any] = {}
    if not most_common[0]:
        return result
    expected = most_common[1][0]["dwell_tags"] if most_common[1] else {}
    for key, sites in configs.items():
        if key != most_common[0]:
            for site in sites:
                result[site["site_id"]] = {
                    "site_name": site["site_name"],
                    "current_config": site["dwell_tags"],
                    "expected_config": expected,
                }
    return result


def _find_occupancy_deviations(
    configs: dict[str, list[dict[str, Any]]],
    most_common: tuple[str | None, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Identify sites deviating from the most common occupancy config."""
    result: dict[str, Any] = {}
    if not most_common[0]:
        return result
    expected = most_common[1][0]["occupancy"] if most_common[1] else {}
    for key, sites in configs.items():
        if key != most_common[0]:
            for site in sites:
                result[site["site_id"]] = {
                    "site_name": site["site_name"],
                    "current_config": site["occupancy"],
                    "expected_config": expected,
                }
    return result


# ======================================================================
# Display helper functions
# ======================================================================


def _display_common_zones(zone_analysis: dict[str, Any], stats: dict[str, Any]) -> None:
    """Display common zones section."""
    common_zones = zone_analysis.get("common_zones", set())
    print("\n[Common Zones] (Present in 75%+ of sites with zones)")
    if common_zones:
        sites_with_zones = stats.get("sites_with_zones", 1) or 1
        for name in sorted(common_zones):
            freq = zone_analysis.get("zone_frequency", {}).get(name, 0)
            pct = freq / sites_with_zones * 100
            print(f"  - {name} ({freq} sites, {pct:.0f}%)")
    else:
        print("  No common zones found (high variation across sites)")


def _display_missing_zones(zone_analysis: dict[str, Any]) -> None:
    """Display sites missing common zones."""
    missing = zone_analysis.get("sites_missing_common_zones", {})
    print(f"\n[Sites Missing Common Zones] ({len(missing)} sites)")
    if missing:
        for data in list(missing.values())[:10]:
            print(f"  - {data['site_name']}")
            print(f"    Missing: {', '.join(sorted(data['missing_zones']))}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more sites")
    else:
        print("  All sites have the common zones configured")


def _display_zone_deviations(zone_analysis: dict[str, Any]) -> None:
    """Display zone count deviations."""
    devs = zone_analysis.get("zone_count_deviations", {})
    print(f"\n[Zone Count Deviations] ({len(devs)} sites)")
    if devs:
        for data in list(devs.values())[:10]:
            print(f"  - {data['site_name']}: {data['zone_count']} zones")
            print(f"    Expected range: {data['expected_range']}," f" Deviation: {data['deviation_score']}x std dev")
        if len(devs) > 10:
            print(f"  ... and {len(devs) - 10} more sites")
    else:
        print("  All sites have zone counts within expected range")


def _display_dwell_configs(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display dwell tag configuration summary."""
    most_common = engagement_analysis.get("most_common_config", (None, []))
    configs = engagement_analysis.get("dwell_tag_configs", {})
    print("\n[Dwell Tag Configurations]")
    print(f"  Total unique configurations: {len(configs)}")
    if most_common[0] and most_common[1]:
        print(f"  Most common config ({len(most_common[1])} sites):")
        tags = most_common[1][0].get("dwell_tags", {})
        print(f"    passerby: {tags.get('passerby', 'N/A')}")
        print(f"    bounce: {tags.get('bounce', 'N/A')}")
        print(f"    engaged: {tags.get('engaged', 'N/A')}")
        print(f"    stationed: {tags.get('stationed', 'N/A')}")


def _display_dwell_deviations(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with dwell tag deviations."""
    devs = engagement_analysis.get("sites_with_dwell_deviations", {})
    print(f"\n[Sites with Dwell Tag Deviations] ({len(devs)} sites)")
    if devs:
        for data in list(devs.values())[:10]:
            print(f"  - {data['site_name']}")
            cur = data.get("current_config", {})
            print(f"    Current: passerby={cur.get('passerby', 'N/A')}," f" bounce={cur.get('bounce', 'N/A')}")
            print(f"             engaged={cur.get('engaged', 'N/A')}," f" stationed={cur.get('stationed', 'N/A')}")
        if len(devs) > 10:
            print(f"  ... and {len(devs) - 10} more sites")
    else:
        print("  All sites have matching dwell tag configurations")


def _display_custom_names(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with custom dwell tag names."""
    custom = engagement_analysis.get("sites_with_custom_names", {})
    print(f"\n[Sites with Custom Dwell Tag Names] ({len(custom)} sites)")
    if custom:
        for data in list(custom.values())[:10]:
            print(f"  - {data['site_name']}")
            for tag_type, name in data.get("custom_names", {}).items():
                print(f"    {tag_type}: '{name}'")
        if len(custom) > 10:
            print(f"  ... and {len(custom) - 10} more sites")
    else:
        print("  No sites have custom dwell tag names configured")


def _display_business_hours(
    engagement_analysis: dict[str, Any],
) -> None:
    """Display sites with business hours configured."""
    hours = engagement_analysis.get("sites_with_business_hours", {})
    print(f"\n[Sites with Business Hours Configured] ({len(hours)} sites)")
    if hours:
        if len(hours) <= 5:
            for data in hours.values():
                print(f"  - {data['site_name']}")
        else:
            print(f"  {len(hours)} sites have business hours configured")
    else:
        print("  No sites have business hours configured")


def _display_occupancy_configs(
    occupancy_analysis: dict[str, Any],
) -> None:
    """Display occupancy configuration summary."""
    most_common = occupancy_analysis.get("most_common_config", (None, []))
    configs = occupancy_analysis.get("occupancy_configs", {})
    print("\n[Occupancy Configurations]")
    print(f"  Total unique configurations: {len(configs)}")
    if most_common[0] and most_common[1]:
        print(f"  Most common config ({len(most_common[1])} sites):")
        occ = most_common[1][0].get("occupancy", {})
        print(f"    min_duration: {occ.get('min_duration', 'N/A')}")
        print(f"    clients_enabled: {occ.get('clients_enabled', 'N/A')}")
        print(f"    sdkclients_enabled:" f" {occ.get('sdkclients_enabled', 'N/A')}")
        print(f"    assets_enabled: {occ.get('assets_enabled', 'N/A')}")
        print(f"    unconnected_clients_enabled:" f" {occ.get('unconnected_clients_enabled', 'N/A')}")

    md_vals = occupancy_analysis.get("min_duration_values", {})
    if len(md_vals) > 1:
        print("\n[Min Duration Distribution]")
        for dur, count in sorted(md_vals.items(), key=lambda x: -x[1]):
            print(f"  {dur}: {count} sites")


def _display_occupancy_deviations(
    occupancy_analysis: dict[str, Any],
) -> None:
    """Display sites with occupancy config deviations."""
    devs = occupancy_analysis.get("sites_with_occupancy_deviations", {})
    print(f"\n[Sites with Occupancy Config Deviations]" f" ({len(devs)} sites)")
    if devs:
        for data in list(devs.values())[:10]:
            print(f"  - {data['site_name']}")
            cur = data.get("current_config", {})
            print(
                f"    min_duration={cur.get('min_duration', 'N/A')},"
                f" clients={cur.get('clients_enabled', 'N/A')},"
                f" unconnected="
                f"{cur.get('unconnected_clients_enabled', 'N/A')}"
            )
        if len(devs) > 10:
            print(f"  ... and {len(devs) - 10} more sites")
    else:
        print("  All sites have matching occupancy configurations")


# ======================================================================
# Export helper functions
# ======================================================================


def _export_summary(
    site_zones: dict[str, Any],
    site_settings: dict[str, Any],
    zone_analysis: dict[str, Any],
    engagement_analysis: dict[str, Any],
    occupancy_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export combined summary by site."""
    rows = _build_summary_rows(
        site_zones,
        site_settings,
        zone_analysis,
        engagement_analysis,
        occupancy_analysis,
    )
    if not rows:
        return
    filename = f"SiteConfigAnalysis_Summary_{timestamp}.csv"
    save_data_fn(rows, filename, api_function_name="site_config_analysis_summary")
    print(f"! Summary exported to {filename}")


def _build_summary_rows(
    site_zones: dict[str, Any],
    site_settings: dict[str, Any],
    zone_analysis: dict[str, Any],
    engagement_analysis: dict[str, Any],
    occupancy_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the combined summary rows sorted by deviation."""
    all_site_ids = set(site_zones.keys()) | set(site_settings.keys())
    rows: list[dict[str, Any]] = []

    for site_id in all_site_ids:
        zd = site_zones.get(
            site_id,
            {"site_name": "Unknown", "zone_count": 0, "zone_names": set()},
        )
        sd = site_settings.get(
            site_id,
            {
                "site_name": "Unknown",
                "engagement": {},
                "occupancy": {},
                "analytic": {},
            },
        )
        rows.append(
            _build_one_summary_row(
                site_id,
                zd,
                sd,
                zone_analysis,
                engagement_analysis,
                occupancy_analysis,
            )
        )

    rows.sort(
        key=lambda r: (
            r["zone_deviation"] != "Yes",
            r["dwell_deviation"] != "Yes",
            r["occupancy_deviation"] != "Yes",
            not r["missing_common_zones"],
            r["site_name"],
        )
    )
    return rows


def _build_one_summary_row(
    site_id: str,
    zone_data: dict[str, Any],
    settings_data: dict[str, Any],
    zone_analysis: dict[str, Any],
    engagement_analysis: dict[str, Any],
    occupancy_analysis: dict[str, Any],
) -> dict[str, Any]:
    """Build a single summary row for one site."""
    site_name = zone_data.get("site_name") or settings_data.get("site_name", "Unknown")

    missing_common = zone_analysis.get("sites_missing_common_zones", {}).get(site_id, {}).get("missing_zones", set())
    zone_dev = zone_analysis.get("zone_count_deviations", {}).get(site_id)

    engagement = settings_data.get("engagement", {})
    dwell_tags = engagement.get("dwell_tags", {})
    dwell_tag_names = engagement.get("dwell_tag_names", {})
    occupancy = settings_data.get("occupancy", {})
    analytic = settings_data.get("analytic", {})

    has_dwell_dev = site_id in engagement_analysis.get("sites_with_dwell_deviations", {})
    has_occ_dev = site_id in occupancy_analysis.get("sites_with_occupancy_deviations", {})

    return {
        "site_id": site_id,
        "site_name": site_name,
        "zone_count": zone_data.get("zone_count", 0),
        "zone_names": ", ".join(sorted(zone_data.get("zone_names", set()))),
        "missing_common_zones": (", ".join(sorted(missing_common)) if missing_common else ""),
        "zone_deviation": "Yes" if zone_dev else "No",
        "dwell_passerby": dwell_tags.get("passerby", ""),
        "dwell_bounce": dwell_tags.get("bounce", ""),
        "dwell_engaged": dwell_tags.get("engaged", ""),
        "dwell_stationed": dwell_tags.get("stationed", ""),
        "dwell_name_passerby": dwell_tag_names.get("passerby", ""),
        "dwell_name_bounce": dwell_tag_names.get("bounce", ""),
        "dwell_name_engaged": dwell_tag_names.get("engaged", ""),
        "dwell_name_stationed": dwell_tag_names.get("stationed", ""),
        "dwell_deviation": "Yes" if has_dwell_dev else "No",
        "analytic_enabled": analytic.get("enabled", ""),
        "occupancy_min_duration": occupancy.get("min_duration", ""),
        "occupancy_clients_enabled": occupancy.get("clients_enabled", ""),
        "occupancy_sdkclients_enabled": occupancy.get("sdkclients_enabled", ""),
        "occupancy_assets_enabled": occupancy.get("assets_enabled", ""),
        "occupancy_unconnected_enabled": occupancy.get("unconnected_clients_enabled", ""),
        "occupancy_deviation": "Yes" if has_occ_dev else "No",
    }


def _export_all_zones(
    site_zones: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export all zones with site context."""
    if not site_zones:
        return
    rows: list[dict[str, Any]] = []
    for site_id, data in site_zones.items():
        for zone in data.get("zones", []):
            rows.append(
                {
                    "site_id": site_id,
                    "site_name": data.get("site_name", ""),
                    "zone_id": zone.get("id", ""),
                    "zone_name": zone.get("name", ""),
                    "map_id": zone.get("map_id", ""),
                    "vertex_count": len(zone.get("vertices", [])),
                    "created_time": zone.get("created_time", ""),
                    "modified_time": zone.get("modified_time", ""),
                }
            )
    if rows:
        filename = f"SiteConfigAnalysis_AllZones_{timestamp}.csv"
        save_data_fn(rows, filename, api_function_name="site_config_all_zones")
        print(f"! All zones exported to {filename}")


def _export_zone_frequency(
    zone_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export zone frequency report."""
    freq = zone_analysis.get("zone_frequency")
    if not freq:
        return
    stats = zone_analysis.get("zone_count_stats", {})
    sites_with_zones = stats.get("sites_with_zones", 1) or 1
    common = zone_analysis.get("common_zones", set())

    rows = []
    for name, count in sorted(freq.items(), key=lambda x: -x[1]):
        pct = count / sites_with_zones * 100
        rows.append(
            {
                "zone_name": name,
                "site_count": count,
                "percentage": f"{pct:.1f}%",
                "is_common": "Yes" if name in common else "No",
            }
        )

    filename = f"SiteConfigAnalysis_ZoneFrequency_{timestamp}.csv"
    save_data_fn(rows, filename, api_function_name="site_config_zone_frequency")
    print(f"! Zone frequency exported to {filename}")


def _export_dwell_configs(
    engagement_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export dwell tag configuration distribution."""
    configs = engagement_analysis.get("dwell_tag_configs")
    if not configs:
        return
    rows = []
    for key, sites in sorted(configs.items(), key=lambda x: -len(x[1])):
        sample = sites[0] if sites else {}
        tags = sample.get("dwell_tags", {})
        rows.append(
            {
                "configuration": key,
                "site_count": len(sites),
                "passerby": tags.get("passerby", ""),
                "bounce": tags.get("bounce", ""),
                "engaged": tags.get("engaged", ""),
                "stationed": tags.get("stationed", ""),
                "sample_sites": ", ".join(s["site_name"] for s in sites[:5]),
            }
        )

    filename = f"SiteConfigAnalysis_DwellConfigs_{timestamp}.csv"
    save_data_fn(rows, filename, api_function_name="site_config_dwell_configs")
    print(f"! Dwell configurations exported to {filename}")


def _export_occupancy_configs(
    occupancy_analysis: dict[str, Any],
    timestamp: str,
    save_data_fn: SaveDataFn,
) -> None:
    """Export occupancy configuration distribution."""
    configs = occupancy_analysis.get("occupancy_configs")
    if not configs:
        return
    rows = []
    for key, sites in sorted(configs.items(), key=lambda x: -len(x[1])):
        sample = sites[0] if sites else {}
        occ = sample.get("occupancy", {})
        rows.append(
            {
                "configuration": key,
                "site_count": len(sites),
                "min_duration": occ.get("min_duration", ""),
                "clients_enabled": occ.get("clients_enabled", ""),
                "sdkclients_enabled": occ.get("sdkclients_enabled", ""),
                "assets_enabled": occ.get("assets_enabled", ""),
                "unconnected_clients_enabled": occ.get("unconnected_clients_enabled", ""),
                "sample_sites": ", ".join(s["site_name"] for s in sites[:5]),
            }
        )

    filename = f"SiteConfigAnalysis_OccupancyConfigs_{timestamp}.csv"
    save_data_fn(
        rows,
        filename,
        api_function_name="site_config_occupancy_configs",
    )
    print(f"! Occupancy configurations exported to {filename}")
