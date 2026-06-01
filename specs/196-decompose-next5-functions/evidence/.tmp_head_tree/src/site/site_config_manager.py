"""Site configuration manager extracted from MistHelper menu 171-174 flows."""

from __future__ import annotations

import csv
import logging
import os
import time
from typing import Any

apisession: Any = None
ConfigUtils: Any = None
FilePathUtils: Any = None
InputUtils: Any = None
DataExporter: Any = None
mistapi: Any = None
DEFAULT_API_PAGE_LIMIT = 1000


def configure_site_config_manager_dependencies(
    *,
    apisession_dependency: Any,
    config_utils: Any,
    file_path_utils: Any,
    input_utils: Any,
    data_exporter: Any,
    mistapi_dependency: Any,
    default_api_page_limit: int,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global ConfigUtils
    global FilePathUtils
    global InputUtils
    global DataExporter
    global mistapi
    global DEFAULT_API_PAGE_LIMIT

    apisession = apisession_dependency
    ConfigUtils = config_utils
    FilePathUtils = file_path_utils
    InputUtils = input_utils
    DataExporter = data_exporter
    mistapi = mistapi_dependency
    DEFAULT_API_PAGE_LIMIT = default_api_page_limit


class SiteConfigManager:
    """
    Manages bulk site configuration operations including test site creation,
    RF template management, and device profile operations.

    All destructive operations require explicit user confirmation.
    """

    # -------------------------------------------------------------------------
    # Test Site Creation (Menu 171)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_test_sites_from_csv():  # type: ignore[no-untyped-def]
        """
        Create test sites from NorthAmericanTestSites.csv in the data directory.
        DESTRUCTIVE: Creates new sites in the organization.
        """
        logging.warning("Menu #171 DESTRUCTIVE: Create test sites from CSV operation started")
        SiteConfigManager._display_test_sites_header()

        if not SiteConfigManager._confirm_test_site_creation():
            return

        org_id = ConfigUtils.get_cached_or_prompted_org_id()
        if not org_id:
            logging.error("No organization ID provided - cannot create sites")
            print(" ERROR: No organization ID provided")
            return

        sites_data = SiteConfigManager._load_test_sites_csv()
        if not sites_data:
            return

        created, failed = SiteConfigManager._execute_site_creation(org_id, sites_data)
        SiteConfigManager._report_site_creation_results(sites_data, created, failed)
        logging.warning("Menu #171 complete: %s sites created, %s failed", len(created), len(failed))

    @staticmethod
    def _display_test_sites_header() -> None:
        """Display test site creation warning header."""
        print("\n========================================")
        print(" DESTRUCTIVE OPERATION WARNING")
        print("========================================")
        print(" This will CREATE 137 new test sites in your organization")
        print(" Sites span 13 North American countries:")
        print(" US, Canada, Mexico, Guatemala, Costa Rica, Panama,")
        print(" Honduras, Belize, Bahamas, Cuba, Jamaica,")
        print(" Dominican Republic, and Haiti")
        print("========================================\n")

    @staticmethod
    def _confirm_test_site_creation() -> bool:
        """Get user confirmation for test site creation."""
        confirmation = InputUtils.safe_input(
            "Type 'CREATE' (uppercase) to proceed with site creation: ", context="site creation confirmation"
        )
        if confirmation != "CREATE":
            print(" Site creation cancelled - confirmation phrase not matched")
            logging.info("Site creation cancelled by user")
            return False
        return True

    @staticmethod
    def _load_test_sites_csv() -> list[dict] | None:  # type: ignore[type-arg]
        """Load test sites from CSV file."""
        csv_file_path = FilePathUtils.get_csv_path("NorthAmericanTestSites.csv")

        if not os.path.exists(csv_file_path):
            logging.error("CSV file not found: %s", csv_file_path)
            print(f" ERROR: CSV file not found: {csv_file_path}")
            return None

        try:
            with open(csv_file_path, encoding="utf-8") as csv_file:
                sites_data = list(csv.DictReader(csv_file))
            logging.info("Loaded %s sites from CSV file", len(sites_data))
            print(f"\n Loaded {len(sites_data)} sites from CSV file")
            return sites_data
        except Exception as read_error:
            logging.error("Failed to read CSV file: %s", read_error)
            print(f" ERROR: Failed to read CSV file: {read_error}")
            return None

    @staticmethod
    def _build_site_payload(site_data: dict) -> dict | None:  # type: ignore[type-arg]
        """Build API payload from site CSV row data."""
        site_name = site_data.get("name", "").strip()
        if not site_name:
            return None

        payload = {"name": site_name}

        if site_data.get("address"):
            payload["address"] = site_data["address"].strip()
        if site_data.get("country_code"):
            payload["country_code"] = site_data["country_code"].strip()
        if site_data.get("timezone"):
            payload["timezone"] = site_data["timezone"].strip()
        if site_data.get("notes"):
            payload["notes"] = site_data["notes"].strip()

        lat_str = site_data.get("lat", "").strip()
        lng_str = site_data.get("lng", "").strip()
        if lat_str and lng_str:
            try:
                payload["latlng"] = {"lat": float(lat_str), "lng": float(lng_str)}
            except ValueError:
                pass

        return payload

    @staticmethod
    def _execute_site_creation(org_id: str, sites_data: list[dict]) -> tuple[list, list]:  # type: ignore[type-arg]
        """Execute site creation API calls. Returns (created, failed) lists."""
        created_sites = []
        failed_sites = []

        print(f"\n Creating sites in organization {org_id}...")

        for index, site_data in enumerate(sites_data, start=1):
            site_payload = SiteConfigManager._build_site_payload(site_data)
            if not site_payload:
                failed_sites.append({"row": index, "name": "MISSING", "error": "No site name"})
                continue

            site_name = site_payload["name"]
            try:
                response = mistapi.api.v1.orgs.sites.createOrgSite(apisession, org_id, body=site_payload)
                if hasattr(response, "data") and response.data:
                    created_site_id = response.data.get("id", "unknown")
                    created_sites.append({"name": site_name, "id": created_site_id, "row": index})
                    print(f" [{index}/{len(sites_data)}] Created: {site_name}")
                else:
                    failed_sites.append({"row": index, "name": site_name, "error": "No data"})
            except Exception as create_error:
                failed_sites.append({"row": index, "name": site_name, "error": str(create_error)})
                logging.error("Failed to create site %s: %s", site_name, create_error)

            time.sleep(0.5)

        return created_sites, failed_sites

    @staticmethod
    def _report_site_creation_results(sites_data: list, created: list, failed: list) -> None:  # type: ignore[type-arg]
        """Report and export site creation results."""
        print("\n========================================")
        print(" SITE CREATION SUMMARY")
        print("========================================")
        print(f" Total sites in CSV: {len(sites_data)}")
        print(f" Successfully created: {len(created)}")
        print(f" Failed: {len(failed)}")
        print("========================================\n")

        if created:
            DataExporter.save_data_to_output(created, "CreatedTestSites.csv")  # type: ignore[no-untyped-call]
            print(" Created sites exported to CreatedTestSites.csv")
        if failed:
            DataExporter.save_data_to_output(failed, "FailedTestSites.csv")  # type: ignore[no-untyped-call]
            print(" Failed sites exported to FailedTestSites.csv")

    # -------------------------------------------------------------------------
    # RF Template Creation (Menu 172)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_country_rf_templates_and_assign():  # type: ignore[no-untyped-def]
        """
        Create country-specific RF templates and assign sites to matching templates.
        DESTRUCTIVE: Creates RF templates and modifies site assignments.
        """
        logging.warning("Menu #172 DESTRUCTIVE: Create country RF templates operation started")
        SiteConfigManager._display_rf_template_header()

        if not apisession:
            logging.error("API session not initialized")
            print(" ERROR: Mist API session not initialized")
            return

        org_id = ConfigUtils.get_cached_or_prompted_org_id()
        if not org_id:
            return

        analysis = SiteConfigManager._analyze_sites_for_rf_templates(org_id)
        if not analysis:
            return

        sites_by_country, sites_without_country, existing_templates = analysis
        plan = SiteConfigManager._plan_rf_template_operations(sites_by_country, existing_templates)
        if not plan:
            return

        templates_to_create, templates_to_update, update_mode = plan

        if not SiteConfigManager._confirm_rf_template_operation(
            templates_to_create, templates_to_update, sites_by_country, update_mode
        ):
            return

        template_mapping = SiteConfigManager._execute_rf_template_operations(
            org_id, templates_to_create, templates_to_update, update_mode
        )

        success, failed = SiteConfigManager._assign_sites_to_rf_templates(sites_by_country, template_mapping)

        SiteConfigManager._report_rf_template_results(
            templates_to_create, templates_to_update, update_mode, success, failed, sites_without_country
        )
        logging.warning(
            "Menu #172 complete: %s templates created, %s sites assigned, %s failed",
            len(templates_to_create),
            len(success),
            len(failed),
        )

    @staticmethod
    def _display_rf_template_header() -> None:
        """Display RF template operation header."""
        print("\n" + "=" * 70)
        print(" Menu 108: Create Country-Specific RF Templates and Assign")
        print("=" * 70)

    @staticmethod
    def _analyze_sites_for_rf_templates(org_id: str) -> tuple | None:  # type: ignore[type-arg]
        """Analyze organization sites and existing RF templates."""
        print("\n  Step 1: Scanning organization sites for unique country codes...")

        try:
            sites_response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)
            sites = mistapi.get_all(response=sites_response, mist_session=apisession)

            if not sites:
                print(" No sites found in organization.")
                return None

            print(f" Found {len(sites)} sites in organization")
        except Exception as error:
            logging.error("Failed to fetch sites: %s", error)
            print(f" ERROR: Failed to fetch sites - {error}")
            return None

        sites_by_country: dict[str, list[dict[str, Any]]] = {}
        sites_without_country: list[dict[str, Any]] = []

        for site in sites:
            country_code = site.get("country_code", "").strip().upper()
            site_info = {"id": site.get("id"), "name": site.get("name", "Unknown")}

            if country_code:
                if country_code not in sites_by_country:
                    sites_by_country[country_code] = []
                sites_by_country[country_code].append(site_info)
            else:
                sites_without_country.append(site_info)

        if not sites_by_country:
            print(" WARNING: No sites have country codes assigned.")
            return None

        print(f"\n  Found {len(sites_by_country)} unique countries:")
        for country in sorted(sites_by_country.keys()):
            print(f"   - {country}: {len(sites_by_country[country])} sites")

        if sites_without_country:
            print(f"\n  WARNING: {len(sites_without_country)} sites have no country code")

        print("\n  Step 2: Checking for existing RF templates...")
        try:
            templates_response = mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates(
                apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT
            )
            existing = mistapi.get_all(response=templates_response, mist_session=apisession) or []
            existing_templates = {t.get("name"): t.get("id") for t in existing}
        except Exception as error:
            logging.error("Failed to fetch RF templates: %s", error)
            return None

        return sites_by_country, sites_without_country, existing_templates

    @staticmethod
    def _plan_rf_template_operations(sites_by_country: dict, existing_templates: dict) -> tuple | None:  # type: ignore[type-arg]
        """Plan which RF templates to create vs update."""
        templates_to_create = []
        templates_to_update = []

        for country in sorted(sites_by_country.keys()):
            template_name = f"RF-{country}"
            if template_name in existing_templates:
                templates_to_update.append(
                    {"country": country, "name": template_name, "id": existing_templates[template_name]}
                )
            else:
                templates_to_create.append({"country": country, "name": template_name})

        update_mode = "skip"
        if templates_to_update:
            print(f"\n  Found {len(templates_to_update)} existing RF templates:")
            for template in templates_to_update[:5]:
                print(f"   - {template['name']}")

            print("\n  How should existing templates be handled?")
            print("   1. SKIP - Keep existing templates as-is (recommended)")
            print("   2. UPDATE - Update existing templates (DESTRUCTIVE)")

            while True:
                choice = InputUtils.safe_input("\n  Enter choice (1 or 2): ", "rf_update_mode").strip()
                if choice == "1":
                    update_mode = "skip"
                    break
                if choice == "2":
                    update_mode = "update"
                    break
                print("  Invalid choice.")

        return templates_to_create, templates_to_update, update_mode

    @staticmethod
    def _confirm_rf_template_operation(  # type: ignore[type-arg]
        to_create: list,
        to_update: list,
        sites_by_country: dict,
        update_mode: str,
    ) -> bool:
        """Confirm RF template operation with user."""
        print("\n  " + "!" * 66)
        print("  WARNING: DESTRUCTIVE OPERATION")
        print("  " + "!" * 66)

        if to_create:
            print(f"  - CREATE {len(to_create)} new RF templates")
        if update_mode == "update" and to_update:
            print(f"  - UPDATE {len(to_update)} existing RF templates")

        total_sites = sum(len(sites) for sites in sites_by_country.values())
        print(f"  - ASSIGN {total_sites} sites to country templates")
        print("  " + "!" * 66)

        confirmation = InputUtils.safe_input("\n  Type 'CREATE' to proceed: ", "rf_template_confirm")
        return confirmation == "CREATE"

    @staticmethod
    def _build_rf_template_payload(country: str, template_name: str) -> dict:  # type: ignore[type-arg]
        """Build RF template API payload with auto settings."""
        return {
            "name": template_name,
            "country_code": country,
            "band_24": {"disabled": False, "bandwidth": 20, "preamble": "short"},
            "band_5": {"disabled": False, "bandwidth": 40, "preamble": "short"},
            "band_6": {"disabled": False, "bandwidth": 80, "preamble": "short"},
            "band_24_usage": "auto",
        }

    @staticmethod
    def _execute_rf_template_operations(org_id: str, to_create: list, to_update: list, update_mode: str) -> dict:  # type: ignore[type-arg]
        """Execute RF template create/update operations. Returns country->template mapping."""
        template_mapping = {}

        if update_mode == "update":
            for template_info in to_update:
                country = template_info["country"]
                payload = SiteConfigManager._build_rf_template_payload(country, template_info["name"])
                try:
                    response = mistapi.api.v1.orgs.rftemplates.updateOrgRfTemplate(
                        apisession, org_id, template_info["id"], body=payload
                    )
                    if response.status_code == 200:
                        template_mapping[country] = {"id": template_info["id"], "name": template_info["name"]}
                        print(f"  Updated: {template_info['name']}")
                    time.sleep(0.5)
                except Exception as error:
                    logging.error("Failed to update template %s: %s", template_info["name"], error)
        else:
            for template_info in to_update:
                template_mapping[template_info["country"]] = {
                    "id": template_info["id"],
                    "name": template_info["name"],
                }

        for template_info in to_create:
            country = template_info["country"]
            payload = SiteConfigManager._build_rf_template_payload(country, template_info["name"])
            try:
                response = mistapi.api.v1.orgs.rftemplates.createOrgRfTemplate(apisession, org_id, payload)
                if response.status_code == 200:
                    created_id = response.data.get("id")
                    template_mapping[country] = {"id": created_id, "name": template_info["name"]}
                    print(f" Created: {template_info['name']}")
                time.sleep(0.5)
            except Exception as error:
                logging.error("Failed to create template %s: %s", template_info["name"], error)

        return template_mapping

    @staticmethod
    def _assign_sites_to_rf_templates(sites_by_country: dict, template_mapping: dict) -> tuple[list, list]:  # type: ignore[type-arg]
        """Assign sites to their country RF templates."""
        success: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for country, sites in sites_by_country.items():
            if country not in template_mapping:
                continue

            template_id = template_mapping[country]["id"]
            template_name = template_mapping[country]["name"]

            for site_info in sites:
                if ConfigUtils.check_stop_signal():
                    return success, failed
                try:
                    response = mistapi.api.v1.sites.sites.updateSiteInfo(
                        apisession, site_info["id"], body={"rftemplate_id": template_id}
                    )
                    if response.status_code == 200:
                        success.append(
                            {"site_name": site_info["name"], "country": country, "template_name": template_name}
                        )
                    else:
                        failed.append({"site_name": site_info["name"], "error": f"HTTP {response.status_code}"})
                    time.sleep(0.3)
                except Exception as error:
                    failed.append({"site_name": site_info["name"], "error": str(error)})

        return success, failed

    @staticmethod
    def _report_rf_template_results(  # type: ignore[type-arg]
        created: list,
        updated: list,
        update_mode: str,
        success: list,
        failed: list,
        skipped: list,
    ) -> None:
        """Report RF template operation results."""
        print("\n" + "=" * 70)
        print(" OPERATION COMPLETE")
        print("=" * 70)
        print(f"  RF Templates Created: {len(created)}")
        if update_mode == "update":
            print(f"  RF Templates Updated: {len(updated)}")
        else:
            print(f"  RF Templates Existing: {len(updated)}")
        print(f"  Sites Successfully Assigned: {len(success)}")
        print(f"  Sites Failed: {len(failed)}")
        print(f"  Sites Skipped (no country): {len(skipped)}")

        if success:
            DataExporter.save_data_to_output(success, "SuccessfulRFTemplateAssignments.csv")  # type: ignore[no-untyped-call]
        if failed:
            DataExporter.save_data_to_output(failed, "FailedRFTemplateAssignments.csv")  # type: ignore[no-untyped-call]

    # -------------------------------------------------------------------------
    # Device Profile Creation (Menu 173)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_ap_model_device_profiles():  # type: ignore[no-untyped-def]
        """
        Create Device Profile for each unique AP model in the organization.
        DESTRUCTIVE: Creates new device profiles.
        """
        logging.warning("Menu #173 DESTRUCTIVE: Create AP model device profiles operation started")
        SiteConfigManager._display_device_profile_header()

        org_id = ConfigUtils.get_cached_or_prompted_org_id()

        ap_models, models_without_info = SiteConfigManager._analyze_ap_models(org_id)
        if not ap_models:
            return

        existing_profiles = SiteConfigManager._get_existing_device_profiles(org_id)
        if existing_profiles is None:
            return

        to_create, to_skip = SiteConfigManager._plan_profile_creation(ap_models, existing_profiles)

        if not to_create:
            print("\n  All AP model Device Profiles already exist.")
            return

        if not SiteConfigManager._confirm_profile_creation(to_create, to_skip):
            return

        created, failed = SiteConfigManager._execute_profile_creation(org_id, to_create)
        SiteConfigManager._report_profile_creation_results(created, failed, to_skip)
        logging.warning("Menu #173 complete: %s profiles created, %s failed", len(created), len(failed))

    @staticmethod
    def _display_device_profile_header() -> None:
        """Display device profile creation header."""
        print("\n" + "=" * 70)
        print(" CREATE AP MODEL DEVICE PROFILES")
        print("=" * 70)

    @staticmethod
    def _analyze_ap_models(org_id: str) -> tuple[set, list]:  # type: ignore[type-arg]
        """Analyze organization inventory for unique AP models."""
        print("\n  Step 1: Scanning organization for AP device models...")

        try:
            inventory_response = mistapi.api.v1.orgs.inventory.getOrgInventory(
                apisession, org_id, type="ap", limit=DEFAULT_API_PAGE_LIMIT
            )
            all_devices = mistapi.get_all(response=inventory_response, mist_session=apisession) or []
        except Exception as error:
            logging.error("Failed to fetch inventory: %s", error)
            print(f" ERROR: Failed to fetch inventory - {error}")
            return set(), []

        if not all_devices:
            print(" No AP devices found in organization.")
            return set(), []

        ap_models = set()
        models_without_info = []

        for device in all_devices:
            model = device.get("model")
            if model:
                ap_models.add(model)
            else:
                models_without_info.append(device.get("name", device.get("mac", "unknown")))

        print(f"\n  Found {len(ap_models)} unique AP models:")
        for model in sorted(ap_models):
            print(f"   - {model}")

        return ap_models, models_without_info

    @staticmethod
    def _get_existing_device_profiles(org_id: str) -> dict | None:  # type: ignore[type-arg]
        """Get existing device profiles from organization."""
        print("\n  Step 2: Checking for existing Device Profiles...")

        try:
            profiles_response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                apisession, org_id, type="ap", limit=DEFAULT_API_PAGE_LIMIT
            )
            existing = mistapi.get_all(response=profiles_response, mist_session=apisession) or []
            return {profile.get("name"): profile.get("id") for profile in existing}
        except Exception as error:
            logging.error("Failed to fetch device profiles: %s", error)
            print(f" ERROR: Failed to fetch device profiles - {error}")
            return None

    @staticmethod
    def _plan_profile_creation(ap_models: set, existing_profiles: dict) -> tuple[list, list]:  # type: ignore[type-arg]
        """Plan which profiles to create vs skip."""
        to_create = []
        to_skip = []

        for model in sorted(ap_models):
            profile_name = f"AP-{model}"
            if profile_name in existing_profiles:
                to_skip.append({"model": model, "name": profile_name, "id": existing_profiles[profile_name]})
            else:
                to_create.append({"model": model, "name": profile_name})

        if to_skip:
            print(f"\n  Found {len(to_skip)} existing Device Profiles (will skip)")
        if to_create:
            print(f"\n  Will create {len(to_create)} new Device Profiles")

        return to_create, to_skip

    @staticmethod
    def _confirm_profile_creation(to_create: list, to_skip: list) -> bool:  # type: ignore[type-arg]
        """Confirm device profile creation with user."""
        print("\n  " + "!" * 66)
        print("  WARNING: DESTRUCTIVE OPERATION")
        print("  " + "!" * 66)
        print(f"  This will CREATE {len(to_create)} new Device Profiles")
        print("  " + "!" * 66)

        confirmation = InputUtils.safe_input("\n  Type 'CREATE' to proceed: ", "profile_creation")
        return confirmation == "CREATE"

    @staticmethod
    def _execute_profile_creation(org_id: str, to_create: list) -> tuple[list, list]:  # type: ignore[type-arg]
        """Execute device profile creation. Returns (created, failed) lists."""
        created: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        print(f"\n  Step 3: Creating {len(to_create)} new Device Profiles...")

        for profile_info in to_create:
            payload = {"name": profile_info["name"], "type": "ap"}
            try:
                response = mistapi.api.v1.orgs.deviceprofiles.createOrgDeviceProfile(apisession, org_id, body=payload)
                if response.status_code == 200:
                    created_id = response.data.get("id")
                    created.append({"model": profile_info["model"], "name": profile_info["name"], "id": created_id})
                    print(f"  Created: {profile_info['name']}")
                else:
                    failed.append(
                        {
                            "model": profile_info["model"],
                            "name": profile_info["name"],
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                time.sleep(0.5)
            except Exception as error:
                failed.append({"model": profile_info["model"], "name": profile_info["name"], "error": str(error)})

        return created, failed

    @staticmethod
    def _report_profile_creation_results(created: list, failed: list, skipped: list) -> None:  # type: ignore[type-arg]
        """Report device profile creation results."""
        print("\n" + "=" * 70)
        print(" OPERATION COMPLETE")
        print("=" * 70)
        print(f"  Device Profiles Created: {len(created)}")
        print(f"  Device Profiles Failed: {len(failed)}")
        print(f"  Device Profiles Skipped: {len(skipped)}")

        if created:
            DataExporter.save_data_to_output(created, "CreatedAPModelDeviceProfiles.csv")  # type: ignore[no-untyped-call]
        if failed:
            DataExporter.save_data_to_output(failed, "FailedAPModelDeviceProfiles.csv")  # type: ignore[no-untyped-call]

    # -------------------------------------------------------------------------
    # Device Profile Assignment (Menu 174)
    # -------------------------------------------------------------------------
    @staticmethod
    def assign_aps_to_matching_device_profiles():  # type: ignore[no-untyped-def]
        """
        Assign AP devices to Device Profiles matching their model type.
        DESTRUCTIVE: Modifies device assignments.
        """
        logging.warning("Menu #174 DESTRUCTIVE: Assign APs to device profiles operation started")
        SiteConfigManager._display_profile_assignment_header()

        org_id = ConfigUtils.get_cached_or_prompted_org_id()

        all_aps = SiteConfigManager._fetch_ap_inventory(org_id)
        if not all_aps:
            return

        profile_map = SiteConfigManager._fetch_profile_map(org_id)
        if not profile_map:
            return

        with_profile, without_profile, without_model = SiteConfigManager._analyze_ap_profile_matching(
            all_aps, profile_map
        )

        if not with_profile:
            print("\n  No APs have matching Device Profiles to assign.")
            return

        if not SiteConfigManager._confirm_profile_assignment(with_profile, without_profile):
            return

        success, failed = SiteConfigManager._execute_profile_assignment(org_id, with_profile)
        SiteConfigManager._report_profile_assignment_results(success, failed, without_profile, without_model)
        logging.warning("Menu #174 complete: %s APs assigned, %s failed", len(success), len(failed))

    @staticmethod
    def _display_profile_assignment_header() -> None:
        """Display profile assignment header."""
        print("\n" + "=" * 70)
        print(" ASSIGN APS TO MATCHING DEVICE PROFILES")
        print("=" * 70)

    @staticmethod
    def _fetch_ap_inventory(org_id: str) -> list | None:  # type: ignore[type-arg]
        """Fetch AP inventory from organization."""
        print("\n  Step 1: Fetching AP inventory from organization...")

        try:
            inventory_response = mistapi.api.v1.orgs.inventory.getOrgInventory(
                apisession, org_id, type="ap", limit=DEFAULT_API_PAGE_LIMIT
            )
            all_aps = mistapi.get_all(response=inventory_response, mist_session=apisession) or []

            if not all_aps:
                print(" No APs found in organization inventory.")
                return None

            print(f"  Found {len(all_aps)} APs in organization")
            return all_aps
        except Exception as error:
            logging.error("Failed to fetch AP inventory: %s", error)
            print(f" ERROR: Failed to fetch AP inventory - {error}")
            return None

    @staticmethod
    def _fetch_profile_map(org_id: str) -> dict | None:  # type: ignore[type-arg]
        """Fetch device profiles and return name->id mapping."""
        print("\n  Step 2: Fetching existing Device Profiles...")

        try:
            profiles_response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                apisession, org_id, type="ap", limit=DEFAULT_API_PAGE_LIMIT
            )
            existing = mistapi.get_all(response=profiles_response, mist_session=apisession) or []

            profile_map = {
                profile.get("name"): profile.get("id")
                for profile in existing
                if profile.get("name") and profile.get("id")
            }

            if not profile_map:
                print(" No Device Profiles found in organization.")
                return None

            print(f"  Found {len(profile_map)} Device Profiles")
            return profile_map
        except Exception as error:
            logging.error("Failed to fetch Device Profiles: %s", error)
            print(f" ERROR: Failed to fetch Device Profiles - {error}")
            return None

    @staticmethod
    def _analyze_ap_profile_matching(all_aps: list, profile_map: dict) -> tuple[list, list, list]:  # type: ignore[type-arg]
        """Analyze which APs can be assigned to profiles."""
        with_profile = []
        without_profile = []
        without_model = []

        for access_point in all_aps:
            ap_mac = access_point.get("mac", "unknown")
            ap_name = access_point.get("name", ap_mac)
            ap_model = access_point.get("model")

            if not ap_model:
                without_model.append({"mac": ap_mac, "name": ap_name})
                continue

            expected_profile = f"AP-{ap_model}"
            if expected_profile in profile_map:
                with_profile.append(
                    {
                        "mac": ap_mac,
                        "name": ap_name,
                        "model": ap_model,
                        "profile_name": expected_profile,
                        "profile_id": profile_map[expected_profile],
                    }
                )
            else:
                without_profile.append(
                    {"mac": ap_mac, "name": ap_name, "model": ap_model, "expected_profile": expected_profile}
                )

        print("\n  Analysis:")
        print(f"   APs with matching profiles: {len(with_profile)}")
        print(f"   APs without matching profiles: {len(without_profile)}")
        print(f"   APs without model info: {len(without_model)}")

        return with_profile, without_profile, without_model

    @staticmethod
    def _confirm_profile_assignment(with_profile: list, without_profile: list) -> bool:  # type: ignore[type-arg]
        """Confirm profile assignment with user."""
        print("\n  " + "!" * 66)
        print("  WARNING: DESTRUCTIVE OPERATION")
        print("  " + "!" * 66)
        print(f"  This will ASSIGN {len(with_profile)} APs to their matching Device Profiles")
        print(f"  APs without matching profiles will be SKIPPED: {len(without_profile)}")
        print("  " + "!" * 66)

        confirmation = InputUtils.safe_input("\n  Type 'ASSIGN' to proceed: ", "profile_assignment")
        return confirmation == "ASSIGN"

    @staticmethod
    def _execute_profile_assignment(org_id: str, with_profile: list) -> tuple[list, list]:  # type: ignore[type-arg]
        """Execute profile assignment API calls."""
        success: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        print(f"\n  Step 3: Assigning {len(with_profile)} APs to Device Profiles...")

        for ap_info in with_profile:
            try:
                response = mistapi.api.v1.orgs.deviceprofiles.assignOrgDeviceProfile(
                    apisession, org_id, ap_info["profile_id"], body={"macs": [ap_info["mac"]]}
                )
                if response.status_code == 200:
                    success.append(
                        {
                            "mac": ap_info["mac"],
                            "name": ap_info["name"],
                            "model": ap_info["model"],
                            "profile_name": ap_info["profile_name"],
                        }
                    )
                else:
                    failed.append(
                        {"mac": ap_info["mac"], "name": ap_info["name"], "error": f"HTTP {response.status_code}"}
                    )
                time.sleep(0.3)
            except Exception as error:
                failed.append({"mac": ap_info["mac"], "name": ap_info["name"], "error": str(error)})

        return success, failed

    @staticmethod
    def _report_profile_assignment_results(  # type: ignore[type-arg]
        success: list,
        failed: list,
        without_profile: list,
        without_model: list,
    ) -> None:
        """Report profile assignment results."""
        print("\n" + "=" * 70)
        print(" OPERATION COMPLETE")
        print("=" * 70)
        print(f"  APs Successfully Assigned: {len(success)}")
        print(f"  APs Failed: {len(failed)}")
        print(f"  APs Skipped (no matching profile): {len(without_profile)}")
        print(f"  APs Skipped (no model info): {len(without_model)}")

        if success:
            DataExporter.save_data_to_output(success, "SuccessfulAPProfileAssignments.csv")  # type: ignore[no-untyped-call]
        if failed:
            DataExporter.save_data_to_output(failed, "FailedAPProfileAssignments.csv")  # type: ignore[no-untyped-call]
        if without_profile:
            DataExporter.save_data_to_output(without_profile, "SkippedAPsNoMatchingProfile.csv")  # type: ignore[no-untyped-call]
