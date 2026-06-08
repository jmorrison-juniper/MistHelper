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


# Install once at module import so the launcher import below can resolve
# ``from dash import ...`` lazily inside register_with. The autouse fixture
# below replaces and restores per-test to avoid leaking the stub into other
# test modules (which probe dash via importlib.util.find_spec).
sys.modules["dash"] = _build_dash_stub()

from src.maps.launcher import MapViewerCallbacks, MapViewerState  # noqa: E402


@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[None]:
    """Per-test: install fresh stub, restore original on teardown."""
    original = sys.modules.get("dash")  # Snapshot for restoration
    sys.modules["dash"] = _build_dash_stub()  # Fresh stub for this test
    try:
        yield  # Test executes here
    finally:
        if original is None:
            sys.modules.pop("dash", None)  # Remove our stub entirely
        else:
            sys.modules["dash"] = original  # Restore whatever was there before


class _FakeCallbackManager:
    """Minimal stand-in for PlotlyMapCallbackManager (records calls)."""

    def __init__(self) -> None:
        self.toggle_calls: list[dict[str, Any]] = []  # Capture toggle_layers args
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

    assert len(app.registered) == 5  # Wave-A registers five callbacks
    # Each registration must have a bound method (decorator was invoked)
    for record in app.registered:
        assert record.bound_func is not None  # Decorator was applied
    # Methods should match the wave-A set (by attribute name on the class)
    bound_names = {record.bound_func.__name__ for record in app.registered}
    assert bound_names == {
        "toggle_layers",
        "display_click_data",
        "toggle_origin_mode",
        "toggle_zone_name_input",
        "toggle_auto_refresh",
    }


def test_register_with_prevents_initial_call_on_three_callbacks() -> None:
    """toggle_origin_mode / toggle_zone_name_input / toggle_auto_refresh use prevent_initial_call=True."""
    state = MapViewerState(callback_manager=_FakeCallbackManager())  # Minimal state
    callbacks = MapViewerCallbacks(state=state)  # Subject under test
    app = _FakeDashApp()  # Records registrations

    callbacks.register_with(app)  # Wire callbacks

    pic_names = {record.bound_func.__name__ for record in app.registered if record.kwargs.get("prevent_initial_call")}
    assert pic_names == {
        "toggle_origin_mode",
        "toggle_zone_name_input",
        "toggle_auto_refresh",
    }


# ---------------------------------------------------------------------------
# MapViewerCallbacks: individual callback behavior
# ---------------------------------------------------------------------------


def test_toggle_layers_delegates_to_callback_manager() -> None:
    """toggle_layers forwards all five layer inputs and current figure."""
    manager = _FakeCallbackManager()  # Records the call
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=manager))
    fig = {"data": [], "layout": {}}  # Sentinel figure

    result = callbacks.toggle_layers(
        infra_layers=["walls"],
        beacon_layers=[],
        client_layers=["clients"],
        device_layers=["aps"],
        filter_layers=[],
        current_fig=fig,
    )

    assert result == {"updated": True}  # Returned the manager's sentinel
    assert len(manager.toggle_calls) == 1  # Called exactly once
    captured = manager.toggle_calls[0]  # Inspect captured kwargs
    assert captured["current_fig"] is fig  # Same figure object forwarded
    assert captured["infra_layers"] == ["walls"]  # Forwarded by keyword
    assert captured["device_layers"] == ["aps"]  # Forwarded by keyword


def test_display_click_data_delegates_to_callback_manager() -> None:
    """display_click_data passes clickData plus the dash.html module."""
    manager = _FakeCallbackManager()  # Records the call
    callbacks = MapViewerCallbacks(state=MapViewerState(callback_manager=manager))
    click = {"points": [{"x": 1, "y": 2}]}  # Sentinel clickData dict

    result = callbacks.display_click_data(click_data=click)

    assert result == {"panel": "details"}  # Returned the manager's sentinel
    assert len(manager.click_calls) == 1  # Called exactly once
    captured = manager.click_calls[0]  # Inspect captured kwargs
    assert captured["click_data"] is click  # Same dict forwarded
    assert captured["html"] is not None  # dash.html module forwarded


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
