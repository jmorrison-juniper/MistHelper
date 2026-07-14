"""Unit tests for FilterOperatorEngine (initiative #878 / #1017 PR-1)."""

from __future__ import annotations

import logging

import pytest

from src.utils.filter_operator_engine import FilterOperatorEngine


class TestCatalogs:
    def test_operator_catalog_has_twelve_entries(self):
        assert len(FilterOperatorEngine.OPERATOR_CATALOG) == 12

    def test_operator_catalog_contents(self):
        assert FilterOperatorEngine.OPERATOR_CATALOG == [
            "is",
            "is not",
            "contains",
            "doesn't contain",
            "starts with",
            "doesn't start with",
            "ends with",
            "doesn't end with",
            "is blank",
            "is not blank",
            "is null",
            "is not null",
        ]

    def test_value_required_operators_membership(self):
        expected = {
            "is",
            "is not",
            "contains",
            "doesn't contain",
            "starts with",
            "doesn't start with",
            "ends with",
            "doesn't end with",
        }
        assert set(FilterOperatorEngine.VALUE_REQUIRED_OPERATORS) == expected
        assert isinstance(FilterOperatorEngine.VALUE_REQUIRED_OPERATORS, frozenset)

    def test_remote_prefilter_operators_is_only_is(self):
        assert set(FilterOperatorEngine.REMOTE_PREFILTER_OPERATORS) == {"is"}


class TestNormalizeMac:
    def test_empty_returns_empty(self):
        assert FilterOperatorEngine.normalize_mac("") == ""

    def test_strips_colons_dashes_dots_and_lowercases(self):
        assert FilterOperatorEngine.normalize_mac("AA:BB-CC.DD:EE:FF") == "aabbccddeeff"

    def test_no_delimiters_lowercased(self):
        assert FilterOperatorEngine.normalize_mac("AABBCCDDEEFF") == "aabbccddeeff"


class TestNormalizeText:
    def test_empty_returns_empty(self):
        assert FilterOperatorEngine.normalize_text("") == ""

    def test_strips_and_lowercases(self):
        assert FilterOperatorEngine.normalize_text("  HeLLo  ") == "hello"


class TestValidateOperatorValue:
    def test_value_required_with_empty_warns_and_returns_false(self, caplog, capsys):
        caplog.set_level(logging.WARNING)
        assert FilterOperatorEngine.validate_operator_value("is", "", "hostname") is False
        assert "requires a non-empty value" in caplog.text
        captured = capsys.readouterr()
        assert "requires a value for hostname" in captured.out

    def test_value_required_with_whitespace_only_returns_false(self):
        assert FilterOperatorEngine.validate_operator_value("contains", "   ", "mac") is False

    def test_value_required_with_content_returns_true(self):
        assert FilterOperatorEngine.validate_operator_value("is", "abc", "hostname") is True

    def test_non_value_required_with_empty_returns_true(self):
        assert FilterOperatorEngine.validate_operator_value("is null", "", "hostname") is True


class TestEvaluateNullBlank:
    def test_is_null_true_when_none(self):
        assert FilterOperatorEngine._evaluate_null_blank(None, "is null") is True

    def test_is_null_false_when_present(self):
        assert FilterOperatorEngine._evaluate_null_blank("value", "is null") is False

    def test_is_not_null_true_when_present(self):
        assert FilterOperatorEngine._evaluate_null_blank("value", "is not null") is True

    def test_is_not_null_false_when_none(self):
        assert FilterOperatorEngine._evaluate_null_blank(None, "is not null") is False

    def test_is_blank_true_when_empty_string(self):
        assert FilterOperatorEngine._evaluate_null_blank("", "is blank") is True

    def test_is_blank_true_when_whitespace(self):
        assert FilterOperatorEngine._evaluate_null_blank("   ", "is blank") is True

    def test_is_blank_false_when_none(self):
        assert FilterOperatorEngine._evaluate_null_blank(None, "is blank") is False

    def test_is_blank_false_when_content(self):
        assert FilterOperatorEngine._evaluate_null_blank("hi", "is blank") is False

    def test_default_is_not_blank_true_when_content(self):
        assert FilterOperatorEngine._evaluate_null_blank("hi", "is not blank") is True

    def test_default_is_not_blank_false_when_empty(self):
        assert FilterOperatorEngine._evaluate_null_blank("   ", "is not blank") is False

    def test_default_is_not_blank_false_when_none(self):
        assert FilterOperatorEngine._evaluate_null_blank(None, "is not blank") is False


class TestNormalizePair:
    def test_mac_branch(self):
        assert FilterOperatorEngine._normalize_pair("AA:BB", "aa-bb", is_mac=True) == ("aabb", "aabb")

    def test_text_branch(self):
        assert FilterOperatorEngine._normalize_pair(" Foo ", "FOO", is_mac=False) == ("foo", "foo")


class TestEvaluateValueOperator:
    @pytest.mark.parametrize(
        ("op", "field", "search", "expected"),
        [
            ("is", "abc", "abc", True),
            ("is", "abc", "xyz", False),
            ("is not", "abc", "xyz", True),
            ("is not", "abc", "abc", False),
            ("contains", "hello world", "world", True),
            ("contains", "hello", "world", False),
            ("doesn't contain", "hello", "world", True),
            ("doesn't contain", "hello world", "world", False),
            ("starts with", "hello", "he", True),
            ("starts with", "hello", "lo", False),
            ("doesn't start with", "hello", "lo", True),
            ("doesn't start with", "hello", "he", False),
            ("ends with", "hello", "lo", True),
            ("ends with", "hello", "he", False),
            ("doesn't end with", "hello", "he", True),
            ("doesn't end with", "hello", "lo", False),
        ],
    )
    def test_operators(self, op, field, search, expected):
        assert FilterOperatorEngine._evaluate_value_operator(field, op, search) is expected

    def test_unknown_operator_returns_false(self):
        assert FilterOperatorEngine._evaluate_value_operator("a", "regex", "b") is False


class TestEvaluateOperator:
    def test_null_blank_operator_delegates(self):
        assert FilterOperatorEngine.evaluate_operator(None, "is null", "") is True

    def test_none_field_with_value_op_returns_false(self):
        assert FilterOperatorEngine.evaluate_operator(None, "is", "abc") is False

    def test_empty_field_with_value_op_returns_false(self):
        assert FilterOperatorEngine.evaluate_operator("   ", "contains", "x") is False

    def test_text_equality(self):
        assert FilterOperatorEngine.evaluate_operator("Hello", "is", "hello") is True

    def test_text_contains(self):
        assert FilterOperatorEngine.evaluate_operator("Hello World", "contains", "world") is True

    def test_mac_equality_delimiter_insensitive(self):
        assert FilterOperatorEngine.evaluate_operator("AA:BB:CC:DD:EE:FF", "is", "aabbccddeeff", is_mac=True) is True

    def test_mac_contains(self):
        assert FilterOperatorEngine.evaluate_operator("AA:BB:CC:DD:EE:FF", "contains", "cc-dd", is_mac=True) is True

    def test_unknown_value_operator_returns_false(self):
        assert FilterOperatorEngine.evaluate_operator("abc", "regex", "abc") is False
