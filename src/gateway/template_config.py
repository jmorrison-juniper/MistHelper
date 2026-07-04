"""Gateway template configuration management for MistHelper.

Extracts GatewayTemplateConfigManager (Menu #105, #106, #111) from
MistHelper.py into a class with dependency injection for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations  # WHY: enable PEP 604 typing on older interpreters

import csv  # WHY: read SiteList.csv when planning clone-by-location assignments
import json  # WHY: persist and reload extraction files as JSON
import logging  # WHY: emit lifecycle warnings and errors for menu operations
import os  # WHY: enumerate cached data-dir contents for file selection
import re  # WHY: pattern matching used by the state/province address parsers
from collections.abc import Callable  # WHY: type-annotate injected callables
from datetime import UTC, datetime  # WHY: stamp extraction timestamps in UTC
from typing import Any  # WHY: describe injected/response objects with unknown structure

import mistapi  # WHY: Mist REST helpers for org/gatewaytemplates/sites APIs
from tqdm import tqdm  # WHY: progress bars for bulk template/site operations

_PICOCELL_INSERT_ANCHOR = 13  # WHY: Picocell must land at policy position 14 (0-indexed 13)
_PICOCELL_INSERT_THRESHOLD = 14  # WHY: below this policy count we just append instead of inserting
_SMALL_ISLAND_COUNTRIES = frozenset({"BS", "BZ", "CU", "HT", "JM", "DO"})  # WHY: no useful state in address
_LATAM_COUNTRIES = frozenset({"MX", "CR", "PA", "HN", "GT"})  # WHY: infer state from trailing token
_MIN_COMMA_PARTS = 3  # WHY: US/CA comma format needs street, city, state-block


class GatewayTemplateConfigManager:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Manage gateway template config extraction, application, and cloning.

    Supports three operations:
    - extract (Menu 105): Extract DIA_Pico and Picocell configs to JSON
    - apply (Menu 106): Apply extracted configs to other templates
    - clone_by_location (Menu 111): Clone template per state/country
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with all external dependencies passed as keyword arguments.

        Keyword Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            input_fn: User input function with (prompt, context=) signature.
            get_csv_path_fn: Resolves CSV filenames to full paths.
            save_data_fn: Writes data to output files.
            check_and_generate_csv_fn: Cache check/generation function.
            generate_sites_fn: Sites CSV generator.
            sanitize_filename_fn: Sanitize filenames for safe filesystem use.
        """
        self._org_id: str = kwargs["org_id"]  # WHY: scope every mistapi call to this org
        self._api: Any = kwargs["apisession"]  # WHY: authenticated session shared across API helpers
        self._input_fn: Callable[..., str] = kwargs["input_fn"]  # WHY: prompts route through host-configured UX
        self._get_csv_path: Callable[[str], str] = kwargs["get_csv_path_fn"]  # WHY: resolves cached-data paths
        self._save_data: Callable[..., Any] = kwargs["save_data_fn"]  # WHY: standard writer used by audit reports
        self._check_csv: Callable[..., Any] = kwargs["check_and_generate_csv_fn"]  # WHY: refreshes cached CSVs
        self._gen_sites: Callable[..., Any] = kwargs["generate_sites_fn"]  # WHY: regenerates SiteList.csv on demand
        self._sanitize: Callable[[str], str] = kwargs["sanitize_filename_fn"]  # WHY: strips unsafe filename chars

    # ------------------------------------------------------------------ #
    # Public entry points                                                 #
    # ------------------------------------------------------------------ #

    def extract(self) -> None:
        """Menu 105: Extract DIA_Pico and Picocell configs from a template."""
        _print_extract_banner()  # WHY: consistent header for menu operations
        logging.info("Menu #105: Starting gateway template configuration extraction")  # WHY: menu-level audit trail
        templates = self._fetch_templates()  # WHY: need the org template list to prompt selection
        if not templates:  # WHY: nothing to extract when no templates or fetch failed
            return  # WHY: _fetch_templates already surfaced the reason
        selected = self._select_template(templates, "extract")  # WHY: user picks source template
        if not selected:  # WHY: selection cancelled/invalid; nothing further to do
            return  # WHY: _select_template printed the cancel reason
        template_config = self._fetch_template_config(selected)  # WHY: need full body to mine configs
        if not template_config:  # WHY: fetch error or unexpected shape
            return  # WHY: helper already logged/printed diagnostics
        extraction = self._extract_configs(template_config, selected)  # WHY: pull DIA_Pico + Picocell blocks
        if extraction:  # WHY: only save when at least one target block was found
            self._save_extraction(extraction, selected)  # WHY: persist for Menu 106 reuse

    def apply(self) -> None:
        """Menu 106: Apply extracted configuration to gateway templates."""
        _print_apply_banner()  # WHY: destructive-op header includes explicit warning
        logging.warning("Menu #106 DESTRUCTIVE: Apply Gateway Template Configuration started")  # WHY: audit trail
        extraction_data = self._load_extraction_file()  # WHY: pick a prior Menu-105 JSON as source
        if not extraction_data:  # WHY: cancelled or no files present
            return  # WHY: helper printed reason
        templates = self._fetch_templates()  # WHY: need the current org template list for targets
        if not templates:  # WHY: no candidate destinations
            return  # WHY: helper printed reason
        destinations = self._select_destination_templates(templates, extraction_data)  # WHY: user chooses recipients
        if not destinations:  # WHY: selection cancelled/invalid/empty
            return  # WHY: helper printed reason
        dia_pico, picocell = _split_extracted_payloads(extraction_data)  # WHY: separate the two config blocks
        if not self._confirm_apply(destinations, dia_pico, picocell):  # WHY: destructive op requires confirmation
            return  # WHY: user declined
        results = self._apply_to_templates(destinations, dia_pico, picocell)  # WHY: perform the writes
        self._report_apply_results(results)  # WHY: emit audit report

    def clone_by_location(self) -> None:
        """Menu 111: Clone template per state/country and assign sites."""
        _print_clone_banner()  # WHY: destructive-op header includes explicit warning
        logging.warning("Menu #111 DESTRUCTIVE: Clone Gateway Templates by " "State/Country operation started")
        loaded = self._load_clone_inputs()  # WHY: bundle three loading steps into a single guard
        if loaded is None:  # WHY: any load step aborted the operation
            return  # WHY: helper printed reason
        sites, templates, source, source_config = loaded  # WHY: unpack bundle for plan phase
        states, countries = self._get_unique_locations(sites)  # WHY: derive unique destinations for creation
        to_create, assignments = self._plan_clone(source, sites, states, countries)  # WHY: precompute plan
        if not self._confirm_clone(to_create, assignments):  # WHY: destructive op requires confirmation
            return  # WHY: user declined
        results = self._execute_clone(source_config, to_create, assignments)  # WHY: create + assign
        self._report_clone_results(to_create, results)  # WHY: emit audit report

    # ------------------------------------------------------------------ #
    # Public-entry helpers                                                #
    # ------------------------------------------------------------------ #

    def _load_clone_inputs(
        self,
    ) -> tuple[list[dict[str, str]], list[dict[str, Any]], dict[str, Any], dict[str, Any]] | None:
        """Load sites, templates, chosen source template and its full config.

        Returns None if any of the loading steps fail or the user cancels.
        """
        sites = self._load_sites_with_location()  # WHY: prerequisite for computing per-location targets
        if not sites:  # WHY: cannot clone without at least one located site
            return None  # WHY: helper printed reason
        templates = self._fetch_templates()  # WHY: need the current template list to choose a source
        if not templates:  # WHY: nothing to clone from
            return None  # WHY: helper printed reason
        source = self._select_template(templates, "clone")  # WHY: user picks the template to clone
        if not source:  # WHY: user cancelled selection
            return None  # WHY: helper printed reason
        source_config = self._fetch_template_config(source)  # WHY: need the body to copy into new templates
        if not source_config:  # WHY: fetch error or unexpected shape
            return None  # WHY: helper printed reason
        return sites, templates, source, source_config  # WHY: pack for the caller

    def _plan_clone(
        self,
        source: dict[str, Any],
        sites: list[dict[str, str]],
        states: set[str],
        countries: set[str],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Compute (to_create, assignments) plan for clone operation."""
        to_create = self._plan_template_creation(source, states, countries)  # WHY: derive per-location template list
        assignments = self._plan_site_assignments(sites, source)  # WHY: derive site->template mapping
        return to_create, assignments  # WHY: caller confirms both before execution

    def _execute_clone(
        self,
        source_config: dict[str, Any],
        to_create: list[dict[str, str]],
        assignments: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Create templates and assign sites, returning per-site results."""
        existing = self._get_existing_template_names()  # WHY: skip re-creating names already present
        tpl_map = self._create_templates(source_config, to_create, existing)  # WHY: name -> id lookup for assignments
        return self._assign_sites(assignments, tpl_map)  # WHY: per-site assignment result rows

    # ------------------------------------------------------------------ #
    # Template fetching and selection                                     #
    # ------------------------------------------------------------------ #

    def _fetch_templates(self) -> list[dict[str, Any]] | None:
        """Fetch all gateway templates for the organization."""
        print("\n  Fetching gateway templates...")  # WHY: signal network activity to the user
        try:
            response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(  # WHY: paginated list
                self._api,
                self._org_id,
                limit=1000,
            )
            templates = mistapi.get_all(response=response, mist_session=self._api)  # WHY: exhaust pagination
            if not templates:  # WHY: empty-org guard
                print("  No gateway templates found for this organization.")  # WHY: user-facing reason
                logging.warning("GatewayTemplateConfigManager: No gateway templates found")  # WHY: audit trail
                return None  # WHY: caller aborts on None
            return sorted(templates, key=lambda t: t.get("name", "Unnamed Template").lower())  # WHY: stable ordering
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            print(f"  Error fetching gateway templates: {error}")  # WHY: user-visible failure
            logging.error("GatewayTemplateConfigManager: Failed to fetch templates: %s", error)  # WHY: audit trail
            return None  # WHY: caller aborts on None

    def _select_template(
        self,
        templates: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any] | None:
        """Display and select a template from the list."""
        _print_template_menu(templates)  # WHY: shared printer for menu rendering
        selection = self._prompt_template_index(templates, operation)  # WHY: guarded prompt returns str or None
        if selection is None:  # WHY: user cancelled via EOF/Ctrl-C
            return None  # WHY: helper printed reason
        index = _validate_template_index(selection, len(templates))  # WHY: parse+range-check in one place
        if index is None:  # WHY: parsing/range check failed
            return None  # WHY: helper printed reason
        selected = templates[index]  # WHY: look up the chosen row
        print(f"\n  Selected Template: {selected.get('name', 'Unnamed')}")  # WHY: confirm selection to user
        return selected  # WHY: caller consumes the row

    def _prompt_template_index(
        self,
        templates: list[dict[str, Any]],
        operation: str,
    ) -> str | None:
        """Prompt for a template index, returning the raw input string or None if cancelled."""
        try:
            return self._input_fn(  # WHY: host-configured prompt
                f"Enter template index to {operation} " f"[0-{len(templates) - 1}]: ",
                context=f"gateway_template_{operation}_selection",
            ).strip()  # WHY: trim whitespace before numeric checks
        except (EOFError, KeyboardInterrupt):  # WHY: user cancelled interactive session
            print("\n  Operation cancelled.")  # WHY: user-facing cancel message
            return None  # WHY: caller treats None as cancel

    # ------------------------------------------------------------------ #
    # Extract helpers                                                     #
    # ------------------------------------------------------------------ #

    def _fetch_template_config(self, template: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch full configuration for a template."""
        template_name = template.get("name", "Unnamed Template")  # WHY: used in log messages
        print("\n  Fetching full template configuration...")  # WHY: signal network activity
        try:
            config = self._call_get_template(template.get("id"))  # WHY: isolate network call for readability
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            _log_fetch_failure(template_name, error)  # WHY: single audit path for network errors
            return None  # WHY: caller aborts on None
        if not isinstance(config, dict):  # WHY: guard against error strings or unexpected shape
            _log_invalid_fetch(template_name)  # WHY: single audit path for shape errors
            return None  # WHY: caller aborts on None
        return config  # WHY: caller receives full config dict

    def _call_get_template(self, template_id: Any) -> Any:
        """Invoke mistapi getOrgGatewayTemplate and return its data payload."""
        response = mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(  # WHY: full body fetch
            self._api,
            self._org_id,
            template_id,
        )
        return response.data if hasattr(response, "data") else {}  # WHY: safely access mocked/real payload

    @staticmethod
    def _extract_configs(
        template_config: dict[str, Any],
        template: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Extract DIA_Pico and Picocell configurations from template."""
        template_name = template.get("name", "Unnamed")  # WHY: used in log messages
        dia_pico = _extract_dia_pico(template_config, template_name)  # WHY: mine traffic-steering block
        picocell = _find_picocell_policy(template_config, template_name)  # WHY: mine application-policy block
        if not dia_pico and not picocell:  # WHY: nothing to save if both are absent
            print("\n  Warning: Neither 'DIA_Pico' nor 'Picocell' " "configurations were found.")  # WHY: user-facing
            return None  # WHY: caller skips save
        return _build_extraction_payload(dia_pico, picocell, template)  # WHY: build the persisted structure

    def _save_extraction(
        self,
        extraction: dict[str, Any],
        template: dict[str, Any],
    ) -> None:
        """Save extraction data to JSON file."""
        template_name = template.get("name", "Unnamed")  # WHY: used to derive filename
        safe_name = self._sanitize(template_name)  # WHY: filesystem-safe name
        json_filename = f"{safe_name}_extracted_config.json"  # WHY: convention for menu-106 discovery
        json_filepath = self._get_csv_path(json_filename)  # WHY: cached-data path
        try:
            with open(json_filepath, "w", encoding="utf-8") as fout:  # WHY: text write with UTC-safe encoding
                json.dump(extraction, fout, indent=2, ensure_ascii=False)  # WHY: human-readable output
            _print_save_success(json_filepath)  # WHY: reusable success message
            logging.info("GatewayTemplateConfigManager: Saved extraction to %s", json_filepath)  # WHY: audit trail
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: filesystem errors vary
            print(f"\n  Error saving extraction file: {error}")  # WHY: user-facing
            logging.error("GatewayTemplateConfigManager: Failed to save JSON: %s", error)  # WHY: audit trail

    # ------------------------------------------------------------------ #
    # Apply helpers                                                       #
    # ------------------------------------------------------------------ #

    def _load_extraction_file(self) -> dict[str, Any] | None:
        """Load a previously saved extraction JSON file."""
        print("\n  Step 1: Finding extraction files...")  # WHY: user-facing step marker
        extraction_files = self._list_extraction_files()  # WHY: enumerate candidate JSON files
        if extraction_files is None:  # WHY: directory read failure
            return None  # WHY: helper printed reason
        if not extraction_files:  # WHY: no matching files present
            print("  No extraction files found. Run Menu #105 first.")  # WHY: guide user to prerequisite
            return None  # WHY: caller aborts
        extraction_files.sort()  # WHY: stable order for user selection
        return self._prompt_file_selection(extraction_files)  # WHY: prompt+load in a single helper

    def _list_extraction_files(self) -> list[str] | None:
        """Enumerate *_extracted_config.json files in the data directory."""
        data_dir = self._get_csv_path("")  # WHY: resolve base data directory
        try:
            return [name for name in os.listdir(data_dir) if name.endswith("_extracted_config.json")]  # WHY: filter
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: filesystem errors vary
            print(f"  Error reading data directory: {error}")  # WHY: user-facing
            return None  # WHY: caller aborts on None

    def _prompt_file_selection(self, files: list[str]) -> dict[str, Any] | None:
        """Prompt user to select an extraction file and load it."""
        _print_file_menu(files)  # WHY: shared menu-render helper
        selection = self._prompt_file_index(files)  # WHY: guarded prompt with EOF handling
        if selection is None:  # WHY: user cancelled
            return None  # WHY: helper printed reason
        if not _is_valid_file_index(selection, len(files)):  # WHY: enforce numeric range
            print("  Invalid selection.")  # WHY: user-facing
            return None  # WHY: caller aborts
        selected_file = files[int(selection)]  # WHY: pull chosen filename
        filepath = os.path.join(self._get_csv_path(""), selected_file)  # WHY: resolve to full path
        return self._load_extraction_json(filepath, selected_file)  # WHY: read+report in helper

    def _prompt_file_index(self, files: list[str]) -> str | None:
        """Prompt for extraction-file index, returning trimmed string or None if cancelled."""
        try:
            return self._input_fn(  # WHY: host-configured prompt
                f"\n  Select extraction file [0-{len(files) - 1}]: ",
                context="menu_106_file_selection",
            ).strip()  # WHY: trim whitespace before numeric checks
        except (EOFError, KeyboardInterrupt):  # WHY: user cancelled interactive session
            print("\n  Operation cancelled.")  # WHY: user-facing cancel message
            return None  # WHY: caller treats None as cancel

    def _load_extraction_json(self, filepath: str, selected_file: str) -> dict[str, Any] | None:
        """Read a JSON extraction file and return its parsed content."""
        try:
            with open(filepath, encoding="utf-8") as fin:  # WHY: text read with explicit encoding
                data: dict[str, Any] = json.load(fin)  # WHY: annotated for mypy strictness
            print(f"\n  Loaded: {selected_file}")  # WHY: user-facing confirmation
            print(f"  Source: {data.get('source_template_name', 'Unknown')}")  # WHY: show provenance
            return data  # WHY: caller consumes payload
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: file/JSON errors vary
            print(f"  Error loading file: {error}")  # WHY: user-facing
            return None  # WHY: caller aborts on None

    def _select_destination_templates(
        self,
        templates: list[dict[str, Any]],
        extraction_data: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        """Select destination templates for configuration application."""
        available = _available_destinations(templates, extraction_data)  # WHY: exclude the source template
        if not available:  # WHY: no candidates left
            print("  No other templates available.")  # WHY: user-facing
            return None  # WHY: caller aborts
        _print_destination_menu(available)  # WHY: shared render helper
        selection = self._prompt_destination_selection()  # WHY: guarded prompt
        if selection is None:  # WHY: user cancelled
            return None  # WHY: helper printed reason
        if selection.lower() == "all":  # WHY: convenience keyword for full sweep
            return available  # WHY: return everything
        return _parse_template_indices(selection, available)  # WHY: parse comma-separated indices

    def _prompt_destination_selection(self) -> str | None:
        """Prompt for destination selection string, or None if cancelled."""
        try:
            return self._input_fn("  Selection: ", context="menu_106_dest_selection").strip()  # WHY: trimmed input
        except (EOFError, KeyboardInterrupt):  # WHY: user cancelled interactive session
            print("\n  Operation cancelled.")  # WHY: user-facing cancel message
            return None  # WHY: caller treats None as cancel

    def _confirm_apply(
        self,
        destinations: list[dict[str, Any]],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> bool:
        """Display preview and get confirmation for apply operation."""
        _print_apply_preview(dia_pico, picocell)  # WHY: show what's about to change
        _print_apply_warning(len(destinations))  # WHY: destructive-op warning
        confirmation = self._prompt_apply_confirmation()  # WHY: guarded prompt
        if confirmation is None:  # WHY: user cancelled interactively
            return False  # WHY: caller aborts
        if confirmation != "APPLY":  # WHY: require exact uppercase match
            print("  Operation cancelled.")  # WHY: user-facing
            return False  # WHY: caller aborts
        return True  # WHY: user confirmed

    def _prompt_apply_confirmation(self) -> str | None:
        """Prompt for the APPLY confirmation word, or None if cancelled."""
        try:
            return self._input_fn("\n  Confirmation: ", context="menu_106_confirmation").strip()  # WHY: trimmed
        except (EOFError, KeyboardInterrupt):  # WHY: user cancelled interactive session
            print("\n  Operation cancelled.")  # WHY: user-facing cancel message
            return None  # WHY: caller treats None as cancel

    def _apply_to_templates(
        self,
        destinations: list[dict[str, Any]],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Apply configurations to destination templates."""
        print("\n  Applying configuration to destination templates...")  # WHY: user-facing step marker
        results: list[dict[str, Any]] = []  # WHY: accumulator for per-template outcomes
        for template in tqdm(destinations, desc="Updating templates", unit="template"):  # WHY: visual progress
            result = self._apply_single_template(mistapi, template, dia_pico, picocell)  # WHY: per-template attempt
            results.append(result)  # WHY: record the outcome
        return results  # WHY: caller reports on the full batch

    def _apply_single_template(
        self,
        mistapi_mod: Any,
        template: dict[str, Any],
        dia_pico: dict[str, Any] | None,
        picocell: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Apply config changes to a single template."""
        template_id: str = template.get("id", "")  # WHY: identifier for logging and API
        template_name = template.get("name", "Unnamed")  # WHY: identifier for logging
        result = _empty_apply_result(template_name, template_id)  # WHY: uniform result skeleton
        try:
            config = self._fetch_single_config(mistapi_mod, template_id, result)  # WHY: get current config
            if config is None:  # WHY: fetch/format error already recorded
                return result  # WHY: bail out with recorded failure
            _merge_dia_pico(config, dia_pico, result)  # WHY: inject or update DIA_Pico
            _merge_picocell(config, picocell, result)  # WHY: inject or update Picocell
            self._push_template_update(mistapi_mod, template_id, config, result)  # WHY: PUT to Mist
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            result["status"] = "FAILED"  # WHY: record generic failure
            result["error"] = str(error)  # WHY: preserve exception text for audit
        return result  # WHY: caller aggregates results

    def _push_template_update(
        self,
        mistapi_mod: Any,
        template_id: str,
        config: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Push the merged template configuration back to Mist."""
        update_resp = mistapi_mod.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate(  # WHY: PUT template body
            self._api,
            self._org_id,
            template_id,
            body=config,
        )
        if update_resp.status_code == 200:  # WHY: Mist success code
            result["status"] = "SUCCESS"  # WHY: caller marks row succeeded
            return  # WHY: no error to record
        result["status"] = "FAILED"  # WHY: non-200 treated as failure
        result["error"] = f"API status {update_resp.status_code}"  # WHY: preserve status for audit

    def _fetch_single_config(
        self,
        mistapi_mod: Any,
        template_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Fetch a single template config for the apply operation."""
        resp = mistapi_mod.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(  # WHY: retrieve current body
            self._api,
            self._org_id,
            template_id,
        )
        config = resp.data if hasattr(resp, "data") else {}  # WHY: safely access mocked/real payload
        if not isinstance(config, dict):  # WHY: guard against error strings
            result["status"] = "FAILED"  # WHY: mark failure so audit reflects it
            result["error"] = "Invalid configuration format"  # WHY: user-facing reason
            return None  # WHY: caller stops the merge chain
        return config  # WHY: caller merges into this config

    def _report_apply_results(self, results: list[dict[str, Any]]) -> None:
        """Generate and display apply operation results."""
        output_file = "GatewayTemplate_Config_Application_Audit.csv"  # WHY: standard audit filename
        csv_results = [_apply_result_row(r) for r in results]  # WHY: normalise for CSV columns
        self._save_data(csv_results, output_file)  # WHY: persist via host writer
        success, failed = _count_apply_outcomes(results)  # WHY: counters for summary
        _print_apply_summary(len(results), success, failed, output_file)  # WHY: user-facing summary
        logging.warning("Menu #106 complete: %s templates updated, %s failed", success, failed)  # WHY: audit trail

    # ------------------------------------------------------------------ #
    # Clone-by-location helpers                                           #
    # ------------------------------------------------------------------ #

    def _load_sites_with_location(
        self,
    ) -> list[dict[str, str]] | None:
        """Load site data with state and country information."""
        print("\n  Step 1: Loading site data...")  # WHY: user-facing step marker
        self._check_csv("SiteList.csv", self._gen_sites)  # WHY: ensure cache is fresh or generated
        all_sites = self._read_sites_csv()  # WHY: parse cached CSV into dicts
        if all_sites is None:  # WHY: read failure surfaced
            return None  # WHY: caller aborts
        if not all_sites:  # WHY: empty org
            print("  No sites found in organization.")  # WHY: user-facing
            return None  # WHY: caller aborts
        sites_with_loc = _filter_sites_with_location(all_sites)  # WHY: drop entries without location
        if not sites_with_loc:  # WHY: nothing to plan against
            print("  No sites found with state or country information.")  # WHY: user-facing
            return None  # WHY: caller aborts
        print(f"  Found {len(sites_with_loc)} sites with location data")  # WHY: user-facing count
        return sites_with_loc  # WHY: caller consumes list

    def _read_sites_csv(self) -> list[dict[str, str]] | None:
        """Read SiteList.csv into a list of dicts, or None on error."""
        sites_path = self._get_csv_path("SiteList.csv")  # WHY: cached-data location
        try:
            with open(sites_path, encoding="utf-8") as fin:  # WHY: text read with explicit encoding
                return list(csv.DictReader(fin))  # WHY: materialise all rows
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: file/CSV errors vary
            print(f"  Error loading sites: {error}")  # WHY: user-facing
            return None  # WHY: caller aborts on None

    @staticmethod
    def _get_unique_locations(
        sites: list[dict[str, str]],
    ) -> tuple[set[str], set[str]]:
        """Extract unique states and countries from site data."""
        states: set[str] = set()  # WHY: state destinations
        countries: set[str] = set()  # WHY: fallback country destinations
        for site in sites:  # WHY: iterate located sites
            if site["state"]:  # WHY: prefer state-level grouping
                states.add(site["state"])  # WHY: unique state accumulation
            elif site["country"]:  # WHY: country fallback when no state
                countries.add(site["country"])  # WHY: unique country accumulation
        print(f"  Unique states found: {len(states)}")  # WHY: user-facing count
        print(f"  Unique countries (for sites without state): {len(countries)}")  # WHY: user-facing count
        return states, countries  # WHY: caller consumes both sets

    @staticmethod
    def _plan_template_creation(
        source: dict[str, Any],
        states: set[str],
        countries: set[str],
    ) -> list[dict[str, str]]:
        """Plan which templates to create based on locations."""
        source_name = source.get("name", "Unnamed")  # WHY: base name for derived templates
        to_create: list[dict[str, str]] = []  # WHY: accumulator for per-location templates
        to_create.extend(_state_creation_plans(source_name, states))  # WHY: sorted state templates
        to_create.extend(_country_creation_plans(source_name, countries))  # WHY: sorted country templates
        _print_creation_preview(to_create)  # WHY: user-facing preview
        return to_create  # WHY: caller confirms before executing

    @staticmethod
    def _plan_site_assignments(
        sites: list[dict[str, str]],
        source: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Plan site-to-template assignments."""
        source_name = source.get("name", "Unnamed")  # WHY: base name for derived templates
        assignments: list[dict[str, str]] = []  # WHY: accumulator for per-site plans
        for site in sites:  # WHY: one plan per located site
            plan = _plan_single_assignment(site, source_name)  # WHY: pure helper handles state/country choice
            if plan is not None:  # WHY: skip sites without any location
                assignments.append(plan)  # WHY: record plan
        print(f"\n  {len(assignments)} sites will be assigned to templates")  # WHY: user-facing count
        return assignments  # WHY: caller confirms before executing

    def _confirm_clone(
        self,
        to_create: list[dict[str, str]],
        assignments: list[dict[str, str]],
    ) -> bool:
        """Get confirmation for clone operation."""
        _print_clone_warning(len(to_create), len(assignments))  # WHY: destructive-op warning
        confirmation = self._prompt_clone_confirmation()  # WHY: guarded prompt
        if confirmation is None:  # WHY: user cancelled interactively
            return False  # WHY: caller aborts
        if confirmation != "CLONE":  # WHY: require exact uppercase match
            print("  Operation cancelled.")  # WHY: user-facing
            return False  # WHY: caller aborts
        return True  # WHY: user confirmed

    def _prompt_clone_confirmation(self) -> str | None:
        """Prompt for the CLONE confirmation word, or None if cancelled."""
        try:
            return self._input_fn("\n  Confirmation: ", context="menu_111_confirmation").strip()  # WHY: trimmed
        except (EOFError, KeyboardInterrupt):  # WHY: user cancelled interactive session
            print("\n  Operation cancelled.")  # WHY: user-facing cancel message
            return None  # WHY: caller treats None as cancel

    def _get_existing_template_names(self) -> dict[str, str]:
        """Get mapping of existing template names to IDs."""
        try:
            resp = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(  # WHY: full list for name lookup
                self._api,
                self._org_id,
                limit=1000,
            )
            templates = mistapi.get_all(response=resp, mist_session=self._api)  # WHY: exhaust pagination
            return {t.get("name"): t.get("id") for t in templates if t.get("name")}  # WHY: name->id dict
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            logging.error("GatewayTemplateConfigManager: Error fetching templates: %s", error)  # WHY: audit
            return {}  # WHY: empty map signals "no known names"

    def _create_templates(
        self,
        source_config: dict[str, Any],
        to_create: list[dict[str, str]],
        existing_names: dict[str, str],
    ) -> dict[str, str]:
        """Create new templates based on source configuration."""
        print("\n  Step 5: Creating templates...")  # WHY: user-facing step marker
        template_map: dict[str, str] = {}  # WHY: name -> id accumulator for assignments
        for info in tqdm(to_create, desc="Creating templates", unit="template"):  # WHY: progress bar
            name = info["name"]  # WHY: candidate template name
            if name in existing_names:  # WHY: idempotency for reruns
                template_map[name] = existing_names[name]  # WHY: reuse existing id
                logging.info("Template %s already exists, skipping", name)  # WHY: audit trail
                continue  # WHY: no creation needed
            self._create_single_template(mistapi, name, source_config, template_map)  # WHY: attempt creation
        return template_map  # WHY: caller uses map for assignments

    def _create_single_template(
        self,
        mistapi_mod: Any,
        name: str,
        source_config: dict[str, Any],
        template_map: dict[str, str],
    ) -> None:
        """Create one template from the source configuration."""
        try:
            new_config = _prepare_new_template_body(source_config, name)  # WHY: strip id/timestamps + rename
            resp = mistapi_mod.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate(  # WHY: POST new template
                self._api,
                self._org_id,
                body=new_config,
            )
            if resp.status_code == 200:  # WHY: Mist success code
                new_id = resp.data.get("id") if hasattr(resp, "data") else ""  # WHY: extract new id safely
                template_map[name] = new_id  # WHY: record for later assignments
                logging.info("Created template %s (ID: %s)", name, new_id)  # WHY: audit trail
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            logging.error("Error creating template %s: %s", name, error)  # WHY: audit trail

    def _assign_sites(
        self,
        assignments: list[dict[str, str]],
        template_map: dict[str, str],
    ) -> list[dict[str, str]]:
        """Assign sites to their corresponding templates."""
        print("\n  Step 6: Assigning sites to templates...")  # WHY: user-facing step marker
        results: list[dict[str, str]] = []  # WHY: accumulator for audit rows
        for assignment in tqdm(assignments, desc="Assigning sites", unit="site"):  # WHY: progress bar
            result = self._assign_single_site(mistapi, assignment, template_map)  # WHY: per-site attempt
            results.append(result)  # WHY: record outcome
        return results  # WHY: caller reports on the batch

    def _assign_single_site(
        self,
        mistapi_mod: Any,
        assignment: dict[str, str],
        template_map: dict[str, str],
    ) -> dict[str, str]:
        """Assign a single site to its target template."""
        site_id = assignment["site_id"]  # WHY: identifier for API call
        target_name = assignment["target_template_name"]  # WHY: expected template name
        target_id = template_map.get(target_name, "")  # WHY: resolve to id via lookup
        result = _empty_site_result(assignment, target_name)  # WHY: uniform row skeleton
        skip_reason = _assignment_skip_reason(target_id, assignment)  # WHY: check idempotency and lookup misses
        if skip_reason is not None:  # WHY: no work needed
            result["status"] = "SKIPPED"  # WHY: mark row skipped
            result["error"] = skip_reason  # WHY: preserve reason for audit
            return result  # WHY: caller records row
        return self._update_site_template(mistapi_mod, site_id, target_id, result)  # WHY: perform the PUT

    def _update_site_template(
        self,
        mistapi_mod: Any,
        site_id: str,
        target_id: str,
        result: dict[str, str],
    ) -> dict[str, str]:
        """Push template assignment update to a single site."""
        try:
            resp = mistapi_mod.api.v1.sites.sites.updateSiteInfo(  # WHY: PUT site-info with template id
                self._api,
                site_id,
                body={"gatewaytemplate_id": target_id},
            )
            _record_update_status(resp, result)  # WHY: status-code branching in helper
        except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types
            result["status"] = "ERROR"  # WHY: distinguish exception from HTTP failure
            result["error"] = str(error)  # WHY: preserve exception text
        return result  # WHY: caller accumulates result rows

    def _report_clone_results(
        self,
        to_create: list[dict[str, str]],
        site_results: list[dict[str, str]],
    ) -> None:
        """Generate and display clone operation results."""
        output = "Site_Template_Assignment_By_State_Country_Audit.csv"  # WHY: standard audit filename
        self._save_data(site_results, output)  # WHY: persist via host writer
        counts = _count_clone_outcomes(site_results)  # WHY: unified counter helper
        _print_clone_summary(len(to_create), counts, output)  # WHY: user-facing summary
        logging.warning(  # WHY: audit trail with success/failure counts
            "Menu #111 complete: %s sites assigned, %s failed",
            counts["assigned"],
            counts["failed"],
        )


# ------------------------------------------------------------------ #
# Module-level helper functions (keep class complexity low)           #
# ------------------------------------------------------------------ #


def _log_fetch_failure(template_name: str, error: Exception) -> None:
    """Emit user + audit output for a failed template fetch."""
    print(f"  Error fetching template configuration: {error}")  # WHY: user-facing
    logging.error(  # WHY: audit trail
        "GatewayTemplateConfigManager: Failed to fetch %s: %s",
        template_name,
        error,
    )


def _log_invalid_fetch(template_name: str) -> None:
    """Emit user + audit output when a fetch returns an unexpected shape."""
    print("  Error: Template configuration is not in expected format.")  # WHY: user-facing
    logging.error(  # WHY: audit trail
        "GatewayTemplateConfigManager: Invalid config format for %s",
        template_name,
    )


def _print_extract_banner() -> None:
    """Print the Menu 105 banner."""
    print("\n  Extract Gateway Template Configuration (Menu 105)")  # WHY: user-facing header
    print("=" * 70)  # WHY: visual separator


def _print_apply_banner() -> None:
    """Print the destructive Menu 106 banner."""
    print("\n  DESTRUCTIVE: Apply Gateway Template Configuration (Menu 106)")  # WHY: header + warning
    print("=" * 70)  # WHY: visual separator
    print("  !? WARNING: This operation modifies gateway templates")  # WHY: safety warning
    print("  !? Requires uppercase 'APPLY' confirmation")  # WHY: input hint
    print("=" * 70)  # WHY: visual separator


def _print_clone_banner() -> None:
    """Print the destructive Menu 111 banner."""
    print("\n  DESTRUCTIVE: Clone Gateway Templates by State and Country")  # WHY: header + warning
    print("=" * 70)  # WHY: visual separator
    print("  !? WARNING: This operation creates new gateway templates")  # WHY: safety warning
    print("  !? WARNING: This operation modifies site template assignments")  # WHY: safety warning
    print("  !? Ensure source template is properly configured before cloning")  # WHY: pre-check reminder
    print("=" * 70)  # WHY: visual separator


def _print_template_menu(templates: list[dict[str, Any]]) -> None:
    """Render the template-selection menu."""
    print(f"\n  Available Gateway Templates ({len(templates)} found):")  # WHY: user-facing header
    print("-" * 70)  # WHY: visual separator
    for index, template in enumerate(templates):  # WHY: numbered list for indexed selection
        name = template.get("name", "Unnamed Template")  # WHY: safe name fallback
        template_type = template.get("type", "standalone")  # WHY: display type for context
        print(f"  [{index}] {name:40} Type: {template_type}")  # WHY: aligned columns
    print()  # WHY: blank line before prompt


def _validate_template_index(user_input: str, size: int) -> int | None:
    """Return a valid template index, or None with a printed reason."""
    if not user_input.isdigit():  # WHY: reject non-numeric input up front
        print("  Invalid input. Please enter a numeric index.")  # WHY: user-facing
        return None  # WHY: caller treats None as invalid
    index = int(user_input)  # WHY: safe now that we know it's digits
    if index < 0 or index >= size:  # WHY: bounds check
        print(f"  Invalid index. Please select between 0 " f"and {size - 1}.")  # WHY: user-facing
        return None  # WHY: caller treats None as out-of-range
    return index  # WHY: caller uses index to look up row


def _extract_dia_pico(template_config: dict[str, Any], template_name: str) -> dict[str, Any] | None:
    """Extract the DIA_Pico block from a template's path_preferences."""
    print("\n  Extracting Traffic Steering configuration...")  # WHY: user-facing step marker
    path_prefs = template_config.get("path_preferences", {})  # WHY: parent container for DIA_Pico
    dia_pico = path_prefs.get("DIA_Pico") if isinstance(path_prefs, dict) else None  # WHY: guarded access
    if dia_pico:  # WHY: user-facing found/not-found messaging
        print("  -> Found 'DIA_Pico' in Traffic Steering")  # WHY: positive result
        logging.info("GatewayTemplateConfigManager: Found DIA_Pico in %s", template_name)  # WHY: audit trail
    else:
        print("  -> 'DIA_Pico' not found in Traffic Steering")  # WHY: negative result
    return dia_pico  # WHY: caller stores or ignores


def _build_extraction_payload(
    dia_pico: dict[str, Any] | None,
    picocell: dict[str, Any] | None,
    template: dict[str, Any],
) -> dict[str, Any]:
    """Build the JSON structure persisted by Menu 105."""
    return {
        "source_template_name": template.get("name", "Unnamed"),  # WHY: provenance for audit/UX
        "source_template_id": template.get("id"),  # WHY: allow re-linking to origin
        "extraction_timestamp": datetime.now(UTC).isoformat(),  # WHY: audit trail on disk
        "extracted_by": "MistHelper Menu #105",  # WHY: identify tool that wrote this file
        "configurations": {
            "traffic_steering": {"DIA_Pico": dia_pico},  # WHY: mirror in-Mist layout
            "application_policies": {"Picocell": picocell},  # WHY: mirror in-Mist layout
        },
    }


def _print_save_success(json_filepath: str) -> None:
    """Print the save-success block for Menu 105."""
    print("\n  Success! Configuration extracted and saved to:")  # WHY: success header
    print(f"  -> {json_filepath}")  # WHY: show file path
    print("\n  Use Menu Option 106 to apply this configuration " "to other templates.")  # WHY: next-step hint


def _print_file_menu(files: list[str]) -> None:
    """Render the extraction-file selection menu."""
    print(f"\n  Available extraction files ({len(files)}):")  # WHY: user-facing header
    for idx, filename in enumerate(files):  # WHY: numbered list
        print(f"  [{idx}] {filename}")  # WHY: display filename


def _is_valid_file_index(selection: str, size: int) -> bool:
    """Return True when selection is a valid numeric index within [0, size)."""
    if not selection.isdigit():  # WHY: reject non-numeric input
        return False  # WHY: caller marks invalid
    return int(selection) < size  # WHY: bounds check


def _available_destinations(
    templates: list[dict[str, Any]],
    extraction_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return templates eligible as apply destinations (source excluded)."""
    source_id = extraction_data.get("source_template_id")  # WHY: prevent self-apply loops
    return [t for t in templates if t.get("id") != source_id]  # WHY: exclude source


def _print_destination_menu(available: list[dict[str, Any]]) -> None:
    """Render the destination-selection menu."""
    print(f"\n  Step 2: Select destination templates " f"({len(available)} available):")  # WHY: header
    for idx, tpl in enumerate(available):  # WHY: numbered list
        print(f"  [{idx}] {tpl.get('name', 'Unnamed')}")  # WHY: display name
    print("\n  Enter template numbers (comma-separated) or 'all':")  # WHY: input hint


def _split_extracted_payloads(
    extraction_data: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Split extraction payload into (dia_pico, picocell) blocks."""
    configs = extraction_data.get("configurations", {})  # WHY: parent container
    dia_pico = configs.get("traffic_steering", {}).get("DIA_Pico")  # WHY: extract DIA_Pico
    picocell = configs.get("application_policies", {}).get("Picocell")  # WHY: extract Picocell
    return dia_pico, picocell  # WHY: caller merges each into destinations


def _print_apply_preview(
    dia_pico: dict[str, Any] | None,
    picocell: dict[str, Any] | None,
) -> None:
    """Print the apply preview block."""
    print("\n  Step 3: Configuration Preview")  # WHY: header
    print("-" * 70)  # WHY: visual separator
    if dia_pico:  # WHY: only show block when present
        print("  Traffic Steering (DIA_Pico):")  # WHY: sub-header
        strategy = dia_pico.get("strategy", "Unknown")  # WHY: summarise strategy for user
        paths = dia_pico.get("paths", [])  # WHY: summarise path count
        print(f"    Strategy: {strategy}, Paths: {len(paths)}")  # WHY: summary line
    if picocell:  # WHY: only show block when present
        print("  Application Policies (Picocell):")  # WHY: sub-header
        print(f"    Name: {picocell.get('name', 'Unknown')}")  # WHY: display policy name


def _print_apply_warning(destination_count: int) -> None:
    """Print the apply destructive-op warning."""
    print(f"\n  {'=' * 70}")  # WHY: visual separator
    print(f"  !? CRITICAL: This will modify {destination_count} template(s)")  # WHY: severity marker
    print("  !? Type 'APPLY' (all caps) to proceed or " "anything else to cancel")  # WHY: input hint
    print(f"  {'=' * 70}")  # WHY: visual separator


def _empty_apply_result(template_name: str, template_id: str) -> dict[str, Any]:
    """Return an empty apply-result skeleton."""
    return {
        "template_name": template_name,  # WHY: audit row identifier
        "template_id": template_id,  # WHY: audit row identifier
        "status": "",  # WHY: filled by later branches
        "changes_made": [],  # WHY: merge helpers append here
        "error": "",  # WHY: filled on failure
    }


def _apply_result_row(r: dict[str, Any]) -> dict[str, Any]:
    """Normalize an apply-result dict into a CSV-friendly row."""
    return {
        "template_name": r["template_name"],  # WHY: keep row identifier
        "template_id": r["template_id"],  # WHY: keep row identifier
        "status": r["status"],  # WHY: SUCCESS/FAILED
        "changes_made": ("; ".join(r["changes_made"]) if r["changes_made"] else ""),  # WHY: flatten list to string
        "error": r["error"],  # WHY: preserve error text
    }


def _count_apply_outcomes(results: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (success, failed) counts from apply results."""
    success = sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: count success rows
    return success, len(results) - success  # WHY: derive failed from complement


def _print_apply_summary(total: int, success: int, failed: int, output_file: str) -> None:
    """Print the Menu 106 completion summary."""
    print("\n  Configuration Application Complete!")  # WHY: header
    print("=" * 70)  # WHY: visual separator
    print(f"  Templates Processed: {total}")  # WHY: total count
    print(f"  Successfully Updated: {success}")  # WHY: success count
    print(f"  Failed: {failed}")  # WHY: failure count
    print(f"\n  Audit report saved to: {output_file}")  # WHY: point user to CSV


def _state_creation_plans(source_name: str, states: set[str]) -> list[dict[str, str]]:
    """Return the per-state template plans."""
    return [
        {
            "name": f"{source_name}_{state}",  # WHY: name convention <source>_<state>
            "location_type": "state",  # WHY: mark plan type
            "location_value": state,  # WHY: keep raw value for audit
        }
        for state in sorted(states)  # WHY: deterministic output
    ]


def _country_creation_plans(source_name: str, countries: set[str]) -> list[dict[str, str]]:
    """Return the per-country template plans."""
    return [
        {
            "name": f"{source_name}_{country}",  # WHY: name convention <source>_<country>
            "location_type": "country",  # WHY: mark plan type
            "location_value": country,  # WHY: keep raw value for audit
        }
        for country in sorted(countries)  # WHY: deterministic output
    ]


def _print_creation_preview(to_create: list[dict[str, str]]) -> None:
    """Print the pre-clone template-creation preview."""
    print(f"\n  Step 4: Preview - {len(to_create)} templates " "will be created:")  # WHY: user-facing header
    for info in to_create:  # WHY: enumerate for review
        print(f"   - {info['name']} " f"(for {info['location_type']}: {info['location_value']})")  # WHY: line


def _plan_single_assignment(
    site: dict[str, str],
    source_name: str,
) -> dict[str, str] | None:
    """Build the per-site assignment plan or None if location is missing."""
    if site["state"]:  # WHY: prefer state-level template
        target = f"{source_name}_{site['state']}"  # WHY: state naming convention
    elif site["country"]:  # WHY: fallback to country template
        target = f"{source_name}_{site['country']}"  # WHY: country naming convention
    else:
        return None  # WHY: no location => no plan
    return {
        "site_id": site["id"],  # WHY: identifier for API call
        "site_name": site["name"],  # WHY: audit-friendly identifier
        "target_template_name": target,  # WHY: name resolved via template_map later
        "current_template_id": site["current_template_id"],  # WHY: used for idempotency check
    }


def _print_clone_warning(create_count: int, assign_count: int) -> None:
    """Print the clone destructive-op warning."""
    print(f"\n  {'=' * 70}")  # WHY: visual separator
    print(f"  !? CRITICAL: This will create {create_count} new templates")  # WHY: severity marker
    print(f"  !? and modify {assign_count} site template assignments")  # WHY: severity marker
    print("  !? Type 'CLONE' (all caps) to proceed or " "anything else to cancel")  # WHY: input hint
    print(f"  {'=' * 70}")  # WHY: visual separator


def _prepare_new_template_body(source_config: dict[str, Any], name: str) -> dict[str, Any]:
    """Return a clean template body derived from the source config."""
    new_config = dict(source_config)  # WHY: shallow copy to avoid mutating caller's dict
    new_config["name"] = name  # WHY: assign new template name
    for field in ("id", "org_id", "created_time", "modified_time"):  # WHY: strip fields owned by Mist
        new_config.pop(field, None)  # WHY: safe pop
    return new_config  # WHY: caller POSTs this body


def _empty_site_result(assignment: dict[str, str], target_name: str) -> dict[str, str]:
    """Return an empty site-assignment result skeleton."""
    return {
        "site_name": assignment["site_name"],  # WHY: audit row identifier
        "site_id": assignment["site_id"],  # WHY: audit row identifier
        "target_template_name": target_name,  # WHY: intended template name
        "status": "",  # WHY: filled by later branches
        "error": "",  # WHY: filled on failure
    }


def _assignment_skip_reason(target_id: str, assignment: dict[str, str]) -> str | None:
    """Return a skip reason string or None if the assignment should proceed."""
    if not target_id:  # WHY: template not created / not found
        return "Target template not found"  # WHY: audit-friendly reason
    if assignment["current_template_id"] == target_id:  # WHY: idempotency; already correct
        return "Already assigned"  # WHY: audit-friendly reason
    return None  # WHY: caller performs the API PUT


def _record_update_status(resp: Any, result: dict[str, str]) -> None:
    """Update result with the outcome of a site-info PUT."""
    if resp.status_code == 200:  # WHY: Mist success code
        result["status"] = "ASSIGNED"  # WHY: mark row assigned
        return  # WHY: no error to record
    result["status"] = "FAILED"  # WHY: non-200 => failure
    result["error"] = f"API status {resp.status_code}"  # WHY: preserve status code


_CLONE_FAILURE_STATUSES = frozenset({"FAILED", "ERROR"})  # WHY: shared set keeps counter branchless


def _count_status(site_results: list[dict[str, str]], status: str) -> int:
    """Return count of site rows whose status equals the target label."""
    return sum(1 for row in site_results if row["status"] == status)  # WHY: single-pass count


def _count_failed(site_results: list[dict[str, str]]) -> int:
    """Return count of site rows whose status indicates any failure category."""
    return sum(1 for row in site_results if row["status"] in _CLONE_FAILURE_STATUSES)  # WHY: shared taxonomy


def _count_clone_outcomes(site_results: list[dict[str, str]]) -> dict[str, int]:
    """Return counts for the three clone outcome categories."""
    return {
        "assigned": _count_status(site_results, "ASSIGNED"),  # WHY: success total
        "skipped": _count_status(site_results, "SKIPPED"),  # WHY: no-op total
        "failed": _count_failed(site_results),  # WHY: failure total (spans two statuses)
    }


def _print_clone_summary(create_count: int, counts: dict[str, int], output: str) -> None:
    """Print the Menu 111 completion summary."""
    print("\n  Gateway Template Cloning by State/Country Complete!")  # WHY: header
    print("=" * 70)  # WHY: visual separator
    print(f"  TEMPLATE CREATION: {create_count} planned")  # WHY: planned template count
    print("\n  SITE ASSIGNMENTS:")  # WHY: sub-header
    print(f"    Assigned: {counts['assigned']}")  # WHY: success count
    print(f"    Skipped: {counts['skipped']}")  # WHY: no-op count
    print(f"    Failed: {counts['failed']}")  # WHY: failure count
    print(f"\n  AUDIT REPORT: {output}")  # WHY: point user to CSV
    print("=" * 70)  # WHY: visual separator


def _find_picocell_policy(
    template_config: dict[str, Any],
    template_name: str,
) -> dict[str, Any] | None:
    """Search service_policies for a Picocell entry."""
    print("\n  Extracting Application Policies configuration...")  # WHY: user-facing step marker
    service_policies = template_config.get("service_policies", [])  # WHY: parent container
    picocell = _scan_service_policies(service_policies, template_name)  # WHY: guarded scan
    if not picocell:  # WHY: user-facing negative-result message
        print("  -> 'Picocell' not found in Application Policies")  # WHY: negative result
    return picocell  # WHY: caller stores or ignores


def _scan_service_policies(service_policies: Any, template_name: str) -> dict[str, Any] | None:
    """Return the first Picocell entry from service_policies, or None."""
    if not isinstance(service_policies, list):  # WHY: guard against malformed configs
        return None  # WHY: nothing to scan
    for policy in service_policies:  # WHY: linear scan; count is small
        if isinstance(policy, dict) and policy.get("name") == "Picocell":  # WHY: name match anchors identity
            print("  -> Found 'Picocell' in Application Policies")  # WHY: positive result
            logging.info("GatewayTemplateConfigManager: Found Picocell in %s", template_name)  # WHY: audit
            return policy  # WHY: caller receives the block
    return None  # WHY: not found


def _parse_template_indices(
    selection: str,
    available: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    """Parse comma-separated indices into template list."""
    indices = _parse_comma_int_list(selection)  # WHY: parse and validate the raw string
    if indices is None:  # WHY: parse failure surfaced by helper
        return None  # WHY: caller aborts on None
    selected = [available[i] for i in indices if 0 <= i < len(available)]  # WHY: filter out-of-range values
    if not selected:  # WHY: no valid picks remain
        print("  No valid templates selected.")  # WHY: user-facing
        return None  # WHY: caller aborts on None
    return selected  # WHY: caller consumes list


def _parse_comma_int_list(selection: str) -> list[int] | None:
    """Return a list of ints from a comma-separated string, or None on error."""
    try:
        return [int(x.strip()) for x in selection.split(",")]  # WHY: tolerate whitespace between values
    except (ValueError, IndexError):  # WHY: non-int token or unexpected shape
        print("  Invalid selection format.")  # WHY: user-facing
        return None  # WHY: caller aborts on None


def _merge_dia_pico(
    config: dict[str, Any],
    dia_pico: dict[str, Any] | None,
    result: dict[str, Any],
) -> None:
    """Merge DIA_Pico into a template configuration."""
    if not dia_pico:  # WHY: nothing to merge when block absent
        return  # WHY: caller keeps config unchanged
    if "path_preferences" not in config:  # WHY: create container when missing
        config["path_preferences"] = {}  # WHY: prepare for the assignment below
    config["path_preferences"]["DIA_Pico"] = dia_pico  # WHY: overwrite/insert DIA_Pico
    result["changes_made"].append("Added/Updated DIA_Pico")  # WHY: audit change


def _merge_picocell(
    config: dict[str, Any],
    picocell: dict[str, Any] | None,
    result: dict[str, Any],
) -> None:
    """Merge Picocell policy into a template configuration."""
    if not picocell:  # WHY: nothing to merge when block absent
        return  # WHY: caller keeps config unchanged
    if "service_policies" not in config:  # WHY: create container when missing
        config["service_policies"] = []  # WHY: prepare for the branches below
    existing_idx = _find_existing_picocell_index(config["service_policies"])  # WHY: prefer in-place update
    if existing_idx is not None:  # WHY: update path
        config["service_policies"][existing_idx] = picocell  # WHY: overwrite existing entry
        result["changes_made"].append("Updated existing Picocell")  # WHY: audit change
        return  # WHY: no insert needed
    _insert_picocell_policy(config["service_policies"], picocell, result)  # WHY: insert path


def _find_existing_picocell_index(
    policies: list[dict[str, Any]],
) -> int | None:
    """Find the index of existing Picocell policy in service_policies."""
    for idx, policy in enumerate(policies):  # WHY: linear scan; count is small
        if isinstance(policy, dict) and policy.get("name") == "Picocell":  # WHY: name match anchors identity
            return idx  # WHY: caller uses index to overwrite
    return None  # WHY: caller inserts instead


def _insert_picocell_policy(
    policies: list[dict[str, Any]],
    picocell: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Insert Picocell policy at the appropriate position."""
    policy_count = len(policies)  # WHY: threshold check below
    if policy_count >= _PICOCELL_INSERT_THRESHOLD:  # WHY: fixed insertion slot when enough policies exist
        policies.insert(_PICOCELL_INSERT_ANCHOR, picocell)  # WHY: land at position 14 (0-indexed 13)
        result["changes_made"].append("Inserted Picocell at position 14")  # WHY: audit change
        return  # WHY: skip the append path
    policies.append(picocell)  # WHY: too few policies; append at end
    result["changes_made"].append(f"Added Picocell at position {policy_count + 1}")  # WHY: audit change


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
    if not address or not country:  # WHY: both inputs required for meaningful parse
        return ""  # WHY: caller treats "" as unknown
    if country in _SMALL_ISLAND_COUNTRIES:  # WHY: these formats don't carry usable states
        return ""  # WHY: skip these countries entirely
    if "," in address:  # WHY: comma format has structured parts
        return _parse_state_comma_separated(address)  # WHY: dedicated parser
    return _parse_state_space_separated(address, country)  # WHY: dedicated parser


def _parse_state_comma_separated(address: str) -> str:
    """Parse state from comma-separated address parts."""
    parts = [p.strip() for p in address.split(",")]  # WHY: normalise whitespace around each part
    if len(parts) < _MIN_COMMA_PARTS:  # WHY: need street/city/state-block trio
        return ""  # WHY: not enough parts
    for part in parts:  # WHY: any part may carry the state token
        state = _match_state_in_part(part)  # WHY: pure matcher returns state or ""
        if state:  # WHY: first hit wins
            return state  # WHY: caller consumes state
    return ""  # WHY: no matches


def _match_state_in_part(part: str) -> str:
    """Return a US/CA/standalone state code found in `part`, or ''."""
    match_us = re.search(r"\b([A-Z]{2})\s+\d{5}", part)  # WHY: US ZIP-adjacent state code
    if match_us:  # WHY: prefer US match when present
        return match_us.group(1)  # WHY: state token
    match_ca = re.search(r"^([A-Z]{2})\s+[A-Z]\d[A-Z]", part)  # WHY: CA postal-adjacent province
    if match_ca:  # WHY: prefer CA match next
        return match_ca.group(1)  # WHY: province token
    match_alone = re.search(r"^([A-Z]{2})$", part)  # WHY: bare 2-letter code
    if match_alone:  # WHY: standalone token
        return match_alone.group(1)  # WHY: code token
    return ""  # WHY: no match in this part


def _parse_state_space_separated(address: str, country: str) -> str:
    """Parse state from space-separated address."""
    parts = address.split()  # WHY: whitespace-separated tokens
    if country == "CA" and len(parts) >= _MIN_COMMA_PARTS:  # WHY: Canadian shape needs 3+ tokens
        return _parse_canadian_state(parts)  # WHY: dedicated parser
    if len(parts) < 2:  # WHY: need at least city + state token
        return ""  # WHY: too short to parse
    return _parse_general_state(address, parts, country)  # WHY: broader parser


def _parse_canadian_state(parts: list[str]) -> str:
    """Parse state from Canadian address format."""
    for i, part in enumerate(parts):  # WHY: scan for province code
        if _is_ca_province_at(parts, i, part):  # WHY: encapsulate two-check predicate
            return part  # WHY: caller receives province token
    return ""  # WHY: no province found


def _is_ca_province_at(parts: list[str], i: int, part: str) -> bool:
    """Return True when parts[i] looks like a CA province followed by a postal code."""
    if len(part) != 2 or not part.isupper():  # WHY: province tokens are 2 uppercase letters
        return False  # WHY: not a province candidate
    if i + 1 >= len(parts):  # WHY: need a following token for the postal test
        return False  # WHY: no follower means we can't confirm
    return bool(re.match(r"^[A-Z]\d[A-Z]$", parts[i + 1]))  # WHY: postal-prefix pattern


def _parse_general_state(address: str, parts: list[str], country: str) -> str:
    """Parse state from general address format."""
    special = _match_special_regions(address)  # WHY: handle named regions like Puerto Rico
    if special:  # WHY: special-case wins over positional guesses
        return special  # WHY: caller receives special region
    postal_index = _find_postal_index(parts)  # WHY: postal token anchors state position
    if postal_index > 1:  # WHY: state usually sits directly before postal
        return parts[postal_index - 1]  # WHY: token immediately before postal
    if postal_index == -1:  # WHY: no postal found; fall back to country-based heuristic
        return _infer_state_without_postal(parts, country)  # WHY: dedicated inference
    return ""  # WHY: postal is at index 0 or 1; nothing reliable to return


def _match_special_regions(address: str) -> str:
    """Return a special-case region label found in address, or ''."""
    address_lower = address.lower()  # WHY: case-insensitive match
    if "puerto rico" in address_lower:  # WHY: US territory label
        return "Puerto Rico"  # WHY: canonical label
    if "bay islands" in address_lower:  # WHY: HN department label
        return "Bay Islands"  # WHY: canonical label
    return ""  # WHY: no special region found


def _find_postal_index(parts: list[str]) -> int:
    """Find the index of the first part starting with a digit."""
    for i, part in enumerate(parts):  # WHY: linear scan; count is small
        if re.match(r"^\d", part):  # WHY: leading digit denotes postal-like token
            return i  # WHY: caller consumes index
    return -1  # WHY: sentinel means no postal found


def _infer_state_without_postal(parts: list[str], country: str) -> str:
    """Infer state when no postal code is present."""
    if country not in _LATAM_COUNTRIES and len(parts) == 2:  # WHY: non-LATAM short address can't be inferred
        return ""  # WHY: not enough info
    if country in _LATAM_COUNTRIES or len(parts) > 2:  # WHY: LATAM or longer addresses trust last token
        return parts[-1]  # WHY: convention places state at the end
    return ""  # WHY: catch-all


def _filter_sites_with_location(
    all_sites: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Filter sites that have state or country location data."""
    result: list[dict[str, str]] = []  # WHY: accumulator for located sites
    for site in all_sites:  # WHY: iterate every site row
        located = _project_site_with_location(site)  # WHY: helper does parse + guard
        if located is not None:  # WHY: skip sites without any location
            result.append(located)  # WHY: record projected row
    return result  # WHY: caller consumes filtered list


def _project_site_with_location(site: dict[str, str]) -> dict[str, str] | None:
    """Return a normalized site dict with state/country, or None if no location."""
    address = site.get("address", "").strip()  # WHY: source for state parsing
    country = site.get("country_code", "").strip()  # WHY: fallback grouping key
    state = parse_state_from_address(address, country)  # WHY: derive state from address
    if not (state or country):  # WHY: skip if neither is usable
        return None  # WHY: caller filters this out
    return {
        "id": site.get("id", "").strip(),  # WHY: site identifier
        "name": site.get("name", "").strip(),  # WHY: audit-friendly name
        "state": state,  # WHY: preferred grouping key
        "country": country,  # WHY: fallback grouping key
        "current_template_id": site.get("gatewaytemplate_id", "").strip(),  # WHY: idempotency check
    }
