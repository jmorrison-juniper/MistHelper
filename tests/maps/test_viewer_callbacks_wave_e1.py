"""Unit tests for wave E1 of the Plotly viewer callback extraction.

Covers the 2 callbacks newly on :class:`MapViewerCallbacks`:

* :py:meth:`MapViewerCallbacks.execute_clone_operation` -- clone the
  current map (validate, fetch source, build payload, download image,
  create cloned map, upload image, clone zones).
* :py:meth:`MapViewerCallbacks._drawing.handle_drawing_tools` -- dispatch the
  drawing toolbar buttons (save shape / delete walls / paths / zones).

Uses the same dash-stub + autouse fixture pattern as
``tests/maps/test_viewer_callbacks_wave_d.py``.
"""

from __future__ import annotations

import importlib.machinery  # Stub-spec construction
import sys  # sys.modules manipulation for stub install
import types  # ModuleType + SimpleNamespace for mistapi stubs
from collections.abc import Iterator  # Typing for fixture generator
from typing import Any  # Permissive typing for mistapi/dash stubs

import pytest  # Test fixture / parametrize APIs


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
        P=lambda *a, **k: {"P": (a, k)},  # Stand-in for dash.html.P
        Div=lambda *a, **k: {"Div": (a, k)},  # Stand-in for dash.html.Div
        H3=lambda *a, **k: {"H3": (a, k)},  # Stand-in for dash.html.H3
        Span=lambda *a, **k: {"Span": (a, k)},  # Stand-in for dash.html.Span
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
        return {}  # Tests don't exercise layer toggling

    def build_click_details(self, **_kwargs: Any) -> dict[str, Any]:
        return {}  # Tests don't exercise click details


class _FakeResponse:
    """Stand-in for a mistapi API response with status_code + data + text."""

    def __init__(self, status_code: int, data: Any = None, text: str = "") -> None:
        self.status_code = status_code  # HTTP status returned by Mist
        self.data = data  # Parsed JSON payload
        self.text = text  # Raw text body (used in error renderers)


class _RecordedCallback:
    """Container for a single recorded @app.callback registration."""

    def __init__(self, args: tuple, kwargs: dict[str, Any]) -> None:
        self.args = args  # Positional args to @app.callback(...)
        self.kwargs = kwargs  # Keyword args
        self.bound_func: Any = None  # Function bound by the returned decorator


class _FakeDashApp:
    """Minimal Dash app stub that records callback registrations."""

    def __init__(self) -> None:
        self.registered: list[_RecordedCallback] = []  # All callback records

    def callback(self, *args: Any, **kwargs: Any):
        record = _RecordedCallback(args=args, kwargs=kwargs)  # Snapshot args
        self.registered.append(record)  # Track registration order

        def _decorator(func: Any) -> Any:
            record.bound_func = func  # Capture the bound function
            return func

        return _decorator


class _MapsManagerStub:
    """Stub for MapsManager._backup_map_geometry; records every call."""

    def __init__(self, backup_path: str | None = "/tmp/backup.json") -> None:
        self.calls: list[dict[str, Any]] = []  # All backup invocations
        self._backup_path = backup_path  # Path returned to caller

    def _backup_map_geometry(
        self,
        api_session: Any,
        site_id: str,
        map_id: str,
        map_name: str,
        backup_reason: str,
    ) -> str | None:
        self.calls.append(  # Capture each backup call for assertions
            {
                "api_session": api_session,
                "site_id": site_id,
                "map_id": map_id,
                "map_name": map_name,
                "backup_reason": backup_reason,
            }
        )
        return self._backup_path


def _make_clone_mistapi(  # many small flags to drive each step independently
    source_response: _FakeResponse,
    create_response: _FakeResponse,
    upload_response: _FakeResponse | None = None,
    zones_list_response: _FakeResponse | None = None,
    zone_create_response: _FakeResponse | None = None,
) -> Any:
    """Build a mistapi stub for the clone callback that records calls."""
    calls: dict[str, list[Any]] = {
        "getSiteMap": [],
        "createSiteMap": [],
        "addSiteMapImageFile": [],
        "listSiteZones": [],
        "createSiteZone": [],
    }

    def _get_site_map(session: Any, site_id: str, map_id: str) -> _FakeResponse:
        calls["getSiteMap"].append({"session": session, "site_id": site_id, "map_id": map_id})
        return source_response

    def _create_site_map(session: Any, site_id: str, body: dict[str, Any]) -> _FakeResponse:
        calls["createSiteMap"].append({"session": session, "site_id": site_id, "body": body})
        return create_response

    def _add_site_map_image_file(session: Any, site_id: str, map_id: str, file: str) -> _FakeResponse:
        calls["addSiteMapImageFile"].append(
            {
                "session": session,
                "site_id": site_id,
                "map_id": map_id,
                "file": file,
            }
        )
        return upload_response or _FakeResponse(200)

    def _list_site_zones(session: Any, site_id: str) -> _FakeResponse:
        calls["listSiteZones"].append({"session": session, "site_id": site_id})
        return zones_list_response or _FakeResponse(200, data=[])

    def _create_site_zone(session: Any, site_id: str, body: dict[str, Any]) -> _FakeResponse:
        calls["createSiteZone"].append({"session": session, "site_id": site_id, "body": body})
        return zone_create_response or _FakeResponse(201)

    maps_ns = types.SimpleNamespace(
        getSiteMap=_get_site_map,
        createSiteMap=_create_site_map,
        addSiteMapImageFile=_add_site_map_image_file,
        updateSiteMap=lambda *a, **k: _FakeResponse(200),
    )
    zones_ns = types.SimpleNamespace(
        listSiteZones=_list_site_zones,
        createSiteZone=_create_site_zone,
        deleteSiteZone=lambda *a, **k: _FakeResponse(200),
    )
    sites_ns = types.SimpleNamespace(maps=maps_ns, zones=zones_ns)
    v1_ns = types.SimpleNamespace(sites=sites_ns)
    api_ns = types.SimpleNamespace(v1=v1_ns)
    mistapi_stub = types.SimpleNamespace(api=api_ns, _calls=calls)  # _calls for assertions
    return mistapi_stub


def _make_state(**overrides: Any) -> MapViewerState:
    """Build a MapViewerState with sensible defaults for wave-E1 tests."""
    defaults: dict[str, Any] = {
        "callback_manager": _FakeCallbackManager(),
        "zones": [],
        "map_id": "test-map-id",
        "site_id": "test-site-id",
        "api_session_ref": object(),
        "ppm": 10.0,
        "mistapi_ref": _make_clone_mistapi(_FakeResponse(200), _FakeResponse(201)),
        "maps_manager_ref": _MapsManagerStub(),
    }
    defaults.update(overrides)
    return MapViewerState(**defaults)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_with_wires_eighteen_callbacks_total() -> None:
    """register_with now wires waves A+B+C+D + 2 wave-E1 callbacks = 18."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    assert len(app.registered) == 24
    bound_names = {record.bound_func.__name__ for record in app.registered}
    assert "execute_clone_operation" in bound_names
    assert "handle_drawing_tools" in bound_names


def test_register_with_wave_e1_uses_prevent_initial_call() -> None:
    """Both wave-E1 callbacks set prevent_initial_call=True."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    wave_e1 = {"execute_clone_operation", "handle_drawing_tools"}
    for record in app.registered:
        if record.bound_func.__name__ in wave_e1:
            assert record.kwargs.get("prevent_initial_call") is True


# ---------------------------------------------------------------------------
# execute_clone_operation
# ---------------------------------------------------------------------------


def test_clone_returns_empty_when_n_clicks_zero() -> None:
    """No click => silent no-op (empty string, no cache-bust update)."""
    callbacks = MapViewerCallbacks(state=_make_state())

    msg, cache = callbacks.execute_clone_operation(0, "name", {"site_id": "s", "map_id": "m"}, {})

    assert msg == ""
    assert cache == "__NO_UPDATE__"


def test_clone_rejects_empty_name() -> None:
    """Missing/blank new_name => user-visible error and no-update cache."""
    callbacks = MapViewerCallbacks(state=_make_state())

    msg, cache = callbacks.execute_clone_operation(1, "   ", {"site_id": "s", "map_id": "m"}, {})

    assert isinstance(msg, dict) and "Span" in msg  # html.Span stub
    assert cache == "__NO_UPDATE__"


def test_clone_rejects_missing_config() -> None:
    """Missing site_id/map_id => user-visible error and no-update cache."""
    callbacks = MapViewerCallbacks(state=_make_state())

    msg, cache = callbacks.execute_clone_operation(1, "NewMap", {}, {})

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


def test_clone_happy_path_creates_map_and_increments_cache_bust() -> None:
    """Successful clone => success Span + incremented cache-bust trigger."""
    source = _FakeResponse(
        200,
        data={
            "name": "Source",
            "type": "image",
            "width": 1000,
            "height": 800,
            "ppm": 10,
            "url": "https://example.com/map.png",
        },
    )
    create = _FakeResponse(201, data={"id": "new-map-id"})
    mistapi_stub = _make_clone_mistapi(source, create)
    maps_manager = _MapsManagerStub()
    state = _make_state(mistapi_ref=mistapi_stub, maps_manager_ref=maps_manager)
    callbacks = MapViewerCallbacks(state=state)

    msg, cache = callbacks.execute_clone_operation(
        1, "CopyMap", {"site_id": "site-1", "map_id": "src-map", "map_name": "Source"}, {"trigger": 5}
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == {"trigger": 6}  # Trigger bumped by 1
    assert len(maps_manager.calls) == 1  # Backup invoked
    assert maps_manager.calls[0]["backup_reason"] == "pre_clone"
    assert len(mistapi_stub._calls["getSiteMap"]) == 1
    assert len(mistapi_stub._calls["createSiteMap"]) == 1
    create_body = mistapi_stub._calls["createSiteMap"][0]["body"]
    assert create_body["name"] == "CopyMap"
    assert create_body["width"] == 1000  # Dimensional props copied


def test_clone_fetch_source_failure_returns_error() -> None:
    """getSiteMap !200 => error Span, no cache-bust update."""
    source = _FakeResponse(404, data=None)
    create = _FakeResponse(201, data={"id": "new"})
    state = _make_state(
        mistapi_ref=_make_clone_mistapi(source, create),
        maps_manager_ref=_MapsManagerStub(backup_path=None),
    )
    callbacks = MapViewerCallbacks(state=state)

    msg, cache = callbacks.execute_clone_operation(
        1, "Copy", {"site_id": "s", "map_id": "m", "map_name": "Src"}, {"trigger": 0}
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


def test_clone_create_failure_returns_error_and_does_not_bump_cache() -> None:
    """createSiteMap !200/201 => error Span, no cache update."""
    source = _FakeResponse(200, data={"type": "image", "width": 1, "height": 1})
    create = _FakeResponse(500, data=None)
    state = _make_state(
        mistapi_ref=_make_clone_mistapi(source, create),
        maps_manager_ref=_MapsManagerStub(),
    )
    callbacks = MapViewerCallbacks(state=state)

    msg, cache = callbacks.execute_clone_operation(
        1, "Copy", {"site_id": "s", "map_id": "m", "map_name": "Src"}, {"trigger": 2}
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


# ---------------------------------------------------------------------------
# handle_drawing_tools (dispatcher + branches)
# ---------------------------------------------------------------------------


def _trigger_dash(_dash_stub: types.ModuleType, button_id: str) -> None:
    """Helper: set dash.callback_context.triggered to the given button id."""
    _dash_stub.callback_context.triggered = [{"prop_id": f"{button_id}.n_clicks"}]


def test_handle_drawing_no_trigger_returns_empty(_dash_stub: types.ModuleType) -> None:
    """When ctx.triggered is empty, callback returns ('', no_update)."""
    _dash_stub.callback_context.triggered = []
    callbacks = MapViewerCallbacks(state=_make_state())

    msg, cache = callbacks._drawing.handle_drawing_tools(  # dispatcher signature
        1, 0, 0, 0, 0, 0, "zone", "Z1", {"layout": {"shapes": []}}, {}, {}
    )

    assert msg == ""
    assert cache == "__NO_UPDATE__"


def test_handle_drawing_clear_button_returns_local_only_message(
    _dash_stub: types.ModuleType,
) -> None:
    """clear-drawings-btn returns the local-only guidance Span."""
    _trigger_dash(_dash_stub, "clear-drawings-btn")
    callbacks = MapViewerCallbacks(state=_make_state())

    msg, cache = callbacks._drawing.handle_drawing_tools(
        0, 1, 0, 0, 0, 0, None, None, {"layout": {"shapes": []}}, None, None
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


def test_handle_drawing_save_zone_rect_calls_createSiteZone(
    _dash_stub: types.ModuleType,
) -> None:
    """save-shape-btn in zone mode with a rect shape calls createSiteZone."""
    _trigger_dash(_dash_stub, "save-shape-btn")
    mistapi_stub = _make_clone_mistapi(_FakeResponse(200), _FakeResponse(201), zone_create_response=_FakeResponse(201))
    state = _make_state(mistapi_ref=mistapi_stub)
    callbacks = MapViewerCallbacks(state=state)

    fig = {
        "layout": {
            "shapes": [{"type": "rect", "x0": 0, "y0": 0, "x1": 100, "y1": 100}],
        }
    }
    msg, cache = callbacks._drawing.handle_drawing_tools(
        1,
        0,
        0,
        0,
        0,
        0,
        "zone",
        "Lobby",
        fig,
        {"site_id": "site-1", "map_id": "map-1", "ppm": 10},
        {"trigger": 7},
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == {"trigger": 8}  # Cache-bust bumped on success
    assert len(mistapi_stub._calls["createSiteZone"]) == 1
    zone_body = mistapi_stub._calls["createSiteZone"][0]["body"]
    assert zone_body["name"] == "Lobby"
    assert zone_body["map_id"] == "map-1"
    assert len(zone_body["vertices"]) == 4  # Rect -> 4 corners


def test_handle_drawing_save_zone_without_name_returns_error(
    _dash_stub: types.ModuleType,
) -> None:
    """Saving a zone without a zone name returns an error Span."""
    _trigger_dash(_dash_stub, "save-shape-btn")
    state = _make_state()
    callbacks = MapViewerCallbacks(state=state)

    fig = {"layout": {"shapes": [{"type": "rect", "x0": 0, "y0": 0, "x1": 10, "y1": 10}]}}
    msg, cache = callbacks._drawing.handle_drawing_tools(
        1,
        0,
        0,
        0,
        0,
        0,
        "zone",
        "",
        fig,
        {"site_id": "s", "map_id": "m", "ppm": 10},
        {},
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


def test_handle_drawing_save_no_shapes_returns_error(
    _dash_stub: types.ModuleType,
) -> None:
    """save-shape-btn with no drawn shapes returns an error Span."""
    _trigger_dash(_dash_stub, "save-shape-btn")
    callbacks = MapViewerCallbacks(state=_make_state())

    fig: dict[str, Any] = {"layout": {"shapes": []}}
    msg, cache = callbacks._drawing.handle_drawing_tools(
        1, 0, 0, 0, 0, 0, "zone", "Lobby", fig, {"site_id": "s", "map_id": "m", "ppm": 10}, {}
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == "__NO_UPDATE__"


def test_handle_drawing_delete_paths_calls_updateSiteMap(
    _dash_stub: types.ModuleType,
) -> None:
    """delete-paths-btn issues updateSiteMap with empty sitesurvey_path."""
    _trigger_dash(_dash_stub, "delete-paths-btn")
    update_calls: list[dict[str, Any]] = []

    def _update(session: Any, site_id: str, map_id: str, body: dict[str, Any]) -> _FakeResponse:
        update_calls.append({"session": session, "site_id": site_id, "map_id": map_id, "body": body})
        return _FakeResponse(200)

    maps_ns = types.SimpleNamespace(updateSiteMap=_update, getSiteMap=lambda *a, **k: _FakeResponse(200))
    zones_ns = types.SimpleNamespace(
        listSiteZones=lambda *a, **k: _FakeResponse(200, data=[]), deleteSiteZone=lambda *a, **k: _FakeResponse(200)
    )
    mistapi_stub = types.SimpleNamespace(
        api=types.SimpleNamespace(v1=types.SimpleNamespace(sites=types.SimpleNamespace(maps=maps_ns, zones=zones_ns)))
    )
    state = _make_state(mistapi_ref=mistapi_stub)
    callbacks = MapViewerCallbacks(state=state)

    msg, cache = callbacks._drawing.handle_drawing_tools(
        0,
        0,
        1,
        0,
        0,
        0,
        None,
        None,
        {"layout": {"shapes": []}},
        {"site_id": "site-1", "map_id": "map-1", "ppm": 10},
        {"trigger": 3},
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == {"trigger": 4}  # Cache-bust bumped on success
    assert len(update_calls) == 1
    assert update_calls[0]["body"] == {"sitesurvey_path": []}


def test_handle_drawing_delete_zones_iterates_each_zone(
    _dash_stub: types.ModuleType,
) -> None:
    """delete-zones-btn loops listSiteZones results and DELETEs each one."""
    _trigger_dash(_dash_stub, "delete-zones-btn")
    delete_calls: list[Any] = []

    def _list(session: Any, site_id: str) -> _FakeResponse:
        return _FakeResponse(
            200,
            data=[
                {"id": "z1", "name": "Z1", "map_id": "map-1"},
                {"id": "z2", "name": "Z2", "map_id": "map-1"},
                {"id": "z3", "name": "Z3", "map_id": "other-map"},  # Filtered out
            ],
        )

    def _del(session: Any, site_id: str, zone_id: str) -> _FakeResponse:
        delete_calls.append(zone_id)
        return _FakeResponse(204)

    zones_ns = types.SimpleNamespace(
        listSiteZones=_list, deleteSiteZone=_del, createSiteZone=lambda *a, **k: _FakeResponse(201)
    )
    maps_ns = types.SimpleNamespace(
        updateSiteMap=lambda *a, **k: _FakeResponse(200), getSiteMap=lambda *a, **k: _FakeResponse(200)
    )
    mistapi_stub = types.SimpleNamespace(
        api=types.SimpleNamespace(v1=types.SimpleNamespace(sites=types.SimpleNamespace(maps=maps_ns, zones=zones_ns)))
    )
    state = _make_state(mistapi_ref=mistapi_stub)
    callbacks = MapViewerCallbacks(state=state)

    msg, cache = callbacks._drawing.handle_drawing_tools(
        0,
        0,
        0,
        0,
        0,
        1,
        None,
        None,
        {"layout": {"shapes": []}},
        {"site_id": "site-1", "map_id": "map-1", "ppm": 10},
        {"trigger": 10},
    )

    assert isinstance(msg, dict) and "Span" in msg
    assert cache == {"trigger": 11}  # Cache-bust bumped after successful deletes
    assert delete_calls == ["z1", "z2"]  # Only zones on map-1 are deleted
