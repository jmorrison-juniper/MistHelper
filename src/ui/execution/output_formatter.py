"""APIResponse parsing + hierarchical formatting helpers.

Replaces ``MistHelperTUI._parse_api_response`` (trivial), ``_format_result_output``
(trivial), and ``_format_value_hierarchical`` (CC=20). Each helper here is CC <= 10.
"""

from __future__ import annotations

import logging
from typing import Any

MAX_SAMPLE_ITEMS = 5  # Default sample-items cap


class APIResponseParser:
    """Extract the ``data`` attribute from mistapi ``APIResponse`` objects."""

    def parse(self, result: Any) -> Any:
        """Return ``result.data`` when present. Otherwise ``result`` unchanged."""
        if hasattr(result, "data"):  # mistapi APIResponse shape
            logging.debug("TUI_DEBUG: Detected APIResponse object, extracting data attribute")
            return result.data
        return result  # Non-APIResponse passthrough


class HierarchicalFormatter:
    """Format any Python value as a human-readable indented text block."""

    def format_result(self, parsed_data: Any, func_name: str, raw_result: Any = None) -> list[str]:
        """Top-level helper: SUCCESS header + recursive body + size hint."""
        output: list[str] = [f"[SUCCESS] {func_name} completed", ""]  # Banner lines
        logging.info("TUI: formatting result for %s", func_name)  # Action log before render
        if raw_result is not None:  # Debug-mode artifact hint
            output.append(f"[dim]Debug: Result saved to data/tui_debug_results/{func_name}_*.json[/dim]")
            output.append("")
        self._render(parsed_data, output, indent=0, key_name="results")  # Recursive body render
        if isinstance(parsed_data, (list, dict)) and len(str(parsed_data)) > 500:
            output.append("")
            output.append("[dim]Tip: Full data available in debug log (run with --debug)[/dim]")
        logging.debug("TUI: result formatting complete for %s", func_name)  # Action log after render
        return output

    # ---- recursive type dispatch -----------------------------------------

    def _render(self, value: Any, output: list[str], indent: int, key_name: str | None) -> None:
        """Dispatch on the type of ``value`` and emit the formatted block."""
        if value is None:  # None short-circuit
            self._emit_simple("None", output, indent, key_name)
            return
        if isinstance(value, dict):
            self._render_dict(value, output, indent, key_name)
            return
        if isinstance(value, (list, tuple)):
            self._render_sequence(value, output, indent, key_name)
            return
        scalar = self._truncate_str(str(value), 200)  # Generic scalar fallback
        self._emit_simple(scalar, output, indent, key_name)

    def _render_dict(self, value: dict[str, Any], output: list[str], indent: int, key_name: str | None) -> None:
        """Emit the header + each key for a dict value."""
        indent_str = "  " * indent  # Per-depth indent
        header = (
            f"{indent_str}{key_name}: dict ({len(value)} keys)" if key_name else f"{indent_str}dict ({len(value)} keys)"
        )
        output.append(header)
        for child_key, child_value in value.items():  # Walk every entry
            self._render_dict_entry(child_key, child_value, output, indent)

    def _render_dict_entry(self, key: str, child_value: Any, output: list[str], indent: int) -> None:
        """Emit a single key from a dict. Recurse into nested structures."""
        if isinstance(child_value, (dict, list)):  # Recurse for nested structures
            self._render(child_value, output, indent + 1, key_name=key)
            return
        indent_str = "  " * indent  # Indent for inline scalar entries
        value_str = self._truncate_str(str(child_value), 60)  # Short inline value
        output.append(f"{indent_str}  {key}: {value_str}")

    def _render_sequence(self, value: Any, output: list[str], indent: int, key_name: str | None) -> None:
        """Emit the header + first ``MAX_SAMPLE_ITEMS`` items for a sequence."""
        indent_str = "  " * indent  # Per-depth indent
        item_count = len(value)  # Count for header
        type_name = "list" if isinstance(value, list) else "tuple"  # Tuple vs list label
        header = (
            f"{indent_str}{key_name}: {type_name} ({item_count} items)"
            if key_name
            else f"{indent_str}{type_name} ({item_count} items)"
        )
        output.append(header)
        if item_count == 0:  # Empty short-circuit
            output.append(f"{indent_str}  (empty)")
            return
        display_count = min(MAX_SAMPLE_ITEMS, item_count)  # How many to show
        for idx in range(display_count):  # Walk first N items
            self._render_sequence_item(value[idx], output, indent, idx)
        if item_count > display_count:  # Truncation indicator
            output.append(f"{indent_str}  ... {item_count - display_count} more items")

    def _render_sequence_item(self, item: Any, output: list[str], indent: int, idx: int) -> None:
        """Emit one item of a sequence. Recurse for nested types."""
        indent_str = "  " * indent  # Indent for the item line
        if isinstance(item, dict):  # Dict item -> show key sample
            output.append(f"{indent_str}  [{idx}]: dict ({len(item)} keys)")
            for key, val in list(item.items())[:3]:  # Show at most 3 key:value pairs
                v_str = self._truncate_str(str(val), 50)
                output.append(f"{indent_str}    {key}: {v_str}")
            if len(item) > 3:  # Indicate omitted keys
                output.append(f"{indent_str}    ... {len(item) - 3} more keys")
            return
        if isinstance(item, (list, tuple)):  # Nested sequence -> recurse
            self._render(item, output, indent + 1, key_name=f"[{idx}]")
            return
        item_str = self._truncate_str(str(item), 60)  # Scalar item
        output.append(f"{indent_str}  [{idx}]: {item_str}")

    @staticmethod
    def _emit_simple(value_str: str, output: list[str], indent: int, key_name: str | None) -> None:
        """Append a single ``indent + key: value`` line (or just value)."""
        indent_str = "  " * indent  # Per-depth indent
        if key_name:
            output.append(f"{indent_str}{key_name}: {value_str}")
            return
        output.append(f"{indent_str}{value_str}")

    @staticmethod
    def _truncate_str(value: str, limit: int) -> str:
        """Return ``value`` truncated to ``limit`` chars with ellipsis suffix."""
        if len(value) > limit:  # Only truncate when over limit
            return value[:limit] + "..."
        return value
