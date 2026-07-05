"""Site analytics configuration manager extracted from MistHelper.py."""  # WHY: module docstring identifies scope.

from __future__ import annotations  # WHY: enables PEP 563 postponed evaluation for cleaner annotations.

import logging  # WHY: structured operator log emission.
from dataclasses import dataclass  # WHY: frozen dependency container avoids >5-param signatures.
from datetime import datetime  # WHY: timestamped export filenames disambiguate runs.
from typing import Any  # WHY: Mist API responses are heterogeneous dicts.

_SEPARATOR: str = "=" * 60  # WHY: shared 60-char rule used across UI banners.
_CONFIRM_TOKEN: str = "CONFIGURE"  # WHY: exact confirmation keyword required from the operator.
_SUMMARY_PREVIEW_LIMIT: int = 10  # WHY: cap preview list length to avoid console flooding.
_DEVIATION_DETAIL_LIMIT: int = 5  # WHY: keep CSV detail column readable.
_HTTP_OK: int = 200  # WHY: Mist API "success" status literal made explicit.
_YES_NO: dict[bool, str] = {True: "Yes", False: "No"}  # WHY: table lookup avoids ternaries in CSV row builder.
_DEVIATION_SECTIONS: tuple[tuple[str, str], ...] = (  # WHY: table drives type/apply/report loops.
    ("rtsa", "RTSA"),  # WHY: real-time asset visibility toggle group.
    ("rogue", "Rogue"),  # WHY: rogue AP detection thresholds group.
    ("engagement", "Engagement"),  # WHY: dwell/hours engagement analytics group.
    ("analytic", "Analytic"),  # WHY: umbrella analytic enable flag group.
    ("occupancy", "Occupancy"),  # WHY: occupancy sensing thresholds group.
    ("wifi", "WiFi"),  # WHY: wifi location services flags group.
)


@dataclass(frozen=True, slots=True)  # WHY: immutable slots container collapses 8 injected callables.
class SiteAnalyticsConfiguratorDeps:  # WHY: DI seam for tests and production wiring.
    """Dependency container for SiteAnalyticsConfigurator execution."""  # WHY: docstring anchors purpose.

    apisession: Any  # WHY: mistapi session object propagated to API helpers.
    mistapi: Any  # WHY: mistapi module reference (setting-getter / updater).
    get_org_id_fn: Any  # WHY: callable returning the current organization id.
    check_stop_fn: Any  # WHY: cooperative cancellation predicate.
    safe_input_fn: Any  # WHY: input prompt that raises SystemExit on disconnect.
    all_sites_fn: Any  # WHY: fetches every site record for scanning.
    save_data_fn: Any  # WHY: writes CSV reports to disk.
    tqdm_fn: Any  # WHY: progress-bar wrapper injected for testability.


class SiteAnalyticsConfigurator:  # WHY: static namespace collecting configurator workflow helpers.
    """Configures site analytics settings to standard values across all sites."""  # WHY: purpose anchor.

    STANDARD_RTSA = {"enabled": True, "track_asset": True, "app_waking": True}  # WHY: canonical RTSA baseline.

    STANDARD_ROGUE = {  # WHY: canonical rogue detection baseline enforced org-wide.
        "min_rssi": -80,  # WHY: quiet-signal rogue threshold in dBm.
        "min_duration": 10,  # WHY: seconds a signal must persist before flagging.
        "enabled": True,  # WHY: rogue detection master switch.
        "honeypot_enabled": True,  # WHY: honeypot AP detection also enabled.
        "whitelisted_bssids": [],  # WHY: no permanent BSSID allowlist by default.
        "whitelisted_ssids": [],  # WHY: no permanent SSID allowlist by default.
    }

    STANDARD_ENGAGEMENT = {  # WHY: canonical dwell-time engagement analytics baseline.
        "dwell_tags": {  # WHY: dwell-time bucket ranges (seconds) used for reports.
            "passerby": "1-300",  # WHY: <=5 minutes counts as passerby.
            "bounce": "301-14400",  # WHY: 5m-4h counts as bounce.
            "engaged": "14401-36000",  # WHY: 4h-10h counts as engaged.
            "stationed": "36001-86400",  # WHY: >10h up to a day counts as stationed.
        },
        "dwell_tag_names": {"passerby": "", "bounce": "", "engaged": "", "stationed": ""},  # WHY: no aliases.
        "hours": {"sun": "", "mon": "", "tue": "", "wed": "", "thu": "", "fri": "", "sat": ""},  # WHY: no hours cfg.
    }

    STANDARD_ANALYTIC = {"enabled": True}  # WHY: analytic feature master toggle baseline.

    STANDARD_OCCUPANCY = {  # WHY: canonical occupancy analytics baseline.
        "min_duration": 300,  # WHY: 5 minutes of continuous presence before counting.
        "clients_enabled": True,  # WHY: count associated wireless clients.
        "sdkclients_enabled": True,  # WHY: count SDK-tagged clients.
        "assets_enabled": True,  # WHY: count tagged assets.
        "unconnected_clients_enabled": False,  # WHY: exclude probes-only devices from counts.
    }

    STANDARD_WIFI = {"enabled": True, "locate_connected": True, "locate_unconnected": False}  # WHY: wifi baseline.

    @staticmethod
    def execute(deps: SiteAnalyticsConfiguratorDeps) -> None:  # WHY: single public workflow entry point.
        """Main entry point for site analytics configuration."""  # WHY: docstring anchors public role.
        SiteAnalyticsConfigurator._print_banner()  # WHY: warn operator before destructive action.
        logging.info("Starting site analytics configuration scan...")  # WHY: audit trail start marker.
        current_org_id = deps.get_org_id_fn()  # WHY: resolve org context before hitting Mist API.
        if not current_org_id:  # WHY: no org context means nothing to do.
            print("! No organization selected. Exiting.")  # WHY: user-visible reason for early return.
            return  # WHY: short-circuit exit.
        deviations = SiteAnalyticsConfigurator._scan_for_deviations(current_org_id, deps)  # WHY: gather drift list.
        if not deviations:  # WHY: no drift means no work required.
            print("\n[OK] All sites are configured with standard analytics settings.")  # WHY: positive confirmation.
            return  # WHY: exit clean state.
        SiteAnalyticsConfigurator._display_deviation_summary(deviations)  # WHY: show operator what will change.
        SiteAnalyticsConfigurator._export_deviation_report(deviations, deps)  # WHY: persist preview evidence.
        if not SiteAnalyticsConfigurator._confirm_operation(deviations, deps):  # WHY: require explicit consent.
            return  # WHY: user declined or session lost.
        results = SiteAnalyticsConfigurator._apply_standard_configuration(deviations, deps)  # WHY: mutate settings.
        SiteAnalyticsConfigurator._export_results(results, deps)  # WHY: persist post-run evidence.

    @staticmethod
    def _print_banner() -> None:  # WHY: extracted banner keeps execute() under 25 lines.
        """Print the destructive-operation banner shown before scanning."""  # WHY: docstring anchors intent.
        print("Site Analytics Configurator:")  # WHY: tool title header.
        print(_SEPARATOR)  # WHY: visual rule above warning.
        print("! DESTRUCTIVE OPERATION - This will modify site settings")  # WHY: explicit destructive warning.
        print(_SEPARATOR)  # WHY: visual rule below warning.

    @staticmethod
    def _confirm_operation(deviations: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps) -> bool:
        """Prompt operator for CONFIGURE confirmation and return acceptance flag."""  # WHY: gates the mutation.
        print("\n" + _SEPARATOR)  # WHY: separate summary block from confirmation prompt.
        print(f"! {len(deviations)} sites will be updated to standard configuration")  # WHY: state impact scope.
        print(_SEPARATOR)  # WHY: close the confirmation banner.
        try:
            confirmation = deps.safe_input_fn(  # WHY: safe_input handles disconnected session gracefully.
                f"Type '{_CONFIRM_TOKEN}' to apply standard settings to all deviating sites: ",
                context="site_analytics_config",  # WHY: audit tag for input logging.
            )
        except SystemExit:  # WHY: safe_input raises SystemExit when session drops.
            logging.info("Site analytics configuration cancelled - session disconnected")  # WHY: cancellation audit.
            return False  # WHY: treat disconnect as declined.
        if confirmation != _CONFIRM_TOKEN:  # WHY: any deviation from token declines the operation.
            print("! Operation cancelled - confirmation not provided")  # WHY: user-visible cancellation.
            logging.warning("Site analytics configuration cancelled by user")  # WHY: audit trail decline marker.
            return False  # WHY: declined path.
        return True  # WHY: operator confirmed with exact token.

    @staticmethod
    def _scan_for_deviations(org_id: str, deps: SiteAnalyticsConfiguratorDeps) -> list[dict[str, Any]]:
        """Scan all sites and identify those deviating from standard configuration."""  # WHY: scan orchestrator.
        logging.info("Fetching all sites for analytics configuration scan...")  # WHY: audit start.
        sites = deps.all_sites_fn(org_id)  # WHY: pull inventory once via injected fetcher.
        if not sites:  # WHY: nothing to scan when org has no sites.
            logging.warning("No sites found in organization.")  # WHY: surface empty-inventory case.
            return []  # WHY: short-circuit with empty deviation list.
        print(f"! Scanning {len(sites)} sites for configuration deviations...")  # WHY: progress hint.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator collecting drift records.
        for site in deps.tqdm_fn(sites, desc="Scanning sites", unit="site"):  # WHY: progress-bar wrap.
            if deps.check_stop_fn():  # WHY: cooperative cancellation between sites.
                break  # WHY: honor stop signal.
            record = SiteAnalyticsConfigurator._scan_single_site(site, deps)  # WHY: delegate per-site work.
            if record is not None:  # WHY: only keep sites that actually deviate.
                deviations.append(record)  # WHY: accumulate drift record.
        print(f"! Found {len(deviations)} sites with configuration deviations")  # WHY: summary line for operator.
        return deviations  # WHY: hand results to caller for display and mutation.

    @staticmethod
    def _fetch_scan_settings(
        site_id: str, site_name: str, deps: SiteAnalyticsConfiguratorDeps
    ) -> dict[str, Any] | None:
        """Fetch site settings for scan, returning None on API/network failure."""  # WHY: isolates GET path.
        try:
            response = deps.mistapi.api.v1.sites.setting.getSiteSetting(deps.apisession, site_id=site_id)
        except Exception as error:  # noqa: BLE001  # WHY: mistapi may raise varied exceptions per site.
            logging.warning("Error scanning %s: %s", site_name, error)  # WHY: continue with next site on error.
            return None  # WHY: treat as unfetchable.
        if response.status_code != _HTTP_OK:  # WHY: non-200 means we cannot trust settings payload.
            logging.warning("Failed to fetch settings for %s: HTTP %s", site_name, response.status_code)
            return None  # WHY: skip site with API error.
        return response.data if isinstance(response.data, dict) else {}  # WHY: defensive shape check.

    @staticmethod
    def _scan_single_site(site: dict[str, Any], deps: SiteAnalyticsConfiguratorDeps) -> dict[str, Any] | None:
        """Return deviation record for one site, or None when it is clean or unfetchable."""  # WHY: per-site anchor.
        site_id = site.get("id")  # WHY: primary key needed for API + downstream reporting.
        site_name = site.get("name", "Unnamed Site")  # WHY: display label with fallback.
        if not isinstance(site_id, str) or not site_id:  # WHY: guard against malformed inventory rows.
            logging.warning("Invalid site_id for %s", site_name)  # WHY: expose bad rows in log.
            return None  # WHY: skip un-addressable site.
        settings = SiteAnalyticsConfigurator._fetch_scan_settings(site_id, site_name, deps)  # WHY: GET helper.
        if settings is None:  # WHY: fetch helper already logged the failure reason.
            return None  # WHY: propagate skip.
        site_deviations = SiteAnalyticsConfigurator._check_deviations(settings, site_id, site_name)  # WHY: analyze.
        return site_deviations if site_deviations["has_deviations"] else None  # WHY: drop clean sites.

    @staticmethod
    def _check_rtsa_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check RTSA settings for deviations."""  # WHY: encapsulates one section for _check_deviations.
        current_rtsa = settings.get("rtsa", {})  # WHY: default empty dict when API omits section.
        rtsa_deviations = SiteAnalyticsConfigurator._compare_settings(  # WHY: shared flat-key comparator.
            current_rtsa,
            SiteAnalyticsConfigurator.STANDARD_RTSA,
            "rtsa",
        )
        if rtsa_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["rtsa_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["rtsa"] = current_rtsa  # WHY: preserve pre-change snapshot.
            deviation_record["deviation_details"].extend(rtsa_deviations)  # WHY: accumulate details for report.

    @staticmethod
    def _check_rogue_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check Rogue settings for deviations."""  # WHY: rogue-section drift check.
        current_rogue = settings.get("rogue", {})  # WHY: default empty dict when API omits section.
        rogue_deviations = SiteAnalyticsConfigurator._compare_settings(  # WHY: shared flat-key comparator.
            current_rogue,
            SiteAnalyticsConfigurator.STANDARD_ROGUE,
            "rogue",
        )
        if rogue_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["rogue_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["rogue"] = current_rogue  # WHY: preserve pre-change snapshot.
            deviation_record["deviation_details"].extend(rogue_deviations)  # WHY: accumulate details for report.

    @staticmethod
    def _check_engagement_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check Engagement settings for deviations."""  # WHY: nested engagement-section drift check.
        current_engagement = settings.get("engagement", {})  # WHY: default empty dict when API omits section.
        engagement_deviations = SiteAnalyticsConfigurator._compare_engagement(current_engagement)  # WHY: nested cmp.
        if engagement_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["engagement_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["engagement"] = current_engagement  # WHY: preserve pre-change snap.
            deviation_record["deviation_details"].extend(engagement_deviations)  # WHY: accumulate details.

    @staticmethod
    def _check_analytic_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check analytic settings for deviations."""  # WHY: analytic-section drift check.
        current_analytic = settings.get("analytic", {})  # WHY: default empty dict when API omits section.
        analytic_deviations = SiteAnalyticsConfigurator._compare_settings(  # WHY: shared flat-key comparator.
            current_analytic,
            SiteAnalyticsConfigurator.STANDARD_ANALYTIC,
            "analytic",
        )
        if analytic_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["analytic_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["analytic"] = current_analytic  # WHY: preserve pre-change snapshot.
            deviation_record["deviation_details"].extend(analytic_deviations)  # WHY: accumulate details for report.

    @staticmethod
    def _check_occupancy_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check occupancy settings for deviations."""  # WHY: occupancy-section drift check.
        current_occupancy = settings.get("occupancy", {})  # WHY: default empty dict when API omits section.
        occupancy_deviations = SiteAnalyticsConfigurator._compare_settings(  # WHY: shared flat-key comparator.
            current_occupancy,
            SiteAnalyticsConfigurator.STANDARD_OCCUPANCY,
            "occupancy",
        )
        if occupancy_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["occupancy_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["occupancy"] = current_occupancy  # WHY: preserve pre-change snap.
            deviation_record["deviation_details"].extend(occupancy_deviations)  # WHY: accumulate details.

    @staticmethod
    def _check_wifi_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check wifi settings for deviations."""  # WHY: wifi-section drift check.
        current_wifi = settings.get("wifi", {})  # WHY: default empty dict when API omits section.
        wifi_deviations = SiteAnalyticsConfigurator._compare_settings(  # WHY: shared flat-key comparator.
            current_wifi,
            SiteAnalyticsConfigurator.STANDARD_WIFI,
            "wifi",
        )
        if wifi_deviations:  # WHY: only mutate record when drift detected.
            deviation_record["wifi_deviation"] = True  # WHY: flag section as drifted.
            deviation_record["has_deviations"] = True  # WHY: mark record as reportable.
            deviation_record["current_settings"]["wifi"] = current_wifi  # WHY: preserve pre-change snapshot.
            deviation_record["deviation_details"].extend(wifi_deviations)  # WHY: accumulate details for report.

    @staticmethod
    def _check_deviations(settings: dict[str, Any], site_id: str, site_name: str) -> dict[str, Any]:
        """Check one site's settings for deviations."""  # WHY: aggregates per-section checks into one record.
        deviation_record: dict[str, Any] = {  # WHY: seed record with all-clean defaults.
            "site_id": site_id,  # WHY: identifier for downstream API calls.
            "site_name": site_name,  # WHY: display label for reports.
            "has_deviations": False,  # WHY: rolled-up flag toggled by section checks.
            "rtsa_deviation": False,  # WHY: per-section drift flag.
            "rogue_deviation": False,  # WHY: per-section drift flag.
            "engagement_deviation": False,  # WHY: per-section drift flag.
            "analytic_deviation": False,  # WHY: per-section drift flag.
            "occupancy_deviation": False,  # WHY: per-section drift flag.
            "wifi_deviation": False,  # WHY: per-section drift flag.
            "current_settings": {},  # WHY: snapshot of pre-change values keyed by section.
            "deviation_details": [],  # WHY: flat list of per-field drift entries.
        }
        SiteAnalyticsConfigurator._check_rtsa_deviations(deviation_record, settings)  # WHY: run RTSA check.
        SiteAnalyticsConfigurator._check_rogue_deviations(deviation_record, settings)  # WHY: run rogue check.
        SiteAnalyticsConfigurator._check_engagement_deviations(deviation_record, settings)  # WHY: engagement check.
        SiteAnalyticsConfigurator._check_analytic_deviations(deviation_record, settings)  # WHY: analytic check.
        SiteAnalyticsConfigurator._check_occupancy_deviations(deviation_record, settings)  # WHY: occupancy check.
        SiteAnalyticsConfigurator._check_wifi_deviations(deviation_record, settings)  # WHY: wifi check.
        return deviation_record  # WHY: hand aggregated record back to scanner.

    @staticmethod
    def _compare_settings(current: dict[str, Any], standard: dict[str, Any], section: str) -> list[dict[str, Any]]:
        """Compare current settings with standard and return list of deviations."""  # WHY: flat-key comparator.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator for per-key drift entries.
        for key, expected_value in standard.items():  # WHY: iterate expected schema keys only.
            current_value = current.get(key)  # WHY: missing key treated same as None.
            if current_value == expected_value:  # WHY: skip matching values quickly.
                continue  # WHY: guard clause keeps loop body shallow.
            reported_current = "NOT SET" if current_value is None else current_value  # WHY: distinguish missing.
            deviations.append(  # WHY: single append path for both missing and mismatch cases.
                {"section": section, "key": key, "current": reported_current, "expected": expected_value},
            )
        return deviations  # WHY: return accumulated drift list.

    @staticmethod
    def _compare_dwell_tags(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement dwell_tags settings."""  # WHY: nested dwell-range comparator.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator for dwell-tag drift entries.
        current_dwell_tags = current.get("dwell_tags", {})  # WHY: default empty dict when API omits sub-section.
        for tag_name, expected_range in standard["dwell_tags"].items():  # WHY: iterate expected tag names.
            current_range = current_dwell_tags.get(tag_name)  # WHY: missing key treated same as None.
            if current_range == expected_range:  # WHY: skip matches to keep loop shallow.
                continue  # WHY: guard clause reduces nesting.
            reported = "NOT SET" if current_range is None else current_range  # WHY: distinguish missing values.
            deviations.append(  # WHY: uniform drift row shape for reports.
                {"section": "engagement.dwell_tags", "key": tag_name, "current": reported, "expected": expected_range},
            )
        return deviations  # WHY: hand list back to engagement aggregator.

    @staticmethod
    def _compare_dwell_tag_names(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement dwell_tag_names settings."""  # WHY: nested dwell-name comparator.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator for dwell-name drift entries.
        current_dwell_names = current.get("dwell_tag_names", {})  # WHY: default empty dict when API omits section.
        for tag_name, expected_name in standard["dwell_tag_names"].items():  # WHY: iterate expected labels.
            current_name = current_dwell_names.get(tag_name)  # WHY: None means unset (skip drift).
            if current_name is None or current_name == expected_name:  # WHY: unset/matching are acceptable.
                continue  # WHY: guard clause avoids adding noise entries.
            deviations.append(  # WHY: uniform drift row shape for reports.
                {
                    "section": "engagement.dwell_tag_names",
                    "key": tag_name,
                    "current": current_name,
                    "expected": expected_name,
                },
            )
        return deviations  # WHY: hand list back to engagement aggregator.

    @staticmethod
    def _compare_engagement_hours(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement hours settings."""  # WHY: nested per-day hours comparator.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator for hours drift entries.
        current_hours = current.get("hours", {})  # WHY: default empty dict when API omits section.
        for day_name, expected_hours in standard["hours"].items():  # WHY: iterate expected days.
            current_day_hours = current_hours.get(day_name)  # WHY: None means unset (skip drift).
            if current_day_hours is None or current_day_hours == expected_hours:  # WHY: unset/match acceptable.
                continue  # WHY: guard clause avoids adding noise entries.
            expected_display = expected_hours if expected_hours else "(empty)"  # WHY: humanize empty schedule.
            deviations.append(  # WHY: uniform drift row shape for reports.
                {
                    "section": "engagement.hours",
                    "key": day_name,
                    "current": current_day_hours,
                    "expected": expected_display,
                },
            )
        return deviations  # WHY: hand list back to engagement aggregator.

    @staticmethod
    def _count_deviations(deviations: list[dict[str, Any]]) -> dict[str, int]:
        """Count sites with each type of deviation."""  # WHY: summary counts per section for banner.
        counts: dict[str, int] = {key: 0 for key, _ in _DEVIATION_SECTIONS}  # WHY: init counters from table.
        for site in deviations:  # WHY: tally per drifted site.
            for key, _ in _DEVIATION_SECTIONS:  # WHY: iterate section table for lookups.
                if site.get(f"{key}_deviation"):  # WHY: increment when this section drifted.
                    counts[key] += 1  # WHY: accumulate section drift count.
        return counts  # WHY: return per-section counts for summary UI.

    @staticmethod
    def _compare_engagement(current: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement settings including nested dwell tags."""  # WHY: fan-out into three sub-comparators.
        standard = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT  # WHY: pin single-source-of-truth.
        deviations: list[dict[str, Any]] = []  # WHY: accumulator for all engagement drift entries.
        deviations.extend(SiteAnalyticsConfigurator._compare_dwell_tags(current, standard))  # WHY: ranges.
        deviations.extend(SiteAnalyticsConfigurator._compare_dwell_tag_names(current, standard))  # WHY: labels.
        deviations.extend(SiteAnalyticsConfigurator._compare_engagement_hours(current, standard))  # WHY: hours.
        return deviations  # WHY: return combined engagement drift list.

    @staticmethod
    def _get_deviation_types(site: dict[str, Any]) -> list[str]:
        """Get list of deviation type names for a site."""  # WHY: table-driven expansion of drift flags.
        return [display for key, display in _DEVIATION_SECTIONS if site[f"{key}_deviation"]]  # WHY: single loop.

    @staticmethod
    def _print_standard_config() -> None:
        """Print the standard configuration to be applied."""  # WHY: banner shown before confirmation.
        rtsa = SiteAnalyticsConfigurator.STANDARD_RTSA  # WHY: alias avoids repeated attribute lookups below.
        rogue = SiteAnalyticsConfigurator.STANDARD_ROGUE  # WHY: alias for readability.
        occupancy = SiteAnalyticsConfigurator.STANDARD_OCCUPANCY  # WHY: alias for readability.
        wifi = SiteAnalyticsConfigurator.STANDARD_WIFI  # WHY: alias for readability.
        print("\n[STANDARD CONFIGURATION TO BE APPLIED]")  # WHY: section header.
        print(f"  RTSA: enabled={rtsa['enabled']}, track_asset={rtsa['track_asset']}, app_waking={rtsa['app_waking']}")
        print(
            f"  Rogue: enabled={rogue['enabled']}, min_rssi={rogue['min_rssi']}, min_duration={rogue['min_duration']}"
        )
        print("  Engagement dwell_tags: passerby=1-300, bounce=301-14400, engaged=14401-36000, stationed=36001-86400")
        print(f"  Analytic: enabled={SiteAnalyticsConfigurator.STANDARD_ANALYTIC['enabled']}")  # WHY: single flag.
        print(f"  Occupancy: min_duration={occupancy['min_duration']}, clients_enabled={occupancy['clients_enabled']}")
        print(
            f"  WiFi: enabled={wifi['enabled']}, locate_connected={wifi['locate_connected']}, "
            f"locate_unconnected={wifi['locate_unconnected']}"
        )

    @staticmethod
    def _display_deviation_summary(deviations: list[dict[str, Any]]) -> None:
        """Display summary of deviations found."""  # WHY: operator-facing summary block.
        print("\n" + _SEPARATOR)  # WHY: banner rule above summary.
        print("SITE ANALYTICS CONFIGURATION DEVIATIONS")  # WHY: header text.
        print(_SEPARATOR)  # WHY: banner rule below header.
        counts = SiteAnalyticsConfigurator._count_deviations(deviations)  # WHY: gather per-section totals.
        print("\n[DEVIATION SUMMARY]")  # WHY: sub-section header.
        print(f"  Total sites with deviations: {len(deviations)}")  # WHY: high-level count.
        print(f"  - RTSA: {counts['rtsa']}  - Rogue: {counts['rogue']}  - Engagement: {counts['engagement']}")
        print(f"  - Analytic: {counts['analytic']}  - Occupancy: {counts['occupancy']}  - WiFi: {counts['wifi']}")
        print(f"\n[SITES WITH DEVIATIONS] (showing first {_SUMMARY_PREVIEW_LIMIT})")  # WHY: preview header.
        for site in deviations[:_SUMMARY_PREVIEW_LIMIT]:  # WHY: capped preview to avoid flooding.
            deviation_types = SiteAnalyticsConfigurator._get_deviation_types(site)  # WHY: enum-to-labels.
            print(f"  - {site['site_name']}: {', '.join(deviation_types)}")  # WHY: preview row.
        if len(deviations) > _SUMMARY_PREVIEW_LIMIT:  # WHY: signal truncation only when necessary.
            print(f"  ... and {len(deviations) - _SUMMARY_PREVIEW_LIMIT} more sites")  # WHY: overflow hint.
        SiteAnalyticsConfigurator._print_standard_config()  # WHY: show target config before confirmation.

    @staticmethod
    def _build_deviation_row(site: dict[str, Any]) -> dict[str, Any]:
        """Build a single CSV row describing one site's deviations."""  # WHY: pure per-site row builder.
        details = "; ".join(  # WHY: comma-separated field cannot collide with CSV cell separator.
            f"{detail['section']}.{detail['key']}: {detail['current']} -> {detail['expected']}"
            for detail in site["deviation_details"][:_DEVIATION_DETAIL_LIMIT]  # WHY: cap for readability.
        )
        row: dict[str, Any] = {"site_id": site["site_id"], "site_name": site["site_name"]}  # WHY: seed row keys.
        for key, _display in _DEVIATION_SECTIONS:  # WHY: table drives yes/no flag columns.
            row[f"{key}_deviation"] = _YES_NO[bool(site[f"{key}_deviation"])]  # WHY: lookup avoids branching.
        row["deviation_count"] = len(site["deviation_details"])  # WHY: total drift entries column.
        row["deviation_details"] = details  # WHY: capped detail text column.
        return row  # WHY: single dict return keeps caller trivial.

    @staticmethod
    def _export_deviation_report(deviations: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps) -> None:
        """Export deviation report before applying changes."""  # WHY: pre-mutation evidence export.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # WHY: filename-safe timestamp.
        rows = [SiteAnalyticsConfigurator._build_deviation_row(site) for site in deviations]  # WHY: map builder.
        filename = f"SiteAnalytics_Deviations_PREVIEW_{timestamp}.csv"  # WHY: preview-tagged filename.
        deps.save_data_fn(rows, filename, api_function_name="site_analytics_deviations")  # WHY: persist rows.
        print(f"\n! Preview report exported to {filename}")  # WHY: surface path to operator.

    @staticmethod
    def _apply_simple_section(
        section_key: str,
        standard: dict[str, Any],
        current_settings: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Copy a flat standard section into current_settings and record the update."""  # WHY: shared apply.
        current_settings[section_key] = standard.copy()  # WHY: deep-enough copy for flat dict payloads.
        result["sections_updated"].append(section_key)  # WHY: track which sections were touched.

    @staticmethod
    def _apply_engagement_section(current_settings: dict[str, Any], result: dict[str, Any]) -> None:
        """Overlay engagement standard onto current settings preserving structure."""  # WHY: nested section apply.
        engagement = current_settings.setdefault("engagement", {})  # WHY: create parent dict if missing.
        engagement["dwell_tags"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["dwell_tags"].copy()  # WHY: reset.
        engagement["dwell_tag_names"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["dwell_tag_names"].copy()
        engagement["hours"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["hours"].copy()  # WHY: reset hours.
        result["sections_updated"].append("engagement")  # WHY: track which sections were touched.

    @staticmethod
    def _apply_standard_sections(
        site: dict[str, Any], current_settings: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Apply standard configuration for each deviating section."""  # WHY: dispatch per-section apply helpers.
        simple_map = {  # WHY: table drives non-engagement section apply loop.
            "rtsa": SiteAnalyticsConfigurator.STANDARD_RTSA,
            "rogue": SiteAnalyticsConfigurator.STANDARD_ROGUE,
            "analytic": SiteAnalyticsConfigurator.STANDARD_ANALYTIC,
            "occupancy": SiteAnalyticsConfigurator.STANDARD_OCCUPANCY,
            "wifi": SiteAnalyticsConfigurator.STANDARD_WIFI,
        }
        for section_key, standard in simple_map.items():  # WHY: single loop over flat sections.
            if site[f"{section_key}_deviation"]:  # WHY: only rewrite drifted sections.
                SiteAnalyticsConfigurator._apply_simple_section(section_key, standard, current_settings, result)
        if site["engagement_deviation"]:  # WHY: engagement needs nested overlay logic.
            SiteAnalyticsConfigurator._apply_engagement_section(current_settings, result)

    @staticmethod
    def _fetch_current_settings(
        site_id: str, deps: SiteAnalyticsConfiguratorDeps, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Fetch current settings for a site or record a failure into result."""  # WHY: isolates GET + error path.
        response = deps.mistapi.api.v1.sites.setting.getSiteSetting(deps.apisession, site_id=site_id)  # WHY: GET.
        if response.status_code != _HTTP_OK:  # WHY: only trust settings when API said 200.
            result["status"] = "FAILED"  # WHY: mark result as failed for reporting.
            result["error"] = f"Failed to fetch current settings: HTTP {response.status_code}"  # WHY: reason.
            return None  # WHY: signal caller to abort update path.
        return response.data if isinstance(response.data, dict) else {}  # WHY: defensive shape check.

    @staticmethod
    def _push_updated_settings(
        site_id: str,
        site_name: str,
        current_settings: dict[str, Any],
        deps: SiteAnalyticsConfiguratorDeps,
        result: dict[str, Any],
    ) -> None:
        """Push mutated settings back to Mist and record success/failure."""  # WHY: isolates PUT + error path.
        update_response = deps.mistapi.api.v1.sites.setting.updateSiteSettings(  # WHY: PUT updated payload.
            deps.apisession,
            site_id,
            body=current_settings,
        )
        if update_response.status_code == _HTTP_OK:  # WHY: 200 means the API accepted the update.
            result["status"] = "SUCCESS"  # WHY: mark success for reporting.
            logging.info("Updated %s: %s", site_name, ", ".join(result["sections_updated"]))  # WHY: audit trail.
            return  # WHY: happy path complete.
        result["status"] = "FAILED"  # WHY: non-200 means the update did not stick.
        result["error"] = f"API returned {update_response.status_code}"  # WHY: propagate HTTP status.
        logging.error("Failed to update %s: HTTP %s", site_name, update_response.status_code)  # WHY: audit trail.

    @staticmethod
    def _apply_site_config(site: dict[str, Any], deps: SiteAnalyticsConfiguratorDeps) -> dict[str, Any]:
        """Apply standard configuration to a single site."""  # WHY: orchestrate GET + mutate + PUT for one site.
        site_id = site["site_id"]  # WHY: primary key needed for both API calls.
        site_name = site["site_name"]  # WHY: display label for log lines.
        result: dict[str, Any] = {  # WHY: seed result with PENDING status; helpers mutate as needed.
            "site_id": site_id,
            "site_name": site_name,
            "status": "PENDING",
            "sections_updated": [],
            "error": None,
        }
        try:
            current_settings = SiteAnalyticsConfigurator._fetch_current_settings(site_id, deps, result)  # WHY: GET.
            if current_settings is None:  # WHY: fetch failure already recorded in result.
                return result  # WHY: short-circuit on fetch failure.
            SiteAnalyticsConfigurator._apply_standard_sections(site, current_settings, result)  # WHY: mutate.
            SiteAnalyticsConfigurator._push_updated_settings(site_id, site_name, current_settings, deps, result)
        except Exception as error:  # noqa: BLE001  # WHY: mistapi can raise varied exceptions per site.
            result["status"] = "ERROR"  # WHY: distinguish exception from HTTP failure.
            result["error"] = str(error)  # WHY: keep exception text in the CSV row.
            logging.error("Error updating %s: %s", site_name, error)  # WHY: audit trail entry.
        return result  # WHY: hand per-site result back to loop.

    @staticmethod
    def _apply_standard_configuration(
        deviations: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps
    ) -> list[dict[str, Any]]:
        """Apply standard configuration to all deviating sites."""  # WHY: outer loop across drifted sites.
        print(f"\nApplying standard configuration to {len(deviations)} sites...")  # WHY: progress hint.
        results: list[dict[str, Any]] = []  # WHY: accumulator for per-site apply outcomes.
        for site in deps.tqdm_fn(deviations, desc="Configuring sites", unit="site"):  # WHY: progress-bar wrap.
            if deps.check_stop_fn():  # WHY: cooperative cancellation between sites.
                break  # WHY: honor stop signal.
            results.append(SiteAnalyticsConfigurator._apply_site_config(site, deps))  # WHY: delegate per-site.
        success_count = sum(1 for result in results if result["status"] == "SUCCESS")  # WHY: tally wins.
        print("\n[CONFIGURATION COMPLETE]")  # WHY: end-of-run banner.
        print(f"  SUCCESS: {success_count} sites")  # WHY: success total.
        print(f"  FAILED: {len(results) - success_count} sites")  # WHY: failure total (includes ERROR).
        return results  # WHY: return outcomes to caller for export.

    @staticmethod
    def _export_results(results: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps) -> None:
        """Export configuration results."""  # WHY: post-mutation evidence export.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # WHY: filename-safe timestamp.
        rows: list[dict[str, Any]] = [  # WHY: single comprehension keeps helper short.
            {
                "site_id": result["site_id"],  # WHY: primary key column.
                "site_name": result["site_name"],  # WHY: display label column.
                "status": result["status"],  # WHY: outcome column (SUCCESS/FAILED/ERROR/PENDING).
                "sections_updated": ", ".join(result["sections_updated"]),  # WHY: comma-list of touched sections.
                "error": result["error"] or "",  # WHY: empty string keeps CSV cell tidy.
            }
            for result in results
        ]
        filename = f"SiteAnalytics_Configuration_Results_{timestamp}.csv"  # WHY: results-tagged filename.
        deps.save_data_fn(rows, filename, api_function_name="site_analytics_results")  # WHY: persist rows.
        print(f"! Results exported to {filename}")  # WHY: surface path to operator.
        success_total = sum(1 for result in results if result["status"] == "SUCCESS")  # WHY: audit tally.
        logging.info("Site analytics configuration complete. %d sites updated.", success_total)  # WHY: end audit.
