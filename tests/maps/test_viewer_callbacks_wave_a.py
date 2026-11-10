"""Unit tests for the wave-A Plotly viewer callback extraction.

Covers:

* :class:`MapViewerState` construction.
* :class:`MapViewerCallbacks` registers the expected wave-A callbacks
  on a Dash-like app object (recording decorator arguments).
* Each callback method preserves the original behavior byte-for-byte
  for trivial input cases.
"""

from __future__ import annotations

import importlib.machinery
import sys
import types
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest


def _build_dash_stub() -> types.ModuleType:
    """Construct a synthetic ``dash`` module exposing the names we need."""
    dash_stub = types.ModuleType("dash")  # Synthetic module object
    # Provide a __spec__ so importlib.util.find_spec('dash') doesn't blow up
    # when other tests probe for dash availability later in the same session.
    dash_stub.__spec__ = importlib.machinery.ModuleSpec("dash", loader=None)
    dash_stub.Input = lambda *a, **k: ("Input", a, k)  # type: ignore[attr-defined]
    dash_stub.Output = lambda *a, **k: ("Output", a, k)  # type: ignore[attr-defined]
    dash_stub.State = lambda *a, **k: ("State", a, k)  # type: ignore[attr-defined]
    dash_stub.html = types.SimpleNamespace(  # type: ignore[attr-defined]
        P=lambda *a, **k: {"P": (a, k)},  # Stand-in for dash.html.P
        Div=lambda *a, **k: {"Div": (a, k)},  # Stand-in for dash.html.Div
        H3=lambda *a, **k: {"H3": (a, k)},  # Stand-in for dash.html.H3
    )
    return dash_stub  # Caller installs into sys.modules


class _AbsentDashModule:
    """Mark that ``dash`` was absent before the test imported its launcher."""


_ABSENT_DASH_MODULE = _AbsentDashModule()  # Distinguish an absent key from a module to restore.


@contextmanager
def _dash_stub_context() -> Iterator[types.ModuleType]:
    """Install a Dash stub while preserving the prior module state."""
    original = sys.modules.get("dash", _ABSENT_DASH_MODULE)  # Keep the exact pre-import state.
    dash_stub = _build_dash_stub()  # Give the launcher its required import names.
    sys.modules["dash"] = dash_stub  # Make the stub available to the lazy launcher import.
    try:
        yield dash_stub  # Keep the stub active for the caller's import or test.
    finally:
        if original is _ABSENT_DASH_MODULE:  # Keep an initially absent key absent.
            sys.modules.pop("dash", None)  # Remove only the stub installed here.
        else:
            sys.modules["dash"] = original  # Restore the exact module that existed before.


# The launcher imports Dash lazily, so collection needs the stub only during this import.
with _dash_stub_context():
    from src.interfaces.visualization.maps.launcher import MapViewerCallbacks, MapViewerState


@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[types.ModuleType]:
    """Install a fresh Dash stub for each test, then restore the prior state."""
    with _dash_stub_context() as dash_stub:
        yield dash_stub  # Give behavior tests the exact stub module under test.


@pytest.mark.parametrize("dash_initially_loaded", [True, False])
def test_dash_stub_context_restores_initial_state(dash_initially_loaded: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """Restore the prior Dash module or preserve its absence."""
    original = types.ModuleType("dash")  # Provide a distinct module for the identity check.
    if dash_initially_loaded:
        monkeypatch.setitem(sys.modules, "dash", original)  # Simulate a previously imported module.
    else:
        monkeypatch.delitem(sys.modules, "dash", raising=False)  # Simulate no prior import.

    with _dash_stub_context() as dash_stub:
        assert sys.modules["dash"] is dash_stub  # Confirm the context installs its own stub.

    if dash_initially_loaded:
        assert sys.modules["dash"] is original  # Preserve the exact pre-existing module.
    else:
        assert "dash" not in sys.modules  # Do not leave a stub after an absent import.


class _FakeCallbackManager:
    """Minimal stand-in for PlotlyMapCallbackManager (records calls)."""

    def __init__(self) -> None:
        self.toggle_calls: list[dict[str, Any]] = []  # Capture apply_layer_toggles args
        self.click_calls: list[dict[str, Any]] = []  # Capture build_click_details args

    def apply_layer_toggles(self, **kwargs: Any) -> dict[str, Any]:
        self.toggle_calls.append(kwargs)  # Record for assertion
        return {"updated": True}  # Sentinel figure dict returned to caller

    def build_click_details(self, **kwargs: Any) -> dict[str, Any]:
        self.click_calls.append(kwargs)  # Record for assertion
        return {"panel": "details"}  # Sentinel children dict


class _RecordedCallback:
    """Captures arguments passed to a single ``app.callback(...)`` call."""

    def __init__(self, args: tuple, kwargs: dict[str, Any]) -> None:
        self.args = args  # Positional arguments (Output(...), Input(...), ...)
        self.kwargs = kwargs  # Keyword arguments (prevent_initial_call=True, ...)
        self.bound_func: Any = None  # Filled in when the decorator is invoked


class _FakeDashApp:
    """Minimal Dash app stub that records callback registrations."""

    def __init__(self) -> None:
        self.registered: list[_RecordedCallback] = []  # All recorded registrations

    def callback(self, *args: Any, **kwargs: Any):
        record = _RecordedCallback(args=args, kwargs=kwargs)  # Capture decorator args
        self.registered.append(record)  # Track registration order

        def _decorator(func: Any) -> Any:
            record.bound_func = func  # Remember which method was wired
            return func  # Pass-through (no actual Dash behavior)

        return _decorator  # Return the inner decorator like real Dash


# ---------------------------------------------------------------------------
# MapViewerState
# ---------------------------------------------------------------------------


def test_map_viewer_state_holds_callback_manager() -> None:
    """MapViewerState exposes the injected callback manager."""
    manager = _FakeCallbackManager()  # Construct a fake collaborator
    state = MapViewerState(callback_manager=manager)  # Inject via dataclass init
    assert state.callback_manager is manager  # Identity preserved


# ---------------------------------------------------------------------------
# MapViewerCallbacks: registration
# ---------------------------------------------------------------------------


def test_register_with_wires_five_wave_a_callbacks() -> None:
    """register_with attaches exactly five callbacks with expected outputs."""
    state = MapViewerState(callback_manager=_FakeCallbackManager())  # Minimal state
    callbacks = MapViewerCallbacks(state=state)  # Subject under test
    app = _FakeDashApp()  # Records registrations

    callbacks.register_with(app)  # Trigger wiring

    # Waves B+C extend this to 13 callbacks total; wave-A subset must still appear
    assert len(app.registered) >= 5
    # Each registration must have a bound method (decorator was invoked)
    for record in app.registered:
        assert record.bound_func is not None  # Decorator was applied
    # The wave-A method names must all be present in the registered set
    bound_names = {record.bound_func.__name__ for record in app.registered}
    wave_a_names = {
        "_pack_and_apply",
        "display_click_data",
        "toggle_origin_mode",
        "toggle_zone_name_input",
        "toggle_auto_refresh",
    }
    assert wave_a_names.issubset(bound_names)


def test_register_with_prevents_initial_call_on_three_callbacks() -> None:
    """toggle_origin_mode / toggle_zone_name_input / toggle_auto_refresh use prevent_initial_call=True."""
    state = MapViewerState(callback_manager=_FakeCallbackManager())  # Minimal state
    callbacks = MapViewerCallbacks(state=state)  # Subject under test
    app = _FakeDashApp()  # Records registrations

    callbacks.register_with(app)  # Wire callbacks

    pic_names = {record.bound_func.__name__ for record in app.registered if record.kwargs.get("prevent_initial_call")}
    # Wave-A subset that uses prevent_initial_call=True must all be present
    assert {
        "toggle_origin_mode",
        "toggle_zone_name_input",
        "toggle_auto_refresh",
    }.issubset(pic_names)


# ---------------------------------------------------------------------------
# MapViewerCallbacks: individual callback behavior
# ---------------------------------------------------------------------------


def test_display_click_data_delegates_to_callback_manager(_dash_stub: types.ModuleType) -> None:
    """display_click_data passes clickData plus the dash.html module."""
    manager = _FakeCallbackManager()  # Records the call
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=manager))
    click = {"points": [{"x": 1, "y": 2}]}  # Sentinel clickData dict

    result = callbacks.display_click_data(click_data=click)

    assert result == {"panel": "details"}  # Returned the manager's sentinel
    assert len(manager.click_calls) == 1  # Called exactly once
    captured = manager.click_calls[0]  # Inspect captured kwargs
    assert captured["click_data"] is click  # Same dict forwarded
    assert captured["html"] is _dash_stub.__dict__["html"]  # The active Dash HTML object is forwarded.


@pytest.mark.parametrize(
    "n_clicks,expected_bg,expected_border",
    [
        (1, "#667eea", "2px solid #00bfff"),  # Odd => active
        (3, "#667eea", "2px solid #00bfff"),  # Still odd => active
        (2, "#3d3d3d", "1px solid #667eea"),  # Even => inactive
        (4, "#3d3d3d", "1px solid #667eea"),  # Even => inactive
    ],
)
def test_toggle_origin_mode_alternates_style(n_clicks: int, expected_bg: str, expected_border: str) -> None:
    """toggle_origin_mode toggles style based on click parity."""
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=_FakeCallbackManager()))
    style: dict[str, Any] = {"backgroundColor": "x", "border": "x"}  # Initial junk

    result = callbacks.toggle_origin_mode(n_clicks=n_clicks, current_style=style)

    assert result["backgroundColor"] == expected_bg  # Active vs inactive fill
    assert result["border"] == expected_border  # Active vs inactive border


def test_toggle_zone_name_input_shows_for_zone_mode_only() -> None:
    """toggle_zone_name_input returns block style for zone, none otherwise."""
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=_FakeCallbackManager()))

    assert callbacks.toggle_zone_name_input("zone") == {
        "display": "block",
        "marginBottom": "10px",
    }
    assert callbacks.toggle_zone_name_input("wall") == {"display": "none"}
    assert callbacks.toggle_zone_name_input("measure") == {"display": "none"}
    assert callbacks.toggle_zone_name_input(None) == {"display": "none"}


def test_toggle_auto_refresh_enabled_returns_active_intervals() -> None:
    """Enabling auto-refresh seeds timestamps and enables all intervals."""
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=_FakeCallbackManager()))

    result = callbacks.toggle_auto_refresh(toggle_value=["enabled"])

    client_disabled, coverage_disabled, tick_disabled, refresh_data, countdown = result
    assert client_disabled is False  # Interval not disabled => active
    assert coverage_disabled is False
    assert tick_disabled is False
    assert refresh_data["client_last_refresh"] > 0  # Seeded to now
    assert refresh_data["coverage_last_refresh"] > 0  # Seeded to now
    assert countdown == "Clients: 30s | RF: 5:00"  # Initial countdown label


def test_toggle_auto_refresh_disabled_returns_stopped_intervals() -> None:
    """Disabling auto-refresh zeroes timestamps and disables all intervals."""
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=_FakeCallbackManager()))

    result = callbacks.toggle_auto_refresh(toggle_value=[])

    client_disabled, coverage_disabled, tick_disabled, refresh_data, countdown = result
    assert client_disabled is True  # Interval disabled => stopped
    assert coverage_disabled is True
    assert tick_disabled is True
    assert refresh_data == {"client_last_refresh": 0, "coverage_last_refresh": 0}
    assert countdown == "Auto-refresh: Off"  # Disabled countdown label
