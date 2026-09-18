"""Unit tests for ConfigUtils blind-handler narrowing."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest collection.

from unittest.mock import patch  # WHY: patch the optional import path deterministically.

import pytest  # WHY: assert propagation for non-import failures.

from src.config.config_utils import ConfigUtils  # WHY: subject under test for issue #2834.


def test_runtime_context_returns_none_when_entrypoint_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing entry point import keeps the local cache path."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # WHY: force the optional import branch during pytest.
    with patch(  # WHY: simulate the optional entry point missing during partial startup.
        "src.config.config_utils.importlib.import_module",
        side_effect=ImportError("missing entry point"),
    ):
        assert ConfigUtils._runtime_context() is None  # WHY: import failures still use the fallback path.


def test_runtime_context_non_import_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected import failures must propagate."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # WHY: force the optional import branch during pytest.
    with (  # WHY: prove the narrowed handler no longer hides programming faults.
        patch(  # WHY: simulate an unexpected loader failure outside the narrowed contract.
            "src.config.config_utils.importlib.import_module",
            side_effect=RuntimeError("loader failed"),
        ),
        pytest.raises(RuntimeError),  # WHY: callers must see unexpected runtime failures.
    ):
        ConfigUtils._runtime_context()  # WHY: execute the changed handler.
