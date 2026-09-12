"""FilterOperatorEngine -- shared operator catalog + evaluation for client search filtering.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 40).
Pure utility class -- no MistHelper live-global dependencies. Provides the
operator catalog (12 operators), value-required + remote-prefilter subsets,
normalization helpers for MAC / free text, and the evaluator that dispatches
by operator name (null/blank predicates via dict, value operators via lambda
map). Callers continue to reach the class through the
``MistHelper.FilterOperatorEngine`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import logging  # WHY: validate_operator_value emits a warning for empty value-required inputs.
import re  # WHY: normalize_mac strips MAC delimiters via re.sub.
from typing import Any  # WHY: operator_map values are heterogeneous lambdas.


class FilterOperatorEngine:  # Filter operator evaluation engine.
    """Shared operator catalog, normalization, and evaluation for client search filtering."""

    OPERATOR_CATALOG: list[str] = [  # Supported operator names.
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

    VALUE_REQUIRED_OPERATORS: frozenset[str] = frozenset(  # Operators needing a value.
        {
            "is",
            "is not",
            "contains",
            "doesn't contain",
            "starts with",
            "doesn't start with",
            "ends with",
            "doesn't end with",
        }
    )

    REMOTE_PREFILTER_OPERATORS: frozenset[str] = frozenset(  # Operators pushed to the API.
        {
            "is",
        }
    )

    @staticmethod
    def normalize_mac(mac_value: str) -> str:  # Normalize a MAC string.
        """Remove delimiters and lowercase for delimiter-insensitive comparison."""
        if not mac_value:  # Empty input.
            return ""  # Return empty.
        return re.sub(r"[:\-.]", "", mac_value).lower()  # Strip separators. Lowercase.

    @staticmethod
    def normalize_text(text_value: str) -> str:  # Normalize free text.
        """Lowercase and strip for case-insensitive comparison."""
        if not text_value:  # Empty input.
            return ""  # Return empty.
        return text_value.strip().lower()  # Trim and lowercase.

    @staticmethod
    def evaluate_operator(field_value: str | None, operator: str, search_value: str, is_mac: bool = False) -> bool:
        """Evaluate a single operator against a field value. Returns True if record matches."""
        if operator in ("is null", "is not null", "is blank", "is not blank"):  # Null/blank operators.
            return FilterOperatorEngine._evaluate_null_blank(field_value, operator)  # Delegate null/blank check.
        if field_value is None or str(field_value).strip() == "":  # Empty field fails value ops.
            return False  # No match.
        normalized = FilterOperatorEngine._normalize_pair(str(field_value), search_value, is_mac)
        return FilterOperatorEngine._evaluate_value_operator(normalized[0], operator, normalized[1])

    @staticmethod
    def validate_operator_value(operator: str, value: str, field_name: str) -> bool:  # Validate operator+value pair.
        """Validate that value-required operators have non-empty normalized values."""
        if operator in FilterOperatorEngine.VALUE_REQUIRED_OPERATORS:  # Value-required operator?
            if not value or not value.strip():  # Missing value.
                logging.warning(
                    "Operator '%s' for %s requires a non-empty value. Please try again.", operator, field_name
                )  # Single WARNING (retired duplicate print() per #886 Phase 2) surfaces on operator terminal.
                return False  # Invalid.
        return True  # Valid.

    # Null/blank operator -> predicate. Dict dispatch keeps _evaluate_null_blank flat (no if-chain/booleans).
    _NULL_BLANK_OPERATORS = {
        "is null": lambda field_value: field_value is None,  # True when the field is absent
        "is not null": lambda field_value: field_value is not None,  # True when the field is present
        "is blank": lambda field_value: (
            field_value is not None and str(field_value).strip() == ""
        ),  # Present but empty/whitespace
    }

    @staticmethod
    def _evaluate_null_blank(field_value: str | None, operator: str) -> bool:  # Evaluate null/blank operators.
        """Evaluate null/blank operators against a field value (default: 'is not blank')."""
        predicate = FilterOperatorEngine._NULL_BLANK_OPERATORS.get(operator)  # Look up the operator predicate
        if predicate:  # A null/null/blank operator matched
            return predicate(field_value)  # Apply its predicate
        return field_value is not None and str(field_value).strip() != ""  # Default: 'is not blank'

    @staticmethod
    def _normalize_pair(field_value: str, search_value: str, is_mac: bool) -> tuple[str, str]:
        """Normalize field and search values for comparison."""
        if is_mac:  # MAC comparison.
            return FilterOperatorEngine.normalize_mac(field_value), FilterOperatorEngine.normalize_mac(search_value)
        return FilterOperatorEngine.normalize_text(field_value), FilterOperatorEngine.normalize_text(search_value)

    @staticmethod
    def _evaluate_value_operator(field: str, operator: str, search: str) -> bool:  # Apply a value operator.
        """Evaluate value-based positional/equality operators."""
        operator_map: dict[str, Any] = {  # Operator -> comparator map.
            "is": lambda f, s: f == s,
            "is not": lambda f, s: f != s,
            "contains": lambda f, s: s in f,
            "doesn't contain": lambda f, s: s not in f,
            "starts with": lambda f, s: f.startswith(s),
            "doesn't start with": lambda f, s: not f.startswith(s),
            "ends with": lambda f, s: f.endswith(s),
            "doesn't end with": lambda f, s: not f.endswith(s),
        }
        evaluator = operator_map.get(operator)  # Look up the comparator.
        return evaluator(field, search) if evaluator else False  # Compare or default false.
