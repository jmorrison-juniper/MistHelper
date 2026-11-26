"""Define the report columns and the spreadsheet guard.

Why:
    Two front ends write the same report, so the column list and the cell rules
    must live in one place. The guard exists because switch text is controlled by
    the device. A spreadsheet reads a cell that starts with an equals sign as a
    formula, so the guard puts an apostrophe in front of such a cell.
"""

from __future__ import annotations

import logging  # Record each column build for the operator trace.
from collections.abc import Iterable  # Accept any collection of field names.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class CellGuard:
    """Stop a spreadsheet from running a text value as a formula."""

    DANGEROUS = ("=", "+", "-", "@", "\t", "\r")  # The leading characters that a spreadsheet reads as a formula.
    EXEMPT = frozenset({"report_run_utc", "scope", "record_type", "collection_status", "item_level"})  # Fixed words.

    @classmethod
    def clean(cls, value: str) -> str:
        """Return the value with a leading apostrophe when it starts with a dangerous character.

        Args:
            value: One cell text.

        Returns:
            The same text, or the text with a leading apostrophe.
        """
        if value.startswith(cls.DANGEROUS):  # Only the first character decides whether a formula can run.
            return "'" + value  # The apostrophe makes the spreadsheet show the text as it is.
        return value  # Every other value is safe.


class ReportColumns:
    """Hold the fixed columns and build the item columns."""

    FIXED = (
        "report_run_utc",
        "scope",
        "org_id",
        "org_name",
        "site_id",
        "site_name",
        "device_id",
        "device_name",
        "record_type",
        "collection_status",
        "collection_detail",
        "device_cli_banner",
        "item_level",
        "item_path",
        "item_type",
    )  # The order that the report contract fixes.
    PREFERRED = (
        "name",
        "version",
        "part_number",
        "serial_number",
        "model_number",
        "clei_code",
        "description",
    )  # The seven identity fields that come first, even when no reply returned them.

    @classmethod
    def column_for(cls, field_name: str) -> str:
        """Return the column name of one item field.

        A field that would take the name of a fixed column gets a suffix, so it can never overwrite one.
        """
        column = f"item_{field_name}"  # Prefix each item field so it is easy to find.
        return f"{column}_field" if column in cls.FIXED else column  # Keep a fixed column safe from a clash.

    @classmethod
    def item_columns(cls, field_names: Iterable[str]) -> list[str]:
        """Return the item columns: the preferred seven first, then every other field in sorted order."""
        extras = sorted(set(field_names) - set(cls.PREFERRED))  # Sort the other fields for a stable file.
        return [cls.column_for(name) for name in (*cls.PREFERRED, *extras)]  # Preferred fields never repeat.

    @classmethod
    def fieldnames(cls, field_names: Iterable[str]) -> list[str]:
        """Return the full column list: the fixed columns followed by the item columns."""
        columns = [*cls.FIXED, *cls.item_columns(field_names)]  # One list for every writer.
        logger.debug("Built %d report columns", len(columns))  # Log the result size.
        return columns  # Hand back the ordered list.
