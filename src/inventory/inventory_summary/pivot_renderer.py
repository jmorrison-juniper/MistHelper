"""Renders the version-per-model pivot table and exports it via DataExporter."""  # File docstring

from __future__ import annotations  # Defer annotation evaluation. Cheap forward refs

import logging  # Structured action logging

from prettytable import PrettyTable  # Terminal-friendly ASCII table rendering

from src.inventory import (  # Parent module exposes DataExporter global
    org_device_inventory_summary as _parent,
)


class PivotRenderer:  # Decomposed replacement for the original `_display_pivot_and_export` helper
    """Decomposed replacement for the original `_display_pivot_and_export` helper."""

    @staticmethod
    def render(rows: list[dict], filename: str) -> None:  # Public entrypoint
        """Render the combined version-per-model pivot table and export it."""
        logging.info(
            "Rendering version-per-model pivot for %d rows -> %s", len(rows), filename
        )  # Trace orchestrator entry
        models, versions, model_type, pivot = PivotRenderer._compute_pivot(rows)  # Build pivot
        table, export_rows, grand_total = PivotRenderer._build_table(  # Construct PrettyTable + export rows
            models,
            versions,
            model_type,
            pivot,
        )
        PivotRenderer._print_table(table)  # User-visible output preserves the original banner / formatting
        PivotRenderer._emit_export(
            export_rows, versions, filename
        )  # Hand off to DataExporter with stable field ordering
        logging.debug(
            "Pivot rendered: %d models x %d versions, grand_total=%d",
            len(models),
            len(versions),
            grand_total,
        )  # Trace outcome

    @staticmethod
    def _populate_pivot(  # Helper to take the outer for-loop out of _compute_pivot
        rows: list[dict], pivot: dict[str, dict[str, int]]
    ) -> None:
        """Walk each input row and write its count into ``pivot[model][version]``."""
        for row in rows:  # Fold every input row into the (model, version) cell
            pivot[row["model"]][row["version"]] = row.get(
                "count", 0
            )  # Last write wins. Input data has no duplicate cells

    @staticmethod
    def _compute_pivot(  # Computes axes + nested counts
        rows: list[dict],
    ) -> tuple[list[str], list[str], dict[str, str], dict[str, dict[str, int]]]:
        """Compute sorted axes plus a nested {model: {version: count}} pivot."""
        models = sorted({row["model"] for row in rows})  # Sorted model axis -> row order
        versions = sorted({row["version"] for row in rows})  # Sorted version axis -> column order
        model_type: dict[str, str] = {
            row["model"]: row["device_type"] for row in rows
        }  # Look-up for export Device Type column
        pivot: dict[str, dict[str, int]] = {
            model: {} for model in models
        }  # Pre-allocate model buckets so .get() works downstream
        PivotRenderer._populate_pivot(rows, pivot)  # Delegate per-row counts (keeps this fn CC<=5)
        return models, versions, model_type, pivot  # Hand back as tuple so callers stay stateless

    @staticmethod
    def _update_row_and_columns(  # Computes per-row dense counts and accumulates per-column totals
        model: str,
        versions: list[str],
        pivot: dict[str, dict[str, int]],
        col_totals: dict[str, int],
    ) -> tuple[list[int], int]:
        """Return ``(row_counts, row_total)`` and accumulate ``col_totals`` in place."""
        row_counts = [pivot[model].get(version, 0) for version in versions]  # Dense per-version counts for this model
        row_total = sum(row_counts)  # Per-row total used by table footer and export rows
        for version, count in zip(versions, row_counts, strict=True):  # Update column totals
            col_totals[version] += count  # Accumulate this row's contribution to each version column
        return row_counts, row_total  # Caller consumes both immediately

    @staticmethod
    def _build_table(  # Builds the PrettyTable + parallel export rows
        models: list[str],
        versions: list[str],
        model_type: dict[str, str],
        pivot: dict[str, dict[str, int]],
    ) -> tuple[PrettyTable, list[dict], int]:
        """Build the PrettyTable instance, export rows, and grand total."""
        table = PrettyTable()  # PrettyTable handles human-readable column alignment
        table.field_names = (
            ["Model"] + versions + ["Total"]
        )  # Header columns: model label + each version + per-row total
        col_totals: dict[str, int] = {version: 0 for version in versions}  # Running per-column totals for the footer
        export_rows: list[dict] = []  # Accumulator for the CSV/SQLite export contract
        for model in models:  # One iteration per pivot row
            row_counts, row_total = PivotRenderer._update_row_and_columns(
                model, versions, pivot, col_totals
            )  # Delegate inner accumulation
            table.add_row([model] + row_counts + [row_total])  # Emit one PrettyTable row
            export_rows.append(
                PivotRenderer._build_export_row(model, model_type, versions, pivot, row_total)
            )  # Mirror as dict for exporter
        col_total_values = [col_totals[version] for version in versions]  # Footer column totals in display order
        grand_total = sum(col_total_values)  # Bottom-right grand total cell
        table.add_row(["TOTAL"] + col_total_values + [grand_total])  # Append footer row
        return table, export_rows, grand_total  # Hand back artifacts for printing and export

    @staticmethod
    def _build_export_row(  # Mirrors one model row for CSV output
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
        return export_row  # Caller appends to the export list

    @staticmethod
    def _print_table(table: PrettyTable) -> None:  # Renders the legacy ASCII banner + table
        """Print the rendered table with the original banner verbatim."""
        # WHY: Top banner preserved exactly from the legacy implementation.
        logging.info("\n%s", "=" * 62)
        # WHY: Header label preserved verbatim for NOC familiarity.
        logging.info("  Version Distribution per Model (All Device Types)")
        # WHY: Bottom of top banner preserved exactly from the legacy implementation.
        logging.info("%s", "=" * 62)
        # WHY: PrettyTable renders to its built-in ASCII grid format.
        logging.info("%s", table)

    @staticmethod
    def _emit_export(  # Delegates persistence to DataExporter with stable column order
        export_rows: list[dict], versions: list[str], filename: str
    ) -> None:
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
        logging.debug("Pivot export complete: %s", filename)  # Trace successful disk / DB write
