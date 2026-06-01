"""Gateway WAN2 variable migration for MistHelper.

Extracts update_gateway_templates_wan2_variable (Menu #104) from
MistHelper.py into a class with dependency injection for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations

import concurrent.futures
import csv
import logging
import threading
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from tqdm import tqdm


class GatewayWan2VariableMigrator:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Migrate gateway templates between hardcoded ports and WAN2 variable.

    Supports bidirectional operation:
    - APPLY: Replace hardcoded 'ge-0/0/1' with {{wan2_interface}} variable
    - REVERT: Replace {{wan2_interface}} with hardcoded 'ge-0/0/1'

    Both modes preserve device-level static IP overrides by migrating
    port_config keys on individual devices.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        org_id: str,
        apisession: Any,
        site_exclude_prefix: str,
        check_and_generate_csv_fn: Callable[..., Any],
        generate_templates_fn: Callable[..., Any],
        generate_sites_fn: Callable[..., Any],
        get_csv_path_fn: Callable[[str], str],
        save_data_fn: Callable[..., Any],
        input_fn: Callable[[str], str] | None = None,
        connection_pool_fn: Callable[..., Any] | None = None,
    ) -> None:
        """Initialize with all external dependencies.

        Args:
            org_id: Mist organization ID.
            apisession: Authenticated mistapi session.
            site_exclude_prefix: Prefix for sites to exclude.
            check_and_generate_csv_fn: Cache check/generation function.
            generate_templates_fn: Gateway templates CSV generator.
            generate_sites_fn: Sites CSV generator.
            get_csv_path_fn: Resolves CSV filenames to full paths.
            save_data_fn: Writes data to output files.
            input_fn: User input function (defaults to built-in input).
            connection_pool_fn: Parallel execution manager for fast mode.
        """
        self._org_id = org_id
        self._apisession = apisession
        self._site_exclude_prefix = site_exclude_prefix
        self._check_csv = check_and_generate_csv_fn
        self._gen_templates = generate_templates_fn
        self._gen_sites = generate_sites_fn
        self._get_csv_path = get_csv_path_fn
        self._save_data = save_data_fn
        self._input_fn = input_fn or input
        self._pool_fn = connection_pool_fn

        # Runtime state (set during execute)
        self._search_pattern = ""
        self._replacement_value = ""
        self._operation_mode = ""
        self._dry_run = False

    # ------------------------------------------------------------------ #
    # Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def execute(self, fast: bool = False, dry_run: bool = False) -> None:
        """Run the WAN2 variable migration workflow.

        Args:
            fast: Enable parallel processing with connection pooling.
            dry_run: Preview changes without modifying anything.
        """
        self._dry_run = dry_run
        self._print_header()
        logging.warning("Menu #104 DESTRUCTIVE: Update Gateway Templates WAN2 Variable operation started")

        data = self._load_csv_data()
        if data is None:
            return
        template_rows, sites, site_counts = data

        selected = self._display_and_select_templates(template_rows, site_counts)
        if selected is None:
            return

        direction = self._select_operation_direction()
        if direction is None:
            return
        self._operation_mode, self._search_pattern, self._replacement_value = direction

        changes = self._analyze_templates_parallel(selected)
        if not changes:
            print(f"\n  No templates found with {self._search_pattern}" " port configurations.")
            print("  No changes needed.")
            logging.info("Menu #104: No templates require modification" f" (searched for {self._search_pattern})")
            return

        if not self._preview_and_confirm(changes):
            return

        results = self._apply_template_changes(changes)

        migrated_ids = {r["template_id"] for r in results if r["status"] == "SUCCESS"}
        devices = self._find_devices_needing_migration(sites, migrated_ids)
        device_results = self._run_device_migrations(devices, fast)
        self._generate_reports(results, device_results, devices)

    # ------------------------------------------------------------------ #
    # Header and data loading                                             #
    # ------------------------------------------------------------------ #

    def _print_header(self) -> None:
        """Display operation header with mode-specific warnings."""
        print("\n  DESTRUCTIVE: Update Gateway Templates" " for WAN2 Variable Migration")
        print("=" * 70)
        if self._dry_run:
            print("  >> DRY-RUN MODE: No changes will be made" " to templates or devices")
            print("  >> This will show what WOULD be changed" " without modifying anything")
        else:
            print("  !? WARNING: This operation modifies gateway templates")
            print("  !? All sites using affected templates" " will inherit the change")
            print("  !? Ensure sites have 'wan2_interface'" " variable set (Menu #103)")
        print("=" * 70)

    def _load_csv_data(
        self,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]] | None:
        """Load template and site CSV data, filter excluded sites.

        Returns:
            Tuple of (template_rows, filtered_sites, template_site_counts)
            or None if no templates found.
        """
        print("\n  Loading gateway template data...")
        self._check_csv("OrgGatewayTemplates.csv", self._gen_templates)
        self._check_csv("SiteList.csv", self._gen_sites)

        templates_path = self._get_csv_path("OrgGatewayTemplates.csv")
        with open(templates_path, encoding="utf-8") as csvfile:
            template_rows = list(csv.DictReader(csvfile))

        if not template_rows:
            print(" No gateway templates found.")
            logging.warning("No gateway templates available for modification")
            return None

        sites_path = self._get_csv_path("SiteList.csv")
        with open(sites_path, encoding="utf-8") as csvfile:
            all_sites = list(csv.DictReader(csvfile))

        sites = self._filter_excluded_sites(all_sites)
        site_counts = self._count_template_assignments(sites)
        return template_rows, sites, site_counts

    def _filter_excluded_sites(self, all_sites: list[dict[str, str]]) -> list[dict[str, str]]:
        """Remove sites matching the exclusion prefix."""
        if not self._site_exclude_prefix:
            return all_sites

        original_count = len(all_sites)
        filtered = [s for s in all_sites if not s.get("name", "").startswith(self._site_exclude_prefix)]
        excluded = original_count - len(filtered)
        if excluded > 0:
            print(
                f"\n  !? SECURITY: Excluded {excluded}"
                f" '{self._site_exclude_prefix}*' sites"
                " from template impact analysis (early filter)"
            )
            logging.info(
                f"Menu #104: Excluded {excluded} sites matching prefix"
                f" '{self._site_exclude_prefix}'"
                " from WAN2 template operation"
            )
        return filtered

    @staticmethod
    def _count_template_assignments(
        sites: list[dict[str, str]],
    ) -> dict[str, int]:
        """Count how many sites are assigned to each template."""
        logging.info(f"Processing {len(sites)} sites for template assignment counts")
        counts: dict[str, int] = {}
        for site in sites:
            tid = site.get("gatewaytemplate_id", "").strip()
            if tid:
                counts[tid] = counts.get(tid, 0) + 1
        return counts

    # ------------------------------------------------------------------ #
    # Template selection and direction                                    #
    # ------------------------------------------------------------------ #

    def _display_and_select_templates(
        self,
        template_rows: list[dict[str, str]],
        site_counts: dict[str, int],
    ) -> list[dict[str, Any]] | None:
        """Display templates with site counts and get user selection.

        Returns:
            List of selected template dicts or None if cancelled.
        """
        sorted_rows = sorted(
            template_rows,
            key=lambda t: t.get("name", "Unnamed Template").lower(),
        )

        print(f"\n  Available Gateway Templates ({len(sorted_rows)}):")
        template_list: list[dict[str, Any]] = []
        for idx, tmpl in enumerate(sorted_rows, start=1):
            tid = tmpl.get("id", "")
            name = tmpl.get("name", "Unnamed Template")
            count = site_counts.get(tid, 0)
            template_list.append({"id": tid, "name": name, "site_count": count})
            print(f"   [{idx}] {name} ({count} sites)")

        return self._prompt_template_selection(template_list)

    def _prompt_template_selection(self, template_list: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Prompt user for template selection."""
        print("\n  Template Selection:")
        print("   Enter template numbers to modify" " (comma-separated, e.g., 1,3,5)")
        print("   Or 'all' to modify all templates")
        print("   Or 'cancel' to abort")

        raw = self._input_fn("\n  Selection: ").strip().lower()

        if raw == "cancel":
            print(" Operation cancelled.")
            logging.info("Menu #104 cancelled by user at template selection")
            return None

        if raw == "all":
            selected = template_list
        else:
            try:
                indices = [int(i.strip()) - 1 for i in raw.split(",")]
                selected = [template_list[i] for i in indices if 0 <= i < len(template_list)]
            except (ValueError, IndexError) as exc:
                print(f" Invalid selection: {exc}")
                logging.error(f"Invalid template selection in Menu #104: {exc}")
                return None

        if not selected:
            print(" No templates selected.")
            return None

        total = sum(t["site_count"] for t in selected)
        print(f"\n  Selected {len(selected)} templates for modification:")
        for tmpl in selected:
            print(f"   - {tmpl['name']} ({tmpl['site_count']} sites)")
        print(f"\n  Total sites affected: {total}")
        return selected

    def _select_operation_direction(
        self,
    ) -> tuple[str, str, str] | None:
        """Prompt for apply or revert direction.

        Returns:
            Tuple of (operation_mode, search_pattern, replacement_value)
            or None if cancelled.
        """
        print("\n  Operation Direction:")
        print("   [1] Replace hardcoded ports with" " {{wan2_interface}} variable (standard migration)")
        print("   [2] Replace {{wan2_interface}} variable" " with hardcoded 'ge-0/0/1' (revert/undo)")
        print("   [cancel] Abort operation")

        choice = self._input_fn("\n  Select operation [1/2/cancel]: ").strip().lower()

        if choice == "cancel":
            print(" Operation cancelled.")
            logging.info("Menu #104 cancelled by user at operation direction selection")
            return None

        if choice == "2":
            print("\n  !? REVERT MODE: Will replace {{wan2_interface}}" " with hardcoded 'ge-0/0/1'")
            logging.info("Menu #104: User selected REVERT mode (variable -> hardcoded)")
            return ("revert", "{{wan2_interface}}", "ge-0/0/1")

        if choice == "1":
            print("\n  APPLY MODE: Will replace hardcoded 'ge-0/0/1'" " with {{wan2_interface}} variable")
            logging.info("Menu #104: User selected APPLY mode (hardcoded -> variable)")
            return ("apply", "ge-0/0/1", "{{wan2_interface}}")

        print(" Invalid selection. Operation cancelled.")
        logging.info("Menu #104 cancelled - invalid operation direction")
        return None

    # ------------------------------------------------------------------ #
    # Template analysis                                                   #
    # ------------------------------------------------------------------ #

    def _fetch_template_config(self, template_info: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch and analyze a single template for port changes.

        Args:
            template_info: Dict with id, name, site_count.

        Returns:
            Dict with change details or None if no changes needed.
        """
        import mistapi  # pylint: disable=import-outside-toplevel

        tid = template_info["id"]
        name = template_info["name"]

        try:
            logging.debug(f"Fetching template configuration for {name}")
            resp = mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(self._apisession, self._org_id, tid)
            config = resp.data if hasattr(resp, "data") else {}

            if not isinstance(config, dict):
                logging.warning(f"Template {name} returned invalid data structure")
                return None

            port_config = config.get("port_config", {})
            if not isinstance(port_config, dict):
                logging.debug(f"Template {name} has no port_config")
                return None

            ports_to_replace = self._find_matching_ports(port_config, name)
            if not ports_to_replace:
                return None

            return {
                "id": tid,
                "name": name,
                "site_count": template_info["site_count"],
                "config": config,
                "ports_to_replace": ports_to_replace,
            }

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logging.error(f"Error analyzing template {name}: {exc}")
            logging.error(traceback.format_exc())
            print(f"\n  !? Error analyzing template '{name}': {exc}")
            return None  # pylint: disable=useless-return

    def _find_matching_ports(
        self,
        port_config: dict[str, Any],
        template_name: str,
    ) -> list[tuple[str, str]]:
        """Find port keys matching the search pattern.

        Returns:
            List of (original_key, new_key) tuples.
        """
        replacements: list[tuple[str, str]] = []
        search = self._search_pattern
        replace = self._replacement_value

        for key in port_config:
            if key == search:
                replacements.append((key, replace))
            elif key.startswith(f"{search}."):
                suffix = key[len(search) :]
                new_key = f"{replace}{suffix}"
                replacements.append((key, new_key))
                logging.info(f"Found subinterface in template {template_name}:" f" {key} -> {new_key}")
            elif search in key:
                logging.warning(f"Found complex port pattern in template" f" {template_name}: {key}")
                print(f"\n  !? Template '{template_name}'" f" uses complex port pattern: '{key}'")
                print("     This requires manual review" " - cannot automatically replace")

        return replacements

    def _analyze_templates_parallel(self, templates_to_modify: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch and analyze templates in parallel.

        Returns:
            List of templates that have changes needed.
        """
        print(f"\n  Analyzing templates for {self._search_pattern}" " port configurations...")
        results: list[dict[str, Any]] = []

        max_workers = min(10, len(templates_to_modify))
        logging.info(
            f"Fetching {len(templates_to_modify)} template configurations" f" in parallel (max {max_workers} workers)"
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(self._fetch_template_config, t): t for t in templates_to_modify}
            for future in tqdm(
                concurrent.futures.as_completed(future_map),
                total=len(templates_to_modify),
                desc="Analyzing templates",
                unit="template",
            ):
                result = future.result()
                if result:
                    results.append(result)

        return results

    # ------------------------------------------------------------------ #
    # Confirmation and template modification                              #
    # ------------------------------------------------------------------ #

    def _preview_and_confirm(self, templates_with_changes: list[dict[str, Any]]) -> bool:
        """Show preview and get user confirmation.

        Returns:
            True if user confirmed (or dry-run mode), False otherwise.
        """
        count = len(templates_with_changes)
        total_sites = sum(t["site_count"] for t in templates_with_changes)

        print(f"\n  Preview of Changes" f" ({self._operation_mode.upper()} mode):")
        print(f"  {count} templates will be modified:")
        for tmpl in templates_with_changes:
            print(f"\n   Template: {tmpl['name']}")
            print(f"   Sites Affected: {tmpl['site_count']}")
            print("   Changes:")
            for old_key, new_key in tmpl["ports_to_replace"]:
                print(f"     Port key '{old_key}' -> '{new_key}'")

        print(f"\n  {'=' * 70}")
        if self._dry_run:
            print(f"  >> DRY-RUN: Would modify {count} templates")
            print(f"  >> affecting {total_sites} sites")
            print("  >> No confirmation needed in dry-run mode" " - proceeding with preview")
        else:
            print(f"  !? CRITICAL: This operation will modify" f" {count} templates")
            print(f"  !? affecting {total_sites} sites")
            print("  !? Type 'MIGRATE' (all caps) to proceed" " or anything else to cancel")
        print(f"  {'=' * 70}")

        if not self._dry_run:
            confirmation = self._input_fn("\n  Confirmation: ").strip()
            if confirmation != "MIGRATE":
                print(" Operation cancelled.")
                logging.info("Menu #104 cancelled by user at final confirmation")
                return False

        return True

    def _apply_template_changes(self, templates_with_changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply port_config changes to templates via API.

        Returns:
            List of result dicts with status information.
        """
        import mistapi  # pylint: disable=import-outside-toplevel

        print("\n  Applying template modifications...")
        results: list[dict[str, Any]] = []

        for tmpl in tqdm(
            templates_with_changes,
            desc="Updating templates",
            unit="template",
        ):
            result = self._apply_single_template(tmpl, mistapi)
            results.append(result)

        return results

    def _apply_single_template(
        self,
        tmpl: dict[str, Any],
        mistapi_mod: Any,
    ) -> dict[str, Any]:
        """Apply changes to a single template."""
        tid = tmpl["id"]
        name = tmpl["name"]
        config = tmpl["config"]

        result: dict[str, Any] = {
            "template_name": name,
            "template_id": tid,
            "site_count": tmpl["site_count"],
            "status": "",
            "changes_made": "",
            "error": "",
        }

        try:
            port_config = config.get("port_config", {})
            changes_list: list[str] = []

            for old_key, new_key in tmpl["ports_to_replace"]:
                if old_key in port_config:
                    port_config[new_key] = port_config.pop(old_key)
                    changes_list.append(f"'{old_key}' -> '{new_key}'")
                    logging.debug(f"Template {name}: Replaced {old_key}" f" with {new_key}")

            if not changes_list:
                result["status"] = "SKIPPED"
                result["error"] = "No matching ports found in configuration"
                return result

            config["port_config"] = port_config
            result["changes_made"] = "; ".join(changes_list)

            if self._dry_run:
                result["status"] = "DRY-RUN"
                logging.info(f"DRY-RUN: Would update template {name}" f" with changes: {result['changes_made']}")
            else:
                logging.debug(f"Updating template {name} via API")
                resp = mistapi_mod.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate(
                    self._apisession,
                    self._org_id,
                    tid,
                    body=config,
                )
                if resp.status_code == 200:
                    result["status"] = "SUCCESS"
                    logging.info(f"Successfully updated template {name}")
                else:
                    result["status"] = "FAILED"
                    result["error"] = f"API returned status {resp.status_code}"
                    logging.error(f"Failed to update template {name}:" f" status {resp.status_code}")

        except Exception as exc:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"
            result["error"] = str(exc)
            logging.error(f"Error updating template {name}: {exc}")
            logging.error(traceback.format_exc())

        return result

    # ------------------------------------------------------------------ #
    # Device override migration                                           #
    # ------------------------------------------------------------------ #

    def _find_devices_needing_migration(
        self,
        sites: list[dict[str, str]],
        migrated_template_ids: set[str],
    ) -> list[dict[str, Any]]:
        """Find devices with port overrides matching the search pattern.

        Args:
            sites: Filtered site list.
            migrated_template_ids: Template IDs successfully migrated.

        Returns:
            List of device dicts needing migration.
        """
        import mistapi  # pylint: disable=import-outside-toplevel

        print("\n  Step 7: Migrating device-level port overrides" f" ({self._operation_mode.upper()} mode)...")
        self._print_device_migration_header()

        affected, site_to_template = self._build_affected_site_set(sites, migrated_template_ids)

        logging.info(
            f"Device migration scope: {len(affected)} sites using"
            f" migrated templates (out of {len(sites)} total sites)"
        )
        print(f"  >> Optimization: Checking only {len(affected)}" f" affected sites (not all {len(sites)} sites)")

        if not affected:
            return []

        print("  >> Fetching gateway device configurations" f" for {len(affected)} affected sites...")
        return self._scan_site_devices(affected, site_to_template, mistapi)

    def _print_device_migration_header(self) -> None:
        """Print device migration mode header."""
        search = self._search_pattern
        replace = self._replacement_value
        if self._operation_mode == "apply":
            print("  !? CRITICAL: Preserving static IP" " configurations on devices")
            print(f"  !? Renaming device overrides from" f" '{search}' to '{replace}'")
        else:
            print("  !? REVERT: Updating device overrides" " to match template reversion")
            print(f"  !? Renaming device overrides from" f" '{search}' to '{replace}'")

    def _build_affected_site_set(
        self,
        sites: list[dict[str, str]],
        migrated_template_ids: set[str],
    ) -> tuple[set[str], dict[str, str]]:
        """Build set of site IDs using migrated templates.

        Returns:
            Tuple of (affected_site_ids, site_to_template_mapping).
        """
        site_to_template: dict[str, str] = {}
        affected: set[str] = set()

        for site in sites:
            sid = site.get("id", "").strip()
            name = site.get("name", "").strip()
            tid = site.get("gatewaytemplate_id", "").strip()

            if self._site_exclude_prefix and name.startswith(self._site_exclude_prefix):
                logging.debug(f"Skipping excluded site {name}" " from device migration scope")
                continue

            if sid and tid:
                site_to_template[sid] = tid
                if tid in migrated_template_ids:
                    affected.add(sid)

        return affected, site_to_template

    def _scan_site_devices(
        self,
        affected_site_ids: set[str],
        site_to_template: dict[str, str],
        mistapi_mod: Any,
    ) -> list[dict[str, Any]]:
        """Scan affected sites for devices with port overrides."""
        devices: list[dict[str, Any]] = []

        for sid in tqdm(
            affected_site_ids,
            desc="Checking site devices",
            unit="site",
        ):
            try:
                resp = mistapi_mod.api.v1.sites.devices.listSiteDevices(self._apisession, sid, type="gateway")
                site_devices = mistapi_mod.get_all(response=resp, mist_session=self._apisession)

                for device in site_devices:
                    match = self._check_device_override(device, sid, site_to_template, mistapi_mod)
                    if match:
                        devices.append(match)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logging.error(f"Error checking devices at site {sid}: {exc}")
                continue

        logging.info(f"Found {len(devices)} devices with" f" {self._search_pattern} overrides needing migration")
        return devices

    def _check_device_override(
        self,
        device: dict[str, Any],
        site_id: str,
        site_to_template: dict[str, str],
        mistapi_mod: Any,
    ) -> dict[str, Any] | None:
        """Check if a single device has port overrides matching pattern."""
        did = device.get("id", "").strip()
        name = device.get("name", "").strip()
        search = self._search_pattern

        resp = mistapi_mod.api.v1.sites.devices.getSiteDevice(self._apisession, site_id, did)
        config = getattr(resp, "data", {})

        port_config = config.get("port_config", {})
        if not isinstance(port_config, dict):
            return None

        has_override = any(k == search or k.startswith(f"{search}.") for k in port_config)

        if has_override:
            logging.info(f"Found device '{name}' with {search}" f" override at site {site_id}")
            return {
                "site_id": site_id,
                "device_id": did,
                "device_name": name,
                "template_id": site_to_template.get(site_id),
            }
        return None

    def _migrate_single_device_override(  # noqa: C901
        self,
        device_info: dict[str, Any],
        connection_semaphore: threading.Semaphore,
    ) -> dict[str, Any]:
        """Migrate port override keys on a single device.

        Args:
            device_info: Dict with site_id, device_id, device_name.
            connection_semaphore: Semaphore for connection pool limiting.

        Returns:
            Result dict with migration status.
        """
        import mistapi  # pylint: disable=import-outside-toplevel

        did = device_info["device_id"]
        name = device_info["device_name"]
        sid = device_info["site_id"]

        result: dict[str, Any] = {
            "device_name": name,
            "device_id": did,
            "site_id": sid,
            "template_id": device_info["template_id"],
            "status": "",
            "ports_migrated": "",
            "error": "",
        }

        try:
            with connection_semaphore:
                logging.debug(f"Fetching device config for {name} ({did})")
                resp = mistapi.api.v1.sites.devices.getSiteDevice(self._apisession, sid, did)
                config = getattr(resp, "data", {})

                if not isinstance(config, dict):
                    result["status"] = "SKIPPED"
                    result["error"] = "Invalid device config structure"
                    return result

                port_config = config.get("port_config", {})
                if not isinstance(port_config, dict):
                    result["status"] = "SKIPPED"
                    result["error"] = "No port_config found"
                    return result

                ports_renamed = self._rename_port_keys(
                    port_config,
                    self._search_pattern,
                    self._replacement_value,
                    name,
                )

                if not ports_renamed:
                    result["status"] = "SKIPPED"
                    result["error"] = f"No {self._search_pattern} ports found in config"
                    return result

                config["port_config"] = port_config
                result["ports_migrated"] = "; ".join(ports_renamed)

                if self._dry_run:
                    result["status"] = "DRY-RUN"
                    logging.info(
                        "DRY-RUN: Would migrate port overrides" f" for device {name}:" f" {result['ports_migrated']}"
                    )
                else:
                    logging.debug(f"Updating device {name} via API")
                    update_resp = mistapi.api.v1.sites.devices.updateSiteDevice(self._apisession, sid, did, body=config)
                    if update_resp.status_code == 200:
                        result["status"] = "SUCCESS"
                        logging.info("Successfully migrated port overrides" f" for device {name}")
                    else:
                        result["status"] = "FAILED"
                        result["error"] = f"API returned status" f" {update_resp.status_code}"
                        logging.error(f"Failed to update device {name}:" f" status {update_resp.status_code}")

        except Exception as exc:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"
            result["error"] = str(exc)
            logging.error(f"Error migrating device {name}: {exc}")
            logging.error(traceback.format_exc())

        return result

    @staticmethod
    def _rename_port_keys(
        port_config: dict[str, Any],
        search: str,
        replacement: str,
        device_name: str,
    ) -> list[str]:
        """Rename port_config keys matching the search pattern in-place.

        Returns:
            List of 'old->new' description strings for renamed keys.
        """
        renamed: list[str] = []
        for key in list(port_config.keys()):
            new_key: str | None = None
            if key == search:
                new_key = replacement
            elif key.startswith(f"{search}."):
                suffix = key[len(search) :]
                new_key = f"{replacement}{suffix}"

            if new_key:
                port_config[new_key] = port_config.pop(key)
                renamed.append(f"{key}->{new_key}")
                logging.debug(f"Device {device_name}: Renamed {key} to {new_key}")
        return renamed

    # ------------------------------------------------------------------ #
    # Device migration orchestration                                      #
    # ------------------------------------------------------------------ #

    def _run_device_migrations(
        self,
        devices_needing_migration: list[dict[str, Any]],
        fast: bool,
    ) -> list[dict[str, Any]]:
        """Orchestrate device override migrations.

        Returns:
            List of device migration result dicts.
        """
        if not devices_needing_migration:
            print("\n  No devices with ge-0/0/1 overrides found" " - no device migrations needed")
            logging.info("No device-level override migrations required")
            return []

        count = len(devices_needing_migration)
        print(f"\n  Found {count} devices with port overrides to migrate")
        print("  These devices will have port_config keys renamed" " from 'ge-0/0/1' to '{{wan2_interface}}'")
        print("  This preserves static IP configurations" " after template migration")

        use_fast = fast and count > 5 and self._pool_fn is not None

        if use_fast:
            results = self._migrate_devices_fast(devices_needing_migration)
        else:
            results = self._migrate_devices_sequential(devices_needing_migration, fast)

        self._save_data(results, "GatewayDevice_WAN2_Override_Migration.csv")

        success = sum(1 for r in results if r["status"] == "SUCCESS")
        failed = len(results) - success

        print("\n  Device Override Migration Complete!")
        print(f"  Devices Processed: {len(results)}")
        print(f"  Successfully Migrated: {success}")
        print(f"  Failed: {failed}")
        print("  Device migration report:" " GatewayDevice_WAN2_Override_Migration.csv")

        logging.info(f"Device override migration:" f" {success} successful, {failed} failed")
        return results

    def _migrate_devices_fast(self, devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Migrate devices using connection pool (fast mode)."""
        assert self._pool_fn is not None  # noqa: S101

        count = len(devices)
        print(f"\n  !? Fast mode enabled: Processing {count}" " devices with connection pooling")
        logging.info(f"Fast mode: Using connection pool" f" for {count} device migrations")

        results, failed = self._pool_fn(
            work_items=devices,
            worker_function=self._migrate_single_device_override,
            batch_description="devices",
        )

        if failed:
            logging.warning(f"Fast mode: {len(failed)} device migrations failed")
        return list(results)

    def _migrate_devices_sequential(
        self,
        devices: list[dict[str, Any]],
        fast: bool,
    ) -> list[dict[str, Any]]:
        """Migrate devices sequentially."""
        count = len(devices)
        if fast and count <= 5:
            print(f"\n  Sequential mode: Processing {count}" " devices (fast mode requires >5 devices)")
        else:
            print(f"\n  Sequential mode: Processing {count} devices")

        logging.info(f"Sequential mode: Processing {count}" " devices one at a time")
        results: list[dict[str, Any]] = []
        dummy_semaphore = threading.Semaphore(1)

        for device_info in tqdm(
            devices,
            desc="Migrating device overrides",
            unit="device",
        ):
            result = self._migrate_single_device_override(device_info, dummy_semaphore)
            results.append(result)

        return results

    # ------------------------------------------------------------------ #
    # Reporting and summary                                               #
    # ------------------------------------------------------------------ #

    def _generate_reports(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Generate audit reports and print final summary."""
        output_file = "GatewayTemplate_WAN2_Migration_Audit.csv"
        self._save_data(results, output_file)

        self._print_template_summary(results)
        self._print_device_summary(device_results, devices_needing_migration)
        self._print_report_paths(output_file, devices_needing_migration)
        self._print_final_guidance(results, device_results, devices_needing_migration)

    def _print_template_summary(self, results: list[dict[str, Any]]) -> None:
        """Print template migration summary."""
        if self._dry_run:
            dry_count = sum(1 for r in results if r["status"] == "DRY-RUN")
            print("\n  WAN2 Variable Migration DRY-RUN Complete!")
            print("=" * 70)
            print("  >> DRY-RUN MODE: No actual changes were made")
            print("  TEMPLATE MIGRATION PREVIEW:")
            print(f"    Templates Analyzed: {len(results)}")
            print(f"    Would Be Updated: {dry_count}")
            print(f"    Skipped: {len(results) - dry_count}")
        else:
            success = sum(1 for r in results if r["status"] == "SUCCESS")
            failed = len(results) - success
            print("\n  WAN2 Variable Migration Complete!")
            print("=" * 70)
            print("  TEMPLATE MIGRATION:")
            print(f"    Templates Processed: {len(results)}")
            print(f"    Successfully Updated: {success}")
            print(f"    Failed: {failed}")

    def _print_device_summary(
        self,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print device migration summary section."""
        if not devices_needing_migration:
            return

        if self._dry_run:
            dry_count = sum(1 for r in device_results if r["status"] == "DRY-RUN")
            print("\n  DEVICE OVERRIDE MIGRATION PREVIEW:")
            print(f"    Devices Analyzed: {len(device_results)}")
            print(f"    Would Preserve Static IPs: {dry_count}")
            print(f"    Skipped: {len(device_results) - dry_count}")
        else:
            success = sum(1 for r in device_results if r["status"] == "SUCCESS")
            failed = len(device_results) - success
            print("\n  DEVICE OVERRIDE MIGRATION:")
            print(f"    Devices Processed: {len(device_results)}")
            print(f"    Static IPs Preserved: {success}")
            print(f"    Failed: {failed}")

    @staticmethod
    def _print_report_paths(
        output_file: str,
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print report file locations."""
        print("\n  REPORTS:")
        print(f"    Template audit: {output_file}")
        if devices_needing_migration:
            print("    Device migration:" " GatewayDevice_WAN2_Override_Migration.csv")
        print("=" * 70)

    def _print_final_guidance(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print final guidance and warnings."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")
        failure_count = len(results) - success_count if not self._dry_run else 0

        if self._dry_run:
            self._print_dry_run_guidance(results, device_results, devices_needing_migration)
        else:
            self._print_live_guidance(success_count, device_results, devices_needing_migration)

        if failure_count > 0:
            print(f"\n  !? {failure_count} templates failed" " to update - check audit report")

        self._print_device_failure_warning(device_results, devices_needing_migration)
        self._log_operation_summary(success_count, failure_count, device_results, devices_needing_migration)

    def _print_device_failure_warning(
        self,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print warnings for failed device migrations."""
        if not devices_needing_migration:
            return
        dev_failed = len(device_results) - sum(1 for r in device_results if r["status"] == "SUCCESS")
        if dev_failed > 0:
            print(f"\n  !? WARNING: {dev_failed}" " devices failed override migration")
            print("  !? These devices may lose" " static IP configurations")
            print("  !? Check" " GatewayDevice_WAN2_Override_Migration.csv" " for details")

    def _log_operation_summary(
        self,
        success_count: int,
        failure_count: int,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Log operation summary for audit trail."""
        logging.warning(
            f"Menu #104 DESTRUCTIVE operation complete"
            f" ({self._operation_mode.upper()} mode):"
            f" {success_count} templates updated,"
            f" {failure_count} failed"
        )
        if devices_needing_migration:
            dev_ok = sum(1 for r in device_results if r["status"] == "SUCCESS")
            dev_fail = len(device_results) - dev_ok
            logging.warning(
                f"Device override migration"
                f" ({self._operation_mode.upper()} mode):"
                f" {dev_ok} successful, {dev_fail} failed"
            )

    def _print_dry_run_guidance(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print dry-run specific guidance."""
        dry_count = sum(1 for r in results if r["status"] == "DRY-RUN")
        if dry_count > 0:
            print(f"\n  >> DRY-RUN: {dry_count} templates" " WOULD use {{wan2_interface}} variable")
            if devices_needing_migration:
                dev_dry = sum(1 for r in device_results if r["status"] == "DRY-RUN")
                print(f"  >> DRY-RUN: {dev_dry} devices" " WOULD have static IP overrides preserved")
                print("  >> DRY-RUN: Port configs WOULD migrate" " from 'ge-0/0/1' to '{{wan2_interface}}'")
            print("\n  >> To apply these changes," " run without --dry-run flag")
            print("  >> Ensure all affected sites have" " 'wan2_interface' variable set (Menu #103)")

    @staticmethod
    def _print_live_guidance(
        success_count: int,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print live-mode specific guidance."""
        if success_count > 0:
            print(f"\n  !? {success_count} templates" " now use {{wan2_interface}} variable")
            if devices_needing_migration:
                dev_ok = sum(1 for r in device_results if r["status"] == "SUCCESS")
                print(f"  !? {dev_ok} devices had" " static IP overrides preserved")
                print("  !? Port configs migrated" " from 'ge-0/0/1' to '{{wan2_interface}}'")
            print("  !? Ensure all affected sites have" " 'wan2_interface' variable set (Menu #103)")
            print("  !? Sites without the variable" " may experience gateway connectivity issues")
