"""MSP orchestration for org device inventory summary extracted from MistHelper.py."""

from __future__ import annotations  # WHY: enable postponed evaluation for typing hints.

import logging  # WHY: emit debug/info/warning traces for MSP orchestration observability.
from collections.abc import Callable  # WHY: type hint injected per-org runner callback.
from dataclasses import dataclass  # WHY: frozen dataclasses group per-org processed output.
from typing import Any  # WHY: injected dependencies + Mist API responses are heterogeneous.

from prettytable import PrettyTable  # WHY: render aligned pivot tables for operator console.

# Module-level constants keep magic strings/values out of function bodies.
_HEADER_DIVIDER: str = "=" * 62  # WHY: legacy divider width for MSP report headers.
_MENU_DIVIDER: str = "=" * 60  # WHY: legacy divider width for the interactive dispatch menu.
_INVALID_SELECTION_MSG: str = "X Invalid selection"  # WHY: single source of truth for range error prompt.
_INVALID_INPUT_MSG: str = "X Invalid input"  # WHY: single source of truth for parse error prompt.
_NO_MSP_MSG: str = "\nX No MSP privileges detected.  Connect with an MSP account to use this mode."  # WHY: shared warn.
_NO_API_SESSION_MSG: str = "X No active API session"  # WHY: shared no-session warning shown to operator.
_NO_ORGS_MSG: str = "  No organizations found under this MSP"  # WHY: shared empty-orgs operator message.
_MIN_ORGS_FOR_COMBINED: int = 2  # WHY: combined MSP reports require at least two orgs to be meaningful.
_SAFE_NAME_ALLOWED: str = "-_"  # WHY: characters kept verbatim in filesystem-safe MSP name transformation.
_MODEL_EXPORT_SUFFIX: str = "_CombinedDeviceModelCounts"  # WHY: filename suffix for combined model export.
_VERSION_EXPORT_SUFFIX: str = "_CombinedDeviceFirmwareSummary"  # WHY: filename suffix for combined version export.
_PIVOT_EXPORT_SUFFIX: str = "_CombinedDeviceVersionPerModel"  # WHY: filename suffix for combined pivot export.

apisession: Any = None  # WHY: mistapi session injected by MistHelper. None until configured.
InputUtils: Any = None  # WHY: injected EOF-safe input wrapper (issue #452).
DataExporter: Any = None  # WHY: injected exporter class exposing write_with_format_selection.
msp_privileges: list[dict[str, Any]] = []  # WHY: injected MSP privilege records from mistapi self endpoint.


@dataclass(frozen=True)
class _OrgProcessedResult:
    """Immutable per-org outputs collected during MSP batch execution."""

    safe_org: str  # WHY: filesystem-safe org name used as key/prefix in combined reports.
    model_rows: list[dict[str, Any]]  # WHY: per-org model count rows for combined model report.
    version_rows: list[dict[str, Any]]  # WHY: per-org version count rows for combined version report.
    ver_per_model: list[dict[str, Any]]  # WHY: per-org version-per-model rows feeding the pivot table.


@dataclass(frozen=True)
class _PivotAccumulator:
    """Shared accumulators for MSP pivot construction bundled to keep signatures narrow."""

    table: PrettyTable  # WHY: PrettyTable receiver that grows one row per pivot entry.
    export_rows: list[dict[str, Any]]  # WHY: CSV row accumulator flattened alongside table rows.
    col_totals: dict[str, int]  # WHY: running per-version totals mutated as rows are emitted.
    versions: list[str]  # WHY: canonical version column order shared across all row emissions.


def configure_org_device_inventory_msp_dependencies(
    *,
    apisession_dependency: Any,
    input_utils: Any,
    data_exporter: Any,
    msp_privileges_value: list[dict[str, Any]],
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession  # WHY: rebind module-level API session dependency.
    global InputUtils  # WHY: rebind module-level input helper dependency.
    global DataExporter  # WHY: rebind module-level exporter dependency.
    global msp_privileges  # WHY: rebind module-level MSP privilege records.

    apisession = apisession_dependency  # WHY: store injected mistapi session.
    InputUtils = input_utils  # WHY: store injected input helper (EOF-safe wrapper).
    DataExporter = data_exporter  # WHY: store injected exporter for downstream CSV writes.
    msp_privileges = msp_privileges_value or []  # WHY: normalise None to empty list for downstream len() checks.


def _print_msp_choices(privileges: list[dict[str, Any]]) -> None:
    """Print the numbered list of MSP privileges to the operator."""
    print("\n  Available MSPs:")  # WHY: legacy header preserved for operator familiarity.
    for idx, msp in enumerate(privileges, start=1):  # WHY: 1-based numbering shown to user.
        print(f"    {idx}. {msp['msp_name']} (role: {msp['role']})")  # WHY: display name + role per privilege.
    print()  # WHY: trailing blank line separates list from prompt.


def _prompt_msp_choice(privileges: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prompt operator to pick an MSP from the printed list, returning selection or None."""
    try:
        choice = InputUtils.safe_input("  Select MSP (number): ", context="msp_select").strip()  # WHY: read choice.
        choice_idx = int(choice) - 1  # WHY: convert 1-based operator input to 0-based index.
        if 0 <= choice_idx < len(privileges):  # WHY: guard against out-of-range indexes.
            return privileges[choice_idx]  # WHY: return the selected MSP dict.
        print(_INVALID_SELECTION_MSG)  # WHY: notify operator of out-of-range selection.
        logging.warning("MSP selection out of range: %s", choice)  # WHY: log for post-mortem debugging.
    except (ValueError, SystemExit):  # WHY: cover parse errors and EOF/interrupt from safe_input.
        print(_INVALID_INPUT_MSG)  # WHY: notify operator of parse error.
        logging.warning("MSP selection input error")  # WHY: log the invalid-input branch.
    return None  # WHY: any failure path resolves to no selection.


def _print_org_choices(orgs_data: list[dict[str, Any]]) -> None:
    """Print the numbered list of orgs to the operator."""
    print(f"\n  Found {len(orgs_data)} organizations:")  # WHY: header with count for context.
    for idx, org in enumerate(orgs_data, start=1):  # WHY: 1-based numbering matches MSP menu style.
        print(
            f"    {idx}. {org.get('name', org.get('id', 'Unknown'))}"
        )  # WHY: fall back through name -> id -> Unknown.
    print()  # WHY: trailing blank line separates list from prompt.


def _prompt_org_index(orgs_data: list[dict[str, Any]]) -> int | None:
    """Prompt operator for an org number and return the 0-based index or None on error."""
    try:
        choice = InputUtils.safe_input("  Select org (number): ", context="msp_org_select").strip()  # WHY: read.
        choice_idx = int(choice) - 1  # WHY: convert 1-based input to 0-based index.
        if not (0 <= choice_idx < len(orgs_data)):  # WHY: guard against out-of-range indexes.
            print(_INVALID_SELECTION_MSG)  # WHY: notify operator of bad range.
            logging.warning("Org selection out of range: %s", choice)  # WHY: log for post-mortem debugging.
            return None  # WHY: signal invalid choice.
        return choice_idx  # WHY: return valid 0-based index for downstream lookup.
    except (ValueError, SystemExit):  # WHY: cover parse errors and EOF/interrupt from safe_input.
        print(_INVALID_INPUT_MSG)  # WHY: notify operator of parse error.
        logging.warning("Org selection input error")  # WHY: log invalid-input branch.
        return None  # WHY: propagate error as sentinel index.


def _normalise_orgs_payload(raw_payload: Any) -> list[dict[str, Any]]:
    """Coerce a mistapi listMspOrgs payload into a uniform list of org dicts."""
    orgs_data: list[dict[str, Any]] = raw_payload or []  # WHY: normalise None/falsy payload to empty list.
    if not isinstance(orgs_data, list):  # WHY: single-org APIs sometimes return a dict.
        orgs_data = [orgs_data]  # WHY: wrap solitary org dict so callers can iterate uniformly.
    return orgs_data  # WHY: guaranteed list for downstream iteration.


def _call_list_msp_orgs(msp_id: str, msp_name: str) -> list[dict[str, Any]]:
    """Call mistapi listMspOrgs and normalise the response to a plain list of dicts."""
    try:
        import mistapi.api.v1.msps.orgs as msp_orgs_api  # WHY: local import avoids module-load side effects.

        orgs_response = msp_orgs_api.listMspOrgs(apisession, msp_id)  # WHY: SDK call returns response envelope.
        raw_data = orgs_response.data if orgs_response and hasattr(orgs_response, "data") else []  # WHY: unwrap.
        orgs_data = _normalise_orgs_payload(raw_data)  # WHY: coerce payload to list form via helper.
    except Exception as error:  # WHY: any SDK failure must surface as empty result plus operator message.
        print(f"X Failed to retrieve organizations: {error}")  # WHY: show error to interactive operator.
        logging.exception("listMspOrgs failed for msp_id=%s: %s", msp_id, error)  # WHY: full stack in log.
        return []  # WHY: empty list lets callers short-circuit gracefully.
    logging.debug("Received %d orgs from MSP %s", len(orgs_data), msp_name)  # WHY: post-call trace.
    return orgs_data  # WHY: return the normalised org list.


def _sanitize_msp_name(msp_name: str) -> str:
    """Return a filesystem-safe MSP name suitable for filename prefixes."""
    return "".join(char if char.isalnum() or char in _SAFE_NAME_ALLOWED else "_" for char in msp_name)  # WHY: fs-safe.


def _flatten_model_rows(collected: list[_OrgProcessedResult]) -> list[dict[str, Any]]:
    """Flatten per-org model rows into a combined list tagged with org name."""
    combined: list[dict[str, Any]] = []  # WHY: accumulator for combined-report rows.
    for entry in collected:  # WHY: iterate all successfully processed orgs.
        for row in entry.model_rows:  # WHY: expand each org's model rows into the combined list.
            combined.append(
                {
                    "Org": entry.safe_org,  # WHY: tag row with owning MSP-safe org name.
                    "Device Type": row["device_type"],  # WHY: preserve legacy Device Type column.
                    "Model": row.get("model", ""),  # WHY: legacy default for missing model.
                    "Count": row.get("count", 0),  # WHY: legacy default for missing count.
                }
            )
    return combined  # WHY: return flat rows to caller for printing + export.


def _flatten_version_rows(collected: list[_OrgProcessedResult]) -> list[dict[str, Any]]:
    """Flatten per-org firmware version rows into a combined list tagged with org name."""
    combined: list[dict[str, Any]] = []  # WHY: accumulator for combined-report rows.
    for entry in collected:  # WHY: iterate all successfully processed orgs.
        for row in entry.version_rows:  # WHY: expand each org's version rows into the combined list.
            combined.append(
                {
                    "Org": entry.safe_org,  # WHY: tag row with owning MSP-safe org name.
                    "Device Type": row["device_type"],  # WHY: preserve legacy Device Type column.
                    "Version": row.get("version", ""),  # WHY: legacy default for missing version.
                    "Count": row.get("count", 0),  # WHY: legacy default for missing count.
                }
            )
    return combined  # WHY: return flat rows to caller for printing + export.


def _print_combined_model_report(model_rows: list[dict[str, Any]]) -> None:
    """Print the combined MSP model count summary table to the operator."""
    model_table = PrettyTable()  # WHY: console table for operator display.
    model_table.field_names = ["Org", "Device Type", "Model", "Count"]  # WHY: stable column order for readers.
    for row in model_rows:  # WHY: add each combined row to the table.
        model_table.add_row([row["Org"], row["Device Type"], row["Model"], row["Count"]])  # WHY: match header.
    print(f"\n{_HEADER_DIVIDER}")  # WHY: preserve legacy divider before header.
    print("  Combined MSP Model Count Summary (All Orgs)")  # WHY: preserve legacy report header text.
    print(f"{_HEADER_DIVIDER}")  # WHY: preserve legacy divider after header.
    print(model_table)  # WHY: render the model summary table.


def _print_combined_version_report(version_rows: list[dict[str, Any]]) -> None:
    """Print the combined MSP firmware version summary table to the operator."""
    version_table = PrettyTable()  # WHY: console table for operator display.
    version_table.field_names = ["Org", "Device Type", "Version", "Count"]  # WHY: stable column order.
    for row in version_rows:  # WHY: add each combined row to the table.
        version_table.add_row([row["Org"], row["Device Type"], row["Version"], row["Count"]])  # WHY: match header.
    print(f"\n{_HEADER_DIVIDER}")  # WHY: preserve legacy divider before header.
    print("  Combined MSP Firmware Version Summary (All Orgs)")  # WHY: preserve legacy report header text.
    print(f"{_HEADER_DIVIDER}")  # WHY: preserve legacy divider after header.
    print(version_table)  # WHY: render the version summary table.


def _print_dispatch_menu() -> None:
    """Print the DEVICE INVENTORY SUMMARY interactive menu."""
    print("\n" + _MENU_DIVIDER)  # WHY: leading blank line + divider mimics legacy formatting.
    print("  DEVICE INVENTORY SUMMARY")  # WHY: preserve legacy menu title.
    print(_MENU_DIVIDER)  # WHY: closing divider before options.
    print("\n  Run mode:")  # WHY: introduce mode list to operator.
    print("    1. Current org only")  # WHY: mode 1 description.
    print("    2. Select a specific org from MSP list")  # WHY: mode 2 description.
    print("    3. All orgs in MSP (batch mode)")  # WHY: mode 3 description.
    print()  # WHY: trailing blank line before prompt.


def _prompt_dispatch_mode() -> str | None:
    """Prompt operator for menu mode. Return the raw string or None if input aborted."""
    try:
        return InputUtils.safe_input("  Select mode (1/2/3): ", context="inventory_dispatch").strip()  # WHY: read.
    except SystemExit:  # WHY: EOF/interrupt should exit the dispatcher cleanly.
        return None  # WHY: signal caller to short-circuit without printing errors.


class OrgDeviceInventoryMSPOrchestrator:
    """MSP selection, org enumeration, and combined reporting orchestration."""

    @staticmethod
    def _resolve_active_msp() -> dict[str, Any] | None:
        """Prompt for MSP selection when multiple are available."""
        if not msp_privileges:  # WHY: no privileges means the operator is not connected as MSP.
            print(_NO_MSP_MSG)  # WHY: show single-source no-privilege message.
            logging.warning("_resolve_active_msp called with no MSP privileges")  # WHY: trace.
            return None  # WHY: signal caller that MSP flow cannot proceed.
        if len(msp_privileges) == 1:  # WHY: single privilege short-circuits selection UI.
            active_msp = msp_privileges[0]  # WHY: only choice available.
            print(f"\n  Using MSP: {active_msp['msp_name']}")  # WHY: confirm auto-selection to operator.
            return active_msp  # WHY: skip prompt when only one option exists.
        _print_msp_choices(msp_privileges)  # WHY: display all MSP options before prompting.
        return _prompt_msp_choice(msp_privileges)  # WHY: delegate to prompt helper (may return None).

    @staticmethod
    def _fetch_org_list(active_msp: dict[str, Any]) -> list[dict[str, Any]]:
        """Retrieve all child organizations for the selected MSP."""
        if apisession is None:  # WHY: session may be missing if wiring skipped.
            print(_NO_API_SESSION_MSG)  # WHY: operator-facing session error.
            logging.error("_fetch_org_list: apisession is None")  # WHY: trace missing session.
            return []  # WHY: empty list lets callers short-circuit gracefully.
        msp_id = active_msp["msp_id"]  # WHY: required identifier for the mistapi call.
        msp_name = active_msp["msp_name"]  # WHY: friendly name for logs and operator messaging.
        logging.info("Fetching orgs for MSP %s (id=%s)", msp_name, msp_id)  # WHY: pre-call trace.
        print(f"\n  Fetching organizations for MSP: {msp_name}...")  # WHY: operator progress feedback.
        return _call_list_msp_orgs(msp_id, msp_name)  # WHY: delegate SDK call + normalisation.

    @staticmethod
    def run_single_msp_org(run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]]) -> None:
        """Mode 2: let user select one org from MSP list and run summary for that org."""
        active_msp = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()  # WHY: resolve or prompt MSP.
        if active_msp is None:  # WHY: resolver returns None on invalid/absent selection.
            return  # WHY: cannot proceed without an MSP.
        orgs_data = OrgDeviceInventoryMSPOrchestrator._fetch_org_list(active_msp)  # WHY: pull child orgs.
        if not orgs_data:  # WHY: nothing to select if MSP has no orgs.
            print(_NO_ORGS_MSG)  # WHY: consistent operator message.
            logging.info("run_single_msp_org: no orgs for MSP %s", active_msp["msp_id"])  # WHY: trace.
            return  # WHY: abort flow when there are no orgs.
        _print_org_choices(orgs_data)  # WHY: show numbered list to operator.
        choice_idx = _prompt_org_index(orgs_data)  # WHY: read validated 0-based index or None.
        if choice_idx is None:  # WHY: prompt helper already surfaced the error to operator.
            return  # WHY: nothing to run.
        chosen = orgs_data[choice_idx]  # WHY: fetch the selected org record.
        chosen_id = chosen.get("id", "")  # WHY: id is required for downstream inventory run.
        if not chosen_id:  # WHY: guard against malformed org records.
            print("X Selected org has no ID")  # WHY: operator-facing error for missing id.
            logging.error("Selected org record missing 'id': %s", chosen)  # WHY: log record for triage.
            return  # WHY: cannot invoke per-org runner without an id.
        logging.info("Running inventory for selected org: %s (%s)", chosen.get("name"), chosen_id)  # WHY: trace.
        run_for_org_fn(chosen_id)  # WHY: hand off to caller-supplied per-org runner.

    @staticmethod
    def _flatten_msp_version_rows(
        all_ver_data: list[tuple[str, list[dict]]],
    ) -> list[dict]:
        """Flatten per-org version row lists into a single list tagged with org name."""
        logging.debug("Flattening MSP version rows from %d orgs", len(all_ver_data))  # WHY: pre-pass trace.
        flat: list[dict] = []  # WHY: accumulator for combined rows across orgs.
        for safe_org, ver_rows in all_ver_data:  # WHY: iterate (org, rows) pairs.
            for row in ver_rows:  # WHY: each row is a model/version count for the given org.
                flat.append({**row, "org": safe_org})  # WHY: tag row with org for downstream pivoting.
        return flat  # WHY: return flat list to caller for pivot construction.

    @staticmethod
    def _build_msp_version_pivot(
        flat: list[dict],
    ) -> tuple[list[str], dict[tuple[str, str], dict]]:
        """Build (sorted versions list, (org, model) -> {device_type, version: count} pivot)."""
        versions = sorted({row["version"] for row in flat})  # WHY: deterministic version column order.
        pivot: dict[tuple, dict] = {}  # WHY: (org, model) -> per-version counts plus device_type.
        for row in flat:  # WHY: single pass to populate pivot cells.
            key = (row["org"], row["model"])  # WHY: compound key per pivot row.
            if key not in pivot:  # WHY: initialise on first sighting of this (org, model).
                pivot[key] = {"device_type": row.get("device_type", "")}  # WHY: seed with device_type.
            pivot[key][row["version"]] = row.get("count", 0)  # WHY: set per-version count cell.
        return versions, pivot  # WHY: caller needs both column order and pivot map.

    @staticmethod
    def _make_export_row(
        safe_org: str,
        model: str,
        ver_counts: dict[str, Any],
        versions: list[str],
        row_total: int,
    ) -> dict[str, Any]:
        """Assemble one CSV export row from a pivot cell."""
        export_row: dict[str, Any] = {
            "Org": safe_org,  # WHY: identify owning org in export.
            "Model": model,  # WHY: identify model in export.
            "Device Type": ver_counts.get("device_type", ""),  # WHY: preserve device_type column.
        }
        for version in versions:  # WHY: fill per-version cells in stable column order.
            export_row[version] = ver_counts.get(version, 0)  # WHY: default missing versions to zero.
        export_row["Total"] = row_total  # WHY: mirror displayed row total in CSV export.
        return export_row  # WHY: caller appends to export_rows list.

    @staticmethod
    def _append_pivot_row(
        accumulator: _PivotAccumulator,
        safe_org: str,
        model: str,
        ver_counts: dict[str, Any],
    ) -> None:
        """Emit one pivot row into the table + export rows and update column totals in-place."""
        versions = accumulator.versions  # WHY: pull canonical column order once for local reuse.
        row_counts = [ver_counts.get(version, 0) for version in versions]  # WHY: cell values in column order.
        row_total = sum(row_counts)  # WHY: per-row total across all versions.
        for version, count in zip(versions, row_counts, strict=True):  # WHY: update column totals in-place.
            accumulator.col_totals[version] += count  # WHY: accumulate per-version total.
        accumulator.table.add_row(
            [safe_org, model, ver_counts.get("device_type", ""), *row_counts, row_total]
        )  # WHY: append the pivot row to the table.
        accumulator.export_rows.append(
            OrgDeviceInventoryMSPOrchestrator._make_export_row(safe_org, model, ver_counts, versions, row_total)
        )  # WHY: append matching CSV row.

    @staticmethod
    def _build_msp_pivot_table_and_rows(
        versions: list[str],
        pivot: dict[tuple[str, str], dict],
    ) -> tuple[PrettyTable, list[dict], dict[str, int], int]:
        """Build PrettyTable + export rows + column totals from the pivot map."""
        table = PrettyTable()  # WHY: console table for operator display.
        table.field_names = ["Org", "Model", "Device Type"] + versions + ["Total"]  # WHY: stable column order.
        col_totals: dict[str, int] = {version: 0 for version in versions}  # WHY: per-version running totals.
        export_rows: list[dict] = []  # WHY: flattened CSV export rows for downstream writer.
        accumulator = _PivotAccumulator(
            table=table, export_rows=export_rows, col_totals=col_totals, versions=versions
        )  # WHY: bundle receivers so per-row helper has a narrow signature.
        for (safe_org, model), ver_counts in sorted(pivot.items()):  # WHY: sort by (org, model) for stable output.
            OrgDeviceInventoryMSPOrchestrator._append_pivot_row(
                accumulator, safe_org, model, ver_counts
            )  # WHY: delegate per-row emission + total accumulation to helper.
        total_row = [col_totals[v] for v in versions]  # WHY: precompute totals row cells once.
        grand_total = sum(total_row)  # WHY: sum precomputed totals.
        table.add_row(["TOTAL", "", "", *total_row, grand_total])  # WHY: append TOTAL summary row.
        return table, export_rows, col_totals, grand_total  # WHY: caller uses table + rows for print/export.

    @staticmethod
    def _print_and_export_pivot(
        table: PrettyTable,
        export_rows: list[dict],
        versions: list[str],
        filename: str,
    ) -> None:
        """Render pivot header/table then export CSV rows via DataExporter."""
        print(f"\n{_HEADER_DIVIDER}")  # WHY: preserve legacy divider before header.
        print("  Combined MSP Version Distribution per Model (All Orgs)")  # WHY: preserve legacy header text.
        print(f"{_HEADER_DIVIDER}")  # WHY: preserve legacy divider after header.
        print(table)  # WHY: render the pivot table to the operator.
        ordered_fields = ["Org", "Model", "Device Type"] + versions + ["Total"]  # WHY: CSV header column order.
        logging.info("Exporting combined MSP pivot to %s", filename)  # WHY: log before export side effect.
        DataExporter.write_with_format_selection(
            export_rows,
            filename,
            api_function_name="orgDeviceVersionPerModel",
            fieldnames=ordered_fields,
        )  # WHY: single writer call handles format selection prompt + file write.
        logging.debug("Combined MSP pivot export complete (%d rows)", len(export_rows))  # WHY: post-write trace.

    @staticmethod
    def _display_combined_pivot_and_export(
        all_ver_data: list[tuple[str, list[dict]]],
        filename: str,
    ) -> None:
        """Build combined version-per-model pivot across all MSP orgs and export it."""
        logging.info("Building combined MSP version pivot from %d org datasets", len(all_ver_data))  # WHY: entry log.
        flat = OrgDeviceInventoryMSPOrchestrator._flatten_msp_version_rows(all_ver_data)  # WHY: flatten per-org rows.
        if not flat:  # WHY: no rows -> nothing to pivot or export.
            print("  No version-per-model data available for combined pivot")  # WHY: preserve legacy message.
            logging.warning("_display_combined_pivot_and_export: no data to pivot")  # WHY: preserve legacy log.
            return  # WHY: abort when there is no data.
        versions, pivot = OrgDeviceInventoryMSPOrchestrator._build_msp_version_pivot(flat)  # WHY: build pivot map.
        table, export_rows, _col_totals, _grand_total = (
            OrgDeviceInventoryMSPOrchestrator._build_msp_pivot_table_and_rows(versions, pivot)
        )  # WHY: build PrettyTable + CSV rows in one pass.
        OrgDeviceInventoryMSPOrchestrator._print_and_export_pivot(
            table, export_rows, versions, filename
        )  # WHY: hand off print + export to helper.

    @staticmethod
    def _emit_combined_model(prefix: str, collected: list[_OrgProcessedResult]) -> None:
        """Flatten, print, and export the combined MSP model summary."""
        combined_model = _flatten_model_rows(collected)  # WHY: aggregate model rows across orgs.
        _print_combined_model_report(combined_model)  # WHY: render combined table to operator.
        DataExporter.write_with_format_selection(
            combined_model,
            f"{prefix}{_MODEL_EXPORT_SUFFIX}",
            api_function_name="orgDeviceModelSummary",
        )  # WHY: single writer handles CSV format selection + write.

    @staticmethod
    def _emit_combined_version(prefix: str, collected: list[_OrgProcessedResult]) -> None:
        """Flatten, print, and export the combined MSP firmware version summary."""
        combined_version = _flatten_version_rows(collected)  # WHY: aggregate firmware rows across orgs.
        _print_combined_version_report(combined_version)  # WHY: render combined table to operator.
        DataExporter.write_with_format_selection(
            combined_version,
            f"{prefix}{_VERSION_EXPORT_SUFFIX}",
            api_function_name="orgDeviceFirmwareSummary",
        )  # WHY: single writer handles CSV format selection + write.

    @staticmethod
    def _build_combined_reports(msp_safe_name: str, collected: list[dict[str, Any]]) -> None:
        """Generate combined MSP model/version and pivot reports from collected org outputs."""
        prefix = f"MSP_{msp_safe_name}"  # WHY: filename prefix shared by all combined reports.
        typed_collected = [_to_org_result(entry) for entry in collected]  # WHY: adapt legacy dicts to dataclass form.
        OrgDeviceInventoryMSPOrchestrator._emit_combined_model(prefix, typed_collected)  # WHY: model report step.
        OrgDeviceInventoryMSPOrchestrator._emit_combined_version(prefix, typed_collected)  # WHY: version report step.
        all_ver_data = [(entry.safe_org, entry.ver_per_model) for entry in typed_collected]  # WHY: pivot inputs.
        OrgDeviceInventoryMSPOrchestrator._display_combined_pivot_and_export(
            all_ver_data,
            f"{prefix}{_PIVOT_EXPORT_SUFFIX}",
        )  # WHY: build + export combined version-per-model pivot.
        print(f"\n  Combined MSP reports written with prefix: {prefix}_")  # WHY: operator confirmation footer.

    @staticmethod
    def _run_org_and_collect(
        child_org_id: str,
        child_org_name: str,
        run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]],
        collected: list[dict[str, Any]],
    ) -> None:
        """Invoke per-org runner and append its outputs. Log/surface errors on failure."""
        try:
            model_rows, version_rows, ver_per_model, safe_org = run_for_org_fn(child_org_id)  # WHY: invoke runner.
            collected.append(
                {
                    "safe_org": safe_org,  # WHY: filesystem-safe org name for combined reports.
                    "model_rows": model_rows,  # WHY: per-org model rows fed into combined model report.
                    "version_rows": version_rows,  # WHY: per-org firmware rows fed into combined version report.
                    "ver_per_model": ver_per_model,  # WHY: per-org rows fed into combined pivot.
                }
            )  # WHY: append raw dict. Adapter converts later.
        except Exception as error:  # WHY: one failing org should not abort the whole batch.
            print(f"    X Error processing {child_org_name}: {error}")  # WHY: surface error to operator.
            logging.exception("run_for_org failed for org %s: %s", child_org_id, error)  # WHY: full trace in log.

    @staticmethod
    def _process_org(
        org_record: dict[str, Any],
        idx: int,
        total: int,
        run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]],
        collected: list[dict[str, Any]],
    ) -> None:
        """Run per-org inventory for one org record and append the result on success."""
        child_org_id = org_record.get("id", "")  # WHY: required identifier for the per-org runner.
        child_org_name = org_record.get("name", child_org_id)  # WHY: display name for logs + operator UI.
        if not child_org_id:  # WHY: cannot invoke runner without an id.
            logging.warning("Skipping org record with no id: %s", org_record)  # WHY: log skipped record.
            return  # WHY: skip malformed record.
        print(f"  [{idx}/{total}] {child_org_name}")  # WHY: operator progress indicator.
        OrgDeviceInventoryMSPOrchestrator._run_org_and_collect(
            child_org_id, child_org_name, run_for_org_fn, collected
        )  # WHY: hand off actual execution + error handling to helper.

    @staticmethod
    def _process_orgs_batch(
        orgs_data: list[dict[str, Any]],
        run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]],
    ) -> list[dict[str, Any]]:
        """Iterate MSP orgs invoking the per-org runner and return successfully collected results."""
        collected: list[dict[str, Any]] = []  # WHY: accumulate per-org outputs for combined reports.
        total = len(orgs_data)  # WHY: used for progress display.
        for idx, org_record in enumerate(orgs_data, start=1):  # WHY: 1-based numbering for operator readability.
            OrgDeviceInventoryMSPOrchestrator._process_org(
                org_record, idx, total, run_for_org_fn, collected
            )  # WHY: delegate single-org run to helper.
        return collected  # WHY: batch results feed downstream combined-report logic.

    @staticmethod
    def execute_msp(run_for_org_fn: Callable[[str], tuple[list[dict], list[dict], list[dict], str]]) -> None:
        """Mode 3: run inventory summaries for all orgs under selected MSP."""
        logging.info("Starting MSP device inventory summary")  # WHY: entry log for batch flow.
        active_msp = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()  # WHY: pick MSP to iterate.
        if active_msp is None:  # WHY: resolver returned None -> cannot continue.
            return  # WHY: nothing to do.
        orgs_data = OrgDeviceInventoryMSPOrchestrator._fetch_org_list(active_msp)  # WHY: retrieve child orgs.
        if not orgs_data:  # WHY: batch mode needs at least one org.
            print(_NO_ORGS_MSG)  # WHY: consistent operator message.
            logging.info("execute_msp: no orgs found for MSP %s", active_msp["msp_id"])  # WHY: trace.
            return  # WHY: abort empty batch.
        print(f"  Found {len(orgs_data)} organizations.  Running inventory summary for each...\n")  # WHY: header.
        collected = OrgDeviceInventoryMSPOrchestrator._process_orgs_batch(orgs_data, run_for_org_fn)  # WHY: batch.
        logging.info("MSP inventory complete for %d orgs", len(orgs_data))  # WHY: post-batch trace.
        print(f"\nMSP inventory summary complete. Processed {len(orgs_data)} organizations.")  # WHY: operator footer.
        if len(collected) >= _MIN_ORGS_FOR_COMBINED:  # WHY: combined reports meaningful only for 2+ orgs.
            msp_safe_name = _sanitize_msp_name(active_msp.get("msp_name", "MSP"))  # WHY: filesystem-safe MSP name.
            OrgDeviceInventoryMSPOrchestrator._build_combined_reports(msp_safe_name, collected)  # WHY: combined step.
        else:
            logging.info("Skipping combined reports: fewer than 2 orgs processed successfully")  # WHY: trace skip.

    @staticmethod
    def dispatch(
        single_org_fn: Callable[[], None], select_org_fn: Callable[[], None], batch_fn: Callable[[], None]
    ) -> None:
        """Interactive dispatcher for menu operation 13 MSP modes."""
        if not msp_privileges:  # WHY: no MSP privileges -> single-org path only.
            single_org_fn()  # WHY: run current-org inventory directly.
            return  # WHY: skip menu display when there is no MSP choice.
        _print_dispatch_menu()  # WHY: show the three MSP mode options.
        mode = _prompt_dispatch_mode()  # WHY: read the operator's mode selection.
        if mode is None:  # WHY: EOF/interrupt from safe_input -> silent abort.
            return  # WHY: caller does not expect a value.
        if mode == "3":  # WHY: explicit match for batch mode.
            batch_fn()  # WHY: run all orgs under the MSP.
        elif mode == "2":  # WHY: explicit match for select-single-org mode.
            select_org_fn()  # WHY: prompt then run single org from MSP list.
        else:
            single_org_fn()  # WHY: mode 1 or fallback -> current-org inventory.


def _to_org_result(entry: dict[str, Any]) -> _OrgProcessedResult:
    """Adapt a legacy per-org dict into the frozen dataclass form used internally."""
    return _OrgProcessedResult(
        safe_org=entry["safe_org"],  # WHY: pull filesystem-safe org name.
        model_rows=entry["model_rows"],  # WHY: pull model rows for combined model report.
        version_rows=entry["version_rows"],  # WHY: pull version rows for combined version report.
        ver_per_model=entry["ver_per_model"],  # WHY: pull version-per-model rows for pivot.
    )
