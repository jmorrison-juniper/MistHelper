"""Unit tests for wave E2 of the Plotly viewer callback extraction.

Covers the 6 callbacks newly on :class:`MapViewerCallbacks`:

* ``set_scale``
* ``refresh_map_dropdown``
* ``handle_site_from_url``
* ``sync_dropdown_with_url``
* ``handle_site_switch_from_dropdown``
* ``handle_url_map_switch``

Plus the new state fields on :class:`MapViewerState` (``serializer``,
``all_sites``, ``all_maps``, ``available_sites``, ``figure_builder``,
``heatmap_renderer``).
"""

from __future__ import annotations

import importlib.machinery  # Stub-spec construction
import sys  # sys.modules manipulation for stub install
import types  # ModuleType + SimpleNamespace for mistapi stubs
from collections.abc import Iterator  # Typing for fixture generator
from typing import Any  # Permissive typing for mistapi/dash stubs

import pytest  # Test fixture API


def _build_dash_stub() -> types.ModuleType:
    """Construct a synthetic ``dash`` module exposing the names we need."""
    dash_stub = types.ModuleType("dash")  # Synthetic dash module
    dash_stub.__spec__ = importlib.machinery.ModuleSpec("dash", loader=None)  # Loader spec
    dash_stub.Input = lambda *a, **k: ("Input", a, k)  # type: ignore[attr-defined]
    dash_stub.Output = lambda *a, **k: ("Output", a, k)  # type: ignore[attr-defined]
    dash_stub.State = lambda *a, **k: ("State", a, k)  # type: ignore[attr-defined]
    dash_stub.no_update = "__NO_UPDATE__"  # type: ignore[attr-defined]
    dash_stub.callback_context = types.SimpleNamespace(triggered=[])  # type: ignore[attr-defined]
    dash_stub.html = types.SimpleNamespace(  # type: ignore[attr-defined]
        P=lambda *a, **k: {"P": (a, k)},
        Div=lambda *a, **k: {"Div": (a, k)},
        Span=lambda *a, **k: {"Span": (a, k)},
    )
    return dash_stub


sys.modules["dash"] = _build_dash_stub()  # Install stub before launcher imports run

from src.maps.launcher import MapViewerCallbacks, MapViewerState  # noqa: E402


@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[types.ModuleType]:
    """Per-test: install fresh stub, restore original on teardown."""
    original = sys.modules.get("dash")  # Snapshot for restoration
    stub = _build_dash_stub()  # Fresh stub for this test
    sys.modules["dash"] = stub  # Install for this test
    try:
        yield stub
    finally:
        if original is None:
            sys.modules.pop("dash", None)
        else:
            sys.modules["dash"] = original  # Restore prior stub


class _FakeCallbackManager:
    """Minimal stand-in for PlotlyMapCallbackManager."""

    def apply_layer_toggles(self, **_kwargs: Any) -> dict[str, Any]:
        return {}

    def build_click_details(self, **_kwargs: Any) -> dict[str, Any]:
        return {}


class _FakeResponse:
    """Stand-in for a mistapi API response."""

    def __init__(self, status_code: int, data: Any = None) -> None:
        self.status_code = status_code  # HTTP status
        self.data = data  # Parsed JSON payload


class _FakeSerializer:
    """Stand-in for PlotlyMapDataSerializer with the 2 methods we exercise."""

    def build_dropdown_options(self, items: list[dict[str, Any]], default_name: str) -> list[dict[str, Any]]:
        return [{"label": it.get("name", default_name), "value": it.get("id")} for it in items]

    def build_named_items(self, items: list[dict[str, Any]], default_name: str) -> list[dict[str, Any]]:
        return [{"id": it.get("id"), "name": it.get("name", default_name)} for it in items]


class _RecordedCallback:
    """Container for a single recorded @app.callback registration."""

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


def _make_mistapi_stub(
    list_maps_response: _FakeResponse | None = None,
    list_devices_response: _FakeResponse | None = None,
) -> types.SimpleNamespace:
    """Build a minimal mistapi namespace with listSiteMaps + listSiteDevicesStats."""
    maps_ns = types.SimpleNamespace(
        listSiteMaps=lambda *a, **k: list_maps_response or _FakeResponse(200, data=[]),
        getSiteMap=lambda *a, **k: _FakeResponse(200, data={}),
    )
    stats_ns = types.SimpleNamespace(
        listSiteDevicesStats=lambda *a, **k: list_devices_response or _FakeResponse(200, data=[]),
        listSiteWirelessClientsStats=lambda *a, **k: _FakeResponse(200, data=[]),
    )
    zones_ns = types.SimpleNamespace(listSiteZones=lambda *a, **k: _FakeResponse(200, data=[]))
    sites_ns = types.SimpleNamespace(maps=maps_ns, stats=stats_ns, zones=zones_ns)
    return types.SimpleNamespace(
        api=types.SimpleNamespace(v1=types.SimpleNamespace(sites=sites_ns)),
        get_all=lambda response, mist_session: (response.data or []),
    )


def _make_state(**overrides: Any) -> MapViewerState:
    """Construct a MapViewerState with sensible defaults for wave-E2 callbacks."""
    defaults: dict[str, Any] = {
        "callback_manager": _FakeCallbackManager(),
        "zones": [],
        "map_id": "test-map-id",
        "site_id": "test-site-id",
        "api_session_ref": object(),
        "ppm": 10.0,
        "mistapi_ref": _make_mistapi_stub(),
        "maps_manager_ref": object(),
        "serializer": _FakeSerializer(),
        "all_sites": [{"id": "site-1", "name": "S1"}],
        "all_maps": [{"id": "map-1", "name": "M1"}],
        "available_sites": [{"id": "site-1", "name": "S1"}],
        "figure_builder": types.SimpleNamespace(
            add_walls=lambda *a, **k: None,
            add_wayfinding=lambda *a, **k: None,
            add_zones=lambda *a, **k: None,
        ),
        "heatmap_renderer": object(),
    }
    defaults.update(overrides)
    return MapViewerState(**defaults)


# ---------------------------------------------------------------------------
# State construction
# ---------------------------------------------------------------------------


def test_state_accepts_new_wave_e2_fields() -> None:
    """MapViewerState exposes the wave E2 fields with sensible defaults."""
    state = _make_state()
    assert state.serializer is not None  # _FakeSerializer provided
    assert state.all_sites == [{"id": "site-1", "name": "S1"}]
    assert state.all_maps == [{"id": "map-1", "name": "M1"}]
    assert state.available_sites == [{"id": "site-1", "name": "S1"}]
    assert state.figure_builder is not None
    # heatmap_renderer defaults to None when omitted
    state2 = MapViewerState(callback_manager=_FakeCallbackManager())
    assert state2.serializer is None
    assert state2.all_sites == []
    assert state2.all_maps == []
    assert state2.available_sites == []


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_with_wires_twentyfour_callbacks_total() -> None:
    """register_with now wires waves A+B+C+D+E1+E2 = 24 callbacks."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()
    callbacks.register_with(app)
    assert len(app.registered) == 24
    bound_names = {record.bound_func.__name__ for record in app.registered}
    assert "set_scale" in bound_names
    assert "refresh_map_dropdown" in bound_names
    assert "handle_site_from_url" in bound_names
    assert "sync_dropdown_with_url" in bound_names
    assert "handle_site_switch_from_dropdown" in bound_names
    assert "handle_url_map_switch" in bound_names


# ---------------------------------------------------------------------------
# set_scale
# ---------------------------------------------------------------------------


def test_set_scale_returns_error_when_inputs_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    msg, fig = callbacks.set_scale(None, None, {"layout": {"shapes": []}})
    assert "valid length" in msg
    assert fig == {"layout": {"shapes": []}}


def test_set_scale_returns_error_when_no_line_drawn() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    msg, _ = callbacks.set_scale(1, 5.0, {"layout": {"shapes": []}})
    assert "draw a line first" in msg


def test_set_scale_updates_ppm_when_line_present() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig: dict[str, Any] = {
        "layout": {
            "shapes": [{"type": "line", "x0": 0, "y0": 0, "x1": 100, "y1": 0}],
            "annotations": [],
        }
    }
    msg, updated = callbacks.set_scale(1, 10.0, fig)
    assert msg.startswith("[OK] Scale set!")
    assert updated["layout"]["meta"]["ppm"] == 10.0  # 100 px / 10 m


# ---------------------------------------------------------------------------
# refresh_map_dropdown
# ---------------------------------------------------------------------------


def test_refresh_map_dropdown_returns_no_update_without_site_id() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    options, store = callbacks.refresh_map_dropdown(None, None, None, {})
    assert options == "__NO_UPDATE__"
    assert store == "__NO_UPDATE__"


def test_refresh_map_dropdown_returns_fresh_options_on_success() -> None:
    mistapi_stub = _make_mistapi_stub(
        list_maps_response=_FakeResponse(200, data=[{"id": "m1", "name": "Lobby"}])
    )
    state = _make_state(mistapi_ref=mistapi_stub)
    callbacks = MapViewerCallbacks(state=state)
    options, store = callbacks.refresh_map_dropdown(None, None, None, {"site_id": "site-1"})
    assert options == [{"label": "Lobby", "value": "m1"}]
    assert store == [{"id": "m1", "name": "Lobby"}]


def test_refresh_map_dropdown_returns_no_update_on_http_error() -> None:
    mistapi_stub = _make_mistapi_stub(list_maps_response=_FakeResponse(500))
    state = _make_state(mistapi_ref=mistapi_stub)
    callbacks = MapViewerCallbacks(state=state)
    options, store = callbacks.refresh_map_dropdown(None, None, None, {"site_id": "s1"})
    assert options == "__NO_UPDATE__"
    assert store == "__NO_UPDATE__"


# ---------------------------------------------------------------------------
# handle_site_from_url
# ---------------------------------------------------------------------------


def test_handle_site_from_url_returns_no_update_when_empty() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    assert callbacks.handle_site_from_url(None, {}, []) == ["__NO_UPDATE__"]
    assert callbacks.handle_site_from_url("", {}, []) == ["__NO_UPDATE__"]


def test_handle_site_from_url_returns_no_update_when_param_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    assert callbacks.handle_site_from_url("?map_id=m1", {}, []) == ["__NO_UPDATE__"]


def test_handle_site_from_url_returns_no_update_when_already_current() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    result = callbacks.handle_site_from_url("?site_id=site-1", {"site_id": "site-1"}, [{"id": "site-1"}])
    assert result == ["__NO_UPDATE__"]


def test_handle_site_from_url_rejects_unknown_site() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    result = callbacks.handle_site_from_url("?site_id=unknown", {}, [{"id": "site-1"}])
    assert result == ["__NO_UPDATE__"]


def test_handle_site_from_url_returns_valid_site_id() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    result = callbacks.handle_site_from_url(
        "?site_id=site-2", {"site_id": "site-1"}, [{"id": "site-1"}, {"id": "site-2"}]
    )
    assert result == ["site-2"]


# ---------------------------------------------------------------------------
# sync_dropdown_with_url
# ---------------------------------------------------------------------------


def test_sync_dropdown_with_url_returns_no_update_when_empty() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    assert callbacks.sync_dropdown_with_url(None, [], None) == "__NO_UPDATE__"


def test_sync_dropdown_with_url_returns_no_update_when_param_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    assert callbacks.sync_dropdown_with_url("?site_id=s1", [], None) == "__NO_UPDATE__"


def test_sync_dropdown_with_url_returns_valid_map_id() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    result = callbacks.sync_dropdown_with_url("?map_id=m2", [{"id": "m1"}, {"id": "m2"}], "m1")
    assert result == "m2"


def test_sync_dropdown_with_url_rejects_unknown_map() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    result = callbacks.sync_dropdown_with_url("?map_id=unknown", [{"id": "m1"}], "m1")
    assert result == "__NO_UPDATE__"


# ---------------------------------------------------------------------------
# handle_site_switch_from_dropdown
# ---------------------------------------------------------------------------


def test_handle_site_switch_returns_no_update_when_empty() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    out = callbacks.handle_site_switch_from_dropdown(None, {}, [], {})
    assert out == ("__NO_UPDATE__",) * 5


def test_handle_site_switch_returns_no_update_when_same_site() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    out = callbacks.handle_site_switch_from_dropdown("site-1", {"site_id": "site-1"}, [], {})
    assert out == ("__NO_UPDATE__",) * 5


def test_handle_site_switch_returns_empty_payload_when_no_maps() -> None:
    state = _make_state(mistapi_ref=_make_mistapi_stub(list_maps_response=_FakeResponse(200, data=[])))
    callbacks = MapViewerCallbacks(state=state)
    options, value, store, config, _fig = callbacks.handle_site_switch_from_dropdown(
        "site-2", {"site_id": "site-1"}, [{"id": "site-2", "name": "S2"}], {}
    )
    assert options == []
    assert value is None
    assert store == []
    assert config["site_id"] == "site-2"
    assert config["map_id"] is None


# ---------------------------------------------------------------------------
# handle_url_map_switch
# ---------------------------------------------------------------------------


def test_handle_url_map_switch_returns_no_update_when_empty() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig, cfg = callbacks.handle_url_map_switch(None, {}, {}, [], None)
    assert fig == "__NO_UPDATE__"
    assert cfg == "__NO_UPDATE__"


def test_handle_url_map_switch_returns_no_update_when_param_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig, cfg = callbacks.handle_url_map_switch("?site_id=s1", {}, {}, [], None)
    assert fig == "__NO_UPDATE__"
    assert cfg == "__NO_UPDATE__"


def test_handle_url_map_switch_returns_no_update_when_map_matches() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig, cfg = callbacks.handle_url_map_switch(
        "?map_id=m1", {"map_id": "m1", "site_id": "s1"}, {}, [{"id": "m1"}], "m1"
    )
    assert fig == "__NO_UPDATE__"
    assert cfg == "__NO_UPDATE__"


def test_handle_url_map_switch_returns_no_update_when_site_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig, cfg = callbacks.handle_url_map_switch("?map_id=m2", {"map_id": "m1"}, {}, [{"id": "m2"}], "m1")
    assert fig == "__NO_UPDATE__"
    assert cfg == "__NO_UPDATE__"


def test_handle_url_map_switch_rejects_unknown_map() -> None:
    state = _make_state(
        mistapi_ref=_make_mistapi_stub(list_maps_response=_FakeResponse(200, data=[{"id": "m1"}]))
    )
    callbacks = MapViewerCallbacks(state=state)
    fig, cfg = callbacks.handle_url_map_switch(
        "?map_id=unknown", {"site_id": "s1", "map_id": "m1"}, {}, [{"id": "m1"}], "m1"
    )
    assert fig == "__NO_UPDATE__"
    assert cfg == "__NO_UPDATE__"
