"""Site analytics configuration manager extracted from MistHelper.py."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SiteAnalyticsConfiguratorDeps:
    """Dependency container for SiteAnalyticsConfigurator execution."""

    apisession: Any
    mistapi: Any
    get_org_id_fn: Any
    check_stop_fn: Any
    safe_input_fn: Any
    all_sites_fn: Any
    save_data_fn: Any
    tqdm_fn: Any


class SiteAnalyticsConfigurator:
    """Configures site analytics settings to standard values across all sites."""

    STANDARD_RTSA = {"enabled": True, "track_asset": True, "app_waking": True}

    STANDARD_ROGUE = {
        "min_rssi": -80,
        "min_duration": 10,
        "enabled": True,
        "honeypot_enabled": True,
        "whitelisted_bssids": [],
        "whitelisted_ssids": [],
    }

    STANDARD_ENGAGEMENT = {
        "dwell_tags": {
            "passerby": "1-300",
            "bounce": "301-14400",
            "engaged": "14401-36000",
            "stationed": "36001-86400",
        },
        "dwell_tag_names": {"passerby": "", "bounce": "", "engaged": "", "stationed": ""},
        "hours": {"sun": "", "mon": "", "tue": "", "wed": "", "thu": "", "fri": "", "sat": ""},
    }

    STANDARD_ANALYTIC = {"enabled": True}

    STANDARD_OCCUPANCY = {
        "min_duration": 300,
        "clients_enabled": True,
        "sdkclients_enabled": True,
        "assets_enabled": True,
        "unconnected_clients_enabled": False,
    }

    STANDARD_WIFI = {"enabled": True, "locate_connected": True, "locate_unconnected": False}

    @staticmethod
    def execute(deps: SiteAnalyticsConfiguratorDeps) -> None:
        """Main entry point for site analytics configuration."""
        print("Site Analytics Configurator:")
        print("=" * 60)
        print("! DESTRUCTIVE OPERATION - This will modify site settings")
        print("=" * 60)
        logging.info("Starting site analytics configuration scan...")

        current_org_id = deps.get_org_id_fn()
        if not current_org_id:
            print("! No organization selected. Exiting.")
            return

        deviations = SiteAnalyticsConfigurator._scan_for_deviations(current_org_id, deps)

        if not deviations:
            print("\n[OK] All sites are configured with standard analytics settings.")
            return

        SiteAnalyticsConfigurator._display_deviation_summary(deviations)
        SiteAnalyticsConfigurator._export_deviation_report(deviations, deps)

        print("\n" + "=" * 60)
        print(f"! {len(deviations)} sites will be updated to standard configuration")
        print("=" * 60)

        try:
            confirmation = deps.safe_input_fn(
                "Type 'CONFIGURE' to apply standard settings to all deviating sites: ",
                context="site_analytics_config",
            )
        except SystemExit:
            logging.info("Site analytics configuration cancelled - session disconnected")
            return

        if confirmation != "CONFIGURE":
            print("! Operation cancelled - confirmation not provided")
            logging.warning("Site analytics configuration cancelled by user")
            return

        results = SiteAnalyticsConfigurator._apply_standard_configuration(deviations, deps)
        SiteAnalyticsConfigurator._export_results(results, deps)

    @staticmethod
    def _scan_for_deviations(org_id: str, deps: SiteAnalyticsConfiguratorDeps) -> list[dict[str, Any]]:
        """Scan all sites and identify those deviating from standard configuration."""
        logging.info("Fetching all sites for analytics configuration scan...")
        sites = deps.all_sites_fn(org_id)

        if not sites:
            logging.warning("No sites found in organization.")
            return []

        print(f"! Scanning {len(sites)} sites for configuration deviations...")

        deviations: list[dict[str, Any]] = []

        for site in deps.tqdm_fn(sites, desc="Scanning sites", unit="site"):
            site_id = site.get("id")
            site_name = site.get("name", "Unnamed Site")

            if not site_id or not isinstance(site_id, str):
                logging.warning("Invalid site_id for %s", site_name)
                continue

            if deps.check_stop_fn():
                break

            try:
                response = deps.mistapi.api.v1.sites.setting.getSiteSetting(deps.apisession, site_id=site_id)

                if response.status_code != 200:
                    logging.warning("Failed to fetch settings for %s: HTTP %s", site_name, response.status_code)
                    continue

                settings = response.data if isinstance(response.data, dict) else {}
                site_deviations = SiteAnalyticsConfigurator._check_deviations(settings, site_id, site_name)

                if site_deviations["has_deviations"]:
                    deviations.append(site_deviations)

            except Exception as error:  # noqa: BLE001
                logging.warning("Error scanning %s: %s", site_name, error)

        print(f"! Found {len(deviations)} sites with configuration deviations")
        return deviations

    @staticmethod
    def _check_rtsa_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check RTSA settings for deviations."""
        current_rtsa = settings.get("rtsa", {})
        rtsa_deviations = SiteAnalyticsConfigurator._compare_settings(
            current_rtsa,
            SiteAnalyticsConfigurator.STANDARD_RTSA,
            "rtsa",
        )
        if rtsa_deviations:
            deviation_record["rtsa_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["rtsa"] = current_rtsa
            deviation_record["deviation_details"].extend(rtsa_deviations)

    @staticmethod
    def _check_rogue_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check Rogue settings for deviations."""
        current_rogue = settings.get("rogue", {})
        rogue_deviations = SiteAnalyticsConfigurator._compare_settings(
            current_rogue,
            SiteAnalyticsConfigurator.STANDARD_ROGUE,
            "rogue",
        )
        if rogue_deviations:
            deviation_record["rogue_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["rogue"] = current_rogue
            deviation_record["deviation_details"].extend(rogue_deviations)

    @staticmethod
    def _check_engagement_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check Engagement settings for deviations."""
        current_engagement = settings.get("engagement", {})
        engagement_deviations = SiteAnalyticsConfigurator._compare_engagement(current_engagement)
        if engagement_deviations:
            deviation_record["engagement_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["engagement"] = current_engagement
            deviation_record["deviation_details"].extend(engagement_deviations)

    @staticmethod
    def _check_analytic_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check analytic settings for deviations."""
        current_analytic = settings.get("analytic", {})
        analytic_deviations = SiteAnalyticsConfigurator._compare_settings(
            current_analytic,
            SiteAnalyticsConfigurator.STANDARD_ANALYTIC,
            "analytic",
        )
        if analytic_deviations:
            deviation_record["analytic_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["analytic"] = current_analytic
            deviation_record["deviation_details"].extend(analytic_deviations)

    @staticmethod
    def _check_occupancy_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check occupancy settings for deviations."""
        current_occupancy = settings.get("occupancy", {})
        occupancy_deviations = SiteAnalyticsConfigurator._compare_settings(
            current_occupancy,
            SiteAnalyticsConfigurator.STANDARD_OCCUPANCY,
            "occupancy",
        )
        if occupancy_deviations:
            deviation_record["occupancy_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["occupancy"] = current_occupancy
            deviation_record["deviation_details"].extend(occupancy_deviations)

    @staticmethod
    def _check_wifi_deviations(deviation_record: dict[str, Any], settings: dict[str, Any]) -> None:
        """Check wifi settings for deviations."""
        current_wifi = settings.get("wifi", {})
        wifi_deviations = SiteAnalyticsConfigurator._compare_settings(
            current_wifi,
            SiteAnalyticsConfigurator.STANDARD_WIFI,
            "wifi",
        )
        if wifi_deviations:
            deviation_record["wifi_deviation"] = True
            deviation_record["has_deviations"] = True
            deviation_record["current_settings"]["wifi"] = current_wifi
            deviation_record["deviation_details"].extend(wifi_deviations)

    @staticmethod
    def _check_deviations(settings: dict[str, Any], site_id: str, site_name: str) -> dict[str, Any]:
        """Check one site's settings for deviations."""
        deviation_record = {
            "site_id": site_id,
            "site_name": site_name,
            "has_deviations": False,
            "rtsa_deviation": False,
            "rogue_deviation": False,
            "engagement_deviation": False,
            "analytic_deviation": False,
            "occupancy_deviation": False,
            "wifi_deviation": False,
            "current_settings": {},
            "deviation_details": [],
        }

        SiteAnalyticsConfigurator._check_rtsa_deviations(deviation_record, settings)
        SiteAnalyticsConfigurator._check_rogue_deviations(deviation_record, settings)
        SiteAnalyticsConfigurator._check_engagement_deviations(deviation_record, settings)
        SiteAnalyticsConfigurator._check_analytic_deviations(deviation_record, settings)
        SiteAnalyticsConfigurator._check_occupancy_deviations(deviation_record, settings)
        SiteAnalyticsConfigurator._check_wifi_deviations(deviation_record, settings)

        return deviation_record

    @staticmethod
    def _compare_settings(current: dict[str, Any], standard: dict[str, Any], section: str) -> list[dict[str, Any]]:
        """Compare current settings with standard and return list of deviations."""
        deviations: list[dict[str, Any]] = []

        for key, expected_value in standard.items():
            current_value = current.get(key)
            if current_value is None:
                deviations.append(
                    {
                        "section": section,
                        "key": key,
                        "current": "NOT SET",
                        "expected": expected_value,
                    }
                )
            elif current_value != expected_value:
                deviations.append(
                    {
                        "section": section,
                        "key": key,
                        "current": current_value,
                        "expected": expected_value,
                    }
                )

        return deviations

    @staticmethod
    def _compare_dwell_tags(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement dwell_tags settings."""
        deviations: list[dict[str, Any]] = []
        current_dwell_tags = current.get("dwell_tags", {})
        for tag_name, expected_range in standard["dwell_tags"].items():
            current_range = current_dwell_tags.get(tag_name)
            if current_range is None:
                deviations.append(
                    {
                        "section": "engagement.dwell_tags",
                        "key": tag_name,
                        "current": "NOT SET",
                        "expected": expected_range,
                    }
                )  # noqa: E501
            elif current_range != expected_range:
                deviations.append(
                    {
                        "section": "engagement.dwell_tags",
                        "key": tag_name,
                        "current": current_range,
                        "expected": expected_range,
                    }
                )  # noqa: E501
        return deviations

    @staticmethod
    def _compare_dwell_tag_names(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement dwell_tag_names settings."""
        deviations: list[dict[str, Any]] = []
        current_dwell_names = current.get("dwell_tag_names", {})
        for tag_name, expected_name in standard["dwell_tag_names"].items():
            current_name = current_dwell_names.get(tag_name)
            if current_name is not None and current_name != expected_name:
                deviations.append(
                    {
                        "section": "engagement.dwell_tag_names",
                        "key": tag_name,
                        "current": current_name,
                        "expected": expected_name,
                    }
                )  # noqa: E501
        return deviations

    @staticmethod
    def _compare_engagement_hours(current: dict[str, Any], standard: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement hours settings."""
        deviations: list[dict[str, Any]] = []
        current_hours = current.get("hours", {})
        for day_name, expected_hours in standard["hours"].items():
            current_day_hours = current_hours.get(day_name)
            if current_day_hours is not None and current_day_hours != expected_hours:
                deviations.append(
                    {
                        "section": "engagement.hours",
                        "key": day_name,
                        "current": current_day_hours,
                        "expected": expected_hours if expected_hours else "(empty)",
                    }
                )  # noqa: E501
        return deviations

    @staticmethod
    def _count_deviations(deviations: list[dict[str, Any]]) -> dict[str, int]:
        """Count sites with each type of deviation."""
        counts: dict[str, int] = {"rtsa": 0, "rogue": 0, "engagement": 0, "analytic": 0, "occupancy": 0, "wifi": 0}
        for site in deviations:
            for key in counts:
                if site.get(f"{key}_deviation"):  # Increment counter if this deviation type is set
                    counts[key] += 1
        return counts

    @staticmethod
    def _compare_engagement(current: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare engagement settings including nested dwell tags."""
        standard = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT
        deviations: list[dict[str, Any]] = []
        deviations.extend(SiteAnalyticsConfigurator._compare_dwell_tags(current, standard))
        deviations.extend(SiteAnalyticsConfigurator._compare_dwell_tag_names(current, standard))
        deviations.extend(SiteAnalyticsConfigurator._compare_engagement_hours(current, standard))
        return deviations

    @staticmethod
    def _get_deviation_types(site: dict[str, Any]) -> list[str]:
        """Get list of deviation type names for a site."""
        deviation_types: list[str] = []
        if site["rtsa_deviation"]:
            deviation_types.append("RTSA")
        if site["rogue_deviation"]:
            deviation_types.append("Rogue")
        if site["engagement_deviation"]:
            deviation_types.append("Engagement")
        if site["analytic_deviation"]:
            deviation_types.append("Analytic")
        if site["occupancy_deviation"]:
            deviation_types.append("Occupancy")
        if site["wifi_deviation"]:
            deviation_types.append("WiFi")
        return deviation_types

    @staticmethod
    def _print_standard_config() -> None:
        """Print the standard configuration to be applied."""
        print("\n[STANDARD CONFIGURATION TO BE APPLIED]")
        print(
            f"  RTSA: enabled={SiteAnalyticsConfigurator.STANDARD_RTSA['enabled']}, track_asset={SiteAnalyticsConfigurator.STANDARD_RTSA['track_asset']}, app_waking={SiteAnalyticsConfigurator.STANDARD_RTSA['app_waking']}"  # noqa: E501
        )
        print(
            f"  Rogue: enabled={SiteAnalyticsConfigurator.STANDARD_ROGUE['enabled']}, min_rssi={SiteAnalyticsConfigurator.STANDARD_ROGUE['min_rssi']}, min_duration={SiteAnalyticsConfigurator.STANDARD_ROGUE['min_duration']}"  # noqa: E501
        )
        print("  Engagement dwell_tags: passerby=1-300, bounce=301-14400, engaged=14401-36000, stationed=36001-86400")
        print(f"  Analytic: enabled={SiteAnalyticsConfigurator.STANDARD_ANALYTIC['enabled']}")
        print(
            f"  Occupancy: min_duration={SiteAnalyticsConfigurator.STANDARD_OCCUPANCY['min_duration']}, clients_enabled={SiteAnalyticsConfigurator.STANDARD_OCCUPANCY['clients_enabled']}"  # noqa: E501
        )
        print(
            f"  WiFi: enabled={SiteAnalyticsConfigurator.STANDARD_WIFI['enabled']}, locate_connected={SiteAnalyticsConfigurator.STANDARD_WIFI['locate_connected']}, locate_unconnected={SiteAnalyticsConfigurator.STANDARD_WIFI['locate_unconnected']}"  # noqa: E501
        )

    @staticmethod
    def _display_deviation_summary(deviations: list[dict[str, Any]]) -> None:
        """Display summary of deviations found."""
        print("\n" + "=" * 60)
        print("SITE ANALYTICS CONFIGURATION DEVIATIONS")
        print("=" * 60)

        counts = SiteAnalyticsConfigurator._count_deviations(deviations)

        print("\n[DEVIATION SUMMARY]")
        print(f"  Total sites with deviations: {len(deviations)}")
        print(f"  - RTSA: {counts['rtsa']}  - Rogue: {counts['rogue']}  - Engagement: {counts['engagement']}")
        print(f"  - Analytic: {counts['analytic']}  - Occupancy: {counts['occupancy']}  - WiFi: {counts['wifi']}")

        print("\n[SITES WITH DEVIATIONS] (showing first 10)")
        for site in deviations[:10]:
            deviation_types = SiteAnalyticsConfigurator._get_deviation_types(site)
            print(f"  - {site['site_name']}: {', '.join(deviation_types)}")
        if len(deviations) > 10:
            print(f"  ... and {len(deviations) - 10} more sites")

        SiteAnalyticsConfigurator._print_standard_config()

    @staticmethod
    def _export_deviation_report(deviations: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps) -> None:
        """Export deviation report before applying changes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        rows: list[dict[str, Any]] = []
        for site in deviations:
            rows.append(
                {
                    "site_id": site["site_id"],
                    "site_name": site["site_name"],
                    "rtsa_deviation": "Yes" if site["rtsa_deviation"] else "No",
                    "rogue_deviation": "Yes" if site["rogue_deviation"] else "No",
                    "engagement_deviation": "Yes" if site["engagement_deviation"] else "No",
                    "analytic_deviation": "Yes" if site["analytic_deviation"] else "No",
                    "occupancy_deviation": "Yes" if site["occupancy_deviation"] else "No",
                    "wifi_deviation": "Yes" if site["wifi_deviation"] else "No",
                    "deviation_count": len(site["deviation_details"]),
                    "deviation_details": "; ".join(
                        [
                            f"{detail['section']}.{detail['key']}: {detail['current']} -> {detail['expected']}"
                            for detail in site["deviation_details"][:5]
                        ]
                    ),
                }
            )

        filename = f"SiteAnalytics_Deviations_PREVIEW_{timestamp}.csv"
        deps.save_data_fn(rows, filename, api_function_name="site_analytics_deviations")
        print(f"\n! Preview report exported to {filename}")

    @staticmethod
    def _apply_standard_sections(
        site: dict[str, Any], current_settings: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Apply standard configuration for each deviating section."""
        if site["rtsa_deviation"]:
            current_settings["rtsa"] = SiteAnalyticsConfigurator.STANDARD_RTSA.copy()
            result["sections_updated"].append("rtsa")
        if site["rogue_deviation"]:
            current_settings["rogue"] = SiteAnalyticsConfigurator.STANDARD_ROGUE.copy()
            result["sections_updated"].append("rogue")
        if site["engagement_deviation"]:
            if "engagement" not in current_settings:
                current_settings["engagement"] = {}
            current_settings["engagement"]["dwell_tags"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT[
                "dwell_tags"
            ].copy()
            current_settings["engagement"]["dwell_tag_names"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT[
                "dwell_tag_names"
            ].copy()
            current_settings["engagement"]["hours"] = SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["hours"].copy()
            result["sections_updated"].append("engagement")
        if site["analytic_deviation"]:
            current_settings["analytic"] = SiteAnalyticsConfigurator.STANDARD_ANALYTIC.copy()
            result["sections_updated"].append("analytic")
        if site["occupancy_deviation"]:
            current_settings["occupancy"] = SiteAnalyticsConfigurator.STANDARD_OCCUPANCY.copy()
            result["sections_updated"].append("occupancy")
        if site["wifi_deviation"]:
            current_settings["wifi"] = SiteAnalyticsConfigurator.STANDARD_WIFI.copy()
            result["sections_updated"].append("wifi")

    @staticmethod
    def _apply_site_config(site: dict[str, Any], deps: SiteAnalyticsConfiguratorDeps) -> dict[str, Any]:
        """Apply standard configuration to a single site."""
        site_id = site["site_id"]
        site_name = site["site_name"]
        result = {
            "site_id": site_id,
            "site_name": site_name,
            "status": "PENDING",
            "sections_updated": [],
            "error": None,
        }

        try:
            response = deps.mistapi.api.v1.sites.setting.getSiteSetting(deps.apisession, site_id=site_id)
            if response.status_code != 200:
                result["status"] = "FAILED"
                result["error"] = f"Failed to fetch current settings: HTTP {response.status_code}"
                return result

            current_settings = response.data if isinstance(response.data, dict) else {}
            SiteAnalyticsConfigurator._apply_standard_sections(site, current_settings, result)

            update_response = deps.mistapi.api.v1.sites.setting.updateSiteSettings(
                deps.apisession,
                site_id,
                body=current_settings,
            )
            if update_response.status_code == 200:
                result["status"] = "SUCCESS"
                logging.info("Updated %s: %s", site_name, ", ".join(result["sections_updated"]))
            else:
                result["status"] = "FAILED"
                result["error"] = f"API returned {update_response.status_code}"
                logging.error("Failed to update %s: HTTP %s", site_name, update_response.status_code)
        except Exception as error:  # noqa: BLE001
            result["status"] = "ERROR"
            result["error"] = str(error)
            logging.error("Error updating %s: %s", site_name, error)

        return result

    @staticmethod
    def _apply_standard_configuration(
        deviations: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps
    ) -> list[dict[str, Any]]:
        """Apply standard configuration to all deviating sites."""
        print(f"\nApplying standard configuration to {len(deviations)} sites...")

        results: list[dict[str, Any]] = []
        for site in deps.tqdm_fn(deviations, desc="Configuring sites", unit="site"):
            if deps.check_stop_fn():
                break
            result = SiteAnalyticsConfigurator._apply_site_config(site, deps)
            results.append(result)

        success_count = sum(1 for result in results if result["status"] == "SUCCESS")
        failure_count = len(results) - success_count
        print("\n[CONFIGURATION COMPLETE]")
        print(f"  SUCCESS: {success_count} sites")
        print(f"  FAILED: {failure_count} sites")

        return results

    @staticmethod
    def _export_results(results: list[dict[str, Any]], deps: SiteAnalyticsConfiguratorDeps) -> None:
        """Export configuration results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        rows: list[dict[str, Any]] = []
        for result in results:
            rows.append(
                {
                    "site_id": result["site_id"],
                    "site_name": result["site_name"],
                    "status": result["status"],
                    "sections_updated": ", ".join(result["sections_updated"]),
                    "error": result["error"] or "",
                }
            )

        filename = f"SiteAnalytics_Configuration_Results_{timestamp}.csv"
        deps.save_data_fn(rows, filename, api_function_name="site_analytics_results")
        print(f"! Results exported to {filename}")

        logging.info(
            "Site analytics configuration complete. %d sites updated.",
            len([result for result in results if result["status"] == "SUCCESS"]),
        )
