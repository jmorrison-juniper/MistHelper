"""WiredClientManufacturerReportGenerator -- wired client report filtered by manufacturer.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 26).
Menu handler that fetches wired clients org-wide, exports the full set, then
optionally exports a filtered subset by user-selected manufacturer. All
methods are static -- no state is kept on the class. Callers continue to
reach it through the ``MistHelper.WiredClientManufacturerReportGenerator``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for report lifecycle events.
import re  # WHY: slugify manufacturer names into filesystem-safe filenames.
from typing import Any  # WHY: raw wired-client rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for search + pagination helpers.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class WiredClientManufacturerReportGenerator:
    """Generates wired client reports filtered by interactive manufacturer selection."""

    @staticmethod
    def execute() -> None:  # Run the report.
        """Main entry point: always export ALL, then optionally filter by manufacturer."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        records = WiredClientManufacturerReportGenerator._fetch_all_clients(org_id)  # Fetch all clients.
        if not records:  # No records.
            logging.warning("No wired clients retrieved from API")  # Warn none retrieved.
            print("\n  No wired clients found in the organization.")  # Tell the user.
            return  # Abort.
        WiredClientManufacturerReportGenerator._write_outputs(records, "")  # Write the full export.
        summary = WiredClientManufacturerReportGenerator._build_manufacturer_summary(records)
        selected = WiredClientManufacturerReportGenerator._prompt_selection(summary)  # Prompt a selection.
        if not selected:  # No selection.
            return  # Abort.
        filtered = WiredClientManufacturerReportGenerator._filter_by_manufacturer(records, selected)
        WiredClientManufacturerReportGenerator._write_outputs(filtered, selected)  # Write the filtered export.

    @staticmethod
    def _fetch_all_clients(org_id: str) -> list[dict[str, Any]]:  # Fetch all wired clients.
        """Fetch all wired clients across the organization without filters."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession global.
        try:
            logging.info("Fetching all organization wired clients for manufacturer report...")  # Log the fetch.
            print("\n  Retrieving all wired clients from organization...")  # Tell the user.
            response = mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients(  # Call the API.
                mh.apisession,
                org_id,
                limit=1000,
            )
            records = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all; default empty.
            logging.info("Retrieved %s wired client records", len(records))  # Log the count.
            print(f"  Retrieved {len(records)} wired client records")  # Tell the user.
            return records  # Return records.
        except Exception as exception:  # Fetch failed.
            logging.exception("Failed to fetch wired clients: %s", exception)  # Log the exception.
            print(f"\n  Error retrieving wired clients: {exception}")  # Tell the user.
            return []  # Return empty.

    @staticmethod
    def _build_manufacturer_summary(records: list[dict[str, Any]]) -> list[tuple[str, int]]:
        """Extract unique manufacturers with client counts, sorted alphabetically."""
        manufacturer_counts: dict[str, int] = {}  # Count map.
        for record in records:  # Walk records.
            manufacturer = str(record.get("manufacture", "Unknown") or "Unknown").strip()  # Normalize the manufacturer.
            manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1  # Increment the count.
        sorted_manufacturers = sorted(manufacturer_counts.items(), key=lambda item: item[0].lower())  # Sort by name.
        return sorted_manufacturers  # Return the summary.

    @staticmethod
    def _print_manufacturer_table(summary: list[tuple[str, int]]) -> None:
        """Render the manufacturer/count picker table to stdout."""
        total_clients = sum(count for _, count in summary)  # Aggregate total client count for header line.
        print(f"\n  Found {total_clients} clients from {len(summary)} manufacturers\n")  # Tell the user totals.
        print(f"  {'#':<5} {'Manufacturer':<45} {'Count':>8}")  # Column header.
        print(f"  {'-' * 5} {'-' * 45} {'-' * 8}")  # Separator row.
        for index, (manufacturer, count) in enumerate(summary, 1):  # List each manufacturer.
            display_name = manufacturer[:44]  # Truncate long names so column stays aligned.
            print(f"  {index:<5} {display_name:<45} {count:>8}")  # Print the row.

    @staticmethod
    def _parse_manufacturer_choice(choice: str, summary: list[tuple[str, int]]) -> str | None:
        """Map user input to a manufacturer name, returning None for empty/invalid/out-of-range."""
        if not choice:  # User skipped the selection prompt.
            return None  # Caller treats None as "no filter".
        try:
            selection_index = int(choice)  # Parse the numeric selection.
        except ValueError:  # Non-numeric input.
            print("  Invalid selection.")  # Tell the user.
            return None  # Abort.
        if 1 <= selection_index <= len(summary):  # In valid range.
            selected_manufacturer = summary[selection_index - 1][0]  # Pick the manufacturer name.
            logging.info("User selected manufacturer: %s", selected_manufacturer)  # Log the choice.
            return selected_manufacturer  # Return chosen manufacturer.
        print("  Selection out of range.")  # Out-of-range selection.
        return None  # Abort.

    @staticmethod
    def _prompt_selection(summary: list[tuple[str, int]]) -> str | None:  # Prompt manufacturer selection.
        """Display manufacturer list with counts and prompt user to select one."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils helper.
        WiredClientManufacturerReportGenerator._print_manufacturer_table(summary)  # Render the picker table.
        choice = mh.InputUtils.safe_input(  # Read the choice.
            "\n  Enter manufacturer number for filtered report (Enter to skip): ",
            default_value="",
            allow_empty=True,
            context="manufacturer_report_selection",
        )
        return WiredClientManufacturerReportGenerator._parse_manufacturer_choice(
            choice, summary
        )  # Map input -> choice.

    @staticmethod
    def _filter_by_manufacturer(records: list[dict[str, Any]], manufacturer: str) -> list[dict[str, Any]]:
        """Filter records by selected manufacturer. Empty string means no filter (all records)."""
        if not manufacturer:  # No filter.
            return records  # Return all.
        normalized_selection = manufacturer.strip().lower()  # Normalize the selection.
        return [  # Keep matching records.
            record
            for record in records
            if str(record.get("manufacture", "") or "").strip().lower() == normalized_selection
        ]

    @staticmethod
    def _build_filename(manufacturer: str) -> str:  # Build the output filename.
        """Build a unique filename incorporating the selected manufacturer."""
        if not manufacturer:  # No manufacturer.
            slug = "ALL"  # Use ALL slug.
        else:
            slug = re.sub(r"[^\w]+", "_", manufacturer).strip("_")[:40]  # Slugify the manufacturer.
        return f"WiredClientManufacturerReport_{slug}"  # Return the filename.

    @staticmethod
    def _write_outputs(filtered: list[dict[str, Any]], manufacturer: str) -> None:  # Write the export outputs.
        """Write filtered records through the standard CSV/SQLite export path."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        label = manufacturer if manufacturer else "ALL manufacturers"  # Label for messages.
        filename = WiredClientManufacturerReportGenerator._build_filename(manufacturer)  # Build the filename.
        print(f"\n  Exporting {len(filtered)} records for: {label}")  # Tell the user.
        if filtered:  # Have records.
            flattened = DataProcessingUtils.flatten_nested_fields(filtered)  # Flatten nested fields.
            sanitized = DataProcessingUtils.escape_multiline(flattened)
        else:
            sanitized = []  # No records.
        mh.DataExporter.write_with_format_selection(  # Write via backend.
            sanitized,
            filename,
            api_function_name="wiredClientManufacturerReport",
        )
        print(f"  Exported to: data/{filename}.csv")  # Tell the user.
        logging.info("Manufacturer report exported: %s records for %s -> %s", len(sanitized), label, filename)
