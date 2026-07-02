"""Small pure-Python helpers shared by the maps CLI modules.

Extracted from ``src/maps/maps_manager.py`` so the utility surface is
importable without pulling in the entire ~7 kLOC MapsManager class.
Each helper is intentionally trivial and dependency-free -- anything
that needs Mist API access or user prompts belongs in a domain module,
not here.
"""

from __future__ import annotations

import csv
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Cap sanitized filenames at 100 chars so we stay well under the 255
# byte limit on Linux/ext4 and 260-char MAX_PATH on legacy Windows,
# even after callers append extensions and timestamps.
_MAX_FILENAME_LEN = 100

# Chars that break at least one common filesystem or shell. Applied to
# every user-provided string before it becomes part of a path.
_INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def flatten_dict_recursively(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
    """Flatten nested dicts/lists into a single flat mapping.

    Nested dicts contribute joined keys; lists of dicts contribute
    index-suffixed keys; scalar lists are stringified so the return
    value is always a flat ``dict[str, Any]`` suitable for CSV rows.
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict_recursively(v, new_key, sep=sep).items())
            continue
        if isinstance(v, list):
            items.extend(_flatten_list_value(v, new_key, sep))
            continue
        items.append((new_key, v))
    return dict(items)


def _flatten_list_value(value: list[Any], new_key: str, sep: str) -> list[tuple[str, Any]]:
    """Flatten a list value inside :func:`flatten_dict_recursively`.

    Lists-of-dicts recurse (so each element gets its own indexed keys);
    scalar lists are stringified because CSV output has no native
    representation for them.
    """
    if value and isinstance(value[0], dict):
        flattened: list[tuple[str, Any]] = []
        for idx, item in enumerate(value):
            flattened.extend(flatten_dict_recursively(item, f"{new_key}{sep}{idx}", sep=sep).items())
        return flattened
    return [(new_key, str(value))]


def sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe filename derived from ``filename``.

    Returns ``"unnamed"`` for empty input so callers never write to an
    accidentally-empty path. Strips filesystem-hostile characters and
    trims trailing spaces/dots which cause issues on Windows.
    """
    if not filename:
        return "unnamed"
    for char in _INVALID_FILENAME_CHARS:
        filename = filename.replace(char, "_")
    filename = filename.strip(" .")
    if not filename:
        return "unnamed"
    return filename[:_MAX_FILENAME_LEN]


def write_data_with_format_selection(
    data: list[dict[str, Any]],
    filename: str,
    _format_override: str | None = None,
    _api_function_name: str | None = None,
) -> bool:
    """Write ``data`` to ``data/<sanitize_filename(filename)>.csv``.

    Returns True on success, False when there is nothing to write or a
    write error occurs. The signature keeps ``_format_override`` and
    ``_api_function_name`` for callers that were built when this
    function did dispatch across CSV/JSON writers.
    """
    if not data:
        logger.warning("write_data_with_format_selection: No data to write")
        return False

    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(data_dir, f"{safe_filename}.csv")

    try:
        _write_csv_rows(data, filepath)
    except Exception as write_error:
        logger.error("Error writing CSV: %s", write_error)
        return False

    logger.info("Data written to %s (%s rows)", filepath, len(data))
    print(f"   Data saved to: {filepath}")
    return True


def _write_csv_rows(data: list[dict[str, Any]], filepath: str) -> None:
    """Write ``data`` rows to ``filepath`` with a superset field header.

    Splitting this out keeps :func:`write_data_with_format_selection`
    focused on filesystem prep + error reporting so its cyclomatic
    complexity stays inside the 5-Item Rule budget.
    """
    all_keys: set[str] = set()
    for row in data:
        all_keys.update(row.keys())
    fieldnames = sorted(all_keys)
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
