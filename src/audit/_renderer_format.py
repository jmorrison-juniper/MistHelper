"""HTML delta-value formatter for :mod:`src.audit.renderer`.

Renders a recursive ``dict`` / ``list`` structure into an indented JSON-like
HTML fragment where the leaf values (the actual changed data) are wrapped
in ``<b>`` tags. Extracted from ``renderer.py`` to isolate the recursive
walker and to keep each helper under the compliance budget.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import html  # WHY: escape user-supplied strings before embedding in HTML
import json  # WHY: canonical JSON quoting for keys and leaf scalars
from dataclasses import dataclass  # WHY: bundle dict-item params under STRUCT-PARAMS limit


@dataclass(frozen=True)  # WHY: immutable bundle passed into per-item renderer
class _DictItemCtx:
    """Per-entry state for rendering one ``key: value`` line inside a dict."""

    key: object  # WHY: dict key to be JSON-quoted then HTML-escaped
    val: object  # WHY: dict value that recurses back through format_delta_html
    idx: int  # WHY: 0-based entry index; drives trailing comma placement
    total: int  # WHY: total entry count; comparator for last-item check
    inner_pad: str  # WHY: precomputed indentation prefix for this entry
    indent: int  # WHY: recursion depth passed to the child call


def format_delta_html(obj: object, indent: int = 0) -> str:  # WHY: entry point used by HTML cluster
    """Render a delta object as indented HTML with bold leaf values."""
    if isinstance(obj, dict):  # WHY: dict branch produces {} block
        return _format_dict(obj, indent)
    if isinstance(obj, list):  # WHY: list branch produces [] block
        return _format_list(obj, indent)
    return _format_leaf(obj)  # WHY: scalars are the only remaining case


def _format_dict(obj: dict[object, object], indent: int) -> str:  # WHY: dict-branch helper
    """Render a dict as a bracketed, indented HTML block."""
    if not obj:  # WHY: preserve compact empty-dict rendering
        return "{}"
    pad = "  " * indent  # WHY: indentation for the closing brace
    inner_pad = "  " * (indent + 1)  # WHY: indentation for entries
    items = list(obj.items())  # WHY: materialize for len-aware comma logic
    total = len(items)  # WHY: cache length so per-entry ctx stays uniform
    lines = ["{"]  # WHY: opening brace on its own line
    for idx, (key, val) in enumerate(items):  # WHY: idx drives trailing-comma placement
        ctx = _DictItemCtx(  # WHY: bundle six params into a single ctx object
            key=key,
            val=val,
            idx=idx,
            total=total,
            inner_pad=inner_pad,
            indent=indent,
        )
        lines.append(_render_dict_item(ctx))  # WHY: append one rendered entry line
    lines.append(f"{pad}}}")  # WHY: closing brace aligned with parent indent
    return "\n".join(lines)


def _render_dict_item(ctx: _DictItemCtx) -> str:  # WHY: takes ctx to satisfy STRUCT-PARAMS limit
    """Render a single ``key: value`` entry with optional trailing comma."""
    comma = "," if ctx.idx < ctx.total - 1 else ""  # WHY: JSON-style trailing comma omitted on last item
    rendered = format_delta_html(ctx.val, ctx.indent + 1)  # WHY: recurse to nest deeper structures
    safe_key = html.escape(json.dumps(ctx.key))  # WHY: json quoting + HTML escape guards embedded quotes
    return f"{ctx.inner_pad}{safe_key}: {rendered}{comma}"  # WHY: final one-line entry


def _format_list(obj: list[object], indent: int) -> str:  # WHY: list-branch helper
    """Render a list as a bracketed, indented HTML block."""
    if not obj:  # WHY: preserve compact empty-list rendering
        return "[]"
    pad = "  " * indent  # WHY: indentation for the closing bracket
    inner_pad = "  " * (indent + 1)  # WHY: indentation for elements
    lines = ["["]  # WHY: opening bracket on its own line
    total = len(obj)  # WHY: cache length for trailing-comma logic
    for idx, item in enumerate(obj):  # WHY: idx drives trailing-comma placement
        comma = "," if idx < total - 1 else ""  # WHY: trailing comma omitted on last element
        rendered = format_delta_html(item, indent + 1)  # WHY: recurse into nested items
        lines.append(f"{inner_pad}{rendered}{comma}")  # WHY: append one rendered element line
    lines.append(f"{pad}]")  # WHY: closing bracket aligned with parent indent
    return "\n".join(lines)


def _format_leaf(obj: object) -> str:  # WHY: scalar-branch helper
    """Render a scalar leaf value inside ``<b>`` tags."""
    safe_val = html.escape(json.dumps(obj, default=str))  # WHY: escape after JSON encoding
    return f"<b>{safe_val}</b>"  # WHY: leaf styling signals the actual changed datum
