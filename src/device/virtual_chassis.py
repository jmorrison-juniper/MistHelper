"""Virtual chassis to virtual MAC conversion operations.

Extracted from MistHelper.py (Issue #213). Provides functionality to convert
virtual chassis switches to virtual MAC addressing, check conversion status,
and perform bulk conversions via CSV site lists.

Menu operations: 92 (single convert), 93 (bulk by site list), 94 (status check).
"""

from __future__ import annotations

import csv
import logging
import os
from collections.abc import Callable
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SafeInputFn = Callable[..., str]
SelectSiteFn = Callable[[], str | None]
GetCsvPathFn = Callable[[str], str]
CreateCsvTemplateFn = Callable[[str], str]
CheckAndGenerateCsvFn = Callable[[str, Any], bool]  # CSV cache check returns a success bool
FlattenFieldsFn = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
EscapeMultilineFn = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
SaveDataFn = Callable[[list[dict[str, Any]], str], bool]  # Exporter returns a success bool, not None

# Converted prefix for virtual MAC
_CONVERTED_PREFIX = "020003"


class VirtualChassisManager:
    """Manage virtual chassis to virtual MAC conversion operations.

    All methods are static. External dependencies are injected as explicit
    function parameters so the module can be tested and run independently
    of MistHelper globals.
    """

    # ------------------------------------------------------------------
    # Public entry-points (menus 92, 93, 94)
    # ------------------------------------------------------------------

    @staticmethod
    def convert_single(
        *,
        apisession: Any,
        select_site_fn: SelectSiteFn,
        safe_input_fn: SafeInputFn,
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        inventory_generator: Any,
        dry_run: bool = False,
    ) -> None:
        """Interactively convert a single VC switch to virtual MAC (Menu 92).

        Args:
            apisession: Authenticated Mist API session.
            select_site_fn: Callback that prompts user and returns a site_id.
            safe_input_fn: Callback for safe user input with EOF handling.
            get_csv_path_fn: Resolves a filename to its full data-directory path.
            check_and_generate_csv_fn: Ensures a cached CSV exists.
            inventory_generator: Callable passed to check_and_generate_csv_fn.
            dry_run: If True, show what would happen without making API calls.
        """
        mode_label = "[DRY RUN] " if dry_run else ""
        print(f"\n  {mode_label}DESTRUCTIVE: Virtual Chassis to Virtual MAC Conversion")
        print("=" * 60)
        if dry_run:
            print("  DRY RUN MODE: No changes will be made. Showing what would happen.")

        site_id = select_site_fn()
        if not site_id:
            print(" No site selected.")
            return

        site_name = VirtualChassisManager._get_site_name(apisession, site_id)
        print(f"\n  Selected Site: {site_name} ({site_id})")

        switches = VirtualChassisManager._load_site_switches(
            site_id, get_csv_path_fn, check_and_generate_csv_fn, inventory_generator
        )
        if not switches:
            print(f"! No virtual chassis switches found at site '{site_name}'.")
            print(" Virtual chassis switches must have a device ID assigned.")
            logging.warning("No virtual chassis switches found at site %s.", site_id)
            return

        selected = VirtualChassisManager._prompt_switch_selection(switches, site_name, safe_input_fn)
        if not selected:
            return

        device_id = selected.get("id")
        if not device_id:
            print(" Missing device_id for selected switch.")
            logging.warning("Missing device_id for selected switch.")
            return

        if not VirtualChassisManager._preflight_check(selected, safe_input_fn):
            return

        if dry_run:
            VirtualChassisManager._print_dry_run(selected, site_name, device_id, site_id)
            return

        if not VirtualChassisManager._confirm_conversion(selected, site_name, device_id, safe_input_fn):
            print(" Operation cancelled.")
            return

        VirtualChassisManager._execute_conversion(apisession, site_id, device_id, selected.get("name", ""), site_name)

    @staticmethod
    def convert_by_site_list(
        *,
        apisession: Any,
        safe_input_fn: SafeInputFn,
        get_csv_path_fn: GetCsvPathFn,
        create_csv_template_fn: CreateCsvTemplateFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        inventory_generator: Any,
        sites_generator: Any,
    ) -> None:
        """Bulk convert VC switches from sites in VCConvert.CSV (Menu 93).

        Args:
            apisession: Authenticated Mist API session.
            safe_input_fn: Callback for safe user input with EOF handling.
            get_csv_path_fn: Resolves a filename to its full data-directory path.
            create_csv_template_fn: Creates an empty CSV template file.
            check_and_generate_csv_fn: Ensures a cached CSV exists.
            inventory_generator: Callable for OrgInventory generation.
            sites_generator: Callable for SiteList generation.
        """
        logging.info("Starting bulk VC to virtual MAC conversion by site list...")

        site_names = VirtualChassisManager._load_site_names_from_csv(
            get_csv_path_fn, create_csv_template_fn, safe_input_fn
        )
        if not site_names:
            return

        print(f"! Loaded {len(site_names)} site names from VCConvert.CSV:")
        for idx, name in enumerate(site_names):
            print(f"  [{idx + 1}] {name}")

        check_and_generate_csv_fn("OrgInventory.csv", inventory_generator)
        check_and_generate_csv_fn("SiteList.csv", sites_generator)

        site_name_to_id = VirtualChassisManager._load_site_name_mapping(get_csv_path_fn)
        if not site_name_to_id:
            return

        target_ids, missing = VirtualChassisManager._resolve_site_ids(site_names, site_name_to_id)

        if missing:
            print("! Warning: The following sites were not found in the organization:")
            for site in missing:
                print(f"   - {site}")

        if not target_ids:
            print(" No valid sites found. Exiting.")
            logging.error("No valid sites found for VC conversion.")
            return

        switches = VirtualChassisManager._load_switches_for_sites(target_ids, site_name_to_id, get_csv_path_fn)
        if not switches:
            print(" No virtual chassis switches found in the specified sites.")
            logging.warning("No virtual chassis switches found in target sites.")
            return

        VirtualChassisManager._display_switches_for_conversion(switches)

        confirm = safe_input_fn(
            "\nType 'CONVERT' to proceed with bulk conversion or anything else to cancel: ",
            context="vc_bulk_conversion",
        )
        if confirm != "CONVERT":
            print(" Conversion cancelled by user.")
            logging.info("Virtual chassis conversion cancelled by user.")
            return

        VirtualChassisManager._execute_bulk_conversion(apisession, switches)

    @staticmethod
    def check_status(
        *,
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        inventory_generator: Any,
        sites_generator: Any,
        flatten_fields_fn: FlattenFieldsFn,
        escape_multiline_fn: EscapeMultilineFn,
        save_data_fn: SaveDataFn,
    ) -> None:
        """Check conversion status of all VC switches in the org (Menu 94).

        Args:
            get_csv_path_fn: Resolves a filename to its full data-directory path.
            check_and_generate_csv_fn: Ensures a cached CSV exists.
            inventory_generator: Callable for OrgInventory generation.
            sites_generator: Callable for SiteList generation.
            flatten_fields_fn: Flattens nested dict fields.
            escape_multiline_fn: Escapes multiline strings for CSV.
            save_data_fn: Writes data list to output file.
        """
        print("\n  Virtual Chassis to Virtual MAC Conversion Status Check")
        print("=" * 70)
        print(" Checking all switches for virtual chassis conversion status...")
        print(f" Converted switches have vc_mac starting with '{_CONVERTED_PREFIX}'")

        logging.info("Starting virtual chassis conversion status check...")

        check_and_generate_csv_fn("OrgInventory.csv", inventory_generator)

        vc_switches = VirtualChassisManager._load_vc_switches(get_csv_path_fn)
        if not vc_switches:
            print(" No switches with vc_mac found in the organization.")
            print(" Only virtual chassis switches have vc_mac assigned.")
            logging.warning("No switches with vc_mac found.")
            return

        site_id_to_name = VirtualChassisManager._load_site_id_mapping(
            get_csv_path_fn, check_and_generate_csv_fn, sites_generator
        )
        converted, not_converted = VirtualChassisManager._analyze_conversion_status(vc_switches, site_id_to_name)

        VirtualChassisManager._display_status_summary(converted, not_converted)
        VirtualChassisManager._export_status_results(
            converted + not_converted,
            flatten_fields_fn,
            escape_multiline_fn,
            save_data_fn,
            get_csv_path_fn,
        )

        print("\n  Usage Notes:")
        print("   !? Use option 92 to convert individual switches")
        print("   !? Use option 93 for bulk conversion by site list")
        print(f"   !? Virtual chassis switches without '{_CONVERTED_PREFIX}' " "vc_mac prefix can be converted")

    # ------------------------------------------------------------------
    # API helpers (require apisession)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_site_name(apisession: Any, site_id: str) -> str:
        """Fetch site name from API."""
        import mistapi

        try:
            response = mistapi.api.v1.sites.getSite(apisession, site_id)
            if response.data:
                return str(response.data.get("name", site_id))
        except Exception as exc:
            logging.warning("Could not fetch site name for %s: %s", site_id, exc)
        return "Unknown Site"

    @staticmethod
    def _execute_conversion(
        apisession: Any,
        site_id: str,
        device_id: str,
        switch_name: str,
        site_name: str,
    ) -> None:
        """Execute API call to convert one switch to virtual MAC."""
        import mistapi

        print(
            f"! Converting switch '{switch_name}' (device_id: {device_id}) " f"at site '{site_name}' to virtual MAC..."
        )
        try:
            response = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(
                apisession, site_id, device_id
            )
            VirtualChassisManager._handle_conversion_response(response, device_id, site_id, site_name, switch_name)
        except Exception as exc:
            print(f"! Failed to convert to virtual MAC: {exc}")
            logging.error("Failed to convert to virtual MAC: %s", exc)

    @staticmethod
    def _handle_conversion_response(
        response: Any,
        device_id: str,
        site_id: str,
        site_name: str,
        switch_name: str,
    ) -> None:
        """Process API response from a conversion call."""
        if hasattr(response, "status_code") and response.status_code >= 400:
            data = getattr(response, "data", "")
            print(f"! Conversion failed (HTTP {response.status_code}): {data}")
            logging.error(
                "Conversion failed for %s at %s. HTTP %s",
                switch_name,
                site_name,
                response.status_code,
            )
            return

        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict) and "detail" in resp_data:
            print(f"! Conversion failed: {resp_data['detail']}")
            logging.error(
                "Conversion failed for %s at %s. Detail: %s",
                switch_name,
                site_name,
                resp_data["detail"],
            )
            return

        print(" Conversion to virtual MAC triggered successfully!")
        print(" Check the device status in the Mist UI to monitor progress.")
        print("\n  Rollback Guidance:")
        print("   If the conversion causes issues, contact Juniper TAC.")
        print("   The device may need a factory reset and re-adoption to revert.")
        print("   Use Menu 94 to verify conversion status after the device reboots.")
        logging.info(
            "Conversion triggered for device %s at site %s. Response: %s",
            device_id,
            site_id,
            getattr(response, "data", ""),
        )

    @staticmethod
    def _execute_bulk_conversion(apisession: Any, switches: list[dict[str, Any]]) -> None:
        """Execute conversion for multiple switches."""
        import mistapi

        print(f"\n  Starting conversion of {len(switches)} switches...")
        successful = 0
        failed = 0

        for idx, switch in enumerate(switches):
            site_id = switch.get("site_id", "")
            device_id = switch.get("id", "")
            switch_name = switch.get("name", "")
            site_name = switch.get("site_name", "")

            print(f"\n[{idx + 1}/{len(switches)}] " f"Converting '{switch_name}' at site '{site_name}'...")

            try:
                response = mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac(
                    apisession, site_id, device_id
                )
                if VirtualChassisManager._is_conversion_error(response):
                    failed += 1
                else:
                    print("! Conversion triggered successfully.")
                    logging.info("Conversion triggered for %s at %s.", switch_name, site_name)
                    successful += 1
            except Exception as exc:
                print(f"! Exception during conversion: {exc}")
                logging.error(
                    "Exception during conversion of %s at %s: %s",
                    switch_name,
                    site_name,
                    exc,
                )
                failed += 1

        VirtualChassisManager._print_bulk_summary(successful, failed, len(switches))

    # ------------------------------------------------------------------
    # CSV / file helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_site_switches(
        site_id: str,
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        inventory_generator: Any,
    ) -> list[dict[str, Any]]:
        """Load switches at a specific site from cached inventory."""
        check_and_generate_csv_fn("OrgInventory.csv", inventory_generator)
        path = get_csv_path_fn("OrgInventory.csv")

        with open(path, encoding="utf-8") as csvfile:
            reader = list(csv.DictReader(csvfile))
            return [
                row
                for row in reader
                if (row.get("type") == "switch" and row.get("id", "").strip() and row.get("site_id") == site_id)
            ]

    @staticmethod
    def _load_site_names_from_csv(
        get_csv_path_fn: GetCsvPathFn,
        create_csv_template_fn: CreateCsvTemplateFn,
        safe_input_fn: SafeInputFn,
    ) -> list[str]:
        """Load site names from VCConvert.CSV file."""
        csv_path = get_csv_path_fn("VCConvert.CSV")
        if not os.path.exists(csv_path):
            VirtualChassisManager._handle_missing_csv(csv_path, create_csv_template_fn, safe_input_fn)
            return []

        try:
            site_names: list[str] = []
            with open(csv_path, encoding="utf-8") as csvfile:
                for row in csv.reader(csvfile):
                    if row and row[0].strip():
                        site_names.append(row[0].strip())
            return site_names
        except Exception as exc:
            print(f"! Error reading VCConvert.CSV: {exc}")
            logging.error("Error reading VCConvert.CSV: %s", exc)
            return []

    @staticmethod
    def _handle_missing_csv(
        csv_path: str,
        create_csv_template_fn: CreateCsvTemplateFn,
        safe_input_fn: SafeInputFn,
    ) -> None:
        """Prompt user when VCConvert.CSV is not found."""
        print("! File 'VCConvert.CSV' not found.")
        print(f"   Please create this file at: {csv_path}")
        print("   This file should contain site names (one per line, no header).")

        answer = (
            safe_input_fn(
                "   Would you like to create an empty file to get started? (y/n): ",
                context="vc_csv_create",
            )
            .strip()
            .lower()
        )

        if answer in ("y", "yes"):
            try:
                path = create_csv_template_fn("VCConvert.CSV")
                print(f"! Empty file created at: {path}")
                print("   Please edit the file to add your site names " "and run the script again.")
            except Exception as exc:
                print(f"! Failed to create file: {exc}")

        logging.error("VCConvert.CSV file not found.")

    @staticmethod
    def _load_site_name_mapping(
        get_csv_path_fn: GetCsvPathFn,
    ) -> dict[str, str]:
        """Load site name-to-ID mapping from cached SiteList.csv."""
        try:
            path = get_csv_path_fn("SiteList.csv")
            with open(path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                return {row.get("name", ""): row.get("id", "") for row in reader}
        except Exception as exc:
            print(f"! Error reading SiteList.csv: {exc}")
            logging.error("Error reading SiteList.csv: %s", exc)
            return {}

    @staticmethod
    def _load_switches_for_sites(
        target_site_ids: list[str],
        site_name_to_id: dict[str, str],
        get_csv_path_fn: GetCsvPathFn,
    ) -> list[dict[str, Any]]:
        """Load switches from inventory for specific sites."""
        try:
            path = get_csv_path_fn("OrgInventory.csv")
            switches: list[dict[str, Any]] = []
            with open(path, encoding="utf-8") as csvfile:
                for row in csv.DictReader(csvfile):
                    if not VirtualChassisManager._is_target_switch(row, target_site_ids):
                        continue
                    site_name = VirtualChassisManager._reverse_lookup(row.get("site_id", ""), site_name_to_id)
                    row["site_name"] = site_name
                    switches.append(row)
            return switches
        except Exception as exc:
            print(f"! Error reading OrgInventory.csv: {exc}")
            logging.error("Error reading OrgInventory.csv: %s", exc)
            return []

    @staticmethod
    def _load_vc_switches(
        get_csv_path_fn: GetCsvPathFn,
    ) -> list[dict[str, Any]]:
        """Load all switches with vc_mac from inventory."""
        try:
            path = get_csv_path_fn("OrgInventory.csv")
            switches: list[dict[str, Any]] = []
            with open(path, encoding="utf-8") as csvfile:
                for row in csv.DictReader(csvfile):
                    if row.get("type") == "switch" and row.get("vc_mac", "").strip():
                        switches.append(row)
            return switches
        except Exception as exc:
            print(f"! Error reading OrgInventory.csv: {exc}")
            logging.error("Error reading OrgInventory.csv: %s", exc)
            return []

    @staticmethod
    def _load_site_id_mapping(
        get_csv_path_fn: GetCsvPathFn,
        check_and_generate_csv_fn: CheckAndGenerateCsvFn,
        sites_generator: Any,
    ) -> dict[str, str]:
        """Load site ID-to-name mapping from cached CSV."""
        try:
            check_and_generate_csv_fn("SiteList.csv", sites_generator)
            path = get_csv_path_fn("SiteList.csv")
            with open(path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                return {row.get("id", ""): row.get("name", "Unknown Site") for row in reader}
        except Exception as exc:
            logging.warning("Could not load site names: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # User-interaction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prompt_switch_selection(
        switches: list[dict[str, Any]],
        site_name: str,
        safe_input_fn: SafeInputFn,
    ) -> dict[str, Any] | None:
        """Display switches and prompt user for selection."""
        print(f"\n  Available Virtual Chassis Switches at '{site_name}':")
        print("-" * 80)

        index_map: dict[int, dict[str, Any]] = {}
        name_map: dict[str, dict[str, Any]] = {}
        for idx, switch in enumerate(switches):
            print(
                f"[{idx}] {switch.get('name', ''):20} "
                f"MAC: {switch.get('mac', ''):17} "
                f"Model: {switch.get('model', ''):10} "
                f"Serial: {switch.get('serial', ''):15} "
                f"ID: {switch.get('id', '')}"
            )
            index_map[idx] = switch
            name_map[switch.get("name", "")] = switch

        user_input = safe_input_fn(
            f"\nEnter the index or switch name to convert " f"to virtual MAC [0-{len(switches) - 1}]: ",
            context="vc_switch_selection",
        ).strip()

        if user_input.isdigit():
            return index_map.get(int(user_input))
        return name_map.get(user_input)

    @staticmethod
    def _preflight_check(switch: dict[str, Any], safe_input_fn: SafeInputFn) -> bool:
        """Validate switch is eligible for VC-to-virtual-MAC conversion."""
        device_type = switch.get("type", "")
        if device_type != "switch":
            print(f"! Preflight FAILED: Device type is '{device_type}', " "expected 'switch'.")
            logging.error("Preflight: wrong device type '%s' for VC conversion", device_type)
            return False

        device_id = switch.get("id", "").strip()
        if not device_id:
            print("! Preflight FAILED: Device has no assigned device ID.")
            logging.error("Preflight: missing device_id for VC conversion")
            return False

        vc_mac = switch.get("vc_mac", "").strip()
        if vc_mac and vc_mac.startswith(_CONVERTED_PREFIX):
            print(f"! Preflight WARNING: Switch '{switch.get('name', '')}' " "appears already converted.")
            print(f"   vc_mac '{vc_mac}' starts with '{_CONVERTED_PREFIX}' " "(virtual MAC prefix).")
            proceed = (
                safe_input_fn(
                    "   Continue anyway? (y/n): ",
                    context="vc_preflight_already_converted",
                )
                .strip()
                .lower()
            )
            if proceed not in ("y", "yes"):
                return False

        logging.info(
            "Preflight passed for switch '%s' (id=%s)",
            switch.get("name", ""),
            device_id,
        )
        return True

    @staticmethod
    def _confirm_conversion(
        switch: dict[str, Any],
        site_name: str,
        device_id: str,
        safe_input_fn: SafeInputFn,
    ) -> bool:
        """Display warning and get confirmation for destructive operation."""
        print("\n   DESTRUCTIVE OPERATION WARNING ")
        print(f"You are about to convert switch " f"'{switch.get('name', '')}' to virtual MAC.")
        print(f"Site: {site_name}")
        print(f"Device ID: {device_id}")
        print(f"MAC: {switch.get('mac', '')}")
        print("This operation cannot be undone!")

        confirm = safe_input_fn(
            "\nType 'CONVERT' to proceed or anything else to cancel: ",
            "",
            True,
            "virtual MAC conversion confirmation",
        )
        return confirm == "CONVERT"

    # ------------------------------------------------------------------
    # Pure logic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_site_ids(site_names: list[str], site_name_to_id: dict[str, str]) -> tuple[list[str], list[str]]:
        """Resolve site names to IDs, returning valid IDs and missing names."""
        target_ids: list[str] = []
        missing: list[str] = []
        for name in site_names:
            site_id = site_name_to_id.get(name)
            if site_id:
                target_ids.append(site_id)
            else:
                missing.append(name)
        return target_ids, missing

    @staticmethod
    def _analyze_conversion_status(
        switches: list[dict[str, Any]], site_id_to_name: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Classify switches as converted or not based on vc_mac prefix."""
        converted: list[dict[str, Any]] = []
        not_converted: list[dict[str, Any]] = []

        for switch in switches:
            vc_mac = switch.get("vc_mac", "")
            site_id = switch.get("site_id", "")
            enhanced = switch.copy()
            enhanced["site_name"] = site_id_to_name.get(site_id, "Unknown Site")

            if vc_mac.startswith(_CONVERTED_PREFIX):
                enhanced["conversion_status"] = "CONVERTED"
                enhanced["conversion_notes"] = f"vc_mac starts with {_CONVERTED_PREFIX} - converted to virtual MAC"
                converted.append(enhanced)
            else:
                enhanced["conversion_status"] = "NOT_CONVERTED"
                enhanced["conversion_notes"] = f"vc_mac starts with {vc_mac[:6]} - not converted to virtual MAC"
                not_converted.append(enhanced)

        return converted, not_converted

    @staticmethod
    def _is_target_switch(row: dict[str, Any], target_site_ids: list[str]) -> bool:
        """Check if an inventory row is a switch in one of the target sites."""
        return (
            row.get("type") == "switch"
            and row.get("site_id", "") in target_site_ids
            and bool(row.get("id", "").strip())
        )

    @staticmethod
    def _reverse_lookup(site_id: str, name_to_id: dict[str, str]) -> str:
        """Find the site name for a given site_id from a name->id map."""
        return next(
            (name for name, sid in name_to_id.items() if sid == site_id),
            "Unknown Site",
        )

    @staticmethod
    def _is_conversion_error(response: Any) -> bool:
        """Return True if the response indicates a conversion failure."""
        if hasattr(response, "status_code") and response.status_code >= 400:
            data = getattr(response, "data", "")
            print(f"! Conversion failed (HTTP {response.status_code}): {data}")
            logging.error("Conversion failed. HTTP %s", response.status_code)
            return True

        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict) and "detail" in resp_data:
            print(f"! Conversion failed: {resp_data['detail']}")
            logging.error("Conversion failed. Detail: %s", resp_data["detail"])
            return True

        return False

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_dry_run(selected: dict[str, Any], site_name: str, device_id: str, site_id: str) -> None:
        """Print dry-run output for a single conversion."""
        print(f"\n  [DRY RUN] Would convert switch " f"'{selected.get('name', '')}' at site '{site_name}'")
        print(f"  [DRY RUN] Device ID: {device_id}")
        print(f"  [DRY RUN] MAC: {selected.get('mac', '')}")
        print("  [DRY RUN] No API call made. Use without --dry-run to execute.")
        logging.info("DRY RUN: Would convert %s at site %s", device_id, site_id)

    @staticmethod
    def _display_switches_for_conversion(
        switches: list[dict[str, Any]],
    ) -> None:
        """Display switches that will be converted."""
        print(f"\n  Found {len(switches)} virtual chassis switches to convert:")
        print("=" * 100)
        for idx, switch in enumerate(switches):
            print(
                f"[{idx + 1:2}] "
                f"Site: {switch.get('site_name', ''):25} | "
                f"Name: {switch.get('name', ''):20} | "
                f"MAC: {switch.get('mac', ''):17} | "
                f"Model: {switch.get('model', ''):12} | "
                f"Serial: {switch.get('serial', '')}"
            )
        print(f"\n  This will convert {len(switches)} " "virtual chassis switches to virtual MAC.")
        print(" This operation cannot be undone easily.")

    @staticmethod
    def _display_status_summary(
        converted: list[dict[str, Any]],
        not_converted: list[dict[str, Any]],
    ) -> None:
        """Display conversion status summary."""
        total = len(converted) + len(not_converted)
        print("\n  Virtual Chassis Conversion Status Summary:")
        print(f"   Total virtual chassis switches: {total}")
        print(f"   Converted to virtual MAC: {len(converted)}")
        print(f"   Not converted: {len(not_converted)}")

        VirtualChassisManager._print_status_list(converted, "Converted", f"vc_mac starts with '{_CONVERTED_PREFIX}'")
        VirtualChassisManager._print_status_list(
            not_converted,
            "Not Converted",
            f"vc_mac does NOT start with '{_CONVERTED_PREFIX}'",
        )

    @staticmethod
    def _print_status_list(switches: list[dict[str, Any]], label: str, description: str) -> None:
        """Print up to 10 switches from a status list."""
        if not switches:
            return
        print(f"\n {label} Switches ({description}):")
        for switch in switches[:10]:
            vc_mac_display = switch.get("vc_mac", "")[:8]
            print(
                f"   !? {switch.get('name', 'Unnamed'):20} | "
                f"Site: {switch.get('site_name', ''):25} | "
                f"vc_mac: {vc_mac_display}..."
            )
        if len(switches) > 10:
            print(f"   ... and {len(switches) - 10} more")

    @staticmethod
    def _print_bulk_summary(successful: int, failed: int, total: int) -> None:
        """Print summary after bulk conversion."""
        print("\n  Conversion Summary:")
        print(f"   Successful conversions: {successful}")
        print(f"   Failed conversions: {failed}")
        print(f"   Total switches processed: {total}")

        if successful > 0:
            print("\n  Note: Successful conversions may take " "a few minutes to complete.")
            print("   Monitor the devices in the Mist portal " "to confirm the conversion status.")

        logging.info(
            "Bulk VC conversion completed: %d successful, %d failed",
            successful,
            failed,
        )

    @staticmethod
    def _export_status_results(
        all_switches: list[dict[str, Any]],
        flatten_fields_fn: FlattenFieldsFn,
        escape_multiline_fn: EscapeMultilineFn,
        save_data_fn: SaveDataFn,
        get_csv_path_fn: GetCsvPathFn,
    ) -> None:
        """Export conversion status results to CSV."""
        try:
            flattened = flatten_fields_fn(all_switches)
            sanitized = escape_multiline_fn(flattened)

            filename = "VirtualChassisConversionStatus.csv"
            save_data_fn(sanitized, filename)

            print(f"\n  Results exported to: {filename}")
            print(f"   Location: {get_csv_path_fn(filename)}")
            logging.info("Virtual chassis conversion status exported to %s", filename)
        except Exception as exc:
            print(f"! Error exporting results: {exc}")
            logging.error("Error exporting conversion status results: %s", exc)
