"""Small pure-Python helpers shared by the maps CLI modules.

Extracted from ``src/maps/maps_manager.py`` so the utility surface is
importable without pulling in the entire ~7 kLOC MapsManager class.
Each helper is intentionally trivial and dependency-free -- anything
that needs Mist API access or user prompts belongs in a domain module,
not here.
"""

from __future__ import annotations  # WHY: PEP 563 postponed evaluation for forward-friendly typing.

import csv  # WHY: stdlib CSV writer for the sole export format supported here.
import logging  # WHY: structured module-level logger keeps prints out of library code.
import os  # WHY: cwd + path joins for portable data-dir writes across OSes.
from typing import Any, Literal  # WHY: heterogeneous dict values + Literal for csv.DictWriter extrasaction.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger avoids configuring the root logger.

# Cap sanitized filenames at 100 chars so we stay well under the 255
# byte limit on Linux/ext4 and 260-char MAX_PATH on legacy Windows,
# even after callers append extensions and timestamps.
_MAX_FILENAME_LEN: int = 100  # WHY: safety margin below 255/260 filesystem ceilings after suffix append.

# Chars that break at least one common filesystem or shell. Applied to
# every user-provided string before it becomes part of a path.
_INVALID_FILENAME_CHARS: str = '<>:"/\\|?*'  # WHY: superset of Windows-reserved plus POSIX path separators.

_FALLBACK_NAME: str = "unnamed"  # WHY: sentinel returned for empty/whitespace filenames to avoid empty writes.
_DATA_DIRNAME: str = "data"  # WHY: repo convention places CSV exports under ./data at cwd.
_CSV_EXT: str = ".csv"  # WHY: single-format export; suffix appended after sanitization.
_REPLACEMENT_CHAR: str = "_"  # WHY: underscore is safe on every target filesystem and shell.
_STRIP_CHARS: str = " ."  # WHY: Windows rejects trailing space/dot in file/directory names.

_LOG_EMPTY_DATA: str = "write_data_with_format_selection: No data to write"  # WHY: no-op guard log message.
_LOG_WRITE_ERROR: str = "Error writing CSV: %s"  # WHY: error template surfaces the underlying exception.
_LOG_WRITE_OK: str = "Data written to %s (%s rows)"  # WHY: success template shows path + row count for audit.
_PRINT_SAVED_TMPL: str = "   Data saved to: {filepath}"  # WHY: user-facing stdout confirmation with indent.

_CSV_MODE_WRITE: str = "w"  # WHY: overwrite existing file each run; callers version via distinct filenames.
_CSV_NEWLINE: str = ""  # WHY: csv module handles newlines internally; empty avoids double-CR on Windows.
_CSV_ENCODING: str = "utf-8"  # WHY: broadest-compatibility encoding for exported Mist data.
_CSV_EXTRAS: Literal["ignore"] = "ignore"  # WHY: silently drop keys missing from the computed superset header.


def flatten_dict_recursively(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
    """Flatten nested dicts/lists into a single flat mapping.

    Nested dicts contribute joined keys; lists of dicts contribute
    index-suffixed keys; scalar lists are stringified so the return
    value is always a flat ``dict[str, Any]`` suitable for CSV rows.
    """
    items: list[tuple[str, Any]] = []  # WHY: accumulate as pairs so ordering follows insertion for stability.
    for k, v in d.items():  # WHY: walk top-level keys; dispatch by value type below.
        new_key = f"{parent_key}{sep}{k}" if parent_key else k  # WHY: prefix only when nested to avoid leading sep.
        if isinstance(v, dict):  # WHY: dict branch recurses to flatten nested structures.
            items.extend(flatten_dict_recursively(v, new_key, sep=sep).items())  # WHY: merge child pairs verbatim.
            continue  # WHY: guard-clause skip keeps list/scalar handling flat.
        if isinstance(v, list):  # WHY: list branch delegates to helper for list-of-dict vs scalar-list split.
            items.extend(_flatten_list_value(v, new_key, sep))  # WHY: helper returns pre-flattened pairs.
            continue  # WHY: same skip-after-branch pattern preserves flat control flow.
        items.append((new_key, v))  # WHY: scalar values land verbatim under the computed key.
    return dict(items)  # WHY: dict() over ordered pairs yields deterministic key order for tests.


def _flatten_list_value(value: list[Any], new_key: str, sep: str) -> list[tuple[str, Any]]:
    """Flatten a list value inside :func:`flatten_dict_recursively`.

    Lists-of-dicts recurse (so each element gets its own indexed keys);
    scalar lists are stringified because CSV output has no native
    representation for them.
    """
    if value and isinstance(value[0], dict):  # WHY: sample first element to distinguish dict-list vs scalar list.
        flattened: list[tuple[str, Any]] = []  # WHY: collect indexed pairs across all list elements.
        for idx, item in enumerate(value):  # WHY: index suffix disambiguates positional keys in the CSV header.
            indexed_key = f"{new_key}{sep}{idx}"  # WHY: precompute nested key to keep call line under 120 chars.
            flattened.extend(flatten_dict_recursively(item, indexed_key, sep=sep).items())  # WHY: recurse per elem.
        return flattened  # WHY: return the fully expanded list of key/value pairs.
    return [(new_key, str(value))]  # WHY: scalar lists become a single stringified cell for CSV compatibility.


def sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe filename derived from ``filename``.

    Returns ``"unnamed"`` for empty input so callers never write to an
    accidentally-empty path. Strips filesystem-hostile characters and
    trims trailing spaces/dots which cause issues on Windows.
    """
    if not filename:  # WHY: empty input maps to the fallback sentinel so we never write to "".
        return _FALLBACK_NAME  # WHY: sentinel keeps callers' error handling simple (never empty).
    for char in _INVALID_FILENAME_CHARS:  # WHY: replace each hostile char in a single left-to-right pass.
        filename = filename.replace(char, _REPLACEMENT_CHAR)  # WHY: underscore preserves length + readability.
    filename = filename.strip(_STRIP_CHARS)  # WHY: trims trailing dot/space which break Windows resolves.
    if not filename:  # WHY: strip may fully consume the string (e.g. all-dots input).
        return _FALLBACK_NAME  # WHY: second sentinel check after stripping mirrors the initial guard.
    return filename[:_MAX_FILENAME_LEN]  # WHY: enforce ceiling so appended extensions stay under FS limits.


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
    if not data:  # WHY: no-data guard avoids creating empty CSVs with just a header row.
        logger.warning(_LOG_EMPTY_DATA)  # WHY: warn rather than raise so batch exports keep going.
        return False  # WHY: False signals "nothing written" to caller loops.
    filepath = _resolve_csv_filepath(filename)  # WHY: single helper handles dir-mkdir + sanitized path assembly.
    try:
        _write_csv_rows(data, filepath)  # WHY: isolated write step so the try/except stays focused.
    except Exception as write_error:  # WHY: broad catch converts any IO/encoding failure into a False return.
        logger.error(_LOG_WRITE_ERROR, write_error)  # WHY: template log includes the underlying error text.
        return False  # WHY: False on write failure preserves batch-export resilience.
    logger.info(_LOG_WRITE_OK, filepath, len(data))  # WHY: audit log includes both path and row count.
    print(_PRINT_SAVED_TMPL.format(filepath=filepath))  # WHY: user-facing confirmation echoed to stdout.
    return True  # WHY: True indicates the CSV was successfully committed to disk.


def _resolve_csv_filepath(filename: str) -> str:
    """Return the fully sanitized CSV filepath under ``data/`` in cwd.

    Ensures the target directory exists and appends the CSV extension
    after sanitization so callers can pass raw display names without
    worrying about filesystem safety.
    """
    data_dir = os.path.join(os.getcwd(), _DATA_DIRNAME)  # WHY: rebuild each call so cwd changes are respected.
    os.makedirs(data_dir, exist_ok=True)  # WHY: exist_ok=True idempotently handles first-run vs. repeat runs.
    safe_filename = sanitize_filename(filename)  # WHY: run through the shared sanitizer before path assembly.
    return os.path.join(data_dir, f"{safe_filename}{_CSV_EXT}")  # WHY: extension appended post-sanitize by design.


def _write_csv_rows(data: list[dict[str, Any]], filepath: str) -> None:
    """Write ``data`` rows to ``filepath`` with a superset field header.

    Splitting this out keeps :func:`write_data_with_format_selection`
    focused on filesystem prep + error reporting so its cyclomatic
    complexity stays inside the 5-Item Rule budget.
    """
    all_keys: set[str] = set()  # WHY: set collapses duplicates as rows are scanned for the header union.
    for row in data:  # WHY: single pass over rows populates the union of keys.
        all_keys.update(row.keys())  # WHY: update() is O(k) per row and avoids intermediate lists.
    fieldnames = sorted(all_keys)  # WHY: sorted header keeps CSV output deterministic run-to-run.
    # WHY: text-mode CSV write; csv module inserts its own line terminators.
    with open(filepath, _CSV_MODE_WRITE, newline=_CSV_NEWLINE, encoding=_CSV_ENCODING) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction=_CSV_EXTRAS)  # WHY: ignore stray keys.
        writer.writeheader()  # WHY: emit the deterministic header row before data rows.
        writer.writerows(data)  # WHY: bulk write is faster than per-row writer.writerow(...) calls.
