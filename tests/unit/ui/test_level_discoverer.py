"""Unit tests for src/ui/runtime/level_discoverer.py."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from src.ui.runtime.level_discoverer import DOC_SHORT_LIMIT, LevelDiscoverer


def _install_fake_module(monkeypatch: pytest.MonkeyPatch, dotted: str, contents: dict[str, Any]) -> types.ModuleType:
    """Install ``dotted`` into ``sys.modules`` with the given attribute mapping."""
    module = types.ModuleType(dotted)  # New empty module
    module.__package__ = dotted  # importlib emits __package__ on real modules
    for name, value in contents.items():  # Attach every name -> value
        setattr(module, name, value)
    monkeypatch.setitem(sys.modules, dotted, module)  # Make importable
    return module


def test_compose_module_path_root(tui_stub) -> None:
    """Empty current_path -> base mistapi.api.v1 module path."""
    tui_stub.current_path = []  # Root level
    assert LevelDiscoverer(tui_stub)._compose_module_path() == "mistapi.api.v1"


def test_compose_module_path_nested(tui_stub) -> None:
    """Nested current_path -> dotted suffix."""
    tui_stub.current_path = ["orgs", "sites"]  # Two-level deep nav
    assert LevelDiscoverer(tui_stub)._compose_module_path() == "mistapi.api.v1.orgs.sites"


def test_import_failure_sets_error_item(tui_stub) -> None:
    """An ImportError populates a single 'error' item and returns None."""
    tui_stub.current_path = ["doesnotexist"]  # Force ImportError
    LevelDiscoverer(tui_stub).discover()  # Run discovery
    assert tui_stub.current_items[0]["type"] == "error"  # Error sentinel set
    assert "Module not found" in tui_stub.current_items[0]["description"]


def test_discover_populates_modules_and_functions(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """Discovery records sub-modules and callables; ignores classes and dunders."""
    sub_module = _install_fake_module(monkeypatch, "mistapi.api.v1.fake.sub", {})  # Child module record

    def some_func(x: int, y: int = 5) -> int:
        """First line.\nSecond line."""
        return x + y  # Body irrelevant to discovery

    class SomeClass:  # Should be skipped (callable but is class)
        """Classes are deliberately omitted."""

    parent_contents = {
        "sub": sub_module,  # Submodule -> module record
        "some_func": some_func,  # Callable -> function record
        "SomeClass": SomeClass,  # Class -> skipped
        "_private": 1,  # Underscore prefix -> skipped
    }
    _install_fake_module(monkeypatch, "mistapi.api.v1.fake", parent_contents)  # Parent of those
    tui_stub.current_path = ["fake"]  # Point discovery at fake parent
    LevelDiscoverer(tui_stub).discover()  # Trigger walk
    names = [item["name"] for item in tui_stub.current_items]  # Extract names
    assert "sub" in names and "some_func" in names  # Both expected entries present
    assert "SomeClass" not in names and "_private" not in names  # Class + private excluded
    types_present = {item["type"] for item in tui_stub.current_items}
    assert {"module", "function"} <= types_present  # Both kinds emitted


def test_discover_sorts_modules_before_functions(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sort order: modules first then functions, each block alphabetical."""
    mod_a = _install_fake_module(monkeypatch, "mistapi.api.v1.sortme.alpha", {})  # Sub-module record

    def zebra() -> None:
        """Z function."""

    def alpha() -> None:
        """A function."""

    _install_fake_module(
        monkeypatch,
        "mistapi.api.v1.sortme",
        {"zebra": zebra, "alpha_func": alpha, "alpha": mod_a},
    )
    tui_stub.current_path = ["sortme"]  # Point at sortme
    LevelDiscoverer(tui_stub).discover()  # Run discovery
    ordered = [(item["type"], item["name"]) for item in tui_stub.current_items]
    assert ordered[0][0] == "module"  # First entry is a module
    assert ordered[-1][0] == "function"  # Last entry is a function
    # All modules precede all functions:
    last_module_idx = max(i for i, e in enumerate(ordered) if e[0] == "module")
    first_func_idx = min(i for i, e in enumerate(ordered) if e[0] == "function")
    assert last_module_idx < first_func_idx


def test_empty_module_produces_empty_sentinel(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """A module with no eligible names produces the (empty) sentinel record."""
    _install_fake_module(monkeypatch, "mistapi.api.v1.blank", {})  # No usable attributes
    tui_stub.current_path = ["blank"]  # Point at blank module
    LevelDiscoverer(tui_stub).discover()  # Trigger discovery
    assert tui_stub.current_items == [
        {"type": "empty", "name": "(empty)", "description": "No items found at this level"}
    ]


def test_short_doc_truncation_first_line_only() -> None:
    """``_short_doc`` truncates long first lines and discards subsequent lines."""
    long_doc = "x" * (DOC_SHORT_LIMIT + 50) + "\nignored second line"  # Long first line
    short = LevelDiscoverer._short_doc(long_doc)  # Static helper call
    assert short.endswith("...")  # Ellipsis appended
    assert len(short) == DOC_SHORT_LIMIT  # Capped at limit
    assert LevelDiscoverer._short_doc(None) == "No description"  # None branch
    assert LevelDiscoverer._short_doc("single line") == "single line"


def test_append_module_record_ignores_non_mistapi(tui_stub) -> None:
    """Non-mistapi sub-modules are skipped."""
    foreign = types.ModuleType("os")  # Foreign module name (not mistapi)
    foreign.__package__ = "os"  # Marks it as os package
    LevelDiscoverer(tui_stub)._append_module_record(foreign, "os")  # Should be a no-op
    assert tui_stub.current_items == []  # Nothing was appended


def test_append_function_record_uses_signature_when_available(tui_stub) -> None:
    """``_append_function_record`` extracts inspect.signature output as a string."""

    def example(a, b="x"):  # noqa: ANN001, ANN201 — bare to avoid PEP 563 stringification
        """Example docstring."""

    LevelDiscoverer(tui_stub)._append_function_record(example, "example")  # Append record
    record = tui_stub.current_items[0]  # Pulled record
    assert record["signature"] == "(a, b='x')"  # Signature captured verbatim
    assert record["full_doc"] == "Example docstring."  # Full doc preserved
    assert record["description"] == "Example docstring."  # Short matches first line


def test_append_function_record_falls_back_when_signature_fails(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """Callables whose signature cannot be introspected use the ``(...)`` placeholder."""
    import inspect as _inspect

    def _raise(_obj):  # noqa: ANN001, ANN202 — test helper
        raise ValueError("no signature")  # Force the except branch in append_function_record

    monkeypatch.setattr(_inspect, "signature", _raise)  # Patch the module symbol
    LevelDiscoverer(tui_stub)._append_function_record(lambda: None, "fn")  # Trigger fallback
    assert tui_stub.current_items[0]["signature"] == "(...)"  # Placeholder used


def test_classify_item_swallows_attribute_errors(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """An attribute that raises on access is skipped silently."""

    class _Bad:
        @property
        def boom(self) -> Any:  # Raises on every read
            raise RuntimeError("nope")

    module = _Bad()  # Object with a raising attribute
    LevelDiscoverer(tui_stub)._classify_item(module, "boom")  # Should not raise
    assert tui_stub.current_items == []  # Nothing appended
