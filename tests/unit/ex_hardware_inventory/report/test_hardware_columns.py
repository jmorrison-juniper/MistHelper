"""Tests for the report columns and the spreadsheet guard."""

from __future__ import annotations

import pytest  # Parametrize the leading characters.

from src.operations.exporting.ex_hardware_inventory.report.columns import CellGuard, ReportColumns  # Units.

FIXED_COLUMNS = [
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
]  # The order that the report contract fixes.


class TestCellGuard:
    """A text value that a spreadsheet could run gets a leading apostrophe."""

    @pytest.mark.parametrize("lead", ["=", "+", "-", "@", "\t", "\r"])
    def test_each_dangerous_lead_gets_an_apostrophe(self, lead: str) -> None:
        """All six dangerous leading characters are neutralized."""
        assert CellGuard.clean(f"{lead}cmd") == f"'{lead}cmd"  # The apostrophe goes first.

    @pytest.mark.parametrize("value", ["", "EX-48P", "650-000001", "a=b", "x+y", "'=already", " =space first"])
    def test_other_values_stay_unchanged(self, value: str) -> None:
        """Only a dangerous first character matters, so every other value stays as it is."""
        assert CellGuard.clean(value) == value  # No change.


class TestReportColumns:
    """The column list has a fixed part and a sorted item part."""

    def test_fixed_columns_follow_the_contract_order(self) -> None:
        """The first fifteen columns never change."""
        assert list(ReportColumns.FIXED) == FIXED_COLUMNS  # The contract order.

    def test_item_columns_start_with_the_seven_preferred_fields(self) -> None:
        """The seven identity fields come first, even when no reply returned them."""
        columns = ReportColumns.item_columns([])  # No reply returned any field.
        assert columns == [
            "item_name",
            "item_version",
            "item_part_number",
            "item_serial_number",
            "item_model_number",
            "item_clei_code",
            "item_description",
        ]  # Only the preferred seven.

    def test_extra_fields_follow_in_sorted_order(self) -> None:
        """Fields that only some switches return come after the preferred seven, sorted."""
        columns = ReportColumns.item_columns(["vendor", "description", "attr_style", "disk_size", "name"])
        assert columns[7:] == ["item_attr_style", "item_disk_size", "item_vendor"]  # Sorted extras only.
        assert columns.count("item_description") == 1  # A preferred field is never repeated.

    def test_fieldnames_join_fixed_and_item_columns(self) -> None:
        """The full column list is the fixed part followed by the item part."""
        names = ReportColumns.fieldnames(["name", "disk_size"])  # One preferred and one extra field.
        assert names[:15] == FIXED_COLUMNS  # The fixed part first.
        assert names[-1] == "item_disk_size"  # The extra field last.
        assert len(names) == len(set(names))  # No column appears twice.

    def test_exempt_columns_are_the_enum_number_and_time_columns(self) -> None:
        """The guard skips columns that hold only fixed words, numbers, or a timestamp."""
        assert CellGuard.EXEMPT == frozenset(
            {"report_run_utc", "scope", "record_type", "collection_status", "item_level"}
        )  # Exactly these five.

    def test_a_field_that_matches_a_fixed_column_gets_a_suffix(self) -> None:
        """Fields named level, path, or type can never overwrite the fixed item columns."""
        assert ReportColumns.column_for("path") == "item_path_field"  # A clash with item_path.
        assert ReportColumns.column_for("level") == "item_level_field"  # A clash with item_level.
        assert ReportColumns.column_for("type") == "item_type_field"  # A clash with item_type.
        assert ReportColumns.column_for("vendor") == "item_vendor"  # No clash, so no suffix.
        names = ReportColumns.fieldnames(["path", "type"])  # A reply that returned both fields.
        assert len(names) == len(set(names))  # Every column name stays unique.
