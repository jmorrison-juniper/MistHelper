"""Compatibility assertion helpers for next-five refactor integration tests."""

from __future__ import annotations

from collections.abc import Callable


def assert_callable_entrypoint(symbol: object, name: str) -> None:
    """Assert that a compatibility entrypoint remains callable."""
    assert callable(symbol), f"Expected callable compatibility entrypoint for {name}"


def assert_target_mapping_complete(target_names: list[str], mapping: dict[str, Callable]) -> None:
    """Assert that all required targets are present in a callable mapping."""
    assert set(target_names) == set(mapping), "Target-to-entrypoint mapping is incomplete"
    for target_name in target_names:
        assert callable(mapping[target_name]), f"Mapped entrypoint for {target_name} must be callable"
