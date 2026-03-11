"""Unit tests for DataProcessingUtils pure functions.

Duplicates flatten_dict(), escape_multiline(), and get_unique_keys() from
MistHelper.py to avoid import side effects (research.md R1 pattern).
"""

from typing import Any, Dict

import pytest


# ---------------------------------------------------------------------------
# Duplicated pure functions (R1: avoid MistHelper.py import side effects)
# ---------------------------------------------------------------------------
def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Mirror of DataProcessingUtils.flatten_dict() from MistHelper.py."""
    items = []
    for k, v in d.items():
        k_str = str(k)
        new_key = f"{parent_key}{sep}{k_str}" if parent_key else k_str
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if all(isinstance(i, dict) for i in v):
                for idx, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{idx}", sep=sep).items())
            else:
                items.append((new_key, ','.join(map(str, v))))
        else:
            items.append((new_key, v))
    return dict(items)


def get_unique_keys(data):
    """Mirror of DataProcessingUtils.get_unique_keys() from MistHelper.py."""
    fields = set()
    for entry in data:
        fields.update(entry.keys())
    return sorted(str(f) for f in fields)


def escape_multiline(data):
    """Mirror of DataProcessingUtils.escape_multiline() from MistHelper.py."""
    for entry in data:
        for key, value in entry.items():
            if isinstance(value, list):
                entry[key] = ','.join(map(str, value))
            elif isinstance(value, str):
                entry[key] = value.replace('\n', '\\n').replace('\r', '')
    return data


# ---------------------------------------------------------------------------
# Tests: flatten_dict
# ---------------------------------------------------------------------------
class TestFlattenDict:
    """Tests for the flatten_dict utility function."""

    def test_simple_dict(self):
        result = flatten_dict({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_nested_dict(self):
        result = flatten_dict({"a": {"b": 1, "c": 2}})
        assert result == {"a_b": 1, "a_c": 2}

    def test_deeply_nested_dict(self):
        result = flatten_dict({"a": {"b": {"c": 3}}})
        assert result == {"a_b_c": 3}

    def test_list_of_dicts(self):
        result = flatten_dict({"items": [{"x": 1}, {"x": 2}]})
        assert result == {"items_0_x": 1, "items_1_x": 2}

    def test_non_dict_list(self):
        result = flatten_dict({"tags": ["red", "blue"]})
        assert result == {"tags": "red,blue"}

    def test_empty_dict(self):
        result = flatten_dict({})
        assert result == {}

    def test_none_value(self):
        result = flatten_dict({"a": None})
        assert result == {"a": None}

    def test_mixed_types(self):
        result = flatten_dict({"a": 1, "b": {"c": "hello"}, "d": [1, 2]})
        assert result == {"a": 1, "b_c": "hello", "d": "1,2"}

    def test_custom_separator(self):
        result = flatten_dict({"a": {"b": 1}}, sep='.')
        assert result == {"a.b": 1}

    def test_parent_key(self):
        result = flatten_dict({"b": 1}, parent_key="a")
        assert result == {"a_b": 1}

    def test_empty_list(self):
        # Empty list passes all(isinstance(i, dict)) vacuously, key is dropped
        result = flatten_dict({"items": []})
        assert result == {}

    def test_numeric_keys(self):
        result = flatten_dict({1: "one", 2: "two"})
        assert result == {"1": "one", "2": "two"}


# ---------------------------------------------------------------------------
# Tests: get_unique_keys
# ---------------------------------------------------------------------------
class TestGetUniqueKeys:
    """Tests for the get_unique_keys utility function."""

    def test_single_dict(self):
        result = get_unique_keys([{"a": 1, "b": 2}])
        assert result == ["a", "b"]

    def test_multiple_dicts(self):
        result = get_unique_keys([{"a": 1}, {"b": 2}, {"a": 3, "c": 4}])
        assert result == ["a", "b", "c"]

    def test_empty_list(self):
        result = get_unique_keys([])
        assert result == []

    def test_empty_dicts(self):
        result = get_unique_keys([{}, {}])
        assert result == []

    def test_sorted_output(self):
        result = get_unique_keys([{"z": 1, "a": 2, "m": 3}])
        assert result == ["a", "m", "z"]


# ---------------------------------------------------------------------------
# Tests: escape_multiline
# ---------------------------------------------------------------------------
class TestEscapeMultiline:
    """Tests for the escape_multiline utility function."""

    def test_newline_escaped(self):
        data = [{"text": "line1\nline2"}]
        result = escape_multiline(data)
        assert result[0]["text"] == "line1\\nline2"

    def test_carriage_return_removed(self):
        data = [{"text": "line1\r\nline2"}]
        result = escape_multiline(data)
        assert result[0]["text"] == "line1\\nline2"

    def test_list_joined(self):
        data = [{"tags": ["a", "b", "c"]}]
        result = escape_multiline(data)
        assert result[0]["tags"] == "a,b,c"

    def test_no_change_for_simple_string(self):
        data = [{"text": "hello world"}]
        result = escape_multiline(data)
        assert result[0]["text"] == "hello world"

    def test_non_string_values_unchanged(self):
        data = [{"count": 42, "active": True}]
        result = escape_multiline(data)
        assert result[0]["count"] == 42
        assert result[0]["active"] is True
