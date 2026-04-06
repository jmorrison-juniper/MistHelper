"""mh_helpers.py
Lightweight helpers extracted from MistHelper.py for incremental refactor (lint-misthelper-chunk-1).
These are intentionally small, well-tested utilities to reduce complexity in the main module.
"""
from __future__ import annotations


def _get_installed_version(package_name: str) -> str:
    """Return installed package version using importlib.metadata.version or empty string on failure.

    Kept intentionally simple and defensive because this helper is used during early startup.
    """
    try:
        # Local import to avoid import-time side effects in environments without importlib.metadata
        from importlib.metadata import version as _version

        return _version(package_name)
    except Exception:
        return ""


def _parse_version(version_str: str) -> tuple:
    """Parse a ``X.Y.Z``-style version string into an integer tuple.

    Examples:
        '0.59.3' -> (0, 59, 3)
        '1.2.3a1' -> (1, 2, 3)

    Non-numeric suffixes are ignored by extracting the numeric prefix per segment.
    """
    try:
        parts: list[int] = []
        for part in version_str.split('.'):
            numeric = ''
            for ch in part:
                if ch.isdigit():
                    numeric += ch
                else:
                    break
            parts.append(int(numeric) if numeric else 0)
        return tuple(parts)
    except Exception:
        return (0,)
