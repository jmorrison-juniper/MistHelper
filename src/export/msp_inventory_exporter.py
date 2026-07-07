"""MSPInventoryExporter -- MSP-wide device inventory exporter.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 8).
Exports device inventory across all MSPs and their organizations into a
consolidated CSV. Requires MSP privileges (obtained via --login interactive
authentication).
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live session + helper classes without circular load.
import logging  # WHY: emit structured trace for MSP + org iteration.
import os  # WHY: build cross-platform output path for CSV artifact.
from typing import Any  # WHY: duck-typed device dicts + Mist API responses.

from src.dataclasses.msp_org_context import MspOrgContext  # Bundled MSP/org identity (issue #470).
from src.refactors.initialize_mist_session_interactive import (
    MistSessionInteractiveInitializer,  # Extracted interactive login initializer (SC-023).
)


class MSPInventoryExporter:
    """MSP-Wide Device Inventory Export.

    Exports device inventory across all MSPs and all organizations into a consolidated CSV.
    Requires MSP privileges (obtained via --login interactive authentication).

    Output Fields:
    - MSP context: msp_id, msp_name
    - Org context: org_id, org_name
    - Site context: site_id, site_name
    - Device fields: type, model, mac, serial, name, version, status, etc.

    Output File: data/MSP_Inventory_Export.csv
    """

    def __init__(self) -> None:
        """Initialize the MSP inventory exporter."""
        self.all_devices: list = []  # type: ignore[type-arg]
        self.msp_count: int = 0
        self.org_count: int = 0
        self.device_count: int = 0
        self.errors: list = []  # type: ignore[type-arg]

    @staticmethod
    def execute() -> None:
        """Main entry point - exports MSP-wide inventory to CSV."""
        exporter = MSPInventoryExporter()
        exporter._run()

    def _run(self) -> None:
        """Execute the MSP inventory export workflow."""
        logging.info("Menu #144: Starting MSP-wide device inventory export")
        self._print_header()

        if not self._ensure_msp_privileges():
            return

        self._process_all_msps()
        self._finalize_export()
        logging.info(
            "Menu #144 complete: %s devices exported from %s orgs across %s MSPs",
            self.device_count,
            self.org_count,
            self.msp_count,
        )

    def _print_header(self) -> None:
        """Print export header banner."""
        print("")
        print("=" * 70)
        print("  MSP-WIDE DEVICE INVENTORY EXPORT")
        print("=" * 70)
        print("")

    def _ensure_msp_privileges(self) -> bool:
        """Ensure MSP privileges are available, offering login if needed."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live msp_privileges module global.

        if mh.msp_privileges:
            print(f"  + MSP privileges detected: {len(mh.msp_privileges)} MSP(s) available")
            print("")
            return True

        return self._attempt_interactive_login()

    def _attempt_interactive_login(self) -> bool:
        """Offer interactive login to obtain MSP privileges."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils helper.

        self._print_login_prompt()

        try:
            proceed = (
                mh.InputUtils.safe_input("  Switch to interactive login? (Y/n): ", context="msp_inventory")
                .strip()
                .lower()
            )
        except SystemExit:
            return False

        if proceed not in ("", "y", "yes"):
            print("  Cancelled.")
            logging.info("MSP inventory export cancelled by user")
            return False

        return self._execute_login_and_validate()

    def _print_login_prompt(self) -> None:
        """Print the login prompt message."""
        print("  MSP privileges not currently available.")
        print("")
        print("  This feature requires MSP-level access. Would you like to")
        print("  switch to interactive login (email/password) now?")
        print("")

    def _execute_login_and_validate(self) -> bool:
        """Execute login and validate MSP privileges obtained."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of detect_msp_privileges + msp_privileges global.

        if not MistSessionInteractiveInitializer.initialize():
            print("")
            print("  X Login failed.")
            return False

        mh.detect_msp_privileges()  # Populates mh.msp_privileges module global.

        if not mh.msp_privileges:
            print("")
            print("  X No MSP privileges after login.")
            print("    Your account may not have MSP-level access.")
            logging.warning("MSP inventory export: no MSP privileges after interactive login")
            return False

        self._print_continuation_header()
        return True

    def _print_continuation_header(self) -> None:
        """Print continuation header after successful login."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of msp_privileges module global.
        print("")
        print("=" * 70)
        print("  MSP-WIDE DEVICE INVENTORY EXPORT (Continuing)")
        print("=" * 70)
        print("")
        print(f"  + MSP privileges detected: {len(mh.msp_privileges)} MSP(s) available")
        print("")

    def _process_all_msps(self) -> None:
        """Process all MSPs to collect device inventory."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of msp_privileges module global.
        for msp_info in mh.msp_privileges:
            self._process_msp(msp_info)

    def _finalize_export(self) -> None:
        """Finalize export by writing results or reporting no data."""
        if self.all_devices:
            self._write_results()
            self._print_summary()
        else:
            print("  X No devices found across any MSP/organization")

    def _validate_msp_info(self, msp_info: dict) -> tuple:  # type: ignore[type-arg]
        """Validate MSP info and return (msp_id, msp_name) or (None, name) on failure."""
        msp_id = msp_info.get("msp_id")
        msp_name = msp_info.get("msp_name", "Unknown MSP")

        if not msp_id or not isinstance(msp_id, str):
            print(f"  X Invalid MSP ID for {msp_name}")
            return (None, msp_name)
        return (msp_id, msp_name)

    @staticmethod
    def _normalize_msp_orgs_response(orgs_data) -> list:  # type: ignore[no-untyped-def, type-arg]
        """Coerce listMspOrgs payload into a list (handles single-dict and None)."""
        if not isinstance(orgs_data, list):  # Not a list -- wrap or default
            return [orgs_data] if orgs_data else []  # Single dict -> 1-element list; None -> empty
        return orgs_data  # Already a list

    def _fetch_msp_orgs(self, msp_id: str, msp_name: str) -> list:  # type: ignore[type-arg]
        """Fetch organizations under this MSP. Returns empty list on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        if mh.apisession is None:
            print("    X API session not initialized")
            return []
        import mistapi.api.v1.msps.orgs as msp_orgs_api  # Lazy import of the MSP orgs endpoint

        response = msp_orgs_api.listMspOrgs(mh.apisession, msp_id)

        if not response or not hasattr(response, "data"):
            print(f"    X Failed to retrieve organizations for {msp_name}")
            self.errors.append(f"MSP {msp_name}: Failed to fetch orgs")
            return []

        return MSPInventoryExporter._normalize_msp_orgs_response(response.data)  # Delegate shape coercion

    def _process_msp_orgs_inventory(self, msp_id: str, msp_name: str) -> None:
        """Fetch the MSP's org list, log/print the count, then dispatch each org through _process_org."""
        orgs_data = self._fetch_msp_orgs(msp_id, msp_name)  # API: list orgs under this MSP.
        if not orgs_data:
            print(f"    ! No organizations found under {msp_name}")
            return
        print(f"    Found {len(orgs_data)} organization(s)")
        for org in orgs_data:  # Per-org processing.
            self._process_org(msp_id, msp_name, org)
        print("")

    def _process_msp(self, msp_info: dict) -> None:  # type: ignore[type-arg]
        """Process a single MSP - fetch all orgs and their devices."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        msp_id, msp_name = self._validate_msp_info(msp_info)
        if msp_id is None:  # Invalid input.
            return
        print(f"  Processing MSP: {msp_name}")
        print("-" * 70)
        self.msp_count += 1  # Count this MSP toward the run total.
        if mh.apisession is None:  # API not initialized.
            print("    X API session not initialized")
            return
        try:
            self._process_msp_orgs_inventory(msp_id, msp_name)  # Walk all orgs under this MSP.
        except Exception as e:  # Tolerate per-MSP failures.
            print(f"    X Error processing MSP {msp_name}: {e}")
            self.errors.append(f"MSP {msp_name}: {e}")
            logging.error("MSP inventory export error for %s: %s", msp_name, e)

    def _fetch_org_inventory(self, org_id: str, org_name: str) -> list:  # type: ignore[type-arg]
        """Fetch all devices from org inventory. Returns empty list on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        if mh.apisession is None:  # No authenticated session available
            print(f"      {org_name}: API session not initialized")  # Tell the user
            return []  # Nothing to fetch
        import mistapi.api.v1.orgs.inventory as org_inventory_api  # Lazy import of the inventory endpoint

        response = org_inventory_api.getOrgInventory(mh.apisession, org_id, limit=1000)  # Fetch the org inventory

        if not response or not hasattr(response, "data"):  # No usable payload came back
            print(f"      {org_name}: No inventory data")  # Tell the user
            return []  # No devices to return
        return self._normalize_inventory_data(response.data)  # Coerce the payload to a list of device dicts

    @staticmethod
    def _normalize_inventory_data(devices_data: Any) -> list:  # type: ignore[type-arg]  # Coerce inventory to a list
        """Normalize an inventory response payload to a list: pass lists through, wrap a single dict, else empty."""
        if isinstance(devices_data, list):  # Already a list of devices
            return devices_data  # Use it as-is
        return [devices_data] if devices_data else []  # Wrap a single record, or empty when falsy

    def _enrich_device_context(
        self,
        device: dict,  # type: ignore[type-arg]
        context: MspOrgContext,
        site_lookup: dict,  # type: ignore[type-arg]
    ) -> None:
        """Add MSP/Org/Site context to a device record (issue #470: MSP/Org identity bundled into context)."""
        device["_msp_id"] = context.msp_id  # Stamp MSP id from the bundled context (issue #470).
        device["_msp_name"] = context.msp_name  # Stamp MSP name from the bundled context (issue #470).
        device["_org_id"] = context.org_id  # Stamp org id from the bundled context (issue #470).
        device["_org_name"] = context.org_name  # Stamp org name from the bundled context (issue #470).
        site_id = device.get("site_id")
        device["_site_name"] = site_lookup.get(site_id, "Unknown Site") if site_id else "Unassigned"

    def _count_device_types(self, devices_data: list) -> dict:  # type: ignore[type-arg]
        """Count devices by type and return type_counts dict."""
        type_counts: dict[str, int] = {}
        for device in devices_data:
            device_type = device.get("type", "unknown")
            type_counts[device_type] = type_counts.get(device_type, 0) + 1
        return type_counts

    def _ingest_org_devices(self, devices_data: list, context: MspOrgContext, site_lookup: dict) -> None:  # type: ignore[type-arg]
        """Enrich each device with MSP/Org/Site context and append it to the running all_devices roll-up."""
        for device in devices_data:  # Per-device enrichment.
            self._enrich_device_context(device, context, site_lookup)  # Stamp identity.
            self.all_devices.append(device)  # Roll into global list.

    def _print_org_inventory_summary(self, org_name: str, devices_data: list) -> None:  # type: ignore[type-arg]
        """Print the per-org device-count summary line, broken out by device type."""
        type_counts = self._count_device_types(devices_data)  # Per-type tally.
        type_summary = ", ".join(f"{t}:{c}" for t, c in sorted(type_counts.items()))
        print(f"      {org_name}: {len(devices_data)} devices ({type_summary})")

    def _validate_org(self, org: dict) -> tuple[str, str] | None:  # type: ignore[type-arg]
        """Pull (org_id, org_name) from an org dict; return None when org_id is missing/invalid."""
        org_id = org.get("id")  # Required identifier
        org_name = org.get("name", "Unknown Org")  # Default name for diagnostics
        if not org_id or not isinstance(org_id, str):  # Bad org row.
            print(f"      {org_name}: Invalid org ID")
            return None
        return org_id, org_name  # Both valid

    def _process_org(self, msp_id: str, msp_name: str, org: dict) -> None:  # type: ignore[type-arg]
        """Process a single organization - fetch all devices from inventory."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        resolved = self._validate_org(org)  # Delegate input validation
        if resolved is None:  # Bad input -- helper already logged
            return
        org_id, org_name = resolved
        self.org_count += 1  # Count toward run total.
        if mh.apisession is None:  # API not initialized.
            return
        try:
            devices_data = self._fetch_org_inventory(org_id, org_name)  # API: list devices.
            if not devices_data:
                print(f"      {org_name}: 0 devices")
                return
            site_lookup = self._build_site_lookup(org_id)  # site_id -> site_name.
            ctx = MspOrgContext(msp_id, msp_name, org_id, org_name)  # Bundle identity (issue #470).
            self._ingest_org_devices(devices_data, ctx, site_lookup)  # Enrich + append.
            self.device_count += len(devices_data)  # Roll into run total.
            self._print_org_inventory_summary(org_name, devices_data)  # Per-type tally + print
        except Exception as e:  # Tolerate per-org failures.
            print(f"      {org_name}: Error - {e}")
            self.errors.append(f"Org {org_name}: {e}")
            logging.error("MSP inventory export error for org %s: %s", org_name, e)

    def _build_site_lookup(self, org_id: str) -> dict:  # type: ignore[type-arg]
        """Build a site_id -> site_name lookup for an org."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils helper.
        try:
            sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)
            return {s.get("id"): s.get("name", "Unknown") for s in sites}
        except Exception as e:
            logging.debug("Failed to build site lookup for org %s: %s", org_id, e)
            return {}

    def _get_priority_fields(self) -> list:  # type: ignore[type-arg]
        """Return list of priority fields for column ordering."""
        return [
            "_msp_name",
            "_msp_id",
            "_org_name",
            "_org_id",
            "_site_name",
            "site_id",
            "type",
            "model",
            "mac",
            "serial",
            "name",
            "version",
            "status",
            "ip",
            "public_ip",
        ]

    def _order_fields(self, all_fields: set, priority_fields: list) -> list:  # type: ignore[type-arg]
        """Order fields: priority first, then remaining alphabetically."""
        remaining_fields = sorted(all_fields - set(priority_fields))
        return [f for f in priority_fields if f in all_fields] + remaining_fields

    def _build_sorted_rows(self, flattened: list, ordered_fields: list) -> list:  # type: ignore[type-arg]
        """Build rows from flattened data and sort by MSP/Org/Site/Type/Name."""
        rows = [{field: device.get(field, "") for field in ordered_fields} for device in flattened]
        rows.sort(
            key=lambda x: (
                x.get("_msp_name", "").lower(),
                x.get("_org_name", "").lower(),
                x.get("_site_name", "").lower(),
                x.get("type", ""),
                x.get("name", "").lower(),
            )
        )
        return rows

    def _write_results(self) -> None:
        """Write all devices to CSV."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        priority_fields = self._get_priority_fields()
        flattened = mh.DataProcessingUtils.flatten_nested_fields(self.all_devices)

        all_fields: set[str] = set()
        for device in flattened:
            all_fields.update(device.keys())

        ordered_fields = self._order_fields(all_fields, priority_fields)
        rows = self._build_sorted_rows(flattened, ordered_fields)

        filename = os.path.join("data", "MSP_Inventory_Export.csv")
        mh.DataExporter.write_with_format_selection(rows, filename, api_function_name="mspInventoryExport")
        print(f"\n  + Results written to: {filename}")

    def _print_summary_errors(self) -> None:
        """Print error summary if any errors occurred."""
        if not self.errors:
            return
        print(f"    Errors encountered:     {len(self.errors)}")
        for error in self.errors[:5]:
            print(f"      - {error}")
        if len(self.errors) > 5:
            print(f"      ... and {len(self.errors) - 5} more")

    def _print_device_breakdown(self) -> None:
        """Print device type breakdown."""
        type_counts = self._count_device_types(self.all_devices)
        if not type_counts:
            return
        print("")
        print("  Device Type Breakdown:")
        for device_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"    {device_type:>12}: {count:>6}")

    def _print_summary(self) -> None:
        """Print summary statistics."""
        print("")
        print("=" * 70)
        print("  EXPORT SUMMARY")
        print("=" * 70)
        print(f"    MSPs processed:         {self.msp_count}")
        print(f"    Organizations scanned:  {self.org_count}")
        print(f"    Total devices exported: {self.device_count}")
        self._print_summary_errors()
        self._print_device_breakdown()
        print("")
