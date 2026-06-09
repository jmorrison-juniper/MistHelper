"""Renders the version-per-model pivot table and exports it via DataExporter."""

from __future__ import annotations

import logging

from prettytable import PrettyTable

from src.inventory import org_device_inventory_summary as _parent  # Parent module exposes DataExporter global


class PivotRenderer:
    """Decomposed replacement for the original `_display_pivot_and_export` helper."""

    @staticmethod
    def render(rows: list[dict], filename: str) -> None:
        """Render the combined version-per-model pivot table and export it."""
        logging.info(
            "Rendering version-per-model pivot for %d rows -> %s", len(rows), filename
        )  # Trace orchestrator entry
        models, versions, model_type, pivot = PivotRenderer._compute_pivot(rows)  # Build the in-memory pivot structure
        table, export_rows, grand_total = PivotRenderer._build_table(  # Construct PrettyTable + export rows from pivot
            models,
            versions,
            model_type,
            pivot,
        )
        PivotRenderer._print_table(table)  # User-visible output preserves the original banner / formatting verbatim
        PivotRenderer._emit_export(
            export_rows, versions, filename
        )  # Hand off to DataExporter with stable field ordering
        logging.debug(
            "Pivot rendered: %d models x %d versions, grand_total=%d", len(models), len(versions), grand_total
        )  # Trace outcome

    @staticmethod
    def _compute_pivot(rows: list[dict]) -> tuple[list[str], list[str], dict[str, str], dict[str, dict[str, int]]]:
        """Compute sorted axes plus a nested {model: {version: count}} pivot."""
        models = sorted({row["model"] for row in rows})  # Sorted model axis becomes the table row order
        versions = sorted({row["version"] for row in rows})  # Sorted version axis becomes the table column order
        model_type: dict[str, str] = {
            row["model"]: row["device_type"] for row in rows
        }  # Look-up for export Device Type column
        pivot: dict[str, dict[str, int]] = {
            model: {} for model in models
        }  # Pre-allocate model buckets so .get() works downstream
        for row in rows:  # Fold every input row into the (model, version) cell
            pivot[row["model"]][row["version"]] = row.get(
                "count", 0
            )  # Last write wins; input data has no duplicate cells
        return models, versions, model_type, pivot  # Hand back as tuple so callers stay stateless

    @staticmethod
    def _build_table(
        models: list[str],
        versions: list[str],
        model_type: dict[str, str],
        pivot: dict[str, dict[str, int]],
    ) -> tuple[PrettyTable, list[dict], int]:
        """Build the PrettyTable instance, export rows, and grand total."""
        table = PrettyTable()  # PrettyTable handles human-readable column alignment for the terminal
        table.field_names = (
            ["Model"] + versions + ["Total"]
        )  # Header columns: model label + each version + per-row total
        col_totals: dict[str, int] = {version: 0 for version in versions}  # Running per-column totals for the footer
        export_rows: list[dict] = []  # Accumulator for the CSV/SQLite export contract
        for model in models:  # One iteration per pivot row
            row_counts = [
                pivot[model].get(version, 0) for version in versions
            ]  # Dense per-version counts for this model
            row_total = sum(row_counts)  # Per-row total used both in the table footer column and the export
            for version, count in zip(versions, row_counts, strict=True):  # Update column totals as we walk row counts
                col_totals[version] += count  # Accumulate this row's contribution to each version column
            table.add_row([model] + row_counts + [row_total])  # Emit one PrettyTable row in display order
            export_rows.append(
                PivotRenderer._build_export_row(model, model_type, versions, pivot, row_total)
            )  # Mirror as dict for exporter
        col_total_values = [col_totals[version] for version in versions]  # Footer column totals in display order
        grand_total = sum(col_total_values)  # Grand total cell in the bottom-right of the table
        table.add_row(["TOTAL"] + col_total_values + [grand_total])  # Append the footer row preserving original look
        return table, export_rows, grand_total  # Hand back artifacts for printing and export

    @staticmethod
    def _build_export_row(
        model: str,
        model_type: dict[str, str],
        versions: list[str],
        pivot: dict[str, dict[str, int]],
        row_total: int,
    ) -> dict:
        """Build a single export-row dict shaped like the legacy CSV output."""
        export_row: dict = {
            "Model": model,
            "Device Type": model_type.get(model, ""),
        }  # First two columns mirror legacy output
        for version in versions:  # One column per version in the same order as the table
            export_row[version] = pivot[model].get(version, 0)  # Missing cells become 0 to keep CSV columns dense
        export_row["Total"] = row_total  # Final column repeats the per-row total computed above
        return export_row

    @staticmethod
    def _print_table(table: PrettyTable) -> None:
        """Print the rendered table with the original banner verbatim."""
        print(f"\n{'=' * 62}")  # Top banner preserved exactly from the legacy implementation
        print(
            "  Version Distribution per Model (All Device Types)"
        )  # Header label preserved verbatim for NOC familiarity
        print(f"{'=' * 62}")  # Bottom of top banner preserved exactly from the legacy implementation
        print(table)  # PrettyTable renders to its built-in ASCII grid format

    @staticmethod
    def _emit_export(export_rows: list[dict], versions: list[str], filename: str) -> None:
        """Hand the rendered export rows to DataExporter with stable field ordering."""
        ordered_fields = (
            ["Model", "Device Type"] + versions + ["Total"]
        )  # Preserve column order in CSV exactly as it appeared in legacy
        logging.info(
            "Exporting %d pivot rows to %s", len(export_rows), filename
        )  # Log before potentially slow disk / database write
        # Delegate format selection (CSV/SQLite/Arango) to the parent exporter
        _parent.DataExporter.write_with_format_selection(
            export_rows,
            filename,
            api_function_name="orgDeviceVersionPerModel",  # PK strategy registered under this synthetic endpoint name
            fieldnames=ordered_fields,
        )
        logging.debug("Pivot export complete: %s", filename)  # Trace successful disk / DB write for ops visibility
