"""Wave 6 P2 coverage for src.data.data_processing_utils.DataProcessingUtils.

Imports the real class from src.data.data_processing_utils (pure module, no side
effects) to exercise the branches missed by the existing ``tests/unit/test_data_processing.py``
(which duplicates the functions inline per R1). All tests are pure Python -- no
mocks are required because DataProcessingUtils has zero runtime dependencies.

Covers missing lines: 41-42 (scalar list join), 52-53 (nested dict recursion),
70-71 (non-dict skip), 91-97 (parse-string try/except), 103-104 (dict merge),
108-112 (list-of-dicts index), 117 (_is_list_of_dicts), 122-127
(convert_list_values_to_strings), 147 (escape_multiline list branch).
"""

from __future__ import annotations  # WHY: PEP 604 unions for optional typing in tests.

from typing import Any  # WHY: Any typing for the intentionally mixed test input.

from src.data.data_processing_utils import DataProcessingUtils  # Real class under test.


class TestFlattenDict:
    """Cover the recursive/list branches of DataProcessingUtils.flatten_dict."""

    def test_simple_scalar_dict_passthrough(self) -> None:
        """Scalar fields survive unchanged when no nesting is present."""
        # WHY: baseline scalar path exercises the final append branch.
        result = DataProcessingUtils.flatten_dict({"a": 1, "b": "x"})  # Invoke real classifier.
        assert result == {"a": 1, "b": "x"}  # Scalars retained verbatim.

    def test_nested_dict_uses_recursive_branch(self) -> None:
        """Nested dicts recurse through the isinstance(v, dict) branch (lines 52-53)."""
        # WHY: hits the recursion branch of flatten_dict itself, not the entry helper.
        result = DataProcessingUtils.flatten_dict({"outer": {"inner": 1}})  # Nested-dict input.
        assert result == {"outer_inner": 1}  # Underscore-joined key path.

    def test_scalar_list_joins_as_csv(self) -> None:
        """Non-dict list values collapse to a comma-joined string (lines 41-42)."""
        # WHY: forces _flatten_list_value to take the scalar-list branch.
        result = DataProcessingUtils.flatten_dict({"tags": ["a", "b"]})  # Scalar list of strings.
        assert result == {"tags": "a,b"}  # CSV-joined via map(str, ...).

    def test_list_of_dicts_gets_index_keys(self) -> None:
        """List-of-dicts entries get numeric index suffixes."""
        # WHY: covers the all(isinstance ... dict) branch of _flatten_list_value.
        result = DataProcessingUtils.flatten_dict({"items": [{"x": 1}, {"x": 2}]})  # List of dicts.
        assert result == {"items_0_x": 1, "items_1_x": 2}  # Indexed underscore keys.

    def test_custom_separator_and_parent_key(self) -> None:
        """Both parent_key and sep parameters propagate through recursion."""
        # WHY: exercises both keyword args together.
        result = DataProcessingUtils.flatten_dict({"b": {"c": 1}}, parent_key="a", sep=".")  # Dot-sep.
        assert result == {"a.b.c": 1}  # Dot-joined, parent-prefixed.


class TestFlattenNestedFields:
    """Cover DataProcessingUtils.flatten_nested_fields entry-level dispatch."""

    def test_non_dict_entries_are_skipped(self) -> None:
        """Non-dict input records get logged and skipped (lines 70-71)."""
        # WHY: forces the isinstance(entry, dict) guard False branch.
        mixed_input: list[Any] = [
            {"a": 1},
            "bogus",
            {"b": 2},
        ]  # WHY: Any typing to satisfy mypy strict on the intentionally mixed payload.
        result = DataProcessingUtils.flatten_nested_fields(mixed_input)  # Trigger dispatch.
        assert result == [{"a": 1}, {"b": 2}]  # String entry dropped, others preserved.

    def test_stringified_json_list_of_dicts_expands(self) -> None:
        """Stringified JSON list-of-dicts values get parsed and indexed (lines 108-112)."""
        # WHY: string starts with "[" so _parse_stringified_value returns a list; _flatten_value_into
        # then routes through the _is_list_of_dicts True branch.
        entry = {"items": '[{"x": 1}, {"x": 2}]'}  # JSON-encoded list of dicts.
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Trigger parse + expansion.
        assert result == [{"items_0_x": 1, "items_1_x": 2}]  # Indexed under items_<idx>.

    def test_stringified_dict_value_merges_into_entry(self) -> None:
        """Stringified dict values are parsed and flattened into the entry (lines 103-104)."""
        # WHY: forces _flatten_value_into to take the isinstance(value, dict) branch.
        entry = {"cfg": "{'a': 1, 'b': 2}"}  # Python-literal string (ast.literal_eval succeeds).
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Trigger parse + merge.
        assert result == [{"cfg_a": 1, "cfg_b": 2}]  # Merged with cfg_ prefix.

    def test_stringified_json_dict_fallback_via_json_loads(self) -> None:
        """JSON-only strings fall back to json.loads when ast.literal_eval fails (lines 94-95)."""
        # WHY: JSON boolean `true` is not a Python literal -> ast fails, json succeeds.
        entry = {"cfg": '{"enabled": true}'}  # JSON dict with boolean.
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Trigger fallback path.
        assert result == [{"cfg_enabled": True}]  # Boolean parsed and merged.

    def test_stringified_value_unparseable_returns_string_unchanged(self) -> None:
        """Malformed JSON/literal returns the original string (line 97)."""
        # WHY: both ast.literal_eval and json.loads raise -> value passes through as string.
        entry = {"cfg": "{not valid json or literal"}  # Starts with '{' but unparseable.
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Trigger both parses.
        # Scalar path takes over: the raw string survives as-is under the original key.
        assert result == [{"cfg": "{not valid json or literal"}]  # Original string preserved.

    def test_stringified_list_of_scalars_joined_as_csv(self) -> None:
        """Parsed scalar lists join into a CSV string (line 112)."""
        # WHY: exercises _flatten_value_into fall-through when list is NOT list-of-dicts.
        entry = {"tags": "['red', 'blue']"}  # Python literal, list of strings.
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Trigger parse + join.
        assert result == [{"tags": "red,blue"}]  # CSV-joined scalar list.

    def test_non_string_value_passthrough(self) -> None:
        """Non-string scalars are not touched by _parse_stringified_value."""
        # WHY: exercise the early return on isinstance(value, str) False.
        entry = {"n": 42, "s": None}  # Scalars not qualifying for parse attempt.
        result = DataProcessingUtils.flatten_nested_fields([entry])  # Scalar merge path.
        assert result == [{"n": 42, "s": None}]  # Values preserved intact.


class TestIsListOfDicts:
    """Cover the _is_list_of_dicts internal helper (line 117)."""

    def test_all_dicts_returns_true(self) -> None:
        """Empty list vacuously satisfies all-dict check; homogeneous list too."""
        # WHY: single-line helper needs direct exercise to hit line 117.
        assert DataProcessingUtils._is_list_of_dicts([{"a": 1}, {"b": 2}]) is True  # Homogeneous.

    def test_mixed_types_returns_false(self) -> None:
        """List with a non-dict element returns False."""
        # WHY: exercise the False branch of the all() short-circuit.
        assert DataProcessingUtils._is_list_of_dicts([{"a": 1}, "oops"]) is False  # Mixed.


class TestConvertListValuesToStrings:
    """Cover DataProcessingUtils.convert_list_values_to_strings (lines 122-127)."""

    def test_list_values_join_as_csv(self) -> None:
        """List values become comma-joined strings in place."""
        # WHY: exercises the isinstance(value, list) True branch.
        data = [{"tags": ["a", "b", "c"]}]  # Single record with a list.
        result = DataProcessingUtils.convert_list_values_to_strings(data)  # In-place mutation.
        assert result == [{"tags": "a,b,c"}]  # CSV-joined.

    def test_tuple_and_set_values_also_convert(self) -> None:
        """Tuple and set values also become CSV strings (branch coverage)."""
        # WHY: the isinstance check accepts tuple and set, not just list.
        data = [{"t": ("a", "b"), "s": {"z"}}]  # Tuple + one-element set (deterministic).
        result = DataProcessingUtils.convert_list_values_to_strings(data)  # Convert both.
        assert result[0]["t"] == "a,b"  # Tuple joined.
        assert result[0]["s"] == "z"  # Single-element set joined.

    def test_scalar_values_pass_through(self) -> None:
        """Non-collection values are left untouched."""
        # WHY: exercises the isinstance False fall-through.
        data = [{"n": 42, "s": "hello"}]  # Only scalars.
        result = DataProcessingUtils.convert_list_values_to_strings(data)  # No conversions.
        assert result == [{"n": 42, "s": "hello"}]  # Unchanged.


class TestGetUniqueKeys:
    """Cover the get_unique_keys helper."""

    def test_returns_sorted_union_of_keys(self) -> None:
        """Union of dict keys is returned sorted and stringified."""
        # WHY: baseline helper for CSV header composition.
        data = [{"b": 1}, {"a": 2, "c": 3}]  # Overlapping / disjoint keys.
        assert DataProcessingUtils.get_unique_keys(data) == ["a", "b", "c"]  # Sorted union.

    def test_empty_input_returns_empty_list(self) -> None:
        """Empty input returns an empty list."""
        # WHY: edge case for defensive callers.
        assert DataProcessingUtils.get_unique_keys([]) == []  # Empty result.


class TestEscapeMultiline:
    """Cover DataProcessingUtils.escape_multiline including list branch (line 147)."""

    def test_newline_and_cr_escaped(self) -> None:
        """String values get newline escaped and CR stripped."""
        # WHY: exercises the isinstance(value, str) branch.
        data = [{"txt": "a\r\nb"}]  # Windows-style line ending.
        result = DataProcessingUtils.escape_multiline(data)  # Escape in place.
        assert result[0]["txt"] == "a\\nb"  # CR removed, LF escaped.

    def test_list_value_joined_as_csv(self) -> None:
        """List values are joined as CSV strings (line 147)."""
        # WHY: exercises the isinstance(value, list) True branch.
        data = [{"tags": ["red", "blue"]}]  # Record with list value.
        result = DataProcessingUtils.escape_multiline(data)  # Join list to CSV.
        assert result[0]["tags"] == "red,blue"  # Comma-joined.

    def test_non_string_non_list_values_unchanged(self) -> None:
        """Scalars other than strings/lists survive untouched."""
        # WHY: exercises the fall-through of both isinstance branches.
        data = [{"n": 42, "b": True}]  # Non-string, non-list scalars.
        result = DataProcessingUtils.escape_multiline(data)  # No mutation expected.
        assert result == [{"n": 42, "b": True}]  # Unchanged.
