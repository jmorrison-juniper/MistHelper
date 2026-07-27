"""GlobalWiredClientReportGenerator -- org-wide wired client report with operator filtering.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 36).
Menu handler that prompts for optional MAC + manufacturer filters (with 12
comparison operators), fetches org-wide wired clients (with best-effort
remote prefiltering), applies local authoritative filtering with AND logic,
then writes both a CSV/SQLite export and a JSON summary artifact.

Direct imports cover stdlib + installed packages (mistapi). Live-global reads
(``apisession``, ``ConfigUtils``, ``FilterOperatorEngine``, ``InputUtils``,
``DataProcessingUtils``, ``DataExporter``) are resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside each helper. Callers
continue to reach the class through the
``MistHelper.GlobalWiredClientReportGenerator`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import json  # WHY: local report summary is serialized as JSON.
import logging  # WHY: structured trace for report lifecycle events.
import os  # WHY: build cross-platform output paths under data/.
from datetime import UTC, datetime  # WHY: UTC ISO timestamp for report metadata.
from typing import Any, Literal  # WHY: Literal[False] to distinguish user cancel from empty result.

import mistapi  # WHY: direct SDK access for search + pagination helpers.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class GlobalWiredClientReportGenerator:
    """Generates organization-wide wired client reports with operator-based MAC/manufacturer filtering."""

    @staticmethod
    def execute() -> None:  # Run the report.
        """Main entry point from menu system."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        criteria = GlobalWiredClientReportGenerator._prompt_filter_criteria()  # Prompt for filters.
        if criteria is False:  # User cancelled.
            return  # Abort.
        records, remote_used = GlobalWiredClientReportGenerator._fetch_clients(org_id, criteria)
        if not records:  # No records.
            logging.warning("No wired clients retrieved from API")  # Warn none retrieved.
            logging.warning("\n  No wired clients found in the organization.")  # Legacy console echo routed via logger.
            return  # Abort.
        matched, metadata = GlobalWiredClientReportGenerator._apply_filters(records, criteria, remote_used)
        GlobalWiredClientReportGenerator._write_outputs(matched, metadata)  # Write the outputs.

    @staticmethod
    def _prompt_filter_criteria() -> dict[str, str] | Literal[False] | None:  # False = user cancelled, never True
        """Collect optional MAC and manufacturer filter criteria from user."""
        logging.warning("\n--- Global Wired Client Report ---")  # Legacy console echo routed via logger.
        logging.warning("Optional filters (press Enter to skip):\n")  # Legacy console echo routed via logger.
        criteria: dict[str, str] = {}  # Collect criteria.
        mac_result = GlobalWiredClientReportGenerator._collect_single_filter("MAC address", "mac", criteria)
        if mac_result is False:  # User cancelled.
            return False  # Abort.
        mfg_result = GlobalWiredClientReportGenerator._collect_single_filter("Manufacturer", "mfg", criteria)
        if mfg_result is False:  # User cancelled.
            return False  # Abort.
        return criteria if criteria else None  # Return criteria or None.

    @staticmethod
    def _collect_single_filter(field_label: str, key_prefix: str, criteria: dict[str, str]) -> bool | None:
        """Collect a single field operator and value. Returns False on validation failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilterOperatorEngine + InputUtils.
        operator = GlobalWiredClientReportGenerator._prompt_operator(field_label)  # Prompt the operator.
        if not operator:  # No operator chosen.
            return None  # Skip this field.
        criteria[f"{key_prefix}_operator"] = operator  # Record the operator.
        if operator not in mh.FilterOperatorEngine.VALUE_REQUIRED_OPERATORS:  # Operator needs no value.
            return True  # Done.
        value = mh.InputUtils.safe_input(f"  Enter {field_label} value: ", context=f"wired_report_{key_prefix}_filter")
        if not mh.FilterOperatorEngine.validate_operator_value(operator, value, field_label):  # Validate the value.
            return False  # Invalid value.
        criteria[f"{key_prefix}_value"] = value  # Record the value.
        return True  # Done.

    @staticmethod
    def _resolve_operator_choice(choice: str, field_name: str) -> str | None:
        """Map a 1-based operator choice (or '0'/empty) to an operator string, or ``None`` on skip/invalid."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilterOperatorEngine.
        if choice == "0" or not choice:  # Operator explicitly skipped
            return None
        try:
            index = int(choice) - 1  # Convert to 0-based catalog index
            if 0 <= index < len(mh.FilterOperatorEngine.OPERATOR_CATALOG):  # Bounds-check parsed index
                selected = mh.FilterOperatorEngine.OPERATOR_CATALOG[index]  # Resolve catalog entry
                logging.info("Selected %s operator: %s", field_name, selected)  # Trace operator choice
                return selected  # type: ignore[no-any-return]
        except ValueError:  # Non-numeric input -> treat as invalid
            pass
        logging.warning(
            "  Invalid selection. No %s filter will be applied.", field_name
        )  # Legacy console echo routed via logger.
        return None

    @staticmethod
    def _prompt_operator(field_name: str) -> str | None:  # Prompt an operator choice.
        """Display operator selection menu and return chosen operator or None."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilterOperatorEngine + InputUtils.
        logging.warning("  %s filter operator:", field_name)  # Legacy console echo routed via logger.
        logging.warning("    0. No filter (skip)")  # Legacy console echo routed via logger.
        for index, operator in enumerate(mh.FilterOperatorEngine.OPERATOR_CATALOG, 1):  # List operators
            logging.warning("    %s. %s", index, operator)  # Legacy console echo routed via logger.
        choice = mh.InputUtils.safe_input(  # Read the choice
            f"  Select {field_name} operator (0-12, default 0): ",
            default_value="0",
            context=f"wired_report_{field_name.lower().replace(' ', '_')}_operator",
        )
        return GlobalWiredClientReportGenerator._resolve_operator_choice(choice, field_name)  # Parse + bounds-check

    @staticmethod
    def _fetch_clients(org_id: str, criteria: dict[str, str] | None) -> tuple[list[dict[str, Any]], bool]:
        """Fetch org-wide wired clients with optional remote prefiltering."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession global.
        remote_params: dict[str, Any] = {"limit": 1000}  # Base API params.
        remote_used = False  # Track remote prefilter use.
        if criteria:  # Have criteria.
            remote_used = GlobalWiredClientReportGenerator._build_remote_params(criteria, remote_params)
        try:
            logging.info("Fetching organization wired clients...")  # Log the fetch.
            logging.warning(
                "\n  Retrieving wired clients from organization..."
            )  # Legacy console echo routed via logger.
            response = mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients(  # Call the API.
                mh.apisession,
                org_id,
                **remote_params,
            )
            records = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all. Default empty.
            logging.info("Retrieved %s wired client records", len(records))  # Log the count.
            logging.warning(
                "  Retrieved %s wired client records", len(records)
            )  # Legacy console echo routed via logger.
            return records, remote_used  # Return records and flag.
        except Exception as exception:  # Fetch failed.
            logging.exception("Failed to fetch wired clients: %s", exception)  # Log the exception.
            logging.warning(
                "\n  Error retrieving wired clients: %s", exception
            )  # Legacy console echo routed via logger.
            return [], False  # Return empty.

    @staticmethod
    def _build_remote_params(criteria: dict[str, str], params: dict[str, Any]) -> bool:
        """Add best-effort remote prefilter params. Returns True if any were added."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilterOperatorEngine.
        remote_used = False  # Track whether we added any server-side prefilter parameters
        mac_operator = criteria.get("mac_operator", "")  # The chosen MAC comparison operator (may be empty)
        if (
            mac_operator in mh.FilterOperatorEngine.REMOTE_PREFILTER_OPERATORS
        ):  # Only some operators can be pushed to the API
            mac_value = criteria.get("mac_value", "")  # The MAC value to prefilter on
            if mac_value:  # A non-empty value was provided
                params["mac"] = mac_value  # Add the MAC prefilter to the API query params
                remote_used = True  # Note that a remote prefilter was applied
                logging.info("Remote prefilter: mac=%s", mac_value)  # Log the applied prefilter
        mfg_operator = criteria.get("mfg_operator", "")  # The chosen manufacturer comparison operator
        if mfg_operator in mh.FilterOperatorEngine.REMOTE_PREFILTER_OPERATORS:  # Only push API-supported operators
            mfg_value = criteria.get("mfg_value", "")  # The manufacturer value to prefilter on
            if mfg_value:  # A non-empty value was provided
                params["manufacture"] = mfg_value  # Add the manufacturer prefilter to the API query params
                remote_used = True  # Note that a remote prefilter was applied
                logging.info("Remote prefilter: manufacture=%s", mfg_value)  # Log the applied prefilter
        return remote_used  # Report whether any server-side prefilter was used

    @staticmethod
    def _build_no_filter_result(
        records: list[dict[str, Any]],
        remote_used: bool,
        criteria: dict[str, str] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Build the (records, metadata) tuple for the empty-criteria path — every record passes."""
        total_retrieved = len(records)  # Pre-filter API record count.
        metadata = GlobalWiredClientReportGenerator._build_metadata(  # No-filter metadata block.
            total_retrieved,
            total_retrieved,
            remote_used,
            False,
            criteria,
        )
        return records, metadata  # Records pass through unchanged.

    @staticmethod
    def _apply_filters(  # Apply local filters.
        records: list[dict[str, Any]],
        criteria: dict[str, str] | None,
        remote_used: bool,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Apply local authoritative filtering with AND logic. Returns matched records and metadata."""
        if not criteria:  # No criteria — every record passes via the no-filter result builder.
            return GlobalWiredClientReportGenerator._build_no_filter_result(records, remote_used, criteria)
        total_retrieved = len(records)  # Pre-filter API record count for metadata.
        matched = [
            record for record in records if GlobalWiredClientReportGenerator._record_matches(record, criteria)
        ]  # Keep only records passing all criteria.
        metadata = GlobalWiredClientReportGenerator._build_metadata(  # Build metadata describing the filter results.
            total_retrieved,
            len(matched),
            remote_used,
            True,
            criteria,
        )
        return matched, metadata  # Return the filtered records plus metadata.

    @staticmethod
    def _record_matches(record: dict[str, Any], criteria: dict[str, str]) -> bool:  # Test one record vs criteria.
        """Evaluate a single record against all active filter criteria with AND logic."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilterOperatorEngine.
        mac_operator = criteria.get("mac_operator")  # The MAC operator to evaluate, if any
        if mac_operator:  # A MAC filter is active
            mac_value = criteria.get("mac_value", "")  # The MAC value to compare against
            field_value = record.get("mac")  # This record's MAC address
            if not mh.FilterOperatorEngine.evaluate_operator(
                field_value, mac_operator, mac_value, is_mac=True
            ):  # Apply the MAC comparison
                return False  # AND logic: any failed criterion rejects the record
        mfg_operator = criteria.get("mfg_operator")  # The manufacturer operator to evaluate, if any
        if mfg_operator:  # A manufacturer filter is active
            mfg_value = criteria.get("mfg_value", "")  # The manufacturer value to compare against
            field_value = record.get("manufacture")  # This record's manufacturer field
            if not mh.FilterOperatorEngine.evaluate_operator(
                field_value, mfg_operator, mfg_value, is_mac=False
            ):  # Apply the manufacturer comparison
                return False  # AND logic: any failed criterion rejects the record
        return True  # The record passed every active criterion

    @staticmethod
    def _build_metadata(  # Build report metadata.
        retrieved: int,
        matched: int,
        remote_used: bool,
        local_used: bool,
        criteria: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Build filtering decision metadata for output summary."""
        metadata: dict[str, Any] = {
            "records_retrieved": retrieved,
            "records_matched": matched,
            "remote_filter_used": remote_used,
            "local_filter_used": local_used,
            "generated_at": datetime.now(UTC).isoformat(),  # UTC ISO timestamp for report metadata
        }
        if criteria:  # Have criteria.
            if criteria.get("mac_operator"):  # MAC filter present.
                metadata["mac_operator"] = criteria["mac_operator"]  # Record MAC operator.
                metadata["mac_value"] = criteria.get("mac_value", "")  # Record MAC value.
            if criteria.get("mfg_operator"):  # Mfg filter present.
                metadata["mfg_operator"] = criteria["mfg_operator"]  # Record mfg operator.
                metadata["mfg_value"] = criteria.get("mfg_value", "")  # Record mfg value.
        return metadata  # Return metadata.

    @staticmethod
    def _write_outputs(matched: list[dict[str, Any]], metadata: dict[str, Any]) -> None:  # Write all report outputs.
        """Write matched records to both local report artifact and standard export."""
        matched_count = metadata["records_matched"]  # Matched count.
        retrieved_count = metadata["records_retrieved"]  # Retrieved count.
        logging.warning(
            "\n  Matched %s of %s wired client records", matched_count, retrieved_count
        )  # Legacy console echo routed via logger.
        if matched_count == 0:  # Nothing matched.
            logging.info("Zero records matched filters -- producing empty outputs")  # Log empty result.
            logging.warning("  No records matched the specified filters.")  # Legacy console echo routed via logger.
        GlobalWiredClientReportGenerator._write_standard_export(matched)  # Write the CSV export.
        GlobalWiredClientReportGenerator._write_local_report(matched, metadata)  # Write the JSON summary.

    @staticmethod
    def _write_standard_export(matched: list[dict[str, Any]]) -> None:  # Write the standard CSV.
        """Write matched records through the standard CSV/SQLite export path."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if matched:  # Have matches.
            flattened = DataProcessingUtils.flatten_nested_fields(matched)  # Flatten nested fields.
            sanitized = DataProcessingUtils.escape_multiline(flattened)  # type: ignore[no-untyped-call]
        else:
            sanitized = []  # No matches.
        mh.DataExporter.write_with_format_selection(  # Write via backend.
            sanitized,
            "GlobalWiredClientReport",
            api_function_name="globalWiredClientReport",
        )
        logging.info("Standard export: %s records to GlobalWiredClientReport", len(sanitized))  # Log the export.

    @staticmethod
    def _write_local_report(matched: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
        """Write local report artifact with summary metadata to data/ directory."""
        report_path = os.path.join("data", "GlobalWiredClientReport_summary.json")  # Report file path.
        report_payload: dict[str, Any] = {  # Build the payload.
            "summary": metadata,
            "record_count": len(matched),
        }
        try:
            with open(report_path, "w", encoding="utf-8") as report_file:  # Open the report file.
                json.dump(report_payload, report_file, indent=2, default=str)  # Dump JSON.
            logging.info("Local report artifact written to %s", report_path)  # Log the write.
            logging.warning("  Report summary written to %s", report_path)  # Legacy console echo routed via logger.
        except OSError as error:  # Write failed.
            logging.error("Failed to write local report artifact: %s", error)  # Log the error.
            logging.warning(
                "  Warning: Could not write report summary to %s", report_path
            )  # Legacy console echo routed via logger.
