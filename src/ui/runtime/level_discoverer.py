"""Replacement for ``MistHelperTUI._discover_current_level`` (CC=22)."""

from __future__ import annotations

import importlib
import inspect
import logging
from typing import Any

DOC_SHORT_LIMIT = 60  # Max chars to show on the items list


class LevelDiscoverer:
    """Introspect the mistapi package to populate ``tui.current_items``."""

    def __init__(self, tui: Any) -> None:
        """Store a back-reference to the owning TUI for shared state access."""
        self._tui = tui  # Back-reference for TUI state

    def discover(self) -> None:
        """Discover modules + functions at the current path; update TUI state."""
        tui = self._tui  # Local alias
        tui.current_items = []  # Reset items list
        module_path = self._compose_module_path()  # Build "mistapi.api.v1[...]" path
        tui.breadcrumb = module_path  # Update header breadcrumb
        logging.info("TUI: discovering level %s", module_path)  # Action log before import
        module = self._import_module(module_path)  # Import or set error state
        if module is None:  # Import failed -> already set
            return
        for name in dir(module):  # Walk every public name
            if name.startswith("_"):  # Skip private/internal
                continue
            self._classify_item(module, name)  # Dispatch to module/function classifier
        tui.current_items.sort(key=lambda x: (0 if x["type"] == "module" else 1, x["name"]))
        if not tui.current_items:  # Sentinel when nothing was found
            tui.current_items = [{"type": "empty", "name": "(empty)", "description": "No items found at this level"}]
        logging.debug("TUI: discovery complete - %d items at %s", len(tui.current_items), module_path)

    # ---- helpers ---------------------------------------------------------

    def _compose_module_path(self) -> str:
        """Compose the dotted module path for the current navigation level."""
        path = self._tui.current_path  # Current navigation path segments
        if not path:  # Root level
            return "mistapi.api.v1"
        return "mistapi.api.v1." + ".".join(path)  # Deeper level joined with dots

    def _import_module(self, module_path: str) -> Any:
        """Import ``module_path``; set error item on failure and return None."""
        try:
            module = importlib.import_module(module_path)  # Try the import
        except ImportError as error:  # Module not found -> show error
            logging.error("TUI: Could not import %s: %s", module_path, error)
            self._tui.current_items = [
                {
                    "type": "error",
                    "name": "Import Error",
                    "description": f"Module not found: {module_path}",
                }
            ]
            return None
        return module

    def _classify_item(self, module: Any, name: str) -> None:
        """Inspect attribute ``name`` and append a module/function record."""
        try:
            item = getattr(module, name)  # Pull the attribute value
        except Exception as error:  # Defensive: skip on access error
            logging.debug("TUI: Skipping %s: %s", name, error)
            return
        if inspect.ismodule(item):  # Sub-module branch
            self._append_module_record(item, name)
            return
        if callable(item) and not inspect.isclass(item):  # Function/method branch
            self._append_function_record(item, name)

    def _append_module_record(self, item: Any, name: str) -> None:
        """Append a module record to current_items when it's a mistapi module."""
        if not hasattr(item, "__package__"):  # No package info -> skip
            return
        if "mistapi" not in str(item.__package__):  # Only mistapi modules are listed
            return
        self._tui.current_items.append(
            {
                "type": "module",
                "name": name,
                "object": item,
                "description": f"Module: {name}",
            }
        )

    def _append_function_record(self, item: Any, name: str) -> None:
        """Append a function record (signature + truncated docstring)."""
        try:
            sig = inspect.signature(item)  # Best-effort signature extraction
            params = str(sig)
        except (ValueError, TypeError):  # Builtins may lack a real signature
            params = "(...)"
        doc = inspect.getdoc(item)  # Full docstring (or None)
        short_doc = self._short_doc(doc)  # First-line summary
        self._tui.current_items.append(
            {
                "type": "function",
                "name": name,
                "object": item,
                "signature": params,
                "description": short_doc,
                "full_doc": doc,
            }
        )

    @staticmethod
    def _short_doc(doc: str | None) -> str:
        """Return the first line of ``doc`` truncated to ``DOC_SHORT_LIMIT`` chars."""
        first_line = doc.split("\n")[0] if doc else "No description"  # Pull just the first line
        if len(first_line) > DOC_SHORT_LIMIT:  # Truncate when too long
            return first_line[: DOC_SHORT_LIMIT - 3] + "..."
        return first_line
