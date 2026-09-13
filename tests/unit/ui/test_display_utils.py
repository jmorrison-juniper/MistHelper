"""Wave 7 P2 coverage for src/ui/display_utils.py (initiative #1018).

Covers every public + private branch of ``DisplayUtils``:

- ``dict_list_as_pretty_table``: empty input short-circuit, fields=None
  auto-derivation via ``DataProcessingUtils.get_unique_keys``, explicit fields,
  sortby honored + sortby ignored (invalid column) + sortby=None,
  row-cell default-empty when a dict is missing a field, debug log emission.
- ``_apply_sort_if_valid``: three branches (no sortby, invalid column, valid).
- ``_populate_table_rows``: rows populated in ``fields`` order with default "".
- ``create_progress_bar``: None, negative, 0, mid-range, exactly 100, above 100,
  and custom ``bar_length``.
- ``_clamp_progress_percentage``: None, negative, 0, mid, exactly 100, > 100.
- ``_render_progress_bar``: filled==bar_length, filled==0, filled in-between.

No live I/O, no MistHelper import; uses real PrettyTable objects and captures
debug log output via ``caplog``.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the rendered-table debug log.

import pytest  # WHY: parametrize + caplog fixtures.
from prettytable import PrettyTable  # WHY: verify real PrettyTable objects flow through helpers.

from src.ui.display_utils import DisplayUtils  # WHY: direct SUT import; class holds only static methods.


class TestApplySortIfValid:
    """Cover the three branches of the internal sort helper."""

    def test_no_sortby_leaves_table_untouched(self) -> None:
        """When sortby is None, the helper returns without setting table.sortby."""
        table = PrettyTable()  # WHY: real PrettyTable makes attribute checks trustworthy.
        table.field_names = ["a", "b"]  # WHY: minimal column set so PrettyTable is valid.
        DisplayUtils._apply_sort_if_valid(table, None, ["a", "b"])  # WHY: exercise no-sort branch.
        assert table.sortby is None  # WHY: no sort applied when sortby is None.

    def test_invalid_column_leaves_table_untouched(self) -> None:
        """A sortby column not present in fields is ignored silently."""
        table = PrettyTable()  # WHY: real PrettyTable for attribute check.
        table.field_names = ["a", "b"]  # WHY: baseline columns.
        DisplayUtils._apply_sort_if_valid(table, "missing", ["a", "b"])  # WHY: exercise invalid-column branch.
        assert table.sortby is None  # WHY: silent skip when sortby not in fields.

    def test_valid_column_sets_sortby(self) -> None:
        """A sortby column present in fields is applied to the table."""
        table = PrettyTable()  # WHY: real PrettyTable to observe attribute mutation.
        table.field_names = ["a", "b"]  # WHY: baseline columns include the sort key.
        DisplayUtils._apply_sort_if_valid(table, "a", ["a", "b"])  # WHY: exercise valid-column branch.
        assert table.sortby == "a"  # WHY: sort applied when column exists.


class TestPopulateTableRows:
    """Cover the row-append helper end-to-end."""

    def test_rows_populated_in_field_order_with_defaults(self) -> None:
        """Rows pull cells in fields order; missing keys default to empty string."""
        table = PrettyTable()  # WHY: real PrettyTable so ``rows`` reflects what was stored.
        table.field_names = ["a", "b", "c"]  # WHY: three columns so cell order is observable.
        data = [  # WHY: one row missing 'c', one row missing 'a' -- both should default to "".
            {"a": "1", "b": "2"},  # WHY: missing 'c'.
            {"b": "22", "c": "33"},  # WHY: missing 'a'.
        ]
        DisplayUtils._populate_table_rows(table, data, ["a", "b", "c"])  # WHY: exercise the SUT.
        # WHY: PrettyTable stores rows in ._rows after add_row (documented internal).
        assert table.rows == [["1", "2", ""], ["", "22", "33"]]  # WHY: default-empty applied per missing key.


class TestDictListAsPrettyTable:
    """Cover every branch of the public table-rendering helper."""

    def test_empty_data_is_noop_and_no_log(self, caplog: pytest.LogCaptureFixture) -> None:
        """An empty data list short-circuits before any log is emitted."""
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: verify no log fires either.
            DisplayUtils.dict_list_as_pretty_table([])  # WHY: exercise empty-data guard.
        assert caplog.records == []  # WHY: no debug log on the empty-data path.

    def test_auto_derives_fields_when_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """When fields=None, keys are derived via DataProcessingUtils.get_unique_keys."""
        data = [{"x": 1, "y": 2}, {"x": 3, "z": 4}]  # WHY: mixed keys force union derivation.
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: capture rendered-table log.
            DisplayUtils.dict_list_as_pretty_table(data)  # WHY: exercise fields=None branch.
        rendered = "\n".join(rec.message for rec in caplog.records)  # WHY: aggregate all messages.
        # WHY: every unique key across both dicts must appear as a column header.
        assert "x" in rendered  # WHY: shared key.
        assert "y" in rendered  # WHY: first-only key derived from union.
        assert "z" in rendered  # WHY: second-only key derived from union.

    def test_explicit_fields_and_valid_sortby(self, caplog: pytest.LogCaptureFixture) -> None:
        """Explicit fields drive column order; a valid sortby is honored."""
        data = [{"a": "2", "b": "y"}, {"a": "1", "b": "x"}]  # WHY: intentionally out-of-order.
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: capture rendered table.
            DisplayUtils.dict_list_as_pretty_table(data, fields=["a", "b"], sortby="a")  # WHY: valid sortby.
        rendered = "\n".join(rec.message for rec in caplog.records)  # WHY: aggregate log messages.
        assert "a" in rendered and "b" in rendered  # WHY: both explicit columns present.
        # WHY: the row starting with '1' must appear before the row starting with '2' after sorting.
        pos_1 = rendered.find(" 1 ")  # WHY: PrettyTable pads cells with spaces.
        pos_2 = rendered.find(" 2 ")  # WHY: locate the other row's cell.
        assert pos_1 != -1 and pos_2 != -1 and pos_1 < pos_2  # WHY: proves sortby actually reordered rows.

    def test_invalid_sortby_is_ignored_silently(self, caplog: pytest.LogCaptureFixture) -> None:
        """A sortby column not in fields is silently ignored, still renders."""
        data = [{"a": "1"}, {"a": "2"}]  # WHY: single-column data.
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: capture rendered table.
            DisplayUtils.dict_list_as_pretty_table(data, fields=["a"], sortby="does_not_exist")  # WHY: invalid.
        rendered = "\n".join(rec.message for rec in caplog.records)  # WHY: still rendered.
        assert "a" in rendered  # WHY: column header printed despite invalid sortby.

    def test_debug_log_emitted(self, caplog: pytest.LogCaptureFixture) -> None:
        """One debug log record is emitted per non-empty render."""
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: capture debug level.
            DisplayUtils.dict_list_as_pretty_table([{"k": "v"}])  # WHY: minimal non-empty data.
        assert len(caplog.records) == 1  # WHY: exactly one render -> one log record.
        assert caplog.records[0].levelno == logging.DEBUG  # WHY: emitted at DEBUG per SUT.


class TestClampProgressPercentage:
    """Cover every branch of the clamp helper."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (None, 0),  # WHY: None -> 0 sentinel.
            (-5, 0),  # WHY: negative -> 0 clamp.
            (0, 0),  # WHY: zero passes through.
            (50, 50),  # WHY: mid-range passes through.
            (100, 100),  # WHY: upper bound passes through.
            (150, 100),  # WHY: above max -> 100 clamp.
            (99.9, 99.9),  # WHY: float within range preserved verbatim.
        ],
    )
    def test_clamp_returns_expected(self, raw: float | None, expected: float) -> None:
        """Values are clamped into the inclusive 0..100 window."""
        assert DisplayUtils._clamp_progress_percentage(raw) == expected  # WHY: clamp contract.


class TestRenderProgressBar:
    """Cover the three branches of the low-level bar renderer."""

    def test_full_bar_is_all_equals(self) -> None:
        """When filled_length == bar_length, the bar is all '=' with no arrow."""
        assert DisplayUtils._render_progress_bar(10, 10) == "=" * 10  # WHY: fully-filled branch.

    def test_empty_bar_is_all_spaces(self) -> None:
        """When filled_length == 0, the bar is all spaces."""
        assert DisplayUtils._render_progress_bar(0, 10) == " " * 10  # WHY: empty branch.

    def test_partial_bar_has_arrow(self) -> None:
        """Intermediate fill uses '=…>' followed by trailing spaces."""
        assert DisplayUtils._render_progress_bar(4, 10) == "===" + ">" + " " * 6  # WHY: partial branch.


class TestCreateProgressBar:
    """Cover the public progress-bar helper end-to-end."""

    def test_none_yields_empty_bar_at_zero_percent(self) -> None:
        """None input clamps to 0% and renders an empty 20-wide bar."""
        assert DisplayUtils.create_progress_bar(None) == f"[{' ' * 20}]   0%"  # WHY: clamp + render + label.

    def test_negative_yields_zero_percent(self) -> None:
        """Negative input clamps to 0% (same rendering as None)."""
        assert DisplayUtils.create_progress_bar(-10) == f"[{' ' * 20}]   0%"  # WHY: clamp-to-zero contract.

    def test_full_progress_has_all_equals_and_100_percent(self) -> None:
        """100% renders a fully-filled bar without an arrow."""
        assert DisplayUtils.create_progress_bar(100) == f"[{'=' * 20}] 100%"  # WHY: full-bar rendering.

    def test_above_100_clamps_to_full(self) -> None:
        """Values above 100 clamp to 100 (fully-filled bar)."""
        assert DisplayUtils.create_progress_bar(250) == f"[{'=' * 20}] 100%"  # WHY: upper clamp contract.

    def test_mid_progress_shows_arrow(self) -> None:
        """Mid-range progress renders '=…>' followed by trailing spaces plus percent."""
        result = DisplayUtils.create_progress_bar(45)  # WHY: 45% * 20 == 9 filled.
        # WHY: 9 filled -> 8 '=' + '>' + 11 ' '; percent right-aligned to width 3.
        assert result == "[" + "=" * 8 + ">" + " " * 11 + "]  45%"  # WHY: exact glyphs and label spacing.

    def test_custom_bar_length_honored(self) -> None:
        """The bar_length parameter changes the total bar width."""
        result = DisplayUtils.create_progress_bar(50, bar_length=10)  # WHY: 50% * 10 == 5 filled.
        assert result == "[" + "=" * 4 + ">" + " " * 5 + "]  50%"  # WHY: 5 filled -> 4 '=' + '>' + 5 ' '.
