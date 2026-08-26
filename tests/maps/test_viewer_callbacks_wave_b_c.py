"""Unit tests for waves B + C of the Plotly viewer callback extraction.

Covers:

* :class:`MapViewerState` accepts the new fields added by waves B + C
  (``zones``, ``map_id``, ``site_id``, ``api_session_ref``, ``ppm``,
  ``mistapi_ref``, ``maps_manager_ref``).
* :class:`MapViewerCallbacks.register_with` registers the eight new
  callbacks with byte-identical decorator arguments.
* Per-callback behavior tests for the non-trivial callbacks:
  ``set_origin_from_click``, ``execute_delete_map``,
  ``handle_zone_actions``, and ``update_shape_labels``.

Mirrors the dash-stub + autouse-fixture pattern from
``test_viewer_callbacks_wave_a.py``.
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
    dash_stub.__spec__ = importlib.machinery.ModuleSpec("dash", loader=None)
    dash_stub.Input = lambda *a, **k: ("Input", a, k)  # type: ignore[attr-defined]
    dash_stub.Output = lambda *a, **k: ("Output", a, k)  # type: ignore[attr-defined]
    dash_stub.State = lambda *a, **k: ("State", a, k)  # type: ignore[attr-defined]
    dash_stub.no_update = "__NO_UPDATE__"  # type: ignore[attr-defined]
    # callback_context is a singleton-like object with a ``triggered`` attribute
    dash_stub.callback_context = types.SimpleNamespace(triggered=[])  # type: ignore[attr-defined]
    dash_stub.html = types.SimpleNamespace(  # type: ignore[attr-defined]
        P=lambda *a, **k: {"P": (a, k)},
        Div=lambda *a, **k: {"Div": (a, k)},
        H3=lambda *a, **k: {"H3": (a, k)},
        Span=lambda *a, **k: {"Span": (a, k)},
    )
    return dash_stub


sys.modules["dash"] = _build_dash_stub()  # Install before launcher imports run

from src.maps.launcher import MapViewerCallbacks, MapViewerState  # noqa: E402


@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[types.ModuleType]:
    """Per-test: install fresh stub, restore original on teardown.

    Yields the active stub so tests can mutate ``callback_context.triggered``.
    """
    original = sys.modules.get("dash")  # Snapshot for restoration
    stub = _build_dash_stub()  # Fresh stub for this test
    sys.modules["dash"] = stub
    try:
        yield stub
    finally:
        if original is None:
            sys.modules.pop("dash", None)
        else:
            sys.modules["dash"] = original


class _FakeCallbackManager:
    """Minimal stand-in for PlotlyMapCallbackManager."""

    def apply_layer_toggles(self, **_kwargs: Any) -> dict[str, Any]:
        return {}

    def build_click_details(self, **_kwargs: Any) -> dict[str, Any]:
        return {}


class _FakeResponse:
    """Minimal stand-in for a mistapi API response."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code  # HTTP status returned by Mist


class _FakeMistapi:
    """Captures mistapi delete calls so tests can assert on them."""

    def __init__(self, status_code: int = 200) -> None:
        self.delete_map_calls: list[dict[str, Any]] = []  # Captured deleteSiteMap kwargs
        self.delete_zone_calls: list[dict[str, Any]] = []  # Captured deleteSiteZone kwargs
        self._status_code = status_code  # Status to return from delete responses
        # Build the nested attribute chain mistapi.api.v1.sites.maps/zones
        delete_map = self._make_delete_map()
        delete_zone = self._make_delete_zone()
        maps_ns = types.SimpleNamespace(deleteSiteMap=delete_map)
        zones_ns = types.SimpleNamespace(deleteSiteZone=delete_zone)
        sites_ns = types.SimpleNamespace(maps=maps_ns, zones=zones_ns)
        v1_ns = types.SimpleNamespace(sites=sites_ns)
        self.api = types.SimpleNamespace(v1=v1_ns)

    def _make_delete_map(self) -> Any:
        def _delete_map(session: Any, site_id: str, map_id: str) -> _FakeResponse:
            self.delete_map_calls.append({"session": session, "site_id": site_id, "map_id": map_id})
            return _FakeResponse(self._status_code)

        return _delete_map

    def _make_delete_zone(self) -> Any:
        def _delete_zone(session: Any, site_id: str, zone_id: str) -> _FakeResponse:
            self.delete_zone_calls.append({"session": session, "site_id": site_id, "zone_id": zone_id})
            return _FakeResponse(self._status_code)

        return _delete_zone


class _FakeMapsManager:
    """Captures _backup_map_geometry calls."""

    def __init__(self, backup_path: str | None = "/tmp/backup.json") -> None:
        self.backup_calls: list[dict[str, Any]] = []  # Captured backup kwargs
        self._backup_path = backup_path  # What to return from the backup call

    def _backup_map_geometry(self, **kwargs: Any) -> str | None:
        self.backup_calls.append(kwargs)  # Record for assertion
        return self._backup_path  # Sentinel path or None


class _RecordedCallback:
    """Captures arguments passed to a single ``app.callback(...)`` call."""

    def __init__(self, args: tuple, kwargs: dict[str, Any]) -> None:
        self.args = args
        self.kwargs = kwargs
        self.bound_func: Any = None


class _FakeDashApp:
    """Minimal Dash app stub that records callback registrations."""

    def __init__(self) -> None:
        self.registered: list[_RecordedCallback] = []

    def callback(self, *args: Any, **kwargs: Any):
        record = _RecordedCallback(args=args, kwargs=kwargs)
        self.registered.append(record)

        def _decorator(func: Any) -> Any:
            record.bound_func = func
            return func

        return _decorator


def _make_state(**overrides: Any) -> MapViewerState:
    """Build a MapViewerState with sensible defaults for tests."""
    defaults: dict[str, Any] = {
        "callback_manager": _FakeCallbackManager(),
        "zones": [],
        "map_id": "test-map-id",
        "site_id": "test-site-id",
        "api_session_ref": object(),
        "ppm": 10.0,
        "mistapi_ref": _FakeMistapi(),
        "maps_manager_ref": _FakeMapsManager(),
    }
    defaults.update(overrides)
    return MapViewerState(**defaults)


# ---------------------------------------------------------------------------
# MapViewerState: new fields
# ---------------------------------------------------------------------------


def test_state_accepts_wave_b_and_c_fields() -> None:
    """MapViewerState exposes every new wave-B/C field."""
    sentinel_session = object()  # Identity check below
    sentinel_mistapi = object()
    sentinel_manager = object()
    zones = [{"id": "z1", "name": "Z1"}]
    state = MapViewerState(
        callback_manager=_FakeCallbackManager(),
        zones=zones,
        map_id="m1",
        site_id="s1",
        api_session_ref=sentinel_session,
        ppm=42.5,
        mistapi_ref=sentinel_mistapi,
        maps_manager_ref=sentinel_manager,
    )
    assert state.zones is zones
    assert state.map_id == "m1"
    assert state.site_id == "s1"
    assert state.api_session_ref is sentinel_session
    assert state.ppm == 42.5
    assert state.mistapi_ref is sentinel_mistapi
    assert state.maps_manager_ref is sentinel_manager


def test_state_defaults_when_only_callback_manager_supplied() -> None:
    """Wave-A only callers can still construct MapViewerState with the new defaults."""
    state = MapViewerState(callback_manager=_FakeCallbackManager())
    assert state.zones == []
    assert state.map_id is None
    assert state.site_id is None
    assert state.api_session_ref is None
    assert state.ppm == 10.0
    assert state.mistapi_ref is None
    assert state.maps_manager_ref is None


# ---------------------------------------------------------------------------
# MapViewerCallbacks: registration
# ---------------------------------------------------------------------------


def test_register_with_wires_thirteen_callbacks_total() -> None:
    """register_with wires 5 wave-A + 4 wave-B + 4 wave-C callbacks (+ 3 wave-D = 16 total)."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    assert len(app.registered) == 24  # waves A+B+C+D+E1+E2

    bound_names = {record.bound_func.__name__ for record in app.registered}
    expected_wave_b = {
        "toggle_individual_zones",
        "toggle_delete_panel",
        "toggle_clone_panel",
        "handle_utilities",
    }
    expected_wave_c = {
        "update_shape_labels",
        "set_origin_from_click",
        "execute_delete_map",
        "handle_zone_actions",
    }
    assert expected_wave_b.issubset(bound_names)
    assert expected_wave_c.issubset(bound_names)


def test_register_with_prevents_initial_call_on_all_new_callbacks() -> None:
    """Every wave-B and wave-C callback uses prevent_initial_call=True."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    new_callback_names = {
        "toggle_individual_zones",
        "toggle_delete_panel",
        "toggle_clone_panel",
        "handle_utilities",
        "update_shape_labels",
        "set_origin_from_click",
        "execute_delete_map",
        "handle_zone_actions",
    }
    for record in app.registered:
        if record.bound_func.__name__ in new_callback_names:
            assert record.kwargs.get("prevent_initial_call") is True


# ---------------------------------------------------------------------------
# Wave B: toggle_individual_zones
# ---------------------------------------------------------------------------


def test_toggle_individual_zones_returns_unchanged_when_no_zones() -> None:
    """Empty zones list means no traces to toggle."""
    callbacks = MapViewerCallbacks(state=_make_state(zones=[]))
    fig = {"data": [{"name": "Zone: A", "visible": True}]}

    result = callbacks.toggle_individual_zones(["zone-a"], fig)

    assert result is fig
    assert fig["data"][0]["visible"] is True  # Unchanged


def test_toggle_individual_zones_flips_visibility_by_id() -> None:
    """Traces named Zone: X get visibility set based on zone id membership."""
    zones = [{"id": "id-a", "name": "A"}, {"id": "id-b", "name": "B"}]
    callbacks = MapViewerCallbacks(state=_make_state(zones=zones))
    fig = {
        "data": [
            {"name": "Zone: A", "visible": False},
            {"name": "Zone: B", "visible": True},
            {"name": "Other", "visible": True},
        ]
    }

    callbacks.toggle_individual_zones(["id-a"], fig)

    assert fig["data"][0]["visible"] is True  # id-a is selected
    assert fig["data"][1]["visible"] is False  # id-b not selected
    assert fig["data"][2]["visible"] is True  # Non-zone trace untouched


# ---------------------------------------------------------------------------
# Wave B: toggle_delete_panel / toggle_clone_panel / handle_utilities
# ---------------------------------------------------------------------------


def test_toggle_delete_panel_no_trigger_returns_no_update(_dash_stub: types.ModuleType) -> None:
    """Without a trigger, return current style + no_update."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = []

    style, name = callbacks.toggle_delete_panel(0, 0, 0, {"display": "block"}, None)

    assert style == {"display": "block"}
    assert name == "__NO_UPDATE__"


def test_toggle_delete_panel_open_shows_block(_dash_stub: types.ModuleType) -> None:
    """delete-btn trigger shows the panel with the current map name."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "delete-btn.n_clicks"}]

    style, name = callbacks.toggle_delete_panel(1, 0, 0, {}, {"map_name": "FloorOne"})

    assert style["display"] == "block"
    assert name == "Map: FloorOne"


def test_toggle_delete_panel_cancel_hides(_dash_stub: types.ModuleType) -> None:
    """cancel-delete-btn / confirm-delete-btn hide the panel."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "cancel-delete-btn.n_clicks"}]

    style, name = callbacks.toggle_delete_panel(0, 1, 0, {}, {"map_name": "x"})

    assert style["display"] == "none"
    assert name == "__NO_UPDATE__"


def test_toggle_clone_panel_open_shows_block(_dash_stub: types.ModuleType) -> None:
    """clone-btn trigger shows the panel."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "clone-btn.n_clicks"}]

    style = callbacks.toggle_clone_panel(1, 0, 0, {})

    assert style["display"] == "block"


def test_toggle_clone_panel_cancel_hides(_dash_stub: types.ModuleType) -> None:
    """cancel-clone-btn / execute-clone-btn hide the panel."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "execute-clone-btn.n_clicks"}]

    style = callbacks.toggle_clone_panel(0, 0, 1, {})

    assert style["display"] == "none"


def test_handle_utilities_no_trigger_returns_empty(_dash_stub: types.ModuleType) -> None:
    """Without a trigger, return empty string."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = []

    assert callbacks.handle_utilities(0, 0, 0, 0) == ""


@pytest.mark.parametrize(
    "button_id",
    ["auto-zone-btn", "change-image-btn", "remove-image-btn", "rename-btn"],
)
def test_handle_utilities_each_button_returns_span(_dash_stub: types.ModuleType, button_id: str) -> None:
    """Every utilities button returns a non-empty Span output."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": f"{button_id}.n_clicks"}]

    result = callbacks.handle_utilities(1, 1, 1, 1)

    assert isinstance(result, dict)
    assert "Span" in result


# ---------------------------------------------------------------------------
# Wave C: update_shape_labels
# ---------------------------------------------------------------------------


def test_update_shape_labels_no_relayout_data_returns_unchanged() -> None:
    """Without relayoutData the figure passes through untouched."""
    callbacks = MapViewerCallbacks(state=_make_state())
    fig = {"layout": {"shapes": []}}

    assert callbacks.update_shape_labels(None, fig) is fig


def test_update_shape_labels_appends_annotation_for_line_shape() -> None:
    """A line shape produces an annotation in layout.annotations."""
    callbacks = MapViewerCallbacks(state=_make_state(ppm=10.0))
    fig = {
        "layout": {
            "shapes": [{"type": "line", "x0": 0, "y0": 0, "x1": 30, "y1": 40}],
        },
        "data": [],
    }

    callbacks.update_shape_labels({"shapes": []}, fig)

    annotations = fig["layout"]["annotations"]
    assert len(annotations) == 1
    text = annotations[0]["text"]
    assert "50.0 px" in text  # sqrt(30^2 + 40^2) = 50
    assert "5.00 m" in text  # 50 / 10 ppm = 5 meters


def test_update_shape_labels_respects_meta_ppm_override() -> None:
    """When layout.meta.ppm exists, it overrides the state default."""
    callbacks = MapViewerCallbacks(state=_make_state(ppm=10.0))
    fig = {
        "layout": {
            "meta": {"ppm": 50.0},  # User-calibrated PPM
            "shapes": [{"type": "line", "x0": 0, "y0": 0, "x1": 50, "y1": 0}],
        }
    }

    callbacks.update_shape_labels({"shapes": []}, fig)

    text = fig["layout"]["annotations"][0]["text"]
    assert "1.00 m" in text  # 50 px / 50 ppm = 1 meter


# ---------------------------------------------------------------------------
# Wave C: set_origin_from_click
# ---------------------------------------------------------------------------


def test_set_origin_from_click_mode_inactive_returns_current() -> None:
    """When mode is inactive (even clicks), return the current origin label."""
    callbacks = MapViewerCallbacks(state=_make_state())
    fig = {"layout": {"meta": {"origin_x": 100, "origin_y": 200}}, "data": []}

    status, returned_fig = callbacks.set_origin_from_click({"points": [{"x": 1, "y": 2}]}, 0, fig)

    assert returned_fig is fig
    # The status is a list containing one html.P stub dict
    assert isinstance(status, list)
    assert len(status) == 1


def test_set_origin_from_click_mode_active_no_click() -> None:
    """When mode is active but clickData missing, prompt the user."""
    callbacks = MapViewerCallbacks(state=_make_state())
    fig = {"layout": {"meta": {}}, "data": []}

    status, returned_fig = callbacks.set_origin_from_click(None, 1, fig)

    assert returned_fig is fig
    assert isinstance(status, list)


def test_set_origin_from_click_sets_meta_and_updates_traces() -> None:
    """A click in active mode updates layout.meta and crosshair traces."""
    callbacks = MapViewerCallbacks(state=_make_state())
    fig = {
        "layout": {},
        "data": [
            {"name": "Origin", "x": [0, 0], "y": [0, 0], "hovertext": ""},
            {"name": "Origin Point", "x": [0], "y": [0], "hovertext": ""},
        ],
    }
    click = {"points": [{"x": 150.0, "y": 250.0}]}

    status, returned_fig = callbacks.set_origin_from_click(click, 1, fig)

    assert returned_fig is fig
    assert fig["layout"]["meta"]["origin_x"] == 150.0
    assert fig["layout"]["meta"]["origin_y"] == 250.0
    assert fig["data"][0]["y"] == [250.0, 250.0]  # Horizontal arm at new Y
    assert fig["data"][1]["x"] == [150.0]  # Center dot moved
    assert isinstance(status, list)
    assert len(status) == 2  # Confirmation + hint


# ---------------------------------------------------------------------------
# Wave C: execute_delete_map
# ---------------------------------------------------------------------------


def test_execute_delete_map_no_confirm_returns_empty() -> None:
    """Without confirm_clicks, no API call is made."""
    fake = _FakeMistapi()
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake))

    status, cache = callbacks.execute_delete_map(0, None, None)

    assert status == ""
    assert cache == "__NO_UPDATE__"
    assert fake.delete_map_calls == []


def test_execute_delete_map_success_increments_cache_bust() -> None:
    """On 200 response, return a Span and increment cache bust trigger."""
    fake = _FakeMistapi(status_code=200)
    manager = _FakeMapsManager(backup_path="/tmp/b.json")
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake, maps_manager_ref=manager))
    config = {"site_id": "s1", "map_id": "m1", "map_name": "Floor"}

    status, cache = callbacks.execute_delete_map(1, {"trigger": 5}, config)

    assert isinstance(status, dict) and "Span" in status
    assert cache == {"trigger": 6}
    assert len(fake.delete_map_calls) == 1
    assert fake.delete_map_calls[0]["site_id"] == "s1"
    assert fake.delete_map_calls[0]["map_id"] == "m1"
    assert len(manager.backup_calls) == 1
    assert manager.backup_calls[0]["backup_reason"] == "pre_delete"


def test_execute_delete_map_http_failure_no_cache_bust() -> None:
    """Non-2xx response returns Span + no_update."""
    fake = _FakeMistapi(status_code=500)
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake))

    status, cache = callbacks.execute_delete_map(1, {"trigger": 0}, {"site_id": "s", "map_id": "m"})

    assert isinstance(status, dict) and "Span" in status
    assert cache == "__NO_UPDATE__"


def test_execute_delete_map_exception_returns_span() -> None:
    """An exception is caught and surfaced as an error Span."""

    class _BrokenMistapi:
        class api:  # mimic mistapi attribute style
            class v1:
                class sites:
                    class maps:
                        @staticmethod
                        def deleteSiteMap(*_a: Any, **_k: Any) -> None:
                            raise RuntimeError("network boom")

    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=_BrokenMistapi()))

    status, cache = callbacks.execute_delete_map(1, None, {"site_id": "s", "map_id": "m"})

    assert isinstance(status, dict) and "Span" in status
    assert cache == "__NO_UPDATE__"


# ---------------------------------------------------------------------------
# Wave C: handle_zone_actions
# ---------------------------------------------------------------------------


def test_handle_zone_actions_no_trigger_returns_prompt(_dash_stub: types.ModuleType) -> None:
    """Without a trigger, returns the 'click a zone' prompt + selection."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = []

    info, selection = callbacks.handle_zone_actions(0, 0, None, None)

    assert isinstance(info, dict) and "P" in info
    assert selection == {"zone_id": None, "zone_name": None}


def test_handle_zone_actions_edit_with_selection(_dash_stub: types.ModuleType) -> None:
    """edit-zone-btn with a selected zone renders the edit hint."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "edit-zone-btn.n_clicks"}]
    selected = {"zone_id": "z1", "zone_name": "Lobby"}

    info, returned = callbacks.handle_zone_actions(1, 0, None, selected)

    assert isinstance(info, dict) and "Div" in info
    assert returned == selected


def test_handle_zone_actions_edit_without_selection(_dash_stub: types.ModuleType) -> None:
    """edit-zone-btn with no selection prompts the user to select first."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "edit-zone-btn.n_clicks"}]

    info, _returned = callbacks.handle_zone_actions(1, 0, None, None)

    assert isinstance(info, dict) and "Div" in info


def test_handle_zone_actions_remove_calls_delete_api(_dash_stub: types.ModuleType) -> None:
    """remove-zone-btn with a selection invokes deleteSiteZone."""
    fake = _FakeMistapi(status_code=200)
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake))
    _dash_stub.callback_context.triggered = [{"prop_id": "remove-zone-btn.n_clicks"}]
    selected = {"zone_id": "z9", "zone_name": "Cafe"}

    info, new_selection = callbacks.handle_zone_actions(0, 1, None, selected)

    assert isinstance(info, dict) and "Div" in info
    assert new_selection == {"zone_id": None, "zone_name": None}
    assert len(fake.delete_zone_calls) == 1
    assert fake.delete_zone_calls[0]["zone_id"] == "z9"
    assert fake.delete_zone_calls[0]["site_id"] == "test-site-id"


def test_handle_zone_actions_remove_http_failure(_dash_stub: types.ModuleType) -> None:
    """Non-2xx zone delete returns the failure Div and keeps selection."""
    fake = _FakeMistapi(status_code=500)
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake))
    _dash_stub.callback_context.triggered = [{"prop_id": "remove-zone-btn.n_clicks"}]
    selected = {"zone_id": "z9", "zone_name": "Cafe"}

    info, new_selection = callbacks.handle_zone_actions(0, 1, None, selected)

    assert isinstance(info, dict) and "Div" in info
    assert new_selection == selected


def test_handle_zone_actions_click_selects_zone(_dash_stub: types.ModuleType) -> None:
    """Clicking a zone-named point updates the selected-zone-store."""
    zones = [{"id": "abc12345-0000-0000-0000-000000000000", "name": "Atrium"}]
    callbacks = MapViewerCallbacks(state=_make_state(zones=zones))
    _dash_stub.callback_context.triggered = [{"prop_id": "map-display.clickData"}]
    click = {"points": [{"hovertext": "Zone: Atrium"}]}

    info, new_selection = callbacks.handle_zone_actions(0, 0, click, None)

    assert isinstance(info, dict) and "Div" in info
    assert new_selection["zone_name"] == "Atrium"
    assert new_selection["zone_id"] == "abc12345-0000-0000-0000-000000000000"


def test_handle_zone_actions_click_non_zone_returns_prompt(_dash_stub: types.ModuleType) -> None:
    """Clicking a non-zone point keeps the current selection and shows prompt."""
    callbacks = MapViewerCallbacks(state=_make_state())
    _dash_stub.callback_context.triggered = [{"prop_id": "map-display.clickData"}]
    click = {"points": [{"hovertext": "AP-1"}]}
    selected = {"zone_id": "z1", "zone_name": "Lobby"}

    info, new_selection = callbacks.handle_zone_actions(0, 0, click, selected)

    assert isinstance(info, dict)
    assert new_selection == selected  # Unchanged
