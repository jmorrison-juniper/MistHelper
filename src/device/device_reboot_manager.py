"""DeviceRebootManager -- gateway-template-driven device reboot orchestrator.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 41).
Manages device reboot operations with comprehensive safety checks and audit
logging. Supports reboot by gateway template list (bulk operations) via
``GatewayTemplateRebootList.CSV``. Logs results to
``GatewayTemplateRebootResults.CSV``. All operations require explicit user
confirmation and log results for auditing.

Direct imports cover stdlib only (importlib, csv, logging, os, datetime,
typing). Every live-global read (``FilePathUtils``, ``InputUtils``,
``CacheUtils``, ``OrgInventoryExporter``, ``OrgSiteExporter``,
``GatewayExportUtils``, ``mistapi``, ``apisession``) is resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside the methods that
consume them. Callers continue to reach the class through the
``MistHelper.DeviceRebootManager`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import csv  # WHY: CSV read/write for reboot lists, template mappings, and results export.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured audit trail for reboot lifecycle events.
import os  # WHY: existence check for the input reboot-list CSV.
from datetime import UTC, datetime  # WHY: ISO timestamp payload for restartSiteDevice call body.
from typing import Any  # WHY: response payloads and dict rows are heterogeneous.

from src.export.org_inventory_exporter import (
    OrgInventoryExporter,  # WHY: 1015 T-06 canonical import (eliminates mh.OrgInventoryExporter).
)


class DeviceRebootManager:  # Device reboot manager.
    """Manage device reboot operations with comprehensive safety checks and audit logging.

    Supports reboot operations by:
    - Gateway template list (bulk operations)
    - Site list
    - Individual device selection

    All operations require explicit user confirmation and log results for auditing.
    """

    @staticmethod
    def by_gateway_template_list() -> None:  # Reboot by template list.
        """Reboot all devices associated with gateway templates in GatewayTemplateRebootList.CSV.

        Logs results to GatewayTemplateRebootResults.CSV.
        """
        logging.info("[Menu 91] Starting DeviceRebootManager.by_gateway_template_list")  # Log start.

        # Step 1: Validate reboot list file exists
        reboot_targets = DeviceRebootManager._load_and_validate_reboot_targets()  # Load reboot targets.
        if not reboot_targets:  # No targets.
            return  # Abort.

        # Step 2: Display confirmation and get user consent
        if not DeviceRebootManager._confirm_reboot_operation(reboot_targets):  # Confirm the reboot.
            return  # Abort.

        # Step 3: Execute reboots and collect results
        results = DeviceRebootManager._execute_reboots(reboot_targets)  # Execute the reboots.

        # Step 4: Export results to CSV
        DeviceRebootManager._export_reboot_results(results)  # Export the results.

    @staticmethod
    def _load_and_validate_reboot_targets() -> list[dict] | None:  # type: ignore[type-arg]
        """Load reboot list and return validated device targets."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        reboot_list_path = mh.FilePathUtils.get_csv_path("GatewayTemplateRebootList.CSV")  # Reboot list path.
        if not os.path.exists(reboot_list_path):  # File missing.
            DeviceRebootManager._handle_missing_reboot_file(reboot_list_path)  # Handle the missing file.
            return None  # Abort.
        DeviceRebootManager._ensure_fresh_csv_cache()  # Refresh the CSV cache.
        template_name_to_id = DeviceRebootManager._load_template_mappings()  # Load template mappings.
        if not template_name_to_id:  # No mappings.
            return None  # Abort.
        reboot_template_names = DeviceRebootManager._load_reboot_template_names()  # Load reboot template names.
        if not reboot_template_names:  # No names.
            return None  # Abort.
        reboot_template_ids = DeviceRebootManager._map_template_names_to_ids(reboot_template_names, template_name_to_id)
        if not reboot_template_ids:  # No ids.
            return None  # Abort.
        return DeviceRebootManager._find_reboot_target_devices(reboot_template_ids, template_name_to_id)

    @staticmethod
    def _handle_missing_reboot_file(reboot_list_path: str) -> None:  # Handle the missing file.
        """Handle missing reboot list file - offer to create template."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils + FilePathUtils.
        logging.error(" GatewayTemplateRebootList.CSV not found.")  # Log the missing file.
        print(" GatewayTemplateRebootList.CSV not found.")  # Tell the user.
        print(f"   Please create this file at: {reboot_list_path}")  # Show the path.
        print("   This file should contain template names to reboot, one per line.")  # Explain the format.

        user_input = (  # Prompt to create it.
            mh.InputUtils.safe_input(
                "   Would you like to create an empty file? (y/n): ",
                context="gateway_reboot_create_template_file",
            )
            .strip()
            .lower()
        )
        if user_input in ["y", "yes"]:  # User said yes.
            try:
                template_path = mh.FilePathUtils.create_csv_template("GatewayTemplateRebootList.CSV")
                print(f"! Empty file created at: {template_path}")  # Tell the user.
                print("   Edit the file to add template names and run again.")  # Tell the user.
            except Exception as error:  # Creation failed.
                print(f"! Failed to create file: {error}")  # Tell the user.

    @staticmethod
    def _ensure_fresh_csv_cache() -> None:  # Refresh the CSV cache.
        """Ensure required CSV files are fresh."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils + exporters.
        mh.CacheUtils.check_and_generate_csv("OrgDevices.csv", OrgInventoryExporter.devices)  # Refresh devices CSV.
        mh.CacheUtils.check_and_generate_csv("SiteList.csv", mh.OrgSiteExporter.sites)  # Refresh sites CSV.
        mh.CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", mh.GatewayExportUtils.templates)
        mh.CacheUtils.check_and_generate_csv(  # Refresh gateway configs CSV.
            "AllSiteGatewayConfigs.csv",
            lambda: mh.GatewayExportUtils.device_configs(fast=True),
        )

    @staticmethod
    def _load_template_mappings() -> dict[str, str] | None:  # Load template name->id.
        """Load template name to ID mapping from OrgGatewayTemplates.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        try:
            gateway_templates_path = mh.FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")  # Templates path.
            template_name_to_id = DeviceRebootManager._read_template_name_id_csv(gateway_templates_path)  # Parse rows.
            logging.info("Loaded %s gateway templates", len(template_name_to_id))  # Log the count.
        except Exception as error:  # Load failed.
            logging.error("! Failed to load gateway templates: %s", error)  # Log the error.
            print(f"! Failed to load gateway templates: {error}")  # Tell the user.
            return None  # Abort.

        if not template_name_to_id:  # No templates.
            logging.warning(" No gateway templates found in OrgGatewayTemplates.csv")  # Warn none.
            print(" No gateway templates found in OrgGatewayTemplates.csv")  # Tell the user.
            return None  # Abort.

        return template_name_to_id  # Return the map.

    @staticmethod
    def _read_template_name_id_csv(csv_path: str) -> dict[str, str]:  # Read name/id rows into a map
        """Read a gateway-templates CSV into a {name: id} dict, skipping rows missing either field."""
        template_name_to_id: dict[str, str] = {}  # Name-to-id map.
        with open(csv_path, encoding="utf-8") as file:  # Open the CSV.
            reader = csv.DictReader(file)  # Parse rows.
            for row in reader:  # Walk rows.
                name = row.get("name", "").strip()  # Read the name.
                tid = row.get("id", "").strip()  # Read the id.
                if name and tid:  # Have both.
                    template_name_to_id[name] = tid  # Map name to id.
        return template_name_to_id  # The parsed name->id map

    @staticmethod
    def _load_reboot_template_names() -> set[str] | None:  # Load reboot template names.
        """Load template names from reboot list file."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        try:
            reboot_list_path = mh.FilePathUtils.get_csv_path("GatewayTemplateRebootList.CSV")  # Reboot list path.
            reboot_template_names = DeviceRebootManager._read_reboot_names_csv(reboot_list_path)  # Parse rows.
            logging.info("Loaded %s template names from reboot list", len(reboot_template_names))  # Log the count.
        except Exception as error:  # Load failed.
            logging.error("! Failed to load reboot template list: %s", error)  # Log the error.
            print(f"! Failed to load reboot template list: {error}")  # Tell the user.
            return None  # Abort.
        return reboot_template_names if reboot_template_names else None  # Return names or None.

    @staticmethod
    def _read_reboot_names_csv(csv_path: str) -> set[str]:  # Read first-column names into a set
        """Read a reboot-list CSV's first column into a set of names, skipping blank rows/values."""
        reboot_template_names: set[str] = set()  # Name set.
        with open(csv_path, encoding="utf-8") as file:  # Open the CSV.
            reader = csv.reader(file)  # Parse rows.
            for row in reader:  # Walk rows.
                if row and row[0].strip():  # Non-empty name.
                    reboot_template_names.add(row[0].strip())  # Collect it.
        return reboot_template_names  # The parsed name set

    @staticmethod
    def _map_template_names_to_ids(names: set[str], mapping: dict[str, str]) -> set[str] | None:  # Map names to ids.
        """Map template names to IDs, logging matches and mismatches."""
        reboot_template_ids = set()  # Id set.
        for name in names:  # Walk names.
            if name in mapping:  # Name found.
                reboot_template_ids.add(mapping[name])  # Collect the id.
                logging.info("! Found template '%s' with ID '%s'", name, mapping[name])  # Log the match.
            else:
                logging.warning("! Template '%s' not found in OrgGatewayTemplates.csv", name)  # Warn not found.
                print(f"! Template '{name}' not found in available templates")  # Tell the user.

        if not reboot_template_ids:  # No matches.
            logging.error(" No matching template IDs found for reboot")  # Log none.
            print(" No matching template IDs found for reboot")  # Tell the user.
            print("Available templates:")  # List available.
            for name, tid in mapping.items():  # Walk templates.
                print(f"  - {name} ({tid})")  # Print each.
            return None  # Abort.

        return reboot_template_ids  # Return the ids.

    @staticmethod
    def _build_gateway_reboot_target(row: dict, resolved: tuple) -> dict:  # type: ignore[type-arg]
        """Build one reboot-target dict from a CSV row + the (template_id, template_name, site_name) tuple."""
        template_id, template_name, site_name = resolved  # Unpack the resolved triple.
        return {
            "device_id": row.get("id", "").strip(),
            "device_name": row.get("name", "").strip(),
            "site_id": row.get("site_id", "").strip(),
            "site_name": site_name,
            "template_id": template_id,
            "template_name": template_name,
        }

    @staticmethod
    def _scan_csv_for_gateway_targets(  # type: ignore[type-arg]
        site_to_template: dict[str, tuple],
    ) -> list[dict] | None:
        """Scan AllSiteGatewayConfigs.csv and collect gateway-row targets whose site uses a tracked template."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        reboot_targets: list[dict] = []  # Collect reboot targets.
        try:
            gateway_configs_path = mh.FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv")  # Configs path.
            with open(gateway_configs_path, encoding="utf-8") as file:  # Open the CSV.
                for row in csv.DictReader(file):  # Walk rows.
                    device_site_id = row.get("site_id", "").strip()  # Read the site id.
                    if device_site_id not in site_to_template or row.get("type", "").strip() != "gateway":
                        continue  # Skip non-matching rows.
                    target = DeviceRebootManager._build_gateway_reboot_target(row, site_to_template[device_site_id])
                    reboot_targets.append(target)  # Collect the target.
                    logging.info("Found gateway '%s' at site '%s'", target["device_name"], target["site_name"])
        except Exception as error:  # Load failed.
            logging.error("! Failed to load gateway configs: %s", error)  # Log the error.
            print(f"! Failed to load gateway configs: {error}")  # Tell the user.
            return None  # Abort.
        return reboot_targets  # Return collected targets (possibly empty).

    @staticmethod
    def _find_reboot_target_devices(template_ids: set[str], mapping: dict[str, str]) -> list[dict] | None:  # type: ignore[type-arg]
        """Find gateway devices in sites using the target templates."""
        template_id_to_name = {tid: name for name, tid in mapping.items()}  # Invert the map.
        site_to_template = DeviceRebootManager._find_sites_using_templates(template_ids, template_id_to_name)
        if not site_to_template:  # No sites.
            logging.warning(" No sites found using the specified gateway templates")  # Warn none.
            print(" No sites found using the specified gateway templates")  # Tell the user.
            return None  # Abort.
        reboot_targets = DeviceRebootManager._scan_csv_for_gateway_targets(site_to_template)  # Collect targets.
        if reboot_targets is None:  # Hard error in CSV load.
            return None  # Propagate abort.
        if not reboot_targets:
            logging.warning(" No gateway devices found in sites using the specified templates")
            print(" No gateway devices found in sites using the specified templates")
            return None
        logging.info("Found %s gateway devices to reboot", len(reboot_targets))
        return reboot_targets

    @staticmethod
    def _find_sites_using_templates(template_ids: set[str], id_to_name: dict[str, str]) -> dict[str, tuple]:  # type: ignore[type-arg]
        """Find sites that use the target gateway templates."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        site_to_template = {}  # Map of site_id -> (template_id, template_name, site_name) for matching sites
        try:
            site_list_path = mh.FilePathUtils.get_csv_path("SiteList.csv")  # Resolve the cached site list CSV path
            with open(site_list_path, encoding="utf-8") as file:  # Open the site list for reading
                reader = csv.DictReader(file)  # Parse each site row into a dictionary
                for row in reader:  # Examine every site
                    gateway_template_id = row.get(
                        "gatewaytemplate_id", ""
                    ).strip()  # The gateway template assigned to this site
                    if gateway_template_id in template_ids:  # This site uses one of the target templates
                        site_id = row.get("id", "").strip()  # The site's unique ID
                        site_name = row.get("name", "").strip()  # The site's display name
                        template_name = id_to_name.get(gateway_template_id, "Unknown")  # Resolve the template's name
                        site_to_template[site_id] = (gateway_template_id, template_name, site_name)  # Record the match
                        logging.info("Found site '%s' using template '%s'", site_name, template_name)  # Log the match
        except Exception as error:  # Reading or parsing the site list failed
            logging.error("! Failed to load site list: %s", error)  # Log the failure detail
            print(f"! Failed to load site list: {error}")  # Inform the user
        return site_to_template  # Return the site-to-template mapping

    @staticmethod
    def _group_targets_by_template(targets: list[dict]) -> dict[str, list[dict[str, Any]]]:  # type: ignore[type-arg]
        """Group reboot targets by their template_name into one list per template."""
        devices_by_template: dict[str, list[dict[str, Any]]] = {}
        for target in targets:  # Walk targets.
            template_name = target["template_name"]  # Read template name.
            devices_by_template.setdefault(template_name, []).append(target)  # Group in place.
        return devices_by_template

    @staticmethod
    def _print_reboot_target_summary(targets: list[dict], devices_by_template: dict[str, list[dict[str, Any]]]) -> None:  # type: ignore[type-arg]
        """Print the per-template device list followed by the totals summary."""
        for template_name, devices in devices_by_template.items():  # Per template.
            print(f"\n  Template: {template_name}")
            print(f"   {len(devices)} devices affected:")
            for device in devices:  # Per device.
                print(f"      !? {device['device_name']} (ID: {device['device_id']}) at '{device['site_name']}'")
        DeviceRebootManager._display_reboot_warnings()  # Inject the critical warnings.
        print("\n  Summary:")
        print(f"   !? Total devices to reboot: {len(targets)}")
        print(f"   !? Templates involved: {len(devices_by_template)}")
        print(f"   !? Sites affected: {len(set(t['site_name'] for t in targets))}")

    @staticmethod
    def _prompt_reboot_confirmation(target_count: int) -> bool:
        """Read the REBOOT confirmation phrase and log the accept/cancel decision."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        print("\n  Type 'REBOOT' to confirm, or anything else to cancel:")
        print("   By typing 'REBOOT', you accept all risks and liability.")
        try:
            user_input = mh.InputUtils.safe_input(">>> ", context="gateway_reboot_confirmation").strip()
            if user_input != "REBOOT":
                print(" Reboot operation cancelled.")
                logging.info("Gateway reboot cancelled by user")
                return False
            print(" User confirmed reboot operation. Proceeding...")
            logging.info("LIABILITY WAIVER ACCEPTED: User confirmed reboot for %s devices", target_count)
            return True
        except (KeyboardInterrupt, EOFError):
            print("\n Reboot operation cancelled.")
            logging.info("Gateway reboot cancelled by user interrupt")
            return False

    @staticmethod
    def _confirm_reboot_operation(targets: list[dict]) -> bool:  # type: ignore[type-arg]
        """Display targets and get user confirmation for reboot."""
        print("\n" + "=" * 100)
        print(" DEVICE REBOOT CONFIRMATION REQUIRED ")
        print("=" * 100)
        print(f"\n  The following {len(targets)} gateway devices will be REBOOTED:")
        print("-" * 100)
        devices_by_template = DeviceRebootManager._group_targets_by_template(targets)  # Group.
        DeviceRebootManager._print_reboot_target_summary(targets, devices_by_template)  # Display.
        return DeviceRebootManager._prompt_reboot_confirmation(len(targets))  # Read decision.

    @staticmethod
    def _display_reboot_warnings() -> None:
        """Display critical reboot warnings."""
        warnings = [
            " CRITICAL WARNING - READ CAREFULLY:",
            "!? This action will REBOOT network gateway devices",
            "!? Network connectivity will be TEMPORARILY LOST during reboot",
            "!? Users may experience service interruptions",
            "!? Remote sites may become inaccessible during reboot",
            "!? The script owner bears NO LIABILITY for any consequences",
        ]
        print("\n" + "??" * 50)
        for warning in warnings:
            print(warning)
        print("??" * 50)

    @staticmethod
    def _reboot_one_device(device: dict) -> str:  # type: ignore[type-arg]
        """Send one restartSiteDevice call and return the status string (or 'ERROR: ...')."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        try:
            logging.info("Rebooting device '%s'", device["device_name"])  # Log before the call.
            print(f"! Rebooting {device['device_name']} at {device['site_name']}...")
            response = mh.mistapi.api.v1.sites.devices.restartSiteDevice(  # Send the reboot.
                mh.apisession,
                device["site_id"],
                device["device_id"],
                body={"timestamp": datetime.now(UTC).isoformat()},
            )
            status = DeviceRebootManager._parse_reboot_response(response)  # Parse the result.
            print("   Reboot command sent successfully")
            logging.info("! Reboot sent for '%s': %s", device["device_name"], status)  # Log after the call.
            return status  # Return the parsed status.
        except Exception as error:  # API failure.
            print(f"   Failed to send reboot: {error}")
            logging.error("! Failed to reboot '%s': %s", device["device_name"], error)
            return f"ERROR: {error}"  # Capture the error for the result row.

    @staticmethod
    def _build_reboot_result_row(device: dict, status: str) -> dict:  # type: ignore[type-arg]
        """Build a single reboot-result row (template/device/site identity plus status string)."""
        return {
            "Template ID": device["template_id"],
            "Template Name": device["template_name"],
            "Device ID": device["device_id"],
            "Device Name": device["device_name"],
            "Site ID": device["site_id"],
            "Site Name": device["site_name"],
            "Status": status,
        }

    @staticmethod
    def _execute_reboots(targets: list[dict]) -> list[dict]:  # type: ignore[type-arg]
        """Execute reboot commands for all target devices."""
        print("\n  Starting device reboot operations...")
        print("=" * 50)
        results: list[dict] = []
        for device in targets:  # Walk targets.
            status = DeviceRebootManager._reboot_one_device(device)  # Reboot + capture status.
            results.append(DeviceRebootManager._build_reboot_result_row(device, status))  # Record row.
        return results

    @staticmethod
    def _parse_reboot_response(response: Any) -> str:
        """Parse reboot API response into status string."""
        if hasattr(response, "data") and response.data:
            if isinstance(response.data, dict):
                return response.data.get("status", f"SUCCESS - {response.data}")  # type: ignore[no-any-return]
            return f"SUCCESS - {response.data}"
        elif hasattr(response, "status_code"):
            return f"SUCCESS - HTTP {response.status_code}"
        return f"SUCCESS - {str(response)}"

    @staticmethod
    def _export_reboot_results(results: list[dict]) -> None:  # type: ignore[type-arg]
        """Export reboot results to CSV."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        try:
            results_csv_path = mh.FilePathUtils.get_csv_path("GatewayTemplateRebootResults.CSV")
            with open(results_csv_path, "w", newline="", encoding="utf-8") as file:
                fieldnames = [
                    "Template ID",
                    "Template Name",
                    "Device ID",
                    "Device Name",
                    "Site ID",
                    "Site Name",
                    "Status",
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            print("\n  Operation completed!")
            print(f"   Reboot commands sent to {len(results)} devices")
            print("   Results logged to GatewayTemplateRebootResults.CSV")
            logging.info("! Reboot results exported (%s entries)", len(results))
        except Exception as error:
            logging.error("! Failed to write results to CSV: %s", error)
            print(f"! Failed to write results to CSV: {error}")
