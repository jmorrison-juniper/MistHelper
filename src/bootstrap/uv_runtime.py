"""UV runtime helper utilities used by dependency bootstrap workflows."""

from __future__ import annotations

from typing import Any


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
    def version_satisfies(installed: str, spec: str) -> bool:
        """Validate whether an installed version satisfies a version spec."""
        if not installed:
            return False
        operators = [">=", "<=", "==", "!=", ">", "<"]
        operator = ">="
        required = ""
        for symbol in operators:
            if symbol in spec:
                lhs, rhs = spec.split(symbol, 1)
                if lhs is not None:
                    operator = symbol
                    required = rhs.strip()
                    break
        if not required:
            return True
        installed_tuple = UVRuntimeHelper.parse_version(installed)
        required_tuple = UVRuntimeHelper.parse_version(required)
        max_len = max(len(installed_tuple), len(required_tuple))
        installed_tuple = installed_tuple + (0,) * (max_len - len(installed_tuple))
        required_tuple = required_tuple + (0,) * (max_len - len(required_tuple))
        if operator == ">=":
            return installed_tuple >= required_tuple
        if operator == ">":
            return installed_tuple > required_tuple
        if operator == "<=":
            return installed_tuple <= required_tuple
        if operator == "<":
            return installed_tuple < required_tuple
        if operator == "==":
            return installed_tuple == required_tuple
        if operator == "!=":
            return installed_tuple != required_tuple
        return True

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
