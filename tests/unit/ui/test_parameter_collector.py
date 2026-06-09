"""Unit tests for src/ui/execution/parameter_collector.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ui.execution.parameter_collector import ParameterCollector


def _make_collector(tui_stub) -> ParameterCollector:
    """Build a ParameterCollector wired with a MagicMock executor."""
    executor = MagicMock()  # FunctionExecutor stand-in
    return ParameterCollector(tui_stub, executor)


def test_submit_guards_when_no_pending_param(tui_stub) -> None:
    """submit() returns silently when current_param_index is past the end."""
    tui_stub.param_list = [{"name": "x", "has_default": False}]  # One param defined
    tui_stub.current_param_index = 1  # ... but already past it
    collector = _make_collector(tui_stub)  # Build collector
    collector.submit()  # Should be a no-op
    collector._executor.execute.assert_not_called()  # Executor never invoked


def test_submit_empty_value_required_param_sets_error(tui_stub) -> None:
    """Empty input on a required parameter surfaces an [ERROR] line."""
    tui_stub.param_list = [{"name": "site_id", "has_default": False}]
    tui_stub.current_param_index = 0  # Pointing at the param
    tui_stub.input_buffer = ""  # Nothing typed
    _make_collector(tui_stub).submit()  # Try submit
    assert tui_stub.output_lines == ["[ERROR] site_id is required"]  # Error surfaced
    assert tui_stub.current_param_index == 0  # Index NOT advanced


def test_submit_empty_value_optional_param_stores_none(tui_stub) -> None:
    """Optional empty value stores None (except 'limit' default)."""
    tui_stub.param_list = [{"name": "filter", "has_default": True, "default": None}]
    tui_stub.current_param_index = 0  # Pointing at the param
    tui_stub.input_buffer = ""  # Empty input
    collector = _make_collector(tui_stub)  # Build
    collector.submit()  # Submit empty
    assert tui_stub.function_params == {"filter": None}  # Stored as None
    assert tui_stub.current_param_index == 1  # Advanced past param
    collector._executor.execute.assert_called_once()  # End of list -> run


def test_submit_empty_limit_defaults_to_1000(tui_stub) -> None:
    """Empty input for parameter named 'limit' defaults to 1000."""
    tui_stub.param_list = [{"name": "limit", "has_default": True, "default": 100}]
    tui_stub.current_param_index = 0  # Pointing at limit
    tui_stub.input_buffer = ""  # Empty input
    _make_collector(tui_stub).submit()  # Submit
    assert tui_stub.function_params == {"limit": 1000}  # Default 1000 applied


def test_submit_int_limit_converts_to_int(tui_stub) -> None:
    """Typed numeric for 'limit' is converted to int."""
    tui_stub.param_list = [{"name": "limit", "has_default": True, "default": 100}]
    tui_stub.current_param_index = 0
    tui_stub.input_buffer = "  250  "  # Whitespace + valid number
    _make_collector(tui_stub).submit()  # Submit
    assert tui_stub.function_params == {"limit": 250}  # Coerced to int


def test_submit_non_numeric_limit_sets_error(tui_stub) -> None:
    """Non-numeric input for 'limit' shows an error and stops."""
    tui_stub.param_list = [{"name": "limit", "has_default": True, "default": 100}]
    tui_stub.current_param_index = 0
    tui_stub.input_buffer = "abc"  # Invalid number
    collector = _make_collector(tui_stub)  # Build
    collector.submit()  # Submit
    assert tui_stub.output_lines == ["[ERROR] limit must be a number"]  # Error surfaced
    assert tui_stub.current_param_index == 0  # No advance
    collector._executor.execute.assert_not_called()  # No run


def test_submit_generic_string_stored_verbatim(tui_stub) -> None:
    """Non-empty, non-'limit' values are stored as-is (whitespace stripped)."""
    tui_stub.param_list = [
        {"name": "org_id", "has_default": False},
        {"name": "site_id", "has_default": False},
    ]
    tui_stub.current_param_index = 0
    tui_stub.input_buffer = "  abc-123  "  # Whitespace gets trimmed
    collector = _make_collector(tui_stub)  # Build
    collector.submit()  # First param
    assert tui_stub.function_params == {"org_id": "abc-123"}  # Trimmed value
    assert tui_stub.current_param_index == 1  # Advanced
    collector._executor.execute.assert_not_called()  # More params remain


def test_submit_runs_executor_when_last_param_collected(tui_stub) -> None:
    """Executor.execute() is called when current_param_index passes the end."""
    tui_stub.param_list = [{"name": "x", "has_default": False}]
    tui_stub.current_param_index = 0
    tui_stub.input_buffer = "value"  # Typed value
    collector = _make_collector(tui_stub)  # Build
    collector.submit()  # Final param
    collector._executor.execute.assert_called_once()  # Executor fired


def test_submit_debug_mode_logs_redacted_secret(tui_stub, caplog: pytest.LogCaptureFixture) -> None:
    """When debug_mode is on, secret-shaped names are logged redacted."""
    tui_stub.param_list = [{"name": "api_token", "has_default": False}]
    tui_stub.current_param_index = 0
    tui_stub.input_buffer = "supersecret"  # Sensitive value
    tui_stub.debug_mode = True  # Enable debug log path
    with caplog.at_level("DEBUG"):  # Capture debug
        _make_collector(tui_stub).submit()  # Trigger logging
    assert any("Parameter stored - api_token: ***REDACTED***" in r.message for r in caplog.records)
