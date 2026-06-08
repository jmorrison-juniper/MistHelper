"""UV runtime helper utilities used by dependency bootstrap workflows."""

from __future__ import annotations

import logging
from typing import Any

_VERSION_OPERATORS = (">=", "<=", "==", "!=", ">", "<")  # 2-char operators listed first to match before 1-char.


class UVRuntimeHelper:
    """Helper methods for comparing and validating package versions."""

    @staticmethod
    def parse_version(version_str: str) -> tuple[int, ...]:
        """Parse a version string into a comparable numeric tuple."""
        try:
            parts: list[int] = []
            for raw_part in version_str.split("."):
                numeric_part = ""
                for char in raw_part:
                    if char.isdigit():
                        numeric_part += char
                    else:
                        break
                parts.append(int(numeric_part) if numeric_part else 0)
            return tuple(parts)
        except Exception:
            return (0,)

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
        package_name = package_spec
        for operator in [">=", "<=", "==", "!=", ">", "<"]:
            if operator in package_name:
                package_name = package_name.split(operator, 1)[0]
                break
        return package_name.strip()


def build_runtime_helpers() -> dict[str, Any]:
    """Return callable helpers for dependency injection in bootstrap orchestration."""
    return {
        "parse_version": UVRuntimeHelper.parse_version,
        "version_satisfies": UVRuntimeHelper.version_satisfies,
        "package_name_from_spec": UVRuntimeHelper.package_name_from_spec,
    }
