"""Gateway template configuration management for MistHelper.

Extracts GatewayTemplateConfigManager (Menu #105, #106, #111) from
MistHelper.py into a class with dependency injection for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations

import csv
import json
import logging
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import mistapi
from tqdm import tqdm


class GatewayTemplateConfigManager:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Manage gateway template config extraction, application, and cloning.

    Supports three operations:
    - extract (Menu 105): Extract DIA_Pico and Picocell configs to JSON
    - apply (Menu 106): Apply extracted configs to other templates
    - clone_by_location (Menu 111): Clone template per state/country
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        org_id: str,
        apisession: Any,
        input_fn: Callable[..., str],
        get_csv_path_fn: Callable[[str], str],
        save_data_fn: Callable[..., Any],
        check_and_generate_csv_fn: Callable[..., Any],
        generate_sites_fn: Callable[..., Any],
        sanitize_filename_fn: Callable[[str], str],
    ) -> None:
        """Initialize with all external dependencies.

        Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            input_fn: User input function with (prompt, context=) signature.
            get_csv_path_fn: Resolves CSV filenames to full paths.
            save_data_fn: Writes data to output files.
            check_and_generate_csv_fn: Cache check/generation function.
            generate_sites_fn: Sites CSV generator.
            sanitize_filename_fn: Sanitize filenames for safe filesystem use.
        """
        self._org_id = org_id
        self._api = apisession
        self._input_fn = input_fn
        self._get_csv_path = get_csv_path_fn
        self._save_data = save_data_fn
        self._check_csv = check_and_generate_csv_fn
        self._gen_sites = generate_sites_fn
        self._sanitize = sanitize_filename_fn

    # ------------------------------------------------------------------ #
    # Public entry points                                                 #
    # ------------------------------------------------------------------ #

    def extract(self) -> None:
        """Menu 105: Extract DIA_Pico and Picocell configs from a template."""
        print("\n  Extract Gateway Template Configuration (Menu 105)")
        print("=" * 70)
        logging.info("Menu #105: Starting gateway template configuration extraction")

        templates = self._fetch_templates()
        if not templates:
            return

        selected = self._select_template(templates, "extract")
        if not selected:
            return

        template_config = self._fetch_template_config(selected)
        if not template_config:
            return

        extraction = self._extract_configs(template_config, selected)
        if extraction:
            self._save_extraction(extraction, selected)

    def apply(self) -> None:
        """Menu 106: Apply extracted configuration to gateway templates."""
        print("\n  DESTRUCTIVE: Apply Gateway Template Configuration (Menu 106)")
        print("=" * 70)
        print("  !? WARNING: This operation modifies gateway templates")
        print("  !? Requires uppercase 'APPLY' confirmation")
        print("=" * 70)

        logging.warning("Menu #106 DESTRUCTIVE: Apply Gateway Template Configuration started")

        extraction_data = self._load_extraction_file()
        if not extraction_data:
            return

        templates = self._fetch_templates()
        if not templates:
            return

        destinations = self._select_destination_templates(templates, extraction_data)
        if not destinations:
            return

        configs = extraction_data.get("configurations", {})
        dia_pico = configs.get("traffic_steering", {}).get("DIA_Pico")
        picocell = configs.get("application_policies", {}).get("Picocell")

        if not self._confirm_apply(destinations, dia_pico, picocell):
            return

        results = self._apply_to_templates(destinations, dia_pico, picocell)
        self._report_apply_results(results)

    def clone_by_location(self) -> None:
        """Menu 111: Clone template per state/country and assign sites."""
        print("\n  DESTRUCTIVE: Clone Gateway Templates by State and Country")
        print("=" * 70)
        print("  !? WARNING: This operation creates new gateway templates")
        print("  !? WARNING: This operation modifies site template assignments")
        print("  !? Ensure source template is properly configured before cloning")
        print("=" * 70)

        logging.warning("Menu #111 DESTRUCTIVE: Clone Gateway Templates by " "State/Country operation started")

        sites = self._load_sites_with_location()
        if not sites:
            return

        states, countries = self._get_unique_locations(sites)

        templates = self._fetch_templates()
        if not templates:
            return

        source = self._select_template(templates, "clone")
        if not source:
            return

        source_config = self._fetch_template_config(source)
        if not source_config:
            return

        to_create = self._plan_template_creation(source, states, countries)
        assignments = self._plan_site_assignments(sites, source)

        if not self._confirm_clone(to_create, assignments):
            return

        existing = self._get_existing_template_names()
        tpl_map = self._create_templates(source_config, to_create, existing)
        results = self._assign_sites(assignments, tpl_map)

        self._report_clone_results(to_create, results)

    # ------------------------------------------------------------------ #
    # Template fetching and selection                                     #
    # ------------------------------------------------------------------ #

    def _fetch_templates(self) -> list[dict[str, Any]] | None:
        """Fetch all gateway templates for the organization."""
        print("\n  Fetching gateway templates...")
        try:
            response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(self._api, self._org_id, limit=1000)
            templates = mistapi.get_all(response=response, mist_session=self._api)

            if not templates:
                print("  No gateway templates found for this organization.")
                logging.warning("GatewayTemplateConfigManager: No gateway templates found")
                return None

            return sorted(
                templates,
                key=lambda t: t.get("name", "Unnamed Template").lower(),
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"  Error fetching gateway templates: {error}")
            logging.error(f"GatewayTemplateConfigManager: Failed to fetch templates: " f"{error}")
            return None

    def _select_template(
        self,
        templates: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any] | None:
        """Display and select a template from the list."""
        print(f"\n  Available Gateway Templates ({len(templates)} found):")
        print("-" * 70)

        for index, template in enumerate(templates):
            name = template.get("name", "Unnamed Template")
            template_type = template.get("type", "standalone")
            print(f"  [{index}] {name:40} Type: {template_type}")

        print()
        try:
            user_input = self._input_fn(
                f"Enter template index to {operation} " f"[0-{len(templates) - 1}]: ",
                context=f"gateway_template_{operation}_selection",
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operation cancelled.")
            return None

        if not user_input.isdigit():
            print("  Invalid input. Please enter a numeric index.")
            return None

        index = int(user_input)
        if index < 0 or index >= len(templates):
            print(f"  Invalid index. Please select between 0 " f"and {len(templates) - 1}.")
            return None

        selected = templates[index]
        print(f"\n  Selected Template: {selected.get('name', 'Unnamed')}")
        return selected

    # ------------------------------------------------------------------ #
    # Extract helpers                                                     #
    # ------------------------------------------------------------------ #

    def _fetch_template_config(self, template: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch full configuration for a template."""
        template_id = template.get("id")
        template_name = template.get("name", "Unnamed Template")

        print("\n  Fetching full template configuration...")
        try:
            response = mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(self._api, self._org_id, template_id)
            config = response.data if hasattr(response, "data") else {}

            if not isinstance(config, dict):
                print("  Error: Template configuration is not in " "expected format.")
                logging.error(f"GatewayTemplateConfigManager: Invalid config " f"format for {template_name}")
                return None

            return config
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"  Error fetching template configuration: {error}")
            logging.error(f"GatewayTemplateConfigManager: Failed to fetch " f"{template_name}: {error}")
            return None

    @staticmethod
    def _extract_configs(
        template_config: dict[str, Any],
        template: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Extract DIA_Pico and Picocell configurations from template."""
        template_name = template.get("name", "Unnamed")

        print("\n  Extracting Traffic Steering configuration...")
        path_prefs = template_config.get("path_preferences", {})
        dia_pico = path_prefs.get("DIA_Pico") if isinstance(path_prefs, dict) else None

        if dia_pico:
            print("  -> Found 'DIA_Pico' in Traffic Steering")
            logging.info(f"GatewayTemplateConfigManager: Found DIA_Pico " f"in {template_name}")
        else:
            print("  -> 'DIA_Pico' not found in Traffic Steering")

        picocell = _find_picocell_policy(template_config, template_name)

        if not dia_pico and not picocell:
            print("\n  Warning: Neither 'DIA_Pico' nor 'Picocell' " "configurations were found.")
            return None

        return {
            "source_template_name": template_name,
            "source_template_id": template.get("id"),
            "extraction_timestamp": datetime.now(UTC).isoformat(),
            "extracted_by": "MistHelper Menu #105",
            "configurations": {
                "traffic_steering": {"DIA_Pico": dia_pico},
                "application_policies": {"Picocell": picocell},
            },
        }

    def _save_extraction(
        self,
        extraction: dict[str, Any],
        template: dict[str, Any],
    ) -> None:
        """Save extraction data to JSON file."""
        template_name = template.get("name", "Unnamed")
        safe_name = self._sanitize(template_name)
        json_filename = f"{safe_name}_extracted_config.json"
        json_filepath = self._get_csv_path(json_filename)

        try:
            with open(json_filepath, "w", encoding="utf-8") as fout:
                json.dump(extraction, fout, indent=2, ensure_ascii=False)

            print("\n  Success! Configuration extracted and saved to:")
            print(f"  -> {json_filepath}")
            print("\n  Use Menu Option 106 to apply this configuration " "to other templates.")
            logging.info(f"GatewayTemplateConfigManager: Saved extraction " f"to {json_filepath}")
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n  Error saving extraction file: {error}")
            logging.error(f"GatewayTemplateConfigManager: Failed to save JSON: " f"{error}")

    # ------------------------------------------------------------------ #
    # Apply helpers                                                       #
    # ------------------------------------------------------------------ #

    def _load_extraction_file(self) -> dict[str, Any] | None:
        """Load a previously saved extraction JSON file."""
        print("\n  Step 1: Finding extraction files...")

        data_dir = self._get_csv_path("")
        extraction_files: list[str] = []

        try:
            for filename in os.listdir(data_dir):
                if filename.endswith("_extracted_config.json"):
                    extraction_files.append(filename)
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"  Error reading data directory: {error}")
            return None

        if not extraction_files:
            print("  No extraction files found. Run Menu #105 first.")
            return None

        extraction_files.sort()
        return self._prompt_file_selection(extraction_files)

    def _prompt_file_selection(self, files: list[str]) -> dict[str, Any] | None:
        """Prompt user to select an extraction file and load it."""
        print(f"\n  Available extraction files ({len(files)}):")
        for idx, filename in enumerate(files):
            print(f"  [{idx}] {filename}")

        try:
            selection = self._input_fn(
                f"\n  Select extraction file [0-{len(files) - 1}]: ",
                context="menu_106_file_selection",
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operation cancelled.")
            return None

        if not selection.isdigit() or int(selection) >= len(files):
            print("  Invalid selection.")
            return None

        selected_file = files[int(selection)]
        filepath = os.path.join(self._get_csv_path(""), selected_file)

        try:
            with open(filepath, encoding="utf-8") as fin:
                data: dict[str, Any] = json.load(fin)
            print(f"\n  Loaded: {selected_file}")
            print(f"  Source: {data.get('source_template_name', 'Unknown')}")
            return data
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"  Error loading file: {error}")
            return None

    def _select_destination_templates(
        self,
        templates: list[dict[str, Any]],
        extraction_data: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        """Select destination templates for configuration application."""
        source_id = extraction_data.get("source_template_id")
        available = [t for t in templates if t.get("id") != source_id]

        if not available:
            print("  No other templates available.")
            return None

        print(f"\n  Step 2: Select destination templates " f"({len(available)} available):")
        for idx, tpl in enumerate(available):
            print(f"  [{idx}] {tpl.get('name', 'Unnamed')}")

        print("\n  Enter template numbers (comma-separated) or 'all':")
        try:
            selection = self._input_fn("  Selection: ", context="menu_106_dest_selection").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operation cancelled.")
            return None

        if selection.lower() == "all":
            return available

        return _parse_template_indices(selection, available)

    def _confirm_apply(
        self,
        destinations: list[dict[str, Any]],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> bool:
        """Display preview and get confirmation for apply operation."""
        print("\n  Step 3: Configuration Preview")
        print("-" * 70)

        if dia_pico:
            print("  Traffic Steering (DIA_Pico):")
            strategy = dia_pico.get("strategy", "Unknown")
            paths = dia_pico.get("paths", [])
            print(f"    Strategy: {strategy}, Paths: {len(paths)}")

        if picocell:
            print("  Application Policies (Picocell):")
            print(f"    Name: {picocell.get('name', 'Unknown')}")

        print(f"\n  {'=' * 70}")
        print(f"  !? CRITICAL: This will modify {len(destinations)} template(s)")
        print("  !? Type 'APPLY' (all caps) to proceed or " "anything else to cancel")
        print(f"  {'=' * 70}")

        try:
            confirmation = self._input_fn("\n  Confirmation: ", context="menu_106_confirmation").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operation cancelled.")
            return False

        if confirmation != "APPLY":
            print("  Operation cancelled.")
            return False

        return True

    def _apply_to_templates(
        self,
        destinations: list[dict[str, Any]],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Apply configurations to destination templates."""
        print("\n  Applying configuration to destination templates...")
        results: list[dict[str, Any]] = []

        for template in tqdm(destinations, desc="Updating templates", unit="template"):
            result = self._apply_single_template(mistapi, template, dia_pico, picocell)
            results.append(result)

        return results

    def _apply_single_template(
        self,
        mistapi_mod: Any,
        template: dict[str, Any],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Apply config changes to a single template."""
        template_id: str = template.get("id", "")
        template_name = template.get("name", "Unnamed")

        result: dict[str, Any] = {
            "template_name": template_name,
            "template_id": template_id,
            "status": "",
            "changes_made": [],
            "error": "",
        }

        try:
            config = self._fetch_single_config(mistapi_mod, template_id, result)
            if config is None:
                return result

            _merge_dia_pico(config, dia_pico, result)
            _merge_picocell(config, picocell, result)

            update_resp = mistapi_mod.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate(
                self._api, self._org_id, template_id, body=config
            )

            if update_resp.status_code == 200:
                result["status"] = "SUCCESS"
            else:
                result["status"] = "FAILED"
                result["error"] = f"API status {update_resp.status_code}"

        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "FAILED"
            result["error"] = str(error)

        return result

    def _fetch_single_config(
        self,
        mistapi_mod: Any,
        template_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Fetch a single template config for the apply operation."""
        resp = mistapi_mod.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(self._api, self._org_id, template_id)
        config = resp.data if hasattr(resp, "data") else {}

        if not isinstance(config, dict):
            result["status"] = "FAILED"
            result["error"] = "Invalid configuration format"
            return None

        return config

    def _report_apply_results(self, results: list[dict[str, Any]]) -> None:
        """Generate and display apply operation results."""
        output_file = "GatewayTemplate_Config_Application_Audit.csv"

        csv_results = [
            {
                "template_name": r["template_name"],
                "template_id": r["template_id"],
                "status": r["status"],
                "changes_made": ("; ".join(r["changes_made"]) if r["changes_made"] else ""),
                "error": r["error"],
            }
            for r in results
        ]

        self._save_data(csv_results, output_file)

        success = sum(1 for r in results if r["status"] == "SUCCESS")
        failed = len(results) - success

        print("\n  Configuration Application Complete!")
        print("=" * 70)
        print(f"  Templates Processed: {len(results)}")
        print(f"  Successfully Updated: {success}")
        print(f"  Failed: {failed}")
        print(f"\n  Audit report saved to: {output_file}")

        logging.warning(f"Menu #106 complete: {success} templates updated, {failed} failed")

    # ------------------------------------------------------------------ #
    # Clone-by-location helpers                                           #
    # ------------------------------------------------------------------ #

    def _load_sites_with_location(
        self,
    ) -> list[dict[str, str]] | None:
        """Load site data with state and country information."""
        print("\n  Step 1: Loading site data...")
        self._check_csv("SiteList.csv", self._gen_sites)

        sites_path = self._get_csv_path("SiteList.csv")
        try:
            with open(sites_path, encoding="utf-8") as fin:
                all_sites = list(csv.DictReader(fin))
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"  Error loading sites: {error}")
            return None

        if not all_sites:
            print("  No sites found in organization.")
            return None

        sites_with_loc = _filter_sites_with_location(all_sites)

        if not sites_with_loc:
            print("  No sites found with state or country information.")
            return None

        print(f"  Found {len(sites_with_loc)} sites with location data")
        return sites_with_loc

    @staticmethod
    def _get_unique_locations(
        sites: list[dict[str, str]],
    ) -> tuple[set[str], set[str]]:
        """Extract unique states and countries from site data."""
        states: set[str] = set()
        countries: set[str] = set()

        for site in sites:
            if site["state"]:
                states.add(site["state"])
            elif site["country"]:
                countries.add(site["country"])

        print(f"  Unique states found: {len(states)}")
        print(f"  Unique countries (for sites without state): {len(countries)}")
        return states, countries

    @staticmethod
    def _plan_template_creation(
        source: dict[str, Any],
        states: set[str],
        countries: set[str],
    ) -> list[dict[str, str]]:
        """Plan which templates to create based on locations."""
        source_name = source.get("name", "Unnamed")
        to_create: list[dict[str, str]] = []

        for state in sorted(states):
            to_create.append(
                {
                    "name": f"{source_name}_{state}",
                    "location_type": "state",
                    "location_value": state,
                }
            )

        for country in sorted(countries):
            to_create.append(
                {
                    "name": f"{source_name}_{country}",
                    "location_type": "country",
                    "location_value": country,
                }
            )

        print(f"\n  Step 4: Preview - {len(to_create)} templates " "will be created:")
        for info in to_create:
            print(f"   - {info['name']} " f"(for {info['location_type']}: {info['location_value']})")

        return to_create

    @staticmethod
    def _plan_site_assignments(
        sites: list[dict[str, str]],
        source: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Plan site-to-template assignments."""
        source_name = source.get("name", "Unnamed")
        assignments: list[dict[str, str]] = []

        for site in sites:
            if site["state"]:
                target = f"{source_name}_{site['state']}"
            elif site["country"]:
                target = f"{source_name}_{site['country']}"
            else:
                continue

            assignments.append(
                {
                    "site_id": site["id"],
                    "site_name": site["name"],
                    "target_template_name": target,
                    "current_template_id": site["current_template_id"],
                }
            )

        print(f"\n  {len(assignments)} sites will be assigned to templates")
        return assignments

    def _confirm_clone(
        self,
        to_create: list[dict[str, str]],
        assignments: list[dict[str, str]],
    ) -> bool:
        """Get confirmation for clone operation."""
        print(f"\n  {'=' * 70}")
        print(f"  !? CRITICAL: This will create {len(to_create)} new templates")
        print(f"  !? and modify {len(assignments)} site template assignments")
        print("  !? Type 'CLONE' (all caps) to proceed or " "anything else to cancel")
        print(f"  {'=' * 70}")

        try:
            confirmation = self._input_fn("\n  Confirmation: ", context="menu_111_confirmation").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Operation cancelled.")
            return False

        if confirmation != "CLONE":
            print("  Operation cancelled.")
            return False

        return True

    def _get_existing_template_names(self) -> dict[str, str]:
        """Get mapping of existing template names to IDs."""
        try:
            resp = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(self._api, self._org_id, limit=1000)
            templates = mistapi.get_all(response=resp, mist_session=self._api)
            return {t.get("name"): t.get("id") for t in templates if t.get("name")}
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.error(f"GatewayTemplateConfigManager: Error fetching templates: " f"{error}")
            return {}

    def _create_templates(
        self,
        source_config: dict[str, Any],
        to_create: list[dict[str, str]],
        existing_names: dict[str, str],
    ) -> dict[str, str]:
        """Create new templates based on source configuration."""
        print("\n  Step 5: Creating templates...")
        template_map: dict[str, str] = {}

        for info in tqdm(to_create, desc="Creating templates", unit="template"):
            name = info["name"]

            if name in existing_names:
                template_map[name] = existing_names[name]
                logging.info(f"Template {name} already exists, skipping")
                continue

            self._create_single_template(mistapi, name, source_config, template_map)

        return template_map

    def _create_single_template(
        self,
        mistapi_mod: Any,
        name: str,
        source_config: dict[str, Any],
        template_map: dict[str, str],
    ) -> None:
        """Create one template from the source configuration."""
        try:
            new_config = dict(source_config)
            new_config["name"] = name
            for field in ["id", "org_id", "created_time", "modified_time"]:
                new_config.pop(field, None)

            resp = mistapi_mod.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate(
                self._api, self._org_id, body=new_config
            )

            if resp.status_code == 200:
                new_id = resp.data.get("id") if hasattr(resp, "data") else ""
                template_map[name] = new_id
                logging.info(f"Created template {name} (ID: {new_id})")
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.error(f"Error creating template {name}: {error}")

    def _assign_sites(
        self,
        assignments: list[dict[str, str]],
        template_map: dict[str, str],
    ) -> list[dict[str, str]]:
        """Assign sites to their corresponding templates."""
        print("\n  Step 6: Assigning sites to templates...")
        results: list[dict[str, str]] = []

        for assignment in tqdm(assignments, desc="Assigning sites", unit="site"):
            result = self._assign_single_site(mistapi, assignment, template_map)
            results.append(result)

        return results

    def _assign_single_site(
        self,
        mistapi_mod: Any,
        assignment: dict[str, str],
        template_map: dict[str, str],
    ) -> dict[str, str]:
        """Assign a single site to its target template."""
        site_id = assignment["site_id"]
        target_name = assignment["target_template_name"]
        target_id = template_map.get(target_name, "")

        result: dict[str, str] = {
            "site_name": assignment["site_name"],
            "site_id": site_id,
            "target_template_name": target_name,
            "status": "",
            "error": "",
        }

        if not target_id:
            result["status"] = "SKIPPED"
            result["error"] = "Target template not found"
            return result

        if assignment["current_template_id"] == target_id:
            result["status"] = "SKIPPED"
            result["error"] = "Already assigned"
            return result

        return self._update_site_template(mistapi_mod, site_id, target_id, result)

    def _update_site_template(
        self,
        mistapi_mod: Any,
        site_id: str,
        target_id: str,
        result: dict[str, str],
    ) -> dict[str, str]:
        """Push template assignment update to a single site."""
        try:
            resp = mistapi_mod.api.v1.sites.sites.updateSiteInfo(
                self._api, site_id, body={"gatewaytemplate_id": target_id}
            )
            if resp.status_code == 200:
                result["status"] = "ASSIGNED"
            else:
                result["status"] = "FAILED"
                result["error"] = f"API status {resp.status_code}"
        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"
            result["error"] = str(error)

        return result

    def _report_clone_results(
        self,
        to_create: list[dict[str, str]],
        site_results: list[dict[str, str]],
    ) -> None:
        """Generate and display clone operation results."""
        output = "Site_Template_Assignment_By_State_Country_Audit.csv"

        self._save_data(site_results, output)

        assigned = sum(1 for r in site_results if r["status"] == "ASSIGNED")
        skipped = sum(1 for r in site_results if r["status"] == "SKIPPED")
        failed = sum(1 for r in site_results if r["status"] in ["FAILED", "ERROR"])

        print("\n  Gateway Template Cloning by State/Country Complete!")
        print("=" * 70)
        print(f"  TEMPLATE CREATION: {len(to_create)} planned")
        print("\n  SITE ASSIGNMENTS:")
        print(f"    Assigned: {assigned}")
        print(f"    Skipped: {skipped}")
        print(f"    Failed: {failed}")
        print(f"\n  AUDIT REPORT: {output}")
        print("=" * 70)

        logging.warning(f"Menu #111 complete: {assigned} sites assigned, {failed} failed")


# ------------------------------------------------------------------ #
# Module-level helper functions (keep class complexity low)           #
# ------------------------------------------------------------------ #


def _find_picocell_policy(
    template_config: dict[str, Any],
    template_name: str,
) -> dict[str, Any] | None:
    """Search service_policies for a Picocell entry."""
    print("\n  Extracting Application Policies configuration...")
    service_policies = template_config.get("service_policies", [])
    picocell: dict[str, Any] | None = None

    if isinstance(service_policies, list):
        for policy in service_policies:
            if isinstance(policy, dict) and policy.get("name") == "Picocell":
                picocell = policy
                print("  -> Found 'Picocell' in Application Policies")
                logging.info(f"GatewayTemplateConfigManager: Found Picocell " f"in {template_name}")
                break

    if not picocell:
        print("  -> 'Picocell' not found in Application Policies")

    return picocell


def _parse_template_indices(
    selection: str,
    available: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    """Parse comma-separated indices into template list."""
    try:
        indices = [int(x.strip()) for x in selection.split(",")]
        selected = [available[i] for i in indices if 0 <= i < len(available)]
        if not selected:
            print("  No valid templates selected.")
            return None
        return selected
    except (ValueError, IndexError):
        print("  Invalid selection format.")
        return None


def _merge_dia_pico(
    config: dict[str, Any],
    dia_pico: dict[str, Any] | None,
    result: dict[str, Any],
) -> None:
    """Merge DIA_Pico into a template configuration."""
    if dia_pico:
        if "path_preferences" not in config:
            config["path_preferences"] = {}
        config["path_preferences"]["DIA_Pico"] = dia_pico
        result["changes_made"].append("Added/Updated DIA_Pico")


def _merge_picocell(
    config: dict[str, Any],
    picocell: dict[str, Any] | None,
    result: dict[str, Any],
) -> None:
    """Merge Picocell policy into a template configuration."""
    if not picocell:
        return

    if "service_policies" not in config:
        config["service_policies"] = []

    existing_idx = _find_existing_picocell_index(config["service_policies"])

    if existing_idx is not None:
        config["service_policies"][existing_idx] = picocell
        result["changes_made"].append("Updated existing Picocell")
    else:
        _insert_picocell_policy(config["service_policies"], picocell, result)


def _find_existing_picocell_index(
    policies: list[dict[str, Any]],
) -> int | None:
    """Find the index of existing Picocell policy in service_policies."""
    for idx, policy in enumerate(policies):
        if isinstance(policy, dict) and policy.get("name") == "Picocell":
            return idx
    return None


def _insert_picocell_policy(
    policies: list[dict[str, Any]],
    picocell: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Insert Picocell policy at the appropriate position."""
    policy_count = len(policies)
    if policy_count >= 14:
        policies.insert(13, picocell)
        result["changes_made"].append("Inserted Picocell at position 14")
    else:
        policies.append(picocell)
        result["changes_made"].append(f"Added Picocell at position {policy_count + 1}")


def parse_state_from_address(address: str, country: str) -> str:
    """Parse state/province from address field based on country format.

    Handles US (2-letter state + ZIP), CA (province + postal code),
    and various Latin American address formats.

    Args:
        address: Full address string.
        country: ISO 2-letter country code.

    Returns:
        State/province string, or empty string if not found.
    """
    if not address or not country:
        return ""

    small_countries = {"BS", "BZ", "CU", "HT", "JM", "DO"}
    if country in small_countries:
        return ""

    if "," in address:
        return _parse_state_comma_separated(address)

    return _parse_state_space_separated(address, country)


def _parse_state_comma_separated(address: str) -> str:
    """Parse state from comma-separated address parts."""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 3:
        return ""

    for part in parts:
        match_us = re.search(r"\b([A-Z]{2})\s+\d{5}", part)
        if match_us:
            return match_us.group(1)
        match_ca = re.search(r"^([A-Z]{2})\s+[A-Z]\d[A-Z]", part)
        if match_ca:
            return match_ca.group(1)
        match_alone = re.search(r"^([A-Z]{2})$", part)
        if match_alone:
            return match_alone.group(1)

    return ""


def _parse_state_space_separated(address: str, country: str) -> str:
    """Parse state from space-separated address."""
    parts = address.split()

    if country == "CA" and len(parts) >= 3:
        return _parse_canadian_state(parts)

    if len(parts) < 2:
        return ""

    return _parse_general_state(address, parts, country)


def _parse_canadian_state(parts: list[str]) -> str:
    """Parse state from Canadian address format."""
    for i, part in enumerate(parts):
        if len(part) == 2 and part.isupper():
            if i + 1 < len(parts) and re.match(r"^[A-Z]\d[A-Z]$", parts[i + 1]):
                return part
    return ""


def _parse_general_state(address: str, parts: list[str], country: str) -> str:
    """Parse state from general address format."""
    address_lower = address.lower()
    if "puerto rico" in address_lower:
        return "Puerto Rico"
    if "bay islands" in address_lower:
        return "Bay Islands"

    postal_index = _find_postal_index(parts)

    if postal_index > 1:
        return parts[postal_index - 1]

    if postal_index == -1:
        return _infer_state_without_postal(parts, country)

    return ""


def _find_postal_index(parts: list[str]) -> int:
    """Find the index of the first part starting with a digit."""
    for i, part in enumerate(parts):
        if re.match(r"^\d", part):
            return i
    return -1


def _infer_state_without_postal(parts: list[str], country: str) -> str:
    """Infer state when no postal code is present."""
    latam = {"MX", "CR", "PA", "HN", "GT"}
    if country not in latam and len(parts) == 2:
        return ""
    if country in latam or len(parts) > 2:
        return parts[-1]
    return ""


def _filter_sites_with_location(
    all_sites: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Filter sites that have state or country location data."""
    result: list[dict[str, str]] = []

    for site in all_sites:
        address = site.get("address", "").strip()
        country = site.get("country_code", "").strip()
        state = parse_state_from_address(address, country)

        if state or country:
            result.append(
                {
                    "id": site.get("id", "").strip(),
                    "name": site.get("name", "").strip(),
                    "state": state,
                    "country": country,
                    "current_template_id": site.get("gatewaytemplate_id", "").strip(),
                }
            )

    return result
