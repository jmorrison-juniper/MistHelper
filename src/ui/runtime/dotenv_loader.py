"""Replacement for ``MistHelperTUI._load_dotenv_only`` (CC=12)."""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: action-log before/after every .env read
import os  # WHY: existence check on the .env file
from typing import Any  # WHY: TUI back-ref is loosely typed

DOTENV_FILENAME = ".env"  # Filename to load from CWD


class DotenvLoader:  # WHY: extracted from MistHelperTUI._load_dotenv_only (was CC=12)
    """Parse a project-local ``.env`` into a plain dict (no env-var merging)."""

    def __init__(self, tui: Any) -> None:  # WHY: bind TUI for the debug-mode flag
        """Store TUI back-reference (used only for the debug-mode flag)."""
        self._tui = tui  # Back-reference for debug flag

    def load(self) -> dict[str, str]:  # WHY: read .env once at startup
        """Return ``{key: value}`` parsed from ``.env``. Empty dict on failure."""
        logging.info("TUI: loading .env values")  # Action log before read
        if not os.path.exists(DOTENV_FILENAME):  # No file -> empty result
            return {}  # WHY: absent .env is not an error, just an empty result
        dotenv_dict: dict[str, str] = {}  # Output accumulator
        try:  # WHY: tolerate malformed/unreadable .env without failing startup
            with open(DOTENV_FILENAME, encoding="utf-8", errors="ignore") as handle:  # WHY: forgiving decode
                for raw_line in handle:  # Walk every line in the file
                    self._parse_line(raw_line, dotenv_dict)  # Append the parsed key to dict
        except Exception as error:  # Match original tolerant behavior
            logging.warning("TUI: Could not read .env file: %s", error)  # WHY: warn but continue
        logging.debug("TUI: loaded %d .env values", len(dotenv_dict))  # Action log after read
        if self._tui.debug_mode:  # Echo loaded keys in debug mode
            logging.debug(  # WHY: dump keys (not values) for debug visibility
                "TUI_DEBUG: Loaded %d values from .env file: %s",
                len(dotenv_dict),
                list(dotenv_dict.keys()),
            )
        return dotenv_dict  # WHY: hand parsed pairs to caller

    @staticmethod
    def _parse_line(raw_line: str, dotenv_dict: dict[str, str]) -> None:  # WHY: single-line parse w/o self
        """Parse one .env line into ``dotenv_dict`` (skip blank/comment lines)."""
        line = raw_line.strip()  # Trim leading/trailing whitespace
        if not line or line.startswith("#"):  # Skip blank + comment lines
            return  # WHY: no key to store
        if "=" not in line:  # Skip malformed (no '=')
            return  # WHY: cannot split key from value
        key, value = line.split("=", 1)  # Split on first '=' only
        key = key.strip()  # Trim key
        value = _strip_surrounding_quotes(value.strip())  # Trim + unquote value
        dotenv_dict[key] = value  # Store parsed pair


def _strip_surrounding_quotes(value: str) -> str:  # WHY: normalize quoted .env values
    """Strip a single matching pair of double or single quotes around ``value``."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):  # Symmetric quote pair
        return value[1:-1]  # WHY: drop the matched pair
    return value  # Otherwise return unchanged
