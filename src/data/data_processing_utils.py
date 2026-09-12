"""``DataProcessingUtils`` extracted from MistHelper (initiative 1015 T-10).

Owns the JSON-flattening / CSV-normalization helpers originally defined
at ``MistHelper.py`` lines 2892-3049. All methods are ``@staticmethod``
with no runtime dependencies -- the class is a pure utility bundle, so
this extraction lands as a bare re-export from ``MistHelper.py`` (no
Pattern 1 DI wrapper, no delegator).

``MistHelper.py`` re-exports the class so historical
``MistHelper.DataProcessingUtils`` / ``mh.DataProcessingUtils`` callers
keep working transparently -- the re-exported symbol is the same class,
not a delegator.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/896 (initiative 1015 T-10).
"""

from __future__ import annotations  # Enable PEP 604 unions on 3.10+.

import ast  # ast.literal_eval fallback for stringified Python literals.
import json  # json.loads fallback for stringified JSON payloads.
import logging  # Structured action logging per Constitution VII.
from typing import Any  # Broad typing for arbitrary field values.


class DataProcessingUtils:
    """Centralized data-transformation utilities (canonical home in ``src/data/``).

    All methods are static. The class is a namespace for JSON flattening,
    key normalization, and CSV-safety helpers. ``MistHelper.py`` re-exports
    this class so historical callers keep working without a delegator.
    """

    @staticmethod
    def _flatten_list_value(new_key: str, sep: str, v: list[Any]) -> list[tuple[str, Any]]:
        """Flatten a list value: list-of-dicts gets index keys. Scalar lists join as CSV."""
        out: list[tuple[str, Any]] = []  # Accumulator for produced pairs.
        if all(isinstance(i, dict) for i in v):  # List of dicts: index each entry.
            for idx, item in enumerate(v):  # Walk list items.
                out.extend(DataProcessingUtils.flatten_dict(item, f"{new_key}{sep}{idx}", sep=sep).items())
            return out  # Return the indexed pairs.
        out.append((new_key, ",".join(map(str, v))))  # Join scalar list as CSV.
        return out  # Return the single joined pair.

    @staticmethod
    def flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
        """Recursively flatten nested dict for CSV/JSON. Lists-of-dicts get index keys."""
        items: list[tuple[str, Any]] = []  # Accumulate flattened (key, value) pairs.
        for k, v in d.items():  # Walk every key/value in the input dict.
            k_str = str(k)  # Stringify the key for safe concatenation.
            new_key = f"{parent_key}{sep}{k_str}" if parent_key else k_str  # Compose the dotted key.
            if isinstance(v, dict):  # Recurse into nested dicts.
                items.extend(DataProcessingUtils.flatten_dict(v, new_key, sep=sep).items())
                continue  # Move to next field.
            if isinstance(v, list):  # Lists need index expansion or CSV join.
                items.extend(DataProcessingUtils._flatten_list_value(new_key, sep, v))
                continue  # Move to next field.
            items.append((new_key, v))  # Scalar value: keep as-is.
        return dict(items)  # Return the flat dict.

    @staticmethod
    def flatten_nested_fields(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten nested fields in a list of dictionaries.

        Attempts to parse stringified dicts/lists. Recursively flattens
        nested dicts and lists of dicts. Joins non-dict lists as CSV.
        """
        flattened = []  # Collect flattened rows.
        for entry in data:  # Process each record.
            if not isinstance(entry, dict):  # Skip non-dict records defensively.
                logging.debug("Skipping non-dictionary entry: %s", type(entry).__name__)  # Trace skipped entry.
                continue  # Move to next record.
            flattened.append(DataProcessingUtils._flatten_entry(entry))  # Delegate per-entry flattening.
        return flattened  # Return all flattened rows.

    @staticmethod
    def _flatten_entry(entry: dict[str, Any]) -> dict[str, Any]:
        """Flatten a single dict entry, returning a new dict with nested values expanded."""
        new_entry: dict[str, Any] = {}  # Accumulator for the flattened output of this entry.
        for key, value in entry.items():  # Walk every field of the entry.
            parsed = DataProcessingUtils._parse_stringified_value(value)  # Maybe parse stringified JSON.
            DataProcessingUtils._flatten_value_into(new_entry, key, parsed)  # Expand nested value.
        return new_entry  # Return the flattened entry.

    @staticmethod
    def _parse_stringified_value(value: Any) -> Any:
        """Try to parse a string starting with ``{`` or ``[`` as Python literal or JSON."""
        if not isinstance(value, str):  # Non-string values pass through unchanged.
            return value  # Nothing to parse.
        if not value.startswith(("{", "[")):  # Not embedded JSON-ish. Skip parsing.
            return value  # Return as-is.
        try:
            return ast.literal_eval(value)  # Try Python-literal parse first.
        except Exception:  # ast.literal_eval failed. Try JSON.
            try:
                return json.loads(value)  # Fall back to JSON parse.
            except Exception:  # nosec B110 - both parses failed. Leave value as string.
                return value  # Final fallback: original string.

    @staticmethod
    def _flatten_value_into(new_entry: dict[str, Any], key: str, value: Any) -> None:
        """Merge a single (key, value) into ``new_entry``, expanding nested dicts/lists."""
        if isinstance(value, dict):  # Nested dict needs flattening.
            new_entry.update(DataProcessingUtils.flatten_dict(value, parent_key=key))  # Merge flattened keys.
            return  # Done for dict path.
        if not isinstance(value, list):  # Scalar (non-dict, non-list).
            new_entry[key] = value  # Keep scalar value as-is.
            return  # Done for scalar path.
        if DataProcessingUtils._is_list_of_dicts(value):  # List of dicts: index each element.
            for idx, item in enumerate(value):  # Walk list items.
                new_entry.update(DataProcessingUtils.flatten_dict(item, parent_key=f"{key}_{idx}"))  # Merge item keys.
            return  # Done for list-of-dicts path.
        new_entry[key] = ",".join(map(str, value))  # Scalar list -- join as CSV.

    @staticmethod
    def _is_list_of_dicts(value: list[Any]) -> bool:
        """Return ``True`` when every element of ``value`` is a dict."""
        return all(isinstance(i, dict) for i in value)  # Check every element is dict-typed.

    @staticmethod
    def convert_list_values_to_strings(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert list, tuple, or set values to CSV-compatible comma-separated strings."""
        for entry in data:  # Process each record.
            for key, value in entry.items():  # Walk each field.
                if isinstance(value, (list, tuple, set)):  # Only convert collections.
                    logging.debug("Converting list/tuple/set at key '%s' to string", key)  # Trace the conversion.
                    entry[key] = ",".join(map(str, value))  # Join as CSV string.
        return data  # Return converted records.

    @staticmethod
    def get_unique_keys(data: list[dict[str, Any]]) -> list[str]:
        """Return a sorted list of unique keys across all dicts in ``data``."""
        fields: set[Any] = set()  # Accumulate distinct keys.
        for entry in data:  # Scan each record.
            fields.update(entry.keys())  # Add this record's keys.
        return sorted(str(f) for f in fields)  # Return sorted field names.

    @staticmethod
    def escape_multiline(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Escape multiline strings for CSV compatibility.

        Joins list values as CSV-separated strings. Replaces newline
        characters with escaped versions on string fields.
        """
        for entry in data:  # Process each record.
            for key, value in entry.items():  # Walk each field.
                if isinstance(value, list):  # Join lists to a CSV string.
                    entry[key] = ",".join(map(str, value))  # CSV-join the list.
                elif isinstance(value, str):  # Escape string newlines for CSV safety.
                    entry[key] = value.replace("\n", "\\n").replace("\r", "")  # Escape CR/LF for CSV.
        return data  # Return escaped records.
