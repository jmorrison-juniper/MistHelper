"""UV runtime helper utilities used by dependency bootstrap workflows."""

from __future__ import annotations  # Enable PEP 604 union types on older Python targets.

import logging  # Stdlib logger for diagnostic breadcrumbs during version parsing.
from typing import Any  # Type hint used by build_runtime_helpers return dict.

_VERSION_OPERATORS = (">=", "<=", "==", "!=", ">", "<")  # 2-char operators listed first to match before 1-char.


class UVRuntimeHelper:  # Groups version parsing/comparison helpers under one namespace.
    """Helper methods for comparing and validating package versions."""

    @staticmethod
    def _parse_numeric_prefix(raw_part: str) -> int:  # Extracted to keep parse_version CC <= 5.
        """Return the leading numeric prefix of a version segment as an int (0 if empty)."""
        # WHY: extracted from parse_version so the outer function stays CC 2 (try/except only).
        numeric_part = ""  # Accumulator for consecutive leading digit characters.
        for char in raw_part:  # Walk segment left-to-right consuming digits.
            if char.isdigit():  # Digit contributes to the numeric prefix.
                numeric_part += char  # Append to accumulator.
            else:
                break  # First non-digit terminates the numeric prefix.
        return int(numeric_part) if numeric_part else 0  # Empty prefix -> 0 (matches legacy behavior).

    @staticmethod
    def parse_version(version_str: str) -> tuple[int, ...]:  # Public parser used by version_satisfies.
        """Parse a version string into a comparable numeric tuple."""
        try:  # Legacy contract: any parse error collapses to (0,) sentinel.
            return tuple(UVRuntimeHelper._parse_numeric_prefix(p) for p in version_str.split("."))
        except Exception:  # Broad catch mirrors original defensive shape.
            return (0,)  # Sentinel used by version_satisfies to reject bad input.

    @staticmethod
    def _split_operator_and_required(spec: str) -> tuple[str, str]:
        """Return (operator, required_version) parsed from a version spec string."""
        logging.debug("Parsing version spec '%s' for operator and required", spec)  # Log spec parse entry.
        for symbol in _VERSION_OPERATORS:  # Iterate 2-char first so '>' never matches before '>='.
            if symbol in spec:  # Spec contains this operator token.
                lhs, rhs = spec.split(symbol, 1)  # Split into name portion and required version portion.
                if lhs is not None:  # Preserves legacy truthiness shape from original implementation.
                    return symbol, rhs.strip()  # Return matched operator and trimmed required version.
        return ">=", ""  # Empty required signals "no constraint" to caller (default operator harmless).

    @staticmethod
    def _compare_versions(installed: tuple[int, ...], required: tuple[int, ...], operator: str) -> bool:
        """Return True when installed tuple satisfies operator vs required tuple."""
        comparisons = {  # Map operator strings to pre-evaluated boolean results for O(1) dispatch.
            ">=": installed >= required,  # Greater-than-or-equal semantics.
            ">": installed > required,  # Strictly greater-than semantics.
            "<=": installed <= required,  # Less-than-or-equal semantics.
            "<": installed < required,  # Strictly less-than semantics.
            "==": installed == required,  # Equality semantics.
            "!=": installed != required,  # Inequality semantics.
        }
        return comparisons.get(operator, True)  # Unknown operator -> trivially satisfied (legacy behavior).

    @staticmethod
    def version_satisfies(installed: str, spec: str) -> bool:
        """Validate whether an installed version satisfies a version spec."""
        if not installed:  # Empty installed version cannot satisfy any constraint.
            return False
        operator, required = UVRuntimeHelper._split_operator_and_required(spec)  # Parse operator + required version.
        if not required:  # No constraint encoded -> spec is trivially satisfied.
            return True
        installed_tuple = UVRuntimeHelper.parse_version(installed)  # Numeric tuple form of installed version.
        required_tuple = UVRuntimeHelper.parse_version(required)  # Numeric tuple form of required version.
        max_len = max(len(installed_tuple), len(required_tuple))  # Normalize lengths for fair tuple compare.
        installed_tuple = installed_tuple + (0,) * (max_len - len(installed_tuple))  # Right-pad with zeros.
        required_tuple = required_tuple + (0,) * (max_len - len(required_tuple))  # Right-pad with zeros.
        logging.debug(
            "Comparing installed=%s required=%s operator=%s", installed_tuple, required_tuple, operator
        )  # Log comparison inputs for diagnostics.
        return UVRuntimeHelper._compare_versions(installed_tuple, required_tuple, operator)  # Dispatch compare.

    @staticmethod
    def package_name_from_spec(package_spec: str) -> str:
        """Extract the package name from a versioned package specification."""
        package_name = package_spec  # Start with the full spec. Strip operator tail if any is found.
        for operator in [">=", "<=", "==", "!=", ">", "<"]:  # 2-char operators first to avoid '>' false-match.
            if operator in package_name:  # Spec contains this operator token.
                package_name = package_name.split(operator, 1)[0]  # Keep only the name portion.
                break  # Only strip the first matching operator.
        return package_name.strip()  # Trim any surrounding whitespace before returning.


def build_runtime_helpers() -> dict[str, Any]:  # Dependency-injection hook for bootstrap orchestration.
    """Return callable helpers for dependency injection in bootstrap orchestration."""
    return {  # Bundle the three public helpers into a plain dict for injection.
        "parse_version": UVRuntimeHelper.parse_version,  # Version tuple parser.
        "version_satisfies": UVRuntimeHelper.version_satisfies,  # Version spec checker.
        "package_name_from_spec": UVRuntimeHelper.package_name_from_spec,  # Name extractor.
    }
