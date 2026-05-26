"""MSP orchestration for org device inventory summary extracted from MistHelper.py."""

from __future__ import annotations

import logging
from typing import Any
from typing import Callable

from prettytable import PrettyTable

apisession: Any = None
InputUtils: Any = None
DataExporter: Any = None
msp_privileges: list[dict[str, Any]] = []


def configure_org_device_inventory_msp_dependencies(
    *,
    apisession_dependency: Any,
    input_utils: Any,
    data_exporter: Any,
    msp_privileges_value: list[dict[str, Any]],
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global InputUtils
    global DataExporter
    global msp_privileges

    apisession = apisession_dependency
    InputUtils = input_utils
    DataExporter = data_exporter
    msp_privileges = msp_privileges_value or []


class OrgDeviceInventoryMSPOrchestrator:
    """MSP selection, org enumeration, and combined reporting orchestration."""

    @staticmethod
    def _resolve_active_msp() -> dict[str, Any] | None:
        """Prompt for MSP selection when multiple are available."""
        if not msp_privileges:
            print("\nX No MSP privileges detected.  Connect with an MSP account to use this mode.")
            logging.warning("_resolve_active_msp called with no MSP privileges")
            return None
        if len(msp_privileges) == 1:
            active_msp = msp_privileges[0]
            print(f"\n  Using MSP: {active_msp['msp_name']}")
            return active_msp
        print("\n  Available MSPs:")
        for idx, msp in enumerate(msp_privileges, start=1):
            print(f"    {idx}. {msp['msp_name']} (role: {msp['role']})")
        print()
        try:
            choice = InputUtils.safe_input("  Select MSP (number): ", context="msp_select").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(msp_privileges):
                return msp_privileges[choice_idx]
            print("X Invalid selection")
            logging.warning("MSP selection out of range: %s", choice)
        except (ValueError, SystemExit):
            print("X Invalid input")
            logging.warning("MSP selection input error")
        return None

    @staticmethod
    def _fetch_org_list(active_msp: dict[str, Any]) -> list[dict[str, Any]]:
        """Retrieve all child organizations for the selected MSP."""
        if apisession is None:
            print("X No active API session")
            logging.error("_fetch_org_list: apisession is None")
            return []
        msp_id = active_msp["msp_id"]
        msp_name = active_msp["msp_name"]
        logging.info("Fetching orgs for MSP %s (id=%s)", msp_name, msp_id)
        print(f"\n  Fetching organizations for MSP: {msp_name}...")
        try:
            import mistapi.api.v1.msps.orgs as msp_orgs_api

            orgs_response = msp_orgs_api.listMspOrgs(apisession, msp_id)
            orgs_data: list[dict[str, Any]] = (
                orgs_response.data if orgs_response and hasattr(orgs_response, "data") else []
            ) or []
            if not isinstance(orgs_data, list):
                orgs_data = [orgs_data]
        except Exception as error:
            print(f"X Failed to retrieve organizations: {error}")
            logging.error("listMspOrgs failed for msp_id=%s: %s", msp_id, error, exc_info=True)
            return []
        logging.debug("Received %d orgs from MSP %s", len(orgs_data), msp_name)
        return orgs_data

    @staticmethod
    def run_single_msp_org(run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]]) -> None:
        """Mode 2: let user select one org from MSP list and run summary for that org."""
        active_msp = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()
        if active_msp is None:
            return
        orgs_data = OrgDeviceInventoryMSPOrchestrator._fetch_org_list(active_msp)
        if not orgs_data:
            print("  No organizations found under this MSP")
            logging.info("run_single_msp_org: no orgs for MSP %s", active_msp["msp_id"])
            return
        print(f"\n  Found {len(orgs_data)} organizations:")
        for idx, org in enumerate(orgs_data, start=1):
            print(f"    {idx}. {org.get('name', org.get('id', 'Unknown'))}")
        print()
        try:
            choice = InputUtils.safe_input("  Select org (number): ", context="msp_org_select").strip()
            choice_idx = int(choice) - 1
            if not (0 <= choice_idx < len(orgs_data)):
                print("X Invalid selection")
                logging.warning("Org selection out of range: %s", choice)
                return
        except (ValueError, SystemExit):
            print("X Invalid input")
            logging.warning("Org selection input error")
            return
        chosen = orgs_data[choice_idx]
        chosen_id = chosen.get("id", "")
        if not chosen_id:
            print("X Selected org has no ID")
            logging.error("Selected org record missing 'id': %s", chosen)
            return
        logging.info("Running inventory for selected org: %s (%s)", chosen.get("name"), chosen_id)
        run_for_org_fn(chosen_id)

    @staticmethod
    def _display_combined_pivot_and_export(
        all_ver_data: list[tuple[str, list[dict]]],
        filename: str,
    ) -> None:
        """Build combined version-per-model pivot across all MSP orgs and export it."""
        flat: list[dict] = []
        for safe_org, ver_rows in all_ver_data:
            for row in ver_rows:
                flat.append({**row, "org": safe_org})
        if not flat:
            print("  No version-per-model data available for combined pivot")
            logging.warning("_display_combined_pivot_and_export: no data to pivot")
            return

        versions = sorted({row["version"] for row in flat})
        pivot: dict[tuple, dict] = {}
        for row in flat:
            key = (row["org"], row["model"])
            if key not in pivot:
                pivot[key] = {"device_type": row.get("device_type", "")}
            pivot[key][row["version"]] = row.get("count", 0)

        table = PrettyTable()
        table.field_names = ["Org", "Model", "Device Type"] + versions + ["Total"]
        col_totals: dict[str, int] = {version: 0 for version in versions}
        export_rows: list[dict] = []

        for (safe_org, model), ver_counts in sorted(pivot.items()):
            row_counts = [ver_counts.get(version, 0) for version in versions]
            row_total = sum(row_counts)
            for version, count in zip(versions, row_counts, strict=True):
                col_totals[version] += count
            table.add_row([safe_org, model, ver_counts.get("device_type", "")] + row_counts + [row_total])
            export_row: dict = {
                "Org": safe_org,
                "Model": model,
                "Device Type": ver_counts.get("device_type", ""),
            }
            for version in versions:
                export_row[version] = ver_counts.get(version, 0)
            export_row["Total"] = row_total
            export_rows.append(export_row)

        col_total_values = [col_totals[version] for version in versions]
        grand_total = sum(col_total_values)
        table.add_row(["TOTAL", "", ""] + col_total_values + [grand_total])

        print(f"\n{'=' * 62}")
        print("  Combined MSP Version Distribution per Model (All Orgs)")
        print(f"{'=' * 62}")
        print(table)

        ordered_fields = ["Org", "Model", "Device Type"] + versions + ["Total"]
        DataExporter.write_with_format_selection(
            export_rows,
            filename,
            api_function_name="orgDeviceVersionPerModel",
            fieldnames=ordered_fields,
        )

    @staticmethod
    def _build_combined_reports(msp_safe_name: str, collected: list[dict[str, Any]]) -> None:
        """Generate combined MSP model/version and pivot reports from collected org outputs."""
        prefix = f"MSP_{msp_safe_name}"

        combined_model: list[dict] = []
        for entry in collected:
            safe_org = entry["safe_org"]
            for row in entry["model_rows"]:
                combined_model.append(
                    {
                        "Org": safe_org,
                        "Device Type": row["device_type"],
                        "Model": row.get("model", ""),
                        "Count": row.get("count", 0),
                    }
                )

        model_table = PrettyTable()
        model_table.field_names = ["Org", "Device Type", "Model", "Count"]
        for row in combined_model:
            model_table.add_row([row["Org"], row["Device Type"], row["Model"], row["Count"]])

        print(f"\n{'=' * 62}")
        print("  Combined MSP Model Count Summary (All Orgs)")
        print(f"{'=' * 62}")
        print(model_table)

        DataExporter.write_with_format_selection(
            combined_model,
            f"{prefix}_CombinedDeviceModelCounts",
            api_function_name="orgDeviceModelSummary",
        )

        combined_version: list[dict] = []
        for entry in collected:
            safe_org = entry["safe_org"]
            for row in entry["version_rows"]:
                combined_version.append(
                    {
                        "Org": safe_org,
                        "Device Type": row["device_type"],
                        "Version": row.get("version", ""),
                        "Count": row.get("count", 0),
                    }
                )

        version_table = PrettyTable()
        version_table.field_names = ["Org", "Device Type", "Version", "Count"]
        for row in combined_version:
            version_table.add_row([row["Org"], row["Device Type"], row["Version"], row["Count"]])

        print(f"\n{'=' * 62}")
        print("  Combined MSP Firmware Version Summary (All Orgs)")
        print(f"{'=' * 62}")
        print(version_table)

        DataExporter.write_with_format_selection(
            combined_version,
            f"{prefix}_CombinedDeviceFirmwareSummary",
            api_function_name="orgDeviceFirmwareSummary",
        )

        all_ver_data = [(entry["safe_org"], entry["ver_per_model"]) for entry in collected]
        OrgDeviceInventoryMSPOrchestrator._display_combined_pivot_and_export(
            all_ver_data,
            f"{prefix}_CombinedDeviceVersionPerModel",
        )

        print(f"\n  Combined MSP reports written with prefix: {prefix}_")

    @staticmethod
    def execute_msp(run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]]) -> None:
        """Mode 3: run inventory summaries for all orgs under selected MSP."""
        logging.info("Starting MSP device inventory summary")
        active_msp = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()
        if active_msp is None:
            return
        orgs_data = OrgDeviceInventoryMSPOrchestrator._fetch_org_list(active_msp)
        if not orgs_data:
            print("  No organizations found under this MSP")
            logging.info("execute_msp: no orgs found for MSP %s", active_msp["msp_id"])
            return

        print(f"  Found {len(orgs_data)} organizations.  Running inventory summary for each...\n")
        collected: list[dict] = []
        for idx, org_record in enumerate(orgs_data, start=1):
            child_org_id = org_record.get("id", "")
            child_org_name = org_record.get("name", child_org_id)
            if not child_org_id:
                logging.warning("Skipping org record with no id: %s", org_record)
                continue
            print(f"  [{idx}/{len(orgs_data)}] {child_org_name}")
            try:
                model_rows, version_rows, ver_per_model, safe_org = run_for_org_fn(child_org_id)
                collected.append(
                    {
                        "safe_org": safe_org,
                        "model_rows": model_rows,
                        "version_rows": version_rows,
                        "ver_per_model": ver_per_model,
                    }
                )
            except Exception as error:
                print(f"    X Error processing {child_org_name}: {error}")
                logging.error("run_for_org failed for org %s: %s", child_org_id, error, exc_info=True)

        logging.info("MSP inventory complete for %d orgs", len(orgs_data))
        print(f"\nMSP inventory summary complete. Processed {len(orgs_data)} organizations.")
        if len(collected) >= 2:
            msp_safe_name = "".join(
                char if char.isalnum() or char in "-_" else "_" for char in active_msp.get("msp_name", "MSP")
            )
            OrgDeviceInventoryMSPOrchestrator._build_combined_reports(msp_safe_name, collected)
        else:
            logging.info("Skipping combined reports: fewer than 2 orgs processed successfully")

    @staticmethod
    def dispatch(single_org_fn: Callable[[], None], select_org_fn: Callable[[], None], batch_fn: Callable[[], None]) -> None:
        """Interactive dispatcher for menu operation 13 MSP modes."""
        if not msp_privileges:
            single_org_fn()
            return

        print("\n" + "=" * 60)
        print("  DEVICE INVENTORY SUMMARY")
        print("=" * 60)
        print("\n  Run mode:")
        print("    1. Current org only")
        print("    2. Select a specific org from MSP list")
        print("    3. All orgs in MSP (batch mode)")
        print()

        try:
            mode = InputUtils.safe_input("  Select mode (1/2/3): ", context="inventory_dispatch").strip()
        except SystemExit:
            return

        if mode == "3":
            batch_fn()
        elif mode == "2":
            select_org_fn()
        else:
            single_org_fn()
