"""UV runtime helper utilities used by dependency bootstrap workflows."""

from __future__ import annotations  # Enable PEP 604 union types on older Python targets.

import logging  # Stdlib logger for diagnostic breadcrumbs during version parsing.
from typing import Any  # Type hint used by build_runtime_helpers return dict.

from packaging.version import InvalidVersion, Version  # WHY: PEP 440 parser handles suffixes and segment counts.

_VERSION_OPERATORS = (">=", "<=", "==", "!=", ">", "<")  # 2-char operators listed first to match before 1-char.


class UVRuntimeHelper:  # Groups version parsing/comparison helpers under one namespace.
    """Helper methods for comparing and validating package versions."""

    @staticmethod
    def parse_version(version_str: str) -> Version:
        """Parse a version string with the PEP 440 version parser."""
        try:  # WHY: Invalid input must not stop the bootstrap dependency check.
            return Version(str(version_str))  # WHY: PEP 440 handles suffixes, leading zeros, and segment counts.
        except (InvalidVersion, TypeError):  # WHY: Bad metadata becomes a safe low version.
            logging.debug("Treating invalid version '%s' as 0", version_str)  # WHY: Leave a diagnostic breadcrumb.
            return Version("0")  # WHY: The sentinel makes a bad installed value fail the constraint.

    @staticmethod
    def _split_operator_and_required(spec: str) -> tuple[str, str]:
        """Return (operator, required_version) parsed from a version spec string."""
        logging.debug("Parsing version spec '%s' for operator and required", spec)  # Log spec parse entry.
        for symbol in _VERSION_OPERATORS:  # Iterate 2-char first so '>' never matches before '>='.
            if symbol in spec:  # Spec contains this operator token.
                lhs, rhs = spec.split(symbol, 1)  # Split into name portion and required version portion.
                if lhs is not None:  # Preserves legacy truthiness shape from original implementation.
                    return symbol, rhs.strip()  # Return matched operator and trimmed required version.
        return ">=", ""  # Empty required signals "no constraint" to caller.

    @staticmethod
    def _compare_versions(installed: Version, required: Version, operator: str) -> bool:
        """Return True when installed satisfies the operator and the required version."""
        comparisons = {  # Map operator strings to evaluated boolean results for clear dispatch.
            ">=": installed >= required,  # Greater-than-or-equal semantics.
            ">": installed > required,  # Strictly greater-than semantics.
            "<=": installed <= required,  # Less-than-or-equal semantics.
            "<": installed < required,  # Strictly less-than semantics.
            "==": installed == required,  # Equality semantics.
            "!=": installed != required,  # Inequality semantics.
        }
        return comparisons.get(operator, True)  # Unknown operator -> trivially satisfied.

    @staticmethod
    def version_satisfies(installed: str, spec: str) -> bool:
        """Validate whether an installed version satisfies a version spec."""
        if not installed:  # Empty installed version cannot satisfy any constraint.
            return False
        operator, required = UVRuntimeHelper._split_operator_and_required(spec)  # Parse operator and required version.
        if not required:  # No constraint encoded -> spec is trivially satisfied.
            return True
        installed_version = UVRuntimeHelper.parse_version(installed)  # Convert the installed version with PEP 440.
        required_version = UVRuntimeHelper.parse_version(required)  # Convert the required version with PEP 440.
        logging.debug(
            "Comparing installed=%s required=%s operator=%s", installed_version, required_version, operator
        )  # Log comparison inputs for diagnostics.
        return UVRuntimeHelper._compare_versions(installed_version, required_version, operator)  # Dispatch compare.

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
