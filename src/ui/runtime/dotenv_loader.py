"""Replacement for ``MistHelperTUI._load_dotenv_only`` (CC=12)."""

from __future__ import annotations

import logging
import os
from typing import Any

DOTENV_FILENAME = ".env"  # Filename to load from CWD


class DotenvLoader:
    """Parse a project-local ``.env`` into a plain dict (no env-var merging)."""

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference for debug flag

    def load(self) -> dict[str, str]:
        """Return ``{key: value}`` parsed from ``.env``; empty dict on failure."""
        logging.info("TUI: loading .env values")  # Action log before read
        if not os.path.exists(DOTENV_FILENAME):  # No file -> empty result
            return {}
        dotenv_dict: dict[str, str] = {}  # Output accumulator
        try:
            with open(DOTENV_FILENAME, encoding="utf-8", errors="ignore") as handle:
                for raw_line in handle:  # Walk every line in the file
                    self._parse_line(raw_line, dotenv_dict)  # Append the parsed key to dict
        except Exception as error:  # Match original tolerant behavior
            logging.warning("TUI: Could not read .env file: %s", error)
        logging.debug("TUI: loaded %d .env values", len(dotenv_dict))  # Action log after read
        if self._tui.debug_mode:  # Echo loaded keys in debug mode
            logging.debug(
                "TUI_DEBUG: Loaded %d values from .env file: %s",
                len(dotenv_dict),
                list(dotenv_dict.keys()),
            )
        return dotenv_dict

    @staticmethod
    def _parse_line(raw_line: str, dotenv_dict: dict[str, str]) -> None:
        """Parse one .env line into ``dotenv_dict`` (skip blank/comment lines)."""
        line = raw_line.strip()  # Trim leading/trailing whitespace
        if not line or line.startswith("#"):  # Skip blank + comment lines
            return
        if "=" not in line:  # Skip malformed (no '=')
            return
        key, value = line.split("=", 1)  # Split on first '=' only
        key = key.strip()  # Trim key
        value = _strip_surrounding_quotes(value.strip())  # Trim + unquote value
        dotenv_dict[key] = value  # Store parsed pair


def _strip_surrounding_quotes(value: str) -> str:
    """Strip a single matching pair of double or single quotes around ``value``."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):  # Symmetric quote pair
        return value[1:-1]
    return value  # Otherwise return unchanged
